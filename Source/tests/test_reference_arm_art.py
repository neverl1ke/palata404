from tests.avatar_revision_contract import assert_female_donor_revision
from tests.avatar_revision_contract import runtime_point
from tests.avatar_revision_contract import assert_rig_revision,assert_ownership_only,OWNERSHIP_PATHS
"""Independent source-point and live-Canvas checks for authorized reference arms."""
from pathlib import Path
import hashlib,json,subprocess,unittest
import numpy as np
from PIL import Image
import tests.test_avatar_core as core
ROOT=core.ROOT;CORE=core.CORE;OUT=ROOT/'review/male-reference-arm-art'
def image_at(art,key,x,y):
 a=np.array(Image.open(CORE/art[key]));b=art['mesh']['bounds'];return a[y-b[1],x-b[0]] if b[0]<=x<b[2] and b[1]<=y<b[3] else np.zeros(4,dtype='uint8')
def assert_reference_cold_pixels_have_known_provenance(case,art,path):
 """Approved ink is valid; every opaque cold pixel must be source/base/hidden reserve."""
 a=np.array(Image.open(CORE/path));b=art['mesh']['bounds'];rgb=a[:,:,:3].astype(int);cold=(a[:,:,3]>=240)&(rgb[:,:,0]-rgb[:,:,2]<=16)
 src=np.array(Image.open(ROOT/art['source']).convert('RGBA'));base=np.array(Image.open(ROOT/'base_male.png'));reference=np.zeros_like(a);x0,y0,x1,y1=b
 reference[:,:,:3]=src[y0-26:y1-26,x0-10:x1-10,:3]
 known=(np.max(np.abs(rgb-reference[:,:,:3].astype(int)),axis=2)<=2)|(np.max(np.abs(rgb-base[y0:y1,x0:x1,:3].astype(int)),axis=2)<=2)
 pose=Path(art['source']).stem;side='left' if 'left-' in path else 'right';reserve=np.array(Image.open(OUT/f'{pose}-{side}-hidden-wrist-mask.png'));known|=reserve[y0-26:y1-26,x0-10:x1-10]>0
 case.assertTrue(np.all(known[cold]),(path,'unexplained opaque cold pixel'));case.assertTrue(np.all(a[a[:,:,3]==0]==0),path)
