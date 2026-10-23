from tests.requested_source_contract import pre_integration_bytes
from tests.avatar_revision_contract import assert_female_donor_revision,assert_foundation_preview_revision
from tests.avatar_revision_contract import runtime_point
from tests.avatar_revision_contract import assert_rig_revision,assert_ownership_only,OWNERSHIP_PATHS
"""Contour regression from independently annotated visible source cross-sections.
The fixtures below are raw reference coordinates, NOT preparation polygons or
new-resource hashes. They fail on the returned 78d3c44/0392140 arms.
"""
from pathlib import Path
import hashlib,io,json,subprocess,unittest
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
import tests.test_avatar_core as core
ROOT=core.ROOT;CORE=core.CORE;OUT=ROOT/'review/male-arm-contour-cleanup'
# Strictly interior spans selected from the supplied reference at 400%, avoiding
# legitimate background, weapon occlusion and antialias fringe. [y,x0,x1] inclusive.
SPANS={'melee':{'right':[[520,215,301],[570,196,279],[620,184,272],[670,180,256],[720,179,229],[760,171,216],[785,169,225]]},'pistol':{'right':[[530,172,263],[560,181,236],[568,188,223]]},'rifle':{'right':[[555,158,312],[580,161,312],[600,212,312]],'left':[[500,620,706],[550,633,714],[600,648,734]]}}
def full(art,key='image',revision=None):
 b=art['mesh']['bounds'];p='avatar-core/'+art[key];data=subprocess.check_output(['git','show',revision+':'+p],cwd=ROOT) if revision else (ROOT/p).read_bytes();a=np.array(Image.open(io.BytesIO(data)));out=np.zeros((1672,941,4),dtype='uint8');out[b[1]:b[3],b[0]:b[2]]=a;return out
class ArmContourSourceTests(unittest.TestCase):
 def test_independent_reference_cross_sections_are_not_cut(self):
  rig=json.loads((CORE/'rigs/male_rig.json').read_text())
  for pose,sides in SPANS.items():
   for side,rows in sides.items():
    a=full(rig['poseArt'][pose][side]);src=np.array(Image.open(ROOT/'review/male-reference-arm-art/Sources'/f'{pose}.png').convert('RGBA'))
    for y,x0,x1 in rows:
     self.assertGreaterEqual(int(src[y,x0:x1+1,3].min()),240,'only visible reference skin belongs in this fixture')
     self.assertGreaterEqual(int(a[y+26,x0+10:x1+11,3].min()),240,(pose,side,y,x0,x1))
 def test_same_cross_sections_detect_the_returned_package_defects(self):
  old=json.loads(subprocess.check_output(['git','show','0392140:avatar-core/rigs/male_rig.json'],cwd=ROOT));missing={}
  for pose,sides in SPANS.items():
   for side,rows in sides.items():
    a=full(old['poseArt'][pose][side],revision='0392140');n=sum(int((a[y+26,x0+10:x1+11,3]<240).sum()) for y,x0,x1 in rows);missing[pose+'-'+side]=n;self.assertGreater(n,0,(pose,side,'fixture must detect the original clipping'))
  (OUT/'baseline-cross-section-failures.json').write_text(json.dumps(missing,indent=2)+'\n')
 def test_melee_wrist_triangle_and_pistol_thumb_arc_are_present(self):
  r=json.loads((CORE/'rigs/male_rig.json').read_text());m=full(r['poseArt']['melee']['right']);p=full(r['poseArt']['pistol']['right'])
  for x,y in [(208,780),(209,780),(210,781),(211,782),(247,274),(248,274),(258,278),(261,279),(265,281),(268,284),(269,286)]:
   a=m if y>700 else p;self.assertGreaterEqual(int(a[y+26,x+10,3]),240,(x,y))
 def test_existing_opaque_finger_colours_are_preserved(self):
  old=json.loads(subprocess.check_output(['git','show','0392140:avatar-core/rigs/male_rig.json'],cwd=ROOT));new=json.loads((CORE/'rigs/male_rig.json').read_text())
  for pose,sides in old['poseArt'].items():
   for side,art in sides.items():
    before=full(art,'frontImage','0392140');after=full(new['poseArt'][pose][side],'frontImage');keep=(before[:,:,3]>=240)&(after[:,:,3]>=240);self.assertGreater(int(keep.sum()),1000)
    # This pass explicitly decontaminates the exterior 1.5px black fringe.
    # Interior approved finger paint remains frozen, not globally recoloured.
    distance=ndi.distance_transform_edt(after[:,:,3]>128);delta=np.abs(before[:,:,:3].astype(int)-after[:,:,:3].astype(int)).max(2)
    self.assertLessEqual(int(delta[keep&(distance>1.5)].max()),1,(pose,side,'interior finger paint changed'))
    self.assertLessEqual(int(delta[keep].max()),8,(pose,side,'fringe correction exceeds the bounded approved cleanup'))
 def test_no_mesh_coverage_holes_or_crop_loss(self):
  r=json.loads((CORE/'rigs/male_rig.json').read_text())
  for pose,sides in r['poseArt'].items():
   for side,art in sides.items():
    mesh=art['mesh'];b=mesh['bounds'];im=Image.open(CORE/art['image']);self.assertEqual(im.size,(b[2]-b[0],b[3]-b[1]));coverage=Image.new('L',im.size);d=ImageDraw.Draw(coverage)
    for tri in mesh['triangles']:d.polygon([(mesh['vertices'][i][0]-b[0],mesh['vertices'][i][1]-b[1]) for i in tri],fill=255)
    a=np.array(im);self.assertTrue(np.all(np.array(coverage)[a[:,:,3]>16]>0),(pose,side));self.assertTrue(np.all(a[a[:,:,3]==0]==0))
 def test_original_character_engine_config_and_anchors_unchanged(self):
  paths=['base_male.png','base_female.png','avatar-core/skin.mjs','avatar-core/pose-art.mjs','avatar-core/math.mjs','avatar-core/weapon-controller.mjs','avatar-core/rigs/female_rig.json','avatar-core/male-preview.json','index.html','paper-doll.js','paper-doll-data.js','wardrobe.js']
  for path in paths:
   if path=='avatar-core/rigs/female_rig.json':assert_female_donor_revision(self,json.loads(subprocess.check_output(['git','show','0392140:'+path],cwd=ROOT)),json.loads((ROOT/path).read_text()))
   elif path=='avatar-core/male-preview.json':assert_foundation_preview_revision(self,json.loads(subprocess.check_output(['git','show','0392140:'+path],cwd=ROOT)),json.loads((ROOT/path).read_text()))
   else:self.assertEqual(pre_integration_bytes(path),subprocess.check_output(['git','show','0392140:'+path],cwd=ROOT),path)
  old=json.loads(subprocess.check_output(['git','show','0392140:avatar-core/rigs/male_rig.json'],cwd=ROOT));new=json.loads((CORE/'rigs/male_rig.json').read_text())
  assert_rig_revision(self,old,new)
  for pose,sides in old['poseArt'].items():
   for side,art in sides.items():
    for key in ['bind','anchors']:self.assertEqual(art[key],new['poseArt'][pose][side][key])
class ArmContourBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page;self.p.evaluate('avatarLab.engine.setOptions({background:"transparent"})')
 def tearDown(self):self.c.tearDown()
 def test_live_canvas_preserves_full_forearm_bicep_and_elbow_spans(self):
  for pose,sides in SPANS.items():
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);a=self.c.image()
   transform_data=self.p.evaluate('()=>({rig:avatarLab.engine.rig,f:avatarLab.engine.frame})') if pose=='melee' else None
   for side,rows in sides.items():
    for y,x0,x1 in rows:
     for x in range(x0,x1+1):
      wx,wy=runtime_point(self.p,pose,x,y,side,kind='arm',data=transform_data);self.assertGreaterEqual(int(a[wy,wx,3]),235,(pose,side,y,x))
 def test_live_shoulder_has_no_reference_black_edge_inside_base_skin(self):
  base=np.array(Image.open(ROOT/'base_male.png')).astype(int)
  for pose in ['melee','pistol','rifle']:
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);a=self.c.image().astype(int)
   for x,y in ([(316,325),(290,336),(293,345)] if pose=='pistol' else [(273,350),(262,365),(290,336)]):self.assertLessEqual(int(np.abs(a[y,x,:3]-base[y,x,:3]).max()),12,(pose,x,y,a[y,x].tolist(),base[y,x].tolist()))
 def test_free_arm_survives_every_direct_pose_cut(self):
  self.p.evaluate('avatarLab.engine.setPose("idle");avatarLab.engine.time=0;avatarLab.engine.render()');idle=self.c.image()
  for previous in ['idle','melee','pistol','rifle']:
   for pose in ['melee','pistol']:
    self.p.evaluate('a=>{let e=avatarLab.engine;e.setOptions({transitionMs:320});e.setPose(a[0]);e.setPose(a[1]);e.render()}',[previous,pose]);a=self.c.image();before=idle[400:1030,660:905];after=a[400:1030,660:905];skin=before[:,:,3]>=240;self.assertTrue(np.all(after[:,:,3][skin]>=240),(previous,pose,'lost original opaque free-arm pixels'));self.assertLessEqual(int(np.abs(before[:,:,:3].astype(int)-after[:,:,:3].astype(int))[skin].max()),2,(previous,pose,'free-arm paint'));self.assertTrue(self.p.evaluate('avatarLab.engine.transition===null'))
 def test_contact_and_visible_volume_stay_stable_over_complete_cycles(self):
  self.p.evaluate('avatarLab.engine.setOptions({breathing:true,cycleMs:4000})')
  for pose in ['idle','melee','pistol','rifle']:
   self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);areas=[];start=None
   for t in range(0,4001,125):
    self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);f=self.p.evaluate('avatarLab.engine.frame');self.assertLess(f['primaryError'],1e-6);self.assertLess(f['supportError'],1e-6);a=self.c.image();areas.append(int((a[300:1035,140:790,3]>=128).sum()))
    if t==0:start=a
    if t==4000:self.assertTrue(np.array_equal(start,a),pose)
   self.assertLess((max(areas)-min(areas))/min(areas),.04,(pose,'sudden volume loss'))
if __name__=='__main__':unittest.main()
