"""Export reproducible, registered derivative art; originals and rigs stay untouched.
Raw local image-edit outputs, source crops and explicit bounds are retained.
Run only after the three historical reproduction tests have finished.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';O=R/'review/avatar-foundation-cleanup';W,H=941,1672

def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def clean(a):
 # Only isolated weak matte and tiny remote specks; no global erosion.
 alpha=a[:,:,3];labels,n=ndi.label(alpha>0,np.ones((3,3)));peaks=np.array(ndi.maximum(alpha,labels,range(n+1)));weak=np.isin(labels,np.flatnonzero(peaks<=16))&(labels>0);solid=alpha>=128;dist,idx=ndi.distance_transform_edt(~solid,return_indices=True);weak|=(alpha>0)&(alpha<=16)&(dist>2);a[weak]=0
 fringe=(a[:,:,3]>0)&(a[:,:,3]<128)
 a[fringe,:3]=a[idx[0][fringe],idx[1][fringe],:3];a[a[:,:,3]==0]=0
 return a
records=[]
for row in json.loads((O/'active-arms-before.json').read_text()):
 g,pose,side=row['gender'],row['pose'],row['side'];id=f'{g}-{pose}-{side}';source=np.array(Image.open(O/'Before'/f'{id}-arm.png').convert('RGBA'));edit=Image.open(O/'Edits'/f'{id}-arm.png').convert('RGBA');ea=np.array(edit);mask=ea[:,:,3]>32;labels,n=ndi.label(mask,np.ones((3,3)));sizes=np.bincount(labels.ravel());main=labels==int(sizes[1:].argmax()+1);ys,xs=np.where(main);box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1));edit=edit.crop(box).resize((source.shape[1],source.shape[0]),Image.Resampling.LANCZOS);a=np.array(edit);y,x=np.indices(source.shape[:2]);weight=smooth((y-25)/40)
 # Preserve proximal registration and native shoulder shading. Below that,
 # use the actual local retouch, not a regenerated torso/whole character.
 common=(a[:,:,3]>240)&(source[:,:,3]>240)&(y>60)
 shift=np.clip(np.median(source[common,:3].astype(float)-a[common,:3],axis=0),-6,6) if common.any() else np.zeros(3)
 a[:,:,:3]=np.clip(a[:,:,:3].astype(float)+shift,0,255).round().astype('uint8')
 oa=source[:,:,3]/255;na=a[:,:,3]/255;alpha=oa*(1-weight)+na*weight
 color=source[:,:,:3]*(oa*(1-weight))[:,:,None]+a[:,:,:3]*(na*weight)[:,:,None]
 a[:,:,:3]=np.rint(color/np.maximum(alpha[:,:,None],1e-8));a[:,:,3]=np.rint(alpha*255)
 a=clean(a)
 if g=='male' and pose=='pistol':
  # Restore the actual original negative space below the wrist. The local
  # retouch wrongly joined forearm to biceps here; this is not a painted seam.
  bx,by,_,_=json.loads((C/'rigs/male_rig.json').read_text())['poseArt']['pistol']['right']['mesh']['bounds']
  gap=(x+bx>=235)&(x+bx<280)&(y+by>=420)&(y+by<510)&(source[:,:,3]==0)
  a[gap]=0
 # Foreground ownership follows the actual edited distal hand. New fill is
 # not discarded by the old damaged finger mask. Source-space cutoff is
 # deliberately explicit and is independent of skin RGB classification.
 front=np.array(Image.open(O/'Before'/f'{id}-front.png').convert('RGBA')); fy,fx=np.where(front[:,:,3]>=128)
 rig=json.loads((C/f'rigs/{g}_rig.json').read_text());art=rig['poseArt'][pose][side];bx,by=(row['box'][:2] if g=='female' else art['mesh']['bounds'][:2]);anchors=art['anchors'];wrist=np.array(anchors['wrist']);grip=np.array(anchors['grip']);direction=(grip-wrist)/np.linalg.norm(grip-wrist);along=(x+bx-wrist[0])*direction[0]+(y+by-wrist[1])*direction[1]
 zone=(along>=-5)&(x>=int(fx.min())-10)&(x<=int(fx.max())+10)&(y>=int(fy.min())-10)&(y<=int(fy.max())+10)
 fa=a.copy();fa[~zone]=0
 complete=a.copy()
 # Only the internal wrist seam gets a 3px underlap. Outer finger fringes
 # belong to ONE layer; copying them twice produces a darker alpha rim.
 reserve=(np.abs(along+5)<=3)&(ndi.distance_transform_edt(complete[:,:,3]>=240)>2)
 a[(fa[:,:,3]>0)&~reserve]=0
 # Assign faint AA texels to the nearby strong owner after the split; do not
 # discard them or leave a remote alpha1 speck attached to the wrong layer.
 db=ndi.distance_transform_edt(a[:,:,3]<128);df=ndi.distance_transform_edt(fa[:,:,3]<128)
 move=(a[:,:,3]>0)&(a[:,:,3]<=16)&(db>2)&(df<=2);fa[move]=a[move];a[move]=0
 move=(fa[:,:,3]>0)&(fa[:,:,3]<=16)&(df>2)&(db<=2);a[move]=fa[move];fa[move]=0
 # Preserve exactly the original full-canvas registration for female assets.
 if g=='female':
  b=np.zeros((H,W,4),dtype='uint8');f=b.copy();full=b.copy();x0,y0,x1,y1=row['box'];b[y0:y1,x0:x1]=a;f[y0:y1,x0:x1]=fa;full[y0:y1,x0:x1]=complete;a,fa,complete=b,f,full
 dest=C/'assets'/g/'foundation-cleanup';dest.mkdir(exist_ok=True)
 for kind,pix in [('arm',a),('front',fa),('complete',complete)]:Image.fromarray(pix).save(dest/f'{pose}-{side}-{kind}.png')
 records.append({'id':id,'crop_bounds':row['box'],'raw_edit_crop':box,'export_size':[a.shape[1],a.shape[0]],'color_shift_rgb':shift.tolist(),'source_sha256':hashlib.sha256((O/'Before'/f'{id}-arm.png').read_bytes()).hexdigest(),'edit_sha256':hashlib.sha256((O/'Edits'/f'{id}-arm.png').read_bytes()).hexdigest(),'foreground_ownership':{'minimum_distal_wrist_projection_px':-5,'original_hand_bbox_padding_px':10}})
for g in ['male','female']:
 p=C/f'{g}-preview.json';cfg=json.loads(p.read_text());cfg['poseArtSurfaces']={};cfg['poseArtCompleteSurfaces']={}
 for row in records:
  if row['id'].startswith(g+'-'):
   _,pose,side=row['id'].split('-');cfg['poseArtSurfaces'][f'art-{pose}-{side}']=f'assets/{g}/foundation-cleanup/{pose}-{side}-arm.png';cfg['poseArtSurfaces'][f'art-front-{pose}-{side}']=f'assets/{g}/foundation-cleanup/{pose}-{side}-front.png'
 cfg['poseArtCompleteSurfaces']={row['id'].split('-',1)[1]:f"assets/{g}/foundation-cleanup/{row['id'].split('-',1)[1]}-complete.png" for row in records if row['id'].startswith(g+'-')}
 cfg['poseMeshExtensions']={}
 rig=json.loads((C/f'rigs/{g}_rig.json').read_text())
 for pose,sides in rig['poseArt'].items():
  for side,art in sides.items():
   path=C/cfg['poseArtSurfaces'][f'art-{pose}-{side}'];a=np.array(Image.open(path));front=np.array(Image.open(C/cfg['poseArtSurfaces'][f'art-front-{pose}-{side}']));a[:,:,3]=np.maximum(a[:,:,3],front[:,:,3]);mesh=art['mesh'];bx,by,_,_=mesh['bounds'];cov=Image.new('L',Image.open(path).size);d=ImageDraw.Draw(cov)
   for tri in mesh['triangles']:d.polygon([(mesh['vertices'][i][0]-bx,mesh['vertices'][i][1]-by) for i in tri],fill=255)
   missing=(a[:,:,3]>0)&(np.array(cov)==0);xs=sorted(set(v[0] for v in mesh['vertices']));ys=sorted(set(v[1] for v in mesh['vertices']));nx=len(xs);extra=[]
   for j in range(len(ys)-1):
    for i in range(nx-1):
     x0,x1=int(xs[i]-bx),int(xs[i+1]-bx);y0,y1=int(ys[j]-by),int(ys[j+1]-by)
     if missing[max(y0,0):y1+1,max(x0,0):x1+1].any():
      v=j*nx+i
      for tri in [[v,v+1,v+nx],[v+1,v+nx+1,v+nx]]:
       if tri not in mesh['triangles']:extra.append(tri)
   if extra:cfg['poseMeshExtensions'][pose+'-'+side]=extra
 cfg['meleeMotion']={'mode':'forward-wrist','upperDegrees':0.035,'foreDegrees':0.12,'handDegrees':1.6,'cycleMs':4000}
 p.write_text(json.dumps(cfg,indent=2,sort_keys=True)+'\n')
(O/'Evidence/art-export.json').write_text(json.dumps(records,indent=2)+'\n');print('Exported',len(records),'registered arm/front pairs; historical art, bases and rigs unchanged')
# Complete separate material-only test props already present in the project.
# No donor flesh or image-generation approximation is used for the weapon.
props=[]
for g in ['male','female']:
 p=C/f'{g}-preview.json';cfg=json.loads(p.read_text())
 for pose,definition in cfg['weapons'].items():
  dst=np.array(definition['primary'],float)
  if pose=='rifle':
   source=C/'assets/weapons/male-lobby/rifle.png';origin=np.array([364,668],float);support=np.array([619,755],float);delta=np.array(definition['support'])-dst;z=complex(*delta)/complex(*(support-origin))
  elif pose=='pistol':
   source=C/'assets/weapons/male-preview/pistol.png';origin=np.array([42.4,81.7]);z=np.exp(-70j*np.pi/180)*(1.05 if g=='male' else .98)
  else:
   source=C/'assets/weapons/male-exact/knife.png';origin=np.array([17.,39.42368045649073]);z=np.exp(-29j*np.pi/180)*(.98 if g=='male' else .9)
  m=np.eye(3);m[:2,:2]=[[z.real,-z.imag],[z.imag,z.real]];m[:2,2]=dst-m[:2,:2]@origin
  image=Image.open(source).convert('RGBA').transform((W,H),Image.Transform.AFFINE,tuple(np.linalg.inv(m)[:2].ravel()),Image.Resampling.BICUBIC)
  a=clean(np.array(image));dest=C/f'assets/{g}/foundation-cleanup/{pose}-weapon.png';Image.fromarray(a).save(dest)
  props.append({'gender':g,'pose':pose,'source':str(source.relative_to(C)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'affine':m.tolist(),'primary':definition['primary'],'support':definition.get('support'),'output':str(dest.relative_to(C))})
  definition.update(image=str(dest.relative_to(C)),size=[W,H],scale=1,angle=0,offset=[0,0],art='complete existing material-only project prop, independently registered; no donor skin')
  definition.pop('stock',None);definition.pop('trigger',None)
  if pose=='rifle':
   definition['stock']=(m@np.array([240,607,1]))[:2].tolist()
   prior=json.loads((R/'review/avatar-core-lobby-rework/prop-registration.json').read_text());trigger=(np.array(prior['similarity'])@np.array([585,285,1]))[:2]
   definition['trigger']=(m@np.r_[trigger,1])[:2].tolist()
 p.write_text(json.dumps(cfg,indent=2,sort_keys=True)+'\n')
(O/'Evidence/prop-export.json').write_text(json.dumps(props,indent=2)+'\n')
# Preserve original base and every original partition; new runtime copies erase
# ONLY documented weak remote alpha, not anatomy or natural edge antialiasing.
a=np.array(Image.open(R/'base_male.png').convert('RGBA'));alpha=a[:,:,3];d=ndi.distance_transform_edt(~(alpha>=32));remove=(alpha>0)&(alpha<=16)&(d>4);labels,n=ndi.label(alpha>0,np.ones((3,3)));peaks=np.array(ndi.maximum(alpha,labels,range(n+1)));remove|=np.isin(labels,np.flatnonzero(peaks<=16))&(labels>0)
# Removing a faint bridge can expose an additional all-weak island.
temp=alpha.copy();temp[remove]=0
labels,n=ndi.label(temp>0,np.ones((3,3)));peaks=np.array(ndi.maximum(temp,labels,range(n+1)));remove|=np.isin(labels,np.flatnonzero(peaks<=16))&(labels>0)
cleanbase=a.copy();cleanbase[remove]=0;folder=C/'assets/male/foundation-cleanup';Image.fromarray(cleanbase).save(folder/'base-runtime.png')
rig=json.loads((C/'rigs/male_rig.json').read_text());cfg=json.loads((C/'male-preview.json').read_text());surfaces={};runtime=[]
entries=[(k,s['image'],s['bounds']) for k,s in rig['segments'].items()]
for side,mesh in rig['skinMeshes'].items():entries.extend([(side+'ArmSkin',mesh['image'],mesh['bounds']),(side+'HandSkin',mesh['handImage'],mesh['bounds'])])
for key,path,bounds in entries:
 old=np.array(Image.open(C/path).convert('RGBA'));b=old.copy();x,y,x1,y1=bounds;region=remove[y:y1,x:x1];b[region]=0
 dest=folder/(key+'-runtime.png');Image.fromarray(b).save(dest);surfaces[key]=str(dest.relative_to(C));runtime.append({'key':key,'source':path,'output':surfaces[key],'removed_pixels':int(np.any(old!=b,axis=2).sum())})
cfg['runtimeSurfaces']=surfaces;cfg['runtimeSource']='assets/male/foundation-cleanup/base-runtime.png';(C/'male-preview.json').write_text(json.dumps(cfg,indent=2,sort_keys=True)+'\n')
Image.fromarray((remove*255).astype('uint8')).save(O/'Evidence/base-male-removed-alpha-mask.png');(O/'Evidence/runtime-alpha-cleanup.json').write_text(json.dumps({'source_sha256':hashlib.sha256((R/'base_male.png').read_bytes()).hexdigest(),'removed_pixels':int(remove.sum()),'all_removed_alpha_max':int(alpha[remove].max()),'all_other_pixels_exact':bool(np.array_equal(cleanbase[~remove],a[~remove])),'surfaces':runtime},indent=2)+'\n')

# Replay the later source-owned partition corrections after historical exports.
if (R/'review/avatar-requested-corrections/Inputs/primary-task.txt').exists():
 import subprocess,sys
 subprocess.run([sys.executable,str(R/'tools/prepare-requested-anatomy.py')],cwd=R,check=True)
# Reapply the later explicitly selected RGB-only arm derivatives after historical exports.
if (R/'review/avatar-selective-merge/AUDIT-BEFORE-EDIT.md').exists():
 import subprocess,sys
 subprocess.run([sys.executable,str(R/'tools/prepare-selective-arms.py')],cwd=R,check=True)
