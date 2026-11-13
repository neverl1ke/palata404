"""Approved pajama items use real wardrobe transactions and real posed canvases.

These checks prove item independence, persistence and actual compositing. The
saved pose images supplement, rather than replace, visual anatomical review.
"""
import base64
import json
from pathlib import Path
import unittest

from tests import test_game as support


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-results' / 'pajamas'
PIECES = {
    'upperBody': 'patient-pajama-top',
    'pants': 'patient-pajama-pants',
    'footwear': 'patient-pajama-slippers',
}
PARTS = {'upperBody': 'top', 'pants': 'pants', 'footwear': 'footwear'}
POSES = [(None, 'idle'), ('gear-knife', 'melee'), ('gear-aks', 'rifle')]


class PajamasUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        results = ROOT / 'test-results'
        if results.is_symlink():
            results.resolve().mkdir(parents=True, exist_ok=True)
        OUT.mkdir(parents=True, exist_ok=True)
        support.GameTests.setUpClass.__func__(cls)

    tearDownClass = classmethod(support.GameTests.tearDownClass.__func__)
    setUp = support.GameTests.setUp
    tearDown = support.GameTests.tearDown
    load = support.GameTests.load

    def open_wardrobe(self):
        self.page.evaluate('openCustomization()')
        self.page.locator('#custom-modal').wait_for(state='visible')

    def gender(self, gender):
        self.page.locator('[data-archive-slot="appearance"]').click()
        self.page.locator('[data-paper-gender="' + gender + '"]').click()
        self.page.locator('[data-archive-slot="equipment"]').click()

    def view(self, mode):
        self.page.locator('[data-paper-view="' + mode + '"]').click()

    def selected(self):
        return self.page.evaluate('''()=>Object.fromEntries(
            ['upperBody','pants','footwear'].map(slot=>[slot,selectedPaperDollItem(slot)?.id||null]))''')

    def facts(self):
        return self.page.evaluate('JSON.stringify({stats,inventory,equippedGear})')

    def toggle_piece(self, slot):
        item_id = PIECES[slot]
        self.page.locator('[data-archive-slot="' + slot + '"]').click()
        self.page.locator('[data-wardrobe-card="' + item_id + '"]').click()
        action = self.page.locator('[data-wardrobe-action="' + item_id + '"]')
        self.assertFalse(action.is_disabled())
        action.click()
        # Mobile equipment details open over the catalogue; return through its
        # real Back control so the next rail remains reachable.
        back = self.page.locator('.archive-detail-close')
        if back.count() and back.is_visible():
            back.click()

    def full_set(self):
        for slot, item_id in PIECES.items():
            if self.selected()[slot] != item_id:
                self.toggle_piece(slot)
        self.assertEqual(self.selected(), PIECES)

    def ready_pose(self, host_id, pose, gender, parts=('pants', 'footwear', 'top')):
        expected = sorted(parts)
        self.page.wait_for_function(r'''({id,pose,gender,parts})=>{
            const host=document.getElementById(id);
            const scene=window.avatarCoreGamePreview?.instances.get(host);
            const actual=(host?.dataset.pajamaParts||'').split(/\s+/).filter(Boolean).sort();
            const visibleStatic=[...(host?.querySelectorAll('.char-layer,.paper-doll-frozen')||[])].some(node=>{
                if(node.classList.contains('hidden'))return false;
                const style=getComputedStyle(node);
                return style.display!=='none' && style.visibility!=='hidden' && Number(style.opacity)>0;
            });
            return host?.dataset.avatarCoreReady==='true'
                && host.dataset.avatarPose===pose
                && !host.dataset.avatarCoreBlocked && !host.dataset.avatarCoreError
                && scene?.engine.gender===gender && scene.engine.pose===pose
                && !scene.running && !scene.pending && scene.canvas && !scene.canvas.hidden
                && scene.canvas.width>=941 && scene.canvas.height===1672
                && !visibleStatic
                && JSON.stringify(actual)===JSON.stringify(parts)
                && (parts.length ? host.dataset.pajamaPose===pose : !host.dataset.pajamaPose);
        }''', arg={'id': host_id, 'pose': pose, 'gender': gender, 'parts': expected}, timeout=60000)

    def repaint_roundtrip(self, host_id, pose, gender):
        # Decode callbacks used to reveal the old static actor after the native
        # canvas became ready. Let those callbacks and real paint frames finish
        # before checking that the actor still has only one visible renderer.
        self.page.locator('#' + host_id).evaluate('''async host=>{
            await Promise.allSettled([...host.querySelectorAll('img[src]')].map(image=>image.decode()));
            await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
        }''')
        self.ready_pose(host_id, pose, gender)

    def apply_and_close(self):
        self.page.locator('.archive-footer').get_by_role('button', name='Применить', exact=True).click()
        self.page.locator('.archive-wardrobe .report-close').click()
        self.page.locator('#custom-modal').wait_for(state='hidden')

    def canvas(self, host_id):
        data = self.page.locator('#' + host_id).evaluate('''host=>{
            const scene=avatarCoreGamePreview.instances.get(host);
            return scene.canvas.toDataURL('image/png');
        }''')
        return base64.b64decode(data.split(',', 1)[1])

    def garment_regions(self):
        return self.page.locator('#wardrobe-paperdoll').evaluate('''host=>{
            const scene=avatarCoreGamePreview.instances.get(host),canvas=scene.canvas;
            const ctx=canvas.getContext('2d');
            const rects={top:[440,650,65,65],pants:[330,1050,55,65],footwear:[310,1600,45,30]};
            return Object.fromEntries(Object.entries(rects).map(([part,[x,y,w,h]])=>{
                const data=ctx.getImageData(x,y,w,h).data,sum=[0,0,0];let count=0;
                for(let i=0;i<data.length;i+=4)if(data[i+3]>=128){
                    sum[0]+=data[i];sum[1]+=data[i+1];sum[2]+=data[i+2];count++;
                }
                return [part,{count,rgb:sum.map(value=>value/Math.max(1,count))}];
            }));
        }''')

    def assert_real_clothing_pixels(self, gender):
        self.ready_pose('wardrobe-paperdoll', 'idle', gender)
        dressed = self.garment_regions()
        self.page.evaluate("['upperBody','pants','footwear'].forEach(s=>wardrobeHiddenSlots.add(s));renderWardrobe()")
        self.ready_pose('wardrobe-paperdoll', 'idle', gender, parts=())
        bare = self.garment_regions()
        self.page.evaluate('wardrobeHiddenSlots.clear();renderWardrobe()')
        self.ready_pose('wardrobe-paperdoll', 'idle', gender)
        for part in ['top', 'pants', 'footwear']:
            self.assertGreater(dressed[part]['count'], 50, part + ' has no opaque pixels')
            difference = sum(abs(a - b) for a, b in zip(dressed[part]['rgb'], bare[part]['rgb'])) / 3
            self.assertGreater(difference, 12, part + ' did not visibly change the actual avatar canvas')

    def test_three_real_ui_items_are_independent_cosmetics_and_both_loadouts_persist(self):
        self.load()
        self.page.set_viewport_size({'width': 1672, 'height': 941})
        self.assertEqual(self.page.evaluate('paperDollState.patientLoadout.upperBody'), 'patient-tunic')
        self.assertIsNone(self.page.evaluate('paperDollState.patientLoadout.pants'))
        self.assertIsNone(self.page.evaluate('paperDollState.patientLoadout.footwear'))
        self.open_wardrobe()
        for gender in ['male', 'female']:
            self.gender(gender)
            for mode in ['patient', 'combat']:
                self.view(mode)
                facts = self.facts()
                self.full_set()
                self.ready_pose('wardrobe-paperdoll', 'idle', gender)
                self.assertEqual(self.facts(), facts)
                for slot in PIECES:
                    self.toggle_piece(slot)
                    expected = dict(PIECES)
                    expected[slot] = None
                    self.assertEqual(self.selected(), expected)
                    self.ready_pose('wardrobe-paperdoll', 'idle', gender,
                                    parts=[part for key, part in PARTS.items() if key != slot])
                    self.assertEqual(self.facts(), facts)
                    self.toggle_piece(slot)
                    self.assertEqual(self.selected(), PIECES)
                self.page.locator('.archive-footer').get_by_role('button', name='Применить', exact=True).click()
                self.ready_pose('character-paperdoll', 'idle', gender)
                self.repaint_roundtrip('character-paperdoll', 'idle', gender)
                self.assertEqual(self.facts(), facts)
        saved = self.page.evaluate('JSON.stringify(paperDollState)')
        facts = self.facts()
        self.apply_and_close()
        self.ready_pose('character-paperdoll', 'idle', 'female')
        self.repaint_roundtrip('character-paperdoll', 'idle', 'female')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('JSON.stringify(paperDollState)'), saved)
        self.assertEqual(self.facts(), facts)
        self.ready_pose('character-paperdoll', 'idle', 'female')
        self.repaint_roundtrip('character-paperdoll', 'idle', 'female')
        state = json.loads(saved)
        for loadout in ['patientLoadout', 'combatLoadout']:
            self.assertEqual({slot: state[loadout][slot] for slot in PIECES}, PIECES)
        # Each part remains usable from the actual narrow wardrobe catalogue.
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.open_wardrobe()
        for slot in PIECES:
            self.toggle_piece(slot)
            self.assertIsNone(self.selected()[slot])
            self.toggle_piece(slot)
            self.assertEqual(self.selected()[slot], PIECES[slot])
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 391)

    def test_face_neck_stays_below_individual_shirt_and_head_is_preserved(self):
        self.load()
        self.page.set_viewport_size({'width': 1672, 'height': 941})
        self.open_wardrobe()
        self.page.evaluate("setPaperDollView('combat');['outerwear','armor','loadout','gloves','pants','footwear','back','accessory','headwear','beard'].forEach(s=>equipPaperDollItem(s,null));equipPaperDollItem('upperBody','patient-pajama-top')")
        for gender, face, hair in [
            ('male', 'face-asian', 'hair-none'),
            ('male', 'face-male-new-stern', 'hair-none'),
            ('female', None, 'hair-none'),
            ('female', 'face-ginger-soft', 'hair-none'),
            ('female', 'face-female-new-soft-gaze', 'hair-bob'),
        ]:
            self.page.evaluate("a=>{setGender(a.gender);equipPaperDollItem('face',a.face);equipPaperDollItem('hair',a.hair)}",
                               {'gender': gender, 'face': face, 'hair': hair})
            for weapon, pose in POSES:
                with self.subTest(gender=gender, face=face, pose=pose):
                    self.page.evaluate("id=>equipPaperDollItem('weapon',id)", weapon)
                    self.ready_pose('wardrobe-paperdoll', pose, gender, parts=('top',))
                    pixels = self.page.evaluate("""async()=>{
                        const s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll'));
                        s.engine.pause();s.engine.options.breathing=false;s.pajamaMotion.breathing=false;s.engine.time=0;s.engine.render();
                        const image=new Image();image.src=selectedPaperDollItem('upperBody').poseClothingByGender[s.engine.gender][s.engine.pose];await image.decode();
                        const garment=document.createElement('canvas');garment.width=941;garment.height=1672;
                        const ctx=garment.getContext('2d');ctx.drawImage(image,0,0,941,1672);
                        const cloth=ctx.getImageData(0,0,941,1672).data;
                        const actual=s.canvas.getContext('2d').getImageData(0,0,s.canvas.width,1672).data;
                        const native=s.engine.canvas.getContext('2d').getImageData(0,0,s.engine.canvas.width,1672).data;
                        let opaqueCollarPixels=0,collarOverpaintPixels=0,changedHeadPixels=0;
                        // No gun intersects this collar rectangle. Fully opaque
                        // cloth must cover the face PNG's old neck/shoulder join.
                        for(let y=220;y<400;y++)for(let x=140;x<800;x++){
                            const i=(y*941+x)*4,j=(y*s.canvas.width+x)*4;
                            if(cloth[i+3]===255){opaqueCollarPixels++;if(Math.max(Math.abs(cloth[i]-actual[j]),Math.abs(cloth[i+1]-actual[j+1]),Math.abs(cloth[i+2]-actual[j+2]))>16)collarOverpaintPixels++;}
                        }
                        for(let y=0;y<220;y++)for(let x=0;x<941;x++){
                            const i=(y*s.engine.canvas.width+x)*4,j=(y*s.canvas.width+x)*4;
                            if([0,1,2,3].some(c=>native[i+c]!==actual[j+c]))changedHeadPixels++;
                        }
                        return {opaqueCollarPixels,collarOverpaintPixels,changedHeadPixels};
                    }""")
                    self.assertGreater(pixels['opaqueCollarPixels'], 10000)
                    self.assertEqual(pixels['collarOverpaintPixels'], 0, pixels)
                    self.assertEqual(pixels['changedHeadPixels'], 0, pixels)

    def test_full_set_keeps_all_native_weapon_poses_in_wardrobe_and_applied_main_avatar(self):
        self.load()
        self.page.set_viewport_size({'width': 1672, 'height': 941})
        self.open_wardrobe()
        evidence = []
        for gender in ['male', 'female']:
            self.gender(gender)
            for mode in ['patient', 'combat']:
                self.view(mode)
                self.full_set()
                for weapon_id, pose in POSES:
                    current = self.page.evaluate('selectedPaperDollItem("weapon")?.id||null')
                    if current != weapon_id:
                        self.page.locator('[data-archive-slot="weapon"]').click()
                        target = weapon_id or current
                        self.page.locator('[data-wardrobe-card="' + target + '"]').click()
                        self.page.locator('[data-wardrobe-action="' + target + '"]').click()
                    self.ready_pose('wardrobe-paperdoll', pose, gender)
                    if mode == 'combat' and pose == 'idle':
                        self.assert_real_clothing_pixels(gender)
                    if mode == 'combat':
                        (OUT / f'{gender}-{pose}-wardrobe-canvas.png').write_bytes(self.canvas('wardrobe-paperdoll'))
                        self.page.screenshot(path=str(OUT / f'{gender}-{pose}-wardrobe.png'))
                    self.page.locator('.archive-footer').get_by_role('button', name='Применить', exact=True).click()
                    self.ready_pose('character-paperdoll', pose, gender)
                    self.repaint_roundtrip('character-paperdoll', pose, gender)
                    self.page.locator('.archive-wardrobe .report-close').click()
                    self.page.locator('#custom-modal').wait_for(state='hidden')
                    self.ready_pose('character-paperdoll', pose, gender)
                    self.repaint_roundtrip('character-paperdoll', pose, gender)
                    if mode == 'combat':
                        (OUT / f'{gender}-{pose}-main-canvas.png').write_bytes(self.canvas('character-paperdoll'))
                        self.page.screenshot(path=str(OUT / f'{gender}-{pose}-main.png'))
                    evidence.append({'gender': gender, 'mode': mode, 'pose': pose,
                                     'wardrobeReady': True, 'appliedMainReady': True,
                                     'noVisibleStaticLayersAfterRepaint': True})
                    self.open_wardrobe()
        self.apply_and_close()
        self.ready_pose('character-paperdoll', 'rifle', 'female')
        self.page.reload(wait_until='networkidle')
        self.ready_pose('character-paperdoll', 'rifle', 'female')
        self.repaint_roundtrip('character-paperdoll', 'rifle', 'female')
        self.page.screenshot(path=str(OUT / 'female-rifle-reload-main.png'))
        (OUT / 'pose-render-checks.json').write_text(json.dumps(evidence, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
