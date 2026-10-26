"""Pixel/phase/motion checks of both actual engines, never artist acceptance."""
from pathlib import Path
import functools,threading,zipfile,base64,io,json,hashlib
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'review/rifle-seams';G=D/'Gallery';Z=zipfile.ZipFile('/workspace/Palata404-Rifle-Arms-AK47-PARTIAL-20261026.zip')
class H(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/before.html':
   data=Z.read('Avatar-Lab.html');self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(data)
  else:super().do_GET()
s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start();errors=[];missing=[];protected={};result=[];pixels=[];equips=[]
def bitmap(data):return Image.open(io.BytesIO(base64.b64decode(data))).convert('RGBA')
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page(viewport={'width':1440,'height':1800});p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
 for stage in ['before','after']:
  p.goto(f'http://127.0.0.1:{s.server_port}/'+('before.html' if stage=='before' else 'avatar-lab/'),timeout=120000);p.wait_for_function('window.avatarLab?.ready',timeout=120000)
  p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",minWidth:0,maxWidth:"none",maxHeight:"none"});e.setOptions({transitionMs:0,breathing:true,cycleMs:4000,amplitude:1,weaponSwayPx:2,weaponPreviewScale:1,background:"#f8f5ed"})}')
  for g in ['male','female']:
   p.evaluate('g=>avatarLab.engine.setGender(g)',g)
   for pose,ident in [('idle',None),('pistol','gear-pm'),('melee','gear-knife')]:
    p.evaluate('i=>avatarLab.engine.equipWeaponItem(i)',ident)
    for t in [0,1000,2000,3000,4000]:
     for visible in ([False] if pose=='idle' else [False,True]):
      data=p.evaluate('v=>{let e=avatarLab.engine;e.time=v[0];e.setLayerVisible("weapon",v[1]);e.render();return e.canvas.toDataURL().split(",")[1]}',[t,visible]);digest=hashlib.sha256(np.array(bitmap(data)).tobytes()).hexdigest();key=f'{g}/{pose}/{t}/{visible}'
      if stage=='before':protected[key]=digest
      else:assert protected[key]==digest,('protected pixels changed',key)
  if stage=='before':continue
  saved=p.evaluate('JSON.stringify({...localStorage})')
  for g in ['male','female']:
   p.evaluate('g=>avatarLab.engine.setGender(g)',g);p.evaluate('avatarLab.engine.equipWeaponItem("gear-aks")')
   for k in [.85,1,1.15]:
    for mode,cycle,amp,sway in [('standard',4000,1,2),('stress',1000,2,4)]:
     p.evaluate('v=>avatarLab.engine.setOptions({weaponPreviewScale:v[0],cycleMs:v[1],amplitude:v[2],weaponSwayPx:v[3],playbackRate:1,background:"transparent"})',[k,cycle,amp,sway])
     row=p.evaluate('''cycle=>{let e=avatarLab.engine,rows=[],first;let image=e.assets['weapon-rifle'];let corners=[[0,0],[image.naturalWidth,0],[image.naturalWidth,image.naturalHeight],[0,image.naturalHeight]];for(let i=0;i<=480;i++){e.time=i*cycle/240;let f=e.compute(),m=f.weapon.matrix;rows.push({time:e.time,primaryError:f.primaryError,supportError:f.supportError,elbow:f.arms.left.elbow,wrist:f.arms.left.wrist,hand:f.arms.left.hand,weaponMatrix:m,controlHull:corners.map(([x,y])=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]])})}return rows}''',cycle)
     assert max(v['primaryError'] for v in row)<1e-6 and max(v['supportError'] for v in row)<1e-6,(g,k,mode)
     hull=np.array([v.pop('controlHull') for v in row]);mid=(hull.max(0)+hull.min(0))/2
     record={'gender':g,'scale':k,'mode':mode,'cycleMs':cycle,'amplitude':amp,'sway':sway,'simulation_ms':2*cycle,'playbackRate':1,'samples':row,'control_rectangle_radius_px':float(np.linalg.norm(hull-mid,axis=2).max()),'matrix_loop_max_error':float(np.abs(np.array(row[0]['weaponMatrix'])-row[-1]['weaponMatrix']).max())}
     # Fully decoded native phases: slideshow timing is explicitly NOT video.
     times=[0,cycle/8,cycle/4,cycle*3/8,cycle/2,cycle*5/8,cycle*3/4,cycle*7/8,cycle,cycle*1.5,cycle*2]
     for visible in [False,True]:
      frames=[]
      for t in times:
       data=p.evaluate('v=>{let e=avatarLab.engine;e.time=v[0];e.setLayerVisible("weapon",v[1]);e.render();return e.canvas.toDataURL().split(",")[1]}',[t,visible]);frames.append(bitmap(data))
      frames[0].save(G/f'native-phases-{g}-{round(k*100)}-{mode}-{visible}.webp',save_all=True,append_images=frames[1:],duration=1000,loop=0,lossless=True)
      record['phase_times']=times;record['phase_slideshow_ms_per_frame']=1000;record['native_phase_size']=[941,1672]
     # Continuous real-time recordings at100%; all sizes have native phases.
     if k==1:
      frames=[]
      for i in range(80):
       data=p.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.setLayerVisible("weapon",true);e.render();return e.canvas.toDataURL().split(",")[1]}',i*cycle/40);im=bitmap(data);bg=Image.new('RGBA',im.size,'#f8f5ed');bg.alpha_composite(im);frames.append(bg.convert('RGB').resize((360,640),Image.Resampling.LANCZOS))
      frames[0].save(G/f'motion-{g}-{mode}.webp',save_all=True,append_images=frames[1:],duration=cycle//40,loop=0,quality=95);record['continuous_frames']=80;record['continuous_duration_ms']=cycle*2
     # Actual current-phase item matrix, screen-space RGBA, no anchor proxy.
     for phase in [0,.25,.5,.75,1]:
      probe=p.evaluate('''t=>{let e=avatarLab.engine;e.time=t;e.setLayerVisible('weapon',false);e.render();let hidden=e.compositeCtx.getImageData(0,0,941,1672).data;e.setLayerVisible('weapon',true);e.render();let shown=e.compositeCtx.getImageData(0,0,941,1672).data;let c=document.createElement('canvas');c.width=941;c.height=1672;let x=c.getContext('2d');let m=e.frame.weapon.matrix;x.transform(...m);x.drawImage(e.assets['weapon-rifle'],0,0);let gun=x.getImageData(0,0,941,1672).data;x.setTransform(1,0,0,1,0,0);x.clearRect(0,0,941,1672);for(let side of ['left','right'])e.drawMaleArm(side,e.frame,true,x);let front=x.getImageData(0,0,941,1672).data;let count=0,max=0,bad=0,alphaChanged=0;for(let y=500;y<800;y++)for(let xx=300;xx<780;xx++){let i=(y*941+xx)*4;if(front[i+3]>=254&&gun[i+3]>=254&&hidden[i+3]===255){count++;let d=Math.max(...[0,1,2].map(k=>Math.abs(shown[i+k]-hidden[i+k])));max=Math.max(max,d);if(d>2)bad++;if(shown[i+3]!==hidden[i+3])alphaChanged++}}return {nativeMatrix:e.frame.weapon.matrix,opaque_front_samples:count,max_RGB_difference:max,samples_over2:bad,alpha_changed:alphaChanged}}''',phase*cycle)
      assert probe['samples_over2']==0 and probe['alpha_changed']==0,(g,k,mode,phase,probe)
      pixels.append(dict(gender=g,scale=k,mode=mode,phase=phase,**probe))
     result.append(record);print(g,k,mode,'two cycles + phases',flush=True)
   # Measure erase-mask alternative, without changing implementation.
   p.evaluate('()=>{let e=avatarLab.engine;e.time=0;e.setOptions({weaponPreviewScale:1,cycleMs:4000,amplitude:1,weaponSwayPx:2,background:"transparent"});e.setLayerVisible("weapon",true);e.render()}')
   comparison=p.evaluate('''()=>{let e=avatarLab.engine,w=e.weaponCtx,desc=Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype,'globalCompositeOperation'),normal=e.compositeCtx.getImageData(0,0,941,1672).data.slice();Object.defineProperty(w,'globalCompositeOperation',{configurable:true,get(){return desc.get.call(w)},set(v){desc.set.call(w,v==='source-atop'?'destination-out':v)}});e.render();let erased=e.compositeCtx.getImageData(0,0,941,1672).data,alphaLost=0,maxLoss=0;for(let i=3;i<normal.length;i+=4)if(normal[i]>erased[i]+2){alphaLost++;maxLoss=Math.max(maxLoss,normal[i]-erased[i])}delete w.globalCompositeOperation;e.render();return {pixels_losing_more_than2_alpha:alphaLost,max_alpha_loss:maxLoss,chosen:'hybrid: source-atop edges, opaque-core item cutout only over opaque underlying skin; full erase rejected due AA coverage loss'}}''');equips.append({'gender':g,'erase_alternative':comparison})
   for color,name in [('#fff','white'),('#777','gray'),('#000','black'),('#0f0','green')]:
    for visible in [False,True]:
     data=p.evaluate('v=>{let e=avatarLab.engine;e.time=0;e.setOptions({background:v[0]});e.setLayerVisible("weapon",v[1]);e.render();return e.canvas.toDataURL().split(",")[1]}',[color,visible]);bitmap(data).save(G/f'background-{g}-{name}-{visible}.webp',lossless=True)
   p.evaluate('()=>{let e=avatarLab.engine;e.time=1234;e.setLayerVisible("weapon",true);e.render()}');frame=p.evaluate('JSON.stringify(avatarLab.engine.snapshot().frame)');p.evaluate('avatarLab.engine.setLayerVisible("weapon",false)');assert p.evaluate('JSON.stringify(avatarLab.engine.snapshot().frame)')==frame
   p.evaluate('avatarLab.engine.equipWeaponItem(null)');assert p.evaluate('avatarLab.engine.pose')=='idle'
  assert p.evaluate('JSON.stringify({...localStorage})')==saved
  p.reload();p.wait_for_function('window.avatarLab?.ready');assert p.evaluate('JSON.stringify({...localStorage})')==saved
 b.close()
s.shutdown();assert not errors and not missing
(D/'Evidence/browser-matrix.json').write_text(json.dumps({'cases':result,'total_samples':len(result)*481,'protected_frames_RGBA_exact':len(protected),'diagnostic_hide_same_pose_time':True,'real_unequip_idle':True,'localStorage_unchanged_and_reload':True,'js_errors':errors,'http_errors':missing,'full_wardrobe_and_live_not_tested':True},indent=2)+'\n')
(D/'Evidence/compositor-pixels.json').write_text(json.dumps({'cases':pixels,'erase_comparison':equips,'warning':'Mask coverage and mechanical correctness are not anatomy acceptance; native image inspection required'},indent=2)+'\n');print('Actual browser matrix complete')
