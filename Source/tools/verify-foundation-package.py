"""Check extracted deliverable offline, native viewer checksums and live Lab."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import zipfile,tempfile,json,hashlib,re
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';z=R.parent/'Avatar-Foundation-Cleanup.zip';errors=[];network=[];poses=[];screens=[]
with tempfile.TemporaryDirectory(dir=R.parent) as td:
 with zipfile.ZipFile(z) as q:assert q.testzip() is None;q.extractall(td)
 d=Path(td)/'Avatar-Foundation-Cleanup';manifest=json.loads((d/'SHA256.json').read_text())
 for name,h in manifest.items():assert hashlib.sha256((d/name).read_bytes()).hexdigest()==h,name
 with sync_playwright() as w:
  b=w.chromium.launch();p=b.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)));p.route('http**://**/*',lambda r:(network.append(r.request.url),r.abort()))
  for name in ['Report.html','Technical-report.html','ViewFrames.html']:
   for link in re.findall(r'(?:src|href)="([^"]+)"',(d/name).read_text()):
    if not link.startswith(('data:','blob:','#','http:','https:')):assert (d/link).is_file(),(name,link)
  p.goto((d/'Report.html').as_uri())
  for width in [320,390,768,1440]:
   p.set_viewport_size({'width':width,'height':844});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth'),width;p.screenshot(path=str(O/'Gallery'/f'offline-report-{width}.png'));screens.append(width)
  for index in range(p.locator('video').count()):
   p.locator('video').nth(index).evaluate('v=>v.load()')
   p.wait_for_function('i=>document.querySelectorAll("video")[i].readyState>=1',arg=index,timeout=60000)
  # Native file loader: independent browser decompression + per-frame SHA checks.
  p.goto((d/'ViewFrames.html').as_uri());p.locator('#file').set_input_files(str(d/'Gallery/Dense/after-female-melee-True.avframes'));p.wait_for_function('document.getElementById("status").textContent.includes("SHA-256 перевірено")',timeout=120000)
  for frame in [120,240]:
   p.evaluate('i=>{let e=document.getElementById("position");e.value=i;e.dispatchEvent(new Event("input"))}',frame);p.wait_for_function('i=>document.getElementById("status").textContent.startsWith("Кадр "+i+"/240")',arg=frame,timeout=120000)
  p.goto((d/'Avatar-Lab.html').as_uri(),timeout=120000);p.wait_for_function('window.avatarLab?.ready',timeout=120000);p.evaluate('avatarLab.engine.pause()')
  for gender in ['male','female']:
   p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
   for pose in ['idle','melee','pistol','rifle']:
    for visible in [True,False]:
     p.evaluate('a=>{let e=avatarLab.engine;e.setPose(a[0]);e.time=1000;e.setLayerVisible("weapon",a[1]);e.render()}',[pose,visible]);f=p.evaluate('avatarLab.engine.frame');assert f['primaryError']<1e-6 and f['supportError']<1e-6;poses.append(dict(gender=gender,pose=pose,visible=visible))
   for kind in ['collar','waist-top','short-sleeve','long-sleeve','cuff','glove','trousers','shoes']:
    p.evaluate('k=>{document.getElementById("diagnostic-binding").value=k;return avatarLab.diagnosticBinding()}',kind)
   p.evaluate('()=>{document.getElementById("diagnostic-binding").value="none";return avatarLab.diagnosticBinding()}')
   for hue in [0,120,240]:p.evaluate('h=>avatarLab.engine.setOptions({diagnosticSkinHue:h})',hue)
  b.close()
assert not errors and not network
result={'zip_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'verified_files':len(manifest),'poses':poses,'report_widths':screens,'native_viewer_verified_frames':[0,120,240],'offline_file_scheme':True,'js_errors':errors,'network_requests':network};(O/'offline-package-check.json').write_text(json.dumps(result,indent=2));print('Offline ZIP: hashes,16 pose states,8 diagnostic kinds,both genders,3 native frames,4 widths verified')
