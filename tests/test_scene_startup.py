"""Cold-cache reveal and the real reference card, including its offscreen transition."""
import json
import unittest
from tests import test_game


class SceneStartupTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)

    def setUp(self):
        self.errors=[]
        self.fresh_page()

    def fresh_page(self):
        if hasattr(self,'context'):self.context.close()
        self.context=self.browser.new_context(viewport={'width':1672,'height':941})
        self.context.add_init_script('window.__PALATA_TEST_DIRECT__=true;')
        self.context.route('https://**/*',lambda r:r.abort())
        self.page=self.context.new_page()
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))

    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])

    def ready(self):
        self.page.wait_for_function('document.querySelector(".hospital-hud").dataset.assetsReady==="true" && Number(getComputedStyle(document.querySelector(".hospital-hud")).opacity)>.999')

    def test_room_stays_hidden_until_delayed_background_avatar_and_font_decode(self):
        for pattern in ['**/warm-ward-room.webp','**/base_male.png*','**/TT2020StyleE-Regular.woff*']:
            with self.subTest(resource=pattern):
                # Each navigation is a new cold cache, including font and image caches.
                if self.page.url!='about:blank':self.fresh_page()
                held=[];self.context.route(pattern,lambda r:held.append(r))
                self.page.goto(self.url,wait_until='domcontentloaded')
                self.page.wait_for_function('Number(document.querySelector(".hospital-hud").dataset.assetCount)>10')
                self.assertTrue(held)
                self.assertEqual(self.page.locator('.hospital-hud').get_attribute('data-assets-ready'),'false')
                self.assertEqual(self.page.locator('.hospital-hud').evaluate('e=>Number(getComputedStyle(e).opacity)'),0)
                self.assertTrue(self.page.locator('.hospital-hud').evaluate('e=>e.inert'))
                self.assertTrue(self.page.locator('#scene-loading').is_visible())
                self.context.unroute(pattern)
                for route in held:route.continue_()
                self.ready()
                self.assertFalse(self.page.locator('.hospital-hud').evaluate('e=>e.inert'))
                self.assertEqual(self.page.evaluate('PalataSceneLoading.failedAssets'),[])
                self.assertGreater(int(self.page.locator('.room-shadow-contact').get_attribute('data-sole-samples')),0)
                self.assertFalse(self.page.locator('#character-paperdoll').evaluate('e=>e.hasAttribute("data-avatar-pending")||e.hasAttribute("data-paper-loading")'))

    def test_failed_required_art_keeps_loading_screen_and_retry_restores_the_room(self):
        pattern='**/patient-compact.webp';self.context.route(pattern,lambda r:r.abort())
        self.page.goto(self.url,wait_until='domcontentloaded')
        self.page.locator('#scene-loading button').wait_for(state='visible')
        self.assertEqual(self.page.locator('.hospital-hud').get_attribute('data-assets-ready'),'false')
        self.assertTrue(self.page.locator('.hospital-hud').evaluate('e=>e.inert'))
        self.assertTrue(any('patient-compact.webp' in s for s in self.page.evaluate('PalataSceneLoading.failedAssets')))
        self.context.unroute(pattern);self.page.get_by_role('button',name='Повторить',exact=True).click()
        self.ready();self.assertTrue(self.page.locator('#patient-card').is_visible())

    def test_initial_reveal_also_waits_for_the_animated_avatar_in_both_genders(self):
        for gender in ['male','female']:
            with self.subTest(gender=gender):
                if self.page.url!='about:blank':self.fresh_page()
                state={'schemaVersion':2,'selectedGender':gender,'activeViewMode':'combat',
                       'appearance':{'face':None,'hair':'hair-none'},'patientLoadout':{},'combatLoadout':{}}
                self.context.add_init_script('localStorage.setItem("palata404_paper_doll",'+json.dumps(json.dumps(state))+');')
                self.page.goto(self.url,wait_until='domcontentloaded');self.ready()
                self.assertEqual(self.page.evaluate('paperDollState.selectedGender'),gender)
                self.assertEqual(self.page.locator('#character-paperdoll').get_attribute('data-avatar-core-ready'),'true')
                self.assertFalse(self.page.evaluate('Boolean(avatarCoreGamePreview.instances.get(document.getElementById("character-paperdoll")).running)'))
                self.assertEqual(self.page.locator('#character-paperdoll').get_attribute('data-avatar-pose'),'idle')
                self.assertGreater(int(self.page.locator('.room-shadow-contact').get_attribute('data-sole-samples')),0)

    def test_default_compact_card_slides_offscreen_before_its_layout_changes(self):
        self.page.goto(self.url,wait_until='networkidle');self.ready()
        card=self.page.locator('#patient-card');button=card.locator('.hud-card-toggle')
        self.assertEqual(card.get_attribute('data-card-mode'),'compact')
        rect=card.bounding_box();self.assertLess(rect['y'],100);self.assertLess(rect['height'],rect['width']*.45)
        self.assertEqual(button.get_attribute('aria-expanded'),'false')
        saved=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,paperDollState})')
        self.page.evaluate('''()=>{window.cardFrames=[];const c=document.getElementById('patient-card');const start=performance.now();function sample(){const r=c.getBoundingClientRect();cardFrames.push({t:performance.now()-start,x:r.x,right:r.right,mode:c.dataset.cardMode,motion:c.dataset.cardMotion});if(performance.now()-start<1000)requestAnimationFrame(sample)}sample()}''')
        button.click();self.page.wait_for_function('!PalataHudCard.moving')
        samples=self.page.evaluate('cardFrames')
        self.assertTrue(any(s['x']<-100 and s['mode']=='compact' for s in samples))
        self.assertTrue(any(s['x']<-100 and s['mode']=='full' for s in samples))
        self.assertEqual(card.get_attribute('data-card-mode'),'full')
        self.assertAlmostEqual(card.bounding_box()['width'],rect['width'],delta=1)
        self.assertEqual(button.get_attribute('aria-expanded'),'true')
        self.assertTrue(self.page.locator('.hud-bank-button').is_visible())
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,paperDollState})'),saved)
        self.page.reload(wait_until='networkidle');self.ready()
        self.assertEqual(card.get_attribute('data-card-mode'),'full')
        button.focus();self.page.keyboard.press('Enter');self.page.wait_for_function('!PalataHudCard.moving')
        self.assertEqual(card.get_attribute('data-card-mode'),'compact')
        self.assertEqual(self.page.evaluate('document.activeElement.className'),'hud-card-toggle')

    def test_compact_fields_are_live_unique_and_reduced_motion_switches_immediately(self):
        self.page.goto(self.url,wait_until='networkidle');self.ready()
        self.page.evaluate('stats.madness=46;stats.energy=32;stats.hp=64;stats.silver=634;stats.pills=7;stats.level=10;stats.exp=1066;stats.nextLvlExp=1200;equipPaperDollItem("weapon","gear-aks");updateUI()')
        for selector,text in [('#damage-val','45'),('#hud-health-value','64'),('#silver-val','634'),('#pills-val','7'),('#player-lvl','10'),('#exp-val','1066 / 1200 EXP'),('#hud-exp-percent','88,8%')]:
            self.assertEqual(self.page.locator(selector).count(),1)
            self.assertEqual(self.page.locator(selector).inner_text(),text)
            self.assertTrue(self.page.locator(selector).is_visible())
        for selector,value in [('.hud-compact-sanity',54),('.hud-compact-energy',32)]:
            self.assertEqual(self.page.locator(selector).get_attribute('aria-valuenow'),str(value))
            ratio=self.page.locator(selector).evaluate('e=>e.firstElementChild.getBoundingClientRect().width/e.getBoundingClientRect().width')
            self.assertAlmostEqual(ratio,value/100,delta=.003)
        self.page.emulate_media(reduced_motion='reduce')
        self.page.locator('.hud-card-toggle').click()
        self.assertEqual(self.page.locator('#patient-card').get_attribute('data-card-mode'),'full')
        self.assertFalse(self.page.evaluate('PalataHudCard.moving'))
        self.assertEqual(self.page.locator('#damage-val').inner_text(),'45')
        self.page.locator('.hud-card-toggle').click()
        self.assertEqual(self.page.locator('#patient-card').get_attribute('data-card-mode'),'compact')
        self.assertFalse(self.page.evaluate('PalataHudCard.moving'))


if __name__=='__main__':
    unittest.main()
