"""Verify the published index.html in Chromium using actual HTTPS bytes.
Python verifies HTTPS certificates; no local runtime/assets are substituted.
"""
from playwright.sync_api import sync_playwright
import urllib.request,json,argparse,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--url',default='https://neverl1ke.github.io/palata404/');parser.add_argument('--output-dir',type=Path,default=ROOT/'test-results/published-paper-doll');args=parser.parse_args()
cache_version=re.search(r'style\.css\?v=([a-zA-Z0-9_-]+)',(ROOT/'index.html').read_text())[1]
runtime_cache_version=re.search(r'paper-doll-data\.js\?v=([a-zA-Z0-9_-]+)',(ROOT/'index.html').read_text())[1]
base=args.url.rstrip('/')+'/';out=args.output_dir;out.mkdir(parents=True,exist_ok=True);cache={};errors=[];http=[];combos=0;samples=0;verified=[]
with sync_playwright() as p:
 browser=p.chromium.launch();context=browser.new_context(viewport={'width':1440,'height':1000})
 def transport(route):
  url=route.request.url
  if not url.startswith(base):route.abort();return
  if url not in cache:
   with urllib.request.urlopen(url,timeout=45) as r:cache[url]=(r.status,r.headers.get('Content-Type','application/octet-stream'),r.read())
  status,mime,body=cache[url]
  if status>=400:http.append(url)
  route.fulfill(status=status,content_type=mime,body=body)
 context.route('https://**/*',transport);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base,wait_until='networkidle',timeout=60000)
 assert cache_version in page.content()
 page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"')
 assert page.locator('script[src^="paper-doll-data.js"]').get_attribute('src')=='paper-doll-data.js?v='+runtime_cache_version
 page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);selectWardrobeCategory("appearance");selectWardrobeSlot("hair")')
 def settle():
  page.wait_for_function('''async()=>{for(const i of document.getElementById('wardrobe-paperdoll').querySelectorAll('img:not(.hidden)')){if(!i.complete||!i.naturalWidth)return false;const r=i.paperHairRequest;if(!r)continue;const n=r.lastIndexOf('|'),s=r.slice(0,n),c=r.slice(n+1);if(i.getAttribute('src')!==await coloredHairSource(s,c,i.paperHairColorReference))return false}return true}''')
 for gender in ['male','female']:
  page.evaluate('g=>{setGender(g);selectWardrobeSlot("hair")}',gender);styles=page.evaluate('wardrobeVisibleItems().map(i=>i.id)');assert len(styles)==(7 if gender=='male' else 8)
  page.evaluate('selectWardrobeSlot("face")')
  faces=page.evaluate('g=>[null,...PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,g)).map(i=>i.id)]',gender)
  assert len(faces)==(6 if gender=='male' else 9)
  for hair in styles:
   page.evaluate('h=>equipPaperDollItem("hair",h)',hair)
   for color in ['original','black','white']:
    page.evaluate('c=>setHairColor(c)',color)
    for face in faces:
     page.evaluate('f=>equipPaperDollItem("face",f)',face);settle()
     if color=='original':combos+=1
     if face:
      assert page.locator('#wardrobe-layer-face').get_attribute('src').startswith('assets/wardrobe/faces/'+gender+'_')
      assert page.locator('#wardrobe-layer-face').evaluate('e=>getComputedStyle(e).zIndex')=='1'
     if hair!='hair-none':assert page.locator('#wardrobe-layer-hair').evaluate('e=>getComputedStyle(e).zIndex')=='9'
     if gender=='male' and hair=='hair-shoulder-length':
      assert page.locator('#wardrobe-layer-hair-rear').evaluate('e=>getComputedStyle(e).zIndex')=='-1'
     else:assert page.locator('#wardrobe-layer-hair-rear').count()==0
     for bg in ['#fff','#555','#000','#00ff00','repeating-conic-gradient(#ddd 0% 25%,#999 0% 50%) 0/20px 20px']:
      page.locator('.wardrobe-stage').evaluate('(e,bg)=>{e.style.background=bg}',bg);samples+=1
      if face=='face-alternative' and hair in ['hair-shoulder-length','hair-bob-bangs'] and color=='white' and bg=='#fff':page.screenshot(path=str(out/f'live-{gender}-white.jpg'),type='jpeg',quality=94)
 page.reload(wait_until='networkidle');page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"');assert page.evaluate('paperDollState.appearance.face')==faces[-1];assert page.evaluate('paperDollState.appearance.hair')=='hair-shoulder-length';assert page.evaluate('paperDollState.appearance.hairColor')=='white'
 page.evaluate('setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")')
 for face in faces[1:]:
  page.evaluate('f=>{openCustomization();selectWardrobeSlot("face");equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-none");setHairColor("original")}',face)
  page.reload(wait_until='networkidle');page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"');assert page.evaluate('paperDollState.appearance.face')==face
  page.evaluate('openCustomization();selectWardrobeSlot("face")');page.locator('.wardrobe-stage').evaluate('e=>{e.style.backgroundImage="none";e.style.backgroundColor="#fff"}')
  page.wait_for_function('()=>[...document.querySelectorAll("#wardrobe-paperdoll img:not(.hidden)")].every(i=>i.complete&&i.naturalWidth>0)')
  page.locator('.wardrobe-stage').screenshot(path=str(out/(face+'.png')))
 page.evaluate('setPaperDollView("combat")');assert page.evaluate('activePaperDollLoadout().upperBody') is None
 page.evaluate('setPaperDollView("patient")');assert page.evaluate('activePaperDollLoadout().upperBody')=='patient-tunic'
 page.evaluate('openCustomization();selectWardrobeCategory("appearance");selectWardrobeSlot("hair");equipPaperDollItem("hair","hair-bob-bangs")')
 for width,height in [(320,568),(390,844),(768,844)]:
  page.set_viewport_size({'width':width,'height':height});page.locator('[data-palette-toggle]').click();page.locator('[data-hair-color-group="natural"]').click();page.locator('[data-hair-color="black"]').click();settle();page.locator('[data-palette-toggle]').click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(out/f'live-mobile-{width}.jpg'),type='jpeg',quality=94)
 for url,(status,mime,body) in cache.items():
  rel=url[len(base):].split('?')[0]
  path=ROOT/(rel or 'index.html')
  if path.is_file():
   assert hashlib.sha256(body).hexdigest()==hashlib.sha256(path.read_bytes()).hexdigest(),rel+' differs from local release'
   verified.append(rel or 'index.html')
 assert combos==114 and samples==1710 and not errors and not http
 result={'url':base,'combinations':combos,'background_color_checks':samples,'all_eight_female_reload':True,'patient_trip_outfits':True,'published_files_byte_verified':sorted(set(verified)),'reload':True,'page_errors':errors,'http_errors':http,'mobile_widths':[320,390,768],'transport':'Actual published HTTPS bytes via certificate-verified urllib, Chromium renders without local substitutions','style_cache_version':cache_version,'runtime_cache_version':runtime_cache_version}
 (out/'live-browser.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));browser.close()
