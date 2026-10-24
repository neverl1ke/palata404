"""Source-owned internal seam reserve and female breast ownership; no repaint.
Original partitions, approved bases and rigs are never overwritten.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';O=R/'review/avatar-requested-corrections';records=[]
for g in ['male','female']:
 rig=json.loads((C/f'rigs/{g}_rig.json').read_text());cfg=json.loads((C/f'{g}-preview.json').read_text());src=np.array(Image.open(C/(cfg.get('runtimeSource') or rig['source'])).convert('RGBA'));folder=C/f'assets/{g}/requested-corrections';folder.mkdir(exist_ok=True)
 def expand(path,bounds):
  out=np.zeros_like(src);x,y,x1,y1=bounds;out[y:y1,x:x1]=np.array(Image.open(C/path).convert('RGBA'));return out
 old={k:expand(f'assets/male/foundation-cleanup/{k}-runtime.png' if g=='male' else s['image'],s['bounds']) for k,s in rig['segments'].items()}
 # Original source pixels in the breast belong to the torso, not the arm.
 transfer=np.zeros(src.shape[:2],bool)
 if g=='female':
  m=Image.new('1',(941,1672));d=ImageDraw.Draw(m)
  d.polygon([(343,395),(331,425),(328,453),(331,479),(343,501),(360,501),(360,395)],fill=1)
  d.polygon([(600,395),(610,418),(620,441),(623,464),(617,487),(602,505),(580,505),(580,395)],fill=1)
  rgb=src[:,:,:3].astype(int)
  garment=(rgb[:,:,0]-rgb[:,:,2]<24)&(rgb[:,:,:3].max(axis=2)<160)
  transfer=np.array(m)&garment&((old['rightUpper'][:,:,3]>0)|(old['leftUpper'][:,:,3]>0))
 yy,xx=np.indices(src.shape[:2]);body=old['torso'][:,:,3]>0;newbody=body|transfer;rootzone=(yy>=300)&(yy<=530);allarms=(old['rightUpper'][:,:,3]>0)|(old['leftUpper'][:,:,3]>0)
 torso_reserve=binary_dilation(newbody,iterations=2)&allarms&rootzone
 for k in ['torso','rightUpper','leftUpper']:
  part=old[k].copy()
  if k=='torso':part[transfer|torso_reserve]=src[transfer|torso_reserve]
  else:
   part[transfer]=0
   reserve=binary_dilation(part[:,:,3]>0,iterations=2)&newbody&rootzone
   part[reserve]=src[reserve]
  x,y,x1,y1=rig['segments'][k]['bounds'];path=folder/f'{k}.png';Image.fromarray(part[y:y1,x:x1]).save(path);cfg.setdefault('runtimeSurfaces',{})[k]=str(path.relative_to(C))
 for side in ['right','left']:
  mesh=rig['skinMeshes'][side];key=side+'ArmSkin';path=mesh['image']
  if g=='male':path=f'assets/male/foundation-cleanup/{key}-runtime.png'
  part=expand(path,mesh['bounds']);part[transfer]=0
  reserve=binary_dilation(part[:,:,3]>0,iterations=2)&newbody&rootzone;part[reserve]=src[reserve]
  x,y,x1,y1=mesh['bounds'];p=folder/f'{key}.png';Image.fromarray(part[y:y1,x:x1]).save(p);cfg.setdefault('runtimeSurfaces',{})[key]=str(p.relative_to(C))
 (C/f'{g}-preview.json').write_text(json.dumps(cfg,indent=2,sort_keys=True)+'\n')
 Image.fromarray((transfer*255).astype('uint8')).save(O/'Evidence'/f'{g}-ownership-transfer.png')
 records.append({'gender':g,'breast_source_pixels_transferred':int(transfer.sum()),'torso_internal_reserve_pixels':int(torso_reserve.sum()),'reserve_width_px':2,'reserve_y':[300,530],'source_sha256':hashlib.sha256((R/f'base_{g}.png').read_bytes()).hexdigest(),'method':'exact source RGBA copied across internal partition; no invented anatomy'})
(O/'Evidence/anatomy-export.json').write_text(json.dumps(records,indent=2)+'\n');print(records)
