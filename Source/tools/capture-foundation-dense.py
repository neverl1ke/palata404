"""Actual Canvas samples at 1000/60ms; lossless animated frames, exact timing manifest.
Transparent samples can be inspected on five backgrounds without rerendering the
subject. Direct rendered backgrounds are independently checked at cycle extremes.
This deterministic capture is not a claim of real-time 60fps performance.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
import base64,functools,threading,io,json,hashlib,gc,time,itertools,zlib,struct
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';G=O/'Gallery';D=G/'Dense';D.mkdir(exist_ok=True);rows=[];errors=[];http=[];durations=[50]*80
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def shot(p):
 return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGBA')

def hashim(im):
 a=np.array(im);a[a[:,:,3]==0]=0;return hashlib.sha256(a.tobytes()).hexdigest()
def encode(frames,path):
 # Exact RGBA delta pack: source pixels, not codec-dependent alpha blending.
 chunks=[];entries=[];previous=np.zeros((1672,941,4),dtype='uint8');offset=0
 for i,frame in enumerate(frames):
  current=np.array(frame);raw=np.bitwise_xor(current,previous).tobytes();chunk=zlib.compress(raw,6);chunks.append(chunk);entries.append({'time_ms':i*4000/240,'offset':offset,'bytes':len(chunk),'rgba_sha256':hashlib.sha256(current.tobytes()).hexdigest()});offset+=len(chunk);previous=current
 header=json.dumps({'version':1,'format':'RGBA uint8, XOR previous frame, zlib','size':[941,1672],'logical_step_ms':1000/60,'frames':entries},separators=(',',':')).encode();pack=path.with_suffix('.avframes')
 with pack.open('wb') as f:
  f.write(b'P404F1\n');f.write(struct.pack('<I',len(header)));f.write(header)
  for chunk in chunks:f.write(chunk)
 # Independent readback checks every source byte, including invisible RGB.
 data=pack.read_bytes();n=struct.unpack('<I',data[7:11])[0];h=json.loads(data[11:11+n]);previous=np.zeros((1672,941,4),dtype='uint8')
 for entry,original in zip(h['frames'],frames):
  at=11+n+entry['offset'];delta=np.frombuffer(zlib.decompress(data[at:at+entry['bytes']]),dtype='uint8').reshape(1672,941,4);previous=np.bitwise_xor(previous,delta);assert previous.tobytes()==original.tobytes()
 # Convenient game-size animation; the native pack is the pixel-exact proof.
 previews=[frames[i].resize((400,711),Image.Resampling.LANCZOS) for i in range(0,240,3)]
 previews[0].save(path,save_all=True,append_images=previews[1:],duration=durations,lossless=True,method=0,loop=0,kmin=9,kmax=17)
 return {'native_pack':str(pack.relative_to(G)),'native_pack_bytes':pack.stat().st_size,'native_pack_sha256':hashlib.sha256(data).hexdigest(),'native_frames_verified':len(frames),'native_RGBA_all_bytes_exact':True,'preview_size':[400,711],'preview_step_ms':50,'preview_is_resized':True}
with sync_playwright() as pw:
 browser=pw.chromium.launch()
 for version,root in [('before',R.parent/'avatar-foundation-baseline'),('after',R)]:
  server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start();p=browser.new_page(viewport={'width':1400,'height':1800});p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:http.append([r.url,r.status]) if r.status>=400 else None);p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",maxWidth:"none",maxHeight:"none"});e.setOptions({breathing:true,background:"transparent"})}')
  for gender in ['male','female']:
   p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
   for pose in (['melee'] if version=='before' else ['melee','idle','pistol','rifle']):
    p.evaluate('p=>{let e=avatarLab.engine;e.setPose(p);e.time=0}',pose)
    for visible in ([True] if version=='before' else [True,False]):
     p.evaluate('v=>avatarLab.engine.setLayerVisible("weapon",v)',visible);frames=[];metrics=[];start=time.monotonic()
     print('start',version,gender,pose,visible,flush=True)
     existing=D/f'{version}-{gender}-{pose}-{visible}.avframes'
     if existing.exists():
      data=existing.read_bytes();hn=struct.unpack('<I',data[7:11])[0];header=json.loads(data[11:11+hn]);previous=np.zeros((1672,941,4),dtype='uint8')
      for entry in header['frames']:
       at=11+hn+entry['offset'];delta=np.frombuffer(zlib.decompress(data[at:at+entry['bytes']]),dtype='uint8').reshape(1672,941,4);previous=np.bitwise_xor(previous,delta);assert hashlib.sha256(previous.tobytes()).hexdigest()==entry['rgba_sha256'];frames.append(Image.fromarray(previous.copy()))
      metrics=p.evaluate('''()=>{let e=avatarLab.engine,rows=[];for(let i=0;i<=240;i++){e.time=i*4000/240;let f=e.compute();rows.push({time:e.time,primary:f.primaryError,support:f.supportError,elbow:f.arms.right.elbow,wrist:f.arms.right.wrist,grip:f.arms.right.grip,hand:f.angles.right.hand,transition:e.transition})}return rows}''')
      for metric,entry in zip(metrics,header['frames']):metric['pixel_sha256']=entry['rgba_sha256'];metric['recovered_from_verified_native_pack']=True
     for i in ([] if frames else range(241)):
      metric=p.evaluate('''i=>{let e=avatarLab.engine;e.time=i*4000/240;e.render();let f=e.frame;return {time:e.time,primary:f.primaryError,support:f.supportError,elbow:f.arms.right.elbow,wrist:f.arms.right.wrist,grip:f.arms.right.grip,hand:f.angles.right.hand,transition:e.transition}}''',i);frames.append(shot(p));metric['pixel_sha256']=hashim(frames[-1]);metrics.append(metric)
      if i%60==0: print('sample',version,gender,pose,visible,i,flush=True)
      assert metric['primary']<1e-6 and metric['support']<1e-6 and metric['transition'] is None
     assert frames[0].tobytes()==frames[-1].tobytes(),(gender,pose,'loop not exact')
     path=D/f'{version}-{gender}-{pose}-{visible}.webp';proof=encode(frames,path);frames[0].save(D/f'{version}-{gender}-{pose}-{visible}-0.png');frames[-1].save(D/f'{version}-{gender}-{pose}-{visible}-4000.png');rows.append({'version':version,'gender':gender,'pose':pose,'visible':visible,'logical_frames':241,'native_rgba_size':[941,1672],'file':str(path.relative_to(G)),'metrics':metrics,**proof});print(version,gender,pose,visible,'241 logical frames;',proof['native_frames_verified'],'encoded; seconds',round(time.monotonic()-start,2),flush=True)
     # Overview of the full native frames, not a different generated renderer.
     sheet=Image.new('RGB',(235*9,444*3),'#777');d=ImageDraw.Draw(sheet)
     for j,i in enumerate(range(0,241,10)):
      im=frames[i];bg=Image.new('RGBA',im.size,'#f8f5ed');bg.alpha_composite(im);sheet.paste(bg.resize((235,418)).convert('RGB'),(j%9*235,j//9*444+22));d.text((j%9*235+3,j//9*444+4),f'{i*4000/240:.2f} ms',fill='white')
     sheet.save(G/f'{version}-{gender}-{pose}-{visible}-dense-sheet.webp',lossless=True)
     del frames;gc.collect();(O/'Evidence/dense-progress.json').write_text(json.dumps({'rows':rows,'js_errors':errors,'http_errors':http}))
  p.close();server.shutdown()
 browser.close()
(O/'Evidence/dense-cycles.json').write_text(json.dumps({'logical_step_ms':1000/60,'backgrounds':['white','gray','black','green','transparent'],'subject_frames':rows,'background_method':'real transparent Canvas subject; other backgrounds composited by viewer CSS, direct renderer cross-check recorded separately','js_errors':errors,'http_errors':http},indent=2));assert not errors and not http
