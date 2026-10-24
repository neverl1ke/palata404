"""Compare the same alpha-composition diagnostic in prior and current runtime."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import threading,functools,tempfile,tarfile,io,subprocess,json
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'review/female-donor-arm-pass';rows=[]
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def serve(path):
 s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=str(path)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
with tempfile.TemporaryDirectory() as td:
 old=Path(td)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive','77199cd','avatar-core','avatar-lab'],cwd=R))) as t:t.extractall(old,filter='data')
 for n in ['base_male.png','base_female.png','paper-doll-data.js','paper-doll.js','hair-color.js','assets','review']:(old/n).symlink_to(R/n,target_is_directory=(R/n).is_dir())
 servers=[serve(old),serve(R)]
 try:
  with sync_playwright() as w:
   b=w.chromium.launch()
   for version,server in zip(['77199cd','current'],servers):
    p=b.new_page(viewport={'width':1440,'height':1800});p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",maxWidth:"none",maxHeight:"none"});e.setOptions({breathing:false,background:"transparent"});e.time=0;e.setPose("melee")}')
    row=p.evaluate('''()=>{let e=avatarLab.engine,a=e.ctx.getImageData(0,0,941,1672).data,ids=[];for(let i=3;i<a.length;i+=4)if(a[i]>0&&a[i]<240)ids.push((i-3)/4);let stride=Math.max(1,Math.floor(ids.length/200)),samples=ids.filter((_,i)=>i%stride===0).slice(0,200).map(i=>[i,[...a.slice(i*4,i*4+4)]]);e.setOptions({background:'#fff'});let out=e.ctx.getImageData(0,0,941,1672).data,max=0,worst=null,sum=0,n=0;for(let [i,c]of samples)for(let k=0;k<3;k++){let expected=c[k]*c[3]/255+255-c[3],error=Math.abs(out[i*4+k]-expected);if(error>max){max=error;worst={x:i%941,y:Math.floor(i/941),channel:k,transparent:c,white:[...out.slice(i*4,i*4+4)],expected}}sum+=error;n++}return{samples:samples.length,max_error:max,mean_error:sum/n,worst,criterion_max_error:4,passed:max<=4}}''');rows.append({'runtime':version,**row});p.close()
   b.close()
 finally:
  for s in servers:s.shutdown()
(O/'alpha-composition-baseline.json').write_text(json.dumps({'same_case':'male melee, 100%, t0, 200 sampled alpha-edge pixels, white background','results':rows,'note':'Diagnostic failure is retained, not hidden by a higher tolerance. Numeric difference alone is not proof of a visible halo.'},indent=2)+'\n');print(rows)
