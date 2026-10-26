"""Make only confirmed interior material opaque; preserve original RGB/holes."""
from pathlib import Path
import json,hashlib
from PIL import Image
import numpy as np
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';D=R/'review/rifle-seams';P=C/'assets/weapons/user-ak47-20261026';master=P/'ak47-master.png'
assert hashlib.sha256(master.read_bytes()).hexdigest()=='891939f70b385def634c127f1999b22db92f55a3a6a80a99369fd01623b3104f'
a=np.array(Image.open(master).convert('RGBA'));out=a.copy();alpha=a[:,:,3]
# No thresholding of the full image. Keep all original low-alpha holes and
# a 2px safety collar around actual boundaries; repair only material enclosed
# by the >=128 material region. RGB is never recolored or repainted.
depth=ndi.distance_transform_edt(alpha>=128);material=depth>=2.5
out[material,3]=255
runtime=P/'ak47-runtime-opaque.png';Image.fromarray(out).save(runtime)
path=C/'equipment-weapons.json';catalog=json.loads(path.read_text());item=next(i for i in catalog['items'] if i['id']=='gear-aks');item['image']=str(runtime.relative_to(C));item['masterImage']=str(master.relative_to(C));item['limitation']='Original user master unchanged; runtime derivative changes confirmed interior alpha only. Rifle anatomy and hand artwork remain pending approval.';path.write_text(json.dumps(catalog,indent=2)+'\n')
mask=np.zeros(alpha.shape,np.uint8);mask[material]=255;Image.fromarray(mask).save(D/'Sources/ak47-confirmed-material-mask.png')
record={'master_sha256':hashlib.sha256(master.read_bytes()).hexdigest(),'runtime_sha256':hashlib.sha256(runtime.read_bytes()).hexdigest(),'RGB_exact':bool(np.array_equal(a[:,:,:3],out[:,:,:3])),'all_alpha_below128_exact':bool(np.array_equal(out[alpha<128,3],alpha[alpha<128])),'all_boundary_collar_exact':bool(np.array_equal(out[~material,3],alpha[~material])),'changed_alpha_pixels':int(np.count_nonzero(out[:,:,3]!=alpha)),'confirmed_interior_pixels':int(material.sum()),'method':'distance>=2.5 inside alpha>=128; preserve original holes and 2px contour collar'}
(D/'Evidence/weapon-opacity.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
