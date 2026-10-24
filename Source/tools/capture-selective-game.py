"""Real index.html inventory preview and actual Canvas contrast-background renders."""
from pathlib import Path
import functools,threading,json,io,base64
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-selective-merge';G=O/'Gallery';errors=[];missing=[];rows=[]
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{s.server_port}/'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page(viewport={'width':1440,'height':1100});p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:missing.append(r.url) if r.status>=400 else None);p.route('https://**/*',lambda r:r.abort());p.goto(url+'index.html?avatarCore=1');p.wait_for_function('window.avatarCoreGamePreview');p.evaluate('()=>{setPaperDollView("combat");for(const k of Object.keys(paperDollState.combatLoadout))paperDollState.combatLoadout[k]=null;for(const name of ["Іржавий ніж","ПМ (Пістолет Макарова)","Штурмовий АКС-74У"])inventory.push({name,category:"weapon",count:1});openCustomization();selectWardrobeCategory("weapons")}')
 for g in ['male','female']:
  p.evaluate('g=>setGender(g)',g)
  for ident in ['gear-knife','gear-pm','gear-aks']:
   p.locator(f'[data-wardrobe-item="{ident}"]').click();p.locator(f'[data-wardrobe-action="{ident}"]').click();p.wait_for_function('id=>[...avatarCoreGamePreview.instances.values()].every(s=>s.engine?.selectedWeaponId===id)',arg=ident)
   p.evaluate('()=>{for(const s of avatarCoreGamePreview.instances.values()){s.engine.pause();s.engine.time=0;s.engine.render()}}');p.screenshot(path=str(G/f'game-{g}-{ident}-1440.png'));rows.append({'gender':g,'item':ident,'width':1440,'screen':'real wardrobe + equipped existing inventory item'})
 for w in [320,390,768]:
  p.set_viewport_size({'width':w,'height':844});p.evaluate('renderWardrobe()');p.wait_for_timeout(200);p.screenshot(path=str(G/f'game-female-wardrobe-{w}.png'),full_page=True);overflow=p.evaluate('document.documentElement.scrollWidth>innerWidth');rows.append({'width':w,'mobile_emulation':True,'horizontal_overflow':overflow});assert not overflow
 p.set_viewport_size({'width':1440,'height':1100});p.evaluate('setPaperDollView("patient")');p.wait_for_timeout(200);p.screenshot(path=str(G/'game-patient-tunic-preserved.png'));rows.append({'patient_tunic_preserved':p.evaluate('selectedPaperDollItem("upperBody")?.id==="patient-tunic"'),'core_blocked_for_unprepared_clothing':p.evaluate('!!document.querySelector("[data-avatar-core-blocked]")')})
 p.close();p=b.new_page(viewport={'width':1400,'height':1800});p.goto(url+'avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",minWidth:0,maxWidth:"none",maxHeight:"none"});e.setOptions({breathing:false})}')
 for g in ['male','female']:
  p.evaluate('g=>avatarLab.engine.setGender(g)',g)
  for pose in ['idle','melee','pistol','rifle']:
   p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',{'idle':None,'melee':'gear-knife','pistol':'gear-pm','rifle':'gear-aks'}[pose]);p.evaluate('p=>{avatarLab.engine.time=0;avatarLab.engine.setPose(p)}',pose)
   for visible in [False] if pose=='idle' else [False,True]:
    sheet=Image.new('RGB',(1600,737),'#ddd');d=ImageDraw.Draw(sheet)
    for i,(name,color) in enumerate([('white','#fff'),('gray','#777'),('black','#000'),('green','#0f0')]):
     p.evaluate('v=>{let e=avatarLab.engine;e.setLayerVisible("weapon",v[0]);e.setOptions({background:v[1]})}',[visible,color]);im=Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGB');sheet.paste(im.resize((400,711)),(400*i,26));d.text((400*i+5,4),name,font=font,fill='black');rows.append({'gender':g,'pose':pose,'weapon_visible':visible,'actual_canvas_background':color,'native_size':[941,1672]})
    sheet.save(G/f'backgrounds-{g}-{pose}-{visible}.webp',lossless=True)
 b.close()
s.shutdown();(O/'Evidence/actual-game-review.json').write_text(json.dumps({'cases':rows,'js_errors':errors,'http_errors':missing,'physical_device':False},ensure_ascii=False,indent=2)+'\n');assert not errors and not missing;print('Real wardrobe screenshots, patient clothing fallback, 56 actual Canvas background renders; no JS/HTTP errors')
