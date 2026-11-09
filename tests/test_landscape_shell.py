"""Fixed landscape composition, independent of physical viewport orientation."""
import unittest
from pathlib import Path
from tests import test_game

class LandscapeShellTests(unittest.TestCase):
    setUpClass = classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(test_game.GameTests.tearDownClass.__func__)
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':844,'height':390},has_touch=True,is_mobile=True)
        self.context.route('https://**/*',lambda route:route.abort())
        self.page=self.context.new_page()
        self.page.goto(self.url,wait_until='networkidle')
        self.page.wait_for_url('**/play.html')
        self.game=self.page.frame_locator('#game-canvas')
        self.game.locator('#player-name').filter(has_not_text='Завантаження...').wait_for()
    def tearDown(self): self.context.close()

    def test_one_composition_survives_rotation_resize_and_modal_clicks(self):
        out=Path('test-results/landscape');out.mkdir(parents=True,exist_ok=True)
        for width,height in [(844,390),(667,375),(568,320),(1280,720),(1600,900),(1200,800),(390,844),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                rotate=height>width and width<900
                self.page.wait_for_function('(r)=>document.body.dataset.rotate===String(r)',arg=rotate)
                self.assertEqual(self.page.locator('#rotate-prompt').is_visible(),rotate)
                self.assertEqual(self.page.locator('#game-canvas').get_attribute('aria-hidden'),str(rotate).lower())
                geometry=self.page.evaluate('''()=>{const f=document.querySelector('#game-canvas'),r=f.getBoundingClientRect();return {w:f.contentWindow.innerWidth,h:f.contentWindow.innerHeight,x:r.x,y:r.y,right:r.right,bottom:r.bottom,ratio:r.width/r.height}}''')
                self.assertEqual((geometry['w'],geometry['h']),(1280,720))
                self.assertAlmostEqual(geometry['ratio'],16/9,places=3)
                self.assertGreaterEqual(geometry['x'],-1);self.assertGreaterEqual(geometry['y'],-1)
                self.assertLessEqual(geometry['right'],width+1);self.assertLessEqual(geometry['bottom'],height+1)
                if rotate:
                    self.page.screenshot(path=str(out/f'rotate-{width}x{height}.png'));continue
                for open_selector,modal in [('[onclick="openInventory()"]','#inventory-modal'),('[onclick="openSettings()"]','#settings-modal'),('[onclick="openBank()"]','#bank-modal'),('[onclick="openDossier()"]','#dossier-modal'),('[onclick="openFriends()"]','#friends-modal')]:
                    self.game.locator(open_selector).first.click()
                    self.assertTrue(self.game.locator(modal).is_visible())
                    self.game.locator(modal+' .btn-close-mini').click()
                self.game.locator('[onclick="openCustomization()"]').click()
                self.assertTrue(self.game.locator('.archive-wardrobe').is_visible())
                # Every physical size retains the same three-column wardrobe.
                self.assertEqual(self.game.locator('.wardrobe-layout').evaluate('e=>getComputedStyle(e).gridTemplateColumns.split(" ").length'),3)
                self.game.locator('[data-wardrobe-item]').first.click()
                self.assertTrue(self.game.locator('#wardrobe-item-detail').evaluate('e=>e.scrollHeight<=e.clientHeight+1&&e.scrollWidth<=e.clientWidth+1'))
                for selector in ['.p404-backing','.p404-slip','.p404-actions']:
                    self.assertTrue(self.game.locator(selector).evaluate("""e=>{const r=e.getBoundingClientRect(),p=e.closest('#wardrobe-item-detail').getBoundingClientRect();return r.left>=p.left-1&&r.right<=p.right+1&&r.top>=p.top-1&&r.bottom<=p.bottom+1;}"""),selector)
                # Trial click verifies hit testing without changing the outfit.
                self.game.locator('.p404-actions button').first.click(trial=True)
                self.page.screenshot(path=str(out/f'wardrobe-{width}x{height}.png'))
                self.game.locator('.archive-footer button:last-child').click()
                self.game.locator('.archive-wardrobe .report-close').click()
        self.assertEqual(self.page.locator('iframe').count(),1)

    def test_entry_preserves_query_and_hash_without_redirect_loop(self):
        self.page.goto(self.url+'?dev=1#layout-check',wait_until='networkidle')
        self.assertIn('play.html?dev=1#layout-check',self.page.url)
        src=self.page.locator('#game-canvas').get_attribute('src')
        self.assertIn('index.html?',src);self.assertIn('dev=1',src)
        self.assertIn('canvas=1',src);self.assertTrue(src.endswith('#layout-check'))
        self.assertEqual(self.game.locator('iframe').count(),0)
