from tests.requested_source_contract import pre_integration_bytes
"""Independent asset preservation and real Canvas/browser regression of Avatar Core."""
import unittest,json,hashlib,functools,threading,io,base64,time,subprocess
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/avatar-core-grip-pass/test-evidence';R.mkdir(parents=True,exist_ok=True);CORE=ROOT/'avatar-core'
class AvatarCoreSourceTests(unittest.TestCase):
 def test_approved_runtime_and_all_original_assets_are_unchanged(self):
  for path,expected in json.loads((ROOT/'review/avatar-core-1/protected-originals.json').read_text())['git_blobs'].items():
   b=pre_integration_bytes(path);self.assertEqual(hashlib.sha1(('blob '+str(len(b))+'\0').encode()+b).hexdigest(),expected,path)
 def test_nine_disjoint_source_partitions_reconstruct_every_visible_pixel(self):
  for gender in ['male','female']:
   rig=json.loads((CORE/'rigs'/f'{gender}_rig.json').read_text());src=np.array(Image.open(ROOT/f'base_{gender}.png'));out=np.zeros_like(src);owners=np.zeros(src.shape[:2],dtype='uint8')
   self.assertEqual(len(rig['segments']),9)
   for name,s in rig['segments'].items():
    a=np.array(Image.open(CORE/s['image']));x,y,x1,y1=s['bounds'];v=a[:,:,3]>0;out[y:y1,x:x1][v]=a[v];owners[y:y1,x:x1]+=v
   self.assertTrue(np.array_equal(src[:,:,3],out[:,:,3]));self.assertTrue(np.array_equal(src[src[:,:,3]>0],out[src[:,:,3]>0]));self.assertLessEqual(int(owners.max()),1)
 def test_pivots_are_inside_actual_source_skin_and_assets_match_hashes(self):
  for gender in ['male','female']:
   rig=json.loads((CORE/'rigs'/f'{gender}_rig.json').read_text());a=np.array(Image.open(ROOT/f'base_{gender}.png'))
   self.assertEqual(hashlib.sha256((ROOT/f'base_{gender}.png').read_bytes()).hexdigest(),rig['source_sha256'])
   for arm in rig['arms'].values():
    for j in ['shoulder','elbow','wrist']:
     x,y=arm[j];self.assertGreaterEqual(int(a[y,x,3]),128,(gender,j))
   for s in rig['segments'].values():self.assertEqual(hashlib.sha256((CORE/s['image']).read_bytes()).hexdigest(),s['sha256'])

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class AvatarCoreBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch();cls.url=f'http://127.0.0.1:{cls.server.server_port}/'
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close();cls.thread.join()
 def setUp(self):
  self.context=self.browser.new_context(viewport={'width':1440,'height':1100});self.page=self.context.new_page();self.errors=[];self.missing=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)));self.page.on('response',lambda r:self.missing.append(r.url) if r.status>=400 else None);self.page.goto(self.url+'avatar-lab/');self.page.wait_for_function('window.avatarLab?.ready');self.page.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({breathing:false,transitionMs:0})')
 def tearDown(self):
  self.context.close();self.assertEqual(self.errors,[]);self.assertEqual(self.missing,[])
 def gender(self,g):self.page.evaluate('async g=>{await avatarLab.engine.setGender(g);await avatarLab.engine.setAppearance({layers:[]})}',g)
 def image(self):return np.array(Image.open(io.BytesIO(base64.b64decode(self.page.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))))
 def full_canvas(self):self.page.evaluate('Object.assign(avatarLab.engine.canvas.style,{width:"941px",maxWidth:"none",minWidth:"0",height:"1672px"});avatarLab.engine.render()')
 def test_idle_render_matches_original_for_both_bases(self):
  self.full_canvas()
  for g in ['male','female']:
   self.gender(g);self.page.evaluate('avatarLab.engine.setPose("idle");avatarLab.engine.setOptions({view:"original"})');original=self.image();self.page.evaluate('avatarLab.engine.setOptions({view:"rig"})');actual=self.image()
   if g=='male' and self.page.evaluate('!!avatarLab.engine.posePreview.runtimeSource'):
    # The protected base is still the original-view reference. Only the
    # explicitly reviewed <=16-alpha cleanup mask may differ in runtime.
    mask=np.array(Image.open(ROOT/'review/avatar-foundation-cleanup/Evidence/base-male-removed-alpha-mask.png'))>0
    changed=np.any(actual!=original,axis=2);self.assertTrue(np.all(~changed|mask),'runtime changed a pixel outside approved faint-matte cleanup')
   else:self.assertTrue(np.array_equal(original,actual),g)
 def test_all_eight_poses_preserve_face_feet_and_grips_across_breathing(self):
  self.full_canvas()
  for g in ['male','female']:
   self.gender(g);self.page.evaluate('avatarLab.engine.setPose("idle");avatarLab.engine.time=0;avatarLab.engine.render()');reference=self.image()
   for pose in ['idle','melee','pistol','rifle']:
    for t in [0,1000,2000,3000]:
     self.page.evaluate('a=>{const e=avatarLab.engine;e.setPose(a.pose);e.setOptions({breathing:true});e.time=a.t;e.transition=null;e.render()}',{'pose':pose,'t':t});s=self.page.evaluate('avatarLab.engine.snapshot()');im=self.image();self.assertTrue(np.array_equal(reference[1500:],im[1500:]),(g,pose,'feet'));self.assertTrue(np.array_equal(reference[20:245,385:560],im[20:245,385:560]),(g,pose,'face'));self.assertLess(s['frame']['primaryError'],1e-6);self.assertLess(s['frame']['supportError'],1e-6)
 def test_moving_joints_remain_opaque_and_main_body_connected(self):
  self.full_canvas();self.page.evaluate('avatarLab.engine.setOptions({background:"transparent"})')
  for g in ['male','female']:
   self.gender(g);self.page.evaluate('avatarLab.engine.setLayerVisible("weapon",false)')
   for pose in ['idle','melee','pistol','rifle']:
    self.page.evaluate('p=>avatarLab.engine.setPose(p)',pose);a=self.image()[:,:,3];f=self.page.evaluate('avatarLab.engine.snapshot().frame');labels,n=ndi.label(a>=128);areas=ndi.sum(a>=128,labels,range(1,n+1));large=[i+1 for i,v in enumerate(areas) if v>=100]
    if g=='male' and pose=='pistol' and 'reference-art/' in self.page.evaluate('avatarLab.engine.rig.poseArt.pistol.right.image') and not self.page.evaluate('avatarLab.engine.rig.poseArt.pistol.right.surfacePreparation'):
     # The reference fingertip shows through the guard. With the prop hidden,
     # require that sole island inside its exact reference box; no other debris.
     self.assertEqual(len(large),2)
     small=min(large,key=lambda i:int(np.count_nonzero(labels==i)));iy,ix=np.where(labels==small)
     self.assertGreaterEqual(int(ix.min()),229);self.assertLessEqual(int(ix.max()),253);self.assertGreaterEqual(int(iy.min()),259);self.assertLessEqual(int(iy.max()),285)
    else:self.assertEqual(len(large),1,(g,pose,'detached body component'))
    moving=['right','left'] if pose=='rifle' else ['right'] if pose=='pistol' else []
    for side in moving:
     x,y=self.page.evaluate('s=>avatarLab.engine.rig.arms[s].wrist',side);self.assertEqual(int(a[y-2:y+3,x-2:x+3].max()),0,(g,pose,side,'old wrist remains'))
    for side in ['right','left']:
     for joint in ['shoulder','elbow','wrist']:
      x,y=map(round,f['arms'][side][joint]);self.assertGreaterEqual(int(a[y-2:y+3,x-2:x+3].min()),128,(g,pose,side,joint))
 def test_authored_female_transitions_use_single_opaque_endpoint(self):
  self.gender('female');self.page.evaluate('avatarLab.engine.setPose("rifle");avatarLab.engine.step(130);avatarLab.engine.setPose("pistol")');self.assertIsNone(self.page.evaluate('avatarLab.engine.transition'));self.assertEqual(self.page.evaluate('avatarLab.engine.pose'),'pistol');self.assertLess(self.page.evaluate('avatarLab.engine.frame.primaryError'),1e-6)
 def test_male_pistol_is_one_handed_even_with_legacy_support_flag(self):
  for g in ['male','female']:
   self.gender(g);self.page.evaluate('avatarLab.engine.setOptions({pistolSupport:true});avatarLab.engine.setPose("pistol")');f=self.page.evaluate('avatarLab.engine.snapshot().frame');self.assertLess(f['primaryError'],1e-6);self.assertLess(f['supportError'],1e-6)
   if g=='male':
    rest=self.page.evaluate('avatarLab.engine.rig.arms.left');self.assertTrue(np.allclose(f['arms']['left']['wrist'],rest['wrist']));self.assertFalse(self.page.evaluate('avatarLab.engine.pistolSupportEnabled()'))
 def test_rapid_gender_switch_is_atomic_and_image_cache_bounded(self):
  self.page.evaluate('async()=>{const e=avatarLab.engine;await Promise.all([e.setGender("female"),e.setGender("male"),e.setGender("female")])}');s=self.page.evaluate('avatarLab.engine.snapshot()');self.assertEqual(s['rig'],'female_rig');self.assertLessEqual(s['cacheEntries'],96)
 def test_binding_api_sleeves_follow_each_rig_and_can_be_removed(self):
  for g in ['male','female']:
   self.page.locator(f'[data-gender="{g}"]').click();self.page.wait_for_function('g=>avatarLab.engine.gender===g&&document.getElementById("status").textContent.startsWith("Готово")',arg=g);self.page.locator('#sleeves').check();self.page.wait_for_function('avatarLab.engine.equipment.size===4&&Array.from(avatarLab.engine.equipment.values()).every(v=>v.bitmap&&v.skinned)');self.page.locator('[data-pose="rifle"]').click();self.assertEqual(len(self.page.evaluate('avatarLab.engine.snapshot().equipment')),4);self.page.locator('#sleeves').uncheck();self.page.wait_for_function('avatarLab.engine.equipment.size===0')
 def test_existing_saves_and_both_loadouts_remain_byte_unchanged(self):
  save={'schemaVersion':2,'selectedGender':'female','activeViewMode':'combat','appearance':{'face':'face-goth-septum','hair':'hair-f5-long-waves','hairColor':'black'},'patientLoadout':{'upperBody':'patient-tunic'},'combatLoadout':{'upperBody':None},'future':{'unknown':'preserve'}}
  self.page.evaluate('s=>{localStorage.setItem("palata404_paper_doll",JSON.stringify(s));localStorage.setItem("progress",JSON.stringify({exp:999,coins:123}))}',save);before=self.page.evaluate('JSON.stringify({...localStorage})');self.page.locator('#read-save').click();self.page.wait_for_function('window.avatarLab.saveSnapshot');self.assertEqual(self.page.locator('#face').input_value(),'face-goth-septum');self.assertEqual(self.page.locator('#hair').input_value(),'hair-f5-long-waves');self.assertEqual(self.page.locator('#color').input_value(),'black');self.page.reload();self.page.wait_for_function('window.avatarLab?.ready');self.assertEqual(before,self.page.evaluate('JSON.stringify({...localStorage})'))
 def test_mobile_and_high_dpi_layout(self):
  for w in [320,390,768]:
   self.page.set_viewport_size({'width':w,'height':844});self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'));self.page.locator('#step').scroll_into_view_if_needed();self.assertGreaterEqual(self.page.locator('#step').bounding_box()['height'],44)
  c=self.browser.new_context(viewport={'width':1440,'height':1100},device_scale_factor=2);p=c.new_page();p.goto(self.url+'avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('avatarLab.engine.pause();avatarLab.engine.render()');d=p.evaluate('avatarLab.engine.snapshot().display');self.assertEqual(d['dpr'],2);self.assertEqual(d['backingWidth'],round(p.locator('#avatar').bounding_box()['width']*2));c.close()
 def test_hidden_tab_stops_and_resume_does_not_catch_up_hidden_time(self):
  self.page.evaluate('avatarLab.engine.pause(false);Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))');t=self.page.evaluate('avatarLab.engine.time');self.page.wait_for_timeout(150);self.assertEqual(t,self.page.evaluate('avatarLab.engine.time'));self.assertIsNone(self.page.evaluate('avatarLab.engine.raf'));self.page.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>false});document.dispatchEvent(new Event("visibilitychange"))');self.page.wait_for_timeout(120);self.assertLess(self.page.evaluate('avatarLab.engine.time')-t,180);self.page.evaluate('avatarLab.engine.destroy()');self.assertIsNone(self.page.evaluate('avatarLab.engine.raf'))
 def test_canvas_appearance_matches_actual_game_renderer(self):
  self.full_canvas();production=self.context.new_page();production.route('https://**/*',lambda r:r.abort());production.goto(self.url+'index.html',wait_until='networkidle');production.wait_for_function('typeof renderPaperDollAt==="function"')
  records=[]
  for g,face,hair in [('male','face-alternative','hair-shoulder-length'),('female','face-young','hair-f5-long-waves')]:
   self.gender(g);self.page.evaluate('async v=>{const e=avatarLab.engine;e.setPose("idle");await e.setAppearance(await avatarCatalog.describe(v[0],v[1],v[2],"original"))}',[g,face,hair]);lab=self.image()
   production.evaluate('v=>{setGender(v[0]);setPaperDollView("combat");for(const k of Object.keys(paperDollState.combatLoadout))paperDollState.combatLoadout[k]=null;equipPaperDollItem("face",v[1]);equipPaperDollItem("hair",v[2]);setHairColor("original");document.getElementById("core-ground-truth")?.remove();const h=document.createElement("div");h.id="core-ground-truth";h.className="character-paperdoll";Object.assign(h.style,{position:"fixed",left:0,top:0,width:"941px",height:"1672px",background:"#d3cfc6",zIndex:2147483647});document.body.append(h);renderPaperDollAt(h,"core-test-")}',[g,face,hair]);production.wait_for_function('Array.from(document.querySelectorAll("#core-ground-truth img:not(.hidden)")).every(i=>i.complete&&i.naturalWidth>0)');actual=np.array(Image.open(io.BytesIO(production.locator('#core-ground-truth').screenshot())).convert('RGBA'));delta=np.abs(actual.astype(int)-lab.astype(int));crop=delta[140:220,440:505,:3];Image.fromarray(lab).save(R/f'{g}-appearance-lab.png');Image.fromarray(actual).save(R/f'{g}-appearance-game.png');Image.fromarray((delta[:,:,:3]*5).clip(0,255).astype('uint8')).save(R/f'{g}-appearance-diff.png');print('appearance comparison',g,float(delta.mean()),int(crop.max()),flush=True);records.append({'gender':g,'whole_image_mean_abs':float(delta.mean()),'face_center_max_abs':int(crop.max())});self.assertEqual(int(crop.max()),0);self.assertLess(float(delta.mean()),.1)
  (R/'appearance-comparison.json').write_text(json.dumps(records,indent=2)+'\n');production.close()
 def test_all_current_faces_four_poses_and_shared_hair_palette(self):
  self.full_canvas();records=[];colors=[];portraits={}
  for g,hair in [('male','hair-shoulder-length'),('female','hair-f5-long-waves')]:
   self.gender(g);faces=self.page.evaluate('g=>[{id:"native",name:"Базове обличчя"},...avatarCatalog.faces(g).map(i=>({id:i.id,name:i.name}))]',g);self.assertEqual(len(faces),9 if g=='male' else 17);portraits[g]=[]
   for face in faces:
    self.page.evaluate('async v=>{const e=avatarLab.engine;e.setPose("idle");await e.setAppearance(await avatarCatalog.describe(v.g,v.face,v.hair,"original"))}',{'g':g,'face':face['id'],'hair':hair});reference=self.image()[0:295,350:610]
    for pose in ['idle','melee','pistol','rifle']:
     self.page.evaluate('p=>avatarLab.engine.setPose(p)',pose);im=self.image();self.assertTrue(np.array_equal(reference,im[0:295,350:610]),(g,face['id'],pose));records.append({'gender':g,'face':face['id'],'hair':hair,'pose':pose})
    portraits[g].append((face['name'],Image.fromarray(im).crop((340,0,620,315)).convert('RGB')))
   for color in self.page.evaluate('avatarCatalog.colors.map(c=>c.id)'):
    self.page.evaluate('async v=>avatarLab.engine.setAppearance(await avatarCatalog.describe(v[0],"native",v[1],v[2]))',[g,hair,color]);self.assertLessEqual(self.page.evaluate('avatarLab.engine.snapshot().cacheEntries'),96);colors.append({'gender':g,'hair':hair,'color':color})
  from PIL import ImageDraw,ImageFont
  font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
  for g,rows in portraits.items():
   sheet=Image.new('RGB',(1120,350*((len(rows)+3)//4)),'#d3cfc6');d=ImageDraw.Draw(sheet)
   for n,(name,im) in enumerate(rows):x=n%4*280;y=n//4*350;d.text((x+6,y+7),name[:30],font=font,fill='#182322');sheet.paste(im,(x,y+32))
   sheet.save(R/f'{g}-all-current-faces.webp',lossless=True)
  (R/'cosmetic-check.json').write_text(json.dumps({'combinations':records,'palette':colors,'head_frames_identical_across_poses':True,'save_writes':False},ensure_ascii=False,indent=2)+'\n')
 def test_two_instances_render_different_genders_without_shared_pose_state(self):
  self.page.evaluate('''async()=>{const {AvatarEngine}=await import('../avatar-core/engine.mjs');const c=document.createElement('canvas');Object.assign(c.style,{width:'200px',height:'355px'});document.body.append(c);const second=await AvatarEngine.create(c,{gender:'female'});second.setOptions({transitionMs:0});second.setPose('rifle');window.avatarLab.second=second;}''')
  self.assertEqual(self.page.evaluate('avatarLab.engine.gender'),'male');self.assertEqual(self.page.evaluate('avatarLab.engine.pose'),'idle');self.assertEqual(self.page.evaluate('avatarLab.second.gender'),'female');self.assertEqual(self.page.evaluate('avatarLab.second.pose'),'rifle');self.page.evaluate('avatarLab.second.destroy()')
 def test_offline_lab_has_no_network_dependencies(self):
  offline=ROOT/'test-results/avatar-core-offline-current.html'
  subprocess.run(['python',str(ROOT/'tools/bundle-avatar-lab.py'),'--output',str(offline)],cwd=ROOT,check=True,capture_output=True)
  p=self.context.new_page();network=[];p.route('http**://**/*',lambda r:(network.append(r.request.url),r.abort()));p.goto(offline.as_uri());p.wait_for_function('window.avatarLab?.ready',timeout=45000);p.evaluate('avatarLab.engine.pause()');p.locator('[data-gender="female"]').click();p.wait_for_function('avatarLab.engine.gender==="female"&&document.getElementById("status").textContent.startsWith("Готово")');p.locator('[data-pose="rifle"]').click();self.assertEqual(network,[]);p.close()
if __name__=='__main__':unittest.main()
