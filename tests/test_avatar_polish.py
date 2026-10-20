"""Independent polish regressions: source protection, real raster order and grips."""
from pathlib import Path
import unittest,json,hashlib,subprocess,math
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import tests.test_avatar_core as core_support
ROOT=core_support.ROOT
CORE=core_support.CORE

REVIEW=ROOT/'review/avatar-core-polish'

class PolishSourceTests(unittest.TestCase):
    def test_every_prototype_png_is_still_byte_identical(self):
        rows=subprocess.check_output(['git','ls-tree','-r','1331a91','avatar-core/assets'],cwd=ROOT,text=True)
        for row in rows.splitlines():
            meta,name=row.split('\t');b=(ROOT/name).read_bytes()
            self.assertEqual(hashlib.sha1(('blob '+str(len(b))+'\0').encode()+b).hexdigest(),meta.split()[2],name)

    def test_corrective_hands_have_single_clean_silhouette_and_fit_uv_bounds(self):
        count=0
        for g in ['male','female']:
            rig=json.loads((CORE/'rigs'/f'{g}_rig.json').read_text())
            for pose,hands in rig['handCorrections'].items():
                for side,e in hands.items():
                    count+=1;p=CORE/e['image'];a=np.array(Image.open(p));b=e['bounds'];mb=rig['skinMeshes'][side]['bounds']
                    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),e['sha256'])
                    self.assertEqual(ndi.label(a[:,:,3]>0)[1],1,(g,pose,side))
                    self.assertTrue(np.all(a[a[:,:,3]==0]==0))
                    self.assertTrue(b[0]>=mb[0] and b[1]>=mb[1] and b[2]<=mb[2] and b[3]<=mb[3],(g,pose,side))
                    x,y=np.rint(e['grip']).astype(int);self.assertEqual(int(a[y-b[1],x-b[0],3]),255)
        self.assertEqual(count,10)
        # Attachments must be on actual weapon pixels, not empty coordinates.
        for name,e in json.loads((CORE/'weapons.json').read_text()).items():
            a=np.array(Image.open(CORE/e['image']))
            for key in ['primary','support']:
                if e.get(key) is not None:
                    x,y=e[key];self.assertGreaterEqual(int(a[y,x,3]),240,(name,key))

    def test_registration_is_reproducible_without_moving_sources(self):
        paths=list((CORE/'assets').rglob('*.png'))+list((CORE/'rigs').glob('*.json'))+[CORE/'weapons.json']
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        subprocess.run(['python',str(ROOT/'tools/prepare-avatar-polish.py')],cwd=ROOT,check=True,capture_output=True)
        if (REVIEW/'sources/wrist-reference.json.gz').exists():
            subprocess.run(['python',str(ROOT/'tools/prepare-avatar-wrist-patches.py')],cwd=ROOT,check=True,capture_output=True)
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

class PolishBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):core_support.AvatarCoreBrowserTests.setUpClass()
    @classmethod
    def tearDownClass(cls):core_support.AvatarCoreBrowserTests.tearDownClass()
    def setUp(self):
        self.case=core_support.AvatarCoreBrowserTests();self.case.setUp();self.p=self.case.page;self.case.full_canvas()
    def tearDown(self):self.case.tearDown()

    def test_cached_skin_preserves_the_uncached_paint_order(self):
        records=[]
        for g in ['male','female']:
            self.case.gender(g)
            for pose in ['melee','pistol','rifle']:
                self.p.evaluate('p=>{avatarLab.engine.setOptions({skinBatching:false,background:"transparent"});avatarLab.engine.setPose(p)}',pose)
                reference=self.case.image();f=self.p.evaluate('avatarLab.engine.frame')
                self.p.evaluate('avatarLab.engine.setOptions({skinBatching:true})');cached=self.case.image()
                for side in ['right','left']:
                    for joint in ['elbow','wrist']:
                        x,y=np.rint(f['arms'][side][joint]).astype(int)
                        a=reference[y-50:y+51,x-50:x+51];b=cached[y-50:y+51,x-50:x+51]
                        inside=ndi.binary_erosion((a[:,:,3]==255)&(b[:,:,3]==255),iterations=3)
                        if not inside.any():continue
                        error=np.abs(a[:,:,:3].astype(float)-b[:,:,:3])[inside]
                        mean=float(error.mean());p99=float(np.quantile(error,.99))
                        records.append({'gender':g,'pose':pose,'side':side,'joint':joint,'mean':mean,'p99':p99})
                        self.assertLessEqual(mean,.5,(g,pose,side,joint))
                        self.assertLessEqual(p99,2,(g,pose,side,joint))
        (REVIEW/'raster-order-check.json').write_text(json.dumps(records,indent=2)+'\n')

    def test_wrist_retouch_is_applied_only_inside_declared_source_band(self):
        """Runtime A/B, not a comparison against newly approved image hashes."""
        records=[]
        for gender in ['male','female']:
            self.case.gender(gender)
            result=self.p.evaluate('''()=>{
                const e=avatarLab.engine, entries=[];
                const read=c=>Array.from(c.getContext('2d').getImageData(0,0,c.width,c.height).data);
                for(const [pose,hands] of Object.entries(e.rig.handCorrections))
                    for(const [side,entry] of Object.entries(hands)){
                        const key=pose+'-'+side,patch=entry.wristPatch;
                        if(!patch) throw Error('Missing wrist correction '+key);
                        const corrected=read(e.poseSkins[key]);
                        delete entry.wristPatch;e.buildMasked();
                        const original=read(e.poseSkins[key]);
                        entry.wristPatch=patch;e.buildMasked();
                        const bounds=e.rig.skinMeshes[side].bounds,width=bounds[2]-bounds[0];
                        let changed=0,outside=0;
                        for(let i=0;i<corrected.length;i+=4){
                            if(corrected.slice(i,i+4).every((v,k)=>v===original[i+k])) continue;
                            changed++;const x=(i/4)%width+bounds[0],y=Math.floor(i/4/width)+bounds[1];
                            if(x<patch.bounds[0]||x>=patch.bounds[2]||y<patch.bounds[1]||y>=patch.bounds[3]) outside++;
                        }
                        const wr=e.rig.arms[side].wrist;
                        const index=((wr[1]-bounds[1])*width+wr[0]-bounds[0])*4;
                        entries.push({pose,side,changed,outside,alpha:corrected[index+3],
                            band:[patch.bounds[1]-wr[1],patch.bounds[3]-wr[1]],
                            gripBelowBand:entry.grip[1]>=patch.bounds[3]});
                    }
                return entries;
            }''')
            self.assertEqual(len(result),5)
            for entry in result:
                self.assertGreater(entry['changed'],100,entry)
                self.assertEqual(entry['outside'],0,entry)
                self.assertGreaterEqual(entry['alpha'],250,entry)
                self.assertEqual(entry['band'],[-40,35],entry)
                self.assertTrue(entry['gripBelowBand'],entry)
                records.append({'gender':gender,**entry})
        (REVIEW/'wrist-patch-scope-check.json').write_text(json.dumps(records,indent=2)+'\n')

    def test_supported_pistol_and_combat_wrists_do_not_fold_backwards(self):
        self.assertTrue(self.p.locator('#pistol-support').is_checked());records=[]
        for g in ['male','female']:
            self.case.gender(g)
            for pose in ['melee','pistol','rifle']:
                for time in [0,1000,3000,4000]:
                    self.p.evaluate('a=>{const e=avatarLab.engine;e.setOptions({breathing:true});e.setPose(a[0]);e.time=a[1];e.render()}',[pose,time])
                    frame=self.p.evaluate('avatarLab.engine.frame')
                    self.assertLess(frame['primaryError'],1e-6);self.assertLess(frame['supportError'],1e-6)
                    if time in [0,4000]:
                        target=self.p.evaluate('p=>avatarLab.engine.rig.poses[p].right',pose)
                        self.assertLess(np.linalg.norm(np.array(frame['arms']['right']['grip'])-target),1e-6,(g,pose,'requested target was clamped'))
                    if pose=='rifle':
                        m=frame['weapon']['matrix'];stock=np.array([m[0]*12+m[2]*40+m[4],m[1]*12+m[3]*40+m[5]])
                        self.assertLess(np.linalg.norm(stock-frame['arms']['right']['shoulder']),60,(g,'stock off shoulder'))
                        support=self.p.evaluate('avatarLab.engine.weapons.rifle.support')
                        self.assertLess(support[0],312,'support must precede the barrel')
                    if pose=='melee':
                        m=frame['weapon']['matrix'];tip=np.array([m[0]*64+m[2]*12+m[4],m[1]*64+m[3]*12+m[5]])
                        grip=frame['arms']['right']['grip'];self.assertGreater(tip[1]-grip[1],80);self.assertLess(tip[0],grip[0]-30)
                        x,y=np.rint(tip).astype(int);base=np.array(Image.open(ROOT/f'base_{g}.png'))
                        self.assertEqual(int(base[y,x,3]),0,'lowered blade must be outside the thigh')
                    for side in ['right','left']:
                        if pose=='melee' and side=='left':continue
                        a=frame['arms'][side];fore=np.array(a['wrist'])-a['elbow'];hand=np.array(a['grip'])-a['wrist']
                        angle=math.degrees(math.acos(np.clip(np.dot(fore,hand)/np.linalg.norm(fore)/np.linalg.norm(hand),-1,1)))
                        records.append({'gender':g,'pose':pose,'side':side,'time':time,'angle_degrees':angle})
                        self.assertLessEqual(angle,70,(g,pose,side,time))
        (REVIEW/'wrist-angle-check.json').write_text(json.dumps(records,indent=2)+'\n')

    def test_hiding_corrective_hands_removes_them_and_old_fingertips_are_absent(self):
        for g in ['male','female']:
            self.case.gender(g)
            for pose in ['melee','pistol','rifle']:
                self.p.evaluate('p=>{const e=avatarLab.engine;e.setOptions({background:"transparent"});e.setPose(p);for(const k of [...Object.keys(e.rig.segments),"weapon"]) e.setLayerVisible(k,false);e.setLayerVisible("rightHand",true)}',pose)
                im=self.case.image();self.assertGreater(np.count_nonzero(im[:,:,3]),100)
                p=self.p.evaluate('''()=>{const e=avatarLab.engine,a=e.rig.arms.right,p=[a.wrist[0],a.wrist[1]+145],m=e.frame.arms.right.hand;return[m[0]*p[0]+m[2]*p[1]+m[4],m[1]*p[0]+m[3]*p[1]+m[5]]}''')
                x,y=np.rint(p).astype(int)
                self.assertEqual(int(im[y-2:y+3,x-2:x+3,3].max()),0,(g,pose,'old source fingertips'))
                self.p.evaluate('avatarLab.engine.setLayerVisible("rightHand",false)')
                self.assertEqual(int(self.case.image()[:,:,3].max()),0,(g,pose,'hidden hand remains'))
                self.case.gender(g)

    def test_all_pose_transitions_keep_joints_continuous_and_wrists_within_range(self):
        poses=['idle','melee','pistol','rifle']
        for gender in ['male','female']:
            self.case.gender(gender)
            for first in poses:
                for second in poses:
                    if first==second:continue
                    records=self.p.evaluate('''([first,second])=>{
                        const e=avatarLab.engine;e.setOptions({breathing:false,transitionMs:0});e.setPose(first);
                        const before=structuredClone(e.frame.arms);e.setOptions({transitionMs:320});e.setPose(second);
                        const after=structuredClone(e.frame.arms),frames=[];
                        for(let i=0;i<4;i++){e.step(80);frames.push(structuredClone(e.frame.arms));}
                        return{before,after,frames};
                    }''',[first,second])
                    for side in ['right','left']:
                        for joint in ['shoulder','elbow','wrist']:
                            self.assertLess(np.linalg.norm(np.array(records['before'][side][joint])-records['after'][side][joint]),1e-6)
                        for f in records['frames']:
                            a=f[side];fore=np.array(a['wrist'])-a['elbow'];hand=np.array(a['grip'])-a['wrist']
                            angle=math.degrees(math.acos(np.clip(np.dot(fore,hand)/np.linalg.norm(fore)/np.linalg.norm(hand),-1,1)))
                            self.assertLessEqual(angle,70,(gender,first,second,side))
        self.p.evaluate('avatarLab.engine.destroy()')
        self.assertEqual(self.p.evaluate('Object.keys(avatarLab.engine.poseSkins).length+Object.keys(avatarLab.engine.poseHandSkins).length'),0)

if __name__=='__main__':unittest.main()
