"""Actual production-URL compatibility QA. No runtime routes or asset edits."""
from pathlib import Path
import hashlib,importlib.util,json
from playwright.sync_api import sync_playwright

R=Path('/workspace/palata404-shirt-release');D=R/'review/pajama-art-release-20261114';O=D/'independent-layers'
spec=importlib.util.spec_from_file_location('previous_qa',R/'review/pajama-waist-occlusion-20261114/independent-layers/browser_qa.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
q.D=D;q.O=O
def pins():
 manifest=json.loads((D/'release-manifest.json').read_text()); paths=list(manifest['runtime'])+[r['runtime']for r in manifest['artwork']]+[f'assets/wardrobe/clothing/patient/pajamas/{g}/thumb-{part}.webp'for g in ('male','female')for part in ('top','pants','footwear')]
 return{p:hashlib.sha256((R/p).read_bytes()).hexdigest()for p in paths}
q.PIN=pins();q.H.sources=pins
q.INFO=q.INFO.replace('return{animated:',"const ownedLayers=[...h.querySelectorAll(':scope>img')].filter(i=>/layer-(upper-body|footwear)-(front|rear)$/.test(i.id)).map(i=>({id:i.id,src:i.getAttribute('src'),shown:!i.classList.contains('hidden')&&getComputedStyle(i).visibility!=='hidden',z:getComputedStyle(i).zIndex,declaredZ:i.style.zIndex,natural:[i.naturalWidth,i.naturalHeight]}));return{ownedLayers,animated:")
raw_record=q.record
def record(page,*args,**kwargs):
 page.evaluate("()=>{for(const a of document.getAnimations()){a.pause();a.currentTime=0}}")
 if len(args)>1 and args[1]=='failed-shirt':page.wait_for_timeout(120)
 return raw_record(page,*args,**kwargs)
q.record=record

def live_page(browser,stage,fault=None):
 context=browser.new_context(viewport={'width':1672,'height':941});context.add_init_script(q.H.INIT)
 if q.seed:context.add_init_script("if(!sessionStorage.getItem('qa-art-seeded')){for(const[k,v]of Object.entries("+json.dumps(q.seed)+"))localStorage.setItem(k,v);sessionStorage.setItem('qa-art-seeded','1')}")
 held=[]
 if fault=='missing-mask':
  def abort_mask(route):held.append(route.request.url);route.abort('failed')
  context.route('**/keep-pants-*.png*',abort_mask)
 if fault=='failed-shirt':context.route('**/pajamas/*/top-*.png*',lambda route:route.abort('failed'))
 if fault=='delayed-mask':context.route('**/keep-pants-*.png*',lambda route:held.append(route))
 page=context.new_page();page.on('pageerror',lambda err:q.errors.append({'stage':stage,'fault':fault,'message':str(err)}));q.H.setup(page)
 if q.seed is None:
  q.seed=page.evaluate("()=>({...Object.fromEntries(Object.entries(localStorage)),palata404_stats:JSON.stringify(stats),palata404_inventory:JSON.stringify(inventory),palata404_equipped:JSON.stringify(equippedGear),palata404_paper_doll:JSON.stringify(paperDollState)})")
  page.evaluate("s=>{for(const[k,v]of Object.entries(s))localStorage.setItem(k,v);sessionStorage.setItem('qa-art-seeded','1')}",q.seed)
 # Control changes only the calibration rule in this private browser heap.
 if stage=='before':page.evaluate("PAPER_DOLL_ITEMS.find(i=>i.id==='patient-pajama-top').poseClothingOccludes=[]")
 page.add_style_tag(content='.avatar-clothed-breathing{animation:none!important;transform:none!important}')
 page.evaluate(q.FIXTURES);page.evaluate("openCustomization();setPaperDollView('combat')")
 return context,page,held
q.page_for=live_page

def grid(browser):
 context,page,_=live_page(browser,'after');out=[]
 for mode in ('patient','combat'):
  page.evaluate('mode=>setPaperDollView(mode)',mode)
  for g in ('male','female'):
   for pose,weapon in q.H.POSES:
    q.H.outfit(page,g,weapon,'pair')
    for host in ('wardrobe-paperdoll','character-paperdoll'):page.wait_for_function(q.H.READY,arg={'id':host,'g':g,'pose':pose,'parts':'footwear pants top'},timeout=60000)
    q.settled(page);info=page.evaluate(q.INFO)
    same=page.evaluate("()=>{const a=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).canvas,b=avatarCoreGamePreview.instances.get(document.getElementById('character-paperdoll')).canvas;return a.toDataURL()===b.toDataURL()}")
    out.append({'mode':mode,'gender':g,'pose':pose,'mainWardrobePixelExact':same,'pantsEquipped':info['pantsEquipped'],'parts':info['parts']})
    if not same:q.failures.append({'case':'main-wardrobe production','mode':mode,'gender':g,'pose':pose})
 page.set_viewport_size({'width':390,'height':844});q.H.outfit(page,'female','gear-aks','pair');page.wait_for_function(q.H.READY,arg={'g':'female','pose':'rifle','parts':'footwear pants top'},timeout=60000);q.settled(page)
 mobile=page.evaluate("()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,images:[...document.querySelectorAll('#wardrobe-paperdoll>img[src]')].every(i=>i.complete&&i.naturalWidth>0)})")
 if mobile['scrollWidth']>391 or not mobile['images']:q.failures.append({'case':'mobile production','detail':mobile})
 context.close();return{'states':out,'mobile':mobile}

def css_cycle(browser):
 context,page,_=live_page(browser,'after');page.evaluate("()=>{for(const s of [...document.querySelectorAll('style')])if(s.textContent.includes('.avatar-clothed-breathing{animation:none'))s.remove()}");out=[]
 for g in ('male','female'):
  q.base(page,g);page.evaluate("equipPaperDollItem('gloves','qa-waist-transparent-gloves')");q.settled(page);state0=q.snapshot(page)
  samples=page.evaluate("""async()=>{
   const h=document.getElementById('wardrobe-paperdoll'),p=document.getElementById('wardrobe-layer-pants'),s=document.getElementById('wardrobe-layer-upper-body-front'),a=h.getAnimations().find(a=>a.animationName==='clothed-avatar-breath');if(!a)throw Error('No CSS breathing');for(const b of document.getAnimations())b.pause();
   const hash=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');const rows=[];
   for(let k=0;k<17;k++){a.currentTime=k*3600/16;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const hb=h.getBoundingClientRect(),rect=i=>{const b=i.getBoundingClientRect();return[(b.left-hb.left)/hb.width,(b.top-hb.top)/hb.height,b.width/hb.width,b.height/hb.height]};const c=document.createElement('canvas');c.width=941;c.height=1672;c.getContext('2d').drawImage(p,0,0,941,1672);rows.push({phase:k,timeMs:a.currentTime,scale:getComputedStyle(h).scale,pantsBox:rect(p),shirtBox:rect(s),decodedPants:await hash(c.getContext('2d').getImageData(0,0,941,1672).data)});}return rows;
  }""")
  drift=max(abs(v-w)for r in samples for key in ('pantsBox','shirtBox')for v,w in zip(r[key],samples[0][key]));same=len({r['decodedPants']for r in samples})==1;stateExact=state0==q.snapshot(page);out.append({'gender':g,'samples':samples,'relativeDrift':drift,'bitmapStatic':same,'stateExact':stateExact})
  if drift>1e-7 or not same or not stateExact or len({r['scale']for r in samples})<2:q.failures.append({'case':'production CSS cycle','gender':g})
 context.close();return out

if __name__=='__main__':
 try:
  with sync_playwright()as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
   for stage in ('before','after'):q.run_main(browser,stage)
   q.run_fault(browser,'after','delayed-mask')
   for fault in ('missing-mask','failed-shirt'):
    for stage in ('before','after'):q.run_fault(browser,stage,fault)
   ui=grid(browser);css=css_cycle(browser);browser.close()
 except Exception as error:
  q.failures.append({'executionInterrupted':repr(error)});q.write();raise
 by={(r['stage'],r['gender'],r['case']):r for r in q.records}
 for (stage,g,name),record in list(by.items()):
  if stage!='after'or('before',g,name)not in by:continue
  before=by[('before',g,name)];record['controlStateExact']=record['state']==before['state']
  if not record['controlStateExact']:q.failures.append({'case':name,'gender':g,'stateDifference':[k for k in record['state']if record['state'][k]!=before['state'][k]]})
  inactive=name in ('shirt-off','pants-off','other-pants-fixture','other-top','eye-top-hidden','draft-removal-before-discard','applied-removal','reload-removal','missing-mask','failed-shirt')
  if inactive and record['screenshotRGBA']!=before['screenshotRGBA']:q.failures.append({'case':name,'gender':g,'inactivePixelsDiffer':True})
  if name=='legacy-pair':
   roles=record['info']['ownedLayers'];expected=['wardrobe-layer-upper-body-rear','wardrobe-layer-upper-body-front','wardrobe-layer-footwear-rear','wardrobe-layer-footwear-front']
   if not all(any(r['id']==name and r['shown']for r in roles)for name in expected):q.failures.append({'case':name,'gender':g,'missingOwnedDOMLayers':roles})
 if q.PIN!=pins():q.failures.append('Production source changed during QA')
 if q.errors:q.failures.append({'pageErrors':q.errors})
 q.write();result=json.loads((O/'BROWSER-QA.json').read_text());result.update(complete=True,status='PASS'if not q.failures else'FAIL',productionNoRuntimeRoutes=True,control='Same live production assets/code; only conditional rule disabled in private control heap.',uiGrid=ui,legacyCSS=css,sourceSha256=q.PIN);(O/'PRODUCTION-UI-QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':result['status'],'records':len(q.records),'uiGrid':len(ui['states']),'legacyPhases':sum(len(c['samples'])for c in css),'failures':q.failures},ensure_ascii=False,indent=2),flush=True)
