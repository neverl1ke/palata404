"""Independent main-index captures, never a replacement portrait renderer.

The review board calls the production compositor in index.html. Wardrobe UI
screenshots are separate. Portrait crops are native Paper Doll pixels; enlarged
crops are nearest-neighbour copies of these actual browser screenshots.
"""
import argparse
import functools
import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FACES = ['asian', 'young', 'exhausted', 'elder', 'alternative',
         'ginger-soft', 'goth-septum', 'goth-black-lips']
BACKGROUNDS = ['#ffffff', '#555555', '#000000', '#00ff00']


def capture(destination, phase, engine, matrix):
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / (phase + '-' + engine)
    output.mkdir(exist_ok=True)
    if (output/'result.json').exists():
        raise SystemExit('Refusing to overwrite completed audit evidence')
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(
        SimpleHTTPRequestHandler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    errors, http, records, reloads, mobiles = [], [], [], [], []
    try:
        with sync_playwright() as pw:
            browser = getattr(pw, engine).launch(headless=True)
            context = browser.new_context(viewport={'width':1280, 'height':1100})
            context.route('https://**/*', lambda route: route.abort())
            page = context.new_page()
            page.on('dialog', lambda dialog: dialog.accept())
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda r: http.append([r.status,r.url]) if r.status>=400 else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html', wait_until='networkidle')
            page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"')
            page.evaluate('openCustomization();setGender("female");setPaperDollView("combat");equipPaperDollItem("upperBody",null)')
            protected = page.evaluate('JSON.stringify({stats,inventory,equippedGear})')
            hairs = page.evaluate('PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair"&&paperDollItemSupportsGender(i,"female")).map(i=>i.id)')

            def board():
                page.evaluate('''()=>{document.getElementById('independent-board')?.remove();
                  const b=document.createElement('div');b.id='independent-board';
                  Object.assign(b.style,{position:'fixed',left:'0',top:'0',display:'flex',
                    zIndex:2147483647,width:'960px',height:'300px'});document.body.append(b);
                  ['#fff','#555','#000','#0f0'].forEach((bg,j)=>{
                    const crop=document.createElement('div');Object.assign(crop.style,{
                      width:'240px',height:'300px',position:'relative',overflow:'hidden',background:bg});
                    const host=document.createElement('div');host.className='character-paperdoll';
                    Object.assign(host.style,{width:'941px',height:'1672px',position:'absolute',left:'-354px',top:'0'});
                    crop.append(host);b.append(crop);renderPaperDollAt(host,'independent-'+j+'-');});}''')
                page.wait_for_function('''async()=>{for(const im of document.querySelectorAll('#independent-board img:not(.hidden)')){
                  if(!im.complete||!im.naturalWidth)return false;
                  if(im.paperHairRequest){const r=im.paperHairRequest,n=r.lastIndexOf('|');
                    if(im.getAttribute('src')!==await coloredHairSource(r.slice(0,n),r.slice(n+1),im.paperHairColorReference))return false;}
                  const match=im.style.maskImage.match(/url\\(["']?(.*?)["']?\\)/);
                  if(match){const mask=new Image();mask.src=match[1];await mask.decode();}
                }return true;}''')

            for kind in FACES:
                face='face-'+kind
                page.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-none");setHairColor("original")}',face)
                board()
                page.locator('#independent-board').screenshot(path=str(output/(face+'-bare.png')))
                page.evaluate('document.getElementById("independent-board").remove();equipPaperDollItem("hair","hair-bob-bangs");setHairColor("white");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")')
                page.reload(wait_until='networkidle')
                # networkidle alone can precede deferred-script execution in
                # Firefox under CPU load. Wait for the actual application too.
                page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"')
                state=page.evaluate('paperDollState')
                assert state['appearance']=={'face':face,'hair':'hair-bob-bangs','hairColor':'white'},state
                assert state['patientLoadout']['upperBody']=='patient-tunic'
                assert state['combatLoadout']['upperBody'] is None
                assert page.evaluate('JSON.stringify({stats,inventory,equippedGear})')==protected
                reloads.append(face)
                page.evaluate('openCustomization();setPaperDollView("combat")')
                page.locator('#wardrobe-paperdoll').screenshot(path=str(output/(face+'-game.png')))

            if matrix:
                import io
                # Visit all faces while the same hair/color is hot in the
                # bounded production recoloring cache. This changes only test
                # traversal order, not game caching or captured combinations.
                page.evaluate('selectWardrobeSlot("face")')
                for color in ['original','black','white']:
                    sheets={k:Image.new('RGB',(960,300*len(hairs))) for k in FACES}
                    for row,hair in enumerate(hairs):
                        for kind in FACES:
                            face='face-'+kind
                            page.evaluate('([f,h,c])=>{equipPaperDollItem("face",f);equipPaperDollItem("hair",h);setHairColor(c)}',[face,hair,color])
                            board()
                            shot=Image.open(io.BytesIO(page.locator('#independent-board').screenshot())).convert('RGB')
                            sheets[kind].paste(shot,(0,300*row))
                            records.append({'face':face,'hair':hair,'color':color,'backgrounds':BACKGROUNDS})
                    for kind,sheet in sheets.items():
                        png=io.BytesIO();webp=io.BytesIO()
                        sheet.save(png,format='PNG',optimize=True)
                        sheet.save(webp,format='WEBP',lossless=True,method=4)
                        encoded,extension=min([(png.getvalue(),'png'),(webp.getvalue(),'webp')],key=lambda p:len(p[0]))
                        assert Image.open(io.BytesIO(encoded)).convert('RGB').tobytes()==sheet.tobytes()
                        (output/('face-'+kind+'-'+color+'.'+extension)).write_bytes(encoded)
                page.evaluate('document.getElementById("independent-board").remove()')

            for w,h in [(320,568),(360,640),(390,844),(430,844),(768,1024),(1440,1000)]:
                page.set_viewport_size({'width':w,'height':h})
                page.evaluate('setPaperDollView("patient");equipPaperDollItem("face",null);selectWardrobeCategory("appearance");selectWardrobeSlot("face")')
                card=page.locator('[data-wardrobe-card="face-goth-black-lips"]')
                card.scroll_into_view_if_needed();card.click()
                action=page.locator('[data-wardrobe-action="face-goth-black-lips"]')
                action.scroll_into_view_if_needed();action.click()
                assert page.evaluate('paperDollState.appearance.face')=='face-goth-black-lips'
                overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
                assert not overflow,(engine,w)
                page.screenshot(path=str(output/f'wardrobe-{w}.png'))
                mobiles.append({'width':w,'height':h,'last_card_clicked':True,'horizontal_overflow':overflow})
            assert not errors and not http,(errors,http)
            assert page.evaluate('[...failedPaperDollImages]')==[]
            result={'engine':engine,'version':browser.version,'phase':phase,'hairs':hairs,
                    'matrix_records':records,'combinations':len(records),
                    'background_samples':len(records)*4,'reloaded_faces':reloads,
                    'ui_viewports':mobiles,'page_errors':errors,'http_errors':http,
                    'capture':'production compositor in actual index.html, native 1:1 Paper Doll pixels',
                    'device':'desktop browser with emulated viewport, no physical mobile device'}
            (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            browser.close()
    except Exception as error:
        (output/'failure.json').write_text(json.dumps({'engine':engine,'phase':phase,
            'exception':str(error),'page_errors':errors,'http_errors':http,
            'completed_matrix_records':len(records),'reloaded_faces':reloads},ensure_ascii=False,indent=2)+'\n')
        raise
    finally:
        server.shutdown();server.server_close();thread.join()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--phase',choices=['before','after'],required=True)
    parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium')
    parser.add_argument('--matrix',action='store_true')
    args=parser.parse_args()
    capture(args.output,args.phase,args.engine,args.matrix)
