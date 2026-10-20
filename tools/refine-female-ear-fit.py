"""Second user-directed fit pass; immutable input is the approved preceding pass.
Only the three requested hairstyles are resampled, using premultiplied RGBA.
Run after refine-female-five-fit.py when rebuilding from original sources.
"""
from pathlib import Path
import hashlib,json,re
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import map_coordinates,distance_transform_edt,label,maximum
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/female-ear-fit';AS=ROOT/'assets/wardrobe/hair/female-five'

def sample(im,sx,sy):
 a=np.array(im).astype(float);alpha=a[:,:,3];prem=a[:,:,:3]*(alpha[:,:,None]/255)
 coord=np.array([sy,sx]);outa=map_coordinates(alpha,coord,order=1,mode='constant',prefilter=False)
 rgb=np.stack([map_coordinates(prem[:,:,c],coord,order=1,mode='constant',prefilter=False) for c in range(3)],axis=2)
 rgb=np.divide(rgb,outa[:,:,None]/255,out=np.zeros_like(rgb),where=outa[:,:,None]>0)
 out=np.rint(np.dstack([rgb,outa])).clip(0,255).astype('uint8')
 # Remove only weak detached resampling specks, never strands connected to strong hair.
 alpha=out[:,:,3];far=(alpha>0)&(alpha<=16)&(distance_transform_edt(alpha<32)>4)
 out[far]=0;labels,n=label(out[:,:,3]>0,np.ones((3,3)));weakids=np.flatnonzero(maximum(out[:,:,3],labels,np.arange(1,n+1))<=16)+1
 out[np.isin(labels,weakids)]=0;out[out[:,:,3]==0]=0
 return out
records=[]
for key in ['long-waves','high-ponytail','braided-updo']:
 src=R/'before/assets'/f'{key}.png';im=Image.open(src).convert('RGBA');yy,xx=np.mgrid[:1672,:941].astype(float);sx=xx.copy();sy=yy.copy()
 if key=='long-waves':
  ys=[0,33,80,140,185,250,420,1671];scales=[1,1.03,1.08,1.14,1.12,1.08,1.08,1.08]
  scale=PchipInterpolator(ys,scales)(yy);sx=472.5+(xx-472.5)/scale
  geometry={'axis_x':472.5,'rows':ys,'horizontal_scale':scales,'vertical_change':0,'purpose':'widen outer ear framing and face opening together; retain clear iris from preceding pass'}
 elif key=='high-ponytail':
  # Inverse y registration stretches the existing ear opening down to the actual ear.
  w=PchipInterpolator([0,505,520,565,590,940],[0,0,1,1,0,0])(xx)
  yin=PchipInterpolator([0,100,124,185,208,230,1671],[0,100,130,165,195,230,1671])(yy)
  sy=yy+w*(yin-yy)
  strength=PchipInterpolator([0,100,124,142,155,170,185,208,230,1671],[0,0,.7,1,.9,.45,0,0,0,0])(yy)
  xin=PchipInterpolator([0,500,537,559,574,620,940],[0,500,525,540,565,620,940])(xx)
  sx=xx+strength*(xin-xx)
  geometry={'affected_box':[500,101,620,229],'source_x':[500,525,540,565,620],'target_x':[500,537,559,574,620],'horizontal_strength_rows':[0,100,124,142,155,170,185,208,230,1671],'horizontal_strength':[0,0,.7,1,.9,.45,0,0,0,0],'source_y':[100,130,165,195,230],'target_y':[100,124,185,208,230],'purpose':'register the existing right ear opening to x545..560, y128..180; do not move crown, left side or lower tail'}
 else:
  scale=.84;ax,ay=472.5,33;sx=ax+(xx-ax)/scale;sy=ay+(yy-ay)/scale
  geometry={'uniform_art_scale':scale,'anchor':[ax,ay],'runtime_placement_unchanged':True,'purpose':'reduce crown and attached side braid together; bring right chignon upward and inward behind ear'}
 ar=sample(im,sx,sy);before=np.array(im)
 if key=='high-ponytail':
  fixed=(yy<=100)|(yy>=230)|(xx<=500)|(xx>=620);ar[fixed]=before[fixed]
 dest=AS/f'{key}.png';Image.fromarray(ar).save(dest,optimize=True)
 records.append({'key':key,'path':str(dest.relative_to(ROOT)),'before_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'changed_pixels':int(np.any(before!=ar,axis=2).sum()),'geometry':geometry,'alpha_bbox':Image.fromarray(ar[:,:,3]).getbbox()})
 print(key,records[-1]['after_sha256'][:8],records[-1]['alpha_bbox'])
for key in ['pixie','jaw-bob']:
 assert (R/'before/assets'/f'{key}.png').read_bytes()==(AS/f'{key}.png').read_bytes(),key+' must remain approved and byte identical'
(R/'corrections.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
p=ROOT/'review/female-five-hairstyles/registration.json';reg=json.loads(p.read_text())
for r in reg:
 c=next((c for c in records if c['key']==r['key']),None)
 if c:r['sha256']=c['after_sha256'];r['ear_fit_correction']=c['geometry'];r['alpha_bbox']=c['alpha_bbox']
p.write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
p=ROOT/'paper-doll-data.js';s=p.read_text()
for c in records:s=re.sub(re.escape(c['path'])+r'\?v=[a-f0-9]+',c['path']+'?v='+c['after_sha256'][:8],s)
p.write_text(s)
