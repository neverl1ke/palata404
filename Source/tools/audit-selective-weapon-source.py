"""Compare inherited weapon derivatives with registered raw Sources; never repaint."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parents[1];D=R/'review/avatar-selective-merge';rows=[]
for pose,name in [('rifle','rifle'),('pistol','pistol'),('melee','knife')]:
 src=np.array(Image.open(R/f'review/male-reference-arm-art/Sources/{pose}.png').convert('RGBA'));raw=np.zeros_like(src);raw[26:,10:]=src[:-26,:-10];current=np.array(Image.open(R/f'avatar-core/assets/weapons/original-visible/weapon_{name}.png').convert('RGBA'));dist=distance_transform_edt(current[:,:,3]>0);delta=np.max(np.abs(current[:,:,:3].astype(int)-raw[:,:,:3].astype(int)),axis=2);uncertain=(current[:,:,3]>=250)&(dist>2)&(delta>3);Image.fromarray((uncertain*255).astype('uint8')).save(D/'Evidence'/f'weapon-{name}-inherited-difference-mask.png');im=Image.fromarray(current);box=im.getbbox();bg=Image.new('RGBA',im.size,'#777');bg.alpha_composite(im);pix=np.array(bg);pix[uncertain,:3]=[255,0,180];Image.fromarray(pix).crop(box).save(D/'Gallery'/f'weapon-{name}-uncertain.webp',lossless=True);rows.append({'pose':pose,'registered_raw_shift':[10,26],'solid_pixels_different_from_raw':int(uncertain.sum()),'interpretation':'historically edited/padded pixels; flagged for source review, not automatically a newly detected visual defect','runtime_changed':False})
(D/'Evidence/inherited-weapon-source-differences.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
