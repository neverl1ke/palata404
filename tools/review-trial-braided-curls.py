"""Exercise the one removable trial style through the real index.html renderer."""
import functools, io, json, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review/trial-braided-curls'
TRIAL = 'hair-trial-braided-curls'


def run():
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    errors, missing, records = [], [], []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={'width':1440,'height':1000})
            page.context.route('https://**/*', lambda route: route.abort())
            page.on('dialog', lambda d: d.accept())
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('response', lambda r: missing.append([r.url,r.status]) if r.status>=400 else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html', wait_until='networkidle')
            page.evaluate('openCustomization();setGender("female");equipPaperDollItem("face","face-young");setPaperDollView("combat");equipPaperDollItem("upperBody",null);selectWardrobeCategory("appearance");selectWardrobeSlot("hair")')
            protected = page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')
            page.locator(f'[data-wardrobe-card="{TRIAL}"]').click()
            page.locator(f'[data-wardrobe-action="{TRIAL}"]').click()
            assert page.evaluate('paperDollState.appearance.hair') == TRIAL
            def settle():
                page.wait_for_function('''async()=>{for(const i of document.querySelectorAll('img.char-layer:not(.hidden)')){if(!i.complete||!i.naturalWidth)return false;if(i.paperHairRequest){const r=i.paperHairRequest,n=r.lastIndexOf('|');if(i.getAttribute('src')!==await coloredHairSource(r.slice(0,n),r.slice(n+1),i.paperHairColorReference))return false;}const m=i.style.maskImage.match(/url\\(["']?(.*?)["']?\\)/);if(m){const a=new Image();a.src=m[1];await a.decode();}}return true;}''')
            def board(bg='#faf7ef'):
                page.evaluate('''bg=>{document.getElementById('trial-board')?.remove();const c=document.createElement('div');c.id='trial-board';Object.assign(c.style,{position:'fixed',left:0,top:0,width:'500px',height:'520px',overflow:'hidden',background:bg,zIndex:2147483647});const h=document.createElement('div');h.className='character-paperdoll';Object.assign(h.style,{position:'absolute',width:'941px',height:'1672px',left:'-222px',top:'20px'});c.append(h);document.body.append(c);renderPaperDollAt(h,'trial-')}''', bg)
                settle()
            def shot(name):
                im = Image.open(io.BytesIO(page.locator('#trial-board').screenshot())).convert('RGB')
                im.save(OUT/(name+'.webp'),lossless=True)
                return im
            board();shot('young-original')
            faces=page.evaluate('[null,...PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,"female")).map(i=>i.id)]')
            montage=Image.new('RGB',(1250,4*285),'#e9e5dd');draw=ImageDraw.Draw(montage)
            for n, face in enumerate(faces):
                page.evaluate('f=>{equipPaperDollItem("face",f);setHairColor("original")}',face);board();im=shot('face-'+(face or 'native'))
                x=n%5*250;y=n//5*285;montage.paste(im.resize((250,260)),(x,y+25));draw.text((x+3,y+4),face or 'native',fill='black');records.append(face)
            montage.save(OUT/'all-female-heads.webp',lossless=True)
            page.evaluate('equipPaperDollItem("face","face-young")')
            for color in ['original','black','white']:
                page.evaluate('c=>setHairColor(c)',color)
                for label,bg in [('light','#faf7ef'),('gray','#777777'),('black','#000000'),('green','#00ff00')]:
                    board(bg);shot(color+'-'+label)
            page.evaluate('document.getElementById("trial-board").remove();setHairColor("original");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")');settle()
            page.screenshot(path=str(OUT/'wardrobe-desktop.png'),full_page=True)
            page.evaluate('closeCustomization()');page.screenshot(path=str(OUT/'room-desktop.png'),full_page=True)
            page.reload(wait_until='networkidle');assert page.evaluate('paperDollState.appearance.hair')==TRIAL;assert page.evaluate('paperDollState.appearance.face')=='face-young';assert page.evaluate('paperDollState.patientLoadout.upperBody')=='patient-tunic';assert page.evaluate('paperDollState.combatLoadout.upperBody') is None
            page.evaluate('openCustomization();setPaperDollView("combat");selectWardrobeSlot("hair")');settle()
            for width,height in [(320,568),(390,844)]:
                page.set_viewport_size({'width':width,'height':height});card=page.locator(f'[data-wardrobe-card="{TRIAL}"]');card.scroll_into_view_if_needed();assert card.is_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(OUT/f'wardrobe-mobile-{width}.png'),full_page=True)
            page.evaluate('setGender("male");selectWardrobeSlot("hair")');assert page.locator(f'[data-wardrobe-card="{TRIAL}"]').count()==0;assert page.evaluate('paperDollState.appearance.hair')=='hair-none'
            page.evaluate('setGender("female");equipPaperDollItem("hair","'+TRIAL+'");equipPaperDollItem("hair","hair-none")');settle();assert page.locator('#layer-hair').get_attribute('src') is None
            assert page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')==protected
            assert not errors and not missing,(errors,missing)
            (OUT/'browser-check.json').write_text(json.dumps({'browser':'Chromium '+browser.version,'entry':'index.html','female_faces_checked':records,'palette':['original','black','white'],'backgrounds':['light','gray','black','green'],'real_ui_selection':True,'reload':True,'male_exclusion':True,'unequip':True,'patient_trip_independent':True,'protected_game_state_unchanged':True,'mobile_emulation_widths':[320,390],'js_errors':errors,'http_errors':missing},ensure_ascii=False,indent=2)+'\n')
            browser.close()
    finally:
        server.shutdown();server.server_close();thread.join()


if __name__ == '__main__': run()
