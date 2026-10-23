import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_game import GameTests,ROOT
out=ROOT/'review/avatar-face-hair-update';out.mkdir(exist_ok=True)
GameTests.setUpClass();t=GameTests();t.setUp()
try:
 t.load();p=t.page;p.set_viewport_size({'width':1600,'height':2600})
 def gallery(n,w):
  p.evaluate('''([n,w])=>{const g=document.createElement('div');g.id='update-gallery';Object.assign(g.style,{position:'fixed',inset:'0',right:'auto',bottom:'auto',width:w+'px',padding:'8px',display:'grid',gridTemplateColumns:'repeat('+n+',1fr)',gap:'8px',background:'#ddd8cf',color:'#222',font:'16px sans-serif',zIndex:'2147483647'});document.body.append(g)}''',[n,w])
 def shot(prefix,label,bg,s=1.5,w=330,h=515):
  p.evaluate('''([prefix,label,bg,s,w,h])=>{const c=document.createElement('article');c.innerHTML='<strong>'+label+'</strong>';const v=document.createElement('div');Object.assign(v.style,{position:'relative',width:w+'px',height:h+'px',overflow:'hidden',background:bg});const host=document.createElement('div');host.className='character-paperdoll';Object.assign(host.style,{position:'absolute',width:941*s+'px',height:1672*s+'px',left:w/2-474*s+'px',top:0});v.append(host);c.append(v);document.getElementById('update-gallery').append(c);renderPaperDollAt(host,prefix)}''',[prefix,label,bg,s,w,h])
  p.wait_for_function('''async prefix=>{const b=document.getElementById(prefix+'layer-body'),f=document.getElementById(prefix+'layer-face'),h=document.getElementById(prefix+'layer-hair');if(!b.complete)return false;if(selectedPaperDollItem('face')&&(!f.complete||f.naturalWidth!==941||f.classList.contains('hidden')||f.getAttribute('src')!==selectedPaperDollItem('face').genderVariants[paperDollState.selectedGender]))return false;if(selectedPaperDollItem('hair').id!=='hair-none'){const src=await coloredHairSource(selectedPaperDollItem('hair').genderVariants[paperDollState.selectedGender],paperDollState.appearance.hairColor);return h.src.endsWith(src)&&h.complete}return true}''',arg=prefix)
 for gender in ['male','female']:
  p.evaluate('g=>{setGender(g);setPaperDollView("combat");setHairColor("original");equipPaperDollItem("hair","hair-none")}',gender)
  gallery(4,1400)
  for j,face in enumerate([None,'face-asian','face-young','face-exhausted','face-elder','face-alternative']):
   for n,hair in enumerate(['hair-none','hair-bob-bangs']):
    p.evaluate('([f,h])=>{equipPaperDollItem("face",f);equipPaperDollItem("hair",h)}',[face,hair])
    if face:p.evaluate('''async()=>{const src=selectedPaperDollItem('face').bodyMaskByGender?.[paperDollState.selectedGender];if(src){const i=new Image();i.src=src;await i.decode()}}''')
    shot(f'{gender}-{j}-{n}-',p.evaluate('()=>selectedPaperDollItem("face")?.name||"Базове обличчя"')+' · '+('без волосся' if n==0 else 'нове каре'),'#faf7ef')
  p.locator('#update-gallery').screenshot(path=str(out/(gender+'-all-faces-bob.jpg')),type='jpeg',quality=95);p.locator('#update-gallery').evaluate('e=>e.remove()')
  gallery(4,1400);p.evaluate('equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-none")')
  for n,bg in enumerate(['#fff','#555','#000','#00ff00']):shot(gender+'-bg'+str(n)+'-','Нове обличчя',bg)
  p.locator('#update-gallery').screenshot(path=str(out/(gender+'-four-backgrounds.png')),type='png');p.locator('#update-gallery').evaluate('e=>e.remove()')
  gallery(4,1400);p.evaluate('equipPaperDollItem("face",null);equipPaperDollItem("hair","hair-none")')
  for n,bg in enumerate(['#fff','#555','#000','#00ff00']):shot(gender+'-base-bg'+str(n)+'-','Базовий аватар',bg,.5,330,850)
  p.locator('#update-gallery').screenshot(path=str(out/(gender+'-base-four-backgrounds.jpg')),type='jpeg',quality=95);p.locator('#update-gallery').evaluate('e=>e.remove()')
  gallery(4,1400);p.evaluate('equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-bob-bangs")')
  for n,bg in enumerate(['#fff','#555','#000','#00ff00']):shot(gender+'-bob-bg'+str(n)+'-','Нове обличчя + каре',bg)
  p.locator('#update-gallery').screenshot(path=str(out/(gender+'-bob-four-backgrounds.jpg')),type='jpeg',quality=96);p.locator('#update-gallery').evaluate('e=>e.remove()')
  gallery(4,1400)
  for n,hair in enumerate(['hair-none','hair-classic-short','hair-textured-short','hair-messy','hair-bob','hair-double-buns','hair-shoulder-length','hair-bob-bangs']):
   p.evaluate('h=>equipPaperDollItem("hair",h)',hair);shot(gender+'-styles'+str(n)+'-',p.evaluate('()=>selectedPaperDollItem("hair").name'),'#faf7ef')
  p.locator('#update-gallery').screenshot(path=str(out/(gender+'-all-hair-new-face.jpg')),type='jpeg',quality=95);p.locator('#update-gallery').evaluate('e=>e.remove()')
  for face,hair,key in [(None,'hair-none','base'),('face-alternative','hair-none','face'),('face-alternative','hair-bob-bangs','bob')]:
   p.evaluate('([f,h])=>{equipPaperDollItem("face",f);equipPaperDollItem("hair",h);openCustomization();selectWardrobeCategory("appearance");selectWardrobeSlot("face")}',[face,hair])
   p.locator('.wardrobe-document').screenshot(path=str(out/(gender+'-'+key+'-wardrobe.jpg')),type='jpeg',quality=93)
 for gender in ['male','female']:
  p.evaluate('g=>{setGender(g);setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic");equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-bob-bangs");setHairColor("original");openCustomization()}',gender)
  p.wait_for_function("""()=>['wardrobe-layer-face','wardrobe-layer-hair','wardrobe-layer-upper-body-front'].every(id=>{const i=document.getElementById(id);return i.complete&&i.naturalWidth>0&&!i.classList.contains('hidden')})""")
  p.set_viewport_size({'width':1440,'height':1000});p.locator('.wardrobe-document').screenshot(path=str(out/(gender+'-patient-desktop.jpg')),type='jpeg',quality=93)
  p.set_viewport_size({'width':390,'height':844});p.locator('.wardrobe-stage').screenshot(path=str(out/(gender+'-patient-phone.jpg')),type='jpeg',quality=93)
 print(json.dumps({'errors':t.errors}))
finally:t.tearDown();GameTests.tearDownClass()
