"""Reproducible local hidden-surface repaint, ownership repair, no base edits.
Run after prepare-reference-arm-art.py. Generated sources are immutable review
inputs; masks limit their use to the previously concealed anatomical surfaces.
"""
from pathlib import Path
import json,hashlib,io,subprocess,importlib.util
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'avatar-core';OUT=ROOT/'review/weapon-independent-anatomy';SRC=OUT/'Sources';SRC.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('contact',ROOT/'tools/reference-contact-surfaces.py');contact=importlib.util.module_from_spec(spec);spec.loader.exec_module(contact)
BASELINE='184e392';rig=json.loads((CORE/'rigs/male_rig.json').read_text());base=np.array(Image.open(ROOT/'base_male.png'))
def old(path):
 fixture=SRC/'Baseline'/path
 if fixture.exists():
  data=fixture.read_bytes();expected=json.loads((SRC/'Baseline/SHA256.json').read_text())['files'][path];assert hashlib.sha256(data).hexdigest()==expected,path;return data
 return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT)
rig['poseArt']=json.loads(old('avatar-core/rigs/male_rig.json'))['poseArt']
def full(art,key):
 a=np.zeros((1672,941,4),np.uint8);x,y,x1,y1=art['mesh']['bounds'];a[y:y1,x:x1]=np.array(Image.open(io.BytesIO(old('avatar-core/'+art[key]))));return a
records=[]
(CORE/'assets/weapons/reference-art/rifle.png').write_bytes(old('avatar-core/assets/weapons/reference-art/rifle.png'))
def repaint(pose,side,filename,box,points,source_box=None):
 art=rig['poseArt'][pose][side];a=full(art,'image');front=full(art,'frontImage');im=Image.open(SRC/filename).convert('RGB');rgb=np.zeros((1672,941,3),np.uint8);x,y,x1,y1=box
 if source_box:im=im.resize((170,255)).crop((source_box[0]-160,source_box[1]-200,source_box[2]-160,source_box[3]-200))
 rgb[y:y1,x:x1]=np.array(im.resize((x1-x,y1-y),Image.Resampling.LANCZOS));m=contact.curved_mask(points);warm=np.clip((rgb[:,:,0].astype(float)-rgb[:,:,2]-14)/12,0,1);m*=warm
 if pose=='rifle' and side=='left':
  # A full lower-wrist matte, not a polygon clipping through the palm. Its
  # foreground is the local repaint's own skin contour, blended only at top.
  yy,xx=np.indices(m.shape);region=(xx>=635)&(xx<=750)&(yy>=620)&(yy<=745)
  silhouette=contact.curved_mask([(647,620),(722,620),(741,655),(734,683),(721,708),(714,732),(710,750),(682,754),(658,735),(649,714),(646,677)])
  m=warm*region*silhouette;wtop=np.clip((yy-620)/18,0,1);m*=wtop
  replace=region&(yy>=670)
  a[replace]=0
 if pose=='pistol':
  yy,xx=np.indices(m.shape);broken=(xx>=215)&(xx<=257)&(yy<294)&(yy>=250)
  a[broken]=0;front[broken]=0
 Image.fromarray(np.rint(m*255).astype('uint8')).save(OUT/f'{pose}-{side}-repaint-mask.png')
 # Keep source fingers in the FRONT pass. Only their missing back surface is
 # repainted. The back coverage is a real painted palm, never nearest-neighbor.
 inside=ndi.distance_transform_edt(m>.5);w=np.clip(inside/3,0,1)*m
 oldalpha=a[:,:,3]/255;exposed=(oldalpha<.5)&(m>.5);w[exposed]=m[exposed]
 # Tone correction is restricted to generated pixels, not the old hand.
 valid=(m>.5)&(oldalpha>.9)&(a[:,:,0]>100)&(a[:,:,0].astype(int)-a[:,:,2]>25)
 if valid.any():
  correction=float(np.median(a[valid,:3].astype(float)-rgb[valid].astype(float)));correction=np.clip(correction,-18,18);rgb=np.clip(rgb.astype(float)+correction,0,255).astype('uint8')
 a[:,:,:3]=np.rint(a[:,:,:3]*(1-w[:,:,None])+rgb*w[:,:,None]);a[:,:,3]=np.maximum(a[:,:,3],np.rint(m*255).astype('uint8'))
 # Palm-edge backdrop crumbs are local extraction remnants. Suppress only
 # isolated <4px islands, never a connected finger or natural grip aperture.
 if pose=='rifle' and side=='left':
  yy,xx=np.indices(m.shape);edge_zone=(xx>=714)&(xx<=729)&(yy>=719)&(yy<=761)
  # These dark fore-end pixels were assigned to the finger matte. Return
  # their exact native paint to the independent item instead of deleting it.
  prop_path=CORE/'assets/weapons/reference-art/rifle.png';prop=np.array(Image.open(prop_path));original_front=front.copy()
  material=edge_zone&(front[:,:,:3].max(2)<120)&(front[:,:,3]>0)
  for im in [a,front]:im[material]=0
  prop[material]=original_front[material];Image.fromarray(prop).save(prop_path)
 for key,im in [('image',a),('frontImage',front)]:
  labels,n=ndi.label(im[:,:,3]>16,structure=np.ones((3,3)));sizes=np.bincount(labels.ravel());small=(sizes<4);small[0]=False;im[small[labels]]=0
  bx,by,bx1,by1=art['mesh']['bounds'];Image.fromarray(im[by:by1,bx:bx1]).save(CORE/art[key])
 # New hidden anatomy occupies previously empty mesh cells. Rebuild coverage
 # from the SAME vertices/weights; no joint or bind matrix is changed.
 vertices=art['mesh']['vertices'];ys=sorted({v[1] for v in vertices});nx=sum(v[1]==ys[0] for v in vertices);tri=[]
 for row in range(len(ys)-1):
  for col in range(nx-1):
   q=row*nx+col;tri.extend([[q,q+1,q+nx],[q+1,q+nx+1,q+nx]])
 art['mesh']['triangles']=tri;art['mesh']['handTriangles']=tri;art['surfacePreparation']='local-repaint-review'
 records.append({'pose':pose,'side':side,'source':filename,'source_sha256':hashlib.sha256((SRC/filename).read_bytes()).hexdigest(),'box':box,'points':points,'front_preservation':'accepted curled fingers retained; broken pistol tip replaced; rifle material returned to prop; detached extraction crumbs removed'})
