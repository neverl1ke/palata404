"""Real game integration: poses, inventory art, saved outfits and rendering races."""
import hashlib,json,unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
from tests import test_game as support
from tests.asset_history import approved_current_hash, approved_female_arms_integration_html
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
            if entry['path'] == 'index.html':
                self.assertEqual(hashlib.sha256(approved_female_arms_integration_html()).hexdigest(),entry['sha256'])
            else:
                self.assertEqual(hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(),approved_current_hash(entry['path'],entry['sha256']),entry['path'])
        class Scripts(HTMLParser):
            def __init__(self, html):
                super().__init__();self.scripts=[];self.feed(html)
            def handle_starttag(self, tag, attrs):
                attrs=dict(attrs)
                if tag=='script' and 'src' in attrs:
                    self.scripts.append((urlsplit(attrs['src']).path,attrs.get('type'),'defer' in attrs))
        original=Scripts(approved_female_arms_integration_html().decode()).scripts
        current=Scripts((ROOT/'index.html').read_text()).scripts
        # New feature scripts are allowed, but every original loader must remain
        # present exactly once, with its module/defer semantics and ordering.
        positions=[]
        for script in original:
            self.assertEqual(current.count(script),1,script)
            positions.append(current.index(script))
        self.assertEqual(positions,sorted(positions))
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
        self.page.evaluate('equipPaperDollItem("weapon","gear-knife")');self.ready('melee')
        self.assertTrue(self.page.evaluate('selectedPaperDollItem("weapon").avatarWeapon'))
        self.page.evaluate('equipPaperDollItem("weapon","gear-aks")');self.ready('rifle')
        self.page.evaluate('typeof applyWardrobeSession === "function" && applyWardrobeSession()');self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.ready('rifle')
        self.assertEqual(self.page.evaluate('selectedPaperDollItem("weapon").id'),'gear-aks')
        self.page.set_viewport_size({'width':390,'height':844});self.page.evaluate('selectWardrobeCategory("weapons");selectWardrobeSlot("weapon")');self.ready('rifle')
        for weapon in ['gear-knife','gear-aks']:
            self.assertTrue(self.page.locator(f'[data-wardrobe-card="{weapon}"] .weapon-icon-frame img:not(.game-icon)').is_visible())
            # Approved rarity cards enlarge the art to 150% of its mount and
            # deliberately allow overhang. Verify that contract, not the old
            # clipped inventory-thumbnail box.
            self.assertTrue(self.page.locator(f'[data-wardrobe-card="{weapon}"] .weapon-icon-frame img:not(.game-icon)').evaluate('''i=>{
                const frame=i.parentElement, box=i.getBoundingClientRect(), artStyle=getComputedStyle(i), mountStyle=getComputedStyle(frame);
                const innerHeight=frame.clientHeight-(artStyle.position==='absolute'?0:parseFloat(mountStyle.paddingTop)+parseFloat(mountStyle.paddingBottom));
                const card=i.closest('[data-wardrobe-card]').getBoundingClientRect();
                return i.complete&&i.naturalWidth>0&&i.naturalHeight>0&&
                    artStyle.objectFit==='contain'&&mountStyle.overflow==='visible'&&
                    Math.abs(box.height/innerHeight-1.5)<.03&&box.width>0&&
                    box.left>=card.left-1&&box.right<=card.right+1&&box.bottom>card.top&&box.top<card.bottom;
            }'''))
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
                # Probe the unchanged approved body without the independently normalized native head.
                self.page.evaluate("async()=>{const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.setOptions({amplitude:1,cycleMs:4000});await e.setAppearance({layers:[],crown:null,bodyMask:null})}")
                actual=self.page.evaluate("""()=>{const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.time=0;e.render();return e.canvas.toDataURL().split(',')[1]}""")
                import base64
                image=Image.open(io.BytesIO(base64.b64decode(actual))).convert('RGBA')
                expected_path=current_review/f'female-{"rifle" if weapon else "no-weapon"}-0.png' if gender=='female' else review/f'{gender}-approved-{"rifle" if weapon else "no-weapon"}.png'
                expected=Image.open(expected_path).convert('RGBA')
                if not weapon:
                    # Compare the approved neutral PNG after the same Canvas
                    # premultiplication; hidden RGB in a source PNG is not visible art.
                    rest=self.page.evaluate('''async([g,w,h])=>{const i=new Image();i.src='base_'+g+'.png';await i.decode();const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').drawImage(i,0,0);return c.toDataURL().split(',')[1]}''',[gender,image.width,image.height])
                    expected=Image.open(io.BytesIO(base64.b64decode(rest))).convert('RGBA')
                self.assertTrue(np.array_equal(np.array(image),np.array(expected)),f'{gender} {pose} differs from uploaded Lab')
                phase_path=current_review/'render-proof.json' if gender=='female' else review/'archive-renderer-equivalence.json'
                phases=json.loads(phase_path.read_text())['phases']
                for phase in [p for p in phases if weapon and p['gender']==gender and p['weapon']==bool(weapon)]:
                    raw=self.page.evaluate("""t=>{const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.time=t;e.render();return e.canvas.toDataURL().split(',')[1]}""",phase['time_ms'])
                    rgba=Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGBA')
                    self.assertEqual(hashlib.sha256(rgba.tobytes()).hexdigest(),phase['rgba_sha256'],f"{gender} {pose} at {phase['time_ms']}ms")
                self.page.set_viewport_size({'width':390,'height':844})
                self.page.wait_for_function("""()=>{const c=document.querySelector('#wardrobe-paperdoll canvas').getBoundingClientRect(),s=document.querySelector('.wardrobe-stage').getBoundingClientRect();return c.width>0&&c.left>=s.left-2&&c.right<=s.right+2}""")
                self.page.locator('.wardrobe-stage').screenshot(path=str(ROOT/'review/male-facial-hair-approved-20261105'/f'{gender}-game-{"rifle" if weapon else "no-weapon"}.png'))
    def test_native_female_head_and_hair_match_static_registered_preview(self):
        import base64,io
        import numpy as np
        from PIL import Image
        self.load();self.page.evaluate('openCustomization();setGender("female");setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("face",null);equipPaperDollItem("hair","hair-none");equipPaperDollItem("weapon",null)');self.ready('idle')
        raw=self.page.evaluate("""()=>{const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.time=0;e.render();return e.canvas.toDataURL().split(',')[1]}""")
        frame=Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGBA');bg=Image.new('RGBA',frame.size,'#f7f4eb');bg.alpha_composite(frame)
        self.page.evaluate("""()=>{const h=document.createElement('div');h.id='native-female-sync';Object.assign(h.style,{position:'fixed',left:0,top:0,width:'941px',height:'1672px',background:'#f7f4eb',zIndex:2147483647});document.body.append(h);renderPaperDollAt(h,'native-sync-')}""")
        self.page.wait_for_function("()=>[...document.querySelectorAll('#native-female-sync img[src]')].every(i=>i.complete&&i.naturalWidth>0&&!i.classList.contains('hidden'))")
        static=Image.open(io.BytesIO(self.page.screenshot(clip={'x':350,'y':0,'width':241,'height':260}))).convert('RGB');actual=bg.crop((350,0,591,260)).convert('RGB')
        error=np.abs(np.array(actual).astype(float)-np.array(static));self.assertLess(error.mean(),.5);self.assertLessEqual(error.max(),2)
        self.assertIsNone(self.page.evaluate('paperDollState.appearance.face'));self.page.locator('#native-female-sync').evaluate('e=>e.remove()')
        self.page.evaluate('equipPaperDollItem("hair","hair-textured-short");setHairColor("blue")');self.ready('idle')
        self.assertTrue(self.page.evaluate("""async()=>{const part=paperDollItemLayers(selectedPaperDollItem('hair'),'female').find(p=>p.id==='front')||selectedPaperDollItem('hair');const fit=femaleHairFitFor('female',null,selectedPaperDollItem('hair').id,part.placementByGender.female);const expected=await fittedFemaleHairSource(part.genderVariants.female,'blue',part.colorReference,fit);const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;return e.appearance.layers.some(l=>l.slot==='hair'&&l.source===expected)}"""))

    def test_stash_art_and_rapid_changes(self):
        self.load();self.page.evaluate('openInventory()')
        self.page.wait_for_function('''()=>[...document.querySelectorAll('#stash-items .weapon-icon-frame img')].length===5&&[...document.querySelectorAll('#stash-items .weapon-icon-frame img')].every(i=>i.complete&&i.naturalWidth>0)''')
        self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);for(let i=0;i<8;i++){setGender(i%2?"male":"female");equipPaperDollItem("weapon",i%2?"gear-knife":"gear-aks")}setGender("female");equipPaperDollItem("weapon","gear-aks")');self.ready('rifle')
        self.assertTrue(self.page.evaluate('''()=>[...avatarCoreGamePreview.instances.values()].every(s=>s.engine.gender==='female'&&s.host.querySelectorAll('canvas').length===1)'''))
        self.page.evaluate('equipPaperDollItem("weapon",null)');self.ready('idle')

    def test_stronger_faster_breathing_for_both_genders(self):
        self.load();self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null)')
        for gender in ['male','female']:
            self.page.evaluate('g=>setGender(g)',gender)
            for weapon,pose in [(None,'idle'),('gear-aks','rifle')]:
                self.page.evaluate('w=>equipPaperDollItem("weapon",w)',weapon);self.ready(pose)
                result=self.page.evaluate("""async()=>{
                    const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;
                    e.pause(); const defaults={amplitude:e.options.amplitude,cycleMs:e.options.cycleMs};
                    const frame=(time,opts)=>{e.setOptions(opts);e.time=time;e.render();return new Uint8ClampedArray(e.canvas.getContext('2d').getImageData(0,0,e.width,1672).data)};
                    const rest=frame(0,defaults),peak=frame(900,defaults),closed=frame(3600,defaults);
                    const samePhase=frame(1000,{amplitude:1.25,cycleMs:4000}),oldPeak=frame(1000,{amplitude:1,cycleMs:4000});
                    const error=(a,b)=>a.reduce((n,v,i)=>n+Math.abs(v-b[i]),0)/a.length;
                    const female=await import('./avatar-core/approved/female-scene.mjs?v=breathing-20261104');
                    const amplitudeRatio=female.breathAt(900,defaults)/female.breathAt(1000);
                    e.setOptions(defaults);
                    return {defaults,moving:error(rest,peak),closure:error(rest,closed),samePhase:error(peak,samePhase),stronger:error(peak,oldPeak),amplitudeRatio};
                }""")
                self.assertEqual(result['defaults'],{'amplitude':1.25,'cycleMs':3600})
                self.assertGreater(result['moving'],0);self.assertGreater(result['stronger'],0)
                self.assertLess(result['closure'],.01);self.assertLess(result['samePhase'],.01)
                self.assertAlmostEqual(result['amplitudeRatio'],1.25)
            self.page.evaluate('setPaperDollView("patient")')
            self.page.wait_for_function('document.getElementById("wardrobe-paperdoll").classList.contains("avatar-clothed-breathing")')
            self.assertEqual(self.page.locator('#wardrobe-paperdoll').evaluate('(e)=>getComputedStyle(e).animationDuration'),'3.6s')
            self.page.evaluate('setPaperDollView("combat");equipPaperDollItem("upperBody",null)')
        self.page.emulate_media(reduced_motion='reduce')
        self.page.wait_for_function('avatarCoreGamePreview.instances.get(document.getElementById("wardrobe-paperdoll")).engine.paused')
