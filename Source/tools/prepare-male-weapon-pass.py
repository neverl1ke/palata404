"""Register new test props and a local wrist-alpha override; never rewrite rig/art."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'avatar-core';OUT=ROOT/'review/avatar-core-2-weapon-pass'
source=OUT/'sources/weapon-atlas.png';atlas=np.array(Image.open(source).convert('RGBA'))
defs=json.loads((CORE/'weapons.json').read_text());records=[]
for name,box,scale,anchors,angle in [
    ('rifle',(0,40,1536,550),.38,{'primary':[490,320],'support':[900,225],'stock':[24,200],'trigger':[585,285]},-5),
    ('pistol',(380,570,1110,1024),.30,{'primary':[545,845],'stock':[480,965],'trigger':[707,776]},0),
]:
    x,y,x1,y1=box;a=atlas[y:y1,x:x1].copy()
    a[:,:,3]=np.clip(np.rint(a[:,:,3].astype(float)*255/254),0,255).astype('uint8')
    solid=a[:,:,3]>=128
    distance,indices=ndi.distance_transform_edt(~solid,return_indices=True)
    a[(distance>1.5)&(a[:,:,3]<128)]=0
    edge=(a[:,:,3]>0)&(a[:,:,3]<128)
    a[edge,:3]=a[indices[0][edge],indices[1][edge],:3]
    a[a[:,:,3]==0]=0
    bb=Image.fromarray(a).getbbox();bx,by,bx1,by1=bb
    im=Image.fromarray(a).crop(bb);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    pixels=np.array(im);pixels[pixels[:,:,3]==0]=0;im=Image.fromarray(pixels)
    if name=='rifle':
        # The main prop keeps a uniform similarity registration between the
        # two grips. Register the wooden stock separately at its receiver seam
        # to reach the accepted shoulder contact without distorting the barrel.
        va=complex(900-490,225-320);vb=complex(285-175,82-120);z=vb/va
        forward=np.array([[z.real,-z.imag,0],[z.imag,z.real,0],[0,0,1.]])
        forward[:2,2]=np.array([175,120])-forward[:2,:2]@np.array([490,320])
        stock_source=np.array([[24,200,1],[405,205,1],[405,240,1]],float)
        seam=np.array([(forward@v)[:2] for v in stock_source[1:]])
        stock_target=np.vstack([[12,40],seam]);stock_forward=np.eye(3)
        stock_forward[:2]=np.linalg.solve(stock_source,stock_target).T
        clean=atlas.copy();clean[550:]=0
        stock=clean.copy();stock[:,411:]=0
        body=clean.copy();body[:,:400]=0
        im=Image.new('RGBA',(520,280))
        for pixels,matrix in [(stock,stock_forward),(body,forward)]:
            inv=np.linalg.inv(matrix)
            part=Image.fromarray(pixels).transform(im.size,Image.Transform.AFFINE,tuple(inv[:2].ravel()),Image.Resampling.BICUBIC)
            im=Image.alpha_composite(im,part)
        arr=np.array(im);solid=arr[:,:,3]>=128;distance,indices=ndi.distance_transform_edt(~solid,return_indices=True)
        arr[(distance>1.5)&(arr[:,:,3]<128)]=0;edge=(arr[:,:,3]>0)&(arr[:,:,3]<128);arr[edge,:3]=arr[indices[0][edge],indices[1][edge],:3]
        arr[:,:,3]=np.clip(np.rint(arr[:,:,3].astype(float)*255/254),0,255).astype('uint8');arr[arr[:,:,3]==0]=0
        im=Image.fromarray(arr)
    dest=CORE/'assets/weapons/male-preview'/f'{name}.png';dest.parent.mkdir(parents=True,exist_ok=True);im.save(dest)
    points={k:[(v[0]-x-bx)*scale,(v[1]-y-by)*scale] for k,v in anchors.items()}
    if name=='rifle':points={'primary':[175,120],'support':[285,82],'stock':[12,40],'trigger':list((forward@np.array([585,285,1]))[:2])};angle=0
    defs[name].update(image=str(dest.relative_to(CORE)),size=list(im.size),scale=1,offset=[0,0],angle=angle,
        primary=points['primary'],support=points.get('support'),stock=points['stock'],trigger=points['trigger'],
        art='realistic illustrated test prop; not production-approved')
    if name=='rifle':defs[name]['scale']=1.35
    records.append({'class':name,'source_box':box,'alpha_crop':bb,'uniform_scale':scale,'anchors_in_atlas':anchors,
        'registered_anchors':points,'image':str(dest.relative_to(CORE)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
# Tight, source-UV wrist edge correction. Preserve RGB and every texel outside
# this small band; existing approved source PNG remains byte-for-byte intact.
rig=json.loads((CORE/'rigs/male_rig.json').read_text());patch=rig['handCorrections']['melee']['right']['wristPatch']
old=np.array(Image.open(CORE/patch['image']).convert('RGBA'));new=old.copy()
xx,yy=np.meshgrid(np.arange(old.shape[1])+patch['bounds'][0],np.arange(old.shape[0])+patch['bounds'][1])
signed=ndi.distance_transform_edt(old[:,:,3]>=128)-ndi.distance_transform_edt(old[:,:,3]<128)
filtered=ndi.gaussian_filter(signed,.75)
local=(xx>=171)&(xx<=247)&(yy>=827)&(yy<=875)&(abs(signed)<2)
alpha=np.clip((filtered+.5)*255,0,255).astype('uint8');new[:,:,3][local]=np.minimum(alpha[local],old[:,:,3][local])
new[new[:,:,3]==0]=0
dest=CORE/'assets/male/weapon-pass/melee-wrist-edge.png';dest.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(new).save(dest)
changed=np.any(new!=old,axis=2)
records.append({'class':'melee-wrist','image':str(dest.relative_to(CORE)),'original':patch['image'],
    'bounds':patch['bounds'],'local_source_box':[171,827,248,876],'changed_texels':int(changed.sum()),
    'method':'signed-distance antialiasing only in a two-pixel contour band; RGB unchanged where alpha survives',
    'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
config={'weapons':defs,'surfaceOverrides':{'melee-right':str(dest.relative_to(CORE))},'transitionPolicy':'opaque-cut'}
# Recover only old-placeholder cutouts and ink, leaving opaque approved skin.
# The replacement pixels come from unchanged original skin in the same pose.
projected=np.array(Image.open(OUT/'sources/original-skin-projected.png').convert('RGBA'))
binding=json.loads((ROOT/'review/avatar-core-2/pose-bindings.json').read_text())['rifle']
m=binding['weapon']['matrix'];matrix=np.array([[m[0],m[2],m[4]],[m[1],m[3],m[5]],[0,0,1.]])
old_weapon=Image.open(CORE/'assets/weapons/rifle.png').convert('RGBA').transform((941,1672),Image.Transform.AFFINE,tuple(np.linalg.inv(matrix)[:2].ravel()),Image.Resampling.BICUBIC)
old_region=ndi.maximum_filter(np.array(old_weapon)[:,:,3]>0,size=7)
config['contactRepairs']=[]
for side in ['right','left']:
    art=rig['poseArt']['rifle'][side];a=np.zeros_like(projected)
    x,y,x1,y1=art['mesh']['bounds'];a[y:y1,x:x1]=np.array(Image.open(CORE/art['image']))
    area=Image.new('L',(941,1672));ImageDraw.Draw(area).polygon([tuple(p) for p in art['polygon']],fill=255)
    # Dark old-weapon outline or transparent cutout; never select normal skin.
    dark=(a[:,:,0]<80)&(a[:,:,1]<65)&(a[:,:,2]<65)
    problem=old_region&((a[:,:,3]<128)|dark)&(np.array(area)>0)&(projected[:,:,3]>128)
    fade=np.clip(1-ndi.distance_transform_edt(~problem)/3,0,1)*(np.array(area)/255)
    rgba=projected.copy();rgba[:,:,3]=np.rint(rgba[:,:,3]*fade).astype('uint8');rgba[rgba[:,:,3]==0]=0
    repair=Image.fromarray(rgba);box=repair.getbbox()
    repair_path=CORE/'assets/male/weapon-pass'/f'rifle-{side}-contact.png';repair.crop(box).save(repair_path)
    config['contactRepairs'].append({'pose':'rifle','side':side,'bone':'upper' if side=='right' else 'fore','image':str(repair_path.relative_to(CORE)),'bounds':list(box)})
    records.append({'class':'rifle-'+side+'-contact','image':str(repair_path.relative_to(CORE)),'bounds':box,'method':'original projected skin; only old placeholder cutouts/ink plus 3px feather','sha256':hashlib.sha256(repair_path.read_bytes()).hexdigest()})
(CORE/'male-preview.json').write_text(json.dumps(config,indent=2)+'\n')
(OUT/'registration.json').write_text(json.dumps({'atlas_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'parts':records},indent=2)+'\n')
print('Registered realistic male rifle/pistol; wrist texels changed:',changed.sum())
