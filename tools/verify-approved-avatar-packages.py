from pathlib import Path
import functools,threading,base64,io,json,hashlib
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np
import argparse
from zipfile import ZipFile
parser=argparse.ArgumentParser(description='Compare game scene renderers with the exact self-contained Labs in the approved ZIPs.')
parser.add_argument('--male-zip',required=True,type=Path)
parser.add_argument('--female-zip',required=True,type=Path)
parser.add_argument('--output',type=Path,default=Path('test-results/approved-package-proof'))
args=parser.parse_args()
root=Path(__file__).resolve().parents[1];review=args.output;review.mkdir(parents=True,exist_ok=True);sources={}
for gender,archive in [('male',args.male_zip),('female',args.female_zip)]:
 with ZipFile(archive) as zipped:
  entry=next(n for n in zipped.namelist() if n.endswith('Avatar-Lab.html'))
  sources[gender]=zipped.read(entry).decode('utf-8')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
results=[]
def pixels(data):return np.array(Image.open(io.BytesIO(base64.b64decode(data.split(',')[1]))).convert('RGBA'))
with sync_playwright() as pw:
 browser=pw.chromium.launch();context=browser.new_context();errors=[];context.on('page',lambda p:p.on('pageerror',lambda e:errors.append(str(e))))
 for gender in ['male','female']:
  print('checking',gender,flush=True)
  reference=context.new_page();reference.route('**/reference.html',lambda r:r.fulfill(content_type='text/html',body=sources[gender]));reference.goto(url+'/reference.html',wait_until='load');reference.wait_for_function('window.avatarTrial?.ready||window.femaleReview?.ready')
  actual=context.new_page();actual.route('**/test-approved.html',lambda r:r.fulfill(content_type='text/html',body='<canvas id="subject"></canvas>'));actual.goto(url+'/test-approved.html');actual.evaluate('''async g=>{const m=await import('/avatar-core/approved/'+g+'-scene.mjs');window.approvedScene=await m.createScene(document.getElementById('subject'))}''',gender)
  for weapon in [False,True]:
   for time in [0,1000,2000,3000]:
    a=actual.evaluate('''([t,w])=>approvedScene.render(t,w).toDataURL()''',[time,weapon]);b=reference.evaluate('''([t,w])=>{const a=window.avatarTrial;if(a){a.state.play=false;a.engine.pause();a.render({time:t,stage:'After',scale:1.07,weapon:w,background:'transparent',breath:true,amplitude:1});return a.canvas.toDataURL()}const f=window.femaleReview;f.state.play=false;f.engine.pause();f.render({time:t,weapon:w?'0.9':'off',background:'transparent',amplitude:1});return f.scene.toDataURL()}''',[time,weapon])
    x,y=pixels(a),pixels(b);same=np.array_equal(x,y);result={'gender':gender,'time_ms':time,'weapon':weapon,'exact':same,'shape':list(x.shape),'changed_pixels':int(np.any(x!=y,axis=2).sum()) if x.shape==y.shape else None};result['rgba_sha256']=hashlib.sha256(x.tobytes()).hexdigest();results.append(result);print(result,flush=True)
    if time==0:
     Image.fromarray(x).save(review/f'{gender}-approved-{"rifle" if weapon else "no-weapon"}.png')
    if not same:raise AssertionError(result)
  actual.close();reference.close()
 browser.close()
assert not errors,errors
(review/'archive-renderer-equivalence.json').write_text(json.dumps({'phases':results,'page_errors':errors},indent=2)+'\n');server.shutdown();server.server_close()
