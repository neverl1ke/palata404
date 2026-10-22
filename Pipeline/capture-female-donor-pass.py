"""Actual old/new Lab captures, settled endpoints and complete background/time matrix."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import sys,base64,functools,io,itertools,json,subprocess,tarfile,tempfile,threading
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'review/female-donor-arm-pass';G=O/'Gallery';G.mkdir(exist_ok=True)
P=['idle','melee','pistol','rifle'];COLORS=['transparent','#fff','#777','#000','#00ff00'];TIMES=list(range(0,4001,250));errors=[];http=[];records=[];frames={};cuts=[];edge_templates={};alpha_checks=[]
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
def serve(root):
 s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
def panel(images,labels,path):
 w=max(i.width for i in images);h=max(i.height for i in images);out=Image.new('RGB',(w*len(images),h+26),'#ebe6dc');d=ImageDraw.Draw(out)
 for i,(im,label) in enumerate(zip(images,labels)):out.paste(im,(w*i,26));d.text((w*i+3,5),label,font=F,fill='#192024')
 out.save(path,lossless=True)
def shot(p,thumb=False):
 js='''()=>{let c=avatarLab.engine.canvas;if(THUMB){let t=document.createElement('canvas');t.width=235;t.height=418;t.getContext('2d').drawImage(c,0,0,235,418);c=t}return c.toDataURL().split(',')[1]}'''.replace('THUMB','true' if thumb else 'false')
 return Image.open(io.BytesIO(base64.b64decode(p.evaluate(js)))).convert('RGBA')
with tempfile.TemporaryDirectory() as td:
 old=Path(td)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive','77199cd','avatar-core','avatar-lab'],cwd=R))) as z:z.extractall(old,filter='data')
 for n in ['base_male.png','base_female.png','paper-doll-data.js','paper-doll.js','hair-color.js','assets','review']:(old/n).symlink_to(R/n,target_is_directory=(R/n).is_dir())
 servers=[serve(old),serve(R)]
 try:
  with sync_playwright() as w:
   b=w.chromium.launch()
   for version,server in zip(['before','after'],servers):
    p=b.new_page(viewport={'width':1440,'height':1800});p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:http.append([r.url,r.status]) if r.status>=400 else None);p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",maxWidth:"none",maxHeight:"none"});e.setOptions({breathing:false,background:"#f8f5ed"})}');storage=p.evaluate('JSON.stringify({...localStorage})')
    for gender in ['male','female']:
     p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
     for pose in P:
      # Old female morph must FINISH before baseline capture. Previous report
      # reset time at pose selection, capturing stale arm/weapon transitions.
      p.evaluate('pose=>{let e=avatarLab.engine;e.setPose(pose);e.time+=1000;e.render();e.time=0;e.setOptions({breathing:false,background:"#f8f5ed"})}',pose)
      for visible in [True,False]:
       p.evaluate('v=>avatarLab.engine.setLayerVisible("weapon",v)',visible);im=shot(p);frames[(version,gender,pose,visible)]=im;im.save(G/f'{version}-{gender}-{pose}-{visible}.webp',lossless=True)
      if version=='before':continue
      for visible in [True,False]:
       for color in COLORS:
        p.evaluate('a=>{let e=avatarLab.engine;e.setLayerVisible("weapon",a[0]);e.setOptions({breathing:true,background:a[1],weaponPreviewScale:1})}',[visible,color]);small=[];first=None;metrics=[]
        for t in TIMES:
         m=p.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.render();let f=e.frame;return{time:t,primaryError:f.primaryError,supportError:f.supportError,transition:e.transition,neckAlpha:(()=>{let a=e.ctx.getImageData(415,293,115,5).data,min=255;for(let i=3;i<a.length;i+=4)min=Math.min(min,a[i]);return min})()}}',t);assert m['primaryError']<1e-6 and m['supportError']<1e-6;assert m['transition'] is None;metrics.append(m);small.append(shot(p,True))
         if t==0:
          key=(gender,pose,visible)
          if color=='transparent':edge_templates[key]=p.evaluate('()=>{let e=avatarLab.engine,a=e.ctx.getImageData(0,0,941,1672).data,ids=[];for(let i=3;i<a.length;i+=4)if(a[i]>0&&a[i]<240)ids.push((i-3)/4);let stride=Math.max(1,Math.floor(ids.length/200));return ids.filter((_,i)=>i%stride===0).slice(0,200).map(i=>[i,[...a.slice(i*4,i*4+4)]])}')
          else:
           bg={'#fff':[255,255,255],'#777':[119,119,119],'#000':[0,0,0],'#00ff00':[0,255,0]}[color]
           check=p.evaluate('v=>{let e=avatarLab.engine,a=e.ctx.getImageData(0,0,941,1672).data,max=0,sum=0,n=0;for(let [i,c]of v[0])for(let k=0;k<3;k++){let expected=c[k]*c[3]/255+v[1][k]*(1-c[3]/255),d=Math.abs(a[i*4+k]-expected);max=Math.max(max,d);sum+=d;n++}return{samples:v[0].length,max_error:max,mean_error:sum/Math.max(n,1)}}',[edge_templates[key],bg]);check['criterion_max_error']=2;check['passed']=check['max_error']<=2;alpha_checks.append({'gender':gender,'pose':pose,'visible':visible,'background':color,**check})
         if color=='transparent' and t in [0,1000,3000,4000]:
          full=shot(p)
          if t==0:full.save(G/f'{gender}-{pose}-{visible}-{t}.png')
          else:full.save(G/f'{gender}-{pose}-{visible}-{t}.webp',lossless=True)
          if t==0:first=np.array(full)
          if t==4000:assert np.array_equal(first,np.array(full)),(gender,pose,'loop')
        name=f'{gender}-{pose}-{visible}-{color.replace("#","")}';sheet=Image.new('RGBA',(235*9,444*2),(60,60,60,255));d=ImageDraw.Draw(sheet)
        for i,im in enumerate(small):sheet.paste(im,(i%9*235,i//9*444+26));d.text((i%9*235+3,i//9*444+5),f'{TIMES[i]} ms',font=F,fill='white')
        sheet.save(G/(name+'-frames.webp'),lossless=True)
        if color=='transparent':small[0].save(G/f'{gender}-{pose}-{visible}-cycle.webp',save_all=True,append_images=small[1:-1],duration=250,loop=0,lossless=True)
        records.append({'gender':gender,'pose':pose,'visible':visible,'background':color,'frames':metrics,'sheet':name+'-frames.webp'})
      p.evaluate('avatarLab.engine.time=0;avatarLab.engine.setOptions({breathing:false,background:"#f8f5ed"})')
      variants=[]
      for scale in [.85,1,1.15]:p.evaluate('s=>{let e=avatarLab.engine;e.setLayerVisible("weapon",true);e.setOptions({weaponPreviewScale:s})}',scale);variants.append(shot(p,True))
      panel(variants,['85% diagnostic','100% calibrated','115% diagnostic'],G/f'{gender}-{pose}-sizes.webp');p.evaluate('avatarLab.engine.setOptions({weaponPreviewScale:1})')
     if version=='after':
      for a,bp in itertools.permutations(P,2):
       p.evaluate('a=>{let e=avatarLab.engine;e.setPose(a[0]);e.setPose(a[1]);e.render()}',[a,bp]);assert p.evaluate('avatarLab.engine.transition===null');cuts.append({'gender':gender,'from':a,'to':bp,'instant':True})
    assert storage==p.evaluate('JSON.stringify({...localStorage})');p.close()
    if version=='before' and '--baseline-only' in sys.argv:raise SystemExit(0)
   b.close()
 finally:
  for s in servers:s.shutdown()
for gender in ['male','female']:
 for pose in P:
  panel([frames[(v,gender,pose,True)].resize((470,836)) for v in ['before','after']],['Before · settled 77199cd','After · donor pass'],G/f'{gender}-{pose}-comparison.webp')
  panel([frames[('after',gender,pose,v)].resize((470,836)) for v in [True,False]],['With item','Without item · same pose'],G/f'{gender}-{pose}-visibility.webp')
# Tight same-coordinate windows, at 100% and 300%. No independent centering.
boxes={'female-rifle-wrist':('female','rifle',(600,570,725,715)),'female-rifle-right':('female','rifle',(280,480,490,625)),'female-rifle-shoulder':('female','rifle',(235,290,355,490)),'female-pistol-grip':('female','pistol',(160,240,290,375)),'female-melee-grip':('female','melee',(155,770,280,930)),'male-rifle-right':('male','rifle',(330,550,515,690)),'male-rifle-left':('male','rifle',(620,640,740,770)),'male-pistol':('male','pistol',(175,245,310,425)),'male-melee':('male','melee',(150,790,315,1000)),'female-neck':('female','rifle',(385,260,565,370))}
for name,(gender,pose,box) in boxes.items():
 for scale in [1,3]:panel([frames[(v,gender,pose,False)].crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale)) for v in ['before','after']],['Before · no item','After · no item'],G/f'{name}-{scale}x.webp')
# Explicit source -> extracted -> adapted -> actual runtime pipeline.
rig=json.loads((R/'avatar-core/rigs/female_rig.json').read_text())
for pose,sides in rig['poseArt'].items():
 for side,art in sides.items():
  box=Image.open(R/'avatar-core'/art['image']).getbbox();src=Image.open(O/'Sources'/f'{pose}.png').convert('RGBA');raw=src.copy();raw.putalpha(Image.open(O/'Masks'/f'{pose}-{side}-arm.png'));adapt=Image.open(R/'avatar-core'/art['image']);actual=frames[('after','female',pose,False)]
  for scale in [1,3]:
   ims=[im.crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale)) for im in [src,raw,adapt,actual]];panel(ims,['Donor source','Extraction before repairs','Adapted RGBA','Actual Lab renderer'],G/f'pipeline-{pose}-{side}-{scale}x.webp')
proof={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'baseline':'77199cd','old_endpoints_settled_before_capture':True,'matrix_states':len(records),'rendered_frames':sum(len(r['frames']) for r in records),'records':records,'cuts':cuts,'alpha_background_consistency_checks':alpha_checks,'js_errors':errors,'http_errors':http,'body_base_replaced':False,'source_hashes':{g:__import__('hashlib').sha256((R/f'base_{g}.png').read_bytes()).hexdigest() for g in ['male','female']}}
(O/'runtime-review.json').write_text(json.dumps(proof,indent=2)+'\n');assert not errors and not http;print('Actual runtime:',proof['rendered_frames'],'frames,',len(records),'background/visibility/pose states, 24 endpoint cuts, sources and enlarged joins')
