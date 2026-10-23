from tests.requested_source_contract import pre_integration_bytes
from tests.avatar_revision_contract import assert_female_donor_revision
"""Weapon-independent anatomy: strict behavior/coverage regression."""
import hashlib,io,json,subprocess,unittest
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import tests.test_avatar_core as core
ROOT=core.ROOT;CORE=core.CORE
class IndependentSurfaceSourceTests(unittest.TestCase):
 def test_originals_and_all_female_resources_are_unchanged(self):
  paths=['base_male.png','base_female.png','avatar-core/rigs/female_rig.json','index.html','wardrobe.js','paper-doll.js']
  paths+=subprocess.check_output(['git','ls-tree','-r','--name-only','184e392','avatar-core/assets/female'],cwd=ROOT,text=True).splitlines()
  for path in paths:
   if path=='avatar-core/rigs/female_rig.json':assert_female_donor_revision(self,json.loads(subprocess.check_output(['git','show','184e392:'+path],cwd=ROOT)),json.loads((ROOT/path).read_text()))
   else:self.assertEqual(pre_integration_bytes(path),subprocess.check_output(['git','show','184e392:'+path],cwd=ROOT),path)
 def test_thigh_pixels_have_exactly_one_owner_and_are_not_in_the_arm(self):
  r=json.loads((CORE/'rigs/male_rig.json').read_text());out=np.zeros((1672,941,4),np.uint8);owners=np.zeros((1672,941),np.uint8)
  for seg in r['segments'].values():
   x,y,x1,y1=seg['bounds'];a=np.array(Image.open(CORE/seg['image']));v=a[:,:,3]>0;out[y:y1,x:x1][v]=a[v];owners[y:y1,x:x1]+=v
  base=np.array(Image.open(ROOT/'base_male.png'));base[base[:,:,3]==0]=0;self.assertTrue(np.array_equal(out,base));self.assertEqual(int(owners.max()),1)
  x,y,x1,y1=r['skinMeshes']['left']['bounds'];a=np.array(Image.open(CORE/'assets/male/leftArmSkin.png'));self.assertEqual(int(a[840-y:1040-y,660-x:680-x,3].max()),0)
 def test_melee_bones_use_full_base_lengths_without_changing_rest_skeleton(self):
  r=json.loads((CORE/'rigs/male_rig.json').read_text());old=json.loads(subprocess.check_output(['git','show','184e392:avatar-core/rigs/male_rig.json'],cwd=ROOT));self.assertEqual(r['arms'],old['arms']);self.assertEqual(r['anatomyProjection']['melee']['right'],[1,1]);self.assertEqual(r['poses']['melee']['right'],[241,906]);self.assertLess(old['anatomyProjection']['melee']['right'][0],.85)
 def test_local_repaint_process_is_deterministic(self):
  paths=[p for p in (CORE/'assets/male').rglob('*.png')]+[CORE/'rigs/male_rig.json'];digest=lambda:[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths];before=digest();subprocess.run(['python','tools/prepare-independent-anatomy.py'],cwd=ROOT,check=True,capture_output=True);self.assertEqual(before,digest())
 def test_new_surfaces_have_mesh_coverage_and_clean_transparent_rgb(self):
  from PIL import ImageDraw
  r=json.loads((CORE/'rigs/male_rig.json').read_text())
  for pose,sides in r['poseArt'].items():
   for side,art in sides.items():
    b=art['mesh']['bounds'];a=np.array(Image.open(CORE/art['image']));coverage=Image.new('L',(b[2]-b[0],b[3]-b[1]));d=ImageDraw.Draw(coverage)
    for t in art['mesh']['triangles']:d.polygon([(art['mesh']['vertices'][i][0]-b[0],art['mesh']['vertices'][i][1]-b[1]) for i in t],fill=255)
    self.assertTrue(np.all(np.array(coverage)[a[:,:,3]>0]>0),(pose,side));self.assertTrue(np.all(a[a[:,:,3]==0]==0))
class IndependentSurfaceBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page
 def tearDown(self):self.c.tearDown()
 def test_hide_weapon_preserves_all_pose_matrices_time_and_hand_passes(self):
  for gender in ['male','female']:
   self.c.gender(gender)
   for pose in ['idle','melee','pistol','rifle']:
    self.p.evaluate('p=>{let e=avatarLab.engine;e.setPose(p);e.time=1000;e.setOptions({breathing:true});e.render()}',pose);before=self.p.evaluate('avatarLab.engine.snapshot()');self.p.evaluate("avatarLab.engine.setLayerVisible('weapon',false)");after=self.p.evaluate('avatarLab.engine.snapshot()');self.assertEqual(before['frame'],after['frame']);self.assertEqual(before['pose'],after['pose']);self.assertEqual(before['time'],after['time']);self.p.evaluate("avatarLab.engine.setLayerVisible('weapon',true)")
 def test_preview_sizes_do_not_change_pose_or_attachment_solution(self):
  for pose in ['melee','pistol','rifle']:
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);before=self.p.evaluate('avatarLab.engine.frame')
   for scale in [.85,1,1.15]:self.p.evaluate('s=>avatarLab.engine.setOptions({weaponPreviewScale:s})',scale);self.assertEqual(before,self.p.evaluate('avatarLab.engine.frame'))
  self.assertTrue(self.p.evaluate('()=>{try{avatarLab.engine.setOptions({weaponPreviewScale:2})}catch(e){return e instanceof RangeError}return false}'))
 def test_no_stationary_neck_gap_through_full_breath_cycle(self):
  self.p.evaluate("avatarLab.engine.setOptions({background:'transparent',breathing:true});avatarLab.engine.setPose('rifle')")
  for t in range(0,4000,250):
   self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);a=self.c.image();self.assertGreaterEqual(int(a[293:298,405:540,3].min()),235,('neck gap',t))
 def test_melee_length_matches_both_original_bone_lengths_in_runtime(self):
  self.p.evaluate("avatarLab.engine.setPose('melee')");f=self.p.evaluate('avatarLab.engine.frame');r=self.p.evaluate('avatarLab.engine.rig');a=f['arms']['right'];b=r['arms']['right']
  for x,y in [('shoulder','elbow'),('elbow','wrist')]:self.assertAlmostEqual(float(np.linalg.norm(np.array(a[x])-a[y])),float(np.linalg.norm(np.array(b[x])-b[y])),places=5)
  self.assertLess(f['primaryError'],1e-6)
 def test_weaponless_pistol_has_no_detached_fingertip(self):
  self.p.evaluate("avatarLab.engine.setOptions({background:'transparent'});avatarLab.engine.setPose('pistol');avatarLab.engine.setLayerVisible('weapon',false)");a=self.c.image();labels,n=ndi.label(a[:,:,3]>=128);areas=np.bincount(labels.ravel());self.assertEqual(sum(areas[1:]>=16),1)
 def test_thigh_edge_does_not_follow_isolated_arm_during_breathing(self):
  self.p.evaluate("avatarLab.engine.setOptions({background:'transparent',breathing:true});['head','torso','lower','rightUpper','rightFore','rightHand','weapon'].forEach(k=>avatarLab.engine.setLayerVisible(k,false))")
  for pose in ['idle','melee']:
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose)
   for t in [0,1000,3000]:
    self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);a=self.c.image();self.assertEqual(int(a[860:1029,660:680,3].max()),0,(pose,t,'thigh stripe still moves with arm'))
 def test_ui_visibility_control_keeps_selected_pose(self):
  self.p.locator('[data-pose="rifle"]').click();self.p.locator('#show-weapon').uncheck();self.assertEqual(self.p.evaluate('avatarLab.engine.pose'),'rifle');self.assertFalse(self.p.evaluate("avatarLab.engine.visible.get('weapon')"));self.p.locator('#weapon-preview-scale').select_option('0.85');self.assertEqual(self.p.evaluate('avatarLab.engine.options.weaponPreviewScale'),.85)
if __name__=='__main__':unittest.main()
