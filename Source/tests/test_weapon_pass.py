from tests.avatar_revision_contract import assert_frozen_or_ownership,OWNERSHIP_PATHS
"""Actual-render regressions for the bounded male weapon/switch pass."""
import hashlib,json,subprocess,unittest
import numpy as np
from PIL import Image
import tests.test_avatar_core as core
ROOT=core.ROOT;CORE=core.CORE

class WeaponPassSourceTests(unittest.TestCase):
    def test_original_pngs_female_rig_and_shared_weapons_are_unchanged(self):
        rows=subprocess.check_output(['git','ls-tree','-r','e549901','avatar-core/assets','avatar-core/rigs'],cwd=ROOT,text=True)
        paths=[r.split('\t')[1] for r in rows.splitlines() if r.split('\t')[1] not in ['avatar-core/rigs/male_rig.json','avatar-core/rigs/male_anatomy.json']]+['base_male.png','base_female.png','avatar-core/weapons.json']
        for path in paths:assert_frozen_or_ownership(self,path,'e549901')
    def test_new_prop_contacts_are_on_real_visible_pixels(self):
        config=json.loads((CORE/'male-preview.json').read_text())
        for name in ['rifle','pistol']:
            part=config['weapons'][name];a=np.array(Image.open(CORE/part['image']))
            self.assertGreater(len(np.unique(a[a[:,:,3]>=128,:3],axis=0)),1000)
            for anchor in ['primary','support','stock']:
                if part.get(anchor) is None:continue
                x,y=np.rint(part[anchor]).astype(int)
                self.assertGreaterEqual(int(a[y-1:y+2,x-1:x+2,3].max()),128,(name,anchor))
        self.assertIsNone(config['weapons']['pistol']['support'])
    def test_wrist_alpha_edit_is_local_and_does_not_repaint_skin(self):
        config=json.loads((CORE/'male-preview.json').read_text());rig=json.loads((CORE/'rigs/male_rig.json').read_text())
        old=rig['handCorrections']['melee']['right']['wristPatch'];a=np.array(Image.open(CORE/old['image']));b=np.array(Image.open(CORE/config['surfaceOverrides']['melee-right']))
        yy,xx=np.indices(a.shape[:2]);xx+=old['bounds'][0];yy+=old['bounds'][1]
        allowed=(xx>=171)&(xx<=247)&(yy>=827)&(yy<=875)
        changed=np.any(a!=b,axis=2);self.assertGreater(int(changed.sum()),0);self.assertEqual(int((changed&~allowed).sum()),0)
        visible=b[:,:,3]>0;self.assertTrue(np.array_equal(a[:,:,:3][visible],b[:,:,:3][visible]))

class WeaponPassBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
    @classmethod
    def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
    def setUp(self):self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page
    def tearDown(self):self.c.tearDown()
    def test_every_male_switch_frame_is_the_opaque_destination(self):
        self.p.evaluate('avatarLab.engine.setOptions({breathing:false,transitionMs:320})')
        poses=['idle','melee','pistol','rifle'];hashes={}
        for pose in poses:
            self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose);hashes[pose]=hashlib.sha256(self.c.image().tobytes()).hexdigest()
        for first in poses:
            for second in poses:
                if first==second:continue
                self.p.evaluate('p=>avatarLab.engine.setPose(p)',first);self.p.evaluate('p=>avatarLab.engine.setPose(p)',second)
                for time in range(0,321,16):
                    self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',time)
                    self.assertIsNone(self.p.evaluate('avatarLab.engine.transition'))
                    self.assertEqual(hashlib.sha256(self.c.image().tobytes()).hexdigest(),hashes[second],(first,second,time))
    def test_rifle_and_pistol_match_their_current_calibrated_art_bind(self):
        for pose,sides in [('rifle',['right','left']),('pistol',['right'])]:
            self.p.evaluate('p=>avatarLab.engine.setPose(p)',pose)
            frame=self.p.evaluate('avatarLab.engine.frame');anchors=self.p.evaluate('p=>avatarLab.engine.rig.poseArt[p]',pose)
            for side in sides:
                for j in ['shoulder','elbow','wrist','grip']:self.assertTrue(np.allclose(frame['arms'][side][j],anchors[side]['anchors'][j],atol=1e-6),(pose,side,j))
            if pose=='rifle':
                stock=self.p.evaluate('''()=>{const e=avatarLab.engine,m=e.frame.weapon.matrix,p=e.weapons.rifle.stock;return[m[0]*p[0]+m[2]*p[1]+m[4],m[1]*p[0]+m[3]*p[1]+m[5]]}''')
                if 'reference-art/' in self.p.evaluate('avatarLab.engine.weapons.rifle.image'):
                    self.assertTrue(np.allclose(stock,[257,512]));s=np.array(frame['arms']['right']['shoulder']);e=np.array(frame['arms']['right']['elbow']);v=e-s;t=np.dot(np.array(stock)-s,v)/np.dot(v,v);self.assertGreater(t,.5);self.assertLess(t,1);self.assertLess(np.linalg.norm(stock-(s+t*v)),25)
                else:
                    self.assertLess(np.linalg.norm(np.array(stock)-frame['arms']['right']['elbow']),35)
                    self.assertGreater(np.linalg.norm(np.array(stock)-frame['arms']['right']['shoulder']),150)
    def test_breathing_defaults_and_closed_cycle_grips_are_preserved(self):
        self.assertEqual(self.p.evaluate('avatarLab.engine.options.cycleMs'),4000)
        self.assertEqual(self.p.evaluate('avatarLab.engine.options.weaponSwayPx'),2)
        for pose in ['melee','pistol','rifle']:
            self.p.evaluate('p=>{avatarLab.engine.setOptions({breathing:true});avatarLab.engine.setPose(p)}',pose)
            start=None
            for time in range(0,4001,250):
                self.p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',time)
                f=self.p.evaluate('avatarLab.engine.frame');self.assertLess(f['primaryError'],1e-6);self.assertLess(f['supportError'],1e-6)
                if time==0:start=self.c.image();start_frame=f
                if time==4000:
                    # sin(2*pi) is not exactly zero; allow one 8-bit raster
                    # rounding level, while joint positions close at 1e-9.
                    self.assertLessEqual(int(np.abs(start.astype(int)-self.c.image().astype(int)).max()),1,pose)
                    for side in ['right','left']:
                        for key in ['shoulder','elbow','wrist','grip']:self.assertTrue(np.allclose(start_frame['arms'][side][key],f['arms'][side][key],atol=1e-9,rtol=0))

if __name__=='__main__':unittest.main()
