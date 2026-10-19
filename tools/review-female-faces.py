"""Capture the actual index.html compositor and wardrobe; no synthetic portraits.

Use --phase before before replacing any art, --phase after for the full matrix.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from test_game import GameTests, ROOT


def capture(phase, destination, url=None, source=None):
    out = destination / phase
    out.mkdir(parents=True, exist_ok=True)
    if phase == 'before' and (out / 'capture.json').exists():
        raise SystemExit('Before evidence exists; refusing to overwrite it')
    GameTests.setUpClass()
    case = GameTests()
    case.setUp()
    errors = []
    records = []
    try:
        page = case.page
        if url:
            case.context.unroute('https://**/*')
            page.goto(url, wait_until='networkidle')
        else:
            case.load()
        if phase == 'inputs':
            entries=[]
            for kind in ['ginger_soft','goth_septum','goth_black_lips']:
                head=source/'new_three/heads_and_masks'/f'female_{kind}_head.png'
                mask=source/'new_three/heads_and_masks'/f'female_{kind}_body_mask.png'
                for part,path in [('head',head),('mask',mask)]:
                    case.context.route('**/female-import-'+kind+'-'+part+'.png',
                        lambda route,request,p=path:route.fulfill(content_type='image/png',body=p.read_bytes()))
                entries.append({'id':'face-'+kind.replace('_','-'),'slot':'face','name':kind,'availableByDefault':True,
                    'genders':['female'],'fittedToGender':True,'renderOrder':1,
                    'genderVariants':{'female':'female-import-'+kind+'-head.png'},
                    'bodyMaskByGender':{'female':'female-import-'+kind+'-mask.png'},
                    'placementByGender':{'female':{'x':0,'y':0,'width':941,'height':1672}}})
            # Re-running this diagnostic on the integrated main must still use
            # the supplied raw images, not the first existing ID in the catalog.
            page.evaluate('''es=>{for(const entry of es){
                const index=PAPER_DOLL_ITEMS.findIndex(i=>i.id===entry.id);
                if(index<0)PAPER_DOLL_ITEMS.push(entry);else PAPER_DOLL_ITEMS[index]=entry;
            }}''',entries)
        page.on('response', lambda r: errors.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
        page.evaluate('setGender("female");setPaperDollView("combat");openCustomization();selectWardrobeCategory("appearance");selectWardrobeSlot("face")')
        faces = page.evaluate('PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,"female")).map(i=>i.id)')
        if phase == 'inputs': faces=[e['id'] for e in entries]
        hairs = page.evaluate('PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair"&&paperDollItemSupportsGender(i,"female")).map(i=>i.id)')
        page.set_viewport_size({'width': 1500, 'height': 2400})

        def settle(prefix):
            page.wait_for_function(r'''async p=>{
                const imgs=[...document.getElementById(p+'host').querySelectorAll('img:not(.hidden)')];
                for(const i of imgs){
                    if(!i.complete||!i.naturalWidth)return false;
                    if(i.paperHairRequest){const r=i.paperHairRequest,n=r.lastIndexOf('|');
                        const expected=await coloredHairSource(r.slice(0,n),r.slice(n+1),i.paperHairColorReference);
                        if(i.getAttribute('src')!==expected)return false;}
                    const mask=i.style.maskImage.match(/url\(["']?(.*?)["']?\)/);
                    if(mask){const m=new Image();m.src=mask[1];await m.decode();}
                }return true;
            }''', arg=prefix)

        def start(cols):
            page.evaluate('''cols=>{const s=document.createElement('section');s.id='female-review';
                Object.assign(s.style,{position:'fixed',inset:'0 auto auto 0',display:'grid',
                  gridTemplateColumns:'repeat('+cols+',280px)',gap:'6px',padding:'6px',background:'#d8d5cd',
                  font:'13px sans-serif',color:'#222',zIndex:'2147483647'});document.body.append(s)}''', cols)

        def panel(prefix, label, bg, full=False):
            page.evaluate('''([p,label,bg,full])=>{const c=document.createElement('article');
                const title=document.createElement('strong');title.textContent=label;c.append(title);
                const v=document.createElement('div');Object.assign(v.style,{position:'relative',width:'280px',
                   height:full?'700px':'355px',overflow:'hidden',background:bg});
                const h=document.createElement('div'),s=full?.4:1.15;h.id=p+'host';h.className='character-paperdoll';
                Object.assign(h.style,{position:'absolute',left:(140-474*s)+'px',top:'0px',width:(941*s)+'px',height:(1672*s)+'px'});
                v.append(h);c.append(v);document.getElementById('female-review').append(c);renderPaperDollAt(h,p);
            }''', [prefix, label, bg, full])
            settle(prefix)

        def save(name):
            page.locator('#female-review').screenshot(path=str(out / (name + '.png')))
            page.locator('#female-review').evaluate('e=>e.remove()')

        backgrounds = ['#fff', '#555', '#000', '#00ff00',
            'repeating-conic-gradient(#ddd 0% 25%,#999 0% 50%) 0/20px 20px']
        for face in faces:
            page.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-none");setHairColor("original")}', face)
            start(5)
            for k, bg in enumerate(backgrounds):
                panel(f'bare-{k}-', face, bg)
            save(face + '-bare')
            start(2)
            panel('full-', face + ' · повний зріст', '#fff', True)
            panel('head-', face + ' · голова та шия', '#fff')
            save(face + '-full')
            if phase == 'after':
                for color in ['original', 'black', 'white']:
                    start(5)
                    page.evaluate('c=>setHairColor(c)', color)
                    for j, hair in enumerate(hairs):
                        page.evaluate('h=>equipPaperDollItem("hair",h)', hair)
                        for k, bg in enumerate(backgrounds):
                            panel(f'matrix-{j}-{k}-', hair + ' · ' + color, bg)
                            records.append({'face': face, 'hair': hair, 'color': color, 'background': k})
                    save(face + '-' + color)
            page.evaluate('setHairColor("original");equipPaperDollItem("hair","hair-none")')
        for w, h in [(320,568),(390,844),(768,1024),(1440,1000)]:
            page.set_viewport_size({'width':w,'height':h})
            page.evaluate('setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic");selectWardrobeSlot("face")')
            page.locator(f'[data-wardrobe-card="{faces[-1]}"]').scroll_into_view_if_needed()
            page.screenshot(path=str(out / f'wardrobe-{w}.png'))
        result = {'phase': phase, 'faces': faces, 'hairs': hairs, 'samples': len(records),
                  'unique_combinations': len({(r['face'], r['hair']) for r in records}),
                  'records': records, 'page_errors': case.errors, 'http_errors': errors}
        (out / 'capture.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        assert not case.errors and not errors, result
        print(json.dumps({k:v for k,v in result.items() if k!='records'}, ensure_ascii=False), flush=True)
    finally:
        case.tearDown()
        GameTests.tearDownClass()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--phase', choices=['before','after','inputs'], required=True)
    p.add_argument('--output', type=Path, default=ROOT/'review/female-faces-integration')
    p.add_argument('--url')
    p.add_argument('--source',type=Path,default=Path('/workspace/female-faces-source'))
    a = p.parse_args()
    capture(a.phase, a.output, a.url, a.source)
