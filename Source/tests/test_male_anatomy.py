from tests.avatar_revision_contract import assert_frozen_or_ownership,OWNERSHIP_PATHS
"""Core2: independent protected-region and actual-browser checks, not art approval."""
import base64,hashlib,io,json,subprocess,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import tests.test_avatar_core as core
ROOT=core.ROOT;CORE=core.CORE

class MaleAnatomySourceTests(unittest.TestCase):
    def test_originals_and_female_rig_are_byte_identical_to_cleanup(self):
        paths=['base_male.png','base_female.png','avatar-core/rigs/female_rig.json']
        rows=subprocess.check_output(['git','ls-tree','-r','90904dd','avatar-core/assets'],cwd=ROOT,text=True)
        paths.extend(row.split('\t')[1] for row in rows.splitlines())
        for path in paths:
            assert_frozen_or_ownership(self,path,'90904dd')
    def test_art_has_no_gray_weapon_or_background_pixels(self):
        rig=json.loads((CORE/'rigs/male_rig.json').read_text())
        for sides in rig['poseArt'].values():
            for a in sides.values():
                for path in [a['image'],a['frontImage']]:
                    p=np.array(Image.open(CORE/path));rgb=p[:,:,:3].astype(int);opaque=p[:,:,3]>0
                    if 'reference-art/' in path:
                        from tests.test_reference_arm_art import assert_reference_cold_pixels_have_known_provenance
                        assert_reference_cold_pixels_have_known_provenance(self,a,path)
                    else:self.assertTrue(np.all(rgb[:,:,0][opaque]-rgb[:,:,2][opaque]>16),path)
                    self.assertTrue(np.all(p[~opaque]==0),path)
                    self.assertEqual(list(p.shape[1::-1]),[a['mesh']['bounds'][2]-a['mesh']['bounds'][0],a['mesh']['bounds'][3]-a['mesh']['bounds'][1]])

class MaleAnatomyBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
    @classmethod
    def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
    def setUp(self):
        self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page
    def tearDown(self):self.c.tearDown()
    def test_female_all_four_poses_preserve_original_head_torso_and_feet(self):
        self.c.gender('female')
        self.p.evaluate('avatarLab.engine.time=0;avatarLab.engine.setOptions({breathing:false,background:"transparent",view:"original"})')
        source=self.c.image();self.p.evaluate('avatarLab.engine.setOptions({view:"rig"})')
        # Strict SOURCE protection; archived flattened screenshots contain the
        # former background rounding and (for pistol) an obsolete gun here.
        for pose in ['idle','melee','pistol','rifle']:
            self.p.evaluate('p=>{let e=avatarLab.engine;e.time=0;e.setPose(p);e.render()}',pose)
            actual=self.c.image()
            for ys,xs in [(slice(20,245),slice(385,560)),(slice(300,430),slice(420,530)),(slice(1450,None),slice(None))]:self.assertTrue(np.array_equal(actual[ys,xs],source[ys,xs]),pose)
            if pose=='idle':self.assertTrue(np.array_equal(actual,source),pose)
    def test_pistol_legacy_aliases_and_flag_never_activate_left_arm(self):
        self.assertEqual(self.p.locator('#pistol-support').count(),0)
        for pose in ['pistol','pistol-two-hand','pistol-supported','pistol-one-hand']:
            self.p.evaluate('p=>{const e=avatarLab.engine;e.setOptions({pistolSupport:true});e.setPose(p)}',pose)
            f=self.p.evaluate('avatarLab.engine.frame');rest=self.p.evaluate('avatarLab.engine.rig.arms.left')
            self.assertEqual(self.p.evaluate('avatarLab.engine.pose'),'pistol')
            for key in ['shoulder','elbow','wrist','grip']:self.assertTrue(np.allclose(f['arms']['left'][key],rest[key]),key)
            self.assertLess(f['primaryError'],1e-6)
    def test_breathing_cycle_preserves_grips_projection_and_fixed_regions(self):
        self.p.evaluate('avatarLab.engine.setPose("idle");avatarLab.engine.time=0;avatarLab.engine.render()');ref=self.c.image()
        for pose in ['idle','melee','pistol','rifle']:
            self.p.evaluate('p=>{const e=avatarLab.engine;e.setOptions({breathing:true,cycleMs:4000});e.setPose(p)}',pose)
            for time in range(0,4001,500):
                self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',time)
                f=self.p.evaluate('avatarLab.engine.frame');im=self.c.image()
                self.assertLess(f['primaryError'],1e-6,(pose,time));self.assertLess(f['supportError'],1e-6,(pose,time))
                self.assertTrue(np.array_equal(ref[20:245,385:560],im[20:245,385:560]),(pose,time,'face'))
                self.assertTrue(np.array_equal(ref[1450:],im[1450:]),(pose,time,'feet'))
                for side in ['right','left']:
                    a=f['arms'][side]
                    for i,joints in enumerate([['shoulder','elbow'],['elbow','wrist']]):
                        projected=np.linalg.norm(np.array(a[joints[0]])-a[joints[1]])
                        self.assertAlmostEqual(projected,f['sourceBoneLengths'][side][i]*f['projection'][side][i],delta=1e-6)
    def test_pose_art_triangles_do_not_flip_during_breathing(self):
        result=self.p.evaluate('''async()=>{
            const {correctiveMatrices,correctiveVertices}=await import('../avatar-core/pose-art.mjs');
            const e=avatarLab.engine;let minRatio=Infinity,changed=0;
            const area=p=>(p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[1][1]-p[0][1])*(p[2][0]-p[0][0]);
            e.setOptions({breathing:true,transitionMs:0});
            for(const pose of ['rifle','pistol']){e.setPose(pose);for(let t=0;t<=4000;t+=125){e.time=t;e.render();
                for(const [side,art] of Object.entries(e.rig.poseArt[pose])){
                    const v=correctiveVertices(art.mesh,correctiveMatrices(art.bind,e.frame.arms[side],e.frame.transforms.torso));
                    for(const tri of art.mesh.triangles){minRatio=Math.min(minRatio,area(tri.map(i=>v[i]))/area(tri.map(i=>art.mesh.vertices[i])));changed++;}
                }
            }}return{minRatio,changed};}''')
        self.assertGreater(result['changed'],10000);self.assertGreater(result['minRatio'],.8,result)
    def test_speed_control_pause_and_bindings_still_work(self):
        self.p.locator('#speed').fill('0.5');self.p.locator('#speed').dispatch_event('input')
        self.assertEqual(self.p.evaluate('avatarLab.engine.options.playbackRate'),.5)
        self.p.locator('#sleeves').check();self.p.wait_for_function('avatarLab.engine.equipment.size===4&&Array.from(avatarLab.engine.equipment.values()).every(e=>e.bitmap)')
        self.p.evaluate('avatarLab.engine.setPose("rifle")');bound=self.c.image()
        self.p.locator('#sleeves').uncheck();self.p.wait_for_function('avatarLab.engine.equipment.size===0')
        self.assertGreater(np.count_nonzero(np.any(bound!=self.c.image(),axis=2)),100)

if __name__=='__main__':unittest.main()
