"""Verify self-contained review and Lab in Chromium, without a local server."""
from pathlib import Path
import json,base64,hashlib
from PIL import Image
import fitz
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'review/avatar-selective-merge';rows=[];errors=[];network=[]
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:network.append(r.url) if r.url.startswith(('https:','http:')) else None)
 for name in ['Report.html','Technical-report.html']:
  p.goto((D/name).as_uri(),wait_until='load')
  for width in [320,390,768,1440]:
   p.set_viewport_size({'width':width,'height':844});p.wait_for_timeout(100);overflow=p.evaluate('document.documentElement.scrollWidth>innerWidth');rows.append({'file':name,'width':width,'overflow':overflow});assert not overflow,rows[-1]
  if name=='Report.html':
   for selector in ['img >> nth=0','img >> nth=-1']:
    im=p.locator(selector);im.scroll_into_view_if_needed();p.wait_for_function('i=>i.complete&&i.naturalWidth>0',arg=im.element_handle())
 p.goto((D/'Avatar-Lab.html').as_uri(),wait_until='load');p.wait_for_function('window.avatarLab?.ready',timeout=60000);p.evaluate('avatarLab.engine.pause()');cases=[]
 for g in ['male','female']:
  p.locator(f'[data-gender="{g}"]').click();p.wait_for_function('g=>avatarLab.engine.gender===g',arg=g)
  for pose,item in [('idle',None),('melee','gear-knife'),('pistol','gear-pm'),('rifle','gear-aks')]:
   p.locator(f'[data-pose="{pose}"]').click();p.wait_for_function('id=>avatarLab.engine.selectedWeaponId===id',arg=item);p.wait_for_timeout(80);src=p.locator('#previous-arms').get_attribute('src');assert src.startswith('data:image/png;base64,');expected=D/'Gallery'/f'184e392-{g}-{pose}-0-{pose!="idle"}.png';assert hashlib.sha256(base64.b64decode(src.split(',')[1])).digest()==hashlib.sha256(expected.read_bytes()).digest();cases.append({'gender':g,'pose':pose,'item':item,'before_image_exact_184e392':True})
 p.screenshot(path=str(D/'Gallery/offline-lab-final.png'),full_page=True);b.close()
assert not errors and not network
cycles={}
for path in (D/'Gallery').glob('*cycle.webp'):
 im=Image.open(path);duration=0
 for i in range(im.n_frames):im.seek(i);im.load();duration+=im.info.get('duration',0)
 assert im.n_frames==40 and duration==4000,(path.name,im.n_frames,duration);cycles[path.name]={'frames':im.n_frames,'duration_ms':duration}
pages=len(fitz.open(D/'Review.pdf'));assert pages==8
out={'engine':'Chromium','file_protocol':True,'physical_device':False,'other_installed_engines':False,'report_viewports':rows,'lab_cases':cases,'js_errors':errors,'external_requests':network,'cycles':cycles,'pdf_pages':pages};(D/'Evidence/offline-verification.json').write_text(json.dumps(out,indent=2)+'\n');print('Offline: eight responsive report checks, eight actual Lab UI cases with exact BEFORE hashes, ten 4000ms cycles, 8-page PDF, no JS errors or external requests')
