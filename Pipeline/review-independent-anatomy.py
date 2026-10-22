"""Capture actual before/after runtime, hidden items, diagnostics and cycles."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import base64,functools,io,itertools,json,subprocess,tarfile,tempfile,threading
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/weapon-independent-anatomy';G=OUT/'Gallery';G.mkdir(parents=True,exist_ok=True)
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
POSES=['idle','melee','pistol','rifle'];BOXES={'neck':(350,270,595,365),'melee-hand':(150,790,330,1020),'melee-axilla':(240,330,420,600),'rifle-left-hand':(620,600,800,805),'rifle-right-hand':(315,540,530,710),'pistol-hand':(165,230,325,460),'pistol-shoulder':(220,290,395,600),'thigh-ownership':(630,800,810,1050)}
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
def serve(root):
 s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
def panel(ims,labels,name):
 w=max(i.width for i in ims);h=max(i.height for i in ims);out=Image.new('RGB',(w*len(ims),h+30),'#ebe6dc');d=ImageDraw.Draw(out)
 for j,(im,l) in enumerate(zip(ims,labels)):out.paste(im,(j*w,30));d.text((j*w+4,5),l,font=F,fill='#192024')
 out.save(G/name,lossless=True)
def shot(p):return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGBA')
errors=[];http=[];frames={};rows=[];switches=[];phase={}
with tempfile.TemporaryDirectory() as td:
 before=Path(td)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive','184e392','avatar-core','avatar-lab'],cwd=ROOT))) as z:z.extractall(before,filter='data')
 for n in ['base_male.png','base_female.png','paper-doll-data.js','paper-doll.js','hair-color.js','assets','review']:(before/n).symlink_to(ROOT/n,target_is_directory=(ROOT/n).is_dir())
 servers=[serve(before),serve(ROOT)]
 try:
  with sync_playwright() as w:
   browser=w.chromium.launch()
   for version,server in zip(['before','after'],servers):
    p=browser.new_page(viewport={'width':1440,'height':1800});p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:http.append([r.url,r.status]) if r.status>=400 else None);p.goto(f'http://localhost:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('''()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:'941px',height:'1672px',maxWidth:'none',maxHeight:'none'});e.setOptions({breathing:false,background:'#f8f5ed'})}''');storage=p.evaluate('JSON.stringify({...localStorage})')
    for gender in ['male','female']:
     p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
     for pose in POSES:
      for visible in [True,False]:
       p.evaluate('a=>{let e=avatarLab.engine;e.time=0;e.setOptions({breathing:false,background:"#f8f5ed"});e.setPose(a[0]);e.setLayerVisible("weapon",a[1]);e.render()}',[pose,visible]);im=shot(p);name=f'{version}-{gender}-{pose}-'+('visible' if visible else 'hidden');im.save(G/(name+'.webp'),lossless=True);frames[(version,gender,pose,visible)]=im
      if version=='before':
       if gender=='male' and pose=='rifle':
        for t in [1000,3000]:
         p.evaluate('t=>{let e=avatarLab.engine;e.setOptions({breathing:true,background:"#f8f5ed"});e.time=t;e.render()}',t);phase[('before',t)]=shot(p)
       continue
      if gender=='female':continue # female legacy is regression evidence, NOT new female art
      for visible in [True,False]:
       p.evaluate('v=>{let e=avatarLab.engine;e.setLayerVisible("weapon",v);e.setOptions({breathing:true,background:"#f8f5ed"})}',visible);cycle=[];full=[];measures=[]
       for t in range(0,4000,250):
        p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);im=shot(p);full.append(im);cycle.append(im.resize((470,836)));f=p.evaluate('avatarLab.engine.frame');assert f['primaryError']<1e-6 and f['supportError']<1e-6;measures.append({'t':t,'primaryError':f['primaryError'],'supportError':f['supportError'],'arms':f['arms']})
        if t in [1000,3000]:phase[(pose,visible,t)]=im
       state='visible' if visible else 'hidden';cycle[0].save(G/f'{pose}-{state}-cycle.webp',save_all=True,append_images=cycle[1:],duration=250,loop=0,lossless=True)
       box=(125,140 if pose=='pistol' else 280,925,1060);parts=[i.crop(box).resize((320,round((box[3]-box[1])*.4))) for i in full];sheet=Image.new('RGB',(320*8,parts[0].height*2),'#777')
       for k,im in enumerate(parts):sheet.paste(im,(k%8*320,k//8*im.height))
       sheet.save(G/f'{pose}-{state}-all-arms-frames.webp',lossless=True);rows.append({'pose':pose,'visible':visible,'samples':measures,'cycleMs':4000})
       p.evaluate('avatarLab.engine.time=4000;avatarLab.engine.render()');assert np.array_equal(np.array(shot(p)),np.array(full[0]))
      p.evaluate('avatarLab.engine.time=0;avatarLab.engine.setOptions({breathing:false})')
      variants=[]
      for scale in [.85,1,1.15]:
       p.evaluate('s=>{avatarLab.engine.setLayerVisible("weapon",true);avatarLab.engine.setOptions({weaponPreviewScale:s})}',scale);variants.append(shot(p).resize((470,836)))
      p.evaluate('avatarLab.engine.setOptions({weaponPreviewScale:1});avatarLab.engine.setLayerVisible("weapon",false)');variants.append(shot(p).resize((470,836)));panel(variants,['85% · diagnostic','100%','115% · diagnostic','No item · same pose'],pose+'-variants.webp');p.evaluate('avatarLab.engine.setOptions({weaponPreviewScale:1})')
      for color in ['#fff','#777','#000','#00ff00']:
       for visible in [True,False]:
        p.evaluate('a=>{let e=avatarLab.engine;e.setOptions({background:a[0]});e.setLayerVisible("weapon",a[1])}',[color,visible]);shot(p).save(G/f'{pose}-background-{color[1:]}-{visible}.webp',lossless=True)
     if version=='after' and gender=='male':
      for visible in [True,False]:
       for a,b in itertools.permutations(POSES,2):
        p.evaluate('a=>{let e=avatarLab.engine;e.setLayerVisible("weapon",a[2]);e.setOptions({breathing:true});e.setPose(a[0]);e.setPose(a[1]);e.render()}',[a,b,visible]);snap=p.evaluate('avatarLab.engine.snapshot()');assert p.evaluate('avatarLab.engine.transition===null');assert snap['frame']['primaryError']<1e-6;switches.append({'from':a,'to':b,'visible':visible,'instant':True})
      # Isolate actual runtime layers, then color their rendered coverage for
      # ownership diagnosis; rectangle overlap alone is never classified wrong.
      p.evaluate("avatarLab.engine.setOptions({breathing:false,background:'transparent'});['head','torso','lower','weapon'].forEach(k=>avatarLab.engine.setLayerVisible(k,false))")
      for pose in POSES:
       p.evaluate('p=>{avatarLab.engine.time=1000;avatarLab.engine.setPose(p)}',pose);a=shot(p);a.save(G/f'{pose}-isolated-arms.webp',lossless=True);tint=Image.new('RGBA',a.size,(0,200,240,255));tint.putalpha(a.getchannel('A'));panel([a,tint],['Actual isolated arm pixels','Cyan = same runtime coverage'],pose+'-ownership.webp')
    assert p.evaluate('JSON.stringify({...localStorage})')==storage;p.close()
   browser.close()
 finally:
  for s in servers:s.shutdown();s.server_close()
# Independent before/after at identical world coordinates; melee hand window
# includes the intentional length correction, not an independently centered crop.
for pose in POSES:
 panel([frames[('after','male',pose,v)].resize((470,836)) for v in [True,False]],['With item','Without item · same pose'],pose+'-current.webp')
 panel([frames[(v,'male',pose,False)].resize((470,836)) for v in ['before','after']],['Before · 184e392','After · hidden surfaces'],pose+'-before-after.webp')
box=BOXES['neck'];panel([phase[('before',3000)].crop(box).resize((735,285)),phase[('rifle',False,3000)].crop(box).resize((735,285))],['Before · exhale 3000ms','After · exhale 3000ms'],'neck-exhale-comparison.webp')
for n,box in BOXES.items():
 pose='rifle' if n.startswith('rifle') or n=='neck' else 'pistol' if n.startswith('pistol') else 'idle' if n=='thigh-ownership' else 'melee'
 panel([frames[(v,'male',pose,False)].crop(box).resize(((box[2]-box[0])*3,(box[3]-box[1])*3)) for v in ['before','after']],['Before · fixed coordinates','After · fixed coordinates'],n+'-comparison.webp')
# Body/face/feet protection is verified on the actual raster, not just hashes.
protected=[]
for gender in ['male','female']:
 for pose in POSES:
  a=np.array(frames[('before',gender,pose,True)]);b=np.array(frames[('after',gender,pose,True)]);face=np.array_equal(a[20:245,385:560],b[20:245,385:560]);feet=np.array_equal(a[1450:],b[1450:]);assert face and feet;equal=np.array_equal(a,b);protected.append({'gender':gender,'pose':pose,'face_unchanged':face,'feet_unchanged':feet,'whole_render_unchanged':equal});assert equal if gender=='female' else True
(OUT/'runtime-review.json').write_text(json.dumps({'baseline':'184e392','cycles':rows,'transitions':switches,'protected':protected,'js_errors':errors,'http_errors':http,'female_stage':'legacy regression only; no new female pose art integrated'},indent=2)+'\n');assert not errors and not http
print('Captured before/after, 8 male cycles, 24 cuts, four backgrounds and both gender regressions.')
