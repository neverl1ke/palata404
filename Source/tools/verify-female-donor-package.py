"""Verify the actual extracted ZIP, hashes, embedded report and offline Lab."""
from pathlib import Path
import base64,hashlib,io,json,re,tempfile,zipfile
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'review/female-donor-arm-pass';z=ROOT.parent/'Avatar-Female-Donor-Review.zip';errors=[];network=[];poses=[]
with tempfile.TemporaryDirectory() as td:
 with zipfile.ZipFile(z) as archive:assert archive.testzip() is None;archive.extractall(td)
 d=Path(td)/'Avatar-Female-Donor-Review';manifest=json.loads((d/'Package-SHA256.json').read_text())
 for name,row in manifest.items():p=d/name;assert p.stat().st_size==row['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
 text=(d/'Report.html').read_text();images=re.findall(r'<img[^>]+src="data:image/[^;]+;base64,([^"]+)',text)
 for b in images:Image.open(io.BytesIO(base64.b64decode(b))).verify()
 with sync_playwright() as w:
  b=w.chromium.launch();p=b.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)));p.route('http**://**/*',lambda r:(network.append(r.request.url),r.abort()));p.goto((d/'Report.html').as_uri());p.wait_for_function('Array.from(document.querySelectorAll("video")).every(v=>v.readyState>=1)',timeout=60000);assert p.locator('video').count()==20
  for width in [320,390,768,1440]:p.set_viewport_size({'width':width,'height':844});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  p.close();p=b.new_page(viewport={'width':1440,'height':1100});p.on('pageerror',lambda e:errors.append(str(e)));p.route('http**://**/*',lambda r:(network.append(r.request.url),r.abort()));p.goto((d/'Avatar-Lab.html').as_uri());p.wait_for_function('window.avatarLab?.ready',timeout=60000);p.evaluate('avatarLab.engine.pause()');storage=p.evaluate('JSON.stringify({...localStorage})')
  for gender in ['male','female']:
   p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
   for pose in ['idle','melee','pistol','rifle']:
    for visible in [True,False]:
     p.evaluate('a=>{let e=avatarLab.engine;e.setPose(a[0]);e.time+=e.options.transitionMs+1;e.setLayerVisible("weapon",a[1]);e.render()}',[pose,visible]);f=p.evaluate('avatarLab.engine.frame');assert f['primaryError']<1e-6 and f['supportError']<1e-6,(gender,pose,visible,f['primaryError'],f['supportError']);poses.append({'gender':gender,'pose':pose,'visible':visible})
  assert p.evaluate('JSON.stringify({...localStorage})')==storage;b.close()
assert not errors and not network
result={'zip_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'verified_files':len(manifest),'extracted_file_scheme':True,'embedded_images_decoded':len(images),'embedded_videos_loaded':20,'poses':poses,'js_errors':errors,'network_requests':network};(O/'offline-package-check.json').write_text(json.dumps(result,indent=2)+'\n');print('Offline extracted ZIP verified:',len(manifest),'files,',len(images),'embedded images, 20 videos, 16 pose/visibility states.')
