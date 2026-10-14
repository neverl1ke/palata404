"""Browser regressions: python3 -m unittest discover -s tests -v.

Uses an isolated local server and browser profile; external services are blocked.
Set PALATA_BROWSER_PATH to use a system Chromium instead of Playwright's browser.
"""
import functools
import json
import os
from pathlib import Path
import re
import threading
import unittest
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class IconAssetTests(unittest.TestCase):
    def test_svg_assets_are_self_contained_and_valid(self):
        paths = sorted((ROOT / 'assets' / 'icons').glob('*.svg'))
        self.assertGreater(len(paths), 50)
        for path in paths:
            with self.subTest(icon=path.name):
                svg = ET.parse(path).getroot()
                self.assertEqual(svg.tag, '{http://www.w3.org/2000/svg}svg')
                self.assertEqual(svg.attrib['viewBox'], '0 0 64 64')
                for node in svg.iter():
                    self.assertNotIn(node.tag.split('}')[-1], ['script', 'text', 'foreignObject', 'image'])
                    self.assertFalse(any('href' in key for key in node.attrib))


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/'
        cls.playwright = sync_playwright().start()
        options = {'headless': True}
        if os.getenv('PALATA_BROWSER_PATH'):
            options['executable_path'] = os.environ['PALATA_BROWSER_PATH']
        cls.browser = cls.playwright.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 800})
        self.context.route('https://**/*', lambda route: route.abort())
        self.errors = []
        self.page = self.context.new_page()
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('dialog', lambda dialog: dialog.accept())

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [], 'Unexpected browser runtime errors')

    def load(self, saves=None, query=''):
        if saves:
            self.context.add_init_script(
                'if (!sessionStorage.getItem("seeded")) {'
                f'for (const [key, value] of Object.entries({json.dumps(saves)})) '
                'localStorage.setItem(key, value);'
                'sessionStorage.setItem("seeded", "1"); }')
        self.page.goto(self.url + query, wait_until='networkidle')
        self.assertNotEqual(self.page.locator('#player-name').inner_text(), 'Завантаження...')

    def state(self):
        return self.page.evaluate('({...stats})')

    def equip(self, name):
        self.page.evaluate('(name) => { openInventory(); openItemInfo(inventory.find(i => i.name === name)); }', name)
        self.page.locator('#item-action-btn').click()

    def use(self, name):
        self.equip(name)

    def test_local_resources_markup_and_event_handlers(self):
        self.load()
        duplicates = self.page.evaluate('''() => {
            const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
            return ids.filter((id, index) => ids.indexOf(id) !== index);
        }''')
        self.assertEqual(duplicates, [])
        handlers = self.page.evaluate(r'''() => [...document.querySelectorAll('[onclick]')]
            .flatMap(e => [...e.getAttribute('onclick').matchAll(/\b([A-Za-z_$][\w$]*)\s*\(/g)])
            .map(m => m[1]).filter(name => !['stopPropagation'].includes(name))
            .filter(name => typeof window[name] !== 'function')''')
        self.assertEqual(handlers, [])
        for name in re.findall(r"[\w-]+\.(?:png|jpg)", '\n'.join(
                (ROOT / file).read_text() for file in ['index.html', 'style.css', 'script.js'])):
            if name == '_dossier_card.png':  # Filename is composed from the canonical boss key.
                continue
            self.assertTrue((ROOT / name).is_file(), name)
        self.assertEqual(self.page.evaluate('''() => [...document.images]
            .filter(img => img.getAttribute('src') && (!img.complete || !img.naturalWidth))
            .map(img => img.getAttribute('src'))'''), [])

    def test_corrupt_saves_and_denied_storage_do_not_break_boot(self):
        self.load({
            'palata404_stats': '{invalid', 'palata404_inventory': 'null',
            'palata404_equipped': '[]', 'palata404_friends': '{}',
            'palata404_gym': '{"exercises":null,"completedRounds":-5}',
            'palata404_progress': 'false', 'palata404_boss_kills': 'null',
            'palata404_gender': '../../missing', 'palata404_face': 'missing.png',
        })
        self.assertEqual(self.state()['hp'], 100)
        self.assertEqual(self.page.locator('#layer-body').get_attribute('src'), 'base_male.png')
        self.page.evaluate('openInventory(); openGym(); openDossier();')
        self.context.add_init_script('''Object.defineProperty(window, 'localStorage', {
            get() { throw new DOMException('Storage unavailable', 'SecurityError'); }
        });''')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['damage'], 10)
        self.page.evaluate('openGym(); doGymExercise("squats"); updateEnergyTimer();')
        self.assertEqual(self.state()['energy'], 98)

    def test_untrusted_text_stays_text(self):
        attack = '<img src=x onerror="window.injected=true">'
        self.load({
            'palata404_nickname': attack,
            'palata404_friends': json.dumps([{'identifier': attack, 'status': attack}]),
            'palata404_inventory': json.dumps([{
                'name': attack, 'icon': attack, 'desc': attack, 'category': 'mod', 'count': 1}]),
        })
        self.assertEqual(self.page.locator('#player-name').inner_text(), attack)
        self.page.evaluate('openFriends()')
        self.assertEqual(self.page.locator('#friends-list img').count(), 0)
        self.page.evaluate('openInventory(); openItemInfo(inventory[0]);')
        self.assertEqual(self.page.locator('#item-info-body img').count(), 0)
        self.assertFalse(self.page.evaluate('Boolean(window.injected)'))

    def test_wardrobe_selected_face_survives_reload(self):
        self.load()
        self.page.evaluate('openCustomization(); setGender("female"); setFace("face_3.png");')
        self.assertEqual(self.page.locator('#layer-face').get_attribute('src'), 'face_3.png')
        self.page.locator('#layer-face').wait_for(state='visible')
        self.assertTrue(self.page.locator('#layer-face').is_visible())
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.locator('#layer-body').get_attribute('src'), 'base_female.png')
        self.assertEqual(self.page.locator('#layer-face').get_attribute('src'), 'face_3.png')

    def test_equipment_swap_reload_and_legacy_training_bonus(self):
        self.load({
            'palata404_stats': json.dumps({'damage': 51, 'armor': 40, 'gymRounds': 2}),
            'palata404_equipped': json.dumps({
                'weapon': 'Штурмовий АКС-74У', 'helmet': 'Побитий шолом санітара', 'armor': 'Бронежилет БР-1'}),
        })
        self.assertEqual(self.state()['damage'], 51)
        self.equip('Іржавий ніж')
        self.assertEqual(self.state()['damage'], 24)
        self.equip('Іржавий ніж')
        self.assertEqual(self.state()['damage'], 16)
        self.equip('Побитий шолом санітара')
        self.assertEqual(self.state()['armor'], 28)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['damage'], 16)
        self.assertEqual(self.state()['armor'], 28)

    def test_shop_and_medicine_effects_match_in_and_out_of_battle(self):
        self.load({'palata404_stats': json.dumps({'silver': 2000, 'bucks': 100})})
        self.page.evaluate('''() => {
            buyMedicalItem('stamina_full', 10, 'bucks');
            buyMedicalItem('hp_10', 30, 'silver');
            buyMedicalItem('hp_full', 150, 'silver');
            buyMedicalItem('madness_pills', 50, 'silver');
            stats.energy = 10; stats.hp = 20; stats.madness = 40; updateUI();
        }''')
        self.assertEqual(self.state()['bucks'], 90)
        self.assertEqual(self.state()['silver'], 1770)
        self.use('Стимулятор')
        self.assertEqual(self.state()['energy'], 100)
        self.use('Мала аптечка')
        self.assertEqual(self.state()['hp'], 30)
        self.use('Таблетки «Аміназин»')
        self.assertEqual(self.state()['madness'], 25)
        self.page.evaluate('startBossFight("nurse"); stats.hp = 20; updateBattleUI();')
        self.page.locator('#medkit-btn-big').click()
        self.assertEqual(self.state()['hp'], 100)
        self.assertEqual(self.page.locator('#medkit-count-big').inner_text(), '0')
        self.page.evaluate('openFleeConfirmModal()')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['hp'], 100)

    def test_invalid_purchase_and_full_health_do_not_spend_resources(self):
        self.load()
        self.page.evaluate("buyMedicalItem('hp_10', -5, 'silver'); buyMedicalItem('unknown', 1, 'silver');")
        self.assertEqual(self.state()['silver'], 150)
        self.page.evaluate("buyMedicalItem('hp_10', 30, 'silver')")
        self.use('Мала аптечка')
        self.assertEqual(self.page.evaluate("inventory.find(i=>i.name==='Мала аптечка').count"), 1)

    def test_gym_energy_psychosis_and_dossier_refresh(self):
        self.load()
        self.page.evaluate('openGym()')
        self.page.locator('#gym-exercises-list button').first.click()
        self.assertEqual(self.state()['energy'], 98)
        self.assertEqual(self.state()['exp'], 5)
        self.page.evaluate('stats.madness=100; updateUI(); doGymExercise("squats"); openDossier();')
        self.assertEqual(self.state()['energy'], 98)
        self.assertEqual(self.page.locator('#dossier-madness-attacks').inner_text(), '4')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('gymComplex.exercises[0].current'), 1)

    def test_energy_regeneration_after_offline_time(self):
        self.load({'palata404_stats': '{"energy":90}',
                   'palata404_last_time': str(0)})
        self.page.evaluate('energyLastTime = Date.now()-5*120000; updateEnergyTimer();')
        self.assertEqual(self.state()['energy'], 95)
        self.page.evaluate('updateEnergyTimer()')
        self.assertEqual(self.state()['energy'], 95)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['energy'], 95)

    def test_map_unlock_is_persistent_and_locked_floor_stays_closed(self):
        self.load({'palata404_stats': '{"madness":100,"energy":100}'})
        self.page.evaluate('toggleMapModal(true); openFloorMap(10);')
        self.assertEqual(self.page.locator('.node-locked').count(), 1)
        self.page.locator('.map-node-pin').filter(has_text='Завал').click()
        self.assertEqual(self.page.locator('.node-locked').count(), 0)
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('toggleMapModal(true); openFloorMap(10);')
        self.assertEqual(self.page.locator('.node-locked').count(), 0)
        self.page.evaluate('showFloorsList(); openFloorMap(9);')
        self.assertTrue(self.page.locator('#map-floors-view').is_visible())

    def test_battle_damage_armor_victory_and_single_reward(self):
        self.load()
        self.equip('Штурмовий АКС-74У')
        self.equip('Побитий шолом санітара')
        self.equip('Бронежилет БР-1')
        self.page.clock.install()
        self.page.evaluate('startBossFight("nurse")')
        self.page.locator('#battle-arena-screen').click(position={'x': 400, 'y': 200})
        self.assertEqual(self.page.evaluate('bossCurrentHp'), 75)
        self.assertEqual(self.page.locator('#b-boss-hp').inner_text(), '75/120')
        self.page.clock.run_for(600)
        self.assertEqual(self.state()['hp'], 100 - self.page.evaluate('Math.ceil(bossesDatabase.nurse.damage*100/140)'))
        self.page.clock.run_for(4000)
        self.page.evaluate('performPlayerAttack()')
        self.page.clock.run_for(4000)
        self.page.evaluate('performPlayerAttack()')
        self.assertTrue(self.page.locator('#nurse-victory-modal').is_visible())
        earned = self.state()['silver']
        self.page.evaluate('handleVictory()')
        self.assertEqual(self.state()['silver'], earned)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['bossesKilled'], 1)

    def test_phone_layout_dialogs_rotation_and_keyboard(self):
        self.load()
        for width, height in [(320,568),(390,844),(768,1024),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                self.page.evaluate('openSettings()')
                self.assertTrue(self.page.locator('#settings-modal').is_visible())
                self.page.keyboard.press('Escape')
                self.assertFalse(self.page.locator('#settings-modal').is_visible())
                self.page.evaluate('openBossDossier("nurse")')
                button = self.page.locator('#universal-dossier-start-btn')
                button.scroll_into_view_if_needed()
                box = button.bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                button.click()
                self.assertTrue(self.page.locator('#nurse-battle-modal').is_visible())
                self.page.evaluate('openFleeConfirmModal()')
        self.page.evaluate('closeOtherModals();')
        self.page.locator('.user-profile-badge').focus()
        self.page.keyboard.press('Enter')
        self.assertTrue(self.page.locator('#dossier-modal').is_visible())

    def test_touch_navigation_and_arena_fit(self):
        # A mobile context also exercises coarse-pointer CSS and tap events.
        context = self.browser.new_context(viewport={'width': 390, 'height': 844},
                                           is_mobile=True, has_touch=True, device_scale_factor=3)
        context.route('https://**/*', lambda route: route.abort())
        page = context.new_page()
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        page.on('dialog', lambda dialog: dialog.accept())
        try:
            page.goto(self.url, wait_until='networkidle')
            page.get_by_role('button', name='Інвентар', exact=True).tap()
            self.assertTrue(page.locator('#inventory-modal').is_visible())
            page.locator('#inventory-modal .btn-close-mini').tap()
            page.evaluate('startBossFight("nurse")')
            box = page.locator('#battle-arena-scale').bounding_box()
            self.assertGreaterEqual(box['x'], -1)
            self.assertGreaterEqual(box['y'], -1)
            self.assertLessEqual(box['x'] + box['width'], 391)
            self.assertLessEqual(box['y'] + box['height'], 845)
            results = ROOT / 'test-results'
            results.mkdir(exist_ok=True)
            page.screenshot(path=str(results / 'mobile-battle.png'), full_page=True)
            # Decorative sprites don't receive pointer events; the arena underneath does.
            target = page.locator('#nurse-boss-sprite').bounding_box()
            x = target['x'] + target['width'] / 2
            y = target['y'] + target['height'] / 2
            self.assertTrue(page.evaluate('''({x,y}) => Boolean(
                document.elementFromPoint(x,y)?.closest('#battle-arena-screen'))''', {'x': x, 'y': y}))
            page.touchscreen.tap(x, y)
            self.assertEqual(page.evaluate('bossCurrentHp'), 110)
            page.evaluate('openFleeConfirmModal()')
            page.screenshot(path=str(results / 'mobile-lobby.png'), full_page=True)
        finally:
            context.close()

    def test_local_icons_render_in_static_and_dynamic_views(self):
        self.load()
        self.assertGreater(self.page.locator('.game-icon').count(), 60)
        self.assertEqual(self.page.locator('#medkit-btn-small img').get_attribute('src'), 'assets/icons/medkit.svg')
        self.assertEqual(self.page.locator('#medkit-btn-big img').get_attribute('src'), 'assets/icons/surgery.svg')
        self.assertEqual(self.page.get_by_role('button', name='Придбати малу аптечку за 30 срібла', exact=True).count(), 1)
        self.page.evaluate('openInventory()')
        self.assertEqual(self.page.locator('#stash-items .game-icon').count(), 5)
        self.assertEqual(self.page.locator('#stash-items .game-icon').nth(2).get_attribute('src'),
                         'assets/icons/rifle.svg')
        for action, selector in [
                ('openGym()', '#gym-exercises-list'),
                ('openMedicalHub()', '#rooms-list-container'),
                ('toggleMapModal(true); openFloorMap(10)', '#blueprint-nodes-container'),
                ('openCustomization()', '#wardrobe-container')]:
            self.page.evaluate(action)
            self.assertGreater(self.page.locator(selector + ' img.game-icon').count(), 0)
            # Every actual dynamic illustration uses a whitelisted local image.
            self.assertTrue(self.page.evaluate('''selector => [...document.querySelectorAll(selector+' img.game-icon')]
                .every(img => img.getAttribute('src').startsWith('assets/icons/'))''', selector))
        self.page.evaluate('showCustomToast("⚠️ Тест повідомлення")')
        self.assertEqual(self.page.locator('#toast-message .game-icon').get_attribute('src'),
                         'assets/icons/warning.svg')
        self.assertNotIn('⚠', self.page.locator('#toast-message').inner_text())
        self.page.wait_for_function('''() => [...document.querySelectorAll('img.game-icon')]
            .every(img => img.complete && img.naturalWidth > 0)''')

    def test_legacy_item_icons_and_untrusted_icon_urls(self):
        self.load({'palata404_inventory': json.dumps([
            {'name':'Старий ключ','icon':'🗝️','category':'quest','count':3},
            {'name':'Невідомий предмет','icon':'https://example.org/track.svg','category':'mod','count':2}
        ])})
        self.page.evaluate('openInventory()')
        icons = self.page.locator('#stash-items .game-icon')
        self.assertEqual(icons.nth(0).get_attribute('src'), 'assets/icons/key.svg')
        self.assertEqual(icons.nth(1).get_attribute('src'), 'assets/icons/box.svg')
        self.assertEqual(self.page.locator('#stash-items .item-count').first.inner_text(), '3')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('inventory[0].count'), 3)


if __name__ == '__main__':
    unittest.main()
