"""Verify approved PNG provenance, the breathing cycle and fixed rifle grips."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import functools,threading,base64,hashlib,io,json
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];out=root/'review/female-arms-approved-20261103';out.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
phases=[];errors=[]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch();page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('**/female-art-check.html',lambda r:r.fulfill(content_type='text/html',body='<canvas id="test"></canvas>'))
  page.goto(f'http://127.0.0.1:{server.server_port}/female-art-check.html')
  page.evaluate("""async()=>{window.module=await import('/avatar-core/approved/female-scene.mjs');window.scene=await module.createScene()}""")
  for weapon in [False,True]:
   frames={}
   for time in [0,125,500,1000,2000,3000,3875,4000]:
    raw=page.evaluate('([t,w])=>scene.render(t,w).toDataURL().split(",")[1]',[time,weapon]);rgba=np.array(Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGBA'));frames[time]=rgba
    phases.append({'gender':'female','weapon':weapon,'time_ms':time,'rgba_sha256':hashlib.sha256(rgba.tobytes()).hexdigest()})
    if time in [0,1000,3000]:Image.fromarray(rgba).save(out/f'female-{"rifle" if weapon else "no-weapon"}-{time}.png')
   assert np.array_equal(frames[0],frames[4000]),'Breathing loop does not close'
   assert not np.array_equal(frames[0],frames[1000]),'Breathing is stationary'
   assert np.array_equal(frames[0][:275],frames[1000][:275]),'Head moved out of cosmetic registration'
   assert np.array_equal(frames[0][925:],frames[1000][925:]),'Legs moved'
   # Compare approved art decoded through the same browser pixel format, not raw hidden RGB.
   expected=page.evaluate('''async w=>{let i=new Image;i.src='/avatar-core/approved/female/Approved20261103/arms-'+(w?'rifle':'no-weapon')+'.png';await i.decode();let c=document.createElement('canvas');c.width=1200;c.height=1672;c.getContext('2d').drawImage(i,0,0);return c.toDataURL().split(',')[1]}''',weapon)
   approved=np.array(Image.open(io.BytesIO(base64.b64decode(expected))).convert('RGBA'));assert np.array_equal(frames[0],approved),'Rest frame differs from approved art'
  grip=page.evaluate('''()=>{const{approvedPose:p,breathingPoint:point,breathAt}=module;return Array.from({length:33},(_,i)=>{let t=i*125,b=breathAt(t),a=point(p.primaryHand,b),s=point(p.supportHand,b);return{time_ms:t,span:Math.hypot(s[0]-a[0],s[1]-a[1]),primaryShift:a.map((v,k)=>v-p.primaryHand[k]),supportShift:s.map((v,k)=>v-p.supportHand[k])}})}''')
  for g in grip:
   assert max(abs(x-y)for x,y in zip(g['primaryShift'],g['supportShift']))<1e-10,'Grip moved relative to rifle'
  browser.close()
 assert not errors,errors
 (out/'render-proof.json').write_text(json.dumps({'phases':phases,'grip_cycle':grip,'page_errors':errors,'approved_rest_frames_exact':True,'cycle_ms':4000,'rifle_scale':.428},indent=2)+'\n');print('PASS: approved rest frames, 16 cycle frames, fixed grips, head/leg registration')
finally:server.shutdown();server.server_close()
