"""Stage the user's authorised finish on the current main tree, without Git push."""
from pathlib import Path
import hashlib
import json
import re
import shutil
from PIL import Image

R = Path(__file__).resolve().parents[1]
D = R / 'review/pajama-art-release-20261114'
A = R / 'assets/wardrobe/clothing/patient/pajamas'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
finish = json.loads((D / 'finish-manifest.json').read_text())
records = []
for g in ('male', 'female'):
    for src in (D / f'candidate/{g}').glob('*.png'):
        dst = A / g / src.name
        shutil.copy2(src, dst)
        records.append({'gender': g, 'name': src.stem, 'master': str(src.relative_to(R)),
                        'runtime': str(dst.relative_to(R)), 'sha256': sha(dst)})
    for part in ('top', 'pants', 'footwear'):
        name = 'top-idle' if part == 'top' else part
        image = Image.open(A / g / (name + '.png')).convert('RGBA')
        if part == 'footwear':
            back = Image.open(A / g / 'back-footwear.png').convert('RGBA')
            back.alpha_composite(image); image = back
        box = image.getbbox(); assert box
        crop = image.crop(box); crop.thumbnail((232, 232), Image.Resampling.LANCZOS)
        thumb = Image.new('RGBA', (256, 256))
        thumb.alpha_composite(crop, ((256-crop.width)//2, (256-crop.height)//2))
        thumb.save(A / g / f'thumb-{part}.webp', lossless=True, exact=True, method=6)

# The already-reviewed derived-image clipping logic, not the former body mask.
for name in ('avatar-core/pajamas.mjs', 'paper-doll.js'):
    shutil.copy2(D / 'renderer-masters' / name, R / name)

catalog = (D / 'originals/runtime/pajama-data.js').read_text()
catalog = catalog.split('// Approved shirt rear pieces')[0].rstrip()
def versioned(m):
    rel = m.group(1)
    if rel.endswith('.webp') and not ('thumb-' in rel or 'foreground-' in rel):
        rel = rel[:-5] + '.png'
    assert (R / rel).is_file(), rel
    return rel + '?v=' + sha(R / rel)[:12]
catalog = re.sub(r'(assets/wardrobe/clothing/patient/pajamas/[a-zA-Z0-9_./-]+)\?v=[a-zA-Z0-9_-]+', versioned, catalog)
def url(g, name):
    p = A / g / (name + '.png')
    return str(p.relative_to(R)) + '?v=' + sha(p)[:12]
shirt_back = {g: {p: url(g, 'back-' + p) for p in ('idle', 'melee', 'rifle')} for g in ('male', 'female')}
shoe_back = {g: {p: url(g, 'back-footwear') for p in ('idle', 'melee', 'rifle')} for g in ('male', 'female')}
keep = {g: {p: url(g, 'keep-pants-' + p) for p in ('idle', 'melee', 'rifle')} for g in ('male', 'female')}
extra = '''
    const shirt = PAPER_DOLL_ITEMS.find(item => item.id === 'patient-pajama-top');
    const slippers = PAPER_DOLL_ITEMS.find(item => item.id === 'patient-pajama-slippers');
    shirt.poseClothingBackByGender = SHIRT_BACK;
    slippers.poseClothingBackByGender = SHOE_BACK;
    // Keep masks belong only to this exact artwork pair; pants stay equipped.
    shirt.poseClothingOccludes = [{
        targetItemId: 'patient-pajama-pants', keepMaskByGender: PANTS_KEEP,
        ownerArtworkByGender: top, targetArtworkByGender: pants
    }];
    // Mixed legacy outfits use the real idle art with the same front/rear order.
    for (const item of [shirt, slippers]) item.layers = [
        {id:'rear', genderVariants:Object.fromEntries(['male','female'].map(g=>[g,item.poseClothingBackByGender[g].idle])), renderOrder:-1},
        {id:'front', genderVariants:item.genderVariants, renderOrder:item.renderOrder}
    ];
'''.replace('SHIRT_BACK', json.dumps(shirt_back)).replace('SHOE_BACK', json.dumps(shoe_back)).replace('PANTS_KEEP', json.dumps(keep))
assert catalog.endswith('})();')
catalog = catalog[:-5] + extra + '})();\n'
(R / 'pajama-data.js').write_text(catalog)

# Refresh only the changed script references, preserving unrelated main content.
adapter = R / 'avatar-core/game-preview.mjs'
text = adapter.read_text()
text = re.sub(r"(\./pajamas\.mjs\?v=)[a-zA-Z0-9_-]+", lambda m: m[1] + sha(R / 'avatar-core/pajamas.mjs')[:12], text)
adapter.write_text(text)
index = R / 'index.html'; text = index.read_text()
for rel in ('pajama-data.js', 'paper-doll.js', 'avatar-core/game-preview.mjs'):
    text, n = re.subn(r'(' + re.escape(rel) + r'\?v=)[a-zA-Z0-9_-]+', lambda m: m[1] + sha(R / rel)[:12], text)
    assert n == 1, (rel, n)
index.write_text(text)

(D / 'release-manifest.json').write_text(json.dumps({
    'authorization': finish['authorization'], 'baseCommit': '8cda2bdb1a39304e2a239e3fcf90d37b82797684',
    'frame': [941, 1672], 'artwork': records,
    'runtime': {p: sha(R / p) for p in ('pajama-data.js', 'paper-doll.js', 'avatar-core/pajamas.mjs', 'avatar-core/game-preview.mjs', 'index.html')},
    'historicalOriginals': 'review/pajama-art-release-20261114/originals',
    'noAvatarOrStateSchemaChanges': True, 'maskGeometryFrom': 'pajama-waist-occlusion-20261114'
}, ensure_ascii=False, indent=2))
print('Staged registered PNG finish, six conditional masks and both render paths')
