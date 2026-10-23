from tests.requested_source_contract import pre_integration_bytes
"""Independent acceptance criteria for female donor art, not golden screenshots."""
from pathlib import Path
import hashlib,io,json,subprocess,unittest
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
import tests.test_avatar_core as core
from tests.avatar_revision_contract import assert_female_donor_revision
R=core.ROOT;C=core.CORE;O=R/'review/female-donor-arm-pass'
class FemaleDonorSourceTests(unittest.TestCase):
 def test_sources_bases_game_and_legacy_assets_are_untouched(self):
  paths=['base_male.png','base_female.png','index.html','script.js','wardrobe.js','paper-doll.js','paper-doll-data.js']+subprocess.check_output(['git','ls-tree','-r','--name-only','77199cd','avatar-core/assets/female'],cwd=R,text=True).splitlines()
  for p in paths:self.assertEqual(pre_integration_bytes(p),subprocess.check_output(['git','show','77199cd:'+p],cwd=R),p)
  old=json.loads((O/'Baseline/female_rig.json').read_text());new=json.loads((C/'rigs/female_rig.json').read_text());assert_female_donor_revision(self,old,new)
 def test_each_donor_is_native_canvas_and_source_mapping_is_explicit(self):
  reg=json.loads((O/'registration.json').read_text());self.assertEqual(len(reg['records']),4)
  for row in reg['records']:
   path=O/'Sources'/(row['pose']+'.png');
   with Image.open(path) as im:self.assertEqual(im.size,(941,1672))
   self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row['source_sha256']);self.assertEqual(row['source_registration'],{'scale':1,'x':0,'y':0})
 def test_alpha_is_clean_and_all_arm_components_are_anatomically_connected(self):
  rig=json.loads((C/'rigs/female_rig.json').read_text())
  for pose,sides in rig['poseArt'].items():
   for side,art in sides.items():
    a=np.array(Image.open(C/art['image']));self.assertEqual(a.shape,(1672,941,4));self.assertTrue(np.all(a[a[:,:,3]==0]==0));labels,n=ndi.label(a[:,:,3]>=128);areas=np.bincount(labels.ravel());self.assertEqual(sum(areas[1:]>=8),1,(pose,side,'detached digit/wrist'))
    solid=a[:,:,3]>=128;distance=ndi.distance_transform_edt(~solid);weak=(a[:,:,3]>0)&(a[:,:,3]<=16);self.assertTrue(np.all(distance[weak]<=2),(pose,side,'remote faint debris'))
 def test_mesh_covers_every_active_pixel_and_foreground_is_skin_only(self):
  rig=json.loads((C/'rigs/female_rig.json').read_text())
  for pose,sides in rig['poseArt'].items():
   for side,art in sides.items():
    a=np.array(Image.open(C/art['image']));coverage=Image.new('L',(941,1672));d=ImageDraw.Draw(coverage)
    for tri in art['mesh']['triangles']:d.polygon([(art['mesh']['vertices'][i][0],art['mesh']['vertices'][i][1]) for i in tri],fill=255)
    self.assertTrue(np.all(np.array(coverage)[a[:,:,3]>0]>0),(pose,side));f=np.array(Image.open(C/art['frontImage']));skin=f[:,:,3]>240
    self.assertGreater(int(skin.sum()),100);self.assertGreater(float(np.mean(f[:,:,0][skin].astype(int)-f[:,:,2][skin].astype(int))),20)
  # Independently inspected source skin points. A prop may underlap them,
  # but must use weapon material rather than the donor's photographed skin.
  for pose,points in {'rifle':[(310,550),(480,579),(420,596),(400,600),(699,680)],'pistol':[(242,292)],'melee':[(231,834)]}.items():
   src=np.array(Image.open(O/'Sources'/f'{pose}.png').convert('RGBA'));prop=np.array(Image.open(C/f'assets/female/donor-art/{pose}-weapon.png'))
   for x,y in points:
    self.assertGreater(int(src[y,x,0])-int(src[y,x,2]),20,'fixture must be actual warm skin, not gray metal')
    if prop[y,x,3]>128:self.assertGreater(int(np.abs(prop[y,x,:3].astype(int)-src[y,x,:3].astype(int)).max()),12,(pose,x,y,'source skin/body paint baked into weapon'))
 def test_export_is_reproducible_including_rig_without_regeneration(self):
  paths=list((C/'assets/female/donor-art').glob('*.png'))+[C/'female-preview.json',C/'rigs/female_rig.json'];before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};subprocess.run(['python','tools/prepare-female-donor-arms.py'],cwd=R,check=True,capture_output=True);self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
class FemaleDonorBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page;self.c.gender('female')
 def tearDown(self):self.c.tearDown()
 def pose(self,p):self.p.evaluate('p=>{let e=avatarLab.engine;e.time=0;e.setPose(p);e.setOptions({breathing:false,background:"transparent"});e.render()}',p)
 def test_idle_is_exact_base_and_four_poses_are_distinct(self):
  self.pose('idle');a=self.c.image();self.p.evaluate('avatarLab.engine.setOptions({view:"original"})');base=self.c.image();self.p.evaluate('avatarLab.engine.setOptions({view:"rig"})');self.assertTrue(np.array_equal(a,base));hashes=set()
  for p in ['idle','melee','pistol','rifle']:self.pose(p);hashes.add(hashlib.sha256(self.c.image().tobytes()).hexdigest())
  self.assertEqual(len(hashes),4)
 def test_three_visible_props_exist_and_hide_preserves_anatomy_time(self):
  for p in ['melee','pistol','rifle']:
   self.pose(p);e=self.p.evaluate('avatarLab.engine.frame');a=self.c.image();self.p.evaluate('avatarLab.engine.setLayerVisible("weapon",false)');b=self.c.image();self.assertEqual(e,self.p.evaluate('avatarLab.engine.frame'));self.assertGreater(int(np.any(a!=b,axis=2).sum()),500,p);self.p.evaluate('avatarLab.engine.setLayerVisible("weapon",true)')
 def test_donor_joints_match_independent_measured_windows_and_one_hand_pistol(self):
  windows={'melee':{'right':[(306,367),(260,570),(205,787)]},'pistol':{'right':[(306,367),(222,526),(211,355)]},'rifle':{'right':[(306,367),(190,522),(350,544)],'left':[(639,368),(687,566),(687,626)]}}
  # The requested melee correction uses the independently measured base
  # joints, not the shorter archived donor. Keep the donor fixture above for
  # uncalibrated history and retain the same 0.01px contact tolerance.
  if self.p.evaluate('!!avatarLab.engine.posePreview.poseCalibration?.melee'):
   windows['melee']['right']=[(306,367),(278,584),(215,825)]
  for pose,sides in windows.items():
   self.pose(pose);f=self.p.evaluate('avatarLab.engine.frame');self.assertLess(f['primaryError'],1e-6);self.assertLess(f['supportError'],1e-6)
   for side,points in sides.items():
    for joint,expected in zip(['shoulder','elbow','wrist'],points):self.assertLess(float(np.linalg.norm(np.array(f['arms'][side][joint])-expected)),.01,(pose,side,joint))
  self.pose('pistol');self.p.evaluate('avatarLab.engine.setOptions({pistolSupport:true})');self.assertFalse(self.p.evaluate('avatarLab.engine.pistolSupportEnabled()'));a=self.p.evaluate('avatarLab.engine.frame.arms.left');r=self.p.evaluate('avatarLab.engine.rig.arms.left');self.assertTrue(np.allclose(a['wrist'],r['wrist']))
 def test_all_endpoint_cuts_have_no_crossfade_or_stale_previous_pose(self):
  for a in ['idle','melee','pistol','rifle']:
   for b in ['idle','melee','pistol','rifle']:
    self.pose(a);self.p.evaluate('p=>avatarLab.engine.setPose(p)',b);self.assertIsNone(self.p.evaluate('avatarLab.engine.transition'));self.assertEqual(self.p.evaluate('avatarLab.engine.pose'),b);self.assertLess(self.p.evaluate('avatarLab.engine.frame.primaryError'),1e-6)
 def test_background_composition_matches_the_transparent_subject(self):
  # Independent source-over equation. The former renderer fails by 7 at
  # male/melee [769,983]; no pose-preparation polygons or golden PNG involved.
  for gender in ['male','female']:
   self.c.gender(gender)
   for pose in ['idle','melee','pistol','rifle']:
    self.pose(pose)
    result=self.p.evaluate("""()=>{let e=avatarLab.engine,a=e.ctx.getImageData(0,0,941,1672).data,ids=[];for(let i=3;i<a.length;i+=4)if(a[i]>0&&a[i]<240)ids.push((i-3)/4);let step=Math.max(1,Math.floor(ids.length/200)),samples=ids.filter((_,i)=>i%step===0).slice(0,200).map(i=>[i,[...a.slice(i*4,i*4+4)]]),rows=[];for(let [background,rgb]of [['#fff',[255,255,255]],['#777',[119,119,119]],['#000',[0,0,0]],['#00ff00',[0,255,0]]]){e.setOptions({background});let b=e.ctx.getImageData(0,0,941,1672).data,max=0;for(let [i,c]of samples)for(let k=0;k<3;k++)max=Math.max(max,Math.abs(b[i*4+k]-(c[k]*c[3]/255+rgb[k]*(1-c[3]/255))));rows.push({background,max_error:max,samples:samples.length})}return rows}""")
    for row in result:self.assertGreater(row['samples'],50);self.assertLessEqual(row['max_error'],2,(gender,pose,row))
 def test_full_cycles_preserve_neck_contact_loop_and_stationary_head_feet(self):
  for pose in ['idle','melee','pistol','rifle']:
   self.pose(pose);self.p.evaluate('avatarLab.engine.setOptions({breathing:true})');start=self.c.image()
   for t in range(0,4001,250):
    self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);a=self.c.image();f=self.p.evaluate('avatarLab.engine.frame');self.assertLess(f['primaryError'],1e-6);self.assertLess(f['supportError'],1e-6);self.assertTrue(np.array_equal(a[:245],start[:245]));self.assertTrue(np.array_equal(a[1450:],start[1450:]));self.assertGreaterEqual(int(a[293:298,415:530,3].min()),235,(pose,t,'neck seam'))
   self.assertTrue(np.array_equal(start,a),pose)
if __name__=='__main__':unittest.main()
