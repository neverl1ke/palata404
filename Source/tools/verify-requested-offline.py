from pathlib import Path
import json
from playwright.sync_api import sync_playwright
from PIL import Image
import fitz
R=Path(__file__).resolve().parents[1]/'review/avatar-requested-corrections';out={'physical_device':False,'engine':'Chromium','pages':[]};errors=[];requests=[]
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page(accept_downloads=True);p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:requests.append(r.url) if r.url.startswith(('https:','http:')) else None)
 for name in ['Report.html','Technical-report.html']:
  p.goto((R/name).as_uri(),wait_until='load')
  for width in [320,390,768,1440]:
   p.set_viewport_size({'width':width,'height':844});p.wait_for_timeout(100)
   row={'file':name,'width':width,'overflow':p.evaluate('document.documentElement.scrollWidth>innerWidth')};out['pages'].append(row);assert not row['overflow'],row
  if name=='Report.html':
   p.locator('img').first.wait_for();assert p.locator('img').first.evaluate('(i)=>i.complete&&i.naturalWidth>0')
   with p.expect_download() as dl:p.locator('button[data-file]').first.click()
   dest=Path('/tmp/requested-report-download.png');dl.value.save_as(dest);im=Image.open(dest);im.verify();out['image_download_verified']=True
 p.goto((R/'Avatar-Lab.html').as_uri(),wait_until='load');p.wait_for_function('window.avatarLab?.ready',timeout=60000)
 cases=[]
 for g in ['male','female']:
  p.evaluate('g=>avatarLab.engine.setGender(g)',g)
  for item in [None,'gear-knife','gear-pm','gear-aks']:
   p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',item);cases.append(p.evaluate('()=>({gender:avatarLab.engine.gender,pose:avatarLab.engine.pose,item:avatarLab.engine.selectedWeaponId})'))
 out['lab_cases']=cases;out['js_errors']=errors;out['external_requests']=requests;b.close()
assert not errors and not requests
pdf=fitz.open(R/'Review.pdf');out['pdf_pages']=len(pdf);assert len(pdf)==8
cycles={}
for f in (R/'Gallery').glob('*cycle.webp'):
 im=Image.open(f);duration=0
 for i in range(im.n_frames):im.seek(i);im.load();duration+=im.info.get('duration',0)
 cycles[f.name]={'frames':im.n_frames,'duration_ms':duration};assert im.n_frames==40 and duration==4000
out['cycles']=cycles;(R/'Evidence/offline-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('Offline: 8 responsive report checks, image download, 8 Lab item/gender cases, 8-page PDF,',len(cycles),'4000ms animations; no external requests or JS errors')
