"""Review before/after, backgrounds, clothing and actual responsive game UI."""
import functools,hashlib,importlib.util,io,json,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'review/female-heads-new-library'
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)

def run(ui_only=False):
 manifest=json.loads((D/'integration-manifest.json').read_text());entries=manifest['files'];out=D/'review-captures';out.mkdir(exist_ok=True);before=D/'before-tone-join';before.mkdir(exist_ok=True)
 spec=importlib.util.spec_from_file_location('prep',ROOT/'tools/prepare-new-female-heads.py');prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)
 base=np.array(Image.open(ROOT/'base_female.png').convert('RGBA'))
 for e in ([] if ui_only else entries):
  head,_,_=prep.prepare(e,base,apply_tone=False,blend_neck=False);Image.fromarray(head).save(before/(e['kind']+'.png'),optimize=True)
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 errors=[];http=[];checks=[];shots=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1440,'height':1000});cdp=page.context.new_cdp_session(page);cdp.send('Network.enable');cdp.send('Network.setBlockedURLs',{'urls':['https://*']})
   page.on('dialog',lambda d:d.accept());page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:http.append([r.status,r.url]) if r.status>=400 else None)
   page.goto(f'http://127.0.0.1:{server.server_port}/index.html',wait_until='networkidle');page.evaluate('openCustomization();setGender("female");setPaperDollView("combat");equipPaperDollItem("upperBody",null)')
   protected=page.evaluate('JSON.stringify({stats,inventory,equippedGear})')
   def ready(selector):
    page.wait_for_function('''async s=>{for(const i of document.querySelectorAll(s+' img:not(.hidden)')){if(!i.complete||!i.naturalWidth)return false;if(i.paperHairRequest){const r=i.paperHairRequest,n=r.lastIndexOf('|');if(i.getAttribute('src')!==await coloredHairSource(r.slice(0,n),r.slice(n+1),i.paperHairColorReference))return false;}const m=i.style.maskImage.match(/url\\(["']?(.*?)["']?\\)/);if(m){let a=new Image();a.src=m[1];await a.decode();}}return true;}''',arg=selector)
   def board(bg='#ffffff',full=False):
    page.evaluate('''([bg,full])=>{document.getElementById('review-board')?.remove();const c=document.createElement('div');c.id='review-board';Object.assign(c.style,{position:'fixed',left:0,top:0,width:full?'480px':'400px',height:full?'850px':'400px',overflow:'hidden',background:bg,zIndex:2147483647});const h=document.createElement('div');h.className='character-paperdoll';Object.assign(h.style,{position:'absolute',width:'941px',height:'1672px',left:full?'5px':'-274px',top:full?'0px':'40px',transform:full?'scale(.5)':'none',transformOrigin:'top left'});c.append(h);document.body.append(c);renderPaperDollAt(h,'review-');}''',[bg,full]);ready('#review-board')
   def save(name,selector='#review-board',fullpage=False):
    p=out/(name+'.webp');p.parent.mkdir(parents=True,exist_ok=True);raw=page.screenshot(full_page=True) if fullpage else page.locator(selector).screenshot();Image.open(io.BytesIO(raw)).convert('RGB').save(p,format='WEBP',lossless=True,method=4);shots.append(str(p.relative_to(D)));return p
   backgrounds=[('white','#ffffff'),('gray','#777777'),('black','#000000'),('green','#00ff00')]
   for e in ([] if ui_only else entries):
    page.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-none");setHairColor("original");setPaperDollView("combat");equipPaperDollItem("upperBody",null)}',e['id']);board();after=save(e['kind']+'/after')
    original=page.evaluate('f=>PAPER_DOLL_ITEMS.find(i=>i.id===f).genderVariants.female',e['id'])
    page.evaluate('([f,s])=>{PAPER_DOLL_ITEMS.find(i=>i.id===f).genderVariants.female=s;renderPaperDoll()}',[e['id'],str((before/(e['kind']+'.png')).relative_to(ROOT))]);board();prior=save(e['kind']+'/before')
    page.evaluate('([f,s])=>{PAPER_DOLL_ITEMS.find(i=>i.id===f).genderVariants.female=s;renderPaperDoll()}',[e['id'],original]);board(full=True);save(e['kind']+'/full')
    for bg,colour in backgrounds:
     for hair in ['hair-none','hair-messy','hair-shoulder-length','hair-bob-bangs']:
      page.evaluate('h=>{equipPaperDollItem("hair",h);setHairColor("white")}',hair);board(colour);save(e['kind']+'/'+bg+'-'+hair)
    page.evaluate('equipPaperDollItem("hair","hair-bob-bangs");setHairColor("original");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")');board();save(e['kind']+'/tunic-original')
    page.evaluate('setHairColor("black")');board();save(e['kind']+'/tunic-black')
    # Only equip actual supported headwear entries; never invent a fixture item.
    hats=page.evaluate('PAPER_DOLL_ITEMS.filter(i=>i.slot==="headwear"&&paperDollItemSupportsGender(i,"female")&&paperDollImageCandidates(i,"female").length).map(i=>i.id)')
    for hat in hats:
     page.evaluate('h=>equipPaperDollItem("headwear",h)',hat);board();save(e['kind']+'/headwear-'+hat)
    page.evaluate('equipPaperDollItem("headwear",null);document.getElementById("review-board")?.remove()')
    # Both scenes use the same face resource and z-index beneath the hair.
    ready('#wardrobe-paperdoll')
    for prefix in ['', 'wardrobe-']:
     order=page.evaluate('p=>{const f=document.getElementById(p+"layer-face"),h=document.getElementById(p+"layer-hair");return [+getComputedStyle(f).zIndex,+getComputedStyle(h).zIndex]}',prefix);assert order[0]<order[1],order
    page.reload(wait_until='networkidle');page.wait_for_function('typeof paperDollState!=="undefined"');assert page.evaluate('paperDollState.appearance.face')==e['id'];assert page.evaluate('JSON.stringify({stats,inventory,equippedGear})')==protected
    page.evaluate('openCustomization()');checks.append({'face':e['id'],'reload':True,'layers':True,'headwear':hats});print('Reviewed',e['kind'],flush=True)
    # Join before/after panels from real browser screenshots, without repaint.
    sheet=Image.new('RGB',(800,428),'#dedbd4');d=ImageDraw.Draw(sheet)
    for i,(label,p) in enumerate([('ДО узгодження тону й стику',prior),('ПІСЛЯ',after)]):sheet.paste(Image.open(p),(i*400,28));d.text((i*400+6,4),label,font=FONT,fill='black')
    sheet.save(out/(e['kind']+'-comparison.webp'),lossless=True)
   if ui_only:
    for e in entries:
     page.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-bob-bangs");setHairColor("white")}',e['id']);ready('#wardrobe-paperdoll')
     page.reload(wait_until='networkidle');page.wait_for_function('typeof paperDollState!=="undefined"');assert page.evaluate('paperDollState.appearance.face')==e['id'];page.evaluate('openCustomization()');checks.append({'face':e['id'],'reload':True,'headwear':[]})
   page.evaluate('document.getElementById("review-board")?.remove();selectWardrobeCategory("appearance");selectWardrobeSlot("face")');ready('#wardrobe-paperdoll');save('desktop-wardrobe',fullpage=True)
   mobile=[]
   for width in [320,360,390,430,768]:
    page.set_viewport_size({'width':width,'height':844 if width>320 else 568})
    page.evaluate('selectWardrobeCategory("appearance");selectWardrobeSlot("face")')
    for e in entries:
     card=page.locator('[data-wardrobe-card="'+e['id']+'"]');card.scroll_into_view_if_needed();card.click();button=page.locator('[data-wardrobe-action="'+e['id']+'"]');button.scroll_into_view_if_needed()
     if button.is_enabled():button.click()
     assert page.evaluate('paperDollState.appearance.face')==e['id']
    page.evaluate('selectWardrobeSlot("hair")');card=page.locator('[data-wardrobe-card="hair-bob-bangs"]');card.scroll_into_view_if_needed();card.click();b=page.locator('[data-wardrobe-action="hair-bob-bangs"]');b.scroll_into_view_if_needed()
    if b.is_enabled():b.click()
    toggle=page.locator('[data-palette-toggle]')
    if toggle.get_attribute('aria-expanded')=='false':toggle.scroll_into_view_if_needed();toggle.click()
    page.locator('[data-hair-color-group="natural"]').click()
    palette=page.locator('[data-hair-color="white"]')
    if palette.count():palette.scroll_into_view_if_needed();palette.click()
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),width
    save('mobile-'+str(width)+'-hair',fullpage=True);page.evaluate('selectWardrobeSlot("face")');save('mobile-'+str(width)+'-faces',fullpage=True);mobile.append({'width':width,'cards':8,'horizontal_overflow':False})
   assert not errors and not http,(errors,http)
   (out/'result.json').write_text(json.dumps({'browser':'Chromium '+browser.version,'checks':checks,'mobile_emulation':mobile,'page_errors':errors,'http_errors':http,'screenshots':sorted(str(p.relative_to(D)) for p in out.rglob('*.webp')),'before_definition':'Same registered new portrait and alpha, before skin-tone gain and lower-neck RGB join; actual game render, not historical old face.'},ensure_ascii=False,indent=2)+'\n');browser.close()
 finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--ui-only',action='store_true');args=p.parse_args();run(args.ui_only)
