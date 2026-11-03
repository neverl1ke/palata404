"""Real game integration: poses, inventory art, saved outfits and rendering races."""
import hashlib,json,unittest
from pathlib import Path
from tests import test_game as support
ROOT=Path(__file__).resolve().parents[1]
class AnimatedAvatarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): support.GameTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls): support.GameTests.tearDownClass.__func__(cls)
    setUp=support.GameTests.setUp
    tearDown=support.GameTests.tearDown
    load=support.GameTests.load
    def ready(self,pose):
        self.page.wait_for_function('''p=>['character-paperdoll','wardrobe-paperdoll'].every(id=>{const h=document.getElementById(id),s=window.avatarCoreGamePreview?.instances.get(h);return h.dataset.avatarCoreReady==='true'&&s?.engine.pose===p&&!s.running})''',arg=pose)
    def test_exact_sources_and_base_registration(self):
        manifest=json.loads((ROOT/'review/approved-avatar-packages-20261102/integration-manifest.json').read_text())
        revision=json.loads((ROOT/'review/female-arms-approved-20261103/integration-manifest.json').read_text())
        for entry in manifest['exact_files']+revision['exact_files']:
            self.assertEqual(hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(),entry['sha256'])
        for gender in ['male','female']:
            rig=json.loads((ROOT/f'avatar-core/approved/{gender}/resources.json').read_text())['json'][f'rigs/{gender}_rig.json']
            self.assertEqual(hashlib.sha256((ROOT/f'base_{gender}.png').read_bytes()).hexdigest(),rig['source_sha256'])
    def test_poses_breathing_cosmetics_and_saved_weapons(self):
        self.load();self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null)')
        for gender,face,hair in [('male','face-male-new-neutral','hair-m6-mullet'),('female','face-ginger-soft','hair-bob')]:
            self.page.evaluate('([g,f,h])=>{setGender(g);equipPaperDollItem("face",f);equipPaperDollItem("hair",h);setHairColor("white")}',[gender,face,hair])
            for weapon,pose in [(None,'idle'),('gear-aks','rifle')]:
                self.page.evaluate('w=>equipPaperDollItem("weapon",w)',weapon);self.ready(pose)
                evidence=self.page.evaluate('''()=>{const s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')),e=s.engine;e.pause();e.setOptions({transitionMs:0});e.time=0;e.render();const first=e.canvas.toDataURL();e.advance(1000);return {moving:first!==e.canvas.toDataURL(),gender:e.gender,face:e.appearance.layers.some(l=>l.slot==='face'),hair:e.appearance.layers.filter(l=>l.slot==='hair').length,hidden:[...s.host.querySelectorAll('.char-layer')].every(i=>i.style.visibility==='hidden')}}''')
                self.assertTrue(evidence['moving']);self.assertTrue(evidence['face']);self.assertGreater(evidence['hair'],0);self.assertTrue(evidence['hidden']);self.assertEqual(evidence['gender'],gender)
                self.page.locator('.wardrobe-stage').screenshot(path=str(ROOT/'test-results'/f'animated-{gender}-{pose}.png'))
                self.page.evaluate('avatarCoreGamePreview.refresh()')
        self.page.evaluate('equipPaperDollItem("weapon","gear-knife")');self.ready('idle')
        self.assertTrue(self.page.evaluate('selectedPaperDollItem("weapon").avatarPoseUnavailable'))
        self.page.evaluate('equipPaperDollItem("weapon","gear-aks")');self.ready('rifle')
        self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.ready('rifle')
        self.assertEqual(self.page.evaluate('selectedPaperDollItem("weapon").id'),'gear-aks')
        self.page.set_viewport_size({'width':390,'height':844});self.page.evaluate('selectWardrobeCategory("weapons");selectWardrobeSlot("weapon")');self.ready('rifle')
        for weapon in ['gear-knife','gear-aks']:
            self.assertTrue(self.page.locator(f'[data-wardrobe-card="{weapon}"] .weapon-icon-frame img:not(.game-icon)').is_visible())
            self.assertTrue(self.page.locator(f'[data-wardrobe-card="{weapon}"] .weapon-icon-frame img:not(.game-icon)').evaluate('(i)=>i.complete&&i.naturalWidth>0&&i.offsetTop+i.offsetHeight<=i.parentElement.clientHeight'))
        self.page.screenshot(path=str(ROOT/'test-results/animated-weapons-mobile.png'))
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        self.page.evaluate('setPaperDollView("patient")')
        self.page.wait_for_function('document.getElementById("wardrobe-paperdoll").dataset.avatarCoreBlocked==="clothing"')
        self.assertEqual(self.page.evaluate('selectedPaperDollItem("upperBody").id'),'patient-tunic')
        self.assertEqual(self.page.locator('#wardrobe-layer-upper-body-front').evaluate('(i)=>getComputedStyle(i).visibility'),'visible')
        self.page.evaluate('setPaperDollView("combat");equipPaperDollItem("weapon",null)');self.ready('idle')
        self.page.emulate_media(reduced_motion='reduce');self.page.wait_for_function('avatarCoreGamePreview.instances.get(document.getElementById("wardrobe-paperdoll")).engine.paused')
    def test_game_canvas_matches_approved_reference_frames(self):
        import io
        import numpy as np
        from PIL import Image
        review=ROOT/'review/approved-avatar-packages-20261102'
        self.load();self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("face",null);equipPaperDollItem("hair","hair-none");setHairColor("original")')
        for gender in ['male','female']:
            current_review=ROOT/'review/female-arms-approved-20261103' if gender=='female' else review
            self.page.evaluate('g=>setGender(g)',gender)
            for weapon,pose in [(None,'idle'),('gear-aks','rifle')]:
                self.page.evaluate('w=>equipPaperDollItem("weapon",w)',weapon);self.ready(pose)
                actual=self.page.evaluate("""()=>{const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.time=0;e.render();return e.canvas.toDataURL().split(',')[1]}""")
                import base64
                image=Image.open(io.BytesIO(base64.b64decode(actual))).convert('RGBA')
                expected_path=current_review/f'female-{"rifle" if weapon else "no-weapon"}-0.png' if gender=='female' else review/f'{gender}-approved-{"rifle" if weapon else "no-weapon"}.png'
                expected=Image.open(expected_path).convert('RGBA')
                self.assertTrue(np.array_equal(np.array(image),np.array(expected)),f'{gender} {pose} differs from uploaded Lab')
                phase_path=current_review/'render-proof.json' if gender=='female' else review/'archive-renderer-equivalence.json'
                phases=json.loads(phase_path.read_text())['phases']
                for phase in [p for p in phases if p['gender']==gender and p['weapon']==bool(weapon)]:
                    raw=self.page.evaluate("""t=>{const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.time=t;e.render();return e.canvas.toDataURL().split(',')[1]}""",phase['time_ms'])
                    rgba=Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGBA')
                    self.assertEqual(hashlib.sha256(rgba.tobytes()).hexdigest(),phase['rgba_sha256'],f"{gender} {pose} at {phase['time_ms']}ms")
                self.page.set_viewport_size({'width':390,'height':844})
                self.assertTrue(self.page.evaluate("""()=>{const c=document.querySelector('#wardrobe-paperdoll canvas').getBoundingClientRect(),s=document.querySelector('.wardrobe-stage').getBoundingClientRect();return c.left>=s.left-2&&c.right<=s.right+2}"""))
                self.page.locator('.wardrobe-stage').screenshot(path=str(current_review/f'{gender}-game-{"rifle" if weapon else "no-weapon"}.png'))
    def test_stash_art_and_rapid_changes(self):
        self.load();self.page.evaluate('openInventory()')
        self.page.wait_for_function('''()=>[...document.querySelectorAll('#stash-items .weapon-icon-frame img')].length===2&&[...document.querySelectorAll('#stash-items .weapon-icon-frame img')].every(i=>i.complete&&i.naturalWidth>0)''')
        self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);for(let i=0;i<8;i++){setGender(i%2?"male":"female");equipPaperDollItem("weapon",i%2?"gear-knife":"gear-aks")}setGender("female");equipPaperDollItem("weapon","gear-aks")');self.ready('rifle')
        self.assertTrue(self.page.evaluate('''()=>[...avatarCoreGamePreview.instances.values()].every(s=>s.engine.gender==='female'&&s.host.querySelectorAll('canvas').length===1)'''))
        self.page.evaluate('equipPaperDollItem("weapon",null)');self.ready('idle')
