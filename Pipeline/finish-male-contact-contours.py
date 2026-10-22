"""Local contour-only male follow-up; fixed skeleton, contacts and fingers."""
from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw
import numpy as np
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';O=R/'review/female-donor-arm-pass';B=O/'Baseline';Y,X=np.indices((1672,941));rig=json.loads((C/'rigs/male_rig.json').read_text())
for side,box,poly in [('right',(330,550,515,690),[(342,618),(362,620),(389,637),(397,655),(380,660),(345,644)]),('left',(620,640,740,770),[(623,699),(648,702),(666,728),(673,755),(645,756),(623,737)])]:
 edit=np.array(Image.open(O/'Retouch'/f'male-rifle-{side}-edited.png').convert('RGBA').resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS));patch=np.zeros((1672,941,4),np.uint8);patch[box[1]:box[3],box[0]:box[2]]=edit
 m=Image.new('L',(941,1672));ImageDraw.Draw(m).polygon(poly,fill=255);zone=np.array(m)/255;zone=ndi.gaussian_filter(zone,.6);art=rig['poseArt']['rifle'][side];x,y,x1,y1=art['mesh']['bounds']
 for key in ['image','frontImage']:
  path=C/art[key];fix=B/(side+'-'+key+'.png')
  if not fix.exists():fix.write_bytes(subprocess.check_output(['git','show','77199cd:avatar-core/'+art[key]],cwd=R))
  a=np.array(Image.open(fix).convert('RGBA'));old=a.copy();p=patch[y:y1,x:x1];z=zone[y:y1,x:x1];oldalpha=a[:,:,3]/255
  # Restore/trim only the demonstrated lower contour. Existing fingers and
  # all remote RGB/alpha are exact original bytes.
  near=ndi.distance_transform_edt(a[:,:,3]==0)<=2
  pa=p[:,:,3]/255*near
  new=oldalpha*(1-z)+pa*z
  if side=='left':
   src=np.array(Image.open(R/'review/male-reference-arm-art/Sources/rifle.png').convert('RGBA'));registered=np.zeros_like(src);registered[26:,10:]=src[:-26,:-10]
   # The reference confirms these are actual little-finger skin, not waste.
   # Never trim a real source-opaque digit to imitate a generated silhouette.
   protect=registered[y:y1,x:x1,3]>=240;new[protect]=np.maximum(new[protect],oldalpha[protect])
  a[:,:,:3]=np.rint((a[:,:,:3]*(oldalpha*(1-z))[:,:,None]+p[:,:,:3]*(pa*z)[:,:,None])/np.maximum(new[:,:,None],1e-8));a[:,:,3]=np.rint(new*255);a[a[:,:,3]==0]=0
  keep=(old[:,:,3]>=128)&(a[:,:,3]>0);a[keep,:3]=old[keep,:3]
  distance=ndi.distance_transform_edt(a[:,:,3]<32);remote=(a[:,:,3]>0)&(a[:,:,3]<=16)&(distance>2);a[remote]=0
  labels,n=ndi.label(a[:,:,3]>0,np.ones((3,3)));peaks=ndi.maximum(a[:,:,3],labels,range(n+1));weak_ids=np.flatnonzero(np.array(peaks)<=16);a[np.isin(labels,weak_ids)&(labels>0)]=0
  Image.fromarray(a).save(path)
 Image.fromarray(np.rint(zone*255).astype('uint8')).save(O/'Masks'/f'male-rifle-{side}-contour.png')
print('Two bounded male rifle contour repairs; skeleton and grips unchanged')
