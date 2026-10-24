"""Register a separate illustrated knife; preserve existing hands and shared female prop."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-exact-reference-pass';CORE=ROOT/'avatar-core';source=OUT/'Sources/knife-working.png'
a=np.array(Image.open(source).convert('RGBA'));a[:,:,3]=np.clip(np.rint(a[:,:,3].astype(float)*255/253),0,255);solid=a[:,:,3]>=128;distance,indices=ndi.distance_transform_edt(~solid,return_indices=True);a[(distance>1.5)&(a[:,:,3]<128)]=0;edge=(a[:,:,3]>0)&(a[:,:,3]<128);a[edge,:3]=a[indices[0][edge],indices[1][edge],:3];a[a[:,:,3]==0]=0
bbox=Image.fromarray(a).getbbox();x,y,x1,y1=bbox;scale=.14;im=Image.fromarray(a).crop(bbox).resize((round((x1-x)*scale),round((y1-y)*scale)),Image.Resampling.LANCZOS);a=np.array(im);a[a[:,:,3]==0]=0;im=Image.fromarray(a);dest=CORE/'assets/weapons/male-exact/knife.png';dest.parent.mkdir(exist_ok=True);im.save(dest)
sx=im.width/(x1-x);sy=im.height/(y1-y);primary=[(513-x)*sx,(350-y)*sy]
p=CORE/'male-preview.json';c=json.loads(p.read_text());c['weapons']['melee'].update(size=list(im.size),primary=primary,image=str(dest.relative_to(CORE)),scale=1,angle=140,art='new illustrated test knife, independent RGBA prop; requires visual approval');p.write_text(json.dumps(c,indent=2)+'\n')
(OUT/'knife-registration.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output':str(dest.relative_to(ROOT)),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_bbox':bbox,'size':list(im.size),'primary_source':[513,350],'primary':primary,'scale_xy_after_integer_rounding':[sx,sy],'angle_definition':140,'male_pose_angle':195,'resulting_angle':335,'hands_unchanged':True,'female_shared_weapon_unchanged':True},indent=2)+'\n');print(im.size,primary)
