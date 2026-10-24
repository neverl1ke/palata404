from pathlib import Path
import json,functools,threading,argparse
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import numpy as np
from scipy.spatial import ConvexHull
from PIL import Image
from playwright.sync_api import sync_playwright
PROJECT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=PROJECT);parser.add_argument('--output',default='actual-weapon-motion.json');args=parser.parse_args();R=args.root;D=PROJECT/'review/avatar-selective-merge';c=json.loads((R/'avatar-core/equipment-weapons.json').read_text());items={i['pose']:i for i in c['items']}
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start();rows=[]
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page();p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('avatarLab.engine.pause()')
 for g in ['male','female']:
  p.evaluate('g=>avatarLab.engine.setGender(g)',g)
  for pose,item in items.items():
   a=np.array(Image.open(R/'avatar-core'/item['image']));y,x=np.where(a[:,:,3]>0);points=np.c_[x,y];points=points[ConvexHull(points).vertices].tolist();p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',item['id']);row=p.evaluate('''points=>{let e=avatarLab.engine;e.setOptions({breathing:true});let samples=[];for(let t=0;t<=4000;t+=50){e.time=t;let f=e.compute(),m=f.weapon.matrix;samples.push(points.map(([x,y])=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]))}return {nominalSway:e.options.weaponSwayPx,samples}}''',points);q=np.array(row.pop('samples'));center=(q.max(axis=0)+q.min(axis=0))/2;row.update(gender=g,pose=pose,actual_max_radius_px=float(np.linalg.norm(q-center,axis=2).max()),actual_peak_to_peak_bbox_px=np.ptp(q,axis=0).max(axis=0).tolist(),interpretation='actual opaque weapon hull measured, not just the UI sway parameter');rows.append(row)
 b.close()
s.shutdown();(D/'Evidence'/args.output).write_text(json.dumps(rows,indent=2)+'\n');print([(r['gender'],r['pose'],round(r['actual_max_radius_px'],3)) for r in rows])
