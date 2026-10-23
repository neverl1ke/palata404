"""Індивідуальне стикування наявних голів із незміненою базовою шиєю.
Потрібні затверджені PNG з 38f5ba4 та два надані архіви джерел.
Генерація зображень не використовується; верх голови зберігається побайтово.
"""
import argparse,hashlib,json,zipfile
from io import BytesIO
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
# Межі вибрані після вимірювання підборіддя й нижньої щелепи кожної голови.
# center, radius, recoveryY, startY, endY, startArc, endArc, overlap.
PROFILES={
 'young':{'male':(474,70,224,258,282,26,22,10),'female':(473,65,225,248,274,25,18,8)},
 'exhausted':{'male':(474,69,223,261,287,27,22,9),'female':(473,62,224,240,272,13,14,9)},
 'elder':{'male':(474,71,224,257,285,23,21,8),'female':(474,64,226,245,276,20,18,7)}}
OFFSETS={'young':{'male':(-10,0),'female':(-18,0)},'exhausted':{'male':(349,30),'female':(356,25)},'elder':{'male':(387,30),'female':(390,25)}}

def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def digest(b):return hashlib.sha256(b).hexdigest()
def soft_distance(a):
 m=a>=.5;d=ndi.distance_transform_edt(m)-ndi.distance_transform_edt(~m)
 edge=(a>0)&(a<1);d[edge]=a[edge]-.5
 return d
def extended_rgb(rgba):
 _,idx=ndi.distance_transform_edt(rgba[:,:,3]<250,return_indices=True)
 return rgba[idx[0],idx[1],:3].astype(float)

