"""Exhaustive, resumable photographs from the production index.html renderer.

Every face/hair/color state gets its own lossless screenshot. No generated
stand-ins, no sampled palette, no alternate portrait compositing implementation.
"""
import argparse
import functools
import hashlib
import io
import json
import threading
import time
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/male-heads-full-library'


def capture(quick=False,geometry=False):
    output=REPORT/('geometry' if geometry else 'quick' if quick else 'captures');output.mkdir(exist_ok=True)
    if (output/'result.json').exists():raise SystemExit('Completed evidence already exists')
    paths=[ROOT/p for p in ['base_male.png','base_female.png','index.html','script.js','style.css',
        'paper-doll-data.js','paper-doll.js','hair-color.js','wardrobe.js']]
    paths+=list((ROOT/'assets/wardrobe').rglob('*.png'))
    inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    if (output/'inputs.json').exists():
        assert json.loads((output/'inputs.json').read_text())==inputs,'Resources changed; use a new --report directory'
    else:(output/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    previous={}
    journal=output/'records.jsonl'
    if journal.exists():
        for line in journal.read_text().splitlines():
            r=json.loads(line);previous[r['key']]=r
    server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    errors=[];http=[];records=[];reloads=[];full=[];start=time.monotonic()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True);context=browser.new_context(viewport={'width':1440,'height':1000})
            page=context.new_page();network=context.new_cdp_session(page)
            network.send('Network.enable');network.send('Network.setBlockedURLs',{'urls':['https://*']})
            network.send('Network.setCacheDisabled',{'cacheDisabled':False})
            page.on('dialog',lambda d:d.accept())
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:http.append([r.status,r.url]) if r.status>=400 else None)
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html',wait_until='networkidle')
            page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"')
            page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null)')
            protected=page.evaluate('JSON.stringify({stats,inventory,equippedGear})')
            catalog=page.evaluate('({colors:HAIR_COLORS,faces:PAPER_DOLL_ITEMS.filter(i=>i.slot==="face").map(i=>({id:i.id,name:i.name})),hairs:PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair").map(i=>({id:i.id,name:i.name}))})')
            def board(fullbody=False,bg='#f8f5ee'):
                page.evaluate('''([full,bg])=>{document.getElementById('library-board')?.remove();
                  const crop=document.createElement('div');crop.id='library-board';Object.assign(crop.style,{position:'fixed',left:'0',top:'0',width:full?'480px':'400px',height:full?'850px':'400px',overflow:'hidden',background:bg,zIndex:2147483647});
                  const host=document.createElement('div');host.className='character-paperdoll';Object.assign(host.style,{position:'absolute',width:'941px',height:'1672px',left:full?'5px':'-274px',top:full?'0px':'40px',transform:full?'scale(.5)':'none',transformOrigin:'top left'});
                  crop.append(host);document.body.append(crop);renderPaperDollAt(host,'library-');}''',[fullbody,bg])
                page.wait_for_function('''async()=>{for(const i of document.querySelectorAll('#library-board img:not(.hidden)')){
                  if(!i.complete||!i.naturalWidth)return false;
                  if(i.paperHairRequest){const r=i.paperHairRequest,n=r.lastIndexOf('|');if(i.getAttribute('src')!==await coloredHairSource(r.slice(0,n),r.slice(n+1),i.paperHairColorReference))return false;}
                  const m=i.style.maskImage.match(/url\\(["']?(.*?)["']?\\)/);if(m){const mask=new Image();mask.src=m[1];await mask.decode();}}
                  return true;}''')
            expected=0;gender_info={}
            with journal.open('a') as log:
                for gender in ['male','female']:
                    page.evaluate('g=>{setGender(g);setPaperDollView("combat");equipPaperDollItem("upperBody",null)}',gender)
                    faces=page.evaluate('g=>[null,...PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,g)).map(i=>i.id)]',gender)
                    hairs=page.evaluate('g=>PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair"&&paperDollItemSupportsGender(i,g)).map(i=>i.id)',gender)
                    colors=[c['id'] for c in catalog['colors']]
                    if quick:
                        hairs=[h for h in hairs if h in ['hair-none','hair-messy','hair-textured-short','hair-shoulder-length']];colors=['original','white']
                    elif geometry:colors=['original']
                    gender_info[gender]={'faces':faces,'hairs':hairs,'colors':colors};expected+=len(faces)*len(hairs)*len(colors)
                    for face in faces:
                        page.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-none");setHairColor("original")}',face)
                        board(True);file=output/gender/(face or 'base')/'full.webp';file.parent.mkdir(parents=True,exist_ok=True)
                        im=Image.open(io.BytesIO(page.locator('#library-board').screenshot())).convert('RGB');im.save(file,lossless=True,format='WEBP',method=4)
                        full.append({'gender':gender,'face':face,'path':str(file.relative_to(REPORT))})
                    for hair in hairs:
                        for color in colors:
                            for face in faces:
                                key='/'.join([gender,face or 'base',hair,color]);file=output/(key+'.webp');file.parent.mkdir(parents=True,exist_ok=True)
                                if key in previous and file.exists() and hashlib.sha256(file.read_bytes()).hexdigest()==previous[key]['sha256']:
                                    records.append(previous[key]);continue
                                page.evaluate('([f,h,c])=>{equipPaperDollItem("face",f);equipPaperDollItem("hair",h);setHairColor(c)}',[face,hair,color]);board()
                                raw=page.locator('#library-board').screenshot();im=Image.open(io.BytesIO(raw)).convert('RGB');im.save(file,format='WEBP',lossless=True,method=4)
                                assert Image.open(file).convert('RGB').tobytes()==im.tobytes()
                                state=page.evaluate('paperDollState.appearance');assert state=={'face':face,'hair':hair,'hairColor':color},state
                                r={'key':key,'gender':gender,'face':face,'hair':hair,'color':color,'path':str(file.relative_to(REPORT)),
                                   'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'width':400,'height':400,
                                   'technical':'OK','status':'REVIEW','issues':[]}
                                records.append(r);log.write(json.dumps(r,ensure_ascii=False)+'\n');log.flush()
                                if len(records)%100==0:print('Captured',len(records),'/',expected,flush=True)
                    page.evaluate('document.getElementById("library-board")?.remove()')
                    for face in faces:
                        page.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-shoulder-length");setHairColor("white");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")}',face)
                        page.reload(wait_until='networkidle');page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"')
                        state=page.evaluate('paperDollState');assert state['appearance']=={'face':face,'hair':'hair-shoulder-length','hairColor':'white'}
                        assert state['patientLoadout']['upperBody']=='patient-tunic';assert state['combatLoadout']['upperBody'] is None
                        assert page.evaluate('JSON.stringify({stats,inventory,equippedGear})')==protected
                        reloads.append([gender,face]);page.evaluate('openCustomization();setPaperDollView("combat")')
            assert len(records)==expected and not errors and not http,(len(records),expected,errors,http)
            assert page.evaluate('[...failedPaperDollImages]')==[]
            result={'engine':'chromium','version':browser.version,'catalog':catalog,'genders':gender_info,'expected':expected,'captured':len(records),
                    'full_body':full,'reloads':reloads,'page_errors':errors,'http_errors':http,'seconds':round(time.monotonic()-start,2),
                    'capture':'Production renderPaperDollAt in actual index.html; 400x400 native pixels; full-body 50%; lossless WebP',
                    'visual_status_note':'REVIEW until explicit visual assessment; technical OK does not certify artistic fit.'}
            (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');browser.close()
    except Exception as e:
        (output/'failure.json').write_text(json.dumps({'error':str(e),'completed':len(records),'page_errors':errors,'http_errors':http},ensure_ascii=False,indent=2)+'\n');raise
    finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--quick',action='store_true');parser.add_argument('--geometry',action='store_true');parser.add_argument('--report',type=Path,default=REPORT)
    args=parser.parse_args();assert not(args.quick and args.geometry);REPORT=args.report.resolve();capture(args.quick,args.geometry)
