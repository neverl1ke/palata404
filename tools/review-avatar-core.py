"""Real Avatar Lab screenshots and reproducible breathing frames, never generated art."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import functools,threading,json,io
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/avatar-core-1';OUT.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();errors=[];http=[];states=[];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
def pair(a,b,title,path):
 out=Image.new('RGB',(a.width+b.width,max(a.height,b.height)+46),'#d3cfc6');d=ImageDraw.Draw(out);d.text((12,9),title+' · ОРИГІНАЛ',font=font,fill='#182322');d.text((a.width+12,9),'МОДУЛЬНИЙ РИГ',font=font,fill='#182322');out.paste(a,(0,46));out.paste(b,(a.width,46));out.save(path,lossless=True)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch();page=browser.new_page(viewport={'width':1560,'height':2050},device_scale_factor=1);page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:http.append([r.url,r.status]) if r.status>=400 else None);page.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');page.wait_for_function('window.avatarLab?.ready');page.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({breathing:false,transitionMs:0});Object.assign(avatarLab.engine.canvas.style,{width:"941px",height:"1672px",maxWidth:"none",minWidth:"0"});avatarLab.engine.render()');before=page.evaluate('JSON.stringify({...localStorage})')
  for gender in ['male','female']:
   page.evaluate('async g=>{const e=avatarLab.engine;await e.setGender(g);await e.setAppearance({layers:[]});e.time=0;e.setOptions({breathing:false,view:"rig"})}',gender)
   for pose in ['idle','melee','pistol','rifle']:
    page.evaluate('p=>avatarLab.engine.setPose(p)',pose);page.locator('#avatar').screenshot(path=str(OUT/f'{gender}-{pose}.png'));states.append(page.evaluate('avatarLab.engine.snapshot()'))
   page.evaluate('avatarLab.engine.setPose("idle");avatarLab.engine.setOptions({view:"original"})');page.locator('#avatar').screenshot(path=str(OUT/f'{gender}-original.png'));page.evaluate('avatarLab.engine.setOptions({view:"rig"})');a=Image.open(OUT/f'{gender}-original.png').convert('RGB');b=Image.open(OUT/f'{gender}-idle.png').convert('RGB');pair(a,b,'Чоловік' if gender=='male' else 'Жінка',OUT/f'{gender}-original-vs-rig.webp')
   page.evaluate('avatarLab.engine.setPose("rifle");avatarLab.engine.setOptions({debugPivots:true,debugGrips:true})');page.locator('#avatar').screenshot(path=str(OUT/f'{gender}-skeleton.png'));page.evaluate('avatarLab.engine.setOptions({debugPivots:false,debugGrips:false})');f=page.evaluate('avatarLab.engine.frame');im=Image.open(OUT/f'{gender}-rifle.png')
   for side in ['right','left']:
    for joint in ['shoulder','elbow','grip']:
     x,y=f['arms'][side][joint];box=(round(x-95),round(y-90),round(x+95),round(y+100));im.crop(box).resize((570,570)).save(OUT/f'{gender}-{side}-{joint}-300.webp',lossless=True)
   page.evaluate('avatarLab.engine.setOptions({breathing:true})')
   for phase,t in [('inhale',1000),('exhale',3000)]:page.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);page.locator('#avatar').screenshot(path=str(OUT/f'{gender}-{phase}.png'))
   page.evaluate('Object.assign(avatarLab.engine.canvas.style,{width:"470px",height:"835.133px"});avatarLab.engine.render()');frames=[]
   for t in range(0,4000,160):
    page.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);frames.append(Image.open(io.BytesIO(page.locator('#avatar').screenshot())).convert('RGB'))
   frames[0].save(OUT/f'{gender}-breathing.webp',save_all=True,append_images=frames[1:],duration=160,loop=0,lossless=True)
   page.evaluate('Object.assign(avatarLab.engine.canvas.style,{width:"941px",height:"1672px"});avatarLab.engine.time=0;avatarLab.engine.setOptions({breathing:false,pistolSupport:true});avatarLab.engine.setPose("pistol")');page.locator('#avatar').screenshot(path=str(OUT/f'{gender}-pistol-supported.png'));page.evaluate('avatarLab.engine.setOptions({pistolSupport:false})');print('captured',gender,'four poses, joints, original comparison and 25 breathing frames',flush=True)
  assert before==page.evaluate('JSON.stringify({...localStorage})')
  page.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');page.wait_for_function('window.avatarLab?.ready');page.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({breathing:false,transitionMs:0});avatarLab.engine.setPose("rifle")');page.screenshot(path=str(OUT/'lab-desktop.png'),full_page=True)
  page.locator('#sleeves').check();page.wait_for_function('avatarLab.engine.equipment.size===4&&Array.from(avatarLab.engine.equipment.values()).every(v=>v.bitmap)');page.locator('#avatar').screenshot(path=str(OUT/'male-test-sleeves.png'));page.locator('[data-gender="female"]').click();page.wait_for_function('avatarLab.engine.gender==="female"&&document.getElementById("status").textContent.startsWith("Готово")');page.wait_for_function('Array.from(avatarLab.engine.equipment.values()).every(v=>v.bitmap)');page.locator('#avatar').screenshot(path=str(OUT/'female-test-sleeves.png'));page.locator('#sleeves').uncheck()
  for width in [320,390,768]:page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(OUT/f'lab-mobile-{width}.png'),full_page=True)
  result={'browser':'Chromium '+browser.version,'entry':'avatar-lab/index.html','states':states,'js_errors':errors,'http_errors':http,'storage_unchanged':True,'mobile_emulation':[320,390,768],'capture_frame':[941,1672],'pose_references':'User reference images guide positioning only; not included as game assets.','art_status':'Mechanical prototype. Relaxed source fingers and strong elbow folds require artist review; not production approved.'};(OUT/'browser-check.json').write_text(json.dumps(result,indent=2)+'\n');assert not errors and not http,(errors,http);browser.close()
finally:server.shutdown();server.server_close()
print('Captured eight full-length poses from actual Avatar Lab, no JS errors/404.')
