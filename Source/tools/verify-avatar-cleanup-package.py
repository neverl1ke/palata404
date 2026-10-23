"""Check the actual portable ZIP in an empty directory, without a server."""
from pathlib import Path
import json,tempfile,zipfile,hashlib
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];out=root/'review/avatar-core-cleanup'
records=[];errors=[];network=[]
with tempfile.TemporaryDirectory(prefix='avatar-review-unpacked-') as temp:
 with zipfile.ZipFile(root.parent/'Avatar-Core-Cleanup.zip') as z:
  assert z.testzip() is None;z.extractall(temp)
 folder=Path(temp)/'Avatar-Core-Cleanup'
 with sync_playwright() as pw:
  browser=pw.chromium.launch();context=browser.new_context(viewport={'width':1440,'height':1100})
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:network.append(r.url) if r.url.startswith(('http:','https:')) else None)
  page.goto((folder/'Avatar-Lab.html').as_uri());page.wait_for_function('window.avatarLab?.ready')
  assert page.locator('#pistol-support').is_checked()
  before=page.evaluate('JSON.stringify({...localStorage})')
  for gender in ['male','female']:
   page.locator('[data-gender="'+gender+'"]').click();page.wait_for_function('g=>avatarLab.engine.gender===g&&document.getElementById("status").textContent.startsWith("Готово")',arg=gender)
   for selector in ['#face','#hair']:
    options=page.locator(selector+' option').evaluate_all('(els)=>els.map(e=>e.value)')
    page.select_option(selector,options[-1]);page.wait_for_timeout(200)
   page.select_option('#color','black');page.wait_for_timeout(200)
   page.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({transitionMs:0,breathing:false})')
   for pose in ['idle','melee','pistol','rifle']:
    page.locator('[data-pose="'+pose+'"]').click();page.wait_for_timeout(50)
    snap=page.evaluate('avatarLab.engine.snapshot()')
    assert snap['frame']['primaryError']<1e-6 and snap['frame']['supportError']<1e-6
    records.append({'gender':gender,'pose':pose,'face':page.locator('#face').input_value(),'hair':page.locator('#hair').input_value(),'color':page.locator('#color').input_value()})
  assert before==page.evaluate('JSON.stringify({...localStorage})')
  for width in [320,390,768]:
   page.set_viewport_size({'width':width,'height':844});page.wait_for_timeout(100)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.evaluate('avatarLab.engine.destroy()');page.goto((folder/'Report.html').as_uri());page.wait_for_function('Array.from(document.images).length===26&&Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)',timeout=60000)
  assert page.locator('img').count()==26
  for width in [320,390,768]:
   page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  for name in ['Report.html','Technical-report.html']:
   page.goto((folder/name).as_uri())
   for link in page.locator('a[href]').evaluate_all('(els)=>els.map(e=>e.getAttribute("href"))'):
    if not link.startswith(('#','http:','https:','data:')):assert (folder/link.split('#')[0]).exists(),(name,link)
  assert not errors and not network,(errors,network)
  result={'browser':'Chromium '+browser.version,'method':'Actual ZIP extracted to a new empty temporary directory; file://, no neighboring repo/server/CDN','crc_ok':True,'actual_lab_cases':records,'report_images_loaded':26,'viewport_widths':[320,390,768],'physical_device':False,'external_http_requests':network,'js_errors':errors,'local_storage_byte_unchanged':True,'html_sha256':{n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ['Avatar-Lab.html','Report.html','Technical-report.html']}}
  browser.close()
(out/'offline-package-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
