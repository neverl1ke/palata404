"""Verify the actual extracted offline ZIP, not its source directory."""
from pathlib import Path
import hashlib,json,tempfile,zipfile,base64,io,re
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-exact-reference-pass';archive=ROOT.parent/'Male-Exact-Reference-Review.zip'
with tempfile.TemporaryDirectory() as td:
 with zipfile.ZipFile(archive) as z:assert z.testzip() is None;z.extractall(td)
 package=Path(td)/'Male-Exact-Reference-Review';manifest=json.loads((package/'Package-SHA256.json').read_text())
 for row in manifest:assert hashlib.sha256((package/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
 embedded=re.findall(r'src="data:image/[^;]+;base64,([^"]+)"',(package/'Report.html').read_text());assert embedded
 for data in embedded:Image.open(io.BytesIO(base64.b64decode(data))).verify()
 errors=[];requests=[];poses=[];views=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch();page=browser.new_page(viewport={'width':1280,'height':950});page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
  page.goto((package/'Report.html').as_uri());page.evaluate('document.images[0].loading="eager"');page.wait_for_function('document.images.length>0 && document.images[0].complete && document.images[0].naturalWidth>0',timeout=60000);assert page.locator('h1').count()==1
  for width in [320,390,768,1440]:
   page.set_viewport_size({'width':width,'height':900});views.append({'width':width,'horizontal_overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')});assert not views[-1]['horizontal_overflow'];page.screenshot(path=str(OUT/f'offline-report-{width}.png'))
  page.goto((package/'Avatar-Lab.html').as_uri());page.wait_for_function('window.avatarLab?.ready');page.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({breathing:false,transitionMs:0})');before=page.evaluate('JSON.stringify({...localStorage})')
  for gender in ['male','female']:
   page.evaluate('g=>avatarLab.engine.setGender(g)',gender)
   for pose in ['idle','rifle','pistol','melee']:
    page.evaluate('p=>avatarLab.engine.setPose(p)',pose);s=page.evaluate('avatarLab.engine.snapshot()');assert s['frame']['primaryError']<1e-6 and s['frame']['supportError']<1e-6;poses.append({'gender':gender,'pose':pose,'primaryError':s['frame']['primaryError'],'supportError':s['frame']['supportError']})
  assert before==page.evaluate('JSON.stringify({...localStorage})');assert not errors and not requests,(errors,requests);browser.close()
 result={'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'zip_bytes':archive.stat().st_size,'manifest_files_verified':len(manifest),'embedded_report_images_decoded':len(embedded),'extracted_file_scheme':True,'views':views,'poses':poses,'js_errors':errors,'network_requests':requests,'storage_unchanged':True,'artistic_approval':False}
 (OUT/'offline-package-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
