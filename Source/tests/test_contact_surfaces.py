from tests.avatar_revision_contract import assert_active_foundation_contacts
from tests.avatar_revision_contract import assert_foundation_preview_revision
from tests.avatar_revision_contract import assert_female_donor_revision
from tests.avatar_revision_contract import runtime_point
from tests.avatar_revision_contract import assert_rig_revision,assert_ownership_only,OWNERSHIP_PATHS
"""Independent regressions of visible solid reference surfaces and real gaps.
Literal probes were inspected in the supplied source, not sampled from new PNGs.
"""
import io,json,subprocess,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import tests.test_avatar_core as core
ROOT=core.ROOT;CORE=core.CORE;OUT=ROOT/'review/male-contact-surface-pass'
WINDOWS={'rifle':(630,645,755,755),'pistol':(195,315,240,355),'melee':(209,842,225,868)}
PROBES={'rifle':[(716,656),(713,658),(696,672),(697,674),(703,688),(706,699),(714,706),(712,719),(735,725)],'pistol':[(203,320),(198,324),(226,325),(222,326),(201,329),(203,332),(201,335),(203,339)],'melee':[(213,842),(215,844),(212,845),(218,847),(220,848),(223,852),(226,857),(239,863)]}
def alpha(pose,revision=None):
 def read(path):return Image.open(io.BytesIO(subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT))) if revision else Image.open(ROOT/path)
 r=json.loads(subprocess.check_output(['git','show',revision+':avatar-core/rigs/male_rig.json'],cwd=ROOT)) if revision else json.loads((CORE/'rigs/male_rig.json').read_text());out=np.zeros((1672,941),float)
 for art in r['poseArt'][pose].values():
  x,y,x1,y1=art['mesh']['bounds']
  for key in ['image','frontImage']:
   a=np.array(read('avatar-core/'+art[key]))[:,:,3]/255;out[y:y1,x:x1]=1-(1-out[y:y1,x:x1])*(1-a)
 w=np.array(read('avatar-core/assets/weapons/reference-art/'+pose+'.png'))[:,:,3]/255;return 1-(1-out)*(1-w)
class ContactSurfaceSourceTests(unittest.TestCase):
 def test_all_annotated_solid_hand_and_object_probes_have_no_background(self):
  for pose,points in PROBES.items():
   a=alpha(pose);source=np.array(Image.open(ROOT/'review/male-reference-arm-art/Sources'/f'{pose}.png').convert('RGBA'))
   for x,y in points:self.assertGreaterEqual(int(source[y,x,3]),240);self.assertGreaterEqual(float(a[y+26,x+10]),.97,(pose,x,y))
 def test_whole_reference_contact_surfaces_conserve_native_opaque_coverage(self):
  for pose,box in WINDOWS.items():
   src=np.array(Image.open(ROOT/'review/male-reference-arm-art/Sources'/f'{pose}.png').convert('RGBA'));a=alpha(pose);x0,y0,x1,y1=box;reference=src[y0:y1,x0:x1,3].astype(int);actual=a[y0+26:y1+26,x0+10:x1+10]*255;mask=reference>=240
   self.assertTrue(np.all(actual[mask]>=reference[mask]-8),(pose,'source-opaque contact paint was cut out'))
 def test_contact_probes_detect_actual_missing_surfaces_in_returned_package(self):
  counts={}
  for pose,points in PROBES.items():
   old=alpha(pose,'c82fb9f');counts[pose]=sum(old[y+26,x+10]<.3 for x,y in points);self.assertGreaterEqual(counts[pose],3,pose)
  (OUT/'baseline-missing-probes.json').write_text(json.dumps({p:int(v) for p,v in counts.items()},indent=2)+'\n')
 def test_core_pose_anchors_originals_engine_female_and_game_stay_unchanged(self):
  for path in ['base_male.png','base_female.png','avatar-core/rigs/female_rig.json','avatar-core/skin.mjs','avatar-core/math.mjs','avatar-core/pose-art.mjs','avatar-core/weapon-controller.mjs','avatar-core/male-preview.json','index.html','wardrobe.js','paper-doll.js','paper-doll-data.js']:
   assert_female_donor_revision(self,json.loads(subprocess.check_output(['git','show','c82fb9f:'+path],cwd=ROOT)),json.loads((ROOT/path).read_text())) if path=='avatar-core/rigs/female_rig.json' else assert_foundation_preview_revision(self,json.loads(subprocess.check_output(['git','show','c82fb9f:'+path],cwd=ROOT)),json.loads((ROOT/path).read_text())) if path=='avatar-core/male-preview.json' else self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show','c82fb9f:'+path],cwd=ROOT),path)
  old=json.loads(subprocess.check_output(['git','show','c82fb9f:avatar-core/rigs/male_rig.json'],cwd=ROOT));new=json.loads((CORE/'rigs/male_rig.json').read_text())
  assert_rig_revision(self,old,new)
  for pose,sides in old['poseArt'].items():
   for side,art in sides.items():
    for key in ['bind','anchors']:self.assertEqual(art[key],new['poseArt'][pose][side][key])
 def test_contact_underlap_uses_object_material_not_baked_source_fingers(self):
  for pose,points in {'rifle':[(370,600),(410,630),(660,680),(685,701)],'pistol':[(202,300),(255,300)],'melee':[(180,830),(230,846)]}.items():
   w=np.array(Image.open(CORE/'assets/weapons/reference-art'/f'{pose}.png'));src=np.array(Image.open(ROOT/'review/male-reference-arm-art/Sources'/f'{pose}.png'))
   for x,y in points:
    if w[y+26,x+10,3]>=240:self.assertGreater(int(np.abs(w[y+26,x+10,:3].astype(int)-src[y,x,:3].astype(int)).max()),12,(pose,x,y,'weapon must not contain visible source hand colour'))
 def test_hidden_wrist_reserves_sample_actual_warm_skin_not_item_pixels(self):
  rig=json.loads((CORE/'rigs/male_rig.json').read_text())
  for pose,sides in rig['poseArt'].items():
   for side,art in sides.items():
    m=np.array(Image.open(OUT/f'{pose}-{side}-hidden-wrist-mask.png'))>0;x0,y0,x1,y1=art['mesh']['bounds'];a=np.array(Image.open(CORE/art['image']));selected=m[y0-26:y1-26,x0-10:x1-10]&(a[:,:,3]>0)
    if selected.any():self.assertGreaterEqual(int((a[:,:,0].astype(int)-a[:,:,2].astype(int))[selected].min()),24,(pose,side,'hidden reserve sampled a dark item instead of skin'))
 def test_harmonization_is_confined_to_shared_shoulder_not_folded_forearm(self):
  m=np.array(Image.open(OUT/'pistol-right-shoulder-harmonization-mask.png'));self.assertEqual(int(m[440:560,:280].max()),0,'no rectangular retexturing across raised forearm');self.assertGreater(int(m.sum()),0)
class ContactSurfaceBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page;self.p.evaluate('avatarLab.engine.setOptions({background:"transparent"})')
 def tearDown(self):self.c.tearDown()
 def test_actual_canvas_has_no_contact_surface_holes(self):
  if self.p.evaluate('!!avatarLab.engine.posePreview.meleeMotion'):
   for pose in PROBES:self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);assert_active_foundation_contacts(self,self.p)
   return
  for pose,points in PROBES.items():
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);a=self.c.image()
   for x,y in points:
    wx,wy=runtime_point(self.p,pose,x,y,kind='item');self.assertGreaterEqual(int(a[wy,wx,3]),235,(pose,x,y))
 def test_whole_contact_windows_have_no_runtime_background_leaks(self):
  if self.p.evaluate('!!avatarLab.engine.posePreview.meleeMotion'):
   for pose in WINDOWS:self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);assert_active_foundation_contacts(self,self.p)
   return
  rows=[]
  for pose,box in WINDOWS.items():
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);src=np.array(Image.open(ROOT/'review/male-reference-arm-art/Sources'/f'{pose}.png').convert('RGBA'));a=self.c.image();x0,y0,x1,y1=box;reference=src[y0:y1,x0:x1,3].astype(int);dx,dy=runtime_point(self.p,pose,0,0,kind='item');actual=a[y0+dy:y1+dy,x0+dx:x1+dx,3].astype(int);mask=reference>=240;missing=int((actual[mask]<reference[mask]-8).sum());rows.append({'pose':pose,'source_window':box,'source_opaque_pixels':int(mask.sum()),'missing_runtime_pixels':missing,'max_alpha_loss':int((reference-actual)[mask].max())});self.assertEqual(missing,0,pose)
  (OUT/'whole-contact-coverage.json').write_text(json.dumps(rows,indent=2)+'\n')
 def test_restored_visible_object_pixels_keep_the_supplied_reference_rgb(self):
  if self.p.evaluate('!!avatarLab.engine.posePreview.meleeMotion'):
   for pose in ['pistol','rifle','melee']:self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);assert_active_foundation_contacts(self,self.p,'material')
   return
  for pose,points in {'pistol':[(203,332),(201,335)],'rifle':[(696,672),(714,706)],'melee':[(218,847),(239,863)]}.items():
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);a=self.c.image();src=np.array(Image.open(ROOT/'review/male-reference-arm-art/Sources'/f'{pose}.png'))
   for x,y in points:
    wx,wy=runtime_point(self.p,pose,x,y,kind='item');self.assertLessEqual(int(np.abs(a[wy,wx,:3].astype(int)-src[y,x,:3].astype(int)).max()),12,(pose,x,y,'must restore real material, not arbitrary opaque filler'))
 def test_palm_fringe_no_longer_has_opaque_black_backdrop_crumbs(self):
  self.p.evaluate('avatarLab.engine.setPose("pistol")');a=self.c.image()
  # These pixels previously rasterized [42,24,20] and [51,27,20] over the base.
  for x,y in [(272,358),(261,376)]:self.assertGreater(int(a[y,x,0]),110,(x,y,a[y,x].tolist()))
 def test_real_negative_space_and_forearm_source_details_are_preserved(self):
  self.p.evaluate('avatarLab.engine.setPose("pistol")');a=self.c.image();self.assertLess(int(a[426,248,3]),64,'natural gap beside the raised forearm must remain')
  if self.p.evaluate('!!avatarLab.engine.posePreview.meleeMotion'):assert_active_foundation_contacts(self,self.p,'forearm');return
  src=np.array(Image.open(ROOT/'review/male-reference-arm-art/Sources/pistol.png'))
  for x,y in [(195,500),(210,490),(200,530)]:self.assertLessEqual(int(np.abs(a[y+26,x+10,:3].astype(int)-src[y,x,:3].astype(int)).max()),8,(x,y,'preserve forearm paint'))
if __name__=='__main__':unittest.main()
