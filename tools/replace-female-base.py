"""Integrate the supplied female base and rejoin existing approved necks.

No portrait, ear, hairstyle, anatomy or wardrobe placement is rescaled. The
input is retained verbatim; cleanup only removes alpha<=16 export garbage.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'review/female-base-replacement'
spec = importlib.util.spec_from_file_location('face_prepare', ROOT/'tools/prepare-female-faces.py')
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    previous = json.loads((REPORT/'replacement-manifest.json').read_text()) if (REPORT/'replacement-manifest.json').exists() else {}
    original = np.array(Image.open(REPORT/'source/approved-base.png').convert('RGBA'))
    assert original.shape == (1672, 941, 4)
    out = original.copy()
    a = out[:, :, 3]
    r, g, b = out[:, :, :3].astype(float).transpose(2, 0, 1)
    colored = ((r > 180)&(g < 85)&(b < 85)) | ((r > 170)&(g > 145)&(b < 90)&(g > b*2))
    remote = ndi.distance_transform_edt(a < 32) > 3
    labels, n = ndi.label(a > 0, np.ones((3, 3)))
    peaks = ndi.maximum(a, labels, np.arange(1, n+1))
    detached = np.isin(labels, np.flatnonzero(peaks <= 16)+1)
    removed = (a > 0)&(a <= 16)&(colored | remote | detached)
    out[removed] = 0
    # Removing a weak connector can detach another faint fragment. Reanalyse
    # the resulting alpha rather than trusting only the original components.
    labels, n = ndi.label(out[:,:,3] > 0, np.ones((3, 3)))
    peaks = ndi.maximum(out[:,:,3], labels, np.arange(1, n+1))
    detached_after = np.isin(labels, np.flatnonzero(peaks <= 16)+1)
    removed |= detached_after & (original[:,:,3] > 0)
    out[detached_after] = 0
    # Preserve all source RGB/alpha outside the explicitly identified weak
    # export garbage, including the original antialiasing and skin texture.
    Image.fromarray(out).save(ROOT/'base_female.png', optimize=True)
    entries = []
    for kind, (scale, tx, ty) in prep.REGISTRATION.items():
        name = f'female_{kind}_approved_source.png' if kind in list(prep.REGISTRATION)[:5] else f'female_{kind}_head.png'
        source = ROOT/'review/female-faces-integration/sources'/name
        im = Image.open(source).convert('RGBA')
        if scale != 1 or tx != 0 or ty != 0:
            scaled = im.resize((round(im.width*scale), round(im.height*scale)), Image.Resampling.LANCZOS)
            sx, sy = scaled.width/im.width, scaled.height/im.height
            im = scaled.transform(prep.SIZE, Image.Transform.AFFINE,
                (sx/scale, 0, -tx*sx/scale, 0, sy/scale, -ty*sy/scale), Image.Resampling.BICUBIC)
        registered, _ = prep.clean_edge(np.array(im)[:340])
        # Reproduce the preceding released resource against its actual base.
        # This prevents silently changing the portrait via a different pipeline.
        oldbase = np.array(Image.open(REPORT/'before-assets/base_female.png'))[:340]
        oldhead, oldmask = prep.neck_pair(registered, oldbase, kind in list(prep.REGISTRATION)[5:],
            clean_neck_fringe=kind in ['ginger_soft', 'goth_septum'])
        hp = f'assets/wardrobe/faces/female_{kind}_head.png'
        mp = f'assets/wardrobe/faces/masks/female_{kind}_body.png'
        released_head = REPORT/'before-assets'/hp
        released_mask = REPORT/'before-assets'/mp
        assert np.array_equal(oldhead, np.array(Image.open(released_head if released_head.exists() else ROOT/hp))[:340]), kind
        assert np.array_equal(oldmask, np.array(Image.open(released_mask if released_mask.exists() else ROOT/mp))[:340]), kind
        head, mask = prep.neck_pair(registered, out[:340], kind in list(prep.REGISTRATION)[5:],
            clean_neck_fringe=kind in ['ginger_soft', 'goth_septum'])
        for path, part, fill in [(hp, head, 0), (mp, mask, 255)]:
            current = ROOT/path
            before = REPORT/'before-assets'/path
            before.parent.mkdir(parents=True, exist_ok=True)
            if not before.exists(): before.write_bytes(current.read_bytes())
            full = np.full(out.shape, fill, dtype='uint8'); full[:340] = part
            if path == hp:
                assert np.array_equal(full[:218], np.array(Image.open(before))[:218]), kind
            Image.fromarray(full).save(current, optimize=True)
            entries.append({'path': path, 'before': str(before.relative_to(REPORT)),
                            'before_sha256': digest(before), 'sha256': digest(current)})
    before = REPORT/'before-assets/base_female.png'
    entries.insert(0, {'path':'base_female.png', 'before': str(before.relative_to(REPORT)),
                      'before_sha256': digest(before), 'sha256': digest(ROOT/'base_female.png')})
    manifest = {'baseline':'b00712bffcac1117f3fdba85f0a81f57b58592ba',
        'source_sha256': digest(REPORT/'source/approved-base.png'), 'frame':[941,1672],
        'removed_weak_pixels': int(removed.sum()), 'removed_colored_pixels':int((removed&colored).sum()),
        'cleanup_max_alpha': int(original[:,:,3][removed].max()),
        'portrait_unchanged_above_y':218, 'head_scale':1, 'head_x':0, 'head_y':0,
        'files':entries, 'protected_sha256':previous.get('protected_sha256', {})}
    (REPORT/'replacement-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__': run()
