"""Verify the actual extracted hand-authoring ZIP via file:// Chromium."""
from pathlib import Path
import hashlib,json,tempfile,zipfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-hand-art-kit';archive=ROOT.parent/'Male-Hand-Art-Kit-2.1.zip'
with tempfile.TemporaryDirectory() as td:
 with zipfile.ZipFile(archive) as z:assert z.testzip() is None;z.extractall(td)
 folder=Path(td)/'Male-Hand-Art-Kit-2.1';manifest=json.loads((folder/'Package-SHA256.json').read_text())
 for r in manifest:assert hashlib.sha256((folder/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
 errors=[];requests=[];failed=[];cases=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch();p=browser.new_page(viewport={'width':1440,'height':1050});p.on('pageerror',lambda e:errors.append(str(e)));p.on('requestfailed',lambda r:failed.append(r.url));p.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
  p.goto((folder/'Report.html').as_uri());p.wait_for_function('window.handKitReady&&Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
  for i in range(3):
   p.select_option('#hand',str(i));p.wait_for_function('window.handKitReady')
   for control in ['arm','weapon','front','mask','guides','blank']:
    initial=p.locator('#'+control).is_checked();p.locator('#'+control).set_checked(not initial);p.wait_for_function('window.handKitReady');p.locator('#'+control).set_checked(initial);p.wait_for_function('window.handKitReady')
   p.locator('#layers').screenshot(path=str(OUT/f'inspector-{i}.png'));cases.append(p.locator('#info').inner_text())
  for width in [320,390,768]:
   p.set_viewport_size({'width':width,'height':844});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
  p.goto((folder/'Technical-report.html').as_uri());assert p.locator('h1').count()==1
  p.goto((folder/'Avatar-Lab.html').as_uri());p.wait_for_function('window.avatarLab?.ready');p.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({breathing:false,transitionMs:0})');storage=p.evaluate('JSON.stringify({...localStorage})');poses=[]
  for gender in ['male','female']:
   p.locator(f'[data-gender="{gender}"]').click();p.wait_for_function('g=>avatarLab.engine.gender===g&&document.getElementById("status").textContent.startsWith("Готово")',arg=gender)
   for pose in ['idle','melee','pistol','rifle']:
    p.locator(f'[data-pose="{pose}"]').click();p.wait_for_function('document.getElementById("previous-arms").complete&&document.getElementById("previous-arms").naturalWidth>0');f=p.evaluate('avatarLab.engine.frame');assert f['primaryError']<1e-6 and f['supportError']<1e-6;poses.append([gender,pose])
  assert storage==p.evaluate('JSON.stringify({...localStorage})');assert not errors and not requests and not failed,(errors,requests,failed)
  result={'archive':archive.name,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'crc':'passed','manifest_files_verified':len(manifest),'browser':browser.version,'extracted_file_uri':True,'inspector_cases':cases,'controls_toggled_per_hand':6,'runtime_cases':poses,'viewport_emulation':[320,390,768],'physical_device':False,'http_requests':requests,'js_errors':errors,'request_failures':failed,'storage_unchanged':True,'new_artwork_count':0,'new_artwork_integrated':False};browser.close()
(OUT/'offline-package-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
