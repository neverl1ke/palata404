"""Real runtime evidence against the exact returned c82fb9f/e1f8e86 package.
Original references and historical review evidence are read-only.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import base64,functools,hashlib,io,itertools,json,subprocess,tarfile,tempfile,threading
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage as ndi
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-contact-surface-pass';G=OUT/'Gallery';G.mkdir(parents=True,exist_ok=True)
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
def serve(root):
 s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
PANELS=[]
def panel(ims,labels,name):
 w=max(im.width for im in ims);h=max(im.height for im in ims);out=Image.new('RGB',(w*len(ims),h+30),'#e8e3d9');d=ImageDraw.Draw(out)
 for i,(im,label) in enumerate(zip(ims,labels)):out.paste(im,(i*w,30));d.text((i*w+5,6),label,font=FONT,fill='#192224')
 out.save(G/name,lossless=True);PANELS.append({'path':name,'labels':labels})
def sheet(ims,cols,w,h,name,labels):
 out=Image.new('RGB',(cols*w,((len(ims)+cols-1)//cols)*(h+25)),'#e8e3d9');d=ImageDraw.Draw(out)
 for i,im in enumerate(ims):x=i%cols*w;y=i//cols*(h+25);out.paste(im.resize((w,h)),(x,y+25));d.text((x+4,y+4),labels[i],font=FONT,fill='#192224')
 out.save(G/name,lossless=True)
# Fixed inspection windows follow anatomy, not the preparation masks.
BOXES={
 'rifle':{'left-forearm-wrist':(605,495,785,795),'left-contact-item':(620,635,790,805),'left-axilla':(565,390,690,575),'right-fingers-grip':(330,580,530,710),'stock-axilla':(255,370,410,565),'right-shoulder':(225,295,405,505),'both-arms':(125,290,815,825)},
 'pistol':{'handle-holes-thumb':(170,255,315,425),'palm-outline-gap':(220,310,345,465),'shoulder':(235,290,395,495),'elbow':(140,480,320,635),'whole-active-arm':(140,155,390,635)},
 'melee':{'contact-handle':(145,785,295,965),'axilla':(255,375,420,590),'shoulder':(225,295,395,505),'whole-active-arm':(135,290,425,970),'blade-thigh':(170,840,415,1090)}
}
CROPS={
 'idle':{'upper':(125,280,925,1060),'hands':(125,770,925,1060),'shoulders':(210,280,750,555),'full':(0,0,941,1672)},
 'rifle':{'upper':(125,280,820,830),'hands':(300,530,825,825),'shoulders':(210,280,750,575),'full':(0,0,941,1672)},
 'pistol':{'upper':(125,140,925,1060),'hands':(150,145,340,460),'free-hand':(640,750,925,1060),'shoulders':(210,280,750,565),'full':(0,0,941,1672)},
 'melee':{'upper':(125,280,925,1060),'hands':(130,755,365,1080),'free-hand':(640,750,925,1060),'shoulders':(210,280,750,575),'full':(0,0,941,1672)}
}

errors=[];http=[];metrics=[];switches=[];images={};masks={};free=[]
with tempfile.TemporaryDirectory() as td:
 before=Path(td);data=subprocess.check_output(['git','archive','c82fb9f','avatar-core','avatar-lab'],cwd=ROOT)
 with tarfile.open(fileobj=io.BytesIO(data)) as archive:archive.extractall(before,filter='data')
 for n in ['base_male.png','base_female.png','paper-doll-data.js','paper-doll.js','hair-color.js','assets','review']:(before/n).symlink_to(ROOT/n,target_is_directory=(ROOT/n).is_dir())
 servers=[serve(before),serve(ROOT)]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch();pages=[]
   def frame(p):return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGBA')
   for server in servers:
    p=browser.new_page(viewport={'width':1440,'height':1800});p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:http.append([r.url,r.status]) if r.status>=400 else None);p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('''()=>{let e=avatarLab.engine;e.pause();Object.assign(e.canvas.style,{width:'941px',height:'1672px',maxWidth:'none',maxHeight:'none',position:'fixed',left:0,top:0});e.time=0;e.setOptions({breathing:false,transitionMs:0,background:'#f8f5ed'});e.render()}''')
    if server is servers[0]:
     # Release the heavy baseline image cache before loading the new runtime.
     for pose in ['idle','rifle','pistol','melee']:
      p.evaluate('p=>avatarLab.engine.setPose(p)',pose);frame(p).save(G/f'before-{pose}.webp',lossless=True);p.evaluate('avatarLab.engine.setOptions({background:"transparent"})');frame(p).save(G/f'before-{pose}-transparent.webp',lossless=True);p.evaluate('avatarLab.engine.setOptions({background:"#f8f5ed"})')
     p.close();pages.append(None)
    else:pages.append(p)
   current=pages[1];storage=current.evaluate('JSON.stringify({...localStorage})')
   def frame(p):return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGBA')
   for pose in ['idle','rifle','pistol','melee']:
    pair=[];alphas=[]
    for p,label in zip(pages,['before','after']):
     if p is None:
      pair.append(Image.open(G/f'before-{pose}.webp').convert('RGB'));alphas.append(np.array(Image.open(G/f'before-{pose}-transparent.webp'))[:,:,3]);continue
     p.evaluate('p=>{let e=avatarLab.engine;e.time=0;e.setOptions({breathing:false,background:"#f8f5ed"});e.setPose(p)}',pose);im=frame(p);im.save(G/f'{label}-{pose}.webp',lossless=True);pair.append(im.convert('RGB'))
     p.evaluate('avatarLab.engine.setOptions({background:"transparent"})');alpha=frame(p);alpha.save(G/f'{label}-{pose}-transparent.webp',lossless=True);alphas.append(np.array(alpha)[:,:,3]);p.evaluate('avatarLab.engine.setOptions({background:"#f8f5ed"})')
    images[pose]=pair[1];masks[pose]=alphas[1]
    if pose!='idle':
     source=Image.open(ROOT/'review/male-reference-arm-art/Sources'/f'{pose}.png').convert('RGBA');bg=Image.new('RGBA',source.size,'#f8f5ed');bg.alpha_composite(source,(10,26));reference=bg.convert('RGB')
     panel([reference.resize((470,836)),pair[0].resize((470,836)),pair[1].resize((470,836))],['Референс · +10,+26','Було · c82fb9f / e1f8e86','Стало · маски й контури'],pose+'-comparison.webp')
     for zone,box in BOXES[pose].items():
      factor=2 if 'whole' in zone or 'forearm' in zone else 3
      panel([im.crop(box).resize(((box[2]-box[0])*factor,(box[3]-box[1])*factor)) for im in [reference,*pair]],['Референс · те саме вікно','Було · те саме вікно','Стало · те саме вікно'],f'{pose}-{zone}.webp')
     # Exposed contours in the real transparent Canvas; reference silhouette is
     # independently derived from source/background, never pipeline POLYS.
     src=np.array(source);subject=src[:,:,3]>128
     if Image.open(ROOT/'review/male-reference-arm-art/Sources'/f'{pose}.png').mode=='RGB':
      dark=src[:,:,:3].max(2)<25;seed=np.zeros(dark.shape,bool);seed[:,0]=dark[:,0];seed[:,-1]=dark[:,-1];seed[0]=dark[0];seed[-1]=dark[-1];subject&=~ndi.binary_propagation(seed,mask=dark)
     shifted=np.zeros_like(subject);shifted[26:,10:]=subject[:-26,:-10];se=shifted&~ndi.binary_erosion(shifted)
     overlays=[]
     for im,alpha in zip(pair,alphas):
      a=np.array(im).copy();edge=(alpha>=128)&~ndi.binary_erosion(alpha>=128);a[ndi.binary_dilation(se)]=[0,210,255];a[edge]=[255,0,180];overlays.append(Image.fromarray(a).crop((140,310,780,930)))
     panel(overlays,['Було: ціан=джерело, рожевий=рендер','Стало: той самий масштаб'],pose+'-contour-overlay.webp')
     for color in ['#fff','#777','#000','#00ff00']:
      current.evaluate('c=>avatarLab.engine.setOptions({background:c})',color);frame(current).crop((130,270,920,1060)).save(G/f'{pose}-background-{color[1:]}.webp',lossless=True)
    current.evaluate('avatarLab.engine.setOptions({breathing:true,cycleMs:4000,background:"#f8f5ed"})');frames=[];rows=[];full=[]
    for t in range(0,4000,125):
     current.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);im=frame(current);full.append(im.convert('RGB'));frames.append(im.resize((470,836)));f=current.evaluate('avatarLab.engine.frame');rows.append({'t':t,'primaryError':f['primaryError'],'supportError':f['supportError'],'arms':f['arms'],'weapon':f['weapon']});assert f['primaryError']<1e-6 and f['supportError']<1e-6
    frames[0].save(G/f'{pose}-breathing.webp',save_all=True,append_images=frames[1:],duration=125,loop=0,lossless=True)
    # All sampled frames, including both full arm contours and free hands.
    for half,box in CROPS[pose].items():
     w=235 if half=='full' else 264;h=round((box[3]-box[1])*w/(box[2]-box[0]));parts=[im.crop(box) for im in full];sheet(parts,8,w,h,f'{pose}-all-frames-{half}.webp',[f'{t} ms' for t in range(0,4000,125)])
     if half=='hands':parts[0].save(G/f'{pose}-contact-cycle.webp',save_all=True,append_images=parts[1:],duration=125,loop=0,lossless=True)
    current.evaluate('avatarLab.engine.time=4000;avatarLab.engine.render()');assert np.array_equal(np.array(frame(current).convert('RGB')),np.array(full[0]))
    metrics.append({'pose':pose,'cycleMs':4000,'frame_interval_ms':125,'samples':rows,'closed':True})
   panel([images[p].resize((470,836)) for p in ['idle','rifle','pistol','melee']],['Idle','Rifle','Pistol','Melee'],'four-current-poses.webp')
   # Free arm compared in the assembled runtime, not merely original file hashes.
   current.evaluate('avatarLab.engine.setOptions({breathing:false,background:"transparent"});avatarLab.engine.time=0;avatarLab.engine.setPose("idle")');idle=np.array(frame(current))
   for pose in ['pistol','melee']:
    current.evaluate('p=>avatarLab.engine.setPose(p)',pose);actual=np.array(frame(current));box=(660,400,905,1030);x0,y0,x1,y1=box;different=int(np.any(actual[y0:y1,x0:x1]!=idle[y0:y1,x0:x1],2).sum());skin=idle[y0:y1,x0:x1,3]>=240;region=actual[y0:y1,x0:x1];lost=int((region[:,:,3][skin]<240).sum());rgb_error=int(np.abs(region[:,:,:3].astype(int)-idle[y0:y1,x0:x1,:3].astype(int))[skin].max());free.append({'pose':pose,'box':box,'different_pixels':different,'lost_opaque_pixels':lost,'max_opaque_rgb_error':rgb_error,'note':'split mesh compositing changes alpha and rounds RGB; compare source skin coverage and paint, not byte identity'});assert lost==0 and rgb_error<=2
   # All twelve directed cuts, before/after single-frame endpoints, no crossfade.
   current.evaluate('avatarLab.engine.setOptions({breathing:true,transitionMs:320,background:"#f8f5ed"})');cutframes=[]
   for a,b in itertools.permutations(['idle','rifle','pistol','melee'],2):
    current.evaluate('a=>{let e=avatarLab.engine;e.time=1125;e.setPose(a)}',a);cutframes.append(frame(current).resize((470,836)));current.evaluate('b=>avatarLab.engine.setPose(b)',b);im=frame(current);cutframes.append(im.resize((470,836)));assert current.evaluate('avatarLab.engine.transition===null');current.evaluate('p=>{let e=avatarLab.engine;e.setPose("idle");e.setPose(p);e.render()}',b);assert np.array_equal(np.array(im),np.array(frame(current)));switches.append({'from':a,'to':b,'instant':True,'no_previous_pose_residue':True})
   cutframes[0].save(G/'all-twelve-cuts.webp',save_all=True,append_images=cutframes[1:],duration=450,loop=0,lossless=True);sheet([f.convert('RGB') for f in cutframes],6,188,334,'all-twelve-cuts-frames.webp',[x for s in switches for x in [s['from']+' > '+s['to']+' before',s['from']+' > '+s['to']+' after']])
   assert storage==current.evaluate('JSON.stringify({...localStorage})');assert not errors and not http
   (OUT/'browser-capture.json').write_text(json.dumps({'baseline':'c82fb9f','browser':browser.version,'entry':'avatar-lab/index.html','runtime_not_static_montage':True,'physical_device':False,'breathing':metrics,'switches':switches,'free_arm_raster':free,'js_errors':errors,'http_errors':http,'storage_unchanged':True,'panels':PANELS,'crop_windows':CROPS},ensure_ascii=False,indent=2)+'\n');browser.close()
 finally:
  for s in servers:s.shutdown();s.server_close()
print('Captured four complete 32-frame cycles, all 12 direct cuts, free-arm raster and matched A/B contour windows')
