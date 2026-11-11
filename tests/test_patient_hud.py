"""The room chart follows saved visible gear, without committing wardrobe drafts."""
import unittest
from tests import test_game


class PatientHudTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
    setUp=test_game.GameTests.setUp
    tearDown=test_game.GameTests.tearDown
    load=test_game.GameTests.load

    def assert_chart(self,damage,armor=0):
        self.assertEqual(self.page.locator('#damage-val').inner_text(),str(damage))
        self.assertEqual(self.page.locator('#armor-val').inner_text(),str(armor))
        self.assertEqual(self.page.locator('#hud-critical-value').inner_text(),'×1,5')

    def test_patient_weapon_and_armor_apply_cancel_remove_and_reload(self):
        self.load();self.assert_chart(10)
        self.page.evaluate('openCustomization();selectWardrobeItem("gear-aks")')
        self.page.locator('.p404-actions [data-wardrobe-action]').click()
        self.page.evaluate('PalataHUD.refresh()')
        self.assert_chart(10)  # An uncommitted fitting cannot change the chart.
        self.page.locator('.archive-footer').get_by_role('button',name='Применить',exact=True).click()
        self.assert_chart(45)
        self.page.evaluate('closeCustomization()')
        self.assertEqual(self.page.evaluate('getEquippedItem("weapon")'),None)
        self.page.reload(wait_until='networkidle');self.assert_chart(45)
        self.page.evaluate('equipPaperDollItem("headwear","gear-helmet");equipPaperDollItem("armor","gear-br1")')
        self.assert_chart(45,40)
        self.page.evaluate('openCustomization();equipPaperDollItem("weapon","weapon-demo-aks-experimental");PalataHUD.refresh()')
        self.assert_chart(45,40)
        self.page.evaluate('discardWardrobeSession();closeCustomization()')
        self.assert_chart(45,40)
        self.page.evaluate('equipPaperDollItem("weapon",null)');self.assert_chart(10,40)
        self.page.reload(wait_until='networkidle');self.assert_chart(10,40)

    def test_current_mode_and_direct_commits_refresh_combat_characteristics(self):
        self.load()
        self.page.evaluate('setPaperDollView("combat");equipPaperDollItem("weapon","weapon-demo-aks-experimental");equipPaperDollItem("armor","gear-br1")')
        self.assert_chart(64,28)
        self.assertEqual(self.page.evaluate('stats.damage'),64)
        self.page.evaluate('setPaperDollView("patient")');self.assert_chart(10)
        self.assertEqual(self.page.evaluate('stats.damage'),64)  # Battle loadout stays authoritative.
        self.page.evaluate('setPaperDollView("combat")');self.assert_chart(64,28)
        self.page.evaluate('WEAPON_MODELS["gear-aks"].rarity.experimental={criticalMultiplier:.5};updateUI()')
        self.assertEqual(self.page.locator('#hud-critical-value').inner_text(),'×2')
        self.page.evaluate('equipPaperDollItem("weapon","gear-pm")');self.assert_chart(28,28)
        self.page.reload(wait_until='networkidle');self.assert_chart(28,28)

    def test_navigation_uses_room_objects_for_wardrobe_map_and_tasks(self):
        self.load()
        nav=self.page.locator('.hud-tabs')
        self.assertEqual(nav.get_by_role('button').evaluate_all('(es)=>es.map(e=>e.getAttribute("aria-label"))'),
                         ['Инвентарь','Рейд','Соседи','Архив рейдов','Архив персонала'])
        self.page.locator('.room-cabinet-action').click()
        self.page.locator('#custom-modal').wait_for(state='visible')
        self.page.evaluate('closeCustomization()')
        self.page.wait_for_function('document.querySelector(".room-cabinet-assembly").dataset.state==="closed"')
        self.page.locator('.room-door-action').click()
        self.page.locator('#map-modal').wait_for(state='visible')
        self.page.keyboard.press('Escape')
        self.page.wait_for_function('document.querySelector(".room-door-assembly").dataset.state==="closed"')
        self.page.locator('.room-tasks-action').click()
        self.assertTrue(self.page.locator('#tasks-modal').is_visible())
        self.page.keyboard.press('Escape')
        self.assertFalse(self.page.locator('#tasks-modal').is_visible())


if __name__=='__main__':
    unittest.main()
