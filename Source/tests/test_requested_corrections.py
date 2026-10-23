"""Independent source ownership, joint geometry and real inventory integration."""
import unittest,json,hashlib,base64,io
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from tests import test_avatar_core as support
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'avatar-core';OUT=ROOT/'review/avatar-requested-corrections/Evidence'
class RequestedSourceTests(unittest.TestCase):
 def test_approved_bases_faces_and_hair_are_byte_identical(self):
  for path,digest in json.loads((OUT/'protected-resources.json').read_text()).items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
 def test_internal_reserves_copy_exact_source_rgba_and_never_paint_anatomy(self):
  for gender in ['male','female']:
   r=json.loads((CORE/f'rigs/{gender}_rig.json').read_text());c=json.loads((CORE/f'{gender}-preview.json').read_text());src=np.array(Image.open(ROOT/f'base_{gender}.png'))
   for key,path in c['runtimeSurfaces'].items():
    if 'requested-corrections/' not in path:continue
    bounds=r['segments'][key]['bounds'] if key in r['segments'] else r['skinMeshes'][key.replace('ArmSkin','')]['bounds'];x,y,x1,y1=bounds;a=np.array(Image.open(CORE/path));m=a[:,:,3]>0
    self.assertTrue(np.array_equal(a[m],src[y:y1,x:x1][m]),(gender,key))
   if gender=='female':
    a=np.array(Image.open(CORE/c['runtimeSurfaces']['torso']));x,y,_,_=r['segments']['torso']['bounds']
    # Independently selected bra-edge pixels from the unchanged approved base.
    for px,py in [(345,455),(608,450),(603,472)]:self.assertTrue(np.array_equal(a[py-y,px-x],src[py,px]),(px,py))
 def test_original_weapon_candidates_never_invent_or_substitute_material(self):
  catalog=json.loads((CORE/'equipment-weapons.json').read_text())['items'];self.assertEqual({i['id'] for i in catalog},{'gear-aks','gear-pm','gear-knife'})
  records=json.loads((OUT/'original-weapons.json').read_text())
  for row in records:
   source=np.array(Image.open(ROOT/row['source']));a=np.array(Image.open(ROOT/row['output']));self.assertTrue(np.array_equal(a[a[:,:,3]>0],source[a[:,:,3]>0]));self.assertEqual(row['status'],'PARTIAL')
   if row['id']=='gear-pm':
    for x,y in [(243,262),(243,265),(247,275),(230,288)]:self.assertEqual(int(a[y,x,3]),0,'source finger remains inside pistol guard')
  for item in catalog:self.assertTrue(item['previewOnly']);self.assertEqual(item['artStatus'],'PARTIAL');self.assertEqual(set(item['attachmentByGender']),{'male','female'})
class RequestedBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):support.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):support.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):
  self.c=support.AvatarCoreBrowserTests('test_idle_render_matches_original_for_both_bases');self.c.setUp();self.p=self.c.page;self.c.full_canvas()
 def tearDown(self):self.c.tearDown()
 def test_idle_seams_remain_filled_inside_the_original_shoulder_silhouette(self):
  for g in ['male','female']:
   self.c.gender(g);source=np.array(Image.open(ROOT/f'base_{g}.png'));mask=ndi.binary_erosion(source[:,:,3]>=250,iterations=5);y,x=np.indices(mask.shape);mask&=(y>305)&(y<480)&(x>270)&(x<675)
   for t in [0,1000,2000,3000,4000]:
    self.p.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.setOptions({background:"transparent",breathing:true});e.setPose("idle")}',t)
    image=self.c.image();self.assertGreaterEqual(int(image[:,:,3][mask].min()),240,(g,t))
 def test_melee_has_base_bone_lengths_stable_elbows_and_closed_grip_cycle(self):
  rows=[]
  for g in ['male','female']:
   self.c.gender(g);self.p.evaluate('()=>{let e=avatarLab.engine;e.setOptions({breathing:true,background:"transparent"});e.setPose("melee")}');frames=self.p.evaluate('()=>{let e=avatarLab.engine;return Array.from({length:241},(_,i)=>{e.time=i*4000/240;return structuredClone(e.compute())})}')
   rest=self.p.evaluate('avatarLab.engine.rig.arms.right');elbows=np.array([f['arms']['right']['elbow'] for f in frames]);self.assertLess(float(np.linalg.norm(np.ptp(elbows,axis=0))),2)
   for f in frames:
    a=f['arms']['right'];self.assertAlmostEqual(np.linalg.norm(np.array(a['elbow'])-a['shoulder']),np.linalg.norm(np.array(rest['elbow'])-rest['shoulder']),places=6);self.assertAlmostEqual(np.linalg.norm(np.array(a['wrist'])-a['elbow']),np.linalg.norm(np.array(rest['wrist'])-rest['elbow']),places=6);self.assertLess(f['primaryError'],1e-6)
   if g=='male':self.assertGreater(frames[0]['arms']['right']['elbow'][0],235)
   else:self.assertLess(np.linalg.norm(np.array(frames[0]['arms']['right']['elbow'])-rest['elbow']),3)
   images=[]
   for t in [0,4000]:self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);images.append(self.c.image())
   self.assertTrue(np.array_equal(*images));rows.append({'gender':g,'frames':241,'elbow_span':np.ptp(elbows,axis=0).tolist(),'first_frame':frames[0]})
  (OUT/'knife-geometry-tests.json').write_text(json.dumps(rows,indent=2)+'\n')
 def test_catalog_switch_hide_and_gender_rebind_preserve_contact_and_anatomy(self):
  rows=[]
  for g in ['male','female']:
   self.c.gender(g)
   for ident,pose in [('gear-knife','melee'),('gear-pm','pistol'),('gear-aks','rifle')]:
    self.p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',ident);self.assertEqual(self.p.evaluate('avatarLab.engine.pose'),pose)
    for t in [0,1000,3000,4000]:
     self.p.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.setOptions({background:"transparent",breathing:true});e.setLayerVisible("weapon",true)}',t);frame=self.p.evaluate('avatarLab.engine.frame');before=self.c.image();self.assertLess(frame['primaryError'],1e-6);self.assertLess(frame['supportError'],1e-6)
     self.p.evaluate('avatarLab.engine.setLayerVisible("weapon",false)');after=self.c.image();self.assertEqual(self.p.evaluate('avatarLab.engine.pose'),pose)
     maskpng=self.p.evaluate('''()=>{const e=avatarLab.engine,c=document.createElement('canvas');c.width=941;c.height=1672;const x=c.getContext('2d');x.transform(...e.frame.weapon.matrix);x.drawImage(e.assets['weapon-'+e.pose],0,0);return c.toDataURL().split(',')[1]}''');mask=np.array(Image.open(io.BytesIO(base64.b64decode(maskpng))))[:,:,3]>0;self.assertTrue(np.array_equal(before[~mask],after[~mask]));rows.append({'gender':g,'item':ident,'time_ms':t,'primary_error':frame['primaryError'],'support_error':frame['supportError']})
   self.p.evaluate('avatarLab.engine.equipWeaponItem(null)');self.assertEqual(self.p.evaluate('avatarLab.engine.pose'),'idle');self.assertIsNone(self.p.evaluate('avatarLab.engine.selectedWeaponId'))
  self.p.evaluate('avatarLab.engine.equipWeaponItem("gear-pm")');self.p.evaluate('avatarLab.engine.setGender("male")');self.assertEqual(self.p.evaluate('avatarLab.engine.selectedWeaponId'),'gear-pm')
  with self.assertRaises(Exception):self.p.evaluate('avatarLab.engine.equipWeaponItem("missing-id")')
  self.assertEqual(self.p.evaluate('avatarLab.engine.selectedWeaponId'),'gear-pm');(OUT/'item-contact-tests.json').write_text(json.dumps(rows,indent=2)+'\n')
 def test_actual_game_inventory_both_loadouts_and_reload_use_existing_save_keys(self):
  p=self.context.new_page() if hasattr(self,'context') else self.c.context.new_page();p.route('https://**/*',lambda r:r.abort());p.goto(self.c.url+'index.html?avatarCore=1');p.wait_for_function('window.avatarCoreGamePreview');p.evaluate('()=>{setPaperDollView("combat");for(let key of Object.keys(paperDollState.combatLoadout))paperDollState.combatLoadout[key]=null;for(let name of ["Іржавий ніж","ПМ (Пістолет Макарова)","Штурмовий АКС-74У"])inventory.push({name,category:"weapon",count:1});equipPaperDollItem("weapon","gear-aks")}');p.wait_for_function('[...avatarCoreGamePreview.instances.values()].every(s=>s.engine?.selectedWeaponId==="gear-aks")')
  before=p.evaluate('JSON.parse(localStorage.getItem("palata404_paper_doll"))');self.assertEqual(before['combatLoadout']['weapon'],'gear-aks');p.reload();p.wait_for_function('window.avatarCoreGamePreview');p.wait_for_function('[...avatarCoreGamePreview.instances.values()].every(s=>s.engine?.selectedWeaponId==="gear-aks")');self.assertEqual(p.evaluate('paperDollState.combatLoadout.weapon'),'gear-aks')
  p.evaluate('setPaperDollView("patient")');self.assertEqual(p.evaluate('paperDollState.combatLoadout.weapon'),'gear-aks');self.assertEqual(p.evaluate('paperDollState.patientLoadout.weapon'),before['patientLoadout']['weapon']);p.close()
 def test_hidden_wardrobe_stops_raf_and_resumes_after_open(self):
  p=self.c.context.new_page();p.route('https://**/*',lambda r:r.abort());p.goto(self.c.url+'index.html?avatarCore=1');p.wait_for_function('window.avatarCoreGamePreview');p.evaluate('()=>{setPaperDollView("combat");for(const k of Object.keys(paperDollState.combatLoadout))paperDollState.combatLoadout[k]=null;renderPaperDoll()}');p.wait_for_function('avatarCoreGamePreview.instances.get(document.getElementById("wardrobe-paperdoll"))?.engine')
  p.wait_for_function('avatarCoreGamePreview.instances.get(document.getElementById("wardrobe-paperdoll")).engine.paused');p.evaluate('openCustomization()');p.wait_for_function('!avatarCoreGamePreview.instances.get(document.getElementById("wardrobe-paperdoll")).engine.paused');p.evaluate('closeCustomization()');p.wait_for_function('avatarCoreGamePreview.instances.get(document.getElementById("wardrobe-paperdoll")).engine.paused');self.assertIsNone(p.evaluate('avatarCoreGamePreview.instances.get(document.getElementById("wardrobe-paperdoll")).engine.raf'));p.close()
