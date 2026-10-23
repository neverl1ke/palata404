"""Capture the actual wardrobe UI, in addition to the fixed library camera."""
import argparse
import functools
import hashlib
import json
import threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/male-heads-full-library'


class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def capture(engine='chromium'):
    inputs=json.loads((REPORT/'captures/inputs.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in inputs.items())
    output=REPORT/('game-ui' if engine=='chromium' else 'game-ui-'+engine);output.mkdir(exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    errors=[];http=[];records=[]
    try:
        with sync_playwright() as pw:
            browser=getattr(pw,engine).launch(headless=True);page=browser.new_page(viewport={'width':1440,'height':1000})
            if engine=='chromium':
                network=page.context.new_cdp_session(page);network.send('Network.enable')
                network.send('Network.setBlockedURLs',{'urls':['https://*']})
            else:page.route('https://**/*',lambda route:route.abort())
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:http.append([r.status,r.url]) if r.status>=400 else None)
            page.on('dialog',lambda d:d.accept())
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html',wait_until='load')
            page.wait_for_function('typeof openCustomization==="function" && typeof paperDollState!=="undefined"')
            for gender,face in [('male','face-male-goth-pierced'),('female','face-goth-septum')]:
                page.evaluate('([g,f])=>{setGender(g);openCustomization();selectWardrobeCategory("appearance");selectWardrobeSlot("face");equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-messy");setHairColor("white");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")}',[gender,face])
                page.wait_for_function('''async()=>{for(const i of document.querySelectorAll('#wardrobe-paperdoll img:not(.hidden)')){
                  if(!i.complete||!i.naturalWidth)return false;
                  if(i.paperHairRequest){const r=i.paperHairRequest,n=r.lastIndexOf('|');if(i.getAttribute('src')!==await coloredHairSource(r.slice(0,n),r.slice(n+1),i.paperHairColorReference))return false;}}
                  return true;}''')
                for width,height in [(1440,1000),(320,568),(390,844),(768,1024)]:
                    page.set_viewport_size({'width':width,'height':height})
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(gender,width)
                    path=str((output/f'{gender}-{width}.png').relative_to(REPORT));page.screenshot(path=str(REPORT/path),full_page=True)
                    records.append({'gender':gender,'face':face,'hair':'hair-messy','color':'white','width':width,'height':height,'path':path})
            assert not errors and not http,(errors,http)
            (output/'result.json').write_text(json.dumps({'engine':engine,'version':browser.version,'records':records,'page_errors':errors,'http_errors':http},indent=2)+'\n')
            browser.close()
    finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox'],default='chromium');args=parser.parse_args();capture(args.engine)
