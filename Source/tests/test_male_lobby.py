from tests.avatar_revision_contract import assert_frozen_or_ownership,OWNERSHIP_PATHS
"""Independent geometric budgets for relaxed male poses; not an artistic approval."""
import json,subprocess,unittest
import numpy as np
from PIL import Image
import tests.test_avatar_core as core
ROOT=core.ROOT;OUT=ROOT/'review/avatar-core-lobby-rework'
class LobbySourceTests(unittest.TestCase):
 def test_originals_old_art_female_and_animation_math_are_preserved(self):
  names=['base_male.png','base_female.png','avatar-core/rigs/female_rig.json','avatar-core/math.mjs','avatar-core/skin.mjs','avatar-core/pose-art.mjs','avatar-core/weapon-controller.mjs']
  names += [r.split('\t')[1] for r in subprocess.check_output(['git','ls-tree','-r','469b973','avatar-core/assets'],cwd=ROOT,text=True).splitlines()]
  for name in names:assert_frozen_or_ownership(self,name,'469b973')
 def test_new_arm_pixels_are_warm_skin_not_the_gray_guide_or_full_avatar(self):
  r=json.loads((ROOT/'avatar-core/rigs/male_rig.json').read_text())
  for side,a in r['poseArt']['rifle'].items():
   self.assertLess(a['mesh']['bounds'][3],800)
   for path in [a['image'],a['frontImage']]:
    p=np.array(Image.open(ROOT/'avatar-core'/path));rgb=p[:,:,:3].astype(int);v=p[:,:,3]>0
    if 'reference-art/' in path:
     from tests.test_reference_arm_art import assert_reference_cold_pixels_have_known_provenance
     assert_reference_cold_pixels_have_known_provenance(self,a,path)
    else:self.assertTrue(np.all(rgb[:,:,0][v]-rgb[:,:,2][v]>16),path)
    self.assertTrue(np.all(p[~v]==0),path)
class LobbyBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.p=self.c.page
 def tearDown(self):self.c.tearDown()
 def test_relaxed_rifle_elbows_stock_contacts_and_face_clearance(self):
  self.p.evaluate('avatarLab.engine.setPose("rifle")');f=self.p.evaluate('avatarLab.engine.frame')
  for side in ['right','left']:
   a=f['arms'][side]
   if 'reference-art/' in self.p.evaluate('s=>avatarLab.engine.rig.poseArt.rifle[s].image',side):
    expected={'right':{'elbow':[213,579],'grip':[390,644]},'left':{'elbow':[714,634],'grip':[675,708]}}[side]
    for key,value in expected.items():self.assertTrue(np.allclose(a[key],value,atol=1e-6),(side,key))
   else:self.assertGreater(a['elbow'][1],580);self.assertGreater(a['grip'][1],650)
  self.assertLess(f['primaryError'],1e-6);self.assertLess(f['supportError'],1e-6)
  stock=self.p.evaluate('''()=>{const e=avatarLab.engine,m=e.frame.weapon.matrix,p=e.weapons.rifle.stock;return[m[0]*p[0]+m[2]*p[1]+m[4],m[1]*p[0]+m[3]*p[1]+m[5]]}''')
  if 'reference-art/' in self.p.evaluate('avatarLab.engine.weapons.rifle.image'):
   self.assertTrue(np.allclose(stock,[257,512]));shoulder=np.array(f['arms']['right']['shoulder']);elbow=np.array(f['arms']['right']['elbow']);v=elbow-shoulder;t=np.dot(np.array(stock)-shoulder,v)/np.dot(v,v);self.assertGreater(t,.5);self.assertLess(t,1);self.assertLess(np.linalg.norm(stock-(shoulder+t*v)),25)
  else:self.assertLess(np.linalg.norm(np.array(stock)-f['arms']['right']['elbow']),35);self.assertGreater(stock[1],580)
 def test_pistol_micro_sway_is_bounded_in_css_pixels_at_two_lab_scales(self):
  rows=[]
  for width in [320,470]:
   self.p.evaluate('w=>{const e=avatarLab.engine;e.canvas.style.minWidth="0";e.canvas.style.maxWidth="none";e.canvas.style.width=w+"px";e.canvas.style.height=w*1672/941+"px";e.setOptions({breathing:true,cycleMs:4000});e.setPose("pistol")}',width)
   points=[];chest=[]
   for t in range(0,4001,125):
    self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);f=self.p.evaluate('avatarLab.engine.frame');points.append(f['arms']['right']['grip']);chest.append(f['transforms']['torso']);self.assertLess(f['primaryError'],1e-6);self.assertIsNone(f['weapon']['support'])
   # Independent budget: full 4-second grip excursion <0.4 screen px.
   actual_width=self.p.evaluate('avatarLab.engine.canvas.getBoundingClientRect().width');excursion=float(np.linalg.norm(np.ptp(points,axis=0))*actual_width/941);self.assertLess(excursion,.4);self.assertGreater(float(np.ptp(np.array(chest)[:,0])),.004)
   rows.append({'requested_css_width':width,'actual_css_width':actual_width,'pistol_grip_peak_to_peak_css_px':excursion,'cycle_ms':4000,'samples':33})
  (OUT/'breathing-metrics.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':unittest.main()
