"""Remove only disconnected <=20px islands whose maximum alpha is <=8.
8-connected labelling preserves diagonal antialiasing. Original PNGs and rig stay read-only.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'avatar-core';OUT=ROOT/'review/male-exact-reference-pass';OUT.mkdir(parents=True,exist_ok=True)
rig=json.loads((CORE/'rigs/male_rig.json').read_text());records=[];overrides={}
for pose,sides in rig['poseArt'].items():
 for side,art in sides.items():
  for key in ['image','frontImage']:
   source=CORE/art[key];a=np.array(Image.open(source));b=a.copy();labels,n=ndi.label(a[:,:,3]>0,structure=np.ones((3,3)));removed=[]
   for i in range(1,n+1):
    island=labels==i;size=int(island.sum());maximum=int(a[:,:,3][island].max())
    if size<=20 and maximum<=8:
     y,x=np.where(island);removed.append({'pixels':size,'max_alpha':maximum,'bbox_local':[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]});b[island]=0
   if not removed:continue
   dest=CORE/'assets/male/exact-pass'/f'{pose}-{side}-{key}.png';dest.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(b).save(dest)
   slot=('art-front-' if key=='frontImage' else 'art-')+pose+'-'+side;overrides[slot]=str(dest.relative_to(CORE))
   records.append({'slot':slot,'source':str(source.relative_to(ROOT)),'output':str(dest.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'removed_islands':removed,'changed_pixels':int(np.any(a!=b,axis=2).sum()),'anatomy_changed':False})
p=CORE/'male-preview.json';cfg=json.loads(p.read_text());cfg['poseArtSurfaces']=overrides;p.write_text(json.dumps(cfg,indent=2)+'\n')
(OUT/'alpha-cleanup.json').write_text(json.dumps(records,indent=2)+'\n');print(sum(r['changed_pixels'] for r in records),'low-alpha disconnected pixels removed from derivative surfaces only')
