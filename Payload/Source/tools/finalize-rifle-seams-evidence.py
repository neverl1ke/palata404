"""Postprocess measured matrices using actual alpha hull, not canvas bounds."""
from pathlib import Path
import json,numpy as np,cv2
from PIL import Image
from scipy.spatial import ConvexHull
R=Path(__file__).resolve().parents[1];D=R/'review/rifle-seams';P=D/'Evidence/browser-matrix.json';d=json.loads(P.read_text());image=np.array(Image.open(R/'avatar-core/assets/weapons/user-ak47-20261026/ak47-runtime-opaque.png'));y,x=np.where(image[:,:,3]>0);points=np.c_[x,y];points=points[ConvexHull(points).vertices];points=np.c_[points,np.ones(len(points))]
for c in d['cases']:
 positions=[]
 for v in c['samples']:
  m=v['weaponMatrix'];M=np.array([[m[0],m[2],m[4]],[m[1],m[3],m[5]]]);positions.append(points@M.T)
 q=np.array(positions);mid=(q.max(0)+q.min(0))/2;c['actual_alpha_hull_radius_px']=float(np.linalg.norm(q-mid,axis=2).max());c['actual_alpha_hull_peak_to_peak_axes_px']=np.ptp(q,axis=0).max(axis=0).tolist()
d['amplitude_definition']='Actual alpha>0 convex hull; max distance of each point from midpoint of its extrema across481 samples. Control rectangle metric is separate.';P.write_text(json.dumps(d,indent=2)+'\n')
rows=[]
for g in ['male','female']:
 c=next(c for c in d['cases'] if c['gender']==g and c['scale']==1 and c['mode']=='standard');m=c['samples'][0]['weaponMatrix'];M=np.array([[m[0],m[2],m[4]],[m[1],m[3],m[5]]]);alpha=cv2.warpAffine(image[:,:,3],M,(941,1672));mask=cv2.erode((alpha==255).astype('uint8'),np.ones((5,5)))>0
 a=np.array(Image.open(D/f'Gallery/background-{g}-white-True.webp').convert('RGBA'));b=np.array(Image.open(D/f'Gallery/background-{g}-black-True.webp').convert('RGBA'));delta=abs(a.astype(int)-b.astype(int));row=dict(gender=g,confirmed_opaque_native_pixels=int(mask.sum()),max_final_background_dependence=int(delta[mask,:3].max()),changed_pixels=int(np.count_nonzero(np.any(delta[mask,:3]>0,axis=1))));assert row['max_final_background_dependence']==0,row;rows.append(row)
(D/'Evidence/weapon-background-isolation.json').write_text(json.dumps({'method':'Actual black/white final renders; current time0 matrix, alpha255 projected item interior eroded2px','cases':rows},indent=2)+'\n')
pix=json.loads((D/'Evidence/compositor-pixels.json').read_text());summary={'total_samples':d['total_samples'],'protected_frames':d['protected_frames_RGBA_exact'],'opaque_front_pixel_samples':sum(c['opaque_front_samples'] for c in pix['cases']),'pixel_samples_over2_RGB':sum(c['samples_over2'] for c in pix['cases']),'max_RGB_difference':max(c['max_RGB_difference'] for c in pix['cases']),'all_mechanical_contacts_under1e_6':all(max(v['primaryError'] for v in c['samples'])<1e-6 and max(v['supportError'] for v in c['samples'])<1e-6 for c in d['cases']),'standard_hull_radius':{c['gender']:c['actual_alpha_hull_radius_px'] for c in d['cases'] if c['scale']==1 and c['mode']=='standard'},'stress_playback':'1x;2 simulation cycles=2000ms continuous video; phase slideshow is not real-time','full_wardrobe_and_historical_regression_not_run':True}
assert summary['pixel_samples_over2_RGB']==0 and summary['all_mechanical_contacts_under1e_6']
(D/'Evidence/verification-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
