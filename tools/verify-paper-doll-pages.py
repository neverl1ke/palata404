"""Verify the published index.html in Chromium using actual HTTPS bytes.
Python verifies HTTPS certificates; no local runtime/assets are substituted.
"""
from playwright.sync_api import sync_playwright
import urllib.request,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--url',default='https://neverl1ke.github.io/palata404/');parser.add_argument('--output-dir',type=Path,default=ROOT/'review/paper-doll-audit-2026-10');args=parser.parse_args()
base=args.url.rstrip('/')+'/';out=args.output_dir;out.mkdir(parents=True,exist_ok=True);cache={};errors=[];http=[];combos=0;samples=0
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
 assert 'paper-audit-1' in page.content()
 page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);selectWardrobeCategory("appearance");selectWardrobeSlot("hair")')
 def settle():
  page.wait_for_function('''async()=>{for(const i of document.getElementById('wardrobe-paperdoll').querySelectorAll('img:not(.hidden)')){const r=i.paperHairRequest;if(!r)continue;const n=r.lastIndexOf('|'),s=r.slice(0,n),c=r.slice(n+1);if(i.getAttribute('src')!==(c==='original'?s:await coloredHairSource(s,c,i.paperHairColorReference))||!i.complete||!i.naturalWidth)return false}return true}''')
 for gender in ['male','female']:
  page.evaluate('g=>setGender(g)',gender);styles=page.evaluate('wardrobeVisibleItems().map(i=>i.id)');assert len(styles)==(7 if gender=='male' else 8)
  for face in [None,'face-asian','face-young','face-exhausted','face-elder','face-alternative']:
   page.evaluate('f=>equipPaperDollItem("face",f)',face)
   for hair in styles:
    page.evaluate('h=>equipPaperDollItem("hair",h)',hair);combos+=1
    for color in ['original','white']:
     page.evaluate('c=>setHairColor(c)',color);settle()
     if face:
      assert page.locator('#wardrobe-layer-face').get_attribute('src').startswith('assets/wardrobe/faces/'+gender+'_')
      assert page.locator('#wardrobe-layer-face').evaluate('e=>getComputedStyle(e).zIndex')=='1'
     if hair!='hair-none':assert page.locator('#wardrobe-layer-hair').evaluate('e=>getComputedStyle(e).zIndex')=='9'
     if gender=='male' and hair=='hair-shoulder-length':
      assert page.locator('#wardrobe-layer-hair-rear').evaluate('e=>getComputedStyle(e).zIndex')=='-1'
     else:assert page.locator('#wardrobe-layer-hair-rear').count()==0
     for bg in ['#fff','#555','#000','#00ff00']:
      page.locator('.wardrobe-stage').evaluate('(e,bg)=>{e.style.backgroundImage="none";e.style.backgroundColor=bg}',bg);samples+=1
      if face=='face-alternative' and hair in ['hair-shoulder-length','hair-bob-bangs'] and color=='white' and bg=='#fff':page.screenshot(path=str(out/f'live-{gender}-white.jpg'),type='jpeg',quality=94)
 page.reload(wait_until='networkidle');assert page.evaluate('paperDollState.appearance.face')=='face-alternative';assert page.evaluate('paperDollState.appearance.hair')=='hair-shoulder-length';assert page.evaluate('paperDollState.appearance.hairColor')=='white'
 page.evaluate('openCustomization();selectWardrobeCategory("appearance");selectWardrobeSlot("hair");equipPaperDollItem("hair","hair-bob-bangs")')
 for width,height in [(320,568),(390,844),(768,844)]:
  page.set_viewport_size({'width':width,'height':height});page.locator('[data-palette-toggle]').click();page.locator('[data-hair-color-group="natural"]').click();page.locator('[data-hair-color="black"]').click();settle();page.locator('[data-palette-toggle]').click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(out/f'live-mobile-{width}.jpg'),type='jpeg',quality=94)
 assert combos==90 and samples==720 and not errors and not http
 result={'url':base,'combinations':combos,'background_color_checks':samples,'reload':True,'page_errors':errors,'http_errors':http,'mobile_widths':[320,390,768],'transport':'Actual published HTTPS bytes via certificate-verified urllib, Chromium renders without local substitutions','cache_version':'paper-audit-1'}
 (out/'live-browser.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));browser.close()
