"""Native base before/after and hairstyle screenshots in actual index.html."""
import functools
import io
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/female-base-replacement'


def run():
    output=REPORT/'native-base';output.mkdir(exist_ok=True)
    if (output/'result.json').exists(): raise SystemExit('Completed evidence already exists')
    server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    errors=[];http=[];records=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            for phase in ['before','after']:
                context=browser.new_context(viewport={'width':1280,'height':1000})
                context.route('https://**/*',lambda route:route.abort())
                if phase=='before':
                    def old_art(route):
                        p=REPORT/'before-assets'/unquote(urlparse(route.request.url).path).lstrip('/')
                        if p.is_file():route.fulfill(path=str(p),content_type='image/png')
                        else:route.continue_()
                    context.route(f'http://127.0.0.1:{server.server_port}/**',old_art)
                page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('response',lambda r:http.append([r.status,r.url]) if r.status>=400 else None)
                page.on('dialog',lambda d:d.accept())
                page.goto(f'http://127.0.0.1:{server.server_port}/index.html',wait_until='networkidle')
                page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"')
                page.evaluate('openCustomization();setGender("female");setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("face",null);equipPaperDollItem("hair","hair-none")')
                def board(full=False):
                    page.evaluate('''full=>{document.getElementById('base-board')?.remove();
                      const board=document.createElement('div');board.id='base-board';document.body.append(board);
                      Object.assign(board.style,{position:'fixed',left:'0',top:'0',display:'flex',zIndex:2147483647,width:full?'480px':'960px',height:full?'850px':'300px'});
                      (full?['#fff']:['#fff','#555','#000','#0f0']).forEach((bg,j)=>{
                        const crop=document.createElement('div');Object.assign(crop.style,{position:'relative',overflow:'hidden',background:bg,width:full?'480px':'240px',height:full?'850px':'300px'});
                        const host=document.createElement('div');host.className='character-paperdoll';Object.assign(host.style,{position:'absolute',width:'941px',height:'1672px',left:full?'5px':'-354px',top:'0',transform:full?'scale(.5)':'none',transformOrigin:'top left'});
                        crop.append(host);board.append(crop);renderPaperDollAt(host,'base-check-'+j+'-');});}''',full)
                    page.wait_for_function('''async()=>{for(const i of document.querySelectorAll('#base-board img:not(.hidden)')){
                      if(!i.complete||!i.naturalWidth)return false;
                      if(i.paperHairRequest){const r=i.paperHairRequest,n=r.lastIndexOf('|');if(i.getAttribute('src')!==await coloredHairSource(r.slice(0,n),r.slice(n+1),i.paperHairColorReference))return false;}}
                      return true;}''')
                board(True);page.locator('#base-board').screenshot(path=str(output/f'{phase}-full.png'))
                hairs=page.evaluate('PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair"&&paperDollItemSupportsGender(i,"female")).map(i=>i.id)')
                for color in ['original','black','white']:
                    sheet=Image.new('RGB',(960,300*len(hairs)))
                    for row,hair in enumerate(hairs):
                        page.evaluate('([h,c])=>{equipPaperDollItem("hair",h);setHairColor(c)}',[hair,color]);board()
                        shot=Image.open(io.BytesIO(page.locator('#base-board').screenshot())).convert('RGB')
                        sheet.paste(shot,(0,row*300));records.append({'phase':phase,'hair':hair,'color':color,'backgrounds':4})
                        if hair=='hair-none' and color=='original':shot.save(output/f'{phase}-bare.png')
                    sheet.save(output/f'{phase}-{color}.webp',lossless=True,method=4)
                context.close()
            assert not errors and not http,(errors,http)
            (output/'result.json').write_text(json.dumps({'engine':'chromium','version':browser.version,
                'combinations':len(records),'background_samples':len(records)*4,'records':records,
                'page_errors':errors,'http_errors':http,'before':'production index.html compositor with exact b00712b art intercepted from preserved before-assets',
                'after':'unmodified current index.html renderer and current files'},indent=2)+'\n')
            browser.close()
    finally:server.shutdown();server.server_close();thread.join()


def clothing():
    """Actual wardrobe UI, both modes and every female head with the tunic."""
    from importlib import util
    import sys
    sys.path.insert(0,str(ROOT))
    spec=util.spec_from_file_location('game_support',ROOT/'tests/test_game.py')
    support=util.module_from_spec(spec);spec.loader.exec_module(support)
    support.GameTests.setUpClass();case=support.GameTests();case.setUp()
    output=REPORT/'clothing';output.mkdir(exist_ok=True)
    if (output/'result.json').exists():raise SystemExit('Completed clothing evidence exists')
    try:
        case.load();page=case.page
        page.evaluate('openCustomization();setGender("female");setHairColor("original");equipPaperDollItem("hair","hair-none");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")')
        records=[]
        for face in [None,'face-asian','face-young','face-exhausted','face-elder','face-alternative','face-ginger-soft','face-goth-septum','face-goth-black-lips']:
            page.evaluate('f=>equipPaperDollItem("face",f)',face)
            page.wait_for_function('''async()=>{for(const i of document.querySelectorAll('#wardrobe-paperdoll img:not(.hidden)')){
              if(!i.complete||!i.naturalWidth)return false;const m=i.style.maskImage.match(/url\\(["']?(.*?)["']?\\)/);
              if(m){const im=new Image();im.src=m[1];await im.decode();}}return true;}''')
            page.locator('#wardrobe-paperdoll').screenshot(path=str(output/f'{face or "base"}-patient.png'))
            records.append(face)
        page.evaluate('setPaperDollView("combat");equipPaperDollItem("upperBody",null);setPaperDollView("patient")')
        page.reload(wait_until='networkidle')
        page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"')
        state=page.evaluate('paperDollState')
        assert state['patientLoadout']['upperBody']=='patient-tunic'
        assert state['combatLoadout']['upperBody'] is None
        assert not case.errors,case.errors
        (output/'result.json').write_text(json.dumps({'faces':records,'page_errors':case.errors,
            'patient_tunic_retained_after_reload':True,'combat_empty_retained_after_reload':True},indent=2)+'\n')
    finally:case.tearDown();support.GameTests.tearDownClass()


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--clothing',action='store_true');args=parser.parse_args()
    clothing() if args.clothing else run()
