"""Native/fractional/DPR seam, material, garment and opaque-cut browser proofs."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
import base64,functools,io,threading,json,itertools,hashlib
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';G=O/'Gallery';rows=[];errors=[];http=[];backgrounds=[];cuts=[];diagnostics=[]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start()
def image(p):return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGBA')
with sync_playwright() as pw:
 browser=pw.chromium.launch()
 for dpr in [1,2]:
  p=browser.new_page(viewport={'width':1440,'height':1800},device_scale_factor=dpr);p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:http.append([r.url,r.status]) if r.status>=400 else None);p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('avatarLab.engine.pause()')
  for width in [320,391.5,941]:
   p.evaluate('w=>{let e=avatarLab.engine;Object.assign(e.canvas.style,{width:w+"px",height:w*1672/941+"px",maxWidth:"none",maxHeight:"none",minWidth:"0",minHeight:"0"});e.setOptions({background:"transparent",breathing:true})}',width)
   for gender in ['male','female']:
    p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
    for pose in ['idle','melee','pistol','rifle']:
     p.evaluate('pose=>avatarLab.engine.setPose(pose)',pose)
     result=p.evaluate('''()=>{let e=avatarLab.engine,c=e.canvas,s=c.width/941,sy=c.height/1672;function sample(){let rows=[];for(let [name,x,y,w,h]of [['neck',430,292,80,8],['waist',390,757,160,7]]){let a=e.ctx.getImageData(Math.ceil(x*s),Math.ceil(y*sy),Math.floor(w*s),Math.floor(h*sy)).data,alphas=[];for(let i=3;i<a.length;i+=4)alphas.push(a[i]);rows.push({name,min:Math.min(...alphas)})}return rows}e.setOptions({view:'original'});let reference=sample();e.setOptions({view:'rig'});let samples=[];for(let time of [0,1000,2000,3000,4000]){e.time=time;e.render();samples.push({time,regions:sample(),primary:e.frame.primaryError,support:e.frame.supportError})}return {backing:[c.width,c.height],reference,samples}}''');rows.append({'dpr':dpr,'css_width':width,'gender':gender,'pose':pose,**result})
     assert result['backing'][0]==int(width*dpr+.5),(width,dpr,result['backing'])
     if width==391.5 and dpr==2 and pose=='idle':
      im=image(p);sc=im.width/941;sy=im.height/1672
      for name,box in [('neck',(390,270,560,330)),('waist',(360,725,580,800))]:im.crop(tuple(round(v*(sc if i%2==0 else sy)) for i,v in enumerate(box))).resize((680,240)).save(G/f'{gender}-{name}-fractional-dpr2.png')
   print('joins',dpr,width,flush=True)
  p.close()
 import sys
 if '--joins-only' in sys.argv:
  old=json.loads((O/'Evidence/browser-probes.json').read_text());old['joins']=rows;old['join_failures']=[r for r in rows if any(v['min']<r['reference'][i]['min'] for x in r['samples'] for i,v in enumerate(x['regions']))];old['exact_requested_css_widths']=True;(O/'Evidence/browser-probes.json').write_text(json.dumps(old,indent=2));assert not old['join_failures'];browser.close();s.shutdown();print('240 exact-width join samples verified',flush=True);raise SystemExit
 p=browser.new_page(viewport={'width':1440,'height':1800});p.on('pageerror',lambda e:errors.append(str(e)));p.goto(f'http://127.0.0.1:{s.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:"941px",height:"1672px",maxWidth:"none",maxHeight:"none",minWidth:"0",minHeight:"0"})}')
 for gender in ['male','female']:
  p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
  for pose in ['idle','melee','pistol','rifle']:
   p.evaluate('pose=>avatarLab.engine.setPose(pose)',pose)
   for visible in [True,False]:
    p.evaluate('v=>avatarLab.engine.setLayerVisible("weapon",v)',visible)
    for t in [0,1000,2000,3000,4000]:
     p.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.setOptions({background:"transparent"})}',t)
     # Direct source-over check against actual RGBA on the same renderer.
     checks=p.evaluate('''()=>{let e=avatarLab.engine,a=e.ctx.getImageData(0,0,941,1672).data,ids=[];for(let i=3;i<a.length;i+=4)if(a[i]>0&&a[i]<240)ids.push((i-3)/4);let stride=Math.max(1,Math.floor(ids.length/250)),probes=ids.filter((_,i)=>i%stride===0).slice(0,250).map(i=>[i,[...a.slice(i*4,i*4+4)]]),rows=[];for(let [color,rgb]of [['#fff',[255,255,255]],['#777',[119,119,119]],['#000',[0,0,0]],['#00ff00',[0,255,0]]]){e.setOptions({background:color});let b=e.ctx.getImageData(0,0,941,1672).data,max=0;for(let [i,c]of probes)for(let k=0;k<3;k++)max=Math.max(max,Math.abs(b[i*4+k]-(c[k]*c[3]/255+rgb[k]*(1-c[3]/255))));rows.push({color,max_error:max,samples:probes.length})}return rows}''');backgrounds.extend({'gender':gender,'pose':pose,'visible':visible,'time':t,**x} for x in checks)
     if t==0:
      ims=[]
      for color in ['#fff','#777','#000','#00ff00','transparent']:
       p.evaluate('c=>avatarLab.engine.setOptions({background:c})',color);im=image(p);im.save(G/f'{gender}-{pose}-{visible}-background-{color.replace("#","")}.webp',lossless=True,method=0);ims.append(im.resize((235,418)))
      sheet=Image.new('RGBA',(1175,442),'#777');d=ImageDraw.Draw(sheet)
      for i,(im,txt) in enumerate(zip(ims,['White','Gray','Black','Green','Transparent'])):sheet.alpha_composite(im,(235*i,24));d.text((235*i+3,4),txt,fill='white')
      sheet.save(G/f'{gender}-{pose}-{visible}-backgrounds.webp',lossless=True,method=0)
  p.evaluate('avatarLab.engine.setLayerVisible("weapon",true);avatarLab.engine.setOptions({background:"#f8f5ed"})')
  for a,b in itertools.permutations(['idle','melee','pistol','rifle'],2):
   p.evaluate('v=>{let e=avatarLab.engine;e.time=0;e.setPose(v[0]);e.setPose(v[1])}',[a,b]);frames=[];samples=[]
   for dt in [i*1000/60 for i in range(20)]+[320]:
    x=p.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.render();return {time:t,transition:e.transition,pose:e.pose,primary:e.frame.primaryError,support:e.frame.supportError,png:e.canvas.toDataURL().split(",")[1]}}',dt);im=Image.open(io.BytesIO(base64.b64decode(x.pop('png')))).convert('RGBA');x['pixel_sha256']=hashlib.sha256(im.tobytes()).hexdigest();samples.append(x);frames.append(im)
   frames[0].save(G/f'{gender}-cut-{a}-{b}.webp',save_all=True,append_images=frames[1:],duration=[17]*20+[100],lossless=True,method=0,loop=0);cuts.append({'gender':gender,'from':a,'to':b,'logical_step_ms':1000/60,'samples':samples})
  for kind in ['collar','waist-top','short-sleeve','long-sleeve','cuff','glove','trousers','shoes']:
   p.evaluate('k=>{document.getElementById("diagnostic-binding").value=k}',kind);p.evaluate('avatarLab.diagnosticBinding()');sheet=Image.new('RGB',(940,862),'#ddd');d=ImageDraw.Draw(sheet)
   for i,pose in enumerate(['idle','melee','pistol','rifle']):
    p.evaluate('pose=>{let e=avatarLab.engine;e.setPose(pose);e.time=1000;e.render()}',pose);im=image(p);sheet.paste(im.resize((235,418)),(i*235,24));d.text((i*235+3,4),pose,fill='black')
    for time in [0,1000,3000,4000]:
     metrics=p.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.render();return {primary:e.frame.primaryError,support:e.frame.supportError}}',time);diagnostics.append({'gender':gender,'kind':kind,'pose':pose,'time':time,**metrics})
   sheet=sheet.crop((0,0,940,442));sheet.save(G/f'{gender}-diagnostic-{kind}.webp',lossless=True,method=0)
  p.evaluate('()=>{document.getElementById("diagnostic-binding").value="none";return avatarLab.diagnosticBinding()}')
  for hue in [120,240]:
   sheet=Image.new('RGB',(940,442),'#ddd');d=ImageDraw.Draw(sheet)
   for i,pose in enumerate(['idle','melee','pistol','rifle']):p.evaluate('a=>{let e=avatarLab.engine;e.setPose(a[0]);e.setOptions({diagnosticSkinHue:a[1]})}',[pose,hue]);sheet.paste(image(p).resize((235,418)),(235*i,24));d.text((235*i+3,4),pose,fill='black')
   sheet.save(G/f'{gender}-skin-probe-{hue}.webp',lossless=True,method=0)
  p.evaluate('avatarLab.engine.setOptions({diagnosticSkinHue:0})')
 p.close();browser.close()
s.shutdown();failures=[r for r in rows if any(v['min']<r['reference'][i]['min'] for x in r['samples'] for i,v in enumerate(x['regions']))];proof={'joins':rows,'join_failures':failures,'direct_background_checks':backgrounds,'cuts':cuts,'diagnostic_cases':diagnostics,'js_errors':errors,'http_errors':http,'physical_device_tested':False,'browser':'Chromium only; Firefox/WebKit executables absent'};(O/'Evidence/browser-probes.json').write_text(json.dumps(proof,indent=2));print('joins:',len(rows)*5,'background checks:',len(backgrounds),'cut samples:',sum(len(c['samples']) for c in cuts),'diagnostic cases:',len(diagnostics),'join failures',len(failures));assert not errors and not http;assert all(x['max_error']<=2 for x in backgrounds)