class ReferenceArmSourceTests(unittest.TestCase):
 def test_all_prior_pngs_engine_female_and_game_files_remain_unchanged(self):
  supplied={'pistol':'05aed1b5e5fbac1ffc6b3fac14bc6b66d17d2d8594d7aa66726f054d6d031177','melee':'ed140cde2c2934638a2248688ae32b76c0951c556c70d5fb8ed6cfea7b83f9ce','rifle':'12d53547d1485b01ca27db1cd0861bc426351b7f173192eed32a034a8706f6f8'}
  for pose,digest in supplied.items():self.assertEqual(hashlib.sha256((OUT/'Sources'/f'{pose}.png').read_bytes()).hexdigest(),digest,'supplied reference must stay immutable')
  names=[line.split('\t')[1] for line in subprocess.check_output(['git','ls-tree','-r','dd61b2d','avatar-core/assets'],cwd=ROOT,text=True).splitlines()]
  names+=['base_male.png','base_female.png','avatar-core/rigs/female_rig.json','avatar-core/weapon-controller.mjs','avatar-core/math.mjs','avatar-core/skin.mjs','avatar-core/pose-art.mjs','avatar-core/weapons.json','paper-doll.js','paper-doll-data.js','script.js','wardrobe.js','index.html']
  for name in names:
   if name in OWNERSHIP_PATHS:assert_ownership_only(self,name,'dd61b2d')
   elif name=='avatar-core/rigs/female_rig.json':assert_female_donor_revision(self,json.loads(subprocess.check_output(['git','show','dd61b2d:'+name],cwd=ROOT)),json.loads((ROOT/name).read_text()))
   else:self.assertEqual((ROOT/name).read_bytes(),subprocess.check_output(['git','show','dd61b2d:'+name],cwd=ROOT),name)
 def test_reference_fingertips_are_present_and_keep_source_rgb(self):
  rig=json.loads((CORE/'rigs/male_rig.json').read_text())
  # These points are inside visible fingers/nails in supplied reference pixels,
  # selected independently of the authored masks. No regenerated hand etalon.
  for pose,side,points in [('rifle','right',[(480,614),(465,600),(410,630),(370,600)]),('rifle','left',[(660,680),(685,701)]),('pistol','right',[(202,300),(255,300)]),('melee','right',[(180,830),(230,846)])]:
   src=np.array(Image.open(OUT/'Sources'/f'{pose}.png').convert('RGBA'));art=rig['poseArt'][pose][side]
   for x,y in points:
    actual=image_at(art,'frontImage',x+10,y+26);self.assertGreaterEqual(int(actual[3]),240,(pose,side,x,y,actual.tolist()));self.assertLessEqual(int(np.abs(actual[:3].astype(int)-src[y,x,:3]).max()),1,(pose,side,x,y))
 def test_visible_weapon_pixels_are_not_baked_into_arm_modules(self):
  rig=json.loads((CORE/'rigs/male_rig.json').read_text())
  for pose,side,xy in [('rifle','right',(260,480)),('pistol','right',(218,333)),('melee','right',(219,855))]:
   x,y=xy;art=rig['poseArt'][pose][side]
   for key in ['image','frontImage']:
    pixel=image_at(art,key,x+10,y+26)
    if pixel[3]>=16:
     self.assertGreater(int(pixel[0])-int(pixel[2]),25,(pose,key,xy,'completed hidden palm must be skin, not weapon'));self.assertGreater(int(pixel[0]),70)
 def test_pose_registration_matches_explicit_reference_landmarks(self):
  r=json.loads((CORE/'rigs/male_rig.json').read_text());cfg=json.loads((CORE/'male-preview.json').read_text());expected={'rifle':{'right':{'elbow':[213,579],'wrist':[341,601],'grip':[390,644]},'left':{'elbow':[714,634],'wrist':[697,681],'grip':[675,708]}},'pistol':{'right':{'elbow':[214,549],'wrist':[221,397],'grip':[230,351]}},'melee':{'right':{'elbow':[242,574],'wrist':[195,807],'grip':[227,880]}}}
  for pose,sides in expected.items():
   for side,points in sides.items():
    for key,value in points.items():self.assertEqual(r['poseArt'][pose][side]['anchors'][key],value,(pose,side,key))
   prop=np.array(Image.open(CORE/cfg['weapons'][pose]['image']));self.assertEqual(prop.shape,(1672,941,4));self.assertTrue(np.all(prop[prop[:,:,3]==0]==0))
   for point in [cfg['weapons'][pose]['primary']]+([cfg['weapons'][pose]['support']] if cfg['weapons'][pose]['support'] else []):
    px,py=map(round,point);self.assertGreaterEqual(int(prop[py,px,3]),240)
   self.assertEqual(cfg['weapons'][pose]['size'],[941,1672]);self.assertEqual(cfg['weapons'][pose]['scale'],1);self.assertEqual(cfg['weapons'][pose]['primary'],sides['right']['grip']);self.assertEqual(r['poses'][pose]['angle'],0)
 def test_body_is_not_replaced_by_a_reference_and_new_assets_have_clean_hidden_rgb(self):
  rig=json.loads((CORE/'rigs/male_rig.json').read_text());self.assertEqual(rig['source'],'../base_male.png')
  for pose,sides in rig['poseArt'].items():
   for side,art in sides.items():
    b=art['mesh']['bounds'];self.assertGreater(b[0],130);self.assertLess(b[2],780);self.assertGreater(b[1],200);self.assertLess(b[3],960)
    for key in ['image','frontImage']:
     a=np.array(Image.open(CORE/art[key]));self.assertTrue(np.all(a[a[:,:,3]==0]==0),(pose,side,key));self.assertEqual(a.shape[:2],(b[3]-b[1],b[2]-b[0]))
 def test_cycle_and_unrelated_configuration_are_preserved(self):
  old=json.loads(subprocess.check_output(['git','show','dd61b2d:avatar-core/male-preview.json'],cwd=ROOT));new=json.loads((CORE/'male-preview.json').read_text())
  for key in ['breathingProfiles','chestDetail','transitionPolicy','surfaceOverrides']:self.assertEqual(old[key],new[key],key)
  for pose in ['melee','pistol','rifle']:
   for key in ['id','class','pose','test_resource','order']:self.assertEqual(old['weapons'][pose][key],new['weapons'][pose][key])
class ReferenceArmBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page
 def tearDown(self):self.c.tearDown()
 def test_all_new_contact_points_and_4000ms_cycles_close_without_hand_disconnect(self):
  self.p.evaluate('avatarLab.engine.setOptions({breathing:true,cycleMs:4000})')
  for pose in ['idle','rifle','pistol','melee']:
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);start=None
   for t in range(0,4001,250):
    self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);f=self.p.evaluate('avatarLab.engine.frame');self.assertLess(f['primaryError'],1e-6);self.assertLess(f['supportError'],1e-6)
    if t==0:start=self.c.image()
    if t==4000:self.assertTrue(np.array_equal(start,self.c.image()),pose)
 def test_actual_canvas_keeps_reference_fingertip_colors_and_separate_props(self):
  if self.p.evaluate('!!avatarLab.engine.posePreview.poseArtCompleteSurfaces'):
   from tests.avatar_revision_contract import assert_active_foundation_contacts
   for pose in ['rifle','pistol','melee']:
    self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);assert_active_foundation_contacts(self,self.p,'hand-color');assert_active_foundation_contacts(self,self.p,'material')
   return
  metrics=[]
  for pose,points in [('rifle',[(480,614),(465,600),(410,630),(660,680),(685,701)]),('pistol',[(202,300),(255,300)]),('melee',[(180,830),(230,846)])]:
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);actual=self.c.image();source=np.array(Image.open(OUT/'Sources'/f'{pose}.png').convert('RGBA'))
   for x,y in points:
    wx,wy=runtime_point(self.p,pose,x,y);delta=int(np.abs(actual[wy,wx,:3].astype(int)-source[y,x,:3]).max());self.assertLessEqual(delta,8,(pose,x,y,delta));metrics.append({'pose':pose,'source':[x,y],'render_rgb_max_error':delta})
  (OUT/'hand-pixel-raster-check.json').write_text(json.dumps(metrics,indent=2)+'\n')
 def test_unilateral_poses_keep_the_left_arm_and_idle_unchanged(self):
  self.p.evaluate('avatarLab.engine.time=0;avatarLab.engine.setPose("idle");avatarLab.engine.setOptions({view:"original"})');original=self.c.image();self.p.evaluate('avatarLab.engine.setOptions({view:"rig"})');actual=self.c.image()
  if self.p.evaluate('!!avatarLab.engine.posePreview.runtimeSource'):
   approved=np.array(Image.open(ROOT/'review/avatar-foundation-cleanup/Evidence/base-male-removed-alpha-mask.png'))>0;source=np.array(Image.open(ROOT/'base_male.png'));self.assertLessEqual(int(source[:,:,3][approved].max()),3);self.assertTrue(np.all(~np.any(actual!=original,axis=2)|approved))
  else:self.assertTrue(np.array_equal(original,actual))
  for pose in ['pistol','melee']:
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);f=self.p.evaluate('avatarLab.engine.frame.arms.left');rest=self.p.evaluate('avatarLab.engine.rig.arms.left')
   for key in ['shoulder','elbow','wrist','grip']:self.assertTrue(np.allclose(f[key],rest[key]))
if __name__=='__main__':unittest.main()
