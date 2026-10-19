"""Check the offline gallery in Chromium via file://, with no HTTP server."""
import io,json
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'review/female-heads-new-library'
def run():
 errors=[];failed=[];checks=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True);p=b.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)));p.on('requestfailed',lambda r:failed.append(r.url))
  for f in sorted(D.glob('*.html')):
   p.goto(f.resolve().as_uri(),wait_until='load');p.evaluate('document.querySelectorAll("img").forEach(i=>i.loading="eager")');p.wait_for_function('()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0)')
   checks.append({'page':f.name,'images':p.locator('img').count()})
  for width in [1440,390]:
   p.set_viewport_size({'width':width,'height':1000 if width==1440 else 844});p.goto((D/'index.html').resolve().as_uri(),wait_until='load');assert not p.evaluate('document.documentElement.scrollWidth>innerWidth')
   im=Image.open(io.BytesIO(p.screenshot())).convert('RGB');im.save(D/('gallery-'+str(width)+'.webp'),lossless=True)
  assert not errors and not failed,(errors,failed)
  (D/'gallery-validation.json').write_text(json.dumps({'engine':'Chromium '+b.version,'transport':'file://','checks':checks,'page_errors':errors,'failed_requests':failed,'widths':[1440,390]},indent=2)+'\n');b.close()
if __name__=='__main__':run()
