"""Independent invariants for the selective art merge, not artistic approval."""
from pathlib import Path
import json,hashlib,subprocess,unittest,io
import numpy as np
from PIL import Image
from tests import test_avatar_core as support
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';D=R/'review/avatar-selective-merge'
def pixels(p):return np.array(Image.open(p).convert('RGBA'))
class SelectiveSourceTests(unittest.TestCase):
 def test_engine_change_only_wires_the_existing_motion_profile(self):
  before=subprocess.check_output(['git','show','5532a93:avatar-core/engine.mjs'],cwd=R,text=True);after=(C/'engine.mjs').read_text();self.assertEqual(after.replace('relaxedMeleeAngles(arms.right, pose, b * this.options.weaponSwayPx / 2, this.posePreview?.meleeMotion);','relaxedMeleeAngles(arms.right, pose, b * this.options.weaponSwayPx / 2);'),before)
 def test_historical_runtime_is_identical_at_184e392_and_766a71e(self):
  self.assertEqual(subprocess.check_output(['git','diff','766a71e','184e392','--','avatar-core','avatar-lab'],cwd=R),b'')
 def test_existing_pngs_rigs_engine_catalog_and_saves_are_not_modified(self):
  paths=['base_male.png','base_female.png','avatar-core/rigs/male_rig.json','avatar-core/rigs/female_rig.json','avatar-core/equipment-weapons.json','avatar-core/game-preview.mjs','script.js','wardrobe.js','paper-doll.js','paper-doll-data.js']
  paths+=json.loads((R/'review/avatar-requested-corrections/Evidence/protected-resources.json').read_text()).keys()
  for p in set(paths):self.assertEqual((R/p).read_bytes(),subprocess.check_output(['git','show','5532a93:'+p],cwd=R),p)
 def test_lab_before_panel_uses_the_named_historical_rerender(self):
  script=(R/'avatar-lab/lab.mjs').read_text();self.assertIn("review/avatar-selective-merge/Gallery/184e392-",script);self.assertNotIn("review/avatar-foundation-cleanup/Gallery/before-",script)
  for g in ['male','female']:
   for p in ['idle','melee','pistol','rifle']:
    f=D/'Gallery'/f'184e392-{g}-{p}-0-{p!="idle"}.png';self.assertEqual(Image.open(f).size,(941,1672))
 def test_derived_alpha_and_hand_texels_are_exact_for_every_layer(self):
  for g in ['male','female']:
   rig=json.loads((C/f'rigs/{g}_rig.json').read_text());before=json.loads(subprocess.check_output(['git','show',f'5532a93:avatar-core/{g}-preview.json'],cwd=R));after=json.loads((C/f'{g}-preview.json').read_text())
   for pose,sides in rig['poseArt'].items():
    for side,art in sides.items():
     for field,key in [('poseArtCompleteSurfaces',pose+'-'+side),('poseArtSurfaces','art-'+pose+'-'+side),('poseArtSurfaces','art-front-'+pose+'-'+side)]:
      a=pixels(C/before[field][key]);b=pixels(C/after[field][key]);self.assertTrue(np.array_equal(a[:,:,3],b[:,:,3]),(g,key,'alpha'));y,x=np.indices(a.shape[:2]);bx,by=art['mesh']['bounds'][:2]
      if a.shape[:2]!=(1672,941):x+=bx;y+=by
      # Independently protect wrist and finger area; no colour edit may alter grip art.
      for joint in ['wrist','grip']:
       jx,jy=art['anchors'][joint];m=(x-jx)**2+(y-jy)**2<85**2;self.assertTrue(np.array_equal(a[m],b[m]),(g,key,joint))
 def test_only_surface_paths_change_in_preview_configs(self):
  for g in ['male','female']:
   a=json.loads(subprocess.check_output(['git','show',f'5532a93:avatar-core/{g}-preview.json'],cwd=R));b=json.loads((C/f'{g}-preview.json').read_text())
   for key in ['poseArtSurfaces','poseArtCompleteSurfaces']:a.pop(key);b.pop(key)
   a.pop('meleeMotion');self.assertEqual(b.pop('meleeMotion'),{'mode':'forward-wrist','upperDegrees':.008,'foreDegrees':.025,'handDegrees':.35,'cycleMs':4000})
   self.assertEqual(a,b)
class SelectiveBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):support.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):support.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):self.c=support.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page
 def tearDown(self):self.c.tearDown()
 def test_rgb_merge_never_changes_rendered_alpha_or_neutral_pose(self):
  for g in ['male','female']:
   self.c.gender(g);before=json.loads(subprocess.check_output(['git','show',f'5532a93:avatar-core/{g}-preview.json'],cwd=R));self.p.evaluate('async cfg=>{let e=avatarLab.engine;window.savedMotion=e.posePreview.meleeMotion;e.posePreview.meleeMotion=cfg.meleeMotion;window.finalArt={...e.assets};window.priorArt={...e.assets};for(let [id,path]of Object.entries(cfg.poseArtSurfaces))priorArt[id]=await e.image(path);for(let [id,path]of Object.entries(cfg.poseArtCompleteSurfaces))priorArt["art-complete-"+id]=await e.image(path)}',before)
   for pose in ['idle','melee','pistol','rifle']:
    self.p.evaluate('p=>{let e=avatarLab.engine;e.setPose(p);e.setOptions({background:"transparent",breathing:true})}',pose)
    for t in [0,1000,2000,3000]:
     self.p.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.assets=window.finalArt;e.render()}',t);a=self.c.image();self.p.evaluate('()=>{let e=avatarLab.engine;e.assets=window.priorArt;e.render()}');b=self.c.image();self.assertTrue(np.array_equal(a[:,:,3],b[:,:,3]),(g,pose,t));
     if pose=='idle':self.assertTrue(np.array_equal(a,b),(g,pose,t))
   self.p.evaluate('()=>{avatarLab.engine.assets=window.finalArt;avatarLab.engine.posePreview.meleeMotion=window.savedMotion}')
 def test_lab_pose_buttons_choose_original_items_by_default(self):
  self.assertEqual(self.p.locator('#equipment-weapon').input_value(),'none')
  for g in ['male','female']:
   self.c.gender(g)
   for pose,item in [('rifle','gear-aks'),('pistol','gear-pm'),('melee','gear-knife')]:
    self.p.locator(f'[data-pose="{pose}"]').click();self.p.wait_for_function('id=>avatarLab.engine.selectedWeaponId===id',arg=item);self.assertEqual(self.p.locator('#equipment-weapon').input_value(),item)
    self.assertIn('/184e392-',self.p.locator('#previous-arms').get_attribute('src'))
  self.p.locator('#equipment-weapon').select_option('gear-pm');self.p.wait_for_function('avatarLab.engine.pose==="pistol"');self.assertIn('-pistol-0-',self.p.locator('#previous-arms').get_attribute('src'));self.assertEqual(self.p.locator('[data-pose="pistol"]').get_attribute('aria-pressed'),'true')
 def test_actual_opaque_weapon_motion_is_at_most_two_pixels(self):
  from scipy.spatial import ConvexHull
  catalog=json.loads((C/'equipment-weapons.json').read_text())['items']
  for g in ['male','female']:
   self.c.gender(g)
   for item in catalog:
    im=pixels(C/item['image']);y,x=np.where(im[:,:,3]>0);points=np.c_[x,y];points=points[ConvexHull(points).vertices].tolist();self.p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',item['id'])
    samples=self.p.evaluate('''points=>{let e=avatarLab.engine;e.setOptions({breathing:true});let out=[];for(let t=0;t<=4000;t+=50){e.time=t;let m=e.compute().weapon.matrix;out.push(points.map(([x,y])=>[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]]))}return out}''',points);a=np.array(samples);center=(a.max(axis=0)+a.min(axis=0))/2;radius=float(np.linalg.norm(a-center,axis=2).max());self.assertLessEqual(radius,2,(g,item['id'],radius))
    if item['pose']=='melee':self.assertGreater(radius,.5,'knife must move with hand')
 def test_original_items_full_cycles_cuts_and_size_primary_pivot(self):
  rows=[]
  for g in ['male','female']:
   self.c.gender(g)
   for item,pose in [(None,'idle'),('gear-knife','melee'),('gear-pm','pistol'),('gear-aks','rifle')]:
    self.p.evaluate('id=>avatarLab.engine.equipWeaponItem(id)',item)
    row=self.p.evaluate('''()=>{let e=avatarLab.engine;e.setOptions({background:'transparent',breathing:true});let a=[];for(let t=0;t<=4000;t+=100){e.time=t;e.render();let f=e.frame;a.push({t,elbow:f.arms.right.elbow,primary:f.primaryError,support:f.supportError,hand:f.angles.right.hand,head:e.rig.segments.head.bounds})}return {samples:a,transition:e.transition,cycle:e.options.cycleMs}}''');self.assertIsNone(row['transition']);self.assertEqual(row['cycle'],4000);self.assertLess(max(x['primary'] for x in row['samples']),1e-6);self.assertLess(max(x['support'] for x in row['samples']),1e-6)
    if pose=='melee':
     elbow=np.array([x['elbow'] for x in row['samples']]);self.assertLess(float(np.ptp(elbow,axis=0).max()),1.3)
    rows.append({'gender':g,'pose':pose,**row})
    if item:
     errors=self.p.evaluate('''()=>{let e=avatarLab.engine,rows=[];for(let k of [.85,1,1.15]){e.setOptions({weaponPreviewScale:k});e.render();let f=e.frame,m=f.weapon.matrix,q=e.weapons[e.pose].primary,ox=m[0]*q[0]+m[2]*q[1]+m[4],oy=m[1]*q[0]+m[3]*q[1]+m[5];rows.push({scale:k,primaryError:Math.hypot(ox-f.arms.right.grip[0],oy-f.arms.right.grip[1]),supportGap:Math.abs(1-k)*Math.hypot(...e.weapons[e.pose].support?.map((v,i)=>v-q[i])||[0,0])*e.weapons[e.pose].scale})}e.setOptions({weaponPreviewScale:1});return rows}''');self.assertLess(max(x['primaryError'] for x in errors),1e-6);rows[-1]['size_tests']=errors
  (D/'Evidence/selective-motion-tests.json').write_text(json.dumps(rows,indent=2)+'\n')
