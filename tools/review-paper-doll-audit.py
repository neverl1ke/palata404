"""Capture the real index.html renderer: 90 combinations, 4 backgrounds, 2 colors.
Use --phase before/after. Historic galleries are never overwritten.
"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_game import GameTests,ROOT
p=argparse.ArgumentParser();p.add_argument('--phase',required=True,choices=['before','after']);p.add_argument('--ui-only',action='store_true');a=p.parse_args();out=ROOT/'review/paper-doll-audit-2026-10'/a.phase;out.mkdir(parents=True,exist_ok=True)
if a.phase=='before' and (out/'capture.json').exists():raise SystemExit('Historic before capture already exists; refusing to overwrite it')
if a.ui_only and a.phase!='after':raise SystemExit('--ui-only is for after only')
GameTests.setUpClass();t=GameTests();t.setUp();records=[];missing=[]
try:
 t.load();page=t.page;page.set_viewport_size({'width':1500,'height':2600});page.on('response',lambda r:missing.append(r.url) if r.status>=400 else None)
 def settle(prefix):
  page.wait_for_function('''async prefix=>{const host=document.getElementById(prefix+'host');for(const i of host.querySelectorAll('img:not(.hidden)')){const request=i.paperHairRequest;if(!request)continue;const cut=request.lastIndexOf('|'),src=request.slice(0,cut),color=request.slice(cut+1);const expected=color==='original'?src:await coloredHairSource(src,color,i.paperHairColorReference);if(i.getAttribute('src')!==expected||!i.complete||!i.naturalWidth)return false;const mask=i.style.maskImage.match(/url\\(["']?(.*?)["']?\\)/);if(mask){const m=new Image();m.src=mask[1];await m.decode()}}return true}''',arg=prefix)
 def start(cols=4):
  page.evaluate('''n=>{const g=document.createElement('section');g.id='audit-gallery';Object.assign(g.style,{position:'fixed',left:0,top:0,width:'1384px',padding:'8px',display:'grid',gridTemplateColumns:'repeat('+n+',1fr)',gap:'8px',background:'#d6d2ca',font:'14px sans-serif',color:'#222',zIndex:2147483647});document.body.append(g)}''',cols)
 def panel(prefix,title,bg,full=False):
  page.evaluate('''([prefix,title,bg,full])=>{const c=document.createElement('article');c.innerHTML='<strong>'+title+'</strong>';const v=document.createElement('div');const s=full?.48:1.35;Object.assign(v.style,{position:'relative',width:'336px',height:full?'810px':'430px',background:bg,overflow:'hidden'});const host=document.createElement('div');host.id=prefix+'host';host.className='character-paperdoll';Object.assign(host.style,{position:'absolute',left:168-474*s+'px',top:0,width:941*s+'px',height:1672*s+'px'});v.append(host);c.append(v);document.getElementById('audit-gallery').append(c);renderPaperDollAt(host,prefix)}''',[prefix,title,bg,full]);settle(prefix)
 def save(name):
  page.locator('#audit-gallery').screenshot(path=str(out/(name+'.jpg')),type='jpeg',quality=96);page.locator('#audit-gallery').evaluate('e=>e.remove()')
 for gender in ([] if a.ui_only else ['male','female']):
  hair=page.evaluate('g=>PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair"&&paperDollItemSupportsGender(i,g)).map(i=>i.id)',gender)
  for face in [None,'face-asian','face-young','face-exhausted','face-elder','face-alternative']:
   for color in ['original','white']:
    start();page.evaluate('([g,f,c])=>{setGender(g);setPaperDollView("combat");equipPaperDollItem("face",f);setHairColor(c)}',[gender,face,color])
    for j,h in enumerate(hair):
     page.evaluate('h=>equipPaperDollItem("hair",h)',h)
     for k,bg in enumerate(['#fff','#555','#000','#00ff00']):panel(f'audit-{j}-{k}-',h+' · '+color,bg)
     records.append({'gender':gender,'face':face,'hair':h,'color':color,'backgrounds':4})
    save(gender+'-'+(face or 'native')+'-'+color)
  start();page.evaluate('g=>{setGender(g);equipPaperDollItem("face",null);equipPaperDollItem("hair","hair-none")}',gender)
  for k,bg in enumerate(['#fff','#555','#000','#00ff00']):panel(f'body-{k}-',gender+' · база',bg,True)
  save(gender+'-body')
 for w,h in [(320,568),(360,640),(390,844),(430,844),(768,844),(1440,1000)]:
  page.set_viewport_size({'width':w,'height':h});page.evaluate('setGender("female");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic");equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-bob-bangs");setHairColor("original");openCustomization();selectWardrobeCategory("appearance")')
  for slot in ['face','hair']:
   page.evaluate('s=>selectWardrobeSlot(s)',slot)
   if slot=='face':page.locator('[data-wardrobe-card="face-alternative"]').scroll_into_view_if_needed()
   page.screenshot(path=str(out/f'wardrobe-{w}-{slot}.jpg'),type='jpeg',quality=94)
  if a.phase=='after' and w in [320,390,768]:
   page.locator('[data-palette-toggle]').click();page.screenshot(path=str(out/f'wardrobe-{w}-palette.jpg'),type='jpeg',quality=94)
   page.evaluate('selectWardrobeCategory("clothes")');page.screenshot(path=str(out/f'wardrobe-{w}-clothes.jpg'),type='jpeg',quality=94)
 if a.phase=='after' and not a.ui_only:
  page.set_viewport_size({'width':1500,'height':2600})
  for g,style,colors in [('male','hair-shoulder-length',['original','black','white','red','blue']),('female','hair-bob-bangs',['original','black','white'])]:
   for color in colors:
    start()
    for j,face in enumerate([None,'face-asian','face-young','face-exhausted','face-elder','face-alternative']):
     page.evaluate('([g,f,h,c])=>{setGender(g);setPaperDollView("combat");equipPaperDollItem("face",f);equipPaperDollItem("hair",h);setHairColor(c)}',[g,face,style,color])
     for k,bg in enumerate(['#fff','#555','#000','#00ff00']):panel(f'palette-{j}-{k}-',(face or 'Базове')+' · '+color,bg)
    save(g+'-target-palette-'+color)
 result={'phase':a.phase,'unique_combinations':len({(e['gender'],e['face'],e['hair']) for e in records}),'render_samples':sum(e['backgrounds'] for e in records),'records':records,'page_errors':t.errors,'http_errors':missing}
 if a.ui_only:result={'phase':'after-ui','viewport_widths':[320,360,390,430,768,1440],'page_errors':t.errors,'http_errors':missing}
 (out/('ui-capture.json' if a.ui_only else 'capture.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)
 assert not t.errors and not missing
finally:t.tearDown();GameTests.tearDownClass()