def repair(kind,gender,approved,raw):
 before=Image.open(BytesIO(approved)).convert('RGBA');old=np.array(before)
 raw_img=Image.open(BytesIO(raw)).convert('RGBA');registered=Image.new('RGBA',(941,1672));registered.paste(raw_img,OFFSETS[kind][gender]);source=np.array(registered)
 base=np.array(Image.open(ROOT/f'base_{gender}.png').convert('RGBA'))
 center,radius,recovery,start,end,start_arc,end_arc,overlap=PROFILES[kind][gender]
 y,x=np.mgrid[:1672,:941]
 # Restore only the lower jaw/neck that the former y=245 crop damaged.
 # Clean the source edge locally; no RGB filtering of the face itself.
 sa=source[:,:,3]/255;sd=ndi.gaussian_filter(ndi.distance_transform_edt(sa>=.5)-ndi.distance_transform_edt(sa<.5),1.4);clean_a=np.clip((sd+.4)/.8,0,1)
 filled=extended_rgb(source);edge=(sd<3)&(clean_a>0)
 source[edge,:3]=np.rint(filled[edge]).astype('uint8')
 source[:,:,3]=np.rint(clean_a*255).astype('uint8')
 r=smooth((y-recovery)/(radius/7))
 a0=old[:,:,3]/255;a1=source[:,:,3]/255
 texture_a=a0*(1-r)+a1*r
 a=np.clip((1-r)*soft_distance(a0)+r*soft_distance(a1)+.5,0,1)
 premul=old[:,:,:3]*a0[:,:,None]*(1-r[:,:,None])+source[:,:,:3]*a1[:,:,None]*r[:,:,None]
 rgb=np.divide(premul,texture_a[:,:,None],out=np.zeros_like(premul),where=texture_a[:,:,None]>0)
 working=np.dstack((np.rint(rgb),np.rint(a*255))).astype('uint8')
 # Curved, personal under-jaw boundary. The centre begins below the chin;
 # the lateral portions follow the mandibular corners, not one horizontal cut.
 arc=np.minimum(((x-center)/radius)**2,1)
 start_field=start-start_arc*arc;end_field=end-end_arc*arc
 b=smooth((y-start_field)/(end_field-start_field))
 ba=base[:,:,3]/255
 da=soft_distance(a);db=soft_distance(ba)
 neck_alpha=np.clip(((1-b)*da+b*db+.5),0,1)
 neck_rgb=(1-b[:,:,None])*extended_rgb(working)+b[:,:,None]*extended_rgb(base)
 at_source=b==0;at_base=b==1
 neck_alpha[at_source]=a[at_source];neck_rgb[at_source]=working[:,:,:3][at_source]
 neck_alpha[at_base]=ba[at_base];neck_rgb[at_base]=base[:,:,:3][at_base]
 # The overlay already equals the original neck at the end of each curved blend.
 # Complementary occlusion prevents both double edges and translucent neck seams.
 g=1-smooth((y-end_field)/overlap)
 # Refine only the personal neck-side interval into a single continuous outline.
 # This removes source-cut stair steps without altering the jaw or clothing.
 old_visibility=np.divide(1-g,1-ba*g,out=np.zeros_like(g),where=(1-ba*g)>1e-8)
 combined=neck_alpha*g+ba*old_visibility*(1-neck_alpha*g)
 rows=np.arange(210,311);left=[];right=[]
 for yy in rows:
  points=np.where(combined[yy,350:601]>=.5)[0]
  left.append(points[0]+350);right.append(points[-1]+350)
 left=ndi.gaussian_filter1d(ndi.median_filter(np.array(left,dtype=float),size=3),1.6)
 right=ndi.gaussian_filter1d(ndi.median_filter(np.array(right,dtype=float),size=3),1.6)
 l=np.interp(np.arange(1672),rows,left)[:,None];rr=np.interp(np.arange(1672),rows,right)[:,None]
 outline_distance=np.minimum(x-(l-.5),(rr+.5)-x)
 contour_end=end-end_arc+overlap
 h=smooth((y-recovery)/(radius/7))*(1-smooth((y-(contour_end-5))/5))
 target=np.clip((1-h)*soft_distance(combined)+h*outline_distance+.5,0,1)
 # Let the overlay own corrected edge pixels; retain the exact old torso elsewhere.
 minimum=np.divide(target-ba,1-ba,out=np.zeros_like(target),where=ba<1)
 opacity=np.maximum(target*g,np.clip(minimum,0,1))
 corrected_edge=(h>0)&(target>0)&((ba<.99)|(neck_alpha<.99))
 opacity[corrected_edge]=target[corrected_edge]
 fill=(1-b[:,:,None])*extended_rgb(working)+b[:,:,None]*extended_rgb(base)
 neck_rgb[corrected_edge]=fill[corrected_edge]
 output=np.dstack((np.rint(neck_rgb),np.rint(opacity*255))).astype('uint8')
 output[output[:,:,3]==0]=0;output[:221]=old[:221]
 denominator=ba*(1-opacity)
 visibility=np.divide(target-opacity,denominator,out=np.ones_like(target),where=denominator>1e-8)
 visibility[(opacity>=1)|(target==0)]=0
 visibility[(ba==0)&(y<end+overlap)]=0
 visibility[(y>=end+overlap)]=1
 mask=np.full((1672,941,4),255,dtype='uint8');mask[:,:,3]=np.rint(np.clip(visibility,0,1)*255).astype('uint8')
 path=ROOT/'assets/wardrobe/faces'/f'{gender}_{kind}_head.png'
 mask_path=ROOT/'assets/wardrobe/faces/masks'/f'{gender}_{kind}_body.png';mask_path.parent.mkdir(exist_ok=True)
 Image.fromarray(output).save(path,optimize=True);Image.fromarray(mask).save(mask_path,optimize=True)
 assert np.array_equal(output[:221],old[:221])
 # Where the neck overlay ends, the base is fully restored without any alteration.
 assert np.all(mask[:,:,3][y>=end+overlap]==255)
 return dict(kind=kind,gender=gender,source_sha256=digest(raw),approved_sha256=digest(approved),
  output=str(path.relative_to(ROOT)),sha256=digest(path.read_bytes()),mask=str(mask_path.relative_to(ROOT)),mask_sha256=digest(mask_path.read_bytes()),
  protected_y=221,protected_sha256=digest(old[:221].tobytes()),
  detail_box=(440,85,510,205),detail_sha256=digest(before.convert('RGB').crop((440,85,510,205)).tobytes()),
  profile=dict(center=center,radius=radius,recovery_y=recovery,start_y=start,end_y=end,start_arc=start_arc,end_arc=end_arc,overlap=overlap),
  bbox=Image.fromarray(output).getbbox())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--approved-dir',type=Path,required=True);p.add_argument('--young-archive',required=True);p.add_argument('--remaining-archive',required=True);args=p.parse_args();entries=[]
 with zipfile.ZipFile(args.young_archive) as young,zipfile.ZipFile(args.remaining_archive) as remaining:
  for kind in PROFILES:
   for gender in ['male','female']:
    name=f'{gender}_{kind}_head.png';raw=young.read(f'{gender}_young_head_full_canvas.png') if kind=='young' else remaining.read(f'{kind}_{gender}_head_neck.png')
    entries.append(repair(kind,gender,(args.approved_dir/name).read_bytes(),raw))
 print(json.dumps(dict(approved_commit='38f5ba4018284a80ba4da2df77ba4e1d5e5ef59f',files=entries),indent=2))
