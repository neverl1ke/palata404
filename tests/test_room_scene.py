"""Room interactions use the real save, avatar renderer and existing dialogs."""
import io
import unittest
from pathlib import Path

from PIL import Image, ImageStat
from tests import test_game


class RoomSceneTests(unittest.TestCase):
    setUpClass = classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(test_game.GameTests.tearDownClass.__func__)

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1672, 'height': 941})
        self.context.add_init_script('window.__PALATA_TEST_DIRECT__=true;')
        self.context.route('https://**/*', lambda route: route.abort())
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(self.url, wait_until='networkidle')
        self.page.evaluate('document.fonts.ready')
        self.page.evaluate('document.getElementById("character-paperdoll").paperDollReady')
        self.page.wait_for_function('Number(document.querySelector(".room-shadow-contact").dataset.soleSamples)>40')

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def freeze(self):
        self.page.evaluate('document.getAnimations().forEach(a=>{a.pause();a.currentTime=0})')

    def seek(self, name, time):
        self.page.evaluate('([name,time])=>{for(const a of document.getAnimations())if(a.animationName===name){a.pause();a.currentTime=time}}', [name, time])
        self.page.wait_for_timeout(80)

    @staticmethod
    def rgb(data, rect):
        return ImageStat.Stat(Image.open(io.BytesIO(data)).convert('RGB').crop(rect)).mean

    def test_soft_rare_flicker_keeps_the_bulb_lit_and_night_outside(self):
        self.freeze()
        bright = self.page.screenshot()
        avatar = self.page.locator('.room-shadow-cast canvas').evaluate('e=>e.toDataURL()')
        values = self.page.locator('.hospital-hud').evaluate('''e=>{
            const a=e.getAnimations().find(a=>a.animationName==='room-light-supply');
            const values=[];for(let t=0;t<61000;t+=100){a.currentTime=t;values.push(Number(getComputedStyle(e).getPropertyValue('--room-light')))}
            a.currentTime=0;return values;
        }''')
        self.assertGreaterEqual(min(values), .68)
        self.assertLess(sum(v < .999 for v in values)/len(values), .12)
        self.seek('room-light-supply', 3904)
        dim = self.page.screenshot()
        for rect in [(897,291,941,335), (1071,178,1100,220), (828,105,848,119)]:
            ratio = sum(self.rgb(dim, rect))/sum(self.rgb(bright, rect))
            self.assertGreater(ratio, .77)
            self.assertLess(ratio, .98)
        bulb = self.rgb(dim, (828,105,848,119))
        self.assertGreater(bulb[0]-bulb[2], 18)  # Warm emitter, no gray semicircle.
        self.assertGreater(sum(bulb)/3, 120)
        self.assertEqual(self.page.locator('.room-shadow-cast canvas').evaluate('e=>e.toDataURL()'), avatar)
        self.seek('room-light-supply', 0)
        self.seek('room-night-cycle', 0)
        dusk = sum(self.rgb(self.page.screenshot(), (709,238,737,260)))/3
        self.seek('room-night-cycle', 36000)
        outside = self.rgb(self.page.screenshot(), (709,238,737,260))
        self.assertLess(sum(outside)/3, dusk*.55)
        self.assertGreater(sum(outside)/3, 30)
        self.assertLess(max(outside)-min(outside), 28)
        self.seek('room-night-cycle', 72000)
        returned = sum(self.rgb(self.page.screenshot(), (709,238,737,260)))/3
        self.assertAlmostEqual(returned, dusk, delta=3)
        light = self.page.locator('.room-distant-left-low')
        self.seek('room-distant-switch', 0)
        before = float(light.evaluate('e=>getComputedStyle(e).opacity'))
        self.seek('room-distant-switch', 26000)
        self.assertGreater(abs(float(light.evaluate('e=>getComputedStyle(e).opacity'))-before), .5)

    def test_contact_shadow_supports_heel_and_toes_for_both_avatars(self):
        self.freeze()
        out = Path('test-results/hospital-room'); out.mkdir(parents=True, exist_ok=True)
        hashes = []
        for gender in ['male', 'female']:
            self.page.evaluate('g=>{setGender(g);updateUI();PalataRoomShadows.refresh()}', gender)
            self.page.evaluate('document.getElementById("character-paperdoll").paperDollReady')
            self.page.wait_for_timeout(250)
            contact = self.page.locator('.room-shadow-contact')
            self.assertGreater(int(contact.get_attribute('data-sole-samples')), 40)
            self.assertGreater(int(contact.get_attribute('data-sole-depth')), 8)
            self.assertEqual(contact.locator('canvas').evaluate('e=>getComputedStyle(e).transform'), 'none')
            self.assertIn('matrix3d', self.page.locator('.room-shadow-cast canvas').evaluate('e=>getComputedStyle(e).transform'))
            hashes.append(contact.locator('canvas').evaluate('e=>e.toDataURL()'))
            self.page.screenshot(path=str(out/f'{gender}.png'))
        self.assertNotEqual(*hashes)

    def test_circle_hover_and_all_task_links_use_the_same_read_only_dialog(self):
        self.freeze()
        switch = self.page.locator('.room-trip-switch')
        art = self.page.locator('.room-switch-art')
        plate_filter = art.evaluate('e=>getComputedStyle(e).filter')
        switch.hover(); self.page.wait_for_timeout(240)
        self.assertEqual(art.evaluate('e=>getComputedStyle(e).filter'), plate_filter)
        self.assertGreater(float(art.evaluate('e=>getComputedStyle(e,"::after").opacity')), .95)
        state = self.page.evaluate('JSON.stringify({stats,inventory,paperDollState})')
        action = self.page.locator('.room-tasks-action')
        action.hover(); self.page.wait_for_timeout(360)
        self.assertGreater(float(self.page.locator('.room-task-corner').evaluate('e=>getComputedStyle(e).opacity')), .95)
        for entry in [action, self.page.locator('.hud-task'), self.page.locator('[data-nav-modal="tasks-modal"]')]:
            entry.click()
            self.assertTrue(self.page.locator('#tasks-modal').is_visible())
            self.assertIn('Задания в разработке', self.page.locator('#tasks-modal').inner_text())
            self.page.keyboard.press('Escape')
            self.assertTrue(self.page.locator('#tasks-modal').is_hidden())
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,paperDollState})'), state)

    def test_door_closes_once_and_cabinet_reveals_the_real_wardrobe_after_both_leaves(self):
        for action, assembly, modal, close in [('.room-door-action','.room-door-assembly','#map-modal','toggleMapModal(false)'), ('.room-cabinet-action','.room-cabinet-assembly','#custom-modal','closeCustomization()')]:
            before = self.page.evaluate('JSON.stringify({inventory,paperDollState})')
            self.page.locator(action).click(); self.page.wait_for_timeout(100)
            self.assertTrue(self.page.locator(modal).is_hidden())
            if modal == '#custom-modal':
                self.assertEqual(self.page.locator('.room-cabinet-door-back').count(), 2)
                self.assertEqual(self.page.locator('.room-handle-grip').count(), 0)
                self.assertIn('original-handle-left.svg', self.page.locator('.room-cabinet-handle .room-handle-face').first.get_attribute('src'))
                self.assertIn('cabinet-inner-right.webp', self.page.locator('.room-cabinet-leaf-left .room-cabinet-door-back').evaluate('e=>getComputedStyle(e).backgroundImage'))
                self.assertEqual(self.page.locator('.room-cabinet-metal-return').count(), 8)
                self.assertEqual(self.page.locator('.room-cabinet-leaf-right').evaluate('e=>getComputedStyle(e,"::after").content'), 'none')
                self.assertGreater(self.page.locator('.room-handle-face').first.evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).m43'), 0)
                self.assertNotEqual(self.page.locator('.room-cabinet-leaf-left').evaluate('e=>getComputedStyle(e).transform'), 'none')
                self.assertFalse(self.page.evaluate('PalataRoom.openDoor()'))
            self.page.locator(modal).wait_for(state='visible')
            if modal == '#custom-modal':
                self.assertTrue(self.page.evaluate('Boolean(wardrobeSession)'))
                # Both doors pass 90 degrees, showing their inner metal surface.
                self.assertLess(self.page.locator('.room-cabinet-leaf-left').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).m11'), 0)
                self.assertLess(self.page.locator('.room-cabinet-leaf-right').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).m11'), 0)
            self.page.evaluate(close); self.page.wait_for_timeout(160)
            self.assertEqual(self.page.locator(assembly).get_attribute('data-state'), 'closing')
            self.assertTrue(self.page.locator(assembly).evaluate('e=>e.classList.contains("is-revealed")'))
            self.page.wait_for_function('s=>document.querySelector(s).dataset.state==="closed"', arg=assembly)
            self.assertFalse(self.page.locator(assembly).evaluate('e=>e.classList.contains("is-revealed")'))
            self.assertEqual(self.page.evaluate('JSON.stringify({inventory,paperDollState})'), before)

    def test_hover_opens_a_small_gap_and_presses_only_the_door_lever(self):
        self.freeze()
        for action, assembly, modal in [('.room-door-action','.room-door-assembly','#map-modal'),('.room-cabinet-action','.room-cabinet-assembly','#custom-modal')]:
            self.page.locator(action).hover(); self.page.wait_for_timeout(720)
            self.assertEqual(self.page.locator(assembly).get_attribute('data-state'), 'closed')
            self.assertTrue(self.page.locator(assembly).evaluate('e=>e.classList.contains("is-peeking")'))
            self.assertTrue(self.page.locator(modal).is_hidden())
            self.page.mouse.move(700,730); self.page.wait_for_timeout(1350)
            self.assertFalse(self.page.locator(assembly).evaluate('e=>e.classList.contains("is-revealed")'))
        self.page.locator('.room-door-action').hover(); self.page.wait_for_timeout(720)
        self.assertGreater(self.page.locator('.room-door-handle').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).b'), .1)
        self.page.locator('.room-door-action').click();self.page.locator('#map-modal').wait_for(state='visible')
        self.assertTrue(self.page.locator('.room-door-assembly').evaluate('e=>e.classList.contains("is-handle-pressed")'))
        self.page.evaluate('toggleMapModal(false)')
        self.page.wait_for_function('document.querySelector(".room-door-assembly").dataset.state==="closed"')
        self.page.wait_for_timeout(200)
        self.assertAlmostEqual(self.page.locator('.room-door-handle').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).b'),0,delta=.001)
        for selector in ['.room-corridor-scene','.room-corridor-sight']:
            self.assertIn('room-corridor.webp',self.page.locator(selector).evaluate('e=>getComputedStyle(e).backgroundImage'))
            self.assertIn('blur(',self.page.locator(selector).evaluate('e=>getComputedStyle(e).filter'))

    def test_contacts_visit_all_glass_and_steps_appear_in_order(self):
        self.freeze()
        for surface,count in [(0,12),(1,12),(2,6)]:
            positions=self.page.evaluate('([surface,count])=>Array.from({length:count},()=>PalataAtmosphere.showContact(surface).slot)',[surface,count])
            self.assertEqual(len(set(positions)),count)
        self.assertEqual(self.page.locator('.room-window-left .room-glass-mark').count(),12)
        self.assertEqual(self.page.locator('.room-window-right .room-glass-mark').count(),12)
        self.assertEqual(self.page.locator('.room-door-glass .room-glass-mark').count(),6)
        self.seek('room-wet-step',8500)
        steps=self.page.locator('.room-floor-print')
        self.assertGreater(float(steps.first.evaluate('e=>getComputedStyle(e).opacity')),.2)
        self.assertEqual(float(steps.last.evaluate('e=>getComputedStyle(e).opacity')),0)
        self.seek('room-wet-step',12500)
        self.assertGreater(float(steps.last.evaluate('e=>getComputedStyle(e).opacity')),.2)
        self.seek('room-wet-step',35000)
        self.assertEqual(float(steps.first.evaluate('e=>getComputedStyle(e).opacity')),0)

    def test_metal_returns_match_the_registered_door_contours(self):
        returns=self.page.locator('.room-cabinet-leaf-right .room-cabinet-metal-return')
        self.assertEqual(returns.count(),4)
        # The free edge runs from y9 to y453, rather than the full 465px rectangle.
        edge=returns.nth(3).evaluate('e=>{const m=new DOMMatrix(getComputedStyle(e).transform);const l=parseFloat(e.style.width);return {start:m.m42,end:m.m42+m.m12*l,depth:parseFloat(e.style.height)}}')
        self.assertAlmostEqual(edge['start'],453,delta=.6)
        self.assertAlmostEqual(edge['end'],9,delta=.6)
        self.assertAlmostEqual(edge['depth'],4,delta=.02)
        self.assertEqual(self.page.locator('.room-handle-side').count(),156)
        self.assertEqual(self.page.locator('.room-cabinet-handle').first.evaluate('e=>getComputedStyle(e).transform'),'none')
        for name,time in [('room-curtain-draft',9000),('room-robe-draft',12500),('room-bag-draft',10000)]:
            self.seek(name,time)
        for selector in ['.room-moving-curtain','.room-moving-robe','.room-moving-bag']:
            self.assertNotEqual(self.page.locator(selector).evaluate('e=>getComputedStyle(e).transform'),'none')

    def test_trip_is_real_and_entrances_honor_reduced_motion(self):
        self.page.emulate_media(reduced_motion='reduce')
        for madness in [100, 0]:
            self.page.locator('.room-trip-switch').click()
            self.assertEqual(self.page.evaluate('stats.madness'), madness)
            self.assertEqual(self.page.evaluate('paperDollState.activeViewMode'), 'combat' if madness else 'patient')
            self.page.locator('.room-door-action').click()
            self.assertTrue(self.page.locator('#map-modal').is_visible())
            self.page.evaluate('toggleMapModal(false)')
            self.page.wait_for_function('document.querySelector(".room-door-assembly").dataset.state==="closed"')
        self.page.locator('.room-cabinet-action').click()
        self.assertTrue(self.page.locator('#custom-modal').is_visible())
        self.page.evaluate('closeCustomization()')
        self.page.wait_for_function('document.querySelector(".room-cabinet-assembly").dataset.state==="closed"')
        self.assertEqual(float(self.page.locator('.hospital-hud').evaluate('e=>getComputedStyle(e).getPropertyValue("--room-light")')), 1)


if __name__ == '__main__':
    unittest.main()
