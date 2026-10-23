"""Show actual prop alpha components; do not erase opaque parts blindly."""
from pathlib import Path
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
import numpy as np,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'review/female-donor-arm-pass';rows=[]
for pose in ['melee','pistol','rifle']:
 p=R/'avatar-core/assets/female/donor-art'/(pose+'-weapon.png');a=np.array(Image.open(p));labels,n=ndi.label(a[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(labels.ravel());ids=sorted(range(1,n+1),key=lambda i:-sizes[i]);im=Image.fromarray(a);bg=Image.new('RGBA',im.size,'#888');bg.alpha_composite(im);d=ImageDraw.Draw(bg);parts=[]
 for i in ids:
  if sizes[i]<8:continue
  yy,xx=np.where(labels==i);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];d.rectangle(box,outline='cyan' if i==ids[0] else 'red',width=1);d.text((box[0],box[1]),str(i),fill='yellow');parts.append({'id':int(i),'pixels':int(sizes[i]),'bounds':box,'max_alpha':int(a[:,:,3][labels==i].max())})
 box=im.getbbox();bg.crop((max(0,box[0]-10),max(0,box[1]-10),min(941,box[2]+10),min(1672,box[3]+10))).save(O/'Gallery'/f'{pose}-prop-component-map.webp',lossless=True);rows.append({'pose':pose,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'components':parts,'review_note':'Separate visible prop material and concealed underlap around source finger occlusion are retained. A component count alone is not proof of noise. This is not an unobstructed universal weapon asset.'})
(O/'prop-components.json').write_text(json.dumps(rows,indent=2)+'\n');print('Updated component maps from actual current prop PNGs')
