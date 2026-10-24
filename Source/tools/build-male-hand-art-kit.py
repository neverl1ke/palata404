"""Export exact male hand authoring masks and real baseline previews; no runtime writes."""
from pathlib import Path
import base64,functools,hashlib,html,io,json,subprocess,threading,shutil
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'avatar-core';OUT=ROOT/'review/male-hand-art-kit';OUT.mkdir(exist_ok=True)
FRAME=(941,1672);rig=json.loads((CORE/'rigs/male_rig.json').read_text());defs=json.loads((CORE/'male-preview.json').read_text())['weapons']
CASES=[
 {'id':'pistol-right','pose':'pistol','side':'right','title':'Права кисть · пістолет','polygon':[(177,246),(235,246),(283,275),(303,311),(306,378),(294,410),(255,416),(234,397),(211,374),(174,340),(168,287)]},
 {'id':'rifle-right','pose':'rifle','side':'right','title':'Права кисть · рукоятка автомата','polygon':[(295,600),(333,594),(378,612),(417,636),(444,663),(448,704),(418,735),(360,738),(324,712),(306,676),(286,646)]},
 {'id':'rifle-left','pose':'rifle','side':'left','title':'Ліва кисть · підтримка цівки','polygon':[(626,684),(666,689),(698,721),(695,760),(664,796),(613,805),(572,786),(542,764),(536,732),(561,711),(598,701)]},
]
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def matrix(m):return np.array([[m[0],m[2],m[4]],[m[1],m[3],m[5]],[0,0,1.]])
def full(im,bounds):c=Image.new('RGBA',FRAME);c.alpha_composite(im.convert('RGBA'),tuple(bounds[:2]));return c
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13);gallery=OUT/'Gallery';gallery.mkdir(exist_ok=True);states={};errors=[];missing=[]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch();p=browser.new_page(viewport={'width':1450,'height':1850},device_scale_factor=1)
  p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:missing.append([r.url,r.status]) if r.status>=400 else None)
  p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({breathing:false,transitionMs:0})');storage=p.evaluate('JSON.stringify({...localStorage})')
  p.evaluate('Object.assign(avatarLab.engine.canvas.style,{width:"941px",height:"1672px",maxWidth:"none",maxHeight:"none",minWidth:"0",position:"fixed",left:0,top:0});avatarLab.engine.render()')
  def frame():return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGBA')
  for pose in ['pistol','rifle']:
   p.evaluate('p=>{const e=avatarLab.engine;e.time=0;e.setPose(p)}',pose);states[pose]=p.evaluate('avatarLab.engine.frame');frame().save(gallery/f'{pose}-full.png')
  for row in CASES:
   pose,side=row['pose'],row['side'];art=rig['poseArt'][pose][side];folder=OUT/'Hands'/row['id'];folder.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(CORE/art['image'],folder/'reference-arm-crop-original.png');shutil.copyfile(CORE/art['frontImage'],folder/'reference-front-crop-original.png')
   arm=full(Image.open(CORE/art['image']),art['mesh']['bounds']);front=full(Image.open(CORE/art['frontImage']),art['mesh']['bounds']);arm.save(folder/'reference-arm-full.png');front.save(folder/'reference-existing-front.png')
   wmat=matrix(states[pose]['weapon']['matrix']);weapon=Image.open(CORE/defs[pose]['image']).convert('RGBA').transform(FRAME,Image.Transform.AFFINE,tuple(np.linalg.inv(wmat)[:2].ravel()),Image.Resampling.BICUBIC);weapon.save(folder/'reference-weapon-full.png')
   region=Image.new('L',FRAME);rd=ImageDraw.Draw(region);rd.polygon(row['polygon'],fill=255)
   for key in ['shoulder','elbow']:
    px,py=art['anchors'][key];rd.ellipse((px-12,py-12,px+12,py+12),fill=0)
   region.save(folder/'edit-region.png')
   a=np.array(arm);reg=np.array(region)/255;yy,xx=np.indices((1672,941));wrist=np.array(art['anchors']['wrist']);grip=np.array(art['anchors']['grip']);axis=grip-wrist;axis/=np.linalg.norm(axis);forearm=wrist-np.array(art['anchors']['elbow']);forearm/=np.linalg.norm(forearm);along=(xx-wrist[0])*forearm[0]+(yy-wrist[1])*forearm[1]
   weight=smooth((along+32)/22)*reg;Image.fromarray(np.rint(weight*255).astype('uint8')).save(folder/'wrist-blend-weight.png');Image.fromarray(np.rint(a[:,:,3]*weight).astype('uint8')).save(folder/'old-skin-remove-mask.png')
   protected=a.copy();protected[:,:,3]=np.rint(a[:,:,3]*(1-weight)).astype('uint8');protected[protected[:,:,3]==0]=0;Image.fromarray(protected).save(folder/'protected-arm-reference.png')
   overlay=np.zeros((1672,941,4),dtype='uint8');overlay[:,:,:3]=[50,170,255];overlay[:,:,3]=np.rint(reg*95);overlay[overlay[:,:,3]==0]=0;Image.fromarray(overlay).save(folder/'edit-overlay.png')
   guide=Image.new('RGBA',FRAME);d=ImageDraw.Draw(guide);d.line(row['polygon']+[row['polygon'][0]],fill='#45bfff',width=2)
   for label,col in [('wrist','#00ffb0'),('grip','#ffce55'),('elbow','#ff7777'),('shoulder','#ff7777')]:
    x,y=art['anchors'][label];d.ellipse((x-4,y-4,x+4,y+4),fill=col);d.text((x+7,y+4),label[0].upper(),fill=col,font=font)
    if label in ['shoulder','elbow']:d.ellipse((x-12,y-12,x+12,y+12),outline=col,width=1)
   d.line([(wrist[0]-axis[0]*32,wrist[1]-axis[1]*32),(grip[0]+axis[0]*35,grip[1]+axis[1]*35)],fill='#00ffb0',width=2);guide.save(folder/'guides.png')
   for part in ['back','front','thumb']:Image.new('RGBA',FRAME).save(folder/f'candidate-{part}.png')
   bb=region.getbbox();crop=[max(0,bb[0]-22),max(0,bb[1]-22),min(941,bb[2]+22),min(1672,bb[3]+22)];shot=Image.open(gallery/f'{pose}-full.png').convert('RGBA');shot.crop(crop).resize(((crop[2]-crop[0])*3,(crop[3]-crop[1])*3)).save(gallery/f'{row["id"]}-before.png')
   diagnostic=Image.alpha_composite(shot,guide);diagnostic.crop(crop).resize(((crop[2]-crop[0])*3,(crop[3]-crop[1])*3)).save(gallery/f'{row["id"]}-registration.png')
   bind=matrix(art['bind']['hand']);inverse=np.linalg.inv(bind)
   row.update(frame=list(FRAME),source_asset=art['image'],source_front=art['frontImage'],source_sha256=sha(CORE/art['image']),source_front_sha256=sha(CORE/art['frontImage']),source_bounds=art['mesh']['bounds'],anchors_pose=art['anchors'],source_wrist=rig['arms'][side]['wrist'],source_grip=rig['handCorrections'][pose][side]['grip'],bind_hand=art['bind']['hand'],inverse_bind_hand=inverse.tolist(),wrist_axis=axis.tolist(),forearm_axis=forearm.tolist(),weapon_matrix_world=states[pose]['weapon']['matrix'],weapon_resource=defs[pose]['image'],weapon_anchors_local={k:defs[pose].get(k) for k in ['primary','support','stock','trigger']},seam={'axis_distance_source_px':[-32,-10],'axis':'forearm_axis, not hand direction','weight':'smoothstep; only the wrist seam, never feather all fingers'},edit_bbox=list(bb),preview_crop=crop,crop_translation=[-crop[0],-crop[1]],candidate_paths=[f'Hands/{row["id"]}/candidate-{part}.png' for part in ['back','front','thumb']],new_art_status='empty templates; no new hand anatomy',layer_order=['hand_back','separate_weapon','front_fingers','optional_near_thumb'],animation_transform='currentHandMatrix * inverse(bind_hand); all new parts share one logical hand')
   (folder/'anchors.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
  p.evaluate('Object.assign(avatarLab.engine.canvas.style,{width:"470px",height:"835.133px"});avatarLab.engine.setOptions({breathing:true})')
  breath=[]
  for pose in ['pistol','rifle']:
   p.evaluate('p=>avatarLab.engine.setPose(p)',pose);fullframes=[];crops={r['id']:[] for r in CASES if r['pose']==pose};rows=[]
   for t in range(0,4000,125):
    p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);im=frame().convert('RGB');fullframes.append(im);f=p.evaluate('avatarLab.engine.frame');rows.append({'time_ms':t,'primary_error':f['primaryError'],'support_error':f['supportError']})
    for r in CASES:
     if r['pose']==pose:
      box=[round(v*470/941) for v in r['preview_crop']];c=im.crop(box);crops[r['id']].append(c.resize((c.width*3,c.height*3)))
   for name,frames in [(pose+'-breathing',fullframes)]+[(key+'-breathing',value) for key,value in crops.items()]:frames[0].save(gallery/(name+'.webp'),save_all=True,append_images=frames[1:],duration=125,loop=0,lossless=True)
   assert max(max(r['primary_error'],r['support_error']) for r in rows)<1e-6;breath.append({'pose':pose,'cycle_ms':4000,'frame_interval_ms':125,'frames':32,'new_hand_art':False,'samples':rows})
  assert storage==p.evaluate('JSON.stringify({...localStorage})');assert not errors and not missing,(errors,missing)
  (OUT/'browser-capture.json').write_text(json.dumps({'browser':browser.version,'entry':'avatar-lab/index.html','reference_runtime':'7854994','js_errors':errors,'http_errors':missing,'storage_unchanged':True,'breathing':breath,'physical_device':False},indent=2)+'\n');browser.close()
finally:server.shutdown();server.server_close()
(OUT/'hand-contract.json').write_text(json.dumps({'baseline':'7854994','source_checkout':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'frame':list(FRAME),'new_art_count':0,'templates_are_not_art':True,'cases':CASES},ensure_ascii=False,indent=2)+'\n')
paths=subprocess.check_output(['git','ls-tree','-r','7854994','avatar-core','avatar-lab'],cwd=ROOT,text=True).splitlines();runtime=[]
for entry in paths:
 name=entry.split('\t')[1];path=ROOT/name
 if path.is_file():
  original=subprocess.check_output(['git','show','7854994:'+name],cwd=ROOT);assert path.read_bytes()==original,name;runtime.append({'path':name,'sha256':sha(path)})
for name in ['base_male.png','base_female.png']:
 path=ROOT/name;assert path.read_bytes()==subprocess.check_output(['git','show','7854994:'+name],cwd=ROOT);runtime.append({'path':name,'sha256':sha(path)})
(OUT/'protected-runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
print('Authoring kit:3 cases,9 explicitly empty candidate layers; runtime unchanged; actual32-frame cycles captured')
