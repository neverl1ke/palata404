"""The existing medicine shop is reachable only in the actual Patient procedure room."""
import unittest
from tests import test_game


class MedicalNavigationTests(unittest.TestCase):
    setUpClass = classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(test_game.GameTests.tearDownClass.__func__)

    def setUp(self):
        self.errors = []
        self.dialogs = []
        self.context = self.browser.new_context(
            viewport={'width': 844, 'height': 390},
            reduced_motion='reduce', is_mobile=True, has_touch=True)
        self.context.route('https://**/*', lambda route: route.abort())
        self.page = self.context.new_page()
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('dialog', self.handle_dialog)
        self.page.goto(self.url + 'play.html')
        self.game = self.page.frames[1]
        self.ready()

    def handle_dialog(self, dialog):
        self.dialogs.append(dialog.message)
        dialog.accept()

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def ready(self):
        self.game.wait_for_function('window.PalataQuestPrototype && '
            'document.querySelector(".hospital-hud")?.dataset.assetsReady==="true"')
        self.page.wait_for_timeout(220)

    def room(self, room):
        if self.game.locator('.quest-room-tools').is_visible():
            self.game.locator('.quest-room-tools button').first.click()
        elif not self.game.locator('#map-modal').is_visible():
            self.game.locator('#location-card-box').click()
        self.game.locator(f'.quest-map-pin[data-room="{room}"]').dblclick(delay=40)
        self.game.wait_for_function('r=>PalataQuestPrototype.snapshot().room===r && '
            '!document.getElementById("quest-location-screen").classList.contains("hidden")', arg=room)

    def medicine_state(self):
        return self.game.evaluate('''()=>({silver:stats.silver,
            count:inventory.filter(x=>x.name===MEDICAL_ITEMS.hp_10.name&&x.category==='meds').reduce((n,x)=>n+x.count,0),
            stacks:inventory.filter(x=>x.name===MEDICAL_ITEMS.hp_10.name&&x.category==='meds').length,
            room:PalataQuestPrototype.snapshot().room,currentRoom:currentRoom.id,
            mode:PalataQuestPrototype.snapshot().mode})''')

    def open_shop(self):
        if self.game.locator('#quest-location-screen').is_hidden():self.room('procedure')
        self.game.locator('[data-medical-shop="true"]').click()
        self.assertTrue(self.game.locator('#procedure-room-modal').is_visible())

    def buy_small_medkit(self):
        self.game.locator('#procedure-room-modal [aria-label="Придбати малу аптечку за 30 срібла"]').click()

    def test_real_procedure_shop_purchase_stack_reload_close_and_insufficient_balance(self):
        self.room('procedure')
        before = self.medicine_state()
        self.assertEqual(before['silver'], 150)
        self.open_shop()
        self.assertEqual(self.medicine_state(), before)
        self.buy_small_medkit()
        first = self.medicine_state()
        self.assertEqual(first['silver'], 120)
        self.assertEqual(first['count'], before['count'] + 1)
        self.buy_small_medkit()
        second = self.medicine_state()
        self.assertEqual(second['silver'], 90)
        self.assertEqual(second['count'], before['count'] + 2)
        self.assertEqual(second['stacks'], 1)
        self.game.locator('#procedure-room-modal .btn-close-mini').click()
        self.assertTrue(self.game.locator('#procedure-room-modal').is_hidden())
        self.assertTrue(self.game.locator('#quest-location-screen').is_visible())
        self.assertEqual(second['room'], 'procedure')
        self.assertEqual(second['currentRoom'], 'procedure')
        self.page.reload()
        self.game = self.page.frames[1]
        self.ready()
        self.assertEqual(self.medicine_state(), second)
        self.open_shop()
        for _ in range(3):
            self.buy_small_medkit()
        spent = self.medicine_state()
        self.assertEqual(spent['silver'], 0)
        self.assertEqual(spent['count'], before['count'] + 5)
        self.buy_small_medkit()
        self.assertEqual(self.medicine_state(), spent)
        self.assertEqual(self.dialogs, ['Мало срібла!'])
        self.game.locator('#procedure-room-modal .btn-close-mini').click()
        self.page.reload()
        self.game = self.page.frames[1]
        self.ready()
        self.assertEqual(self.medicine_state(), spent)

    def test_unusable_mode_medicine_is_explained_and_cannot_be_bought(self):
        self.room('procedure')
        self.open_shop()
        pills = self.game.locator('#procedure-room-modal [aria-label="Придбати Аміназин за 50 срібла"]')
        self.assertTrue(pills.is_disabled())
        self.assertEqual(pills.get_attribute('aria-describedby'), 'procedure-mode-note')
        self.assertIn('червоним перемикачем', self.game.locator('#procedure-mode-note').inner_text())
        self.assertEqual(self.game.locator('#procedure-room-modal button[onclick^="buyMedicalItem"]:enabled').count(), 4)
        before = self.game.evaluate('JSON.stringify({stats,inventory})')
        # Native disabled controls ignore keyboard activation and programmatic click.
        pills.evaluate('button=>button.click()')
        self.assertEqual(self.game.evaluate('JSON.stringify({stats,inventory})'), before)

    def test_remote_patient_and_trip_legacy_navigation_do_not_teleport_or_open_shop(self):
        before = self.medicine_state()
        # Exercise the compatibility entry point; there is no remote shop UI.
        self.game.evaluate('openProcedureRoom()')
        self.assertTrue(self.game.locator('#map-modal').is_visible())
        self.assertTrue(self.game.locator('#procedure-room-modal').is_hidden())
        self.assertEqual(self.medicine_state(), before)
        self.game.locator('#map-modal .btn-close-map').click()
        self.game.locator('#quest-unlock-all').click()
        self.game.locator('.room-trip-switch').click()
        self.room('procedure')
        self.assertEqual(self.game.locator('[data-medical-shop]').count(), 0)
        before = self.medicine_state()
        self.assertEqual(before['mode'], 'trip')
        self.game.evaluate('openProcedureRoom()')
        self.assertTrue(self.game.locator('#procedure-room-modal').is_hidden())
        self.assertEqual(self.medicine_state(), before)


if __name__ == '__main__':
    unittest.main()
