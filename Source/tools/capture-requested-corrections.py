from pathlib import Path
import functools,threading,base64,io,json,sys
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'review/avatar-requested-corrections';version=sys.argv[1];root=Path('/workspace/avatar-requested-baseline') if version=='before' else R
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page(viewport={'width':1400,'height':1800});p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",minWidth:0,maxWidth:"none",maxHeight:"none"});e.setOptions({background:"transparent",breathing:true})}')
 metrics=[]
 for g in ['male','female']:
  p.evaluate('g=>avatarLab.engine.setGender(g)',g)
  for pose in ['idle','melee','pistol','rifle']:
   if version=='after':p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',{'idle':None,'melee':'gear-knife','pistol':'gear-pm','rifle':'gear-aks'}[pose])
   for t in [0,1000,3000]:
    for vis in [False,True] if pose!='idle' else [False]:
     p.evaluate('v=>{let e=avatarLab.engine;e.time=v[1];e.setPose(v[0]);e.setLayerVisible("weapon",v[2]);e.render()}',[pose,t,vis]);data=base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]'));(D/'Gallery'/f'{version}-{g}-{pose}-{t}-{vis}.png').write_bytes(data)
    if t==0:metrics.append(p.evaluate('avatarLab.engine.snapshot()'))
 (D/'Evidence'/f'{version}-snapshots.json').write_text(json.dumps(metrics,indent=2))
 b.close()
s.shutdown();print('captured',version,flush=True)
