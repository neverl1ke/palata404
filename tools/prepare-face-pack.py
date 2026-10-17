"""Локальне очищення наявних PNG облич без генерації та розмиття рис.
python tools/prepare-face-pack.py missing.zip --young-source-dir /path/to/young-before
Залежності: Pillow, NumPy, SciPy. Попередні молоді PNG: коміт 4f48ec8.
"""
import argparse, hashlib, json, zipfile
from io import BytesIO
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
PLACEMENTS = {'exhausted': {'male': (349,30), 'female': (356,25)},
              'elder': {'male': (387,30), 'female': (390,25)}}

def clean(raw, kind, gender, offset):
    source = Image.open(BytesIO(raw)).convert('RGBA')
    canvas = Image.new('RGBA',(941,1672)); canvas.paste(source,offset)
    rgba = np.array(canvas); a = rgba[:,:,3]
    support = a > 127; support[230:] = a[230:] > 8; support[264:] = False
    labels,_ = ndi.label(support)
    label = labels[110,470]
    if not label: raise ValueError('Не знайдено голову в очікуваній точці')
    support = ndi.binary_fill_holes(labels == label)
    # Shape only the lower neck into a continuous cap, never a hard rectangular cut.
    row = np.where(support[230])[0]
    left0,right0 = float(row.min()),float(row.max())
    base_alpha=np.array(Image.open(ROOT/f'base_{gender}.png').getchannel('A'))
    target=np.where(base_alpha[245]>127)[0]
    left1,right1=float(target.min()),float(target.max())
    for y in range(231,264):
        if y<245:
            t=(y-230)/15
            left=left0+(left1-left0)*t;right=right0+(right1-right0)*t
            support[y,:max(0,int(np.ceil(left)))] = False
            support[y,min(941,int(np.floor(right))+1):] = False
        else:
            support[y] &= base_alpha[y]>127
    # Signed-distance smoothing regularizes single-pixel steps without blurring RGB.
    inside = ndi.distance_transform_edt(support)
    outside = ndi.distance_transform_edt(~support)
    distance = ndi.gaussian_filter(inside-outside, sigma=1.8)
    # Slight inward trim removes the old dark matte rim, not facial features.
    alpha = np.clip((distance-.45+.6)/1.2,0,1)
    # Remove chest/clavicles and keep a narrow neck, with an 18px lower transition.
    alpha[245:]=np.minimum(alpha[245:],base_alpha[245:]/255)
    alpha *= np.clip((263-np.arange(1672))/18,0,1)[:,None]
    # Only outer 3px: use existing nearest interior skin, eliminating matte contamination.
    core = inside >= 3.1
    _,indices = ndi.distance_transform_edt(~core,return_indices=True)
    nearest = rgba[indices[0],indices[1],:3]
    edge = (alpha>0) & ~core
    rgba[edge,:3] = nearest[edge]
    rgba[:,:,3] = np.rint(alpha*255).astype('uint8')
    rgba[rgba[:,:,3]==0] = 0
    result = Image.fromarray(rgba)
    path = ROOT/'assets/wardrobe/faces'/f'{gender}_{kind}_head.png'
    result.save(path,optimize=True)
    # Central facial pixels are untouched, including eyes, brows, nose and wrinkles.
    box=(440,85,510,205)
    detail=canvas.convert('RGB').crop(box).tobytes()
    assert detail == result.convert('RGB').crop(box).tobytes()
    return dict(kind=kind,gender=gender,source_sha256=hashlib.sha256(raw).hexdigest(),
        output=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        registration=dict(x=offset[0],y=offset[1],scale=1),bbox=result.getbbox(),
        detail_box=box,detail_sha256=hashlib.sha256(detail).hexdigest())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--young-source-dir',type=Path,required=True);args=p.parse_args()
    entries=[]
    for gender in ['male','female']:
        entries.append(clean((args.young_source_dir/f'{gender}_young_head.png').read_bytes(),'young',gender,(0,0)))
    with zipfile.ZipFile(args.archive) as archive:
        for kind,variants in PLACEMENTS.items():
            for gender,offset in variants.items():
                entries.append(clean(archive.read(f'{kind}_{gender}_head_neck.png'),kind,gender,offset))
    print(json.dumps(dict(young_source_commit='4f48ec87d601d0249c203c56e0b39f5a720a7f48',files=entries),indent=2))
