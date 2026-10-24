"""Register an existing portrait retouch to the approved facial landmarks.
Only RGB is consumed; source alpha and head placement are retained.
"""
from PIL import Image
import numpy as np,json,argparse
from scipy import ndimage as ndi,optimize
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--draft',type=Path,default=ROOT/'review/paper-doll-targeted-fix/sources/male-alternative-repaint-draft.png');args=p.parse_args();r=ROOT/'review/paper-doll-targeted-fix/sources';src=np.array(Image.open(args.snapshot/'assets/wardrobe/faces/male_alternative_head.png').crop((365,20,585,285)).convert('RGBA'));gen=np.array(Image.open(args.draft).convert('RGBA').resize((220,265),Image.Resampling.LANCZOS))
_,idx=ndi.distance_transform_edt(gen[:,:,3]<240,return_indices=True);rgb=gen[idx[0],idx[1],:3].astype(float);y,x=np.mgrid[:265,:220];mask=((x-110)/70)**2+((y-150)/85)**2<1
lum=lambda a:a@np.array([.2126,.7152,.0722])
old=lum(src[:,:,:3].astype(float));old=ndi.gaussian_filter(old,.7)-ndi.gaussian_filter(old,5);old=old/max(np.std(old[mask]),.001)
def warp(params):
 s,tx,ty,angle=params;angle*=np.pi/180;xx=(x-110-tx)/s;yy=(y-130-ty)/s;xx,yy=np.cos(angle)*xx+np.sin(angle)*yy+110,-np.sin(angle)*xx+np.cos(angle)*yy+130
 return np.stack([ndi.map_coordinates(rgb[:,:,c],[yy,xx],order=1,mode='nearest') for c in range(3)],axis=2)
def loss(p):
 z=lum(warp(p));z=ndi.gaussian_filter(z,.7)-ndi.gaussian_filter(z,5);z=z/max(np.std(z[mask]),.001);return np.mean((z[mask]-old[mask])**2)
res=optimize.minimize(loss,[1,1,-1,0],method='Powell',bounds=[(.97,1.03),(-5,5),(-5,5),(-1,1)],options={'maxiter':60});print(res.x,res.fun)
aligned=warp(res.x);Image.fromarray(np.uint8(np.clip(aligned,0,255))).save(r/'male-alternative-painted-rgb.png');(r/'portrait-registration.json').write_text(json.dumps({'source_commit':'8bcf1830429008113c145e15c016a9bc709e35a1','target':'assets/wardrobe/faces/male_alternative_head.png','style_reference':'assets/wardrobe/faces/male_young_head.png','draft':'male-alternative-repaint-draft.png','runtime_geometry':'Original full-frame alpha and facial-feature emphasis; independent edge cleanup only','crop':[365,20,585,285],'scale':float(res.x[0]),'translation':res.x[1:3].tolist(),'rotation_degrees':float(res.x[3]),'normalized_structure_error':float(res.fun)},indent=2)+'\n')
