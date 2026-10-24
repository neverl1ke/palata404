"""Capture immutable historical/native Canvas renders; no substituted artwork."""
from pathlib import Path
import sys,functools,threading,json,base64
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'review/avatar-selective-merge';version=sys.argv[1];root=R if version=='final' else R.parent/('avatar-selective-'+version)
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();errors=[];rows=[]
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page(viewport={'width':1400,'height':1800});p.on('pageerror',lambda e:errors.append(str(e)));p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",minWidth:0,maxWidth:"none",maxHeight:"none"});e.setOptions({background:"#f8f5ed",breathing:true,transitionMs:0});}')
 for g in ['male','female']:
  p.evaluate('g=>avatarLab.engine.setGender(g)',g)
  for pose in ['idle','melee','pistol','rifle']:
   if version in ['5532a93','final']:p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',{'idle':None,'melee':'gear-knife','pistol':'gear-pm','rifle':'gear-aks'}[pose])
   for t in [0,1000,2000,3000]:
    for visible in ([False] if pose=='idle' else [False,True]):
     p.evaluate('v=>{let e=avatarLab.engine;e.time=v[1];e.setPose(v[0]);e.setLayerVisible("weapon",v[2]);e.render()}',[pose,t,visible]);name=f'{version}-{g}-{pose}-{t}-{visible}.png';(D/'Gallery'/name).write_bytes(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')));rows.append({'file':name,'gender':g,'pose':pose,'time':t,'weapon_visible':visible,'snapshot':p.evaluate('avatarLab.engine.snapshot()') if t==0 else None})
   if version=='final' and pose!='idle':
    for scale in [.85,1,1.15]:
     p.evaluate('v=>{let e=avatarLab.engine;e.setOptions({weaponPreviewScale:v});e.time=0;e.setLayerVisible("weapon",true);e.render()}',scale);name=f'final-{g}-{pose}-scale-{scale}.png';(D/'Gallery'/name).write_bytes(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))
    p.evaluate('avatarLab.engine.setOptions({weaponPreviewScale:1})')
 b.close()
s.shutdown();(D/'Evidence'/f'{version}-captures.json').write_text(json.dumps({'root':str(root),'rows':rows,'js_errors':errors},indent=2)+'\n');assert not errors;print(version,len(rows),'native 941x1672 renders; JS errors',len(errors))
