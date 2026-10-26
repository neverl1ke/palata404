"""Read-only actual file:// Lab verification; receipt is outside final ZIP."""
from pathlib import Path
import argparse,base64,io,json,hashlib,zipfile,re
from PIL import Image
import numpy as np
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--zip',type=Path);p.add_argument('--pdf',action='store_true');p.add_argument('--pdf-only',action='store_true');a=p.parse_args();D=a.directory;errors=[];external=[];checks=[]
def canonical(im):
 data=np.array(im.convert('RGBA'));data[data[:,:,3]==0]=0;return hashlib.sha256(data.tobytes()).hexdigest()
def image64(data):return Image.open(io.BytesIO(base64.b64decode(data)))
hashes={}
if a.zip:
 with zipfile.ZipFile(a.zip) as z:
  assert z.testzip() is None;manifest=json.loads(z.read('SHA256SUMS.json'))
  for name,h in manifest.items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==h,name
 hashes['ZIP_SHA256']=hashlib.sha256(a.zip.read_bytes()).hexdigest();hashes['manifest_entries_exact']=len(manifest)
text=(D/'Avatar-Lab.html').read_text();start=text.index('const engineURL=moduleURL(');start=text.index('"import ',start);engine=json.JSONDecoder().raw_decode(text[start:])[0];engine_hash=hashlib.sha256(engine.encode()).hexdigest();runtime=D/'Runtime/avatar-core/engine.mjs';runtime=runtime if runtime.exists() else R/'avatar-core/engine.mjs';assert engine_hash==hashlib.sha256(runtime.read_bytes()).hexdigest();hashes['engine_SHA256']=engine_hash
assert runtime.read_bytes()==(R/'avatar-core/engine.mjs').read_bytes(),'archive engine differs from current source'
with sync_playwright() as pw:
 b=pw.chromium.launch();page=b.new_page(viewport={'width':1440,'height':1800});page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda req:external.append(req.url) if not req.url.startswith(('file:','data:','blob:')) else None)
 page.goto((D/'Report.html').as_uri(),wait_until='load',timeout=120000);assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
 if a.pdf or a.pdf_only:
  # Compact print previews only. All original lossless native controls stay
  # in Gallery and are independently verified below; PDF is not a pixel test.
  print_html=(D/'Report.html').read_text()
  for src in set(re.findall(r'<img[^>]+src="([^"]+)"',print_html)):
   image=Image.open(D/src).convert('RGBA');background=Image.new('RGBA',image.size,'#f8f5ed');background.alpha_composite(image);image=background.convert('RGB');image.thumbnail((520,2000));data=io.BytesIO();image.save(data,format='JPEG',quality=91)
   print_html=print_html.replace('src="'+src+'"','src="data:image/jpeg;base64,'+base64.b64encode(data.getvalue()).decode()+'"')
  page.set_content(print_html,wait_until='load',timeout=120000)
  page.pdf(path=str(D/'Review.pdf'),format='A4',print_background=True)
  if a.pdf_only:page.close();b.close();print('Compact PDF print previews; native evidence unchanged');raise SystemExit(0)
 page.goto((D/'Avatar-Lab.html').as_uri(),wait_until='load',timeout=120000);page.wait_for_function('window.avatarLab?.ready',timeout=120000);page.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",minWidth:0,maxWidth:"none",maxHeight:"none"});e.setOptions({transitionMs:0,background:"transparent",breathing:true,playbackRate:1})}')
 saved=page.evaluate('JSON.stringify({...localStorage})')
 for g in ['male','female']:
  await_selector=f'[data-gender="{g}"]';page.locator(await_selector).click();page.wait_for_function('g=>avatarLab.engine.gender===g',arg=g)
  cfgpath=D/f'Runtime/avatar-core/{g}-preview.json';cfgpath=cfgpath if cfgpath.exists() else R/f'avatar-core/{g}-preview.json';cfg=json.loads(cfgpath.read_text());assert page.evaluate('g=>AVATAR_CORE_EMBED.json[g+"-preview.json"]',g)==cfg;hashes[g+'_config_SHA256']=hashlib.sha256(cfgpath.read_bytes()).hexdigest()
  assert cfgpath.read_bytes()==(R/f'avatar-core/{g}-preview.json').read_bytes()
  for pose,id in [('idle',None),('pistol','gear-pm'),('melee','gear-knife'),('rifle','gear-aks')]:
   page.locator(f'[data-pose="{pose}"]').click();page.wait_for_function('v=>avatarLab.engine.pose===v[0]&&avatarLab.engine.selectedWeaponId===v[1]',arg=[pose,id])
  for k in [.85,1,1.15]:
   for mode,cycle,amp,sway in [('standard',4000,1,2),('stress',1000,2,4)]:
    page.evaluate('v=>avatarLab.engine.setOptions({weaponPreviewScale:v[0],cycleMs:v[1],amplitude:v[2],weaponSwayPx:v[3]})',[k,cycle,amp,sway])
    for visible in [False,True]:
     path=D/f'Gallery/native-phases-{g}-{round(k*100)}-{mode}-{visible}.webp';bundle=Image.open(path);frames=[]
     for index in range(bundle.n_frames):bundle.seek(index);frames.append(canonical(bundle))
     for t in [0,cycle/8,cycle/4,cycle*3/8,cycle/2,cycle*5/8,cycle*3/4,cycle*7/8,cycle,cycle*1.5,cycle*2]:
      data=page.evaluate('v=>{let e=avatarLab.engine;e.time=v[0];e.setLayerVisible("weapon",v[1]);e.render();return e.canvas.toDataURL().split(",")[1]}',[t,visible]);h=canonical(image64(data));assert h in frames,('phase does not match offline Lab',g,k,mode,visible,t)
      checks.append({'gender':g,'scale':k,'mode':mode,'visible':visible,'time':t,'bundle':str(path.relative_to(D)),'decoded_frame':frames.index(h),'canonical_RGBA_SHA256':h,'exact':True})
    print('Verified offline native phases',g,k,mode,flush=True)
  for key in [cfg['poseArtCompleteSurfaces']['rifle-right'],cfg['poseArtCompleteSurfaces']['rifle-left'],cfg['poseArtSurfaces']['art-front-rifle-right'],cfg['poseArtSurfaces']['art-front-rifle-left'],cfg['poseTorsoSurfaces']['rifle'],'assets/weapons/user-ak47-20261026/ak47-master.png','assets/weapons/user-ak47-20261026/ak47-runtime-opaque.png']:
   data=page.evaluate('k=>AVATAR_CORE_EMBED.images[k]',key).split(',')[1];actual=hashlib.sha256(base64.b64decode(data)).hexdigest();reference=D/'Runtime/avatar-core'/key;reference=reference if reference.exists() else R/'avatar-core'/key;assert actual==hashlib.sha256(reference.read_bytes()).hexdigest();hashes[key]=actual
   assert reference.read_bytes()==(R/'avatar-core'/key).read_bytes(),key
  page.evaluate('()=>{let e=avatarLab.engine;e.time=1234;e.setLayerVisible("weapon",true);e.render()}');frame=page.evaluate('JSON.stringify(avatarLab.engine.snapshot().frame)');page.evaluate('avatarLab.engine.setLayerVisible("weapon",false)');assert frame==page.evaluate('JSON.stringify(avatarLab.engine.snapshot().frame)')
  page.evaluate('avatarLab.engine.equipWeaponItem(null)');assert page.evaluate('avatarLab.engine.pose')=='idle'
 assert page.evaluate('JSON.stringify({...localStorage})')==saved
 page.reload();page.wait_for_function('window.avatarLab?.ready');assert page.evaluate('JSON.stringify({...localStorage})')==saved
 b.close()
