"""Register the generated trial sprite without changing any approved avatar or hair."""
from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage as ndi
import hashlib,json
root=Path(__file__).resolve().parents[1];src=root/'review/trial-braided-curls/generated-source.png';im=Image.open(src).convert('RGBA');s=.3;tx=325.5;ty=-6
scaled=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS);sx,sy=scaled.width/im.width,scaled.height/im.height
out=scaled.transform((941,1672),Image.Transform.AFFINE,(sx/s,0,-tx*sx/s,0,sy/s,-ty*sy/s),Image.Resampling.BICUBIC)
a=np.array(out);alpha=a[:,:,3];remote=(alpha>0)&(alpha<=16)&(ndi.distance_transform_edt(alpha<32)>4);removed=int(remote.sum());a[remote]=0
labels,n=ndi.label(a[:,:,3]>0,np.ones((3,3)));weak=np.isin(labels,np.flatnonzero(ndi.maximum(a[:,:,3],labels,np.arange(1,n+1))<=16)+1);a[weak]=0;a[a[:,:,3]==0]=0
path=root/'assets/wardrobe/hair/trial/female_braided_curls.png';Image.fromarray(a).save(path,optimize=True);digest=hashlib.sha256(path.read_bytes()).hexdigest()
report={'source':str(src.relative_to(root)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_size':list(im.size),'working_reference':{'crop':[300,0,660,560],'magnification':3,'size':[1080,1680]},'source_registration':{'scale':s,'x':tx,'y':ty,'part_axis_x':490},'output':str(path.relative_to(root)),'sha256':digest,'canvas':[941,1672],'placement':{'x':0,'y':0,'width':941,'height':1672},'remote_alpha_pixels_removed':removed,'female_only':True,'generated_with':'image_gen; photo design + game screenshot + reference avatar; no avatar generated or replaced'}
report['local_edit']={'scope':'jaw curls and ear coverage only','approved_base':'review/trial-braided-curls/approved-texture-source.png','patch':'review/trial-braided-curls/local-jaw-ear-edit.png','mask':'review/trial-braided-curls/local-edit-mask.png','rebuild':'bash tools/apply-trial-local-edit.sh','mix':'straight RGBA; preserves exact original pixels where mask=0'}
(root/'review/trial-braided-curls/registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(digest,removed)
