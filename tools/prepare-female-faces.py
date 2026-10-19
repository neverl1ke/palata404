"""Register approved female portraits and build complementary neck/body masks.

No generation, feature warping, body edits, or hairstyle edits. The measured
uniform source transforms are recorded here and in the release manifest.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
SIZE = (941, 1672)
BASE_REF = '4046cac744394faf8b1096d845d8a5e1463aeaf5'
REGISTRATION = {
    'asian': (.20635531247733335, 369.18125819498874, -13.94950105476596),
    'young': (.2128263884899065, 368.3721829337334, -2.7329903707657195),
    'exhausted': (.22221260535537626, 366.8699832143986, -21.230951954867436),
    'elder': (.21937465097775488, 370.970948727176, -23.405364613156536),
    'alternative': (.22709844865961248, 362.73518569057444, -25.02171544057299),
    'ginger_soft': (1., 0., 0.),
    'goth_septum': (1., 0., 0.),
    'goth_black_lips': (1., 0., 0.),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def distance(alpha):
    m = alpha >= .5
    d = ndi.distance_transform_edt(m) - ndi.distance_transform_edt(~m)
    edge = (alpha > 0) & (alpha < 1)
    d[edge] = alpha[edge] - .5
    return d


def extend(a):
    _, idx = ndi.distance_transform_edt(a[:, :, 3] < 248, return_indices=True)
    return a[idx[0], idx[1], :3].astype(float)


def clean_edge(a):
    out = a.copy()
    alpha = out[:, :, 3]
    remote = (alpha > 0) & (alpha <= 16) & (ndi.distance_transform_edt(alpha < 32) > 3)
    alpha[remote] = 0
    labels, n = ndi.label(alpha > 0, np.ones((3, 3)))
    peaks = ndi.maximum(alpha, labels, np.arange(1, n+1))
    alpha[np.isin(labels, np.flatnonzero(peaks <= 16)+1)] = 0
    # Several supplied exports have alpha 252/253 across solid skin. Restore
    # opacity only in the actual interior, leaving AA and piercing holes intact.
    interior = ndi.distance_transform_edt(alpha >= 128) > 2
    filled = interior & (alpha < 255)
    alpha[interior] = 255
    # Preserve opaque anatomy and piercing. Correct only contaminated AA RGB,
    # using the nearest actual opaque pixel, never a generated skin color.
    opaque = alpha >= 248
    _, idx = ndi.distance_transform_edt(~opaque, return_indices=True)
    nearest = out[idx[0], idx[1], :3].astype(float)
    rgb = out[:, :, :3].astype(float)
    difference = np.max(np.abs(rgb-nearest), axis=2)
    bad = (alpha > 0) & (alpha < 230) & (difference > 45)
    out[bad, :3] = nearest[bad].astype('uint8')
    out[out[:, :, 3] == 0] = 0
    return out, {'remote_weak_removed': int(remote.sum()), 'edge_rgb_corrected': int(bad.sum()),
                 'interior_opacity_restored': int(filled.sum())}


def neck_pair(head, base, short_export=False):
    """Morph only the under-jaw silhouette into the exact existing body neck.

    A curved transition is below the chin; complementary mask avoids AA double
    edges and restores every original body pixel below the local join.
    """
    y, x = np.mgrid[:head.shape[0], :941]
    arc = np.minimum(((x-474)/65)**2, 1)
    start, end = 242-24*arc, 278-20*arc
    if short_export:
        start, end = 226-8*arc, 260-10*arc
    b = smooth((y-start)/(end-start))
    ha, ba = head[:, :, 3]/255, base[:, :, 3]/255
    source_distance = distance(ha)
    # A source's lower export cut is not the anatomical neck silhouette.
    # Continue the existing section into the blend using only existing pixels.
    source_distance[236:] = source_distance[235]
    continued = np.clip(source_distance+.5,0,1)
    continued[:236] = ha[:236]
    target = np.clip((1-b)*source_distance+b*distance(ba)+.5, 0, 1)
    target[b == 0] = continued[b == 0]
    target[b == 1] = ba[b == 1]
    labels, count = ndi.label(target >= .5, np.ones((3,3)))
    for label, box in enumerate(ndi.find_objects(labels), 1):
        if box and box[0].start >= 218 and box[0].stop < 286:
            fragment = labels == label
            if np.count_nonzero(fragment) <= 4:
                target[fragment] = 0
    hrgb, brgb = extend(head), extend(base)
    rgb = hrgb*(1-b[:, :, None])+brgb*b[:, :, None]
    rgb[b == 0] = head[:, :, :3][b == 0]
    rgb[b == 1] = base[:, :, :3][b == 1]
    g = 1-smooth((y-end)/8)
    opacity = target*g
    required = np.divide(target-ba, 1-ba, out=np.zeros_like(ba), where=ba < 1)
    opacity = np.maximum(opacity, np.clip(required, 0, 1))
    den = ba*(1-opacity)
    visible = np.divide(target-opacity, den, out=np.zeros_like(den), where=den > 1e-8)
    visible[y >= 286] = 1
    visible[y < 210] = 0
    out = np.dstack((np.rint(rgb), np.rint(opacity*255))).clip(0,255).astype('uint8')
    # The neck blend can detach a few alpha-1..16 source pixels. Recheck the
    # resulting overlay, not just its input, without touching strong details.
    components, n = ndi.label(out[:, :, 3] > 0, np.ones((3,3)))
    peaks = ndi.maximum(out[:, :, 3], components, np.arange(1,n+1))
    out[np.isin(components,np.flatnonzero(peaks<=16)+1)] = 0
    out[out[:, :, 3] == 0] = 0
    mask = np.full(base.shape, 255, dtype='uint8')
    mask[:, :, 3] = np.rint(np.clip(visible,0,1)*255).astype('uint8')
    return out, mask


def prepare(source, report, target=ROOT):
    report.mkdir(parents=True, exist_ok=True)
    supplied = json.loads((source/'FILE_MANIFEST.json').read_text())
    discrepancies = []
    for e in supplied:
        p = source/e['path']
        actual = sha(p.read_bytes()) if p.exists() else None
        if actual != e['sha256']:
            discrepancies.append({'path': e['path'], 'declared_sha256': e['sha256'], 'actual_sha256': actual})
    paths = ['base_male.png','base_female.png']
    paths += subprocess.check_output(['git','ls-tree','-r','--name-only',BASE_REF,'assets/wardrobe'],cwd=ROOT,text=True).splitlines()
    before = {}
    for rel in paths:
        raw = subprocess.check_output(['git','show',f'{BASE_REF}:{rel}'],cwd=ROOT)
        before[rel] = sha(raw)
        if '/faces/female_' in rel or '/faces/masks/female_' in rel:
            p = report/'before/assets'/rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists(): p.write_bytes(raw)
    base = np.array(Image.open(ROOT/'base_female.png').convert('RGBA'))[:340]
    entries = []
    for kind, (scale, tx, ty) in REGISTRATION.items():
        rel = f'legacy_five/approved_visual_sources/female_{kind}_approved_source.png' if kind in list(REGISTRATION)[:5] else f'new_three/heads_and_masks/female_{kind}_head.png'
        p = source/rel
        raw = p.read_bytes()
        original = Image.open(p).convert('RGBA')
        sources = report/'sources'
        sources.mkdir(exist_ok=True)
        (sources/p.name).write_bytes(raw)
        if scale == 1 and tx == 0 and ty == 0:
            registered = original.copy()
        else:
            # Downsample the source before fractional placement for antialiasing.
            scaled = original.resize((round(original.width*scale),round(original.height*scale)),Image.Resampling.LANCZOS)
            sx, sy = scaled.width/original.width, scaled.height/original.height
            # Use a single exact uniform transform, with prefiltering for downscale.
            registered = scaled.transform(SIZE,Image.Transform.AFFINE,
                (sx/scale,0,-tx*sx/scale,0,sy/scale,-ty*sy/scale),Image.Resampling.BICUBIC)
        a, cleanup = clean_edge(np.array(registered)[:340])
        short_export = kind in ['ginger_soft','goth_septum','goth_black_lips']
        head, mask = neck_pair(a, base, short_export)
        full = np.zeros((1672,941,4),dtype='uint8');full[:340] = head
        fullmask = np.full((1672,941,4),255,dtype='uint8');fullmask[:340] = mask
        hpath = f'assets/wardrobe/faces/female_{kind}_head.png'
        mpath = f'assets/wardrobe/faces/masks/female_{kind}_body.png'
        (target/hpath).parent.mkdir(parents=True, exist_ok=True)
        (target/mpath).parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(full).save(target/hpath,optimize=True)
        Image.fromarray(fullmask).save(target/mpath,optimize=True)
        # Central opaque portrait is byte-exact to the registered approved source.
        box = (425,80,525,210)
        expected = np.array(registered)[80:210,425:525]
        opaque = expected[:, :, 3] >= 230
        assert np.array_equal(full[80:210,425:525,:3][opaque],expected[:,:,:3][opaque]), kind
        entries.append({'kind':kind,'id':'face-'+kind.replace('_','-'),'source':str(Path('sources')/p.name),
            'source_archive_path':rel,'source_sha256':sha(raw),'source_size':list(original.size),
            'registration':{'scale':scale,'x':tx,'y':ty,'rotation':0},'placement':{'x':0,'y':0,'width':941,'height':1672},
            'output':hpath,'sha256':sha((target/hpath).read_bytes()),'mask':mpath,'mask_sha256':sha((target/mpath).read_bytes()),
            'detail_box':list(box),'detail_sha256':sha(full[80:210,425:525].tobytes()),
            'bbox':list(Image.fromarray(full).getbbox()),'cleanup':cleanup,
            'neck':{'start_center':226 if short_export else 242,'end_center':260 if short_export else 278,
                    'start_arc':8 if short_export else 24,'end_arc':10 if short_export else 20,'overlap':8,'body_restored_y':286}})
    historical_catalog = subprocess.check_output(['git','show',BASE_REF+':paper-doll-data.js'],cwd=ROOT)
    node = "const fs=require('fs'),vm=require('vm');process.stdout.write(vm.runInNewContext(fs.readFileSync(0,'utf8')+';JSON.stringify(PAPER_DOLL_ITEMS.filter(i=>i.slot===\"hair\"))'))"
    hair_items = json.loads(subprocess.check_output(['node','-e',node],input=historical_catalog,cwd=ROOT))
    data = {'baseline_commit':BASE_REF,'hair_items_before':hair_items,'archive_discrepancies':discrepancies,'files':entries,'before_sha256':before,
            'method':'Uniform registration of approved pixels; local edge RGB cleanup; curved complementary neck masks; no generation'}
    (report/'integration-manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'prepared':len(entries),'archive_discrepancies':len(discrepancies)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--report',type=Path,default=ROOT/'review/female-faces-integration')
    p.add_argument('--target',type=Path,default=ROOT)
    a = p.parse_args()
    prepare(a.source,a.report,a.target)
