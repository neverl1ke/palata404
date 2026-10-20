"""Independent final-cleanup checks: immutable inputs, bounded edits, fixed stance."""
import hashlib,json,subprocess,unittest,math
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import tests.test_avatar_core as core
ROOT=core.ROOT;OUT=ROOT/'review/avatar-core-cleanup';BASE='4f46b15'

class CleanupSourceTests(unittest.TestCase):
    def test_all_65_precleanup_pngs_are_byte_identical(self):
        rows=subprocess.check_output(['git','ls-tree','-r',BASE,'avatar-core/assets'],cwd=ROOT,text=True)
        checked=0
        for row in rows.splitlines():
            meta,name=row.split('\t')
            if not name.endswith('.png'):continue
            payload=(ROOT/name).read_bytes();actual=hashlib.sha1(('blob '+str(len(payload))+'\0').encode()+payload).hexdigest()
            self.assertEqual(actual,meta.split()[2],name);checked+=1
        self.assertEqual(checked,65)
        for gender in ['male','female']:
            previous=json.loads(subprocess.check_output(['git','show',BASE+':avatar-core/rigs/'+gender+'_rig.json'],cwd=ROOT))
            current=json.loads((ROOT/'avatar-core/rigs'/f'{gender}_rig.json').read_text())
            for field in ['arms','poses','landmarks','breathing','segments']:
                self.assertEqual(current[field],previous[field],(gender,field))
            for side in ['right','left']:
                for field in ['vertices','triangles','handTriangles','bounds']:
                    self.assertEqual(current['skinMeshes'][side][field],previous['skinMeshes'][side][field],(gender,side,field))
        self.assertEqual((ROOT/'avatar-core/weapons.json').read_bytes(),subprocess.check_output(['git','show',BASE+':avatar-core/weapons.json'],cwd=ROOT))

    def test_new_transition_edges_have_no_faint_projection_away_from_the_silhouette(self):
        records=[]
        for gender in ['male','female']:
            rig=json.loads((ROOT/'avatar-core/rigs'/f'{gender}_rig.json').read_text())
            for pose,hands in rig['handCorrections'].items():
                for side,entry in hands.items():
                    patch=entry['wristPatch'];a=np.array(Image.open(ROOT/'avatar-core'/patch['image']))
                    wr=rig['arms'][side]['wrist'][1];yy=np.arange(patch['bounds'][1],patch['bounds'][3])[:,None]-wr
                    xx=np.arange(patch['bounds'][0],patch['bounds'][2])[None,:]
                    local=abs(xx-rig['arms'][side]['wrist'][0])<75
                    transition=((yy>-40)&(yy<-20))|((yy>15)&(yy<35))
                    faint=(a[:,:,3]>0)&(a[:,:,3]<128)&transition&local
                    previous=np.array(Image.open(ROOT/'avatar-core'/patch['image'].replace('-wrist-clean.png','-wrist-patch.png')))
                    self.assertTrue(np.array_equal(a[:,~local[0]],previous[:,~local[0]]),'remote original coverage changed')
                    distance=ndi.distance_transform_edt(a[:,:,3]<128)
                    maximum=float(distance[faint].max()) if faint.any() else 0
                    # One raster-pixel antialias fringe, including a diagonal.
                    self.assertLessEqual(maximum,1.5,(gender,pose,side))
                    self.assertTrue(np.all(a[a[:,:,3]==0]==0))
                    records.append({'gender':gender,'pose':pose,'side':side,'max_fringe_distance_pixels':maximum})
        (OUT/'edge-fringe-check.json').write_text(json.dumps(records,indent=2)+'\n')

class CleanupBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):core.AvatarCoreBrowserTests.setUpClass()
    @classmethod
    def tearDownClass(cls):core.AvatarCoreBrowserTests.tearDownClass()
    def setUp(self):
        self.c=core.AvatarCoreBrowserTests();self.c.setUp();self.c.full_canvas();self.p=self.c.page
    def tearDown(self):self.c.tearDown()

    def test_actual_render_changes_only_at_wrists_and_female_rifle_shoulder(self):
        states={(s['gender'],s['pose']):s for s in json.loads((OUT/'before/browser-check.json').read_text())['states']}
        records=[]
        for gender in ['male','female']:
            self.c.gender(gender)
            for pose in ['idle','melee','pistol','rifle']:
                self.p.evaluate('p=>{const e=avatarLab.engine;e.time=0;e.setOptions({pistolSupport:true});e.setPose(p)}',pose)
                frame=self.p.evaluate('avatarLab.engine.frame');before=states[gender,pose]['frame']
                def same(a,b,angles=False):
                    if isinstance(a,dict):
                        self.assertEqual(a.keys(),b.keys())
                        for k in a:same(a[k],b[k],angles)
                    elif isinstance(a,list):
                        self.assertEqual(len(a),len(b))
                        for x,y in zip(a,b):same(x,y,angles)
                    elif isinstance(a,(int,float)) and not isinstance(a,bool):
                        if angles:
                            self.assertAlmostEqual(math.sin(a),math.sin(b),delta=1e-9)
                            self.assertAlmostEqual(math.cos(a),math.cos(b),delta=1e-9)
                        else:self.assertAlmostEqual(a,b,delta=1e-9)
                    else:self.assertEqual(a,b)
                for field in ['arms','weapon','angles','transforms']:same(frame[field],before[field],field=='angles')
                actual=self.c.image();reference=np.array(Image.open(OUT/'before'/f'{gender}-{pose}.png').convert('RGBA'))
                self.assertEqual(actual.shape,reference.shape)
                allowed=np.zeros(actual.shape[:2],bool)
                if pose!='idle':
                    for side in ['right','left'] if pose!='melee' else ['right']:
                        x,y=np.rint(frame['arms'][side]['wrist']).astype(int)
                        allowed[y-100:y+101,x-100:x+101]=True
                if gender=='female' and pose=='rifle':allowed[290:530,590:800]=True
                changed=np.any(actual!=reference,axis=2)
                self.assertEqual(int((changed&~allowed).sum()),0,(gender,pose,'edit escaped local area'))
                self.assertTrue(np.array_equal(actual[:295],reference[:295]))
                self.assertTrue(np.array_equal(actual[1450:],reference[1450:]))
                records.append({'gender':gender,'pose':pose,'changed_pixels':int(changed.sum()),'changed_outside_local_areas':0,'stance_identical':True})
        (OUT/'render-scope-check.json').write_text(json.dumps(records,indent=2)+'\n')

    def test_shoulder_surface_is_local_continuous_and_never_changes_skeleton(self):
        self.c.gender('female')
        result=self.p.evaluate('''async()=>{
            const {skinVertices}=await import('../avatar-core/skin.mjs');
            const {armMatrices}=await import('../avatar-core/math.mjs');
            const e=avatarLab.engine,mesh=e.rig.skinMeshes.left,rest=e.rig.arms.left;
            const plain={...mesh};delete plain.shoulderArcBlend;
            let maxOffset=0,outside=0,maxStep=0,changed=0,prev=null;
            for(let angle=0;angle>=-1.301;angle-=.001){
                const arm=armMatrices(rest,rest.shoulder,{upper:angle,fore:0,hand:0});
                const baseline=skinVertices(plain,arm,[1,0,0,1,0,0],rest);
                const current=skinVertices(mesh,arm,[1,0,0,1,0,0],rest);
                const deltas=current.map((p,i)=>[p[0]-baseline[i][0],p[1]-baseline[i][1]]);
                deltas.forEach((d,i)=>{
                    const size=Math.hypot(...d),v=mesh.vertices[i];maxOffset=Math.max(maxOffset,size);
                    if(size>1e-8){changed++;if(v[1]>=500||v[2]===0||v[2]===1||v[3]>0||v[4]>0||angle>-.75)outside++;}
                    if(prev)maxStep=Math.max(maxStep,Math.hypot(d[0]-prev[i][0],d[1]-prev[i][1]));
                });prev=deltas;
            }
            return{maxOffset,outside,maxStep,changed};
        }''')
        self.assertGreater(result['changed'],0)
        self.assertEqual(result['outside'],0)
        self.assertLess(result['maxOffset'],25)
        self.assertLess(result['maxStep'],.2)
        (OUT/'shoulder-continuity-check.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':unittest.main()
