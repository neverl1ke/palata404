"""Real-game before/after and contrast checks for female head normalization."""
import functools,io,json,subprocess,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'review/female-head-standard'
def run():
 m=json.loads((D/'manifest.json').read_text());out=D/'captures';out.mkdir(exist_ok=True)
 old=subprocess.check_output(['git','show',m['baseline']+':paper-doll-data.js'],cwd=ROOT,text=True)
 before=json.loads(subprocess.check_output(['node','-e','const vm=require("vm"),fs=require("fs");console.log(vm.runInNewContext(fs.readFileSync(0,"utf8")))'],input=old+';JSON.stringify(PAPER_DOLL_ITEMS)',text=True));(D/'baseline-catalog.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
 oldfaces={e['id']:e for e in before if e['slot']=='face'}
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();errors=[];http=[];shots=[];checks=[]
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch();p=b.new_page(viewport={'width':1440,'height':1000});net=p.context.new_cdp_session(p);net.send('Network.enable');net.send('Network.setBlockedURLs',{'urls':['https://*']});p.on('dialog',lambda d:d.accept());p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:http.append([r.url,r.status]) if r.status>=400 else None)
   p.goto(f'http://127.0.0.1:{server.server_port}/index.html',wait_until='networkidle');p.evaluate('openCustomization();setGender("female");setPaperDollView("combat");equipPaperDollItem("upperBody",null);globalThis.standardRenderer=paperDollRenderedFace;globalThis.standardResourceBackup=PAPER_DOLL_ITEMS.filter(i=>i.slot==="face").map(i=>({id:i.id,src:i.genderVariants?.female,mask:i.bodyMaskByGender?.female}))')
   def resources(old_mode):
    if old_mode:
     p.evaluate('a=>{for(const e of a){const i=PAPER_DOLL_ITEMS.find(i=>i.id===e.id);if(i&&e.genderVariants?.female){i.genderVariants.female=e.genderVariants.female;i.bodyMaskByGender.female=e.bodyMaskByGender.female}}paperDollRenderedFace=()=>selectedPaperDollItem("face");renderPaperDoll()}',list(oldfaces.values()))
    else:p.evaluate('()=>{for(const e of standardResourceBackup){const i=PAPER_DOLL_ITEMS.find(i=>i.id===e.id);if(e.src){i.genderVariants.female=e.src;i.bodyMaskByGender.female=e.mask}}paperDollRenderedFace=standardRenderer;renderPaperDoll()}')
   def board(bg='#f8f5ee'):
    p.evaluate('bg=>{document.getElementById("standard-board")?.remove();const c=document.createElement("div");c.id="standard-board";Object.assign(c.style,{position:"fixed",left:0,top:0,width:"400px",height:"400px",overflow:"hidden",background:bg,zIndex:2147483647});const h=document.createElement("div");h.className="character-paperdoll";Object.assign(h.style,{position:"absolute",width:"941px",height:"1672px",left:"-274px",top:"40px"});c.append(h);document.body.append(c);renderPaperDollAt(h,"standard-")}',bg)
    p.wait_for_function('''async()=>{for(const i of document.querySelectorAll('#standard-board img:not(.hidden)')){if(!i.complete||!i.naturalWidth)return false;if(i.paperHairRequest){const r=i.paperHairRequest,n=r.lastIndexOf('|');if(i.getAttribute('src')!==await coloredHairSource(r.slice(0,n),r.slice(n+1),i.paperHairColorReference))return false;}const mm=i.style.maskImage.match(/url\\(["']?(.*?)["']?\\)/);if(mm){const a=new Image();a.src=mm[1];await a.decode();}}return true;}''')
   def save(rel):
    path=out/(rel+'.webp');path.parent.mkdir(parents=True,exist_ok=True);im=Image.open(io.BytesIO(p.locator('#standard-board').screenshot())).convert('RGB');im.save(path,lossless=True,method=4);shots.append(str(path.relative_to(D)));return im
   font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
   for e in m['heads']:
    kind=e['kind'];p.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-none");setHairColor("original")}',e['id']);resources(True);board();a=save(kind+'/before');resources(False);board();after=save(kind+'/after')
    if e['reference']:assert a.tobytes()==after.tobytes(),'Reference changed in actual renderer'
    sheet=Image.new('RGB',(800,428),'#dedbd4');draw=ImageDraw.Draw(sheet)
    for i,(label,im) in enumerate([('ДО',a),('ПІСЛЯ',after)]):sheet.paste(im,(i*400,28));draw.text((i*400+8,3),label,font=font,fill='black')
    sheet.save(out/(kind+'-comparison.webp'),lossless=True)
    for bg,color in [('white','#ffffff'),('gray','#777777'),('black','#000000'),('green','#00ff00')]:board(color);save(kind+'/'+bg+'-bare')
    for hair in ['hair-classic-short','hair-textured-short']:
     for color in ['black','white']:
      p.evaluate('([h,c])=>{equipPaperDollItem("hair",h);setHairColor(c)}',[hair,color]);board();save(kind+'/'+hair+'-'+color)
    p.evaluate('equipPaperDollItem("hair","hair-shoulder-length");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")');board();save(kind+'/tunic')
    p.evaluate('document.getElementById("standard-board").remove();setPaperDollView("combat")');checks.append({'id':e['id'],'reference_identical':bool(e['reference']),'source':'production index.html with explicit before/after resource mapping'});print('Captured',kind,flush=True)
   p.evaluate('selectWardrobeCategory("appearance");selectWardrobeSlot("face")');p.screenshot(path=str(out/'desktop.png'),full_page=True)
   for w in [320,390,768]:
    p.set_viewport_size({'width':w,'height':844 if w>320 else 568});p.evaluate('openCustomization();selectWardrobeSlot("face")');card=p.locator('[data-wardrobe-card="face-female-new-almond-eyes"]');card.scroll_into_view_if_needed();card.click();button=p.locator('[data-wardrobe-action="face-female-new-almond-eyes"]');button.scroll_into_view_if_needed()
    if p.evaluate('paperDollState.appearance.face')!='face-female-new-almond-eyes':button.click()
    assert not p.evaluate('document.documentElement.scrollWidth>innerWidth');p.screenshot(path=str(out/('mobile-'+str(w)+'.png')),full_page=True)
   assert not errors and not http,(errors,http)
   (out/'result.json').write_text(json.dumps({'browser':'Chromium '+b.version,'checks':checks,'screenshots':shots,'mobile_emulation_widths':[320,390,768],'page_errors':errors,'http_errors':http,'before':'fd20bc3 approved original source/mask URLs, native render fallback disabled only in isolated browser context','after':'current normalized head derivatives; same actual production renderer and geometry'},ensure_ascii=False,indent=2)+'\n');b.close()
 finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':run()
