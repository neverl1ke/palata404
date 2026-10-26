"""Actual Chromium evidence from immutable candidate ZIP or current runtime."""
from pathlib import Path
import argparse,base64,io,json,functools,threading,zipfile
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from PIL import Image
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'review/rifle-seams';G=D/'Gallery';G.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('stage');p.add_argument('--baseline',action='store_true');p.add_argument('--diagnostic',action='store_true');a=p.parse_args();z=zipfile.ZipFile('/workspace/Palata404-Rifle-Arms-AK47-PARTIAL-20261026.zip')
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/candidate.html':
   b=z.read('Avatar-Lab.html');self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b)
  else:super().do_GET()
s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start();rows=[];errors=[]
def save(data,name,crop=None):
 im=Image.open(io.BytesIO(base64.b64decode(data))).convert('RGBA')
 if crop:im=im.crop(crop)
 im.save(G/(a.stage+'-'+name+'.webp'),lossless=True)
with sync_playwright() as pw:
 b=pw.chromium.launch();page=b.new_page(viewport={'width':1440,'height':1800});page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{s.server_port}/'+('candidate.html' if a.baseline else 'avatar-lab/'),timeout=120000);page.wait_for_function('window.avatarLab?.ready',timeout=120000)
 page.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",minWidth:0,maxWidth:"none",maxHeight:"none"});e.setOptions({transitionMs:0,breathing:true,cycleMs:4000,amplitude:1,weaponSwayPx:2,background:"transparent"})}')
 for gender in ['male','female']:
  page.evaluate('g=>avatarLab.engine.setGender(g)',gender);page.evaluate('avatarLab.engine.equipWeaponItem("gear-aks")')
  for k in [.85,1,1.15]:
   for t in ([0,500,1000,1500,2000,2500,3000,3500,4000,6000,8000] if k==1 else [0,1000,3000,4000]):
    for visible in [False,True]:
     result=page.evaluate('v=>{let e=avatarLab.engine;e.time=v[0];e.setOptions({weaponPreviewScale:v[1]});e.setLayerVisible("weapon",v[2]);e.render();return {image:e.canvas.toDataURL().split(",")[1],frame:e.snapshot().frame}}',[t,k,visible]);save(result.pop('image'),f'{gender}-{round(k*100)}-{t}-{visible}',None if t==0 and k==1 else (140,280,910,820));rows.append(dict(gender=gender,scale=k,time=t,visible=visible,frame=result['frame']))
   if a.diagnostic and k==1:
    for t in [0,1000,3000]:
     page.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.render()}',t)
     for layer in ['torso','right','left','front-right','front-left']:
      data=page.evaluate('layer=>{let e=avatarLab.engine,c=document.createElement("canvas");c.width=941;c.height=1672;let x=c.getContext("2d");if(layer==="torso"){let old=e.compositeCtx;e.compositeCtx=x;e.drawPinnedTorso(e.frame,e.assets["torso-pose-rifle"]||e.bitmaps.torso);e.compositeCtx=old}else{let front=layer.startsWith("front-"),side=layer.replace("front-","");e.drawMaleArm(side,e.frame,front,x)}return c.toDataURL().split(",")[1]}',layer)
      save(data,f'{gender}-isolate-{layer}-{t}',(120,270,760,800))
  page.evaluate('avatarLab.engine.equipWeaponItem(null)');assert page.evaluate('avatarLab.engine.pose')=='idle'
 b.close()
s.shutdown();assert not errors; (D/'Evidence'/f'{a.stage}-captures.json').write_text(json.dumps({'baseline_from_exact_ZIP':a.baseline,'cases':rows,'js_errors':errors,'real_unequip_idle':True},indent=2)+'\n');print(a.stage,len(rows),'actual phase captures')
