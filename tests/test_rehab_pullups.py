"""Real room entry, click-powered lift, durable completion and cancellation."""
from pathlib import Path
import unittest
from tests import test_game
OUT=Path(__file__).resolve().parents[1]/'test-results/level-rehab/pullups-live';OUT.mkdir(parents=True,exist_ok=True)
class RehabPullupTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
    setUp=test_game.GameTests.setUp
    tearDown=test_game.GameTests.tearDown
    load=test_game.GameTests.load
    def gym(self):
        self.page.locator('#location-card-box').click();self.page.locator('.quest-map-pin[data-room="gym"]').dblclick(delay=40)
        self.page.wait_for_function('document.querySelector("[data-scene-room=gym]")?.dataset.rehabRenderer==="webgl"')
        self.page.locator('[data-rehab-equipment=pullup]').click()
        self.page.wait_for_function('document.querySelector(".rehab-pullups")?.dataset.pullupReady==="true"')
    def seed_energy(self):
        self.page.evaluate('stats.energy=100;stats.maxEnergy=100;saveGameProgress()')
    def tap(self,interval=100):
        # The view itself is stationary. Locator.click waits for two render
        # frames and turns a rapid cadence into slow clicks on a busy runner.
        box=self.page.locator('[data-pullup-view]').bounding_box()
        self.page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
        if getattr(self,'use_clock',False):self.page.clock.run_for(interval)
        else:self.page.wait_for_timeout(interval)
    def test_slowing_or_stopping_falls_without_a_rep_and_peak_descends_immediately(self):
        self.load();self.seed_energy();self.gym();self.page.clock.install();self.page.clock.pause_at((self.page.evaluate('Date.now()')+100)/1000);self.use_clock=True;self.page.locator('[data-pullup-start]').click()
        for i in range(30):
            self.tap()
            if float(self.page.locator('.rehab-pullups').get_attribute('data-pullup-lift'))>.45:break
        self.assertGreater(float(self.page.locator('.rehab-pullups').get_attribute('data-pullup-lift')),.45)
        self.page.clock.run_for(280)
        self.assertEqual(self.page.locator('.rehab-pullups').get_attribute('data-pullup-motion'),'down')
        height=float(self.page.locator('.rehab-pullups').get_attribute('data-pullup-lift'))
        self.tap(interval=350)
        self.assertLess(float(self.page.locator('.rehab-pullups').get_attribute('data-pullup-lift')),height)
        self.assertEqual(self.page.locator('.rehab-pullups').get_attribute('data-pullup-reps'),'0')
        for i in range(45):
            self.tap()
            if self.page.locator('.rehab-pullups').get_attribute('data-pullup-phase')=='down':break
        self.assertEqual(self.page.locator('.rehab-pullups').get_attribute('data-pullup-reps'),'1')
        self.assertEqual(self.page.locator('.rehab-pullups').get_attribute('data-pullup-phase'),'down')
        top=float(self.page.locator('.rehab-pullups').get_attribute('data-pullup-lift'));self.page.clock.run_for(80)
        self.assertLess(float(self.page.locator('.rehab-pullups').get_attribute('data-pullup-lift')),top)
        self.page.clock.run_for(650)
        self.assertEqual(float(self.page.locator('.rehab-pullups').get_attribute('data-pullup-lift')),0)
        self.assertEqual(self.page.evaluate('stats.energy'),100)
    def test_both_modes_lift_moves_scene_down_and_cancellation_costs_nothing(self):
        self.load();self.seed_energy()
        for mode in ['patient','trip']:
            if mode=='trip':
                self.page.locator('.quest-room-tools button').first.click();self.page.locator('#map-modal .btn-close-map').click();self.page.locator('.room-trip-switch').click()
            self.gym();self.page.screenshot(path=str(OUT/(mode+'-hanging.png')))
            self.assertIn('pullup-'+mode+'.png',self.page.locator('.pullup-main').get_attribute('src'))
            self.page.locator('[data-pullup-start]').click()
            for i in range(25):
                self.tap()
                if float(self.page.locator('.rehab-pullups').get_attribute('data-pullup-lift'))>.35:break
            self.assertGreater(float(self.page.locator('.rehab-pullups').get_attribute('data-pullup-lift')),.35)
            self.assertGreater(self.page.locator('.pullup-world').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).m42'),0)
            self.page.screenshot(path=str(OUT/(mode+'-rising.png')))
            self.assertEqual(self.page.evaluate('stats.energy'),100)
            self.page.keyboard.press('Escape');self.page.wait_for_timeout(250)
            self.assertEqual(self.page.evaluate('stats.energy'),100)
            self.assertEqual(self.page.evaluate('PalataRehabRules.normalize(stats.rehabTraining).pullup.completed'),0)
    def test_click_set_grants_one_durable_rank_then_cooldown_blocks_replay(self):
        self.load();self.seed_energy();self.page.evaluate('stats.rehabTraining=PalataRehabRules.normalize({pullup:{completed:9}});saveGameProgress()');self.gym()
        # Exercise cadence, not host CPU load: real pointer input at 100 ms
        # intervals under the browser clock, including the automatic descent.
        self.page.clock.install();self.page.clock.pause_at((self.page.evaluate('Date.now()')+100)/1000)
        self.page.locator('[data-pullup-start]').click()
        box=self.page.locator('[data-pullup-view]').bounding_box()
        for i in range(180):
            self.page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2);self.page.clock.run_for(100)
            if self.page.evaluate('stats.rehabTraining.pullup.completed')==10:break
        self.assertEqual(self.page.evaluate('stats.rehabTraining.pullup.completed'),10)
        self.assertEqual(self.page.evaluate('stats.energy'),90)
        self.assertEqual(self.page.evaluate('PalataRehabRules.bonuses(stats.rehabTraining).damage'),1)
        self.assertEqual(self.page.locator('.rehab-pullups').get_attribute('data-pullup-reps'),'5')
        self.page.clock.run_for(700);self.page.clock.resume()
        self.page.screenshot(path=str(OUT/'completed.png'))
        self.page.wait_for_function('!document.querySelector("[data-pullup-start]").disabled')
        self.page.locator('[data-pullup-start]').click();self.page.wait_for_timeout(200)
        self.assertEqual(self.page.evaluate('stats.rehabTraining.pullup.completed'),10);self.assertEqual(self.page.evaluate('stats.energy'),90)
        self.page.locator('[data-pullup-back]').click();self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('stats.rehabTraining.pullup.completed'),10);self.assertEqual(self.page.evaluate('stats.energy'),90)
    def test_no_timer_only_completion_keyboard_mobile_and_missing_art(self):
        self.load();self.seed_energy();self.gym();self.page.locator('[data-pullup-start]').click();self.page.wait_for_timeout(12500)
        self.assertEqual(self.page.evaluate('PalataRehabRules.normalize(stats.rehabTraining).pullup.completed'),0)
        self.assertEqual(self.page.evaluate('stats.energy'),100)
        self.page.set_viewport_size({'width':390,'height':844});self.page.emulate_media(reduced_motion='reduce')
        self.page.locator('[data-pullup-view]').press('Space');self.page.wait_for_timeout(250)
        self.assertEqual(self.page.locator('.rehab-pullups').get_attribute('data-pullup-clicks'),'1')
        self.assertEqual(self.page.locator('.pullup-main').evaluate('e=>getComputedStyle(e).transform'),'none')
        self.page.screenshot(path=str(OUT/'phone.png'));self.page.keyboard.press('Escape')
        self.page.route('**/assets/rehabilitation/pullup-patient.png',lambda r:r.abort())
        self.page.reload(wait_until='networkidle')
        self.page.wait_for_function('document.querySelector(".hospital-hud")?.dataset.assetsReady==="true"')
        self.page.locator('#scene-loading').wait_for(state='hidden')
        self.page.locator('#location-card-box').click();self.page.locator('.quest-map-pin[data-room="gym"]').dblclick(delay=40)
        self.page.wait_for_function('document.querySelector("[data-scene-room=gym]")?.dataset.rehabRenderer==="webgl"')
        self.page.locator('[data-rehab-equipment=pullup]').click()
        self.page.wait_for_function('document.querySelector(".rehab-pullups").dataset.pullupReady==="error"')
        self.assertTrue(self.page.locator('[data-pullup-start]').is_disabled());self.page.locator('[data-pullup-back]').click()
        self.assertEqual(self.page.evaluate('stats.energy'),100)
