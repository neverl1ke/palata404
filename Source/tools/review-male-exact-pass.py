"""Actual unchanged-character Core renders against reference-only full sprites."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import base64,functools,hashlib,html,io,json,shutil,threading
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-exact-reference-pass';G=OUT/'Gallery';G.mkdir(exist_ok=True)
REF=Path('/workspace/exact-reference-poses');font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[];missing=[];metrics=[];panels=[]
def sheet(images,name,labels):
 w=max(i.width for i in images);h=max(i.height for i in images);s=Image.new('RGB',(w*len(images),h+36),'#dedbd3');d=ImageDraw.Draw(s)
 for j,(im,label) in enumerate(zip(images,labels)):s.paste(im,(w*j,36));d.text((w*j+8,7),label,font=font,fill='#172022')
 s.save(G/name,lossless=True);panels.append(name)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch();p=browser.new_page(viewport={'width':1440,'height':1800},device_scale_factor=1);p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:missing.append([r.url,r.status]) if r.status>=400 else None)
  p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('''()=>{const e=avatarLab.engine;e.pause();e.setOptions({breathing:false,transitionMs:0,background:'#f7f4ec'});Object.assign(e.canvas.style,{width:'941px',height:'1672px',maxWidth:'none',maxHeight:'none',position:'fixed',left:0,top:0});e.render()}''');storage=p.evaluate('JSON.stringify({...localStorage})')
  def frame():return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGB')
  reference_hashes=[]
  for pose in ['idle','rifle','pistol','melee']:
   p.evaluate('x=>{const e=avatarLab.engine;e.time=0;e.setOptions({breathing:false});e.setPose(x)}',pose);actual=frame();actual.save(G/f'{pose}-actual.webp',lossless=True)
   ref=REF/'assets'/('male_idle.png' if pose=='idle' else f'male_{pose}_reference.png');ref=ref if ref.exists() else G/(pose+'-reference.png');im=Image.open(ref).convert('RGBA');reference_hashes.append({'file':str(ref.relative_to(REF)) if ref.is_relative_to(REF) else str(ref.relative_to(ROOT)),'size':list(im.size),'sha256':hashlib.sha256(ref.read_bytes()).hexdigest()})

   if ref.resolve()!=(G/(pose+'-reference.png')).resolve():shutil.copyfile(ref,G/(pose+'-reference.png'))
   bg=Image.new('RGBA',im.size,'#f7f4ec');bg.alpha_composite(im);reference=bg.convert('RGB')
   if reference.size!=actual.size:reference.thumbnail(actual.size);tmp=Image.new('RGB',actual.size,'#f7f4ec');tmp.paste(reference,(0,0));reference=tmp
   sheet([reference.resize((470,836)),actual.resize((470,836))],pose+'-comparison.webp',['РЕФЕРЕНС · не ресурс гри','ФАКТИЧНИЙ CORE · модульний'])
   p.evaluate('''async()=>{const e=avatarLab.engine;window.oldKnife=e.weapons.melee;window.oldKnifeBitmap=e.assets['weapon-melee'];if(e.pose==='melee'){e.weapons.melee={...e.weapons.melee,size:[140,300],primary:[67,240],image:'assets/weapons/melee.png',scale:.8,angle:0};e.assets['weapon-melee']=await e.image('assets/weapons/melee.png')}window.cleanAssets={};for(const [key] of Object.entries(e.malePreview.poseArtSurfaces)){cleanAssets[key]=e.assets[key];const [,front,pose,side]=[];const parts=key.split('-');const isFront=parts[1]==='front';const art=e.rig.poseArt[parts[isFront?2:1]][parts[isFront?3:2]];e.assets[key]=await e.image(art[isFront?'frontImage':'image']);}e.render()}''');before=frame();p.evaluate("Object.assign(avatarLab.engine.assets,cleanAssets);avatarLab.engine.weapons.melee=oldKnife;avatarLab.engine.assets['weapon-melee']=oldKnifeBitmap;avatarLab.engine.render()");assert frame().tobytes()==actual.tobytes()
   for side in (['right','left'] if pose=='rifle' else ['right'] if pose!='idle' else []):
    for joint in ['grip','wrist','shoulder']:
     xy=p.evaluate('a=>avatarLab.engine.frame.arms[a.side][a.joint]',{'side':side,'joint':joint});x,y=map(round,xy);box=(x-65,y-65,x+65,y+65)
     sheet([before.crop(box).resize((390,390)),actual.crop(box).resize((390,390))],f'{pose}-{side}-{joint}.webp',['ДО · 02cae62','ПІСЛЯ · альфа / окремий ніж'])
   for bg in ['#fff','#777','#000','#00ff00']:
    p.evaluate('bg=>avatarLab.engine.setOptions({background:bg})',bg);frame().crop((145,270,850,970)).save(G/f'{pose}-background-{bg[1:]}.webp',lossless=True)
   p.evaluate("avatarLab.engine.setOptions({background:'#f7f4ec',breathing:true,cycleMs:4000})");frames=[];rows=[]
   for t in range(0,4000,125):
    p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);frames.append(frame().resize((470,836)));f=p.evaluate('avatarLab.engine.frame');rows.append({'t':t,'primaryError':f['primaryError'],'supportError':f['supportError']})
   frames[0].save(G/f'{pose}-breathing.webp',save_all=True,append_images=frames[1:],duration=125,loop=0,lossless=True);assert max(max(r['primaryError'],r['supportError']) for r in rows)<1e-6;metrics.append({'pose':pose,'cycleMs':4000,'samples':rows})
  p.evaluate('avatarLab.engine.setOptions({breathing:false});avatarLab.engine.time=0')
  catalog=p.evaluate('({faces:[{id:"source",name:"Оригінал"},{id:"native",name:"Базове"},...avatarCatalog.faces("male")].map(({id,name})=>({id,name})),hairs:avatarCatalog.hairs("male").map(({id,name})=>({id,name}))})');combinations=[]
  for fi,f in enumerate(catalog['faces']):
   tiles=[]
   for h in catalog['hairs']:
    desc={'f':f['id'],'h':h['id']};p.evaluate('async a=>avatarLab.engine.setAppearance(await avatarCatalog.describe("male",a.f,a.h,"original"))',desc)
    for pose in ['idle','rifle','pistol','melee']:
     p.evaluate('p=>avatarLab.engine.setPose(p)',pose);snap=p.evaluate('avatarLab.engine.snapshot()');assert snap['frame']['primaryError']<1e-6 and snap['frame']['supportError']<1e-6;combinations.append({**desc,'pose':pose,'raster_loaded':True})
    tiles.append(frame().crop((270,0,685,330)).resize((207,165)))
   sheet(tiles,f'appearance-{fi}.webp',[h['id'] for h in catalog['hairs']])
  p.evaluate('avatarLab.engine.setAppearance({layers:[]})')
  p.locator('#sleeves').check();p.wait_for_function('avatarLab.engine.equipment.size===4&&Array.from(avatarLab.engine.equipment.values()).every(v=>v.bitmap&&v.skinned)')
  for pose in ['idle','rifle','pistol','melee']:
   p.evaluate('p=>avatarLab.engine.setPose(p)',pose);frame().resize((470,836)).save(G/f'{pose}-diagnostic-sleeves.webp',lossless=True)
  p.locator('#sleeves').uncheck();assert storage==p.evaluate('JSON.stringify({...localStorage})');assert not errors and not missing,(errors,missing)
  result={'browser':browser.version,'entry':'avatar-lab/index.html','actual_avatar':'original base_male.png partitioned by existing Core; no reference sprite in renderer','main_game_integration':False,'artistic_grips_fixed':False,'physical_mobile_device':False,'clothing':'four diagnostic bound sleeves only; production wardrobe adaptation NOT certified','js_errors':errors,'http_errors':missing,'storage_unchanged':True,'catalog':catalog,'appearance_pose_cases':combinations,'breathing':metrics,'references':reference_hashes};(OUT/'browser-capture.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');browser.close()
finally:server.shutdown();server.server_close()
print('Captured all four real Core poses;',len(combinations),'appearance/pose cases; four 32-frame breathing cycles; zero browser errors')
