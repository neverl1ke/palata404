"""Approved 160 beard fits, independent pigment, and real idle/melee/rifle transitions."""
import hashlib,json,unittest
from pathlib import Path
from tests import test_game as support
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'review/male-facial-hair-approved-20261105'
class BeardAssetTests(unittest.TestCase):
    def test_every_integrated_fit_is_exact_owner_approved_rgba(self):
        from PIL import Image
        manifest=json.loads((REVIEW/'integration-manifest.json').read_text())
        self.assertEqual(len(manifest['files']),160)
        for head in range(1,17):
            approved=json.loads((REVIEW/f'M{head:02}-approval.json').read_text())
            self.assertEqual(len(approved['fits']),10)
            for entry in [e for e in manifest['files'] if e['head']==f'M{head:02}']:
                path=ROOT/entry['path'];digest=hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(digest,entry['sha256'])
                self.assertEqual(digest,next(e['sha256'] for e in approved['fits'] if e['number']==entry['number']))
                with Image.open(path) as image:
                    self.assertEqual(image.size,(941,1672));self.assertEqual(image.mode,'RGBA')
                    self.assertEqual(image.getchannel('A').getextrema(),(0,255))
class BeardWeaponBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):support.GameTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls):support.GameTests.tearDownClass.__func__(cls)
    setUp=support.GameTests.setUp
    tearDown=support.GameTests.tearDown
    load=support.GameTests.load
    def ready(self,pose='idle'):
        self.page.wait_for_function('''p=>[...avatarCoreGamePreview.instances.values()].length===2&&[...avatarCoreGamePreview.instances.values()].every(s=>s.host.dataset.avatarCoreReady==='true'&&!s.canvas.hidden&&s.engine.pose===p&&!s.running)''',arg=pose)
    def start(self):
        self.load();self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("hair","hair-none");equipPaperDollItem("face",null);equipPaperDollItem("weapon",null)');self.ready()
    def test_weapon_cycles_return_to_exact_neutral_body_both_genders(self):
        self.start()
        for gender in ['male','female']:
            self.page.evaluate('g=>{setGender(g);equipPaperDollItem("face",null);equipPaperDollItem("weapon",null)}',gender);self.ready()
            for weapon,pose in [(None,'idle'),('gear-aks','rifle'),(None,'idle'),('gear-knife','melee'),('gear-aks','rifle'),('gear-knife','melee'),(None,'idle')]:
                self.page.evaluate('w=>equipPaperDollItem("weapon",w)',weapon);self.ready(pose)
                result=self.page.evaluate('''async()=>{const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.time=0;e.render();const ctx=e.canvas.getContext('2d'),actual=ctx.getImageData(0,310,941,1362).data;let opaque=0;for(let i=3;i<actual.length;i+=4)if(actual[i])opaque++;
                    const img=new Image();img.src='base_'+e.gender+'.png';await img.decode();const c=document.createElement('canvas');c.width=941;c.height=1672;c.getContext('2d').drawImage(img,0,0);const ref=c.getContext('2d').getImageData(0,310,941,1362).data;let max=0;for(let i=0;i<actual.length;i++)max=Math.max(max,Math.abs(actual[i]-ref[i]));return{opaque,max}}''')
                self.assertGreater(result['opaque'],120000,f'{gender} {pose} lost body')
                if pose=='idle':self.assertLessEqual(result['max'],2,gender+' did not restore approved neutral arms')
            self.page.evaluate('''()=>{for(let i=0;i<10;i++){equipPaperDollItem('weapon','gear-aks');equipPaperDollItem('weapon','gear-knife');equipPaperDollItem('weapon',null)}}''');self.ready()
            self.page.evaluate('equipPaperDollItem("weapon","gear-knife")');self.ready('melee')
            self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.ready('melee')
            self.page.evaluate('equipPaperDollItem("weapon",null)');self.ready()
    def test_beard_palette_per_head_layers_and_persistence(self):
        self.start();self.page.evaluate('setGender("male");equipPaperDollItem("beard","beard-06");setHairColor("ginger");setBeardColor("blue");selectWardrobeCategory("appearance");selectWardrobeSlot("beard")');self.ready()
        self.assertEqual(self.page.locator('[data-wardrobe-card^="beard-"]').count(),10)
        if self.page.locator('[data-palette-toggle]').is_visible():self.page.locator('[data-palette-toggle]').click()
        self.assertEqual(self.page.locator('[data-hair-color]').count(),13)
        self.page.locator('[data-hair-color-group="natural"]').click()
        self.page.locator('[data-hair-color="white"]').click();self.ready()
        self.assertEqual(self.page.evaluate('paperDollState.appearance.hairColor'),'ginger')
        self.assertEqual(self.page.evaluate('paperDollState.appearance.beardColor'),'white')
        self.page.locator('[data-hair-color-group="alternative"]').click()
        self.assertEqual(self.page.locator('[data-hair-color]').count(),13)
        self.page.locator('[data-hair-color="blue"]').click();self.ready()
        entries=json.loads((REVIEW/'integration-manifest.json').read_text())['files']
        actual=self.page.evaluate('''()=>{const before=paperDollState.appearance.face,rows=[];const faces=[null,...PAPER_DOLL_ITEMS.filter(i=>i.slot==='face'&&paperDollItemSupportsGender(i)).map(i=>i.id)];for(const f of faces){paperDollState.appearance.face=f;for(const b of PAPER_DOLL_ITEMS.filter(i=>i.slot==='beard'))rows.push({face:f||'@native',number:Number(b.id.slice(-2)),path:paperDollItemLayers(b,'male')[0].genderVariants.male.split('?')[0]})}paperDollState.appearance.face=before;return rows}''')
        self.assertEqual(len(actual),160)
        self.assertEqual({(r['face'],r['number'],r['path']) for r in actual},{(r['face'],r['number'],r['path']) for r in entries})
        # Full palette preserves the exact alpha, including soft corner cleanup.
        self.assertTrue(self.page.evaluate('''async()=>{const p=paperDollItemLayers(selectedPaperDollItem('beard'),'male')[0].genderVariants.male;const pixels=async s=>{const i=new Image();i.src=s;await i.decode();const c=document.createElement('canvas');c.width=i.width;c.height=i.height;c.getContext('2d').drawImage(i,0,0);return c.getContext('2d').getImageData(0,0,c.width,c.height).data};const original=await pixels(p);for(const color of HAIR_COLORS){const colored=await pixels(await coloredHairSource(p,color.id));for(let i=3;i<original.length;i+=4)if(original[i]!==colored[i])return false}return true}'''))
        self.page.evaluate('setPaperDollView("patient")');self.page.wait_for_function('document.getElementById("wardrobe-paperdoll").dataset.avatarCoreBlocked==="clothing"')
        self.assertEqual(self.page.evaluate('selectedPaperDollItem("beard").id'),'beard-06')
        self.page.wait_for_function('()=>document.getElementById("wardrobe-layer-beard-front")?.complete')
        self.page.evaluate('setPaperDollView("combat");setGender("female")');self.ready()
        self.assertIsNone(self.page.evaluate('selectedPaperDollItem("beard")||null'))
        self.assertFalse(self.page.evaluate('avatarCoreGamePreview.instances.get(document.getElementById("wardrobe-paperdoll")).engine.appearance.layers.some(l=>l.slot==="beard")'))
        self.assertEqual(self.page.locator('[data-wardrobe-slot="beard"]').count(),0)
        self.page.evaluate('setGender("male")');self.ready()
        self.assertEqual(self.page.evaluate('selectedPaperDollItem("beard").id'),'beard-06')
        self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.ready()
        self.assertEqual(self.page.evaluate('paperDollState.appearance.beardColor'),'blue')
        self.assertEqual(self.page.evaluate('selectedPaperDollItem("beard").id'),'beard-06')
        self.page.evaluate('equipPaperDollItem("beard",null)');self.ready()
        self.assertFalse(self.page.evaluate('avatarCoreGamePreview.instances.get(document.getElementById("wardrobe-paperdoll")).engine.appearance.layers.some(l=>l.slot==="beard")'))
    def test_mobile_beard_selection_palette_and_removal(self):
        self.start();self.page.evaluate('setGender("male");selectWardrobeCategory("appearance");selectWardrobeSlot("beard")')
        for width,height in [(390,844),(320,568)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.locator('[data-wardrobe-card="beard-05"]').click()
            self.page.locator('[data-wardrobe-action="beard-05"]').click();self.ready()
            self.assertEqual(self.page.evaluate('selectedPaperDollItem("beard").id'),'beard-05')
            toggle=self.page.locator('[data-palette-toggle]')
            if toggle.get_attribute('aria-expanded')=='false':toggle.click()
            self.page.locator('[data-hair-color-group="natural"]').click()
            self.page.locator('[data-hair-color="gray"]').click();self.ready()
            self.assertEqual(self.page.evaluate('paperDollState.appearance.beardColor'),'gray')
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            self.page.screenshot(path=str(REVIEW/f'beard-mobile-{width}.jpg'),type='jpeg',quality=70)
            self.page.locator('[data-wardrobe-action="beard-05"]').click();self.ready()
            self.assertIsNone(self.page.evaluate('selectedPaperDollItem("beard")||null'))
