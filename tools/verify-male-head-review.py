from pathlib import Path
from io import BytesIO
import sys,hashlib
import json,threading,http.server,functools,base64,time
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
repo=Path(__file__).resolve().parents[1];report=repo/'review/male-head-hair-20261104';m=json.loads((report/'integration.json').read_text());cfg=m['config'];results=[];errors=[];pixels_only='--pixels-only' in sys.argv
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(repo)));threading.Thread(target=s.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 b=pw.chromium.launch();page=b.new_page(viewport={'width':1600,'height':1900},device_scale_factor=1);page.route('https://**',lambda route:route.abort());page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{s.server_port}/index.html',wait_until='networkidle');page.wait_for_function('typeof renderPaperDollAt === "function" && typeof paperDollState === "object"')
 page.evaluate('''()=>{for(const key of ['patientLoadout','combatLoadout'])for(const slot of Object.keys(paperDollState[key]))paperDollState[key][slot]=null;paperDollState.activeViewMode='patient';let h=document.createElement('div');h.id='integration-stage';h.style.cssText='position:fixed;left:0;top:0;width:941px;height:1672px;background:#f7f4eb;z-index:2147483647;overflow:hidden;';document.body.appendChild(h);}''')
 # Decode CSS masks as well as image sources before screenshot capture.
 page.evaluate('''async()=>{await Promise.all(PAPER_DOLL_ITEMS.filter(x=>x.slot==='face').flatMap(x=>Object.values(x.bodyMaskByGender||{})).map(async p=>{let i=new Image();i.src=p;await i.decode()}))}''')
 def render(g,face,hair,color='original'):
  page.evaluate('''([gender,face,hair,color])=>{paperDollState.selectedGender=gender;paperDollState.appearance={face,hair,hairColor:color};renderPaperDoll();renderPaperDollAt(document.getElementById('integration-stage'),'integration-');}''',[g,face,hair,color]);page.wait_for_function('''()=>Array.from(document.querySelectorAll('#integration-stage img')).filter(i=>i.getAttribute('src')).every(i=>i.complete&&i.naturalWidth>0&&!i.classList.contains('hidden'))''');page.evaluate('''()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))''')
 portraits={}
 for rec in m['records']:
  render('male',None if rec['face_id']=='@native' else rec['face_id'],rec['hair']);raw=page.screenshot(clip={'x':300,'y':0,'width':345,'height':360},animations='disabled');portrait=Image.new('RGB',(345,370),'#f7f4eb');portrait.paste(Image.open(BytesIO(raw)).convert('RGB'),(0,10));approved=np.array(Image.open(repo/rec['reference']).convert('RGB'));actual=np.array(portrait);diff=np.abs(actual.astype(float)-approved.astype(float));entry={'head':rec['head'],'hair':rec['hair'],'mean_abs_error':float(diff.mean()),'max_error':int(diff.max()),'central_face_error':int(diff[130:275,140:205].max())};results.append(entry);portraits[(rec['head'],rec['number'])]=portrait
  assert page.evaluate("()=>Array.from(document.querySelectorAll('#integration-stage [id$=skin-edge]')).every(i=>getComputedStyle(i).zIndex==='2')")
  assert entry['mean_abs_error']<1.2,entry
  assert entry['central_face_error']<=2,entry
 combinations=[]
 if not pixels_only:
  # Every accepted male head and all12 styles load in both actual hosts and preserve root hair IDs.
  combinations=page.evaluate('''()=>{let hair=PAPER_DOLL_ITEMS.filter(x=>x.slot==='hair'&&x.id!=='hair-none'&&paperDollItemSupportsGender(x,'male'));return Object.keys(MALE_HAIR_REVIEW.heads).flatMap(face=>hair.map(x=>[face==='@native'?null:face,x.id]))}''')
  for face,hair in combinations:
   render('male',face,hair);assert page.evaluate('''()=>['layer-hair','wardrobe-layer-hair'].every(id=>{let i=document.getElementById(id);return i.complete&&i.naturalWidth>0&&!i.classList.contains('hidden')})'''),(face,hair)
  # Recoloring leaves own skin-edge layers untouched and races resolve to selected head.
  for face in [None,'face-male-new-almond','face-male-goth-pierced']:
   for hair in ['hair-shoulder-length','hair-m6-mullet','hair-m6-asymmetric-fringe']:
    for color in ['black','platinum','blue']:
     render('male',face,hair,color);assert page.evaluate('''()=>{let e=document.getElementById('integration-layer-hair-skin-edge');return !e||e.paperHairRequest.endsWith('|original')}''')
  render('female',None,'hair-shoulder-length','original');assert page.evaluate('''()=>!document.querySelector('#integration-stage [id$="skin-edge"]')&&document.getElementById('layer-hair').paperHairFitKey.startsWith('F')''')
  render('male','face-male-new-youthful','hair-m6-mullet');page.evaluate("paperDollState.appearance.hair='hair-none';renderPaperDoll();renderPaperDollAt(document.getElementById('integration-stage'),'integration-');");assert page.evaluate('''()=>!document.querySelector('#integration-stage [data-paper-extra]')&&!document.getElementById('integration-layer-hair').getAttribute('src')''')
  page.evaluate("paperDollState.appearance.hair='hair-m6-cornrows';savePaperDollState()");page.reload(wait_until='networkidle');assert page.evaluate("paperDollState.appearance.hair==='hair-m6-cornrows'&&paperDollState.appearance.face==='face-male-new-youthful'")
 b.close()
s.shutdown()
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';tf=ImageFont.truetype(font,26);sf=ImageFont.truetype(font,17);board=Image.new('RGB',(1432,2842),'#e8e5dd');d=ImageDraw.Draw(board);d.text((16,14),'Гра · усі 16 голів · погоджені зачіски №6, №9 та №12',font=tf,fill='#292925')
for k in range(1,17):
 x=16+((k-1)%2)*710;y=64+((k-1)//2)*342;d.text((x+5,y+3),f'M{k:02}',font=sf,fill='#292925')
 for j,n in enumerate([6,9,12]):d.text((x+j*230+6,y+30),f'№{n}',font=sf,fill='#49483f');board.paste(portraits[(f'M{k:02}',n)].crop((45,15,300,325)).resize((230,280),Image.Resampling.LANCZOS),(x+j*230,y+56))
board.save(report/'game-all16-hair06-09-12.png',optimize=True)
checks={'actual_game_renderer':True,'native_frame':[941,1672],'comparisons':results,'all_male_combinations_loaded':len(combinations),'colors_checked':[] if pixels_only else ['black','platinum','blue'],'female_switch_cleanup':None if pixels_only else True,'unequip_cleanup':None if pixels_only else True,'stable_save_ids':None if pixels_only else True,'fit_data_sha256':hashlib.sha256((repo/'male-hair-fit-data.js').read_bytes()).hexdigest(),'page_errors':errors,'worst_mean_error':max(x['mean_abs_error'] for x in results)};(report/('final-pixel-checks.json' if pixels_only else 'browser-checks.json')).write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'comparisons':48,'combinations':len(combinations),'worst_mean_error':checks['worst_mean_error'],'page_errors':errors}))
