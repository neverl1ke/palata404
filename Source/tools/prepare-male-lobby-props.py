from pathlib import Path
import json,numpy as np
from PIL import Image
from scipy import ndimage as ndi
r=Path(__file__).resolve().parents[1];core=r/'avatar-core';out=r/'review/avatar-core-lobby-rework'
a=np.array(Image.open(r/'review/avatar-core-2-weapon-pass/sources/weapon-atlas.png'));a[550:]=0
src=np.array([450,340]);dst=np.array([364,668]);z=complex(619-364,755-668)/complex(990-450,230-340)
m=np.array([[z.real,-z.imag,0],[z.imag,z.real,0],[0,0,1.]]);m[:2,2]=dst-m[:2,:2]@src
s=np.array([[24,300,1],[405,205,1],[405,240,1]],float);t=np.vstack([[240,607],[(m@p)[:2] for p in s[1:]]]);sm=np.eye(3);sm[:2]=np.linalg.solve(s,t).T
stock=a.copy();stock[:,411:]=0;body=a.copy();body[:,:400]=0
im=Image.new('RGBA',(941,1672))
for pixels,mat in [(stock,sm),(body,m)]:
 part=Image.fromarray(pixels).transform(im.size,Image.Transform.AFFINE,tuple(np.linalg.inv(mat)[:2].ravel()),Image.Resampling.BICUBIC);im=Image.alpha_composite(im,part)
a=np.array(im);solid=a[:,:,3]>=128;d,i=ndi.distance_transform_edt(~solid,return_indices=True);a[(d>1.5)&(a[:,:,3]<128)]=0;edge=(a[:,:,3]>0)&(a[:,:,3]<128);a[edge,:3]=a[i[0][edge],i[1][edge],:3];a[:,:,3]=np.clip(np.rint(a[:,:,3].astype(float)*255/254),0,255);a[a[:,:,3]==0]=0
folder=core/'assets/weapons/male-lobby';folder.mkdir(exist_ok=True);Image.fromarray(a).save(folder/'rifle.png')
p=core/'male-preview.json';cfg=json.loads(p.read_text());cfg['weapons']['rifle'].update(image='assets/weapons/male-lobby/rifle.png',size=[941,1672],primary=[364,668],support=[619,755],stock=[240,607],trigger=list((m@np.array([585,285,1]))[:2]),scale=1,angle=0)
cfg['weapons']['pistol']['primary']=[42.4,81.7]
p.write_text(json.dumps(cfg,indent=2)+'\n');(out/'prop-registration.json').write_text(json.dumps({'source':'review/avatar-core-2-weapon-pass/sources/weapon-atlas.png','similarity':m.tolist(),'stock_at_receiver_seam':sm.tolist(),'reason':'stock rests near lowered right forearm, never the shoulder','pistol_primary':[42.4,81.7]},indent=2))