repaint('rifle','left','rifle-left-local-repaint.png',(600,580,800,810),[(665,650),(684,656),(711,669),(733,678),(735,695),(725,718),(709,732),(686,730),(667,715),(660,692)])
# The short trigger digit keeps its original fingertip and pose; only its
# missing proximal surface is reconstructed behind the unchanged front layer.
repaint('pistol','right','pistol-local-repaint.png',(219,260,256,310),[(224,269),(231,262),(241,262),(251,268),(253,279),(246,291),(245,307),(229,309),(220,292)],source_box=(208,240,241,306))
repaint('rifle','right','rifle-right-local-repaint.png',(315,545,530,705),[(342,618),(362,623),(388,633),(410,644),(418,657),(407,664),(386,655),(364,649),(346,640)])
repaint('melee','right','melee-local-repaint.png',(155,780,290,960),[(219,853),(231,856),(239,870),(234,888),(223,909),(213,912),(210,897),(213,876)])
# Return the thigh-edge pixels accidentally assigned to the left arm to LOWER.
# The rectangle is only a localization. Ownership is taken from the actual
# source alpha in the old arm, not filled with an invented color.
mesh=rig['skinMeshes']['left'];x,y,x1,y1=mesh['bounds'];arm=np.array(Image.open(io.BytesIO(old('avatar-core/assets/male/leftArmSkin.png'))));transfer=np.zeros((1672,941),bool);transfer[840:1040,660:680]=True;owned=np.zeros_like(transfer);owned[y:y1,x:x1]=arm[:,:,3]>0;transfer &= owned
for sid,seg in rig['segments'].items():
 bx,by,bx1,by1=seg['bounds'];a=np.array(Image.open(io.BytesIO(old('avatar-core/'+seg['image']))));m=transfer[by:by1,bx:bx1]
 if sid.startswith('left'):a[m]=0
 elif sid=='lower':a[m]=base[by:by1,bx:bx1][m]
 else:continue
 if not m.any():
  (CORE/seg['image']).write_bytes(old('avatar-core/'+seg['image']))
 else:Image.fromarray(a).save(CORE/seg['image'])
 seg['sha256']=hashlib.sha256((CORE/seg['image']).read_bytes()).hexdigest()
for name in ['leftArmSkin','leftHandSkin']:
 a=np.array(Image.open(io.BytesIO(old('avatar-core/assets/male/'+name+'.png'))));a[transfer[y:y1,x:x1]]=0;Image.fromarray(a).save(CORE/'assets/male'/f'{name}.png')
Image.fromarray((transfer*255).astype('uint8')).save(OUT/'thigh-ownership-transfer-mask.png')
(OUT/'repaint-registration.json').write_text(json.dumps({'baseline':BASELINE,'operations':records,'transferred_thigh_pixels':int(transfer.sum()),'original_base_unchanged':True},indent=2)+'\n')
# Historical intermediate replayers copy canonical atlases into these legacy
# caches. Preserve those historical bytes; current runtime uses canonical files.
for n in ['left-arm-source','left-open-hand-source']:
 (CORE/'assets/male/hands'/f'{n}.png').write_bytes(old('avatar-core/assets/male/hands/'+n+'.png'))
# Runtime formerly selected the historical hand-source copies, not the
# canonical partition atlases. Point it at the corrected source atlases.
rig['skinMeshes']['left']['image']='assets/male/leftArmSkin.png'
rig['skinMeshes']['left']['handImage']='assets/male/leftHandSkin.png'
# Explicit follow-up: remove the 16.4% melee upper-arm foreshortening.
# The existing corrective art keeps its original inverse bind; only the
# runtime skeletal target changes. Fingers and item follow the same grip.
rig['anatomyProjection']['melee']['right']=[1,1]
rig['poses']['melee']['right']=[241,906]
# Shoulder cap belongs to the torso, not the newly lengthened humerus.
for v in rig['poseArt']['melee']['right']['mesh']['vertices']:
 t=max(0,min(1,(v[1]-365)/60));v[2]*=t*t*(3-2*t)
(CORE/'rigs/male_rig.json').write_text(json.dumps(rig,indent=2)+'\n')
print('Prepared local painted back surfaces and transferred',int(transfer.sum()),'thigh pixels to lower.')

# Latest user-authorized local contour pass and female donor stage.
if (ROOT/'review/female-donor-arm-pass/Sources/rifle.png').exists():
 import subprocess,sys
 for stage in ['finish-male-contact-contours.py','prepare-female-donor-arms.py']:
  subprocess.run([sys.executable,str(ROOT/'tools'/stage)],cwd=ROOT,check=True)
