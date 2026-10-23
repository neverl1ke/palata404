"""Record real RAF playback; report actual decoded frame timestamps, no FPS claim."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
import threading,functools,json,base64,subprocess
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';G=O/'Gallery';rows=[];errors=[]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
with sync_playwright() as pw:
 b=pw.chromium.launch()
 for version,root in [('before',R.parent/'avatar-foundation-baseline'),('after',R)]:
  s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();p=b.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)));p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('avatarLab.engine.pause()')
  for gender in ['male','female']:
   p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
   for pose in (['melee'] if version=='before' else ['idle','melee','pistol','rifle']):
    p.evaluate('p=>{let e=avatarLab.engine;e.pause();e.time=0;e.setPose(p);e.setOptions({breathing:true,background:"#f8f5ed",playbackRate:1});Object.assign(e.canvas.style,{width:"470px",height:"836px",maxWidth:"none",maxHeight:"none"})}',pose)
    result=p.evaluate('''async()=>{let e=avatarLab.engine,s=e.canvas.captureStream(30),r=new MediaRecorder(s,{mimeType:'video/webm;codecs=vp9',videoBitsPerSecond:2000000}),chunks=[],samples=[],active=true;r.ondataavailable=x=>chunks.push(x.data);let done=new Promise(x=>r.onstop=x);let monitor=()=>{if(!active)return;let f=e.frame;samples.push({time:e.time,primary:f.primaryError,support:f.supportError,elbow:f.arms.right.elbow,grip:f.arms.right.grip});requestAnimationFrame(monitor)};r.start();e.pause(false);requestAnimationFrame(monitor);await new Promise((resolve,reject)=>{let start=performance.now(),timer=setInterval(()=>{if(e.time>=4050){clearInterval(timer);resolve()}else if(performance.now()-start>30000){clearInterval(timer);reject(Error('RAF cycle did not finish in 30s'))}},25)});active=false;e.pause();r.stop();await done;s.getTracks().forEach(t=>t.stop());let data=await new Promise(x=>{let f=new FileReader();f.onload=()=>x(f.result.split(',')[1]);f.readAsDataURL(new Blob(chunks))});return {data,samples}}''')
    path=G/f'{version}-{gender}-{pose}-raf.webm';path.write_bytes(base64.b64decode(result.pop('data')));probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(path)],text=True));pts=[float(f['best_effort_timestamp_time']) for f in probe['frames']];assert len(pts)>10 and result['samples'][-1]['time']>=4000;assert max(x['primary'] for x in result['samples'])<1e-6;assert max(x['support'] for x in result['samples'])<1e-6;rows.append(dict(version=version,gender=gender,pose=pose,file=path.name,decoded_frames=len(pts),pts_seconds=pts,max_gap_seconds=max(b-a for a,b in zip(pts,pts[1:])),**result));print(version,gender,pose,len(pts),'decoded frames',flush=True)
  p.close();s.shutdown()
 b.close()
(O/'Evidence/real-raf-motion.json').write_text(json.dumps({'recordings':rows,'errors':errors,'physical_device':False,'renderer':'Chromium real requestAnimationFrame, Canvas MediaRecorder at requested 30fps; see actual PTS'},indent=2));assert not errors
