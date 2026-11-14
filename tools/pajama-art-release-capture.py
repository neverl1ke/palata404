"""Capture the staged production sources in the real game without image routes."""
from pathlib import Path
import base64
import hashlib
import io
import json
from PIL import Image
from playwright.sync_api import sync_playwright

R = Path(__file__).resolve().parents[1]
D = R / 'review/pajama-art-release-20261114'
OLD = R / 'review/pajama-waist-occlusion-20261114'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
release = json.loads((D / 'release-manifest.json').read_text())
old = json.loads((OLD / 'capture-checks.json').read_text())
pins = {row['runtime']: sha(R / row['runtime']) for row in release['artwork']}
pins.update({p: sha(R / p) for p in release['runtime']})
prior = {(r['kind'], r['gender'], r['pose']): r for r in old['records'] if r['stage'] == 'after'}
POSES = [('idle', None), ('melee', 'gear-knife'), ('rifle', 'gear-aks')]
SNAP = "()=>JSON.parse(JSON.stringify({stats,inventory,equippedGear,profile:getCombatWeaponStats(),paperDollState,storage:Object.fromEntries(Object.entries(localStorage).filter(([k])=>['palata404_stats','palata404_inventory','palata404_equipped','palata404_paper_doll'].includes(k)))}))"
records, errors, requests = [], [], []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1672, 'height': 941})
    context.add_init_script('window.__PALATA_TEST_DIRECT__=true;Math.random=()=>.5;Date.now=()=>1794660000000;')
    context.add_init_script('for(const[k,v]of Object.entries('+json.dumps(old['initialStorageSeed'])+'))localStorage.setItem(k,v);')
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda req: requests.append(req.url))
    page.goto('http://127.0.0.1:3000/index.html?canvas=1', wait_until='networkidle', timeout=120000)
    page.wait_for_function('document.querySelector(".hospital-hud")?.dataset.assetsReady==="true"', timeout=120000)
    page.evaluate("openCustomization();setPaperDollView('combat')")
    for kind, parts in [('full', ['footwear','pants','top']), ('shirt', ['top']),
                        ('pants', ['pants']), ('footwear', ['footwear']), ('none', [])]:
        for g in ('male', 'female'):
            for pose, weapon in POSES:
                page.evaluate('''a=>{setGender(a.g);for(const s of ['upperBody','outerwear','armor','loadout','gloves','pants','footwear','back','accessory','headwear','weapon'])equipPaperDollItem(s,null);equipPaperDollItem('face',null);equipPaperDollItem('hair','hair-none');equipPaperDollItem('beard',null);if(a.parts.includes('top'))equipPaperDollItem('upperBody','patient-pajama-top');if(a.parts.includes('pants'))equipPaperDollItem('pants','patient-pajama-pants');if(a.parts.includes('footwear'))equipPaperDollItem('footwear','patient-pajama-slippers');equipPaperDollItem('weapon',a.w)}''', {'g':g,'parts':parts,'w':weapon})
                page.wait_for_function('''a=>{const h=document.getElementById('wardrobe-paperdoll'),s=avatarCoreGamePreview.instances.get(h);return h.dataset.avatarCoreReady==='true'&&!s.running&&!s.pending&&s.engine.gender===a.g&&s.engine.pose===a.pose&&(h.dataset.pajamaParts||'')===a.parts&&!h.dataset.avatarCoreError&&!h.dataset.avatarCoreBlocked}''', arg={'g':g,'pose':pose,'parts':' '.join(parts)}, timeout=60000)
                snapshot = page.evaluate(SNAP)
                data = page.evaluate('''async()=>{const s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll'));s.engine.pause();s.pajamaMotion={...s.engine.options,...s.pajamaMotion,breathing:true};if(!s.pajamas)s.engine.options.breathing=true;const cycle=s.pajamaMotion.cycleMs,frames=[];for(let k=0;k<17;k++){s.engine.time=k*cycle/16;s.engine.render();const im=s.canvas.getContext('2d').getImageData(0,0,s.canvas.width,s.canvas.height);const rgbaSha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',im.data))].map(x=>x.toString(16).padStart(2,'0')).join('');frames.push({phase:k,timeMs:s.engine.time,rgbaSha256,png:s.canvas.toDataURL()});}return{cycleMs:cycle,frames,native:s.engine.canvas.toDataURL()};}''')
                folder = D / f'captures/{kind}/{g}-{pose}'; folder.mkdir(parents=True, exist_ok=True)
                native = base64.b64decode(data.pop('native').split(',',1)[1])
                oldnative = OLD / f'captures/native/{g}-{pose}.png'
                assert native == oldnative.read_bytes(), (g,pose,'native changed')
                if kind == 'full':
                    n = D / f'captures/native/{g}-{pose}.png'; n.parent.mkdir(exist_ok=True); n.write_bytes(native)
                for f in data['frames']:
                    raw = base64.b64decode(f.pop('png').split(',',1)[1]); image = Image.open(io.BytesIO(raw)).convert('RGBA')
                    f['fullPNGsha256'] = hashlib.sha256(raw).hexdigest()
                    if f['phase'] == 0 or (kind == 'full' and f['phase'] in (4,12)):
                        full = folder / f"frame-{f['phase']:02d}.png"; full.write_bytes(raw); f['path'] = str(full.relative_to(R))
                    if kind == 'full':
                        waist = folder / f"waist-{f['phase']:02d}.png"; image.crop((230,635,720,900)).save(waist); f['waist'] = str(waist.relative_to(R))
                        thumb = folder / f"thumb-{f['phase']:02d}.png"; image.crop((100,0,1200,1672)).resize((330,502),Image.Resampling.LANCZOS).save(thumb); f['thumb'] = str(thumb.relative_to(R))
                        before = prior['pair',g,pose]['frames'][f['phase']]
                        with Image.open(R / before['path']) as previous:
                            assert image.crop((230,635,720,900)).getchannel('A').tobytes() == previous.getchannel('A').tobytes(),(g,pose,f['phase'],'waist silhouette changed')
                        if f['phase'] in (0,4,12):
                            with Image.open(R / before['fullFramePath']) as previous:
                                assert image.getchannel('A').tobytes() == previous.getchannel('A').tobytes(),(g,pose,'whole silhouette changed')
                if kind == 'full':
                    assert snapshot == prior['pair',g,pose]['state'], (g,pose,'state/stats/save changed')
                data.update(kind=kind,gender=g,pose=pose,state=snapshot,nativePNGsha256=hashlib.sha256(native).hexdigest())
                records.append(data);print(kind,g,pose,'17 actual phases; native unchanged',flush=True)
    # Every published asset URL must serve the exact staged byte version.
    served = {}
    for path, h in pins.items():
        res = page.request.get('http://127.0.0.1:3000/' + path)
        assert res.ok and hashlib.sha256(res.body()).hexdigest() == h, path
        served[path] = h
    browser.close()
assert not errors, errors
assert all(sha(R / p) == h for p,h in pins.items())
(D / 'render-checks.json').write_text(json.dumps({
    'captureComplete':True,'artworkRoutesMocked':False,'actualFrames':510,
    'records':records,'browserErrors':errors,'servedSourceSha256':served,
    'fullSetSilhouetteMatchesPrevious':True,'nativeBodyExactAllPoses':True,
    'fullSetStateStatsEquipmentSaveExactPrevious':True,
    'limits':['17 sampled phases of existing shared breathing; no separate walking/arm combat animation.']
},indent=2))
print('PASS: 510 actual game frames; staged source bytes verified without routes')
