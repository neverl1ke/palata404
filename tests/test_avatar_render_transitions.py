"""Pose-specific shoulder masks, hair occlusion and complete-frame appearance swaps."""
import json,time,unittest
from pathlib import Path
from tests import test_beards_weapons as support
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'review/avatar-render-fixes-20261105'
class AvatarRenderTransitions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):support.BeardWeaponBrowserTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls):support.BeardWeaponBrowserTests.tearDownClass.__func__(cls)
    setUp=support.BeardWeaponBrowserTests.setUp
    tearDown=support.BeardWeaponBrowserTests.tearDown
    load=support.BeardWeaponBrowserTests.load
    ready=support.BeardWeaponBrowserTests.ready
    start=support.BeardWeaponBrowserTests.start
    def test_all_female_rifle_heads_preserve_the_original_trapezius_coverage(self):
        self.page.emulate_media(reduced_motion='reduce');self.start()
        self.page.evaluate('setGender("female");equipPaperDollItem("weapon","gear-aks")');self.ready('rifle')
        faces=self.page.evaluate('[null,...PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i)).map(i=>i.id)]')
        rows=[]
        for face in faces:
            self.page.evaluate('f=>equipPaperDollItem("face",f)',face);self.ready('rifle')
            lost=self.page.evaluate('''()=>{const s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')),e=s.engine;e.pause();e.time=0;e.render();const a=e.scene.canvas.getContext('2d').getImageData(260,260,420,90).data,b=s.canvas.getContext('2d').getImageData(260,260,420,90).data;let n=0;for(let i=3;i<a.length;i+=4)if(a[i]>200&&b[i]<a[i]-2)n++;return n}''')
            self.assertEqual(lost,0,face);rows.append({'face':face,'lost_shoulder_pixels':lost})
        (REVIEW/'shoulder-coverage.json').write_text(json.dumps(rows,indent=2)+'\n')
    def test_front_hair_covers_beard_in_canvas_and_static_layers(self):
        self.page.emulate_media(reduced_motion='reduce');self.start();self.page.evaluate('setGender("male");equipPaperDollItem("hair","hair-shoulder-length");equipPaperDollItem("beard","beard-10")');self.ready()
        result=self.page.evaluate('''()=>{const s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')),e=s.engine;e.pause();e.time=0;e.render();const h=e.appearance.layers.find(l=>l.slot==='hair'&&l.order>=9&&l.recolor!==false),b=e.appearance.layers.find(l=>l.slot==='beard');const pixels=i=>{const c=document.createElement('canvas');c.width=941;c.height=1672;c.getContext('2d').drawImage(i,0,0);return c.getContext('2d').getImageData(0,0,941,1672).data},hp=pixels(h.bitmap),bp=pixels(b.bitmap),actual=s.canvas.getContext('2d').getImageData(0,0,941,1672).data;let found=0,max=0;for(let i=0;i<hp.length;i+=4)if(hp[i+3]===255&&bp[i+3]===255&&Math.abs(hp[i]-bp[i])+Math.abs(hp[i+1]-bp[i+1])+Math.abs(hp[i+2]-bp[i+2])>30){found++;for(let k=0;k<3;k++)max=Math.max(max,Math.abs(hp[i+k]-actual[i+k]))}return{hair:h.order,beard:b.order,found,max}}''')
        self.assertLess(result['beard'],result['hair']);self.assertGreater(result['found'],0);self.assertLessEqual(result['max'],2)
        self.page.evaluate('setPaperDollView("patient")');self.page.wait_for_function('document.getElementById("wardrobe-paperdoll").dataset.avatarCoreBlocked==="clothing"&&!document.getElementById("wardrobe-paperdoll").hasAttribute("data-paper-loading")')
        self.assertTrue(self.page.evaluate('Number(getComputedStyle(document.getElementById("wardrobe-layer-beard-front")).zIndex)<Number(getComputedStyle(document.getElementById("wardrobe-layer-hair")).zIndex)'))
    def trace(self):
        self.page.evaluate('''()=>{window.frameSamples=[];window.tracing=true;const c=document.createElement('canvas');c.width=40;c.height=72;const x=c.getContext('2d');const tick=()=>{const h=document.getElementById('wardrobe-paperdoll'),s=avatarCoreGamePreview.instances.get(h);if(s&&!s.canvas.hidden){x.clearRect(0,0,40,72);x.drawImage(s.canvas,0,0,s.canvas.width,1672,0,0,40,72);const d=x.getImageData(0,0,40,72).data;let v=2166136261;for(let i=0;i<d.length;i++)v=Math.imul(v^d[i],16777619);frameSamples.push(v>>>0)}if(tracing)requestAnimationFrame(tick)};tick()}''')
    def test_delayed_gender_head_and_hair_swap_only_presents_complete_frames(self):
        self.page.emulate_media(reduced_motion='reduce');self.start();self.trace()
        def delayed(route):
            time.sleep(.12);route.continue_()
        self.page.route('**/faces/**',delayed);self.page.route('**/hair/**',delayed)
        self.page.evaluate('setGender("female");equipPaperDollItem("face","face-asian");equipPaperDollItem("hair","hair-female-braids");equipPaperDollItem("weapon","gear-aks")');self.ready('rifle')
        self.page.wait_for_timeout(100)
        values=self.page.evaluate('tracing=false;[...new Set(frameSamples)]')
        self.assertEqual(len(values),2,'Intermediate default body, head or pose was presented')
        self.assertTrue(self.page.evaluate('''()=>[...avatarCoreGamePreview.instances.values()].every(s=>!s.canvas.hidden&&s.engine.gender==='female'&&!s.host.querySelector('.paper-doll-frozen')&&!s.host.hasAttribute('data-avatar-pending')&&!s.host.hasAttribute('data-paper-loading'))'''))
    def test_cold_reload_never_paints_the_default_avatar(self):
        self.page.emulate_media(reduced_motion='reduce');self.start();self.page.evaluate('setGender("female");equipPaperDollItem("face","face-asian");equipPaperDollItem("hair","hair-female-braids");equipPaperDollItem("weapon","gear-aks")');self.ready('rifle')
        self.context.add_init_script('''window.bootFrames=[];const c=document.createElement('canvas');c.width=40;c.height=72;const x=c.getContext('2d');const tick=()=>{const h=document.getElementById('character-paperdoll');if(h){const a=h.querySelector('canvas.avatar-core-wardrobe-preview');if(a&&!a.hidden){x.clearRect(0,0,40,72);x.drawImage(a,0,0,a.width,1672,0,0,40,72);const d=x.getImageData(0,0,40,72).data;let v=2166136261;for(let i=0;i<d.length;i++)v=Math.imul(v^d[i],16777619);bootFrames.push(v>>>0)}else{const visible=[...h.querySelectorAll(':scope > .char-layer')].some(i=>i.getAttribute('src')&&!i.classList.contains('hidden')&&getComputedStyle(i).visibility!=='hidden');if(visible)bootFrames.push('partial-dom')}}requestAnimationFrame(tick)};requestAnimationFrame(tick);''')
        self.page.route('**/faces/**',lambda route:(time.sleep(.12),route.continue_()))
        self.page.evaluate('typeof applyWardrobeSession === "function" && applyWardrobeSession()');self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.ready('rifle');self.page.wait_for_timeout(100)
        self.assertEqual(self.page.evaluate('[...new Set(bootFrames)].length'),1)
        self.assertNotIn('partial-dom',self.page.evaluate('bootFrames'))
        self.assertFalse(self.page.evaluate('document.getElementById("character-paperdoll").hasAttribute("data-avatar-pending")'))
        self.assertEqual(self.page.locator('#layer-body').get_attribute('src'),'base_female.png?v=a27b499c')
    def test_static_outfit_waits_for_head_hair_and_body_mask_together(self):
        self.page.emulate_media(reduced_motion='reduce');self.load();self.page.evaluate('openCustomization();setGender("female");equipPaperDollItem("face",null);equipPaperDollItem("hair","hair-none")')
        self.page.wait_for_function('document.getElementById("wardrobe-paperdoll").dataset.avatarCoreBlocked==="clothing"&&!document.getElementById("wardrobe-paperdoll").hasAttribute("data-paper-loading")')
        self.page.wait_for_function('getComputedStyle(document.getElementById("wardrobe-layer-body")).visibility==="visible"&&!document.getElementById("wardrobe-layer-body").classList.contains("hidden")')
        self.page.wait_for_function('!document.getElementById("wardrobe-paperdoll").querySelector(".paper-doll-frozen")');self.page.route('**/faces/**',lambda route:(time.sleep(.15),route.continue_()))
        self.page.evaluate("""()=>{window.staticFrames=[];window.staticTracing=true;window.sampleStaticFrame=()=>{const h=document.getElementById('wardrobe-paperdoll'),f=h.querySelector('.paper-doll-frozen'),images=f?[...f.querySelectorAll('img')]:[...h.querySelectorAll(':scope > .char-layer')].filter(i=>!i.classList.contains('hidden')&&getComputedStyle(i).visibility!=='hidden');staticFrames.push(images.map(i=>i.getAttribute('src')).filter(Boolean).sort().join('|'))};const tick=()=>{sampleStaticFrame();if(staticTracing)requestAnimationFrame(tick)};tick();equipPaperDollItem('face','face-asian');equipPaperDollItem('hair','hair-female-curls')}""")
        self.page.wait_for_function('!document.getElementById("wardrobe-paperdoll").hasAttribute("data-paper-loading")');self.page.wait_for_timeout(100)
        self.page.wait_for_function('!document.getElementById("wardrobe-paperdoll").querySelector(".paper-doll-frozen")');self.assertEqual(self.page.evaluate('staticTracing=false;sampleStaticFrame();new Set(staticFrames).size'),2)
