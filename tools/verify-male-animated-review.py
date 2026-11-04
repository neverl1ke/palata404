from pathlib import Path
from io import BytesIO
import json,base64,threading,http.server,functools
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
repo=Path(__file__).resolve().parents[1];report=repo/'review/male-head-hair-20261104';m=json.loads((report/'integration.json').read_text());results=[];errors=[]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(repo)));threading.Thread(target=s.serve_forever,daemon=True).start()
with sync_playwright() as pw:
 b=pw.chromium.launch();page=b.new_page(viewport={'width':1280,'height':900});page.route('https://**',lambda route:route.abort());page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{s.server_port}/index.html',wait_until='networkidle');page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("weapon",null);setGender("male");setHairColor("original")')
 for rec in m['records']:
  page.evaluate('([f,h])=>{equipPaperDollItem("face",f);equipPaperDollItem("hair",h)}',[None if rec['face_id']=='@native' else rec['face_id'],rec['hair']]);page.wait_for_function('''()=>{let s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll'));return s?.host.dataset.avatarCoreReady==='true'&&!s.running&&!s.pending}''')
  out=page.evaluate('''()=>{let e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.setOptions({transitionMs:0});e.time=0;e.render();return {png:e.canvas.toDataURL(),sources:e.appearance.layers.map(l=>({slot:l.slot,source:l.source,order:l.order}))}}''');im=Image.open(BytesIO(base64.b64decode(out['png'].split(',')[1]))).convert('RGBA');c=Image.new('RGBA',im.size,'#f7f4eb');c.alpha_composite(im);crop=Image.new('RGB',(345,370),'#f7f4eb');crop.paste(c.crop((300,0,645,360)).convert('RGB'),(0,10));ref=np.array(Image.open(repo/rec['reference']).convert('RGB'));err=np.abs(np.array(crop).astype(float)-ref);results.append({'head':rec['head'],'hair':rec['number'],'mean_abs_error':float(err.mean()),'head_core_mean_error':float(err[:235].mean()),'sources':out['sources']});
  if len(results)==1:
   crop.save(report/'animated-M01-H06.png');print('animated sizes',im.size,'error regions',float(err[:125].mean()),float(err[130:235,125:220].mean()),float(err[235:].mean()),flush=True)
  assert err[:235].mean()<1,results[-1]
 for color in ['blue','white']:
  page.evaluate('c=>setHairColor(c)',color);page.wait_for_function('''()=>{let s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll'));return s?.host.dataset.avatarCoreReady==='true'&&!s.running&&!s.pending}''');assert page.evaluate('''()=>avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine.appearance.layers.filter(l=>l.order===2).every(l=>!l.source.startsWith('data:'))''')
 page.set_viewport_size({'width':390,'height':844});page.evaluate('setHairColor("original");equipPaperDollItem("face","face-male-goth-pierced");equipPaperDollItem("hair","hair-m6-mullet")');page.wait_for_function('''()=>{let s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll'));return s?.host.dataset.avatarCoreReady==='true'&&!s.running&&!s.pending}''');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.locator('.wardrobe-stage').screenshot(path=str(report/'mobile-animated-male.png'))
 page.evaluate('equipPaperDollItem("weapon","gear-aks")');page.wait_for_function('''()=>{let s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll'));return s?.engine.pose==='rifle'&&!s.running}''');assert page.evaluate('''()=>{let e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.time=0;e.render();let p=e.canvas.toDataURL();e.advance(1000);return e.canvas.toDataURL()!==p}''')
 page.evaluate('setPaperDollView("patient")');page.wait_for_function('document.getElementById("wardrobe-paperdoll").dataset.avatarCoreBlocked==="clothing"');assert page.locator('#wardrobe-layer-hair').evaluate('(i)=>i.complete&&getComputedStyle(i).visibility==="visible"');page.locator('.wardrobe-stage').screenshot(path=str(report/'mobile-patient-male.png'))
 b.close()
s.shutdown();data={'animated_comparisons':results,'worst_mean_error':max(x['mean_abs_error'] for x in results),'worst_head_core_mean_error':max(x['head_core_mean_error'] for x in results),'uncolored_skin_edges':True,'mobile_bounds':True,'rifle_breathing':True,'patient_fallback':True,'page_errors':errors};(report/'animated-browser-checks.json').write_text(json.dumps(data,indent=2)+'\n');print({'animated_comparisons':48,'worst_error':data['worst_mean_error'],'page_errors':errors})
