"""Real index.html screenshots of all 5 x 17 female combinations, palette and saves."""
import functools,io,json,threading,hashlib,sys
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/female-five-hairstyles';CAP=OUT/'captures'

def run():
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 errors=[];missing=[];records=[];color_records=[];styles=json.loads((OUT/'registration.json').read_text());assert len(styles)==5
 all_styles=styles[:];only=sys.argv[sys.argv.index('--style')+1] if '--style' in sys.argv else None
 if only:
  styles=[s for s in styles if s['key']==only];assert len(styles)==1
  previous=json.loads((OUT/'browser-check.json').read_text());changed={s['id'] for s in styles}
  for s in all_styles:
   if s['id'] not in changed:assert previous['runtime_sha256'][s['path']]==hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()
  records=[x for x in previous['combinations'] if x['hair'] not in changed];color_records=[x for x in previous.get('color_combinations',[]) if x['hair'] not in changed]
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1000});page.context.route('https://**/*',lambda r:r.abort());page.on('dialog',lambda d:d.accept());page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:missing.append([r.url,r.status]) if r.status>=400 else None)
   page.goto(f'http://127.0.0.1:{server.server_port}/index.html',wait_until='networkidle');page.evaluate('openCustomization();setGender("female");equipPaperDollItem("face","face-young");setPaperDollView("combat");equipPaperDollItem("upperBody",null);selectWardrobeCategory("appearance");selectWardrobeSlot("hair")')
   protected=page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})');faces=page.evaluate('[null,...PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,"female")).map(i=>({id:i.id,name:i.name}))]');faces[0]={'id':None,'name':'Базове обличчя'}
   def settle():
    page.wait_for_function('''async()=>{for(const i of document.querySelectorAll('img.char-layer:not(.hidden)')){if(!i.complete||!i.naturalWidth)return false;if(i.paperHairRequest){const r=i.paperHairRequest,n=r.lastIndexOf('|');if(i.getAttribute('src')!==await coloredHairSource(r.slice(0,n),r.slice(n+1),i.paperHairColorReference))return false;}const m=i.style.maskImage.match(/url\\(["']?(.*?)["']?\\)/);if(m){const a=new Image();a.src=m[1];await a.decode();}}return true;}''')
   def board(bg='#faf7ef'):
    page.evaluate('''bg=>{document.getElementById('five-board')?.remove();const c=document.createElement('div');c.id='five-board';Object.assign(c.style,{position:'fixed',left:0,top:0,width:'500px',height:'520px',overflow:'hidden',background:bg,zIndex:2147483647});const h=document.createElement('div');h.className='character-paperdoll';Object.assign(h.style,{position:'absolute',width:'941px',height:'1672px',left:'-222px',top:'20px'});c.append(h);document.body.append(c);renderPaperDollAt(h,'five-')}''',bg);settle()
   def shot(path):
    im=Image.open(io.BytesIO(page.locator('#five-board').screenshot())).convert('RGB');im.save(path,lossless=True);return im
   comparison=Image.new('RGB',(1500,350),'#e9e5dd');draw=ImageDraw.Draw(comparison)
   for sn,s in enumerate(styles):
    sid=s['id'];key=s['key'];page.evaluate('equipPaperDollItem("face","face-young");setHairColor("original")');page.locator(f'[data-wardrobe-card="{sid}"]').click();page.locator(f'[data-wardrobe-action="{sid}"]').click();assert page.evaluate('paperDollState.appearance.hair')==sid
    board();im=shot(CAP/f'{key}-young.webp');im.save(OUT/f'{key}.png');comparison.paste(im.resize((300,312)),(sn*300,38));draw.text((sn*300+8,8),s['name'],font=font,fill='#151515')
    montage=Image.new('RGB',(1250,1140),'#e9e5dd');d=ImageDraw.Draw(montage)
    for fn,f in enumerate(faces):
     page.evaluate('f=>{equipPaperDollItem("face",f);setHairColor("original")}',f['id']);board();im=shot(CAP/f'{key}-{f["id"] or "native"}.webp');x=fn%5*250;y=fn//5*285;montage.paste(im.resize((250,260)),(x,y+25));d.text((x+3,y+4),f['name'][:26],font=font,fill='black');records.append({'hair':sid,'face':f['id']})
     layers=page.locator('#five-board img.char-layer:not(.hidden)').evaluate_all('es=>es.map(e=>({id:e.id,z:+e.style.zIndex}))');assert next(x['z'] for x in layers if x['id'].endswith('layer-body'))==0;assert next(x['z'] for x in layers if x['id'].endswith('layer-face'))==1;assert next(x['z'] for x in layers if x['id'].endswith('layer-hair'))==9
    montage.save(OUT/f'{key}-all-heads.webp',lossless=True)
    page.evaluate('equipPaperDollItem("face","face-young")')
    for color in ['original','black','white']:
     page.evaluate('c=>setHairColor(c)',color)
     for label,bg in [('light','#faf7ef'),('gray','#777777'),('black','#000000'),('green','#00ff00')]:board(bg);shot(CAP/f'{key}-{color}-{label}.webp')
    if '--all-colors' in sys.argv:
     colors=page.evaluate('HAIR_COLORS.map(c=>({id:c.id,name:c.name}))');color_sheet=Image.new('RGB',(1250,5*285),'#e9e5dd');cd=ImageDraw.Draw(color_sheet)
     for cn,c in enumerate(colors):
      page.evaluate('equipPaperDollItem("face","face-young")');page.evaluate('c=>setHairColor(c)',c['id']);board();im=shot(CAP/f'{key}-palette-{c["id"]}.webp');x=cn%5*250;y=cn//5*285;color_sheet.paste(im.resize((250,260)),(x,y+25));cd.text((x+4,y+4),c['name'],font=font,fill='black')
      mismatch=page.evaluate("""async c=>{const i=selectedPaperDollItem('hair'),src=i.genderVariants.female,dst=await coloredHairSource(src,c);const load=async s=>{const im=new Image();im.src=s;await im.decode();const cv=document.createElement('canvas');cv.width=im.width;cv.height=im.height;const cx=cv.getContext('2d',{willReadFrequently:true});cx.drawImage(im,0,0);return cx.getImageData(0,0,im.width,im.height).data};const a=await load(src),b=await load(dst);let n=0;for(let k=3;k<a.length;k+=4)if(a[k]!==b[k])n++;return n;}""",c['id']);assert mismatch==0,(key,c['id'],mismatch)
      page.evaluate('document.getElementById("five-board")?.remove()')
      for f in faces:
       page.evaluate('f=>equipPaperDollItem("face",f)',f['id']);settle();assert page.locator('#wardrobe-layer-hair').evaluate('i=>i.complete&&i.naturalWidth===941');color_records.append({'hair':sid,'color':c['id'],'face':f['id']})
     color_sheet.save(OUT/f'{key}-all-colors.webp',lossless=True)
     print('palette verified',key,len(colors)*len(faces),'actual head/color renders',flush=True)
    page.evaluate('document.getElementById("five-board")?.remove();equipPaperDollItem("face","face-young");setHairColor("original");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")');settle();page.reload(wait_until='networkidle');assert page.evaluate('paperDollState.appearance.hair')==sid;assert page.evaluate('paperDollState.appearance.face')=='face-young';assert page.evaluate('paperDollState.appearance.hairColor')=='original';assert page.evaluate('paperDollState.patientLoadout.upperBody')=='patient-tunic';assert page.evaluate('paperDollState.combatLoadout.upperBody') is None
    page.evaluate('openCustomization();setPaperDollView("combat");selectWardrobeCategory("appearance");selectWardrobeSlot("hair")')
    print('checked',sid,len(faces),'faces; palette; reload',flush=True)
   comparison=Image.new('RGB',(1500,350),'#e9e5dd');draw=ImageDraw.Draw(comparison)
   for n,s in enumerate(all_styles):
    im=Image.open(OUT/(s['key']+'.png')).convert('RGB');comparison.paste(im.resize((300,312)),(n*300,38));draw.text((n*300+8,8),s['name'],font=font,fill='#151515')
   comparison.save(OUT/'five-comparison.png');page.screenshot(path=str(OUT/'wardrobe-desktop.png'),full_page=True);page.evaluate('closeCustomization()');page.screenshot(path=str(OUT/'room-desktop.png'),full_page=True);page.evaluate('openCustomization();selectWardrobeSlot("hair")')
   for width,height in [(320,568),(390,844)]:
    page.set_viewport_size({'width':width,'height':height});page.locator('[data-wardrobe-card="hair-f5-pixie"]').scroll_into_view_if_needed();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(OUT/f'wardrobe-mobile-{width}.png'),full_page=True)
   page.evaluate('setGender("male");selectWardrobeSlot("hair")');assert page.locator('[data-wardrobe-card^="hair-f5-"]').count()==0;assert page.evaluate('paperDollState.appearance.hair')=='hair-none'
   page.evaluate('setGender("female");equipPaperDollItem("hair","hair-f5-pixie");equipPaperDollItem("hair","hair-none")');settle();assert page.locator('#layer-hair').get_attribute('src') is None;assert page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')==protected;assert not errors and not missing,(errors,missing)
   result={'browser':'Chromium '+browser.version,'entry':'index.html','faces':faces,'combinations':records,'combination_count':len(records),'all_color_head_combinations':len(color_records),'color_combinations':color_records,'palette':['original','black','white'],'backgrounds':['light','gray','black','green'],'ui_selection':True,'reload_each_style':True,'patient_trip_independent':True,'male_exclusion':True,'unequip':True,'protected_state_unchanged':True,'mobile_emulation':[320,390],'js_errors':errors,'http_errors':missing,'runtime_sha256':{s['path']:hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest() for s in all_styles},'incremental_style_rechecked':only,'unchanged_styles_reused':[s['key'] for s in all_styles if only and s['key']!=only]}
   (OUT/'browser-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');browser.close()
 finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':run()
