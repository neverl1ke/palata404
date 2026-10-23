from tests.avatar_revision_contract import assert_frozen_or_ownership,assert_foundation_preview_revision
"""Chest-only addition: independent displacement/raster budgets and preservation."""
import json,subprocess,unittest
import numpy as np
import tests.test_avatar_core as core
ROOT=core.ROOT;OUT=ROOT/'review/avatar-core-grip-pass'
class GripSourceTests(unittest.TestCase):
 def test_every_prior_png_rig_and_pose_is_unchanged(self):
  paths=[r.split('\t')[1] for r in subprocess.check_output(['git','ls-tree','-r','f49ae7b','avatar-core/assets','avatar-core/rigs'],cwd=ROOT,text=True).splitlines()]+['base_male.png','base_female.png','avatar-core/math.mjs','avatar-core/skin.mjs','avatar-core/pose-art.mjs','avatar-core/weapon-controller.mjs']
  paths=[p for p in paths if p!='avatar-core/rigs/male_rig.json']
  old_rig=json.loads(subprocess.check_output(['git','show','f49ae7b:avatar-core/rigs/male_rig.json'],cwd=ROOT));new_rig=json.loads((ROOT/'avatar-core/rigs/male_rig.json').read_text())
  for key in ['poses','anatomyProjection','handCorrections','poseArt']:old_rig.pop(key);new_rig.pop(key)
  for k in ['leftUpper','leftFore','leftHand','lower']:old_rig['segments'][k]['sha256']=new_rig['segments'][k]['sha256']
  for k in ['image','handImage']:old_rig['skinMeshes']['left'][k]=new_rig['skinMeshes']['left'][k]
  self.assertEqual(old_rig,new_rig,'only explicit pose/art and thigh ownership changes are authorized')
  for path in paths:assert_frozen_or_ownership(self,path,'f49ae7b')
  old_engine=subprocess.check_output(['git','show','f49ae7b:avatar-core/engine.mjs'],cwd=ROOT,text=True);new_engine=(ROOT/'avatar-core/engine.mjs').read_text()
  section=lambda s:s.split('    setPose(pose) {',1)[1].split('    setWeapon(',1)[0]
  self.assertEqual(section(old_engine),section(new_engine).replace("if (this.gender === 'male' || this.rig.posePolicy?.instant) {","if (this.gender === 'male') {"),'male instant-cut branch must remain unchanged; only new female policy is authorized')
  current=json.loads((ROOT/'avatar-core/male-preview.json').read_text())
  if 'runtimeSource' in current:
   prior=json.loads(subprocess.check_output(['git','show','c2822a7:avatar-core/male-preview.json'],cwd=ROOT));assert_foundation_preview_revision(self,prior,current);current=prior
  current.pop('chestDetail');current.pop('poseArtSurfaces',None);old=json.loads(subprocess.check_output(['git','show','f49ae7b:avatar-core/male-preview.json'],cwd=ROOT));
  for pose in ['rifle','pistol','melee']:
   for key in ['image','size','primary','support','stock','trigger','scale','angle','offset','art']:current['weapons'][pose].pop(key,None);old['weapons'][pose].pop(key,None)
  self.assertEqual(current,old)
class ChestBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page
 def tearDown(self):self.c.tearDown()
 def test_chest_surface_changes_only_chest_pixels_not_hand_contacts(self):
  rows=[]
  for pose in ['idle','melee','pistol','rifle']:
   self.p.evaluate('p=>{const e=avatarLab.engine;e.setPose(p);e.time=1000;e.setOptions({breathing:true})}',pose)
   before_frame=self.p.evaluate('avatarLab.engine.frame');actual=self.c.image()
   self.p.evaluate('()=>{const e=avatarLab.engine;window.savedChest=e.malePreview.chestDetail;delete e.malePreview.chestDetail;e.render()}');control=self.c.image()
   self.assertEqual(before_frame,self.p.evaluate('avatarLab.engine.frame'))
   changed=np.any(actual!=control,axis=2);y,x=np.where(changed);self.assertGreater(len(y),500)
   self.assertGreaterEqual(int(x.min()),280);self.assertLess(int(x.max()),670);self.assertGreaterEqual(int(y.min()),310);self.assertLess(int(y.max()),625)
   for box in [(0,0,941,300),(0,650,941,1672),(180,240,280,410)]:
    x0,y0,x1,y1=box;self.assertTrue(np.array_equal(actual[y0:y1,x0:x1],control[y0:y1,x0:x1]),(pose,box))
   rows.append({'pose':pose,'time_ms':1000,'changed_chest_pixels':int(len(y)),'changed_bbox':[int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1],'frame_and_weapon_contacts_unchanged':True})
   self.p.evaluate('avatarLab.engine.malePreview.chestDetail=savedChest;avatarLab.engine.render()')
  (OUT/'chest-raster-check.json').write_text(json.dumps(rows,indent=2)+'\n')
 def test_chest_mesh_has_bounded_expansion_positive_topology_and_closed_cycle(self):
  result=self.p.evaluate('''()=>{const e=avatarLab.engine;e.setPose('rifle');e.setOptions({breathing:true,cycleMs:4000});let max=0,minRatio=Infinity,outside=0;let first;
   const area=p=>(p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[1][1]-p[0][1])*(p[2][0]-p[0][0]);
   for(let t=0;t<=4000;t+=125){e.time=t;e.render();const v=e.chestDetailVertices(e.frame),m=e.frame.transforms.torso,d=e.malePreview.chestDetail,mesh=e.chestDetailMesh;if(t===0)first=v;
    mesh.vertices.forEach(([x,y],i)=>{const target=[m[0]*x+m[2]*y+m[4],m[1]*x+m[3]*y+m[5]];const delta=Math.hypot(v[i][0]-target[0],v[i][1]-target[1]);max=Math.max(max,delta);if(((x-d.center[0])/d.radius[0])**2+((y-d.center[1])/d.radius[1])**2>=1&&delta>1e-9)outside++});
    for(const tri of mesh.triangles)minRatio=Math.min(minRatio,area(tri.map(i=>v[i]))/area(tri.map(i=>mesh.vertices[i])));
    if(t===4000)for(let i=0;i<v.length;i++)if(Math.hypot(v[i][0]-first[i][0],v[i][1]-first[i][1])>1e-9)throw Error('cycle not closed');
   }return{max_local_displacement_source_px:max,min_triangle_ratio:minRatio,outside_support_vertices_changed:outside,cycle_ms:4000,samples:33};}''')
  self.assertGreater(result['max_local_displacement_source_px'],1);self.assertLess(result['max_local_displacement_source_px'],2);self.assertGreater(result['min_triangle_ratio'],.95);self.assertEqual(result['outside_support_vertices_changed'],0)
  (OUT/'chest-metrics.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':unittest.main()
