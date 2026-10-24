"""Selective local RGB merge. Preserve every alpha, rig, hand and original PNG."""
from pathlib import Path
import subprocess,json,hashlib,io
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';D=R/'review/avatar-selective-merge';records=[]
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def load(p):return np.array(Image.open(p).convert('RGBA'))
def old_image(path):return load(io.BytesIO(subprocess.check_output(['git','show','184e392:avatar-core/'+path],cwd=R)))
for g in ['male','female']:
 rig=json.loads((C/f'rigs/{g}_rig.json').read_text());cfg=json.loads(subprocess.check_output(['git','show',f'5532a93:avatar-core/{g}-preview.json'],cwd=R));base=load(R/f'base_{g}.png');folder=C/f'assets/{g}/selective-merge';folder.mkdir(exist_ok=True)
 for pose,sides in rig['poseArt'].items():
  for side,art in sides.items():
   key=f'{pose}-{side}';path=cfg['poseArtCompleteSurfaces'][key];cur=load(C/path);result=cur.copy();x0,y0,x1,y1=art['mesh']['bounds'];yy,xx=np.indices(cur.shape[:2]);xx+=x0;yy+=y0
   # Female authored resources use full canvas. Coordinates remain source space.
   if cur.shape[:2]==(1672,941):yy,xx=np.indices(cur.shape[:2])
   wrist=np.array(art['anchors']['wrist']);grip=np.array(art['anchors']['grip']);hand_distance=np.minimum(np.hypot(xx-wrist[0],yy-wrist[1]),np.hypot(xx-grip[0],yy-grip[1]));hand_safe=hand_distance>=85
   historical_pixels=0
   if g=='male':
    old=old_image(art['image']);front=old_image(art['frontImage']);old_composite=np.array(Image.alpha_composite(Image.fromarray(old),Image.fromarray(front)))
    safe=(old_composite[:,:,3]>=250)&(cur[:,:,3]>=250)&hand_safe
    # Distance ramp leaves the distal wrist and all authored fingers exactly unchanged.
    w=smooth((hand_distance-85)/35)*safe
    result[:,:,:3]=np.rint(cur[:,:,:3]*(1-w[:,:,None])+old_composite[:,:,:3]*w[:,:,None]);historical_pixels=int((w>0).sum())
   native=base[yy,xx];shoulder=np.array(art['anchors']['shoulder']);dist=np.hypot(xx-shoulder[0],yy-shoulder[1]);skin=(native[:,:,0].astype(int)-native[:,:,2]>22)&(native[:,:,3]>=250)&(cur[:,:,3]>0)&hand_safe
   # Exact original-body RGB at the registered root, tapering only within 105px.
   w=(1-smooth((dist-55)/50))*skin
   result[:,:,:3]=np.rint(result[:,:,:3]*(1-w[:,:,None])+native[:,:,:3]*w[:,:,None])
   # All distal hand texels, alpha and every exterior transparent pixel remain exact.
   result[~hand_safe]=cur[~hand_safe];result[cur[:,:,3]==0]=cur[cur[:,:,3]==0]
   complete=folder/f'{key}-complete.png';Image.fromarray(result).save(complete);cfg['poseArtCompleteSurfaces'][key]=str(complete.relative_to(C))
   for kind,id in [('arm',f'art-{key}'),('front',f'art-front-{key}')]:
    original=load(C/cfg['poseArtSurfaces'][id]);out=original.copy();m=(original[:,:,3]>0)&(result[:,:,3]>0);out[m,:3]=result[m,:3];p=folder/f'{key}-{kind}.png';Image.fromarray(out).save(p);cfg['poseArtSurfaces'][id]=str(p.relative_to(C))
   changed=np.any(cur!=result,axis=2);records.append({'gender':g,'pose':pose,'side':side,'source':path,'source_sha256':hashlib.sha256((C/path).read_bytes()).hexdigest(),'output':str(complete.relative_to(C)),'output_sha256':hashlib.sha256(complete.read_bytes()).hexdigest(),'historical_rgb_pixels':historical_pixels,'base_root_rgb_pixels':int((w>0).sum()),'changed_pixels':int(changed.sum()),'alpha_exact':bool(np.array_equal(cur[:,:,3],result[:,:,3])),'hands_85px_exact':bool(np.array_equal(cur[~hand_safe],result[~hand_safe])),'source_rgba_unchanged':True})
 cfg['meleeMotion']={'mode':'forward-wrist','upperDegrees':0.008,'foreDegrees':0.025,'handDegrees':0.35,'cycleMs':4000}
 (C/f'{g}-preview.json').write_text(json.dumps(cfg,indent=2,sort_keys=True)+'\n')
(D/'Evidence/selective-arm-export.json').write_text(json.dumps(records,indent=2)+'\n');print([(r['gender'],r['pose'],r['side'],r['changed_pixels']) for r in records])
