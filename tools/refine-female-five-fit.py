"""User-authorized local PNG deformation. No generation, face edits or global stretch."""
from pathlib import Path
import json,hashlib,re
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import map_coordinates
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/female-five-fit-audit';AS=ROOT/'assets/wardrobe/hair/female-five'
def warp(im, maps):
 a=np.array(im).astype(np.float64);out=a.copy()
 # Premultiplied sampling prevents transparent RGB from producing dark edge halos.
 prem=a[:,:,:3]*(a[:,:,3:4]/255)
 for y,xmap in maps.items():
  alpha=map_coordinates(a[:,:,3],np.array([np.full(941,y),xmap]),order=1,mode='constant',cval=0,prefilter=False)
  rgb=np.stack([map_coordinates(prem[:,:,c],np.array([np.full(941,y),xmap]),order=1,mode='constant',cval=0,prefilter=False) for c in range(3)],axis=1)
  out[y,:,3]=alpha;out[y,:,:3]=np.divide(rgb,alpha[:,None]/255,out=np.zeros_like(rgb),where=alpha[:,None]>0)
 out=np.rint(out).clip(0,255).astype('uint8');out[out[:,:,3]==0]=0
 return Image.fromarray(out)
records=[]
for key in ['pixie','jaw-bob','long-waves','high-ponytail','braided-updo']:
 src=R/'before/assets'/f'{key}.png';im=Image.open(src).convert('RGBA');a=np.array(im)[:,:,3];maps={};details={}
 if key=='pixie':
  # Measured source edges and female skull/temple landmarks, not a global percentage.
  ys=[78,85,95,105,115,125,135,145,155,164]
  left=[0,0,3,1,6,9,14,13,13,13];right=[0,1,5,6,8,15,13,16,16,16]
  dl=PchipInterpolator(ys,left);dr=PchipInterpolator(ys,right)
  for y in range(79,164):
   xx=np.flatnonzero(a[y]>0)
   if not len(xx):continue
   sl=np.flatnonzero(a[y,:438]>=128);sr=np.flatnonzero(a[y,508:]>=128)+508
   l=min(int(sl[0]) if len(sl) else int(xx[0]),430);r=max(int(sr[-1]) if len(sr) else int(xx[-1]),515);sx=[0,350,l,437.5,507.5,r,600,940];dx=[0,350,l-float(dl(y)),437.5,507.5,r+float(dr(y)),600,940]
   inv=PchipInterpolator(dx,sx)(np.arange(941));inv[:350]=np.arange(350);inv[438:508]=np.arange(438,508);inv[600:]=np.arange(600,941);maps[y]=inv
  details={'rows':ys,'left_outward_px':left,'right_outward_px':right,'fixed_central_x':[438,507],'unchanged_crown_y_max':78,'rationale':'head row125 x399..546 vs hair x404..535; add natural temple volume while keeping crown and central fringe fixed'}
 if key=='long-waves':
  ys=[110,120,130,135,142,148,155,170,185];delta=[0,4,12,16,17,15,9,3,0];d=PchipInterpolator(ys,delta)
  for y in range(111,185):
   sx=[0,400,450,480,940];dx=[0,400,450-float(d(y)),480,940];inv=PchipInterpolator(dx,sx)(np.arange(941));inv[:400]=np.arange(400);inv[480:]=np.arange(480,941);maps[y]=inv
  details={'rows':ys,'left_outward_px':delta,'affected_x':[400,479],'rationale':'original alpha151 at left iris (445,142); move crossing foreground strand outward while retaining lower tresses and neck framing'}
 result=warp(im,maps) if maps else im
 # Copy explicitly protected pixels exactly rather than subjecting them to float roundoff.
 ar=np.array(result);before=np.array(im)
 if key=='pixie':ar[:79]=before[:79];ar[164:]=before[164:];ar[:,438:508]=before[:,438:508];ar[:,:350]=before[:,:350];ar[:,600:]=before[:,600:]
 if key=='long-waves':ar[:111]=before[:111];ar[185:]=before[185:];ar[:,:400]=before[:,:400];ar[:,480:]=before[:,480:]
 removed=0
 if maps:
  alpha=ar[:,:,3];far=(alpha>0)&(alpha<=16)&(ndi.distance_transform_edt(alpha<32)>4);removed=int(far.sum());ar[far]=0
  labels,n=ndi.label(ar[:,:,3]>0,np.ones((3,3)))
  weak=np.isin(labels,np.flatnonzero(ndi.maximum(ar[:,:,3],labels,np.arange(1,n+1))<=16)+1);removed+=int(weak.sum());ar[weak]=0
 dest=AS/f'{key}.png'
 if maps:Image.fromarray(ar).save(dest,optimize=True)
 else:dest.write_bytes(src.read_bytes())
 changed=np.any(before!=ar,axis=2)
 record={'key':key,'path':str(dest.relative_to(ROOT)),'before_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'changed_pixels':int(changed.sum()),'resampled_weak_alpha_removed':removed,'geometry':details};records.append(record);print(key,record['changed_pixels'],record['after_sha256'][:8])
(R/'corrections.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
# Update registration without hiding the raw-source registration history.
p=ROOT/'review/female-five-hairstyles/registration.json';reg=json.loads(p.read_text())
for r in reg:
 c=next(v for v in records if v['key']==r['key']);r['sha256']=c['after_sha256'];r['post_registration_correction']=c['geometry'];r['alpha_bbox']=Image.open(ROOT/r['path']).getchannel('A').getbbox()
p.write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
# Change only the URLs of the two corrected sprites.
p=ROOT/'paper-doll-data.js';s=p.read_text()
for c in records:s=re.sub(re.escape(c['path'])+r'\?v=[a-f0-9]+',c['path']+'?v='+c['after_sha256'][:8],s)
p.write_text(s)
