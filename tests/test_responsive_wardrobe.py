"""Responsive geometry and real hit-target regressions, in an isolated browser."""
import unittest
from pathlib import Path
from tests import test_game

class ResponsiveWardrobeTests(unittest.TestCase):
    setUpClass = classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(test_game.GameTests.tearDownClass.__func__)
    def setUp(self):
        self.context = self.browser.new_context()
        self.context.add_init_script('window.__PALATA_TEST_DIRECT__=true;')
        self.context.route('https://**/*', lambda route: route.abort())
        self.page = self.context.new_page()
        self.page.on('dialog', lambda dialog: dialog.accept())
    def tearDown(self):
        self.context.close()

    def test_resize_inspect_return_and_apply(self):
        self.page.goto(self.url)
        self.page.evaluate('openCustomization()')
        for width,height in [(390,844),(844,390),(667,375),(568,320),(320,568),(1024,600),(1280,500),(1280,800),(1600,900),(390,844)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size(dict(width=width,height=height))
                self.page.evaluate("document.querySelector('.archive-wardrobe').removeAttribute('data-inspecting');selectWardrobeSlot('weapon')")
                self.page.wait_for_timeout(100)
                for selector in ['.archive-wardrobe .report-close','.archive-footer button:last-child']:
                    box=self.page.locator(selector).bounding_box()
                    self.assertGreaterEqual(box['height'],44)
                    self.assertGreaterEqual(box['y'],0)
                    self.assertLessEqual(box['y']+box['height'],height+1)
                    self.assertTrue(self.page.locator(selector).evaluate('(e)=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'))
                self.assertTrue(self.page.locator('.wardrobe-layout').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1'))
                card=self.page.locator('[data-wardrobe-item]').first
                card.click()
                self.assertTrue(self.page.locator('#wardrobe-item-detail').is_visible())
                action=self.page.locator('#wardrobe-item-detail [data-wardrobe-action]').first
                action.scroll_into_view_if_needed()
                box=action.bounding_box()
                self.assertGreaterEqual(box['height'],44)
                self.assertTrue(action.evaluate('(e)=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'))
                out=Path('test-results/responsive');out.mkdir(parents=True,exist_ok=True)
                self.page.screenshot(path=str(out/f'wardrobe-{width}x{height}.png'))
                if width<=1100 or height<=650:
                    back=self.page.locator('.archive-detail-close')
                    self.assertTrue(back.evaluate('(e)=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'))
                    back.click()
                    self.assertFalse(self.page.locator('#wardrobe-item-detail').is_visible())
                self.page.locator('.archive-footer button:last-child').click()
        self.page.locator('.archive-wardrobe .report-close').click()
        self.assertFalse(self.page.locator('#custom-modal').is_visible())
