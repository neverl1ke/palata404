"""Capture actual frozen-before/current Lab endpoints, not generated avatar substitutes."""
from pathlib import Path
import base64,functools,io,json,threading
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';G=O/'Gallery';errors=[];shots={};metrics=[]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
with sync_playwright() as pw:
 b=pw.chromium.launch()
 for version,root in [('before',R.parent/'avatar-foundation-baseline'),('after',R)]:
  s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();p=b.new_page(viewport={'width':1400,'height':1800});p.on('pageerror',lambda e:errors.append(str(e)));p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",maxWidth:"none",maxHeight:"none"});e.setOptions({breathing:false,background:"#f8f5ed"})}')
  for gender in ['male','female']:
   p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
   for pose in ['idle','melee','pistol','rifle']:
    p.evaluate('p=>{let e=avatarLab.engine;e.time=0;e.setPose(p)}',pose)
    for visible in [True,False]:
     p.evaluate('v=>avatarLab.engine.setLayerVisible("weapon",v)',visible);im=Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGBA');im.save(G/f'{version}-{gender}-{pose}-{visible}.png');shots[version,gender,pose,visible]=im
    row=p.evaluate('''()=>{let e=avatarLab.engine;e.setOptions({breathing:true});let out=[];for(let i=0;i<=240;i++){e.time=i*4000/240;let f=e.compute();out.push({time:e.time,elbow:f.arms.right.elbow,wrist:f.arms.right.wrist,grip:f.arms.right.grip,angle:f.weapon?.angle,primaryError:f.primaryError,supportError:f.supportError})}e.time=0;e.setOptions({breathing:false});return out}''');metrics.append({'version':version,'gender':gender,'pose':pose,'frames':row})
  p.close();s.shutdown()
 b.close()
for gender in ['male','female']:
 for pose in ['idle','melee','pistol','rifle']:
  out=Image.new('RGB',(1410,862),'#eee9df');d=ImageDraw.Draw(out)
  for i,(v,vis,label) in enumerate([('before',True,'BEFORE c2822a7'),('after',True,'AFTER / item'),('after',False,'AFTER / skin only')]):out.paste(shots[v,gender,pose,vis].resize((470,836)),(i*470,26));d.text((i*470+5,5),label,fill='black')
  out.save(G/f'{gender}-{pose}-comparison.webp',lossless=True)
boxes={'female-rifle-shoulder':('female','rifle',(230,290,360,490)),'female-rifle-right':('female','rifle',(280,480,515,625)),'female-rifle-left':('female','rifle',(600,570,730,720)),'female-pistol':('female','pistol',(155,240,295,420)),'female-melee':('female','melee',(155,770,290,940)),'male-rifle-right':('male','rifle',(330,550,515,700)),'male-rifle-left':('male','rifle',(610,620,760,790)),'male-pistol':('male','pistol',(170,240,320,440)),'male-melee':('male','melee',(145,790,315,1010))}
for name,(g,pose,box) in boxes.items():
 for k in [1,3]:
  w=(box[2]-box[0])*k;h=(box[3]-box[1])*k;out=Image.new('RGB',(w*3,h+24),'#eee9df');d=ImageDraw.Draw(out)
  for i,(v,vis,label) in enumerate([('before',False,'Before skin'),('after',False,'After skin'),('after',True,'After item')]):out.paste(shots[v,g,pose,vis].crop(box).resize((w,h)),(w*i,24));d.text((w*i+3,5),label,fill='black')
  out.save(G/f'{name}-{k}x.webp',lossless=True)
(O/'Evidence/endpoint-motion.json').write_text(json.dumps({'metrics':metrics,'js_errors':errors},indent=2));assert not errors;print('32 actual endpoints; 18 same-coordinate closeups; 3856 computed cycle samples')
