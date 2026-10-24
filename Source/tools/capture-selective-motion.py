"""Deterministic real Canvas samples; not an FPS or physical-device measurement."""
from pathlib import Path
import io,base64,functools,threading,json
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-selective-merge';G=O/'Gallery';rows=[];sequences={}
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
with sync_playwright() as pw:
 b=pw.chromium.launch()
 for v,root in [('before',R.parent/'avatar-selective-184e392'),('current',R.parent/'avatar-selective-5532a93'),('final',R)]:
  s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();p=b.new_page(viewport={'width':1400,'height':1200});p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"400px",height:400*1672/941+"px",minWidth:0,maxWidth:"none",maxHeight:"none"});e.setOptions({breathing:true,background:"#f8f5ed",transitionMs:0})}')
  for g in ['male','female']:
   p.evaluate('g=>avatarLab.engine.setGender(g)',g)
   for pose in ['melee'] if v!='final' else ['idle','melee','pistol','rifle']:
    if v!='before':p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',{'idle':None,'melee':'gear-knife','pistol':'gear-pm','rifle':'gear-aks'}[pose])
    p.evaluate('pose=>avatarLab.engine.setPose(pose)',pose);frames=[]
    for t in range(0,4000,100):
     p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);im=Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGB');frames.append(im.copy())
    sequences[v,g,pose]=frames
    if v=='final':frames[0].save(G/f'{g}-{pose}-cycle.webp',save_all=True,append_images=frames[1:],duration=100,loop=0,lossless=False,quality=95)
    rows.append({'version':v,'gender':g,'pose':pose,'samples_ms':list(range(0,4000,100)),'method':'actual Canvas renders at explicit times; animated WebP quality 95 preview; static native captures remain lossless; no real-time FPS claim'})
  p.close();s.shutdown()
 b.close()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
for g in ['male','female']:
 frames=[]
 for i in range(40):
  pair=Image.new('RGB',(1200,737),'#e5e0d8');d=ImageDraw.Draw(pair)
  for j,v in enumerate(['before','current','final']):pair.paste(sequences[v,g,'melee'][i],(400*j,26));d.text((400*j+6,5),{'before':'ДО 184e392','current':'ПІСЛЯ 5532a93','final':'ФІНАЛ'}[v]+' · '+str(i*100)+' ms',font=font,fill='black')
  frames.append(pair)
 frames[0].save(G/f'{g}-knife-triple-cycle.webp',save_all=True,append_images=frames[1:],duration=100,loop=0,lossless=False,quality=95)
(O/'Evidence/motion-captures.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print('480 real Canvas samples, 8 full cycles, 2 synchronized triple comparisons; 100ms steps')
