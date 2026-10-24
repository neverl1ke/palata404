"""Deterministic real Canvas samples; not an FPS or physical-device measurement."""
from pathlib import Path
import io,base64,functools,threading,json
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-requested-corrections';G=O/'Gallery';rows=[];sequences={}
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
with sync_playwright() as pw:
 b=pw.chromium.launch()
 for v,root in [('before',R.parent/'avatar-requested-baseline'),('after',R)]:
  s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();p=b.new_page(viewport={'width':1400,'height':1200});p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"400px",height:400*1672/941+"px",minWidth:0,maxWidth:"none",maxHeight:"none"});e.setOptions({breathing:true,background:"#f8f5ed"})}')
  for g in ['male','female']:
   p.evaluate('g=>avatarLab.engine.setGender(g)',g)
   for pose in ['melee'] if v=='before' else ['idle','melee','pistol','rifle']:
    if v=='after':p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',{'idle':None,'melee':'gear-knife','pistol':'gear-pm','rifle':'gear-aks'}[pose])
    p.evaluate('pose=>avatarLab.engine.setPose(pose)',pose);frames=[]
    for t in range(0,4000,100):
     p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);im=Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGB');frames.append(im.copy())
    sequences[v,g,pose]=frames
    if v=='after':frames[0].save(G/f'{g}-{pose}-cycle.webp',save_all=True,append_images=frames[1:],duration=100,loop=0,lossless=True)
    rows.append({'version':v,'gender':g,'pose':pose,'samples_ms':list(range(0,4000,100)),'method':'actual Canvas renders at explicit times; sampled preview, no real-time FPS claim'})
  p.close();s.shutdown()
 b.close()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
for g in ['male','female']:
 frames=[]
 for i in range(40):
  pair=Image.new('RGB',(800,737),'#e5e0d8');d=ImageDraw.Draw(pair)
  for j,v in enumerate(['before','after']):pair.paste(sequences[v,g,'melee'][i],(400*j,26));d.text((400*j+6,5),('ДО' if v=='before' else 'ПІСЛЯ')+' · '+str(i*100)+' ms',font=font,fill='black')
  frames.append(pair)
 frames[0].save(G/f'{g}-knife-before-after.webp',save_all=True,append_images=frames[1:],duration=100,loop=0,lossless=True)
(O/'Evidence/motion-captures.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print('400 real Canvas samples, 8 full cycles, 2 synchronized comparisons; 100ms steps')
