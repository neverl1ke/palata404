"""Measured rAF timing of the real lab, not a synthetic skeleton benchmark."""
import functools,threading,json,argparse
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode',choices=['before','after'],help='Compare rigid-cell batching disabled/enabled on the same engine')
parser.add_argument('--output-dir',default='review/avatar-core-1')
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=str(ROOT)));threading.Thread(target=s.serve_forever,daemon=True).start();records=[]
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch();p=b.new_page(viewport={'width':1440,'height':1100});p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('v=>{avatarLab.engine.setOptions({skinBatching:v});avatarLab.engine.setPose("rifle")}',args.mode == 'after'); p.wait_for_timeout(400)
  for g in ['male','female']:
   p.evaluate('async g=>{await avatarLab.engine.setGender(g);avatarLab.engine.pause(false)}',g)
   r=p.evaluate('''async()=>{const times=[];let last=performance.now();for(let i=0;i<100;i++){await new Promise(requestAnimationFrame);const t=performance.now();times.push(t-last);last=t;}times.sort((a,b)=>a-b);return {frames:100,meanMs:times.reduce((a,b)=>a+b)/times.length,p95Ms:times[94],display:avatarLab.engine.lastDraw};}''');r.update({'skinBatching':args.mode == 'after','gender':g,'pose':'rifle','viewport':[1440,1100],'browser':'Chromium '+b.version,'note':'Headless shared execution host; not a physical mobile benchmark'});records.append(r);print(g,r['meanMs'],r['p95Ms'],flush=True)
  b.close()
finally:s.shutdown();s.server_close()
out=ROOT/args.output_dir/('performance-'+args.mode+'.json');out.write_text(json.dumps(records,indent=2)+'\n')
