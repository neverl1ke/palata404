"""Actual source-body Core: reference / dd61b2d / current, not generated previews."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import base64,functools,hashlib,io,json,subprocess,tempfile,threading
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-reference-arm-art';G=OUT/'Gallery';G.mkdir(exist_ok=True);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
def serve(root):
 s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
reg=json.loads((OUT/'registration.json').read_text());metrics=[];errors=[];missing=[];details=[];images={};servers=[]
def panel(ims,labels,name):
 h=max(i.height for i in ims);w=max(i.width for i in ims);s=Image.new('RGB',(w*len(ims),h+36),'#e6e0d7');d=ImageDraw.Draw(s)
 for k,(im,label) in enumerate(zip(ims,labels)):s.paste(im,(k*w,36));d.text((k*w+8,8),label,font=font,fill='#192224')
 s.save(G/name,lossless=True);details.append({'path':name,'labels':labels})
with tempfile.TemporaryDirectory() as td:
 before=Path(td)
 files=['avatar-core/'+n for n in ['engine.mjs','math.mjs','skin.mjs','pose-art.mjs','weapon-controller.mjs','weapons.json','manifest.json','male-preview.json','rigs/male_rig.json','rigs/female_rig.json']]+['avatar-lab/'+n for n in ['index.html','lab.mjs','lab.css','catalog-bridge.js']]
 for n in files:
  p=before/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show','dd61b2d:'+n],cwd=ROOT))
 for n in ['base_male.png','base_female.png','paper-doll-data.js','paper-doll.js','hair-color.js','assets','review','avatar-core/assets']:(before/n).symlink_to(ROOT/n,target_is_directory=(ROOT/n).is_dir())
 servers=[serve(before),serve(ROOT)]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch();pages=[]
   for server in servers:
    p=browser.new_page(viewport={'width':1440,'height':1800});p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:missing.append([r.url,r.status]) if r.status>=400 else None);p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('''()=>{const e=avatarLab.engine;e.pause();e.time=0;e.setOptions({breathing:false,transitionMs:0,background:'#f8f5ed'});Object.assign(e.canvas.style,{width:'941px',height:'1672px',maxWidth:'none',maxHeight:'none',position:'fixed',left:0,top:0});e.render()}''');pages.append(p)
   current=pages[1];storage=current.evaluate('JSON.stringify({...localStorage})')
   def frame(p):return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGB')
   states=[]
   for pose in ['idle','rifle','pistol','melee']:
    ims=[];fs=[]
    for p,label in zip(pages,['before','after']):
     p.evaluate('p=>{const e=avatarLab.engine;e.time=0;e.setOptions({breathing:false,background:"#f8f5ed"});e.setPose(p)}',pose);im=frame(p);im.save(G/f'{label}-{pose}.webp',lossless=True);ims.append(im);fs.append(p.evaluate('avatarLab.engine.frame'))
    images[pose]=ims[1]
    if pose!='idle':
     source=Image.open(OUT/'Sources'/f'{pose}.png').convert('RGBA');bg=Image.new('RGBA',source.size,'#f8f5ed');bg.alpha_composite(source,(10,26));reference=bg.convert('RGB');reference.save(G/f'{pose}-aligned-reference.webp',lossless=True)
     panel([reference.resize((470,836)),ims[0].resize((470,836)),ims[1].resize((470,836))],['Референс · плечі +10,+26','Було · dd61b2d','Стало · модульні руки'],pose+'-comparison.webp')
     for side in reg['anchors'][pose]:
      for joint in ['grip','wrist','elbow','shoulder']:
       def crop(im,pt):x,y=map(round,pt);return im.crop((x-65,y-65,x+65,y+65)).resize((390,390))
       new=reg['anchors'][pose][side][joint];old=fs[0]['arms'][side][joint];panel([crop(reference,new),crop(ims[0],old),crop(ims[1],new)],['Референс ×3','Було ×3 · своє положення','Стало ×3 · нова прив’язка'],f'{pose}-{side}-{joint}.webp')
     for color in ['#fff','#777','#000','#00ff00']:
      current.evaluate('c=>avatarLab.engine.setOptions({background:c})',color);frame(current).crop((130,270,920,1060)).save(G/f'{pose}-background-{color[1:]}.webp',lossless=True)
    current.evaluate('avatarLab.engine.setOptions({breathing:true,cycleMs:4000,background:"#f8f5ed"})');frames=[];rows=[]
    for t in range(0,4000,125):
     current.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);frames.append(frame(current).resize((470,836)));f=current.evaluate('avatarLab.engine.frame');rows.append({'t':t,'primaryError':f['primaryError'],'supportError':f['supportError'],'arms':f['arms'],'weapon':f['weapon']})
    frames[0].save(G/f'{pose}-breathing.webp',save_all=True,append_images=frames[1:],duration=125,loop=0,lossless=True);metrics.append({'pose':pose,'cycleMs':4000,'samples':rows});assert max(max(r['primaryError'],r['supportError']) for r in rows)<1e-6
   overview=Image.new('RGB',(1880,836),'#f8f5ed')
   for i,pose in enumerate(['idle','rifle','pistol','melee']):overview.paste(images[pose].resize((470,836)),(i*470,0))
   overview.save(G/'four-current-poses.webp',lossless=True)
   # Actual catalog compatibility, not a claim about production clothing.
   catalog=current.evaluate('({faces:[{id:"source"},{id:"native"},...avatarCatalog.faces("male")].map(x=>x.id),hairs:avatarCatalog.hairs("male").map(x=>x.id)})');cases=[];current.evaluate('avatarLab.engine.setOptions({breathing:false});avatarLab.engine.time=0')
   for fi,face in enumerate(catalog['faces']):
    tiles=[]
    for hair in catalog['hairs']:
     current.evaluate('async a=>avatarLab.engine.setAppearance(await avatarCatalog.describe("male",a[0],a[1],"original"))',[face,hair])
     for pose in ['idle','rifle','pistol','melee']:
      current.evaluate('p=>avatarLab.engine.setPose(p)',pose);f=current.evaluate('avatarLab.engine.frame');assert f['primaryError']<1e-6 and f['supportError']<1e-6;cases.append({'face':face,'hair':hair,'pose':pose})
     tiles.append(frame(current).crop((270,0,685,330)).resize((207,165)))
    panel(tiles,catalog['hairs'],f'appearance-{fi}.webp')
   current.evaluate('avatarLab.engine.setAppearance({layers:[]})');current.locator('#sleeves').check();current.wait_for_function('avatarLab.engine.equipment.size===4&&Array.from(avatarLab.engine.equipment.values()).every(v=>v.bitmap&&v.skinned)')
   for pose in ['idle','rifle','pistol','melee']:
    current.evaluate('p=>avatarLab.engine.setPose(p)',pose);frame(current).resize((470,836)).save(G/f'{pose}-diagnostic-sleeves.webp',lossless=True)
   current.locator('#sleeves').uncheck();assert storage==current.evaluate('JSON.stringify({...localStorage})');assert not errors and not missing,(errors,missing)
   (OUT/'browser-capture.json').write_text(json.dumps({'baseline':'dd61b2d','browser':browser.version,'entry':'avatar-lab/index.html','uses_real_game_base':True,'full_sprite_replacement':False,'main_index_modified':False,'physical_device':False,'clothing_verified':'diagnostic bound sleeves only; no full wardrobe certification','cases':cases,'breathing':metrics,'js_errors':errors,'http_errors':missing,'storage_unchanged':True,'panels':details},ensure_ascii=False,indent=2)+'\n');browser.close()
 finally:
  for s in servers:s.shutdown();s.server_close()
print('Actual A/B captured;4 cycles;',len(cases),'catalog cases; no browser errors')
