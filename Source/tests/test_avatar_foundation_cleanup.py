from tests.requested_source_contract import pre_integration_bytes
"""Acceptance probes independent of the original extraction colour masks."""
from pathlib import Path
import hashlib,json,subprocess,unittest
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
import tests.test_avatar_core as core
R=core.ROOT;C=R/'avatar-core';O=R/'review/avatar-foundation-cleanup'
class FoundationSourceTests(unittest.TestCase):
 def test_original_bases_refs_and_art_are_byte_identical(self):
  paths=['base_male.png','base_female.png','index.html','script.js','wardrobe.js','paper-doll.js','paper-doll-data.js','avatar-core/rigs/male_rig.json','avatar-core/rigs/female_rig.json']
  paths+=subprocess.check_output(['git','ls-tree','-r','--name-only','c2822a7','avatar-core/assets/male/reference-art','avatar-core/assets/female/donor-art','review/female-donor-arm-pass/Sources'],cwd=R,text=True).splitlines()
  for p in paths:self.assertEqual(pre_integration_bytes(p),subprocess.check_output(['git','show','c2822a7:'+p],cwd=R),p)
 def test_runtime_base_removes_only_documented_faint_matte_not_anatomy(self):
  old=np.array(Image.open(R/'base_male.png'));new=np.array(Image.open(C/'assets/male/foundation-cleanup/base-runtime.png'));mask=np.array(Image.open(O/'Evidence/base-male-removed-alpha-mask.png'))>0
  self.assertGreater(int(mask.sum()),4200);self.assertLessEqual(int(old[:,:,3][mask].max()),16);self.assertTrue(np.array_equal(old[~mask],new[~mask]));self.assertTrue(np.all(new[mask]==0));alpha=new[:,:,3];dist=ndi.distance_transform_edt(~(alpha>=32));self.assertEqual(int(((alpha>0)&(alpha<=16)&(dist>4)).sum()),0)
  labels,n=ndi.label(alpha>0,np.ones((3,3)));peaks=ndi.maximum(alpha,labels,range(1,n+1));self.assertTrue(all(p>16 for p in peaks))
 def test_all_active_arms_have_coverage_clean_alpha_and_same_registration(self):
  for g in ['male','female']:
   rig=json.loads((C/f'rigs/{g}_rig.json').read_text());cfg=json.loads((C/f'{g}-preview.json').read_text())
   for pose,sides in rig['poseArt'].items():
    for side,art in sides.items():
     for role in ['art-','art-front-']:
      path=C/cfg['poseArtSurfaces'][role+pose+'-'+side];a=np.array(Image.open(path));x,y,x1,y1=art['mesh']['bounds'];self.assertEqual(a.shape,(y1-y,x1-x,4));self.assertTrue(np.all(a[a[:,:,3]==0]==0));d=ndi.distance_transform_edt(~(a[:,:,3]>=128));self.assertEqual(int(((a[:,:,3]>0)&(a[:,:,3]<=16)&(d>2)).sum()),0)
      cov=Image.new('L',(x1-x,y1-y));dr=ImageDraw.Draw(cov)
      for tri in art['mesh']['triangles']+cfg.get('poseMeshExtensions',{}).get(pose+'-'+side,[]):dr.polygon([(art['mesh']['vertices'][i][0]-x,art['mesh']['vertices'][i][1]-y) for i in tri],fill=255)
      self.assertTrue(np.all(np.array(cov)[a[:,:,3]>0]>0),str(path))
 def test_foreground_ownership_never_includes_proximal_forearm(self):
  for gender in ['male','female']:
   rig=json.loads((C/f'rigs/{gender}_rig.json').read_text());cfg=json.loads((C/f'{gender}-preview.json').read_text())
   for pose,sides in rig['poseArt'].items():
    for side,art in sides.items():
     front=np.array(Image.open(C/cfg['poseArtSurfaces']['art-front-'+pose+'-'+side]));y,x=np.where(front[:,:,3]>=32);bx,by,_,_=art['mesh']['bounds'];w=np.array(art['anchors']['wrist']);g=np.array(art['anchors']['grip']);axis=(g-w)/np.linalg.norm(g-w);projection=(x+bx-w[0])*axis[0]+(y+by-w[1])*axis[1];self.assertGreaterEqual(float(projection.min()),-5,(gender,pose,side,'forearm in front of item'))
 def test_every_prop_is_only_registered_material_from_an_independent_complete_source(self):
  allowed={'assets/weapons/male-lobby/rifle.png','assets/weapons/male-preview/pistol.png','assets/weapons/male-exact/knife.png'}
  for row in json.loads((O/'Evidence/prop-export.json').read_text()):
   self.assertIn(row['source'],allowed);source=C/row['source'];self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),row['source_sha256']);m=np.array(row['affine']);a=np.array(Image.open(source).convert('RGBA').transform((941,1672),Image.Transform.AFFINE,tuple(np.linalg.inv(m)[:2].ravel()),Image.Resampling.BICUBIC));b=np.array(Image.open(C/row['output']));solid=b[:,:,3]>=128;self.assertTrue(np.array_equal(a[solid],b[solid]));self.assertGreater(int(solid.sum()),500)
 def test_export_is_idempotent_and_diagnostic_meshes_are_reproducible(self):
  paths=[p for g in ['male','female'] for p in (C/f'assets/{g}/foundation-cleanup').glob('*.png')]+[C/f'{g}-preview.json' for g in ['male','female']];digest=lambda:[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths];before=digest();subprocess.run(['python','tools/prepare-foundation-cleanup.py'],cwd=R,check=True,capture_output=True);self.assertEqual(before,digest())
class FoundationBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
 @classmethod
 def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
 def setUp(self):self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page
 def tearDown(self):self.c.tearDown()
 def test_knife_both_genders_uses_wrist_sway_not_inverse_elbow_motion(self):
  for g in ['male','female']:
   self.c.gender(g);samples=self.p.evaluate('''()=>{let e=avatarLab.engine;e.setPose('melee');e.setOptions({breathing:true});let a=[];for(let i=0;i<=240;i++){e.time=i*4000/240;let f=e.compute();a.push({elbow:f.arms.right.elbow,wrist:f.arms.right.wrist,hand:f.angles.right.hand,primary:f.primaryError,upper:f.angles.right.upper})}return a}''')
   elbows=np.array([s['elbow'] for s in samples]);self.assertLess(float(np.ptp(elbows[:,0])),1.3);self.assertLess(float(np.ptp(elbows[:,1])),1.3);profile=self.p.evaluate('avatarLab.engine.posePreview.meleeMotion');self.assertAlmostEqual(float(np.ptp([s['hand'] for s in samples]))*180/np.pi,2*profile['handDegrees'],delta=.02);self.assertGreater(profile['handDegrees'],0);self.assertLess(max(s['primary'] for s in samples),1e-6)
 def test_neck_and_waist_have_no_transparent_seams_at_breath_extremes(self):
  for g in ['male','female']:
   self.c.gender(g)
   for pose in ['idle','melee','pistol','rifle']:
    self.p.evaluate('p=>{let e=avatarLab.engine;e.setPose(p);e.setOptions({breathing:true,background:"transparent"})}',pose)
    for t in [0,1000,2000,3000,4000]:
     self.p.evaluate('t=>{let e=avatarLab.engine;e.time=t;e.render()}',t);a=self.c.image();source=np.array(Image.open(R/f'base_{g}.png'));self.assertGreaterEqual(int(a[293:298,430:510,3].min()),int(source[293:298,430:510,3].min()),(g,pose,t,'neck lost source opacity'));self.assertGreaterEqual(int(a[758:762,390:550,3].min()),int(source[758:762,390:550,3].min()),(g,pose,t,'waist lost source opacity'))
 def test_pose_space_garments_match_the_active_corrective_mesh_and_unbind(self):
  for g in ['male','female']:
   self.c.gender(g)
   for kind in ['collar','waist-top','short-sleeve','long-sleeve','cuff','glove','trousers','shoes']:
    self.p.evaluate('k=>{document.getElementById("diagnostic-binding").value=k}',kind);self.p.evaluate('avatarLab.diagnosticBinding()')
    for pose in ['idle','melee','pistol','rifle']:
     self.p.evaluate('p=>{let e=avatarLab.engine;e.setPose(p);e.time=1000;e.render()}',pose);self.assertLess(self.p.evaluate('avatarLab.engine.frame.primaryError'),1e-6)
    self.assertGreater(self.p.evaluate('avatarLab.engine.equipment.size'),0)
   self.p.evaluate('()=>{document.getElementById("diagnostic-binding").value="none";return avatarLab.diagnosticBinding()}');self.assertEqual(self.p.evaluate('avatarLab.engine.equipment.size'),0)
 def test_colour_probe_changes_skin_and_never_changes_weapon_resource(self):
  for g in ['male','female']:
   self.c.gender(g)
   for pose in ['melee','pistol','rifle']:
    result=self.p.evaluate('''p=>{let e=avatarLab.engine;e.setPose(p);e.time=0;e.setOptions({breathing:false});let c=document.createElement('canvas'),im=e.assets['weapon-'+p];c.width=im.width;c.height=im.height;c.getContext('2d').drawImage(im,0,0);let rows=[],items=[];for(let hue of [0,120,240]){e.visible.clear();e.buildMasked();e.setOptions({diagnosticSkinHue:hue});rows.push(e.canvas.toDataURL());for(let k of Object.keys(e.rig.segments))e.visible.set(k,false);e.buildMasked();e.render();items.push(e.canvas.toDataURL())}e.visible.clear();e.buildMasked();e.setOptions({diagnosticSkinHue:0});return {unique:new Set(rows).size,itemUnchanged:new Set(items).size===1}}''',pose);self.assertEqual(result['unique'],3);self.assertTrue(result['itemUnchanged'])
 def test_native_grids_do_not_paint_a_ghost_arm_outside_actual_skin(self):
  for g in ['male','female']:
   self.c.gender(g)
   for pose in ['idle','melee','pistol','rifle']:
    self.p.evaluate('p=>{let e=avatarLab.engine;e.setPose(p);e.time=1000;e.setOptions({breathing:true,background:"transparent"});e.setLayerVisible("weapon",false)}',pose)
    self.p.evaluate('()=>{document.getElementById("diagnostic-binding").value="none";return avatarLab.diagnosticBinding()}');base=self.c.image();distance=ndi.distance_transform_edt(base[:,:,3]<32)
    for kind in ['long-sleeve','glove']:
     self.p.evaluate('k=>{document.getElementById("diagnostic-binding").value=k}',kind);self.p.evaluate('avatarLab.diagnosticBinding()');overlay=self.c.image();outside=(overlay[:,:,3]>32)&(distance>1.5);
     if outside.any():
      Image.fromarray(base).save(O/'Evidence/ghost-base.png');Image.fromarray(overlay).save(O/'Evidence/ghost-overlay.png');ys,xs=np.where(outside);(O/'Evidence/ghost-pixels.json').write_text(json.dumps([{'x':int(x),'y':int(y),'base':base[y,x].tolist(),'overlay':overlay[y,x].tolist(),'distance':float(distance[y,x])} for x,y in zip(xs,ys)],indent=2))
     self.assertEqual(int(outside.sum()),0,(g,pose,kind,'garment left the actual arm'));self.assertGreater(int(np.any(base[:,:,:3]!=overlay[:,:,:3],axis=2).sum()),100)
    self.p.evaluate('()=>{document.getElementById("diagnostic-binding").value="none";return avatarLab.diagnosticBinding()}')
 def test_weapon_visibility_preserves_unoccluded_skin_exactly(self):
  for gender in ['male','female']:
   self.c.gender(gender)
   for pose in ['idle','melee','pistol','rifle']:
    self.p.evaluate('p=>{let e=avatarLab.engine;e.setPose(p);e.time=1000;e.setOptions({breathing:true,background:"transparent"});e.setLayerVisible("weapon",false)}',pose);bare=self.c.image()
    self.p.evaluate('avatarLab.engine.setLayerVisible("weapon",true)');armed=self.c.image()
    # The weapon group is exposed only to derive its spatial support, never expected skin RGB.
    data=self.p.evaluate('avatarLab.engine.weaponCtx.getImageData(0,0,941,1672).data.filter((v,i)=>i%4===3)');mask=ndi.distance_transform_edt(np.array(data,dtype="uint8").reshape(1672,941)==0)>2
    self.assertTrue(np.array_equal(bare[mask],armed[mask]),(gender,pose,'unoccluded skin changed with item visibility'))
 def test_all_current_contacts_and_unoccluded_material_pixels_have_independent_sources(self):
  from tests.avatar_revision_contract import assert_active_foundation_contacts
  for gender in ['male','female']:
   self.c.gender(gender)
   for pose in ['melee','pistol','rifle']:
    self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);assert_active_foundation_contacts(self,self.p);assert_active_foundation_contacts(self,self.p,'material');assert_active_foundation_contacts(self,self.p,'forearm')
 def test_fractional_display_scaling_and_dpr_do_not_reopen_partition_seams(self):
  # The old scaled-per-part compositor independently fails at width320:
  # neck alpha150 vs source253, waist247. Native-only tests miss this.
  for dpr in [1,2]:
   context=core.AvatarCoreBrowserTests.browser.new_context(viewport={'width':1440,'height':1800},device_scale_factor=dpr);page=context.new_page();page.goto(core.AvatarCoreBrowserTests.url+'avatar-lab/');page.wait_for_function('window.avatarLab?.ready');page.evaluate('avatarLab.engine.pause()')
   try:
    for width in [320,391.5,941]:
     for gender in ['male','female']:
      page.evaluate('g=>avatarLab.engine.setGender(g)',gender)
      for pose in ['idle','melee','pistol','rifle']:
       result=page.evaluate("""a=>{let e=avatarLab.engine;Object.assign(e.canvas.style,{width:a[0]+'px',height:a[0]*1672/941+'px',maxWidth:'none',maxHeight:'none',minWidth:'0',minHeight:'0'});e.setPose(a[1]);e.setOptions({breathing:true,background:'transparent'});let sample=()=>{let c=e.canvas,s=c.width/941,sy=c.height/1672,rows=[];for(let y of [294,759]){let a=e.ctx.getImageData(Math.ceil(430*s),Math.floor(y*sy),Math.floor(80*s),3).data;rows.push(Math.min(...Array.from(a).filter((v,i)=>i%4===3)))}return rows};e.setOptions({view:'original'});let source=sample();e.setOptions({view:'rig'});let frames=[];for(let t of [1000,3000]){e.time=t;e.render();frames.push(sample())}return {source,frames,width:e.canvas.width}}""",[width,pose])
       self.assertEqual(result['width'],int(width*dpr+.5),'actual backing width must match requested CSS size')
       for frame in result['frames']:
        for i,alpha in enumerate(frame):self.assertGreaterEqual(alpha,result['source'][i],(gender,pose,width,dpr,i,'scaled partition seam'))
   finally:context.close()
if __name__=='__main__':unittest.main()
