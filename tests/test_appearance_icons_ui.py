"""User-supplied illustrations and a single compact palette keep avatar art separate."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image
from tests import test_game

ROOT=Path(__file__).resolve().parents[1]


class AppearanceIconAssetTests(unittest.TestCase):
    def test_supplied_pngs_are_preserved_and_runtime_icons_cover_all_66_entries(self):
        manifest=json.loads((ROOT/'assets/ui/wardrobe/appearance-icons/manifest.json').read_text())
        self.assertEqual(len(manifest['files']),66)
        for entry in manifest['files']:
            self.assertEqual(hashlib.sha256((ROOT/entry['source']).read_bytes()).hexdigest(),entry['sourceSha256'])
            self.assertEqual(hashlib.sha256((ROOT/entry['runtime']).read_bytes()).hexdigest(),entry['sha256'])
            with Image.open(ROOT/entry['runtime']) as image:
                self.assertEqual(image.size,(256,256));self.assertEqual(image.mode,'RGBA')
                self.assertLess(image.getchannel('A').getextrema()[0],1)


class AppearanceIconUiTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
    setUp=test_game.GameTests.setUp
    tearDown=test_game.GameTests.tearDown
    load=test_game.GameTests.load

    def test_every_catalogue_variant_and_category_uses_the_supplied_icon(self):
        self.load();self.page.set_viewport_size({'width':1672,'height':941})
        original=self.page.evaluate('JSON.stringify({items:PAPER_DOLL_ITEMS,bodies:PAPER_DOLL_BODIES})')
        self.page.evaluate('openCustomization();selectWardrobeCategory("appearance")')
        for gender in ['male','female']:
            self.page.evaluate('g=>setGender(g)',gender)
            for slot in ['face','hair']+(['beard'] if gender=='male' else []):
                self.page.evaluate('s=>selectWardrobeSlot(s)',slot)
                missing=self.page.evaluate('wardrobeVisibleItems().filter(i=>!wardrobeAppearanceIcon(i)).map(i=>i.id)')
                self.assertEqual(missing,[])
                images=self.page.locator('#wardrobe-container .wardrobe-item-image img')
                self.assertTrue(all('appearance-icons/' in s for s in images.evaluate_all('(es)=>es.map(e=>e.getAttribute("src"))')))
                self.page.wait_for_function('''()=>[...document.querySelectorAll('#wardrobe-container .wardrobe-item-image img')].every(i=>i.complete&&i.naturalWidth===256)''')
                self.assertEqual(self.page.locator('.wardrobe-face-portrait').count(),0)
                rails=self.page.locator('.appearance-slot-art')
                self.assertGreaterEqual(rails.count(),2)
                self.assertTrue(all('appearance-icons/' in s for s in rails.evaluate_all('(es)=>es.map(e=>getComputedStyle(e).backgroundImage)')))
        self.assertEqual(self.page.evaluate('JSON.stringify({items:PAPER_DOLL_ITEMS,bodies:PAPER_DOLL_BODIES})'),original)

    def test_unified_right_palette_has_all_colors_and_keeps_hair_and_beard_independent(self):
        self.load();self.page.set_viewport_size({'width':1672,'height':941})
        self.page.evaluate('openCustomization();equipPaperDollItem("beard","beard-06");setHairColor("ginger");selectWardrobeCategory("appearance");selectWardrobeSlot("beard")')
        palette=self.page.locator('#wardrobe-hair-palette')
        self.assertEqual(palette.evaluate('e=>e.parentElement.id'),'wardrobe-inspection')
        expected=self.page.evaluate('HAIR_COLORS.map(c=>c.id)')
        self.assertEqual(palette.locator('[data-hair-color]').evaluate_all('(es)=>es.map(e=>e.dataset.hairColor)'),expected)
        self.assertEqual(palette.locator('[data-hair-color-group],[data-palette-toggle]').count(),0)
        self.assertLess(palette.bounding_box()['height'],250)
        self.assertGreater(palette.bounding_box()['x'],self.page.locator('#wardrobe-items').bounding_box()['x'])
        for color in ['white','blue','original','burgundy']:
            self.page.locator('[data-hair-color="'+color+'"]').click()
            self.assertEqual(self.page.evaluate('paperDollState.appearance.beardColor'),color)
            self.assertEqual(self.page.evaluate('paperDollState.appearance.hairColor'),'ginger')
        self.page.evaluate('selectWardrobeSlot("hair")')
        self.assertEqual(palette.locator('[data-hair-color]').count(),25)
        self.page.locator('[data-hair-color="turquoise"]').click()
        self.assertEqual(self.page.evaluate('paperDollState.appearance.beardColor'),'burgundy')
        self.assertEqual(self.page.evaluate('paperDollState.appearance.hairColor'),'turquoise')
        self.page.locator('.archive-footer').get_by_role('button',name='Применить',exact=True).click()
        self.page.evaluate('closeCustomization()');self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('paperDollState.appearance.beardColor'),'burgundy')
        self.assertEqual(self.page.evaluate('paperDollState.appearance.hairColor'),'turquoise')

    def test_small_screens_keep_palette_scrollable_and_color_buttons_reachable(self):
        self.load();self.page.evaluate('openCustomization();selectWardrobeCategory("appearance");selectWardrobeSlot("beard")')
        for width,height in [(390,844),(320,568),(844,390)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.locator('[data-hair-color="red"]').click()
            self.assertEqual(self.page.evaluate('paperDollState.appearance.beardColor'),'red')
            self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width+1)
            self.assertTrue(self.page.locator('.archive-footer').get_by_role('button',name='Применить',exact=True).is_visible())


if __name__=='__main__':
    unittest.main()
