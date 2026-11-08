"""Responsive shell regression tests, using the same isolated server as test_game.

Run: PALATA_BROWSER_PATH=/usr/bin/chromium python3 -m unittest tests.test_general_responsive -v
"""
import unittest
from tests import test_game


class GeneralResponsiveTests(unittest.TestCase):
    setUpClass = classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(test_game.GameTests.tearDownClass.__func__)

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 800})
        self.context.route('https://**/*', lambda route: route.abort())
        self.page = self.context.new_page()
        self.page.on('dialog', lambda dialog: dialog.accept())
        self.page.goto(self.url)
        self.page.wait_for_function("typeof openInventory === 'function'")

    def tearDown(self):
        self.context.close()

    def assert_inside(self, selector, bounds=None):
        result = self.page.locator(selector).evaluate('''(el, bounds) => {
            const r = el.getBoundingClientRect();
            const b = bounds ? document.querySelector(bounds).getBoundingClientRect()
                             : {left:0,top:0,right:innerWidth,bottom:innerHeight};
            return {x:r.left >= b.left-1 && r.right <= b.right+1,
                    y:r.top >= b.top-1 && r.bottom <= b.bottom+1,
                    width:r.width,height:r.height};
        }''', bounds)
        self.assertTrue(result['x'], (selector, result))
        self.assertTrue(result['y'], (selector, result))
        self.assertGreater(result['width'], 0)
        self.assertGreater(result['height'], 0)

    def test_landscape_hud_and_panels_survive_live_resize(self):
        for width, height in [(844,390), (667,375), (568,320), (1024,600), (1280,480), (1440,900)]:
            with self.subTest(width=width, height=height):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate("document.getElementById('nav-map-btn').style.display='flex'")
                self.assert_inside('.top-nav')
                self.assert_inside('.top-right-group')
                self.assert_inside('.center-nav')
                self.assert_inside('.left-panel')
                self.assert_inside('.right-panel')
                self.assert_inside('.center-stage')
                # Last folder tab must be reachable, including very narrow landscape.
                last = self.page.locator('#nav-staff-btn')
                last.scroll_into_view_if_needed()
                self.assert_inside('#nav-staff-btn', '.center-nav')
                self.page.locator('.bank-btn').scroll_into_view_if_needed()
                self.assert_inside('.bank-btn', '.left-panel')
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)

    def test_portrait_document_scroll_has_no_horizontal_overflow(self):
        for width, height in [(320,568), (390,844), (768,1024)]:
            with self.subTest(width=width):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('window.scrollTo(0,0)')
                self.assert_inside('.top-nav')
                self.assert_inside('#nav-staff-btn', '.center-nav')
                self.page.locator('#location-card-box').scroll_into_view_if_needed()
                self.assert_inside('#location-card-box')
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)

    def test_common_dialogs_fit_short_and_narrow_viewports(self):
        dialogs = [('openSettings()', 'settings-modal'),
                   ('openBank()', 'bank-modal'),
                   ('openInventory()', 'inventory-modal'),
                   ('openDossier()', 'dossier-modal'),
                   ('openFriends()', 'friends-modal')]
        for width, height in [(320,568), (568,320), (844,390), (1280,480), (1440,900)]:
            self.page.set_viewport_size({'width':width,'height':height})
            for action, modal in dialogs:
                with self.subTest(width=width,height=height,modal=modal):
                    self.page.evaluate(action)
                    self.assert_inside('#'+modal+' > .modal-content')
                    close = self.page.locator('#'+modal+' .btn-close-mini')
                    close.scroll_into_view_if_needed()
                    self.assert_inside('#'+modal+' .btn-close-mini')
                    close.click()
                    self.assertTrue(self.page.locator('#'+modal).is_hidden())


if __name__ == '__main__':
    unittest.main()
