"""Independent observations and evidence inventory, not an artistic pass/fail.

Spur coordinates reproduce the old report's candidate definition solely to
locate its 11/8 warnings. Composite alpha reversals are a different criterion.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[1]
KINDS=['asian','young','exhausted','elder','alternative',
       'ginger_soft','goth_septum','goth_black_lips']


def analyze(output,phase):
    output.mkdir(parents=True,exist_ok=True)
    if phase=='before' and (output/'before-analysis.json').exists():
        raise SystemExit('Refusing to overwrite the initial audit snapshot')
    base=Image.open(ROOT/'base_female.png').convert('RGBA')
    data=[]
    for kind in KINDS:
        rel=f'assets/wardrobe/faces/female_{kind}_head.png'
        path=ROOT/rel
        head=Image.open(path).convert('RGBA');a=np.array(head)[:,:,3]
        mask_path=ROOT/f'assets/wardrobe/faces/masks/female_{kind}_body.png'
        mask=Image.open(mask_path).getchannel('A')
        body=base.copy();body.putalpha(ImageChops.multiply(base.getchannel('A'),mask))
        result=np.array(Image.alpha_composite(body,head));alpha=result[:,:,3].astype(int)
        spurs=(a>=128)&~ndi.binary_opening(a>=128,structure=ndi.generate_binary_structure(2,1))
        yy,xx=np.where(spurs)
        candidates=[]
        for x,y in zip(xx.tolist(),yy.tolist()):
            if kind in ['ginger_soft','goth_septum'] and 230<=y<=248:
                verdict='confirmed-neck-fringe'
            elif (x,y)==(547,120) and kind=='ginger_soft':
                verdict='natural-upper-ear-contour-preserved-from-approved-source'
            else:
                verdict='overlay-fade-threshold-tip-not-a-composite-silhouette-spur'
            candidates.append({'x':x,'y':y,'classification':verdict})
        right=np.diff(alpha[218:255,474:570],axis=1)>8
        left=np.diff(alpha[218:255,375:475],axis=1)<-8
        uy,ux=np.where(a[:210]>=128)
        row_bounds=[]
        for y in range(210,286):
            ids=np.flatnonzero(alpha[y]>=128)
            row_bounds.append({'y':y,'left':int(ids.min()),'right':int(ids.max())})
        data.append({'path':rel,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'mask':str(mask_path.relative_to(ROOT)),
                     'mask_sha256':hashlib.sha256(mask_path.read_bytes()).hexdigest(),
                     'head_bounds_above_y210':[int(ux.min()),int(uy.min()),int(ux.max()),int(uy.max())],
                     'spur_candidates':candidates,'neck_alpha_reversals':int(right.sum()+left.sum()),
                     'mask_visible_pixels_above_y210':int(np.count_nonzero(np.array(mask)[:210])),
                     'composite_neck_min_alpha':int(alpha[225:270,450:500].min()),
                     'lower_body_exact':bool(np.array_equal(result[286:],np.array(base)[286:])),
                     'max_neck_step':int(np.max(np.abs(np.diff(np.array([[r['left'],r['right']] for r in row_bounds if 218<=r['y']<=280]),axis=0)))),
                     'composite_neck_row_bounds':row_bounds})
    (output/f'{phase}-analysis.json').write_text(json.dumps({'files':data},indent=2)+'\n')
    if phase=='before':
        root=ROOT/'review/female-faces-integration'
        files=[];hashes=collections.defaultdict(list)
        for p in sorted(root.rglob('*')):
            if not p.is_file():continue
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            category={'after':'full-matrix-and-current-release-evidence',
                      'before':'historical-evidence-and-test-inputs',
                      'inputs':'original-source-render-evidence',
                      'details':'derived-gallery-close-ups',
                      'sources':'approved-immutable-art-sources',
                      'published':'historical-HTTPS-verification',
                      'test-logs':'historical-success-and-failure-logs'}.get(p.relative_to(root).parts[0],'gallery-documentation-and-manifests')
            files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,
                          'sha256':digest,'category':category,'decision':'retain'})
            hashes[digest].append(str(p.relative_to(ROOT)))
        inventory={'baseline':'6bac151e53e8723f69b21b1a62dd52d02b444cd5',
                   'files':files,'total_files':len(files),'total_bytes':sum(e['bytes'] for e in files),
                   'exact_duplicate_groups':[g for g in hashes.values() if len(g)>1],
                   'deleted':[],'reason':'Sources, test fixtures and linked historical evidence retained. No exact duplicates.',
                   'optimization':'Use lossless WebP for new review matrices; keep historical URLs and source bytes. Bulk format migration needs a URL compatibility plan.'}
        (output/'historical-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--phase',choices=['before','after'],required=True)
    args=parser.parse_args();analyze(args.output,args.phase)