assert not errors and not external,(errors,external)
movies=[]
for g in ['male','female']:
 for mode,duration in [('standard',8000),('stress',2000)]:
  path=D/f'Gallery/motion-{g}-{mode}.webp';im=Image.open(path);total=0
  for i in range(im.n_frames):im.seek(i);im.load();total+=im.info['duration']
  assert im.n_frames==80 and total==duration,(g,mode,im.n_frames,total);movies.append({'gender':g,'mode':mode,'frames':im.n_frames,'real_playback_duration_ms':total})
record={'directory':str(D),'zip':str(a.zip) if a.zip else None,'hashes':hashes,'native_phase_checks':checks,'native_phases_compared':len(checks),'canonicalization':'Ignore RGB only at alpha0; all visible RGBA exact. WEBP may merge duplicate phases; actual decoded frame is recorded.','continuous_movies':movies,'js_errors':errors,'external_requests':external,'diagnostic_hide_same_pose_time':True,'real_unequip_idle':True,'gender_pose_buttons_checked':True,'localStorage_unchanged_and_reload':True,'full_wardrobe_live_and_physical_device_not_tested':True}
a.receipt.write_text(json.dumps(record,indent=2)+'\n');print('Actual extracted file Lab, all264 native phases, hashes, UI controls and movies verified')
