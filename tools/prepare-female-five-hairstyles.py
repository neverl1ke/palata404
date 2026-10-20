"""Register five independent new hair sprites; never alter existing artwork."""
from pathlib import Path
import hashlib,json
from PIL import Image
import numpy as np
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'review/female-five-hairstyles'
STYLES=[('pixie','Коротка піксі'),('jaw-bob','Каре до щелепи'),('long-waves','Довгі вільні хвилі'),('high-ponytail','Високий хвіст'),('braided-updo','Зібрана коса')]
records=[]
for key,name in STYLES:
    src=R/'sources'/f'{key}.png'
    if not src.exists(): continue
    im=Image.open(src).convert('RGBA')
    if key=='braided-updo':
        # Detached non-hair mark confined to the otherwise empty top-left corner.
        clean=np.array(im);clean[:80,:80]=0;im=Image.fromarray(clean)
    # Same measured source coordinate frame as the accepted trial; runtime stays full-frame.
    s=.3;tx=325.5;ty=-6
    if key=='pixie': tx=322.5;ty=0
    if key=='high-ponytail': tx=325.5;ty=-14
    if key=='braided-updo': ty=-12
    small=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS)
    sx,sy=small.width/im.width,small.height/im.height
    out=small.transform((941,1672),Image.Transform.AFFINE,(sx/s,0,-tx*sx/s,0,sy/s,-ty*sy/s),Image.Resampling.BICUBIC)
    a=np.array(out);alpha=a[:,:,3]
    far=(alpha>0)&(alpha<=16)&(ndi.distance_transform_edt(alpha<32)>4)
    a[far]=0
    labels,n=ndi.label(a[:,:,3]>0,np.ones((3,3)))
    weak=np.isin(labels,np.flatnonzero(ndi.maximum(a[:,:,3],labels,np.arange(1,n+1))<=16)+1)
    a[weak]=0;a[a[:,:,3]==0]=0
    path=ROOT/'assets/wardrobe/hair/female-five'/f'{key}.png'
    Image.fromarray(a).save(path,optimize=True)
    record={'key':key,'id':'hair-f5-'+key,'name':name,'source':str(src.relative_to(ROOT)),'source_size':list(im.size),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'registration':{'scale':s,'x':tx,'y':ty},'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'placement':{'x':0,'y':0,'width':941,'height':1672},'alpha_bbox':Image.fromarray(a[:,:,3]).getbbox(),'weak_remote_removed':int(far.sum())}
    records.append(record);print(key,record['sha256'][:8],record['alpha_bbox'])
(R/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')

# The approved follow-up fit pass is reproducible from its preserved pre-fix PNGs.
if (ROOT/"review/female-five-fit-audit/corrections.json").exists():
    import subprocess,sys
    subprocess.run([sys.executable,str(ROOT/"tools/refine-female-five-fit.py")],check=True)
