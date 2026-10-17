"""Actual index.html regression walkthrough, requests, layouts and repeatable render benchmark."""
import argparse,json,sys,hashlib,urllib.request
from urllib.parse import urlsplit,unquote
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tests.test_game as support
ROOT=support.ROOT

def run(output,url=None):
 output.mkdir(parents=True,exist_ok=True);support.GameTests.setUpClass()
 if url:support.GameTests.url=url.rstrip('/')+'/'
 case=support.GameTests();case.setUp();page=case.page;requests=set();http=[];transport_cache={};verified=set();external_hosts=set()
 if url:
  def transport(route):
   source=route.request.url;base=support.GameTests.url
   host=urlsplit(source).hostname;own=source.startswith(base)
   if not own and host not in {'fonts.googleapis.com','fonts.gstatic.com','telegram.org'}:route.abort();return
   if not own:external_hosts.add(host)
   if source not in transport_cache:
    with urllib.request.urlopen(source,timeout=60) as response:transport_cache[source]=(response.status,dict(response.headers),response.read())
   status,headers,data=transport_cache[source]
   if own:
    relative=unquote(urlsplit(source[len(base):]).path) or 'index.html';local=ROOT/relative
    if local.is_file():assert data==local.read_bytes(),f'Published bytes differ: {relative}';verified.add(relative)
   route.fulfill(status=status,headers=headers,body=data)
  case.context.route('https://**/*',transport)
 page.on('request',lambda r:requests.add(r.url.split(support.GameTests.url)[-1]) if r.url.startswith(support.GameTests.url) else None)
 page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
 try:
  case.load();startup=page.evaluate('''()=>({navigation:performance.getEntriesByType('navigation').map(n=>({domContentLoaded:n.domContentLoadedEventEnd,responseEnd:n.responseEnd,load:n.loadEventEnd})),resources:performance.getEntriesByType('resource').filter(e=>e.name.startsWith(location.origin)).map(e=>({url:e.name.split(location.origin)[1],bytes:e.transferSize,duration:e.duration})),heap:performance.memory?.usedJSHeapSize})''')
  page.evaluate('openCustomization();setGender("male");equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-shoulder-length");setHairColor("original");')
  page.wait_for_function('document.getElementById("wardrobe-layer-hair").complete && document.getElementById("wardrobe-layer-hair").naturalWidth>0')
  benchmark=page.evaluate('''()=>{const host=document.getElementById('wardrobe-paperdoll');const observer=new MutationObserver(()=>{});observer.observe(host,{subtree:true,attributes:true,attributeFilter:['src']});let calls=0;const original=smoothPaperDollCrown;smoothPaperDollCrown=(...args)=>{calls++;return original(...args)};const samples=[];for(let s=0;s<7;s++){const start=performance.now();for(let i=0;i<100;i++)renderPaperDoll();samples.push(performance.now()-start)}smoothPaperDollCrown=original;const srcMutations=observer.takeRecords().filter(r=>r.target.id==='wardrobe-layer-hair').length;observer.disconnect();return {iterations:700,batch:100,samples_ms:samples,median_ms:samples.sort((a,b)=>a-b)[3],front_src_mutations:srcMutations,crown_calculations:calls}}''')
  for width,height in [(320,568),(360,640),(390,844),(430,844),(768,844),(1440,1000)]:
   page.set_viewport_size({'width':width,'height':height})
   for name,call in [('wardrobe','openCustomization();selectWardrobeCategory("appearance");selectWardrobeSlot("hair")'),('inventory','openInventory()'),('staff','openStaffArchive("nurse")'),('dossier','openBossDossier("doctor")'),('gym','openGym()'),('medical','openProcedureRoom()'),('map','toggleMapModal(true);openFloorMap(10)'),('settings','openSettings()'),('friends','openFriends()'),('bank','openBank()'),('archive','openRaidArchive()')]:
    page.evaluate(call);page.wait_for_timeout(20)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),(width,name,'horizontal overflow')
    if name in ['wardrobe','inventory','staff','dossier'] and width in [320,390,768,1440]:page.screenshot(path=str(output/f'{name}-{width}.jpg'),type='jpeg',quality=88)
   page.evaluate('openCustomization()')
   for category,slots in page.evaluate('Object.entries(WARDROBE_CATEGORIES).map(([k,v])=>[k,v.slots])'):
    page.evaluate('c=>selectWardrobeCategory(c)',category)
    for slot in slots:
     page.evaluate('s=>selectWardrobeSlot(s)',slot)
     assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,category,slot)
  page.set_viewport_size({'width':1440,'height':1000});combos=0;samples=0
  for gender in ['male','female']:
   page.evaluate('g=>{setGender(g);selectWardrobeCategory("appearance");selectWardrobeSlot("hair")}',gender)
   styles=page.evaluate('wardrobeVisibleItems().map(i=>i.id)');assert len(styles)==(7 if gender=='male' else 8)
   for face in [None,'face-asian','face-young','face-exhausted','face-elder','face-alternative']:
    page.evaluate('f=>equipPaperDollItem("face",f)',face)
    for hair in styles:
     page.evaluate('h=>equipPaperDollItem("hair",h)',hair);combos+=1
     for color in ['original','black','white']:
      page.evaluate('c=>setHairColor(c)',color)
      page.wait_for_function('''async()=>{for(const i of document.getElementById('wardrobe-paperdoll').querySelectorAll('img:not(.hidden)')){const r=i.paperHairRequest;if(!r)continue;const n=r.lastIndexOf('|'),s=r.slice(0,n),c=r.slice(n+1);if(i.getAttribute('src')!==(c==='original'?s:await coloredHairSource(s,c,i.paperHairColorReference))||!i.complete||!i.naturalWidth)return false}return true}''')
      for bg in ['#fff','#555','#000','#00ff00']:
       page.locator('.wardrobe-stage').evaluate('(e,bg)=>{e.style.backgroundImage="none";e.style.backgroundColor=bg}',bg);samples+=1
     if hair=='hair-shoulder-length' and face=='face-alternative':page.screenshot(path=str(output/f'{gender}-white.jpg'),type='jpeg',quality=90)
  page.evaluate('setPaperDollView("combat");equipPaperDollItem("weapon","gear-pm");setPaperDollView("patient");equipPaperDollItem("upperBody",null)')
  appearance=page.evaluate('JSON.stringify(paperDollState)');page.reload(wait_until='networkidle');assert page.evaluate('JSON.stringify(paperDollState)')==appearance
  # Real victory finalization + duplicate guard, archive opening and reload.
  before=page.evaluate('stats.silver');page.evaluate('startBossFight("nurse")')
  hp=page.evaluate('bossCurrentHp');damage=page.evaluate('stats.damage')
  page.locator('#battle-arena-screen').click(position={'x':500,'y':300})
  assert page.evaluate('bossCurrentHp')==hp-damage
  page.locator('#battle-arena-screen').click(position={'x':500,'y':300})
  assert page.evaluate('bossCurrentHp')==hp-damage,'Attack cooldown bypass'
  page.wait_for_timeout(600);assert page.evaluate('stats.hp')<page.evaluate('stats.maxHp')
  page.screenshot(path=str(output/'battle-1440.jpg'),type='jpeg',quality=88)
  page.evaluate('bossCurrentHp=0;handleVictory();handleVictory()');result=page.evaluate('lastBattleResult');assert page.evaluate('stats.silver')==before+result['payout']['silver']
  silver=page.evaluate('stats.silver');page.evaluate('openLastBattleResult();openDetailedBattleReport();openRaidArchive();saveGameProgress()');page.reload(wait_until='networkidle');assert page.evaluate('stats.silver')==silver;assert page.evaluate('readRaidArchive().length')==1
  assert combos==90 and samples==1080 and not case.errors and not http
  pngs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('base_*.png')}
  result={'published_url':url,'external_hosts':sorted(external_hosts),'published_files_verified':sorted(verified),'transport':'Certificate-verified actual HTTPS bytes, no local substitution' if url else 'Local isolated HTTP server','startup':startup,'render_benchmark':benchmark,'combinations':combos,'color_background_samples':samples,'widths':[320,360,390,430,768,1440],'screens':11,'wardrobe_all_categories':True,'reload':True,'reward_exactly_once':True,'actual_attack_and_counter':True,'cooldown':True,'victory_finalization':'Controlled zero-HP transition after real attack/counter','http_errors':http,'js_errors':case.errors,'requested_paths':sorted(requests),'base_png_hashes':pngs,'external_services':'Published Google Fonts and Telegram SDK allowed' if url else 'Blocked for reproducible local tests; no physical phone'}
  (output/'browser.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['render_benchmark','combinations','color_background_samples','http_errors','js_errors']}))
 finally:case.tearDown();support.GameTests.tearDownClass()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--url');args=parser.parse_args();run(args.output,args.url)
