"""Lossless, same-camera in-game detail captures from current or immutable snapshot."""
import argparse,sys,json,mimetypes
from pathlib import Path
from urllib.parse import urlparse,unquote
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_game import GameTests,ROOT
p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=ROOT/'review/paper-doll-audit-2026-10');p.add_argument('--phase',choices=['before','after'],required=True);p.add_argument('--snapshot',type=Path);p.add_argument('--targeted',action='store_true');a=p.parse_args()
if a.phase=='before' and not a.snapshot:p.error('before requires the immutable snapshot')
out=a.output_dir/a.phase;out.mkdir(exist_ok=True)
if a.phase=='before' and (out/'male-base-head-detail.png').exists():raise SystemExit('Historic detail capture already exists; refusing to overwrite it')
GameTests.setUpClass();t=GameTests();t.setUp()
try:
 if a.phase=='before':
  def original(route):
   rel=unquote(urlparse(route.request.url).path).lstrip('/') or 'index.html';path=a.snapshot/rel
   if path.is_file() and '..' not in Path(rel).parts:route.fulfill(body=path.read_bytes(),content_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
   else:route.continue_()
  t.context.route(GameTests.url+'**',original)
 t.load();page=t.page;page.set_viewport_size({'width':2400,'height':1800})
 cases=[]
 for g in ['male','female']:
  for region,box in [('head',(360,0,585,255)),('neck',(350,210,600,325)),('hand',(100,760,265,1050)),('feet',(270,1500,710,1672))]:cases.append((g,None,'hair-none',g+'-base-'+region,box))
  for region,box in [('head',(360,0,585,255)),('neck',(350,210,600,325))]:cases.append((g,'face-alternative','hair-none',g+'-alternative-'+region,box))
 cases.extend([('male','face-alternative','hair-messy','male-messy',(350,0,600,300)),('male','face-alternative','hair-shoulder-length','male-shoulder',(350,0,600,300)),('female','face-asian','hair-none','female-asian-neck',(350,170,600,325))])
 if a.targeted:
  cases.extend([('male','face-asian','hair-none','male-asian-head',(350,0,600,280)),('male','face-asian','hair-none','male-asian-neck',(350,190,600,310)),('female','face-exhausted','hair-none','female-exhausted-head',(350,0,600,280)),('female','face-exhausted','hair-none','female-exhausted-neck',(350,190,600,310)),('female','face-alternative','hair-none','female-alternative-ear-left',(385,120,435,242)),('female','face-alternative','hair-none','female-alternative-ear-right',(518,120,568,242)),('female',None,'hair-none','female-inner-thighs',(310,790,630,1120))])
 for number,(g,face,hair,name,box) in enumerate(cases):
  scale=4 if '-ear-' in name else 1.2
  page.evaluate('([g,f,h])=>{setGender(g);setPaperDollView("combat");equipPaperDollItem("face",f);equipPaperDollItem("hair",h);setHairColor("original")}',[g,face,hair])
  page.evaluate('''()=>{const v=document.createElement('div');v.id='detail-gallery';Object.assign(v.style,{position:'fixed',left:0,top:0,width:'2304px',display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'8px',padding:'8px',background:'#d6d2ca',zIndex:2147483647});document.body.append(v)}''')
  for k,bg in enumerate(['#fff','#555','#000','#00ff00']):
   prefix=f'detail-{number}-{k}-'
   page.evaluate('''([prefix,bg,box,scale])=>{const v=document.createElement('div');Object.assign(v.style,{position:'relative',width:'560px',height:(box[3]-box[1])*scale+'px',background:bg,overflow:'hidden'});const host=document.createElement('div');host.id=prefix+'host';host.className='character-paperdoll';Object.assign(host.style,{position:'absolute',width:941*scale+'px',height:1672*scale+'px',left:(560-(box[2]-box[0])*scale)/2-box[0]*scale+'px',top:-box[1]*scale+'px'});v.append(host);document.getElementById('detail-gallery').append(v);renderPaperDollAt(host,prefix)}''',[prefix,bg,box,scale])
   page.wait_for_function('''async prefix=>{for(const i of document.getElementById(prefix+'host').querySelectorAll('img:not(.hidden)')){if(!i.complete||!i.naturalWidth)return false;const mask=i.style.maskImage.match(/url\\(["']?(.*?)["']?\\)/);if(mask){const m=new Image();m.src=mask[1];await m.decode()}}return true}''',arg=prefix)
  page.locator('#detail-gallery').screenshot(path=str(out/(name+'-detail.png')));page.locator('#detail-gallery').evaluate('e=>e.remove()')
 print(json.dumps({'phase':a.phase,'details':len(cases),'scale':1.2,'backgrounds':4,'errors':t.errors}));assert not t.errors
finally:t.tearDown();GameTests.tearDownClass()
