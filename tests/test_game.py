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
        self.context.add_init_script('Math.random=()=>0.5;')
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
        self.page.evaluate('openProcedureRoom()')
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

    def test_victory_protocol_identity_rewards_and_archive_reopen(self):
        self.load()
        previous_id = None
        for key, code, number, exp, silver in [('nurse','404-KL','№001',52,31), ('doctor','404-IZ','№002',126,84)]:
            with self.subTest(boss=key):
                before = self.state()['silver']
                self.page.evaluate('''key => {
                    stats.baseDamage=300; recalculateEquipmentStats();
                    startBossFight(key); performPlayerAttack();
                }''', key)
                self.assertTrue(self.page.locator('#nurse-victory-modal').is_visible())
                self.assertEqual(self.page.locator('#victory-summary-exp').inner_text(), f'+{exp}')
                self.assertEqual(self.page.locator('#victory-summary-silver').inner_text(), f'+{silver}')
                self.assertEqual(self.page.locator('#victory-summary-boss').inner_text(), self.page.evaluate('lastBattleResult.boss.name'))
                self.assertTrue(self.page.locator('#victory-summary-mvp').is_visible())
                self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
                self.assertFalse(self.page.locator('#nurse-victory-modal').is_visible())
                self.assertTrue(self.page.locator('#battle-detail-modal').is_visible())
                self.assertEqual(self.page.locator('#victory-boss-id').inner_text(), key)
                self.assertEqual(self.page.locator('#victory-case-code').inner_text(), code)
                self.assertEqual(self.page.locator('#victory-boss-number').inner_text(), number)
                self.assertEqual(self.page.locator('#victory-total-exp').inner_text(), str(exp))
                self.assertEqual(self.page.locator('#victory-total-silver').inner_text(), str(silver))
                self.assertEqual(self.state()['silver'], before+silver)
                current_id = self.page.locator('#victory-report-id').inner_text()
                self.assertNotEqual(current_id, previous_id)
                previous_id = current_id
                self.page.evaluate('handleVictory(); closeDetailedBattleReport(); openDetailedBattleReport();')
                self.assertEqual(self.state()['silver'], before+silver)
                self.assertEqual(self.page.locator('#victory-statistics-body tr').count(), 1)
                self.assertEqual(self.page.locator('#victory-rewards').count(), 1)
        after = self.state()
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openSettings()')
        self.page.get_by_role('button', name='Останній протокол бою', exact=True).click()
        self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
        self.assertEqual(self.page.locator('#victory-case-code').inner_text(), '404-IZ')
        self.assertEqual(self.state()['silver'], after['silver'])
        self.assertEqual(self.state()['bossesKilled'], after['bossesKilled'])

    def test_victory_protocol_mobile_scroll_and_controls(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack();')
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(320,568),(390,844),(844,390),(1280,800)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openDetailedBattleReport()')
                report = self.page.locator('#victory-detail-document')
                box = report.bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertGreaterEqual(box['y'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                self.assertLessEqual(box['y']+box['height'], height+1)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                if width < 900:
                    self.assertTrue(self.page.locator('.report-table-scroll').evaluate('e=>e.scrollWidth>e.clientWidth'))
                for button in self.page.locator('#battle-detail-modal .report-actions button').all():
                    button.scroll_into_view_if_needed()
                    action = button.bounding_box()
                    self.assertGreaterEqual(action['x'], 0)
                    self.assertLessEqual(action['x']+action['width'], width+1)
                    self.assertGreaterEqual(action['height'], 44)
                report.evaluate('e=>e.scrollTop=0')
                self.page.screenshot(path=str(results/f'victory-{width}x{height}.png'))
                self.page.get_by_role('button', name='Закрити детальний звіт', exact=True).click()
                self.assertFalse(self.page.locator('#battle-detail-modal').is_visible())
                self.assertTrue(self.page.locator('#nurse-victory-modal').is_visible())

    def test_compact_victory_fits_desktop_and_keeps_mobile_actions_visible(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack();')
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(1366,768),(1024,600),(320,568),(390,844),(844,390),(320,320)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openLastBattleResult()')
                report = self.page.locator('.victory-summary')
                box = report.bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertGreaterEqual(box['y'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                self.assertLessEqual(box['y']+box['height'], height+1)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                if width >= 1024:
                    for selector in ['.victory-summary', '#victory-summary-content']:
                        self.assertTrue(self.page.locator(selector).evaluate('e=>e.scrollHeight<=e.clientHeight+1'))
                    self.assertTrue(self.page.locator('#victory-summary-items').is_visible())
                for button in self.page.locator('.victory-summary-actions button').all():
                    action = button.bounding_box()
                    self.assertGreaterEqual(action['x'], 0)
                    self.assertGreaterEqual(action['y'], 0)
                    self.assertLessEqual(action['x']+action['width'], width+1)
                    self.assertLessEqual(action['y']+action['height'], height+1)
                    self.assertGreaterEqual(action['height'], 44)
                    self.assertTrue(button.evaluate('e=>{const r=e.getBoundingClientRect(); return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}'))
                self.page.screenshot(path=str(results/f'victory-summary-{width}x{height}.png'))
                self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
                self.assertTrue(self.page.locator('#battle-detail-modal').is_visible())
                self.page.keyboard.press('Escape')
                self.assertTrue(self.page.locator('#nurse-victory-modal').is_visible())

    def test_compact_victory_actions_and_report_reopening_do_not_pay_again(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack();')
        before = self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,lastBattleResult,storage:{...localStorage}})')
        for _ in range(3):
            self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
            self.assertTrue(self.page.locator('#victory-conclusion').inner_text())
            self.assertEqual(self.page.locator('#victory-statistics-body tr').count(), 1)
            self.page.get_by_role('button', name='Повернутися до підсумку', exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,lastBattleResult,storage:{...localStorage}})'), before)
        self.page.get_by_role('button', name='Повернутися на карту', exact=True).click()
        self.assertTrue(self.page.locator('#map-modal').is_visible())
        self.assertFalse(self.page.locator('#nurse-victory-modal').is_visible())
        self.page.evaluate('openLastBattleResult(); currentBossKey="nurse";')
        self.page.get_by_role('button', name='Повторити бій', exact=True).click()
        self.assertTrue(self.page.locator('#nurse-battle-modal').is_visible())
        self.assertEqual(self.page.evaluate('currentBattleSession.bossKey'), 'doctor')
        self.assertEqual(self.state()['silver'], 234)
        self.page.evaluate('performPlayerAttack()')
        self.assertEqual(self.state()['silver'], 318)
        self.assertIn('Вже в інвентарі:', self.page.locator('#victory-summary-items').inner_text())
        self.assertEqual(self.page.evaluate('inventory.filter(i=>i.category==="quest").length'), 1)

    def test_helper_mvp_and_long_report_remain_accessible_in_compact_view(self):
        self.load()
        self.page.evaluate('''() => {
            startBossFight('nurse'); callAllFriends(); Math.random=()=>0;
            for(let i=0;i<10;i++) friendsAutoAttackTick();
        }''')
        self.assertTrue(self.page.locator('#victory-summary-mvp').is_visible())
        self.assertEqual(self.page.locator('#victory-summary-mvp-name').inner_text(), 'MVP: Сліпий Микола')
        self.assertFalse(self.page.locator('#victory-summary-mvp-bonus').is_visible())
        self.assertEqual(self.page.locator('#victory-summary-exp').inner_text(), '+50')
        self.assertEqual(self.page.locator('#victory-summary-silver').inner_text(), '+30')
        self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
        self.assertEqual(self.page.locator('#victory-statistics-body tr').count(), 4)
        self.assertIn('MVP', self.page.locator('#victory-statistics-body').inner_text())
        self.assertIn('Не застосовується', self.page.locator('#victory-statistics-body').inner_text())
        self.page.get_by_role('button', name='Повернутися до підсумку', exact=True).click()
        self.page.set_viewport_size({'width':320,'height':320})
        self.page.evaluate('''() => {
            const preview=JSON.parse(JSON.stringify(lastBattleResult));
            preview.boss.name='Довга назва об’єкта '.repeat(10);
            preview.extraRewards=Array.from({length:12},(_,i)=>({name:'Предмет '+i,icon:'key',granted:true}));
            renderBattleSummary(preview);
        }''')
        self.assertTrue(self.page.locator('#victory-summary-content').evaluate('e=>e.scrollHeight>e.clientHeight'))
        self.page.locator('#victory-summary-items li').last.scroll_into_view_if_needed()
        self.assertTrue(self.page.locator('#victory-summary-items li').last.is_visible())
        for button in self.page.locator('.victory-summary-actions button').all():
            box = button.bounding_box()
            self.assertGreaterEqual(box['y'], 0)
            self.assertLessEqual(box['y']+box['height'], 320)

    def test_raid_archive_hud_snapshots_and_clear_confirmation(self):
        self.load({'palata404_nickname':'Історичний пацієнт'})
        institution = 'ЦЕНТР ІНТЕНСИВНОГО ЛІКУВАННЯ ПСИХІЧНИХ РОЗЛАДІВ № 404'
        self.page.get_by_role('button', name='Архів рейдів', exact=True).click()
        self.assertTrue(self.page.locator('#raid-archive-empty').is_visible())
        self.page.get_by_role('button', name='Закрити архів рейдів', exact=True).click()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack();')
        first = self.page.evaluate('JSON.parse(JSON.stringify(lastBattleResult))')
        self.assertEqual(self.page.locator('#victory-summary-mvp-name').inner_text(), 'MVP: Історичний пацієнт')
        self.assertTrue(self.page.locator('#victory-summary-mvp-bonus').is_visible())
        self.assertIn(institution, self.page.locator('#nurse-victory-modal .report-institution').inner_text())
        self.page.evaluate('playerName="Новий пацієнт"; startBossFight("doctor"); performPlayerAttack(); openRaidArchive();')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 2)
        self.assertIn(institution, self.page.locator('#raid-archive-modal .report-institution').inner_text())
        state = self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,gameProgress,storage:{...localStorage}})')
        old = self.page.locator('.raid-archive-card').filter(has_text=first['boss']['name'])
        self.assertIn('+52 EXP', old.inner_text())
        self.assertIn('+31 срібла', old.inner_text())
        self.assertIn('Історичний пацієнт', old.inner_text())
        old.click()
        self.assertEqual(self.page.locator('#victory-report-id').inner_text(), first['battleId'])
        self.assertEqual(self.page.locator('#victory-mvp-name').inner_text(), 'Історичний пацієнт')
        self.assertIn(institution, self.page.locator('#battle-detail-modal .report-institution').inner_text())
        self.assertEqual(self.page.locator('#battle-detail-modal .report-participant-stamp').inner_text(), 'MVP')
        self.page.get_by_role('button', name='Повернутися до архіву', exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,gameProgress,storage:{...localStorage}})'), state)
        self.page.reload(wait_until='networkidle')
        nav = self.page.get_by_role('button', name='Архів рейдів', exact=True)
        nav.focus()
        self.page.keyboard.press('Enter')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 2)
        self.page.get_by_role('button', name='Очистити архів', exact=True).click()
        self.assertTrue(self.page.locator('#raid-archive-confirm').is_visible())
        self.page.get_by_role('button', name='Скасувати', exact=True).click()
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 2)
        protected = self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,gameProgress,lastBattleResult})')
        self.page.get_by_role('button', name='Очистити архів', exact=True).click()
        self.page.locator('#raid-archive-confirm').get_by_role('button', name='Очистити архів', exact=True).click()
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 0)
        self.assertTrue(self.page.locator('#raid-archive-empty').is_visible())
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,gameProgress,lastBattleResult})'), protected)
        self.page.evaluate('handleVictory(); retryBattleResultSave(); openRaidArchive();')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 0)
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 0)
        self.page.get_by_role('button', name='Закрити архів рейдів', exact=True).click()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); openRaidArchive();')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 1)
        self.assertNotIn('Отримано:', self.page.locator('.raid-archive-card').inner_text())

    def test_raid_archive_limit_mobile_bounds_and_stamps(self):
        self.load()
        self.page.evaluate('''() => {
            const originalNow=Date.now; let now=originalNow(); Date.now=()=>now;
            stats.baseDamage=300; recalculateEquipmentStats();
            for(let i=0;i<51;i++) { startBossFight('nurse'); performPlayerAttack(); now++; }
            Date.now=originalNow; openRaidArchive();
        }''')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 50)
        self.assertEqual(self.page.locator('#raid-archive-count').inner_text(), '50 / 50')
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 50)
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(320,568),(390,844),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openRaidArchive()')
                box = self.page.locator('.raid-archive-document').bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertGreaterEqual(box['y'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                self.assertLessEqual(box['y']+box['height'], height+1)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                self.page.locator('.raid-archive-card').last.click()
                self.assertTrue(self.page.locator('#battle-detail-modal').is_visible())
                self.page.keyboard.press('Escape')
                self.assertTrue(self.page.locator('#raid-archive-modal').is_visible())
                self.page.locator('.raid-archive-document').evaluate('e=>e.scrollTop=0')
                self.page.screenshot(path=str(results/f'raid-archive-{width}x{height}.png'))
        self.page.evaluate('startBossFight("nurse"); callAllFriends(); Math.random=()=>0; for(let i=0;i<10;i++) friendsAutoAttackTick(); openDetailedBattleReport();')
        self.assertEqual(self.page.get_by_text('УХИЛЯВСЯ ВІД ПРОЦЕДУРИ', exact=True).count(), 1)
        self.assertEqual(self.page.locator('#battle-detail-modal .report-participant-stamp').count(), 2)

    def test_raid_archive_identity_and_shared_tabs(self):
        self.load({'palata404_web_id':'WEB-archive-tabs'})
        other = self.context.new_page()
        other.on('pageerror', lambda error: self.errors.append(str(error)))
        other.on('dialog', lambda dialog: dialog.accept())
        other.goto(self.url, wait_until='networkidle')
        for page, boss in [(self.page,'nurse'),(other,'doctor')]:
            page.evaluate('''boss=>{ stats.baseDamage=300; recalculateEquipmentStats(); startBossFight(boss); performPlayerAttack(); }''',boss)
        self.page.evaluate('openRaidArchive()')
        other.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 2)
        self.assertEqual(other.locator('.raid-archive-card').count(), 2)
        saved = self.page.evaluate('JSON.stringify(readRaidArchive())')
        self.page.evaluate('safeStorageSet("palata404_web_id","WEB-other-account")')
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 0)
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); clearRaidArchive();')
        self.assertEqual(other.evaluate('JSON.stringify(readRaidArchive())'), saved)
        other.close()

    def test_archive_full_dossier_images_and_personal_statuses(self):
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats();
            startBossFight('nurse'); performPlayerAttack();
            startBossFight('doctor'); performPlayerAttack(); openRaidArchive();
        }''')
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(320,568),(390,844),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                for filename, case in [('nurse_dossier_card.png','404-KL'),('doctor_dossier_card.png','404-IZ')]:
                    card = self.page.locator('.raid-archive-card').filter(has_text=case)
                    image = card.locator('.raid-card-dossier-image')
                    image.scroll_into_view_if_needed()
                    self.page.wait_for_function('(src)=>[...document.querySelectorAll(".raid-card-dossier-image")].some(e=>e.getAttribute("src")===src && e.complete && e.naturalWidth>0)', arg=filename)
                    self.assertEqual(image.get_attribute('src'), filename)
                    self.assertFalse(card.locator('.raid-card-no-dossier').is_visible())
                    self.assertEqual(card.locator('.raid-card-personal-stamp').inner_text(), 'MVP')
                    self.assertTrue(image.evaluate('e=>Math.abs(e.clientWidth/e.clientHeight-e.naturalWidth/e.naturalHeight)<0.02'))
                    self.assertEqual(image.evaluate('e=>getComputedStyle(e).objectFit'), 'contain')
                    self.assertEqual(card.locator('.raid-card-dossier-image').count(), 1)
                    photo = card.locator('.raid-card-visual').bounding_box()
                    text = card.locator('.raid-card-details').bounding_box()
                    if width > 600:
                        self.assertLessEqual(photo['x']+photo['width'], text['x'])
                    else:
                        self.assertLessEqual(photo['y']+photo['height'], text['y'])
                    box = card.bounding_box()
                    self.assertGreaterEqual(box['x'], 0)
                    self.assertLessEqual(box['x']+box['width'], width+1)
                self.page.locator('.raid-archive-document').evaluate('e=>e.scrollTop=0')
                self.page.screenshot(path=str(results/f'raid-dossiers-{width}x{height}.png'))
        before = self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,archive:readRaidArchive(),storage:{...localStorage}})')
        old_card = self.page.locator('.raid-archive-card').filter(has_text='404-KL')
        old_card.locator('.raid-card-open').click()
        self.assertEqual(self.page.locator('#victory-case-code').inner_text(), '404-KL')
        self.page.get_by_role('button', name='Повернутися до архіву', exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,archive:readRaidArchive(),storage:{...localStorage}})'), before)
        self.page.evaluate('''() => {
            startBossFight('nurse'); callAllFriends(); Math.random=()=>0;
            for(let i=0;i<10;i++) friendsAutoAttackTick(); openRaidArchive();
        }''')
        idle = self.page.locator('.raid-archive-card').first
        self.assertEqual(idle.locator('.raid-card-personal-stamp').inner_text(), 'УХИЛЯВСЯ ВІД ПРОЦЕДУРИ')
        self.assertIn('MVP: Сліпий Микола', idle.inner_text())
        self.assertIn('+50 EXP', idle.inner_text())
        self.page.evaluate('''() => {
            startBossFight('nurse'); raidMembers[0].metrics.healing=1;
            callAllFriends(); for(let i=0;i<10;i++) friendsAutoAttackTick(); openRaidArchive();
        }''')
        support = self.page.locator('.raid-archive-card').first
        self.assertEqual(support.locator('.raid-card-personal-stamp').count(), 0)
        self.assertIn('MVP: Сліпий Микола', support.inner_text())
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').first.locator('.raid-card-personal-stamp').count(), 0)

    def test_staff_archive_unknown_cases_first_contact_and_details(self):
        self.load()
        self.page.get_by_role('button', name='Архів персоналу', exact=True).click()
        archive = self.page.locator('#staff-archive-modal')
        self.assertEqual(archive.locator('.staff-case-button').count(), 2)
        self.assertEqual(archive.get_by_text('ОСОБУ НЕ ВСТАНОВЛЕНО', exact=True).count(), 3)
        self.assertEqual(archive.locator('img[src*="dossier_card"]').count(), 0)
        self.assertNotIn('Черговий лікар', archive.inner_text())
        self.assertNotIn('Сестра Клара', archive.inner_text())
        self.assertNotIn('Копія наказу', archive.inner_text())
        self.page.evaluate('openBossDossier("doctor")')
        self.page.get_by_role('button', name='ДЕТАЛЬНІ ВІДОМОСТІ', exact=True).click()
        self.assertIn('№002', self.page.locator('#staff-case-sheet').inner_text())
        self.assertIn('ОСОБУ НЕ ВСТАНОВЛЕНО', self.page.locator('#staff-case-sheet').inner_text())
        self.assertEqual(self.page.evaluate('Object.keys(staffArchiveState.cases).length'), 0)
        self.page.evaluate('startBossFight("doctor"); stats.hp=1; performPlayerAttack();')
        self.page.wait_for_function('!isBattleActive')
        self.page.evaluate('openStaffArchive("doctor")')
        self.assertIn('Черговий лікар', self.page.locator('#staff-case-sheet').inner_text())
        image = self.page.locator('.staff-dossier-image')
        self.assertEqual(image.get_attribute('src'), 'doctor_dossier_card.png')
        self.page.get_by_role('button', name='Архівні документи', exact=True).click()
        sheet = self.page.locator('#staff-case-sheet')
        self.assertIn('ДОКУМЕНТ №002-03 — ЗАСЕКРЕЧЕНО', sheet.inner_text())
        self.assertNotIn('Незаповнена графа наказу', sheet.inner_text())
        self.assertNotIn('Копія наказу головного лікаря', sheet.inner_text())
        sheet.get_by_role('button', name='Читати документ', exact=True).first.click()
        self.assertIn('Об’єкт №002 відомий', sheet.inner_text())
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openStaffArchive("doctor")')
        self.assertIn('Черговий лікар', self.page.locator('#staff-case-sheet').inner_text())
        self.assertEqual(self.page.evaluate('staffCaseProgress("doctor").opened'), 2)

    def test_staff_pity_rewards_and_clear_preserve_collection(self):
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0.5;
            for(let i=0;i<29;i++) { startBossFight('doctor'); performPlayerAttack(); }
        }''')
        self.assertEqual(self.page.evaluate('staffArchiveState.cases.doctor.misses'), 29)
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack();')
        self.assertEqual(self.page.evaluate('staffArchiveState.cases.doctor.misses'), 0)
        self.assertEqual(self.page.evaluate('lastBattleResult.extraRewards.filter(r=>r.type==="document").length'), 1)
        self.page.evaluate('''() => {
            Math.random=()=>0; startBossFight('doctor'); performPlayerAttack(); openStaffArchive('doctor'); changeStaffArchiveTab('rewards');
        }''')
        self.assertEqual(self.page.evaluate('staffCaseProgress("doctor").complete'), True)
        self.assertEqual(self.page.locator('.staff-reward-status').all_text_contents(), ['ДОСТУПНО','ДОСТУПНО'])
        before = self.state()['silver']
        buttons = self.page.locator('.staff-claim-button')
        self.assertEqual(buttons.count(), 2)
        buttons.first.click()
        self.assertEqual(self.state()['silver'], before+1)
        self.assertEqual(self.page.locator('.staff-reward-status').all_text_contents(), ['ОТРИМАНО','ДОСТУПНО'])
        self.page.locator('.staff-claim-button').click()
        self.assertEqual(self.state()['silver'], before+2)
        self.assertEqual(self.page.locator('.staff-claim-button').count(), 0)
        self.assertEqual(self.page.locator('.staff-reward-status').all_text_contents(), ['ОТРИМАНО','ОТРИМАНО'])
        self.assertEqual(self.page.locator('.staff-visual-progress progress').evaluate_all('es=>es.map(e=>e.value/e.max)'), [1,1])
        profile = self.page.evaluate('JSON.stringify(staffArchiveState)')
        self.page.evaluate('openRaidArchive(); requestRaidArchiveClear();')
        self.page.locator('#raid-archive-confirm').get_by_role('button', name='Очистити архів', exact=True).click()
        self.assertEqual(self.page.evaluate('readRaidArchive().length'), 0)
        self.assertEqual(self.page.evaluate('JSON.stringify(staffArchiveState)'), profile)
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openStaffArchive("doctor"); changeStaffArchiveTab("rewards");')
        self.assertEqual(self.state()['silver'], before+2)
        self.assertEqual(self.page.locator('.staff-claim-button').count(), 0)

    def test_staff_journal_documents_and_reward_cards_are_read_only_and_responsive(self):
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0;
            for (const boss of ['nurse','doctor']) { startBossFight(boss); performPlayerAttack(); }
            openStaffArchive('nurse');
        }''')
        before=self.page.evaluate('JSON.stringify({stats,inventory,gameProgress,staffArchiveState,storage:{...localStorage}})')
        results=ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                for boss in ['nurse','doctor']:
                    self.page.evaluate('boss=>openStaffArchive(boss)',boss)
                    for tab in ['identity','observations','documents','rewards']:
                        self.page.locator(f'[data-staff-tab="{tab}"]').click()
                        sheet=self.page.locator('#staff-case-sheet')
                        if tab=='identity':
                            self.assertEqual(sheet.locator('.staff-form-field').count(),8)
                        elif tab in ['observations','documents']:
                            self.assertNotRegex(sheet.inner_text(),r'5%|\d+/30|гаранті|drop rate|chance|pity')
                            self.assertGreater(sheet.locator('.staff-record-open').count(),0)
                            self.assertGreater(sheet.locator('.staff-record-locked').count(),0)
                            self.assertNotIn('Фрагмент журналу експериментів' if boss=='nurse' else 'Незаповнена графа наказу',sheet.inner_text())
                            if tab=='observations':
                                self.assertEqual(sheet.locator('.staff-observation-journal').count(),1)
                                self.assertGreater(sheet.locator('.staff-observation-text').count(),0)
                            sheet.get_by_role('button',name='Читати документ',exact=True).first.click()
                            self.assertTrue(sheet.locator('.staff-document-reading').is_visible())
                        else:
                            self.assertEqual(sheet.locator('.staff-reward-section').count(),2)
                            self.assertEqual(sheet.locator('progress').count(),2)
                            self.assertEqual(sheet.locator('.staff-reward-status').all_text_contents(),['НЕ ЗАВЕРШЕНО','НЕ ЗАВЕРШЕНО'])
                            self.assertEqual(sheet.locator('.staff-claim-button').count(),0)
                            progress=self.page.evaluate('boss=>staffCaseProgress(boss)',boss)
                            self.assertEqual(sheet.locator('progress').first.get_attribute('value'),str(progress['opened']))
                            self.assertIn('Завершено справ: 0/1',sheet.inner_text())
                            self.assertIn('+1 срібла',sheet.inner_text())
                        self.assertLessEqual(sheet.evaluate('e=>e.scrollWidth-e.clientWidth'),1)
                        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                        if width in [1280,390]:
                            self.page.screenshot(path=str(results/f'archive-{boss}-{tab}-{width}.png'))
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,gameProgress,staffArchiveState,storage:{...localStorage}})'),before)

    def test_folder_hud_navigation_active_tabs_and_mobile_bounds(self):
        self.load()
        self.page.evaluate('stats.madness=100; updateUI();')
        before=self.page.evaluate('JSON.stringify({stats,inventory,staffArchiveState,storage:{...localStorage}})')
        nav=self.page.get_by_role('navigation',name='Ігрове меню')
        results=ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                for button in nav.locator('.hud-folder-tab').all():
                    box=button.bounding_box()
                    self.assertIsNotNone(box)
                    self.assertGreaterEqual(box['height'],44)
                    self.assertGreaterEqual(box['x'],0)
                    self.assertLessEqual(box['x']+box['width'],width)
                    self.assertLessEqual(button.evaluate('e=>e.scrollWidth-e.clientWidth'),1)
                    self.assertTrue(button.locator('span').is_visible())
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                self.assertTrue(self.page.locator('#armor-val').is_visible())
                self.page.screenshot(path=str(results/f'folder-hud-{width}x{height}.png'))
        for name,modal in [('Інвентар','inventory-modal'),('Гардероб','custom-modal'),('Карта','map-modal'),('Сусіди по блоку','friends-modal'),('Архів рейдів','raid-archive-modal'),('Архів персоналу','staff-archive-modal')]:
            button=nav.get_by_role('button',name=name,exact=True)
            button.click()
            self.assertTrue(self.page.locator(f'#{modal}').is_visible())
            self.page.wait_for_function('name=>document.querySelector(`.center-nav [aria-label="${name}"]`).getAttribute("aria-pressed")==="true"',arg=name)
            self.assertEqual(nav.locator('[aria-pressed="true"]').count(),1)
            self.page.keyboard.press('Escape')
            self.page.wait_for_function('()=>!document.querySelector(".center-nav [aria-pressed=true]")')
        nav.get_by_role('button',name='Завдання',exact=True).click()
        nav.get_by_role('button',name='Рейд',exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,staffArchiveState,storage:{...localStorage}})'),before)
        self.page.evaluate('startBossFight("nurse"); closeNurseBattle();')
        nav.get_by_role('button',name='Рейд',exact=True).click()
        self.assertTrue(self.page.locator('#nurse-battle-modal').is_visible())
        self.assertTrue(self.page.locator('#lobby-raid-subtimer').is_visible())
        self.assertEqual(self.page.locator('#lobby-raid-subtimer').evaluate('e=>getComputedStyle(e).position'),'static')
        self.page.evaluate('openFleeConfirmModal()')

    def test_staff_archive_and_enlarged_dossiers_mobile_bounds(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); startBossFight("nurse"); performPlayerAttack(); openStaffArchive("nurse");')
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(1024,768),(768,1024),(320,568),(390,844),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openStaffArchive("nurse")')
                paper = self.page.locator('.staff-archive-document')
                box = paper.bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertGreaterEqual(box['y'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                self.assertLessEqual(box['y']+box['height'], height+1)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                for name in ['Архівні документи','Службові спостереження','Винагороди та колекції','Анкетні відомості']:
                    self.page.get_by_role('button', name=name, exact=True).click()
                self.page.screenshot(path=str(results/f'staff-archive-{width}x{height}.png'))
                self.page.evaluate('openBossDossier("doctor")')
                photo = self.page.locator('#universal-dossier-img')
                self.assertEqual(photo.get_attribute('src'), 'doctor_dossier_card.png')
                if width >= 1024:
                    self.assertGreaterEqual(photo.bounding_box()['width'], 290)
                self.page.get_by_role('button', name='ДЕТАЛЬНІ ВІДОМОСТІ', exact=True).click()
                self.assertIn('Черговий лікар', self.page.locator('#staff-case-sheet').inner_text())
                self.page.evaluate('openRaidArchive()')
                image = self.page.locator('.raid-card-dossier-image').first
                image.scroll_into_view_if_needed()
                self.page.wait_for_function('()=>[...document.querySelectorAll(".raid-card-dossier-image")].some(e=>e.complete&&e.naturalWidth>0)')
                if width >= 1024:
                    self.assertGreaterEqual(image.bounding_box()['width'], 315)
                    text = self.page.locator('.raid-card-details').first.bounding_box()
                    visual = self.page.locator('.raid-card-visual').first.bounding_box()
                    self.assertAlmostEqual(visual['y'], text['y'], delta=2)
                    self.assertLessEqual(text['x']-(visual['x']+visual['width']), 13)
                self.assertTrue(image.evaluate('e=>Math.abs(e.clientWidth/e.clientHeight-e.naturalWidth/e.naturalHeight)<0.02'))
                self.page.screenshot(path=str(results/f'raid-enlarged-{width}x{height}.png'))
                self.page.keyboard.press('Escape')
                self.assertFalse(self.page.locator('#raid-archive-modal').is_visible())

    def test_staff_collection_interrupted_claim_recovers_once(self):
        self.context.add_init_script('''
            const nativeSet=Storage.prototype.setItem;
            Storage.prototype.setItem=function(key,value) {
                if(window.blockStaffClaim && key==='palata404_stats') throw new DOMException('Interrupted','QuotaExceededError');
                return nativeSet.call(this,key,value);
            };
        ''')
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0;
            for(let i=0;i<5;i++) { startBossFight('doctor'); performPlayerAttack(); }
            openStaffArchive('doctor'); changeStaffArchiveTab('rewards'); window.blockStaffClaim=true;
        }''')
        before = self.state()['silver']
        self.page.locator('.staff-claim-button').first.click()
        self.assertEqual(self.state()['silver'], before+1)
        self.assertTrue(self.page.locator('#staff-save-note').is_visible())
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['silver'], before+1)
        self.page.evaluate('openStaffArchive("doctor"); changeStaffArchiveTab("rewards");')
        self.assertEqual(self.page.locator('.staff-claim-button').count(), 1)
        self.assertFalse(self.page.locator('#staff-save-note').is_visible())

    def test_compact_photo_composition_and_floor_filter_are_read_only(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack(); startBossFight("doctor"); performPlayerAttack();')
        before = self.page.evaluate('JSON.stringify({stats,inventory,staffArchiveState,archive:readRaidArchive(),storage:{...localStorage}})')
        self.page.evaluate('openStaffArchive("doctor")')
        options = self.page.locator('#staff-floor-filter option').all_text_contents()
        self.assertEqual(options, ['Усі поверхи','9 поверх','10 поверх'])
        self.assertEqual(self.page.locator('.staff-form-field').filter(has_text='Відділення:').locator('dd').inner_text(), 'Блок ізоляторів')
        self.assertEqual(self.page.locator('.staff-form-field').filter(has_text='Локація:').locator('dd').inner_text(), 'Кабінет спостереження, 10-й поверх')
        self.page.get_by_label('Поверх', exact=True).select_option('9')
        self.assertEqual(self.page.locator('.staff-case-button').count(), 0)
        self.assertIn('На цьому поверсі справ не зареєстровано', self.page.locator('#staff-case-sheet').inner_text())
        self.page.get_by_label('Поверх', exact=True).select_option('10')
        self.assertEqual(self.page.locator('.staff-case-button').count(), 2)
        self.page.get_by_label('Поверх', exact=True).select_option('')
        self.assertEqual(self.page.locator('.staff-case-button').count(), 2)
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                for boss in ['nurse','doctor']:
                    self.page.evaluate('boss=>openStaffArchive(boss)',boss)
                    visual = self.page.locator('.staff-dossier-visual')
                    visual.scroll_into_view_if_needed()
                    image = visual.locator('img')
                    self.page.wait_for_function('()=>document.querySelector(".staff-dossier-image")?.naturalWidth>0')
                    frame = visual.bounding_box()
                    text = self.page.locator('.staff-identity-details').bounding_box()
                    if width > 600:
                        self.assertAlmostEqual(frame['y'],text['y'],delta=1)
                        self.assertGreaterEqual(text['x']-frame['x']-frame['width'],9)
                        self.assertLessEqual(text['x']-frame['x']-frame['width'],13)
                    else:
                        self.assertGreaterEqual(text['y'],frame['y']+frame['height'])
                    # Project measured source alpha bounds into the CSS viewport.
                    photo = image.bounding_box()
                    source_width = image.evaluate('e=>e.naturalWidth')
                    scale = photo['width']/source_width
                    self.assertAlmostEqual(photo['x']+312*scale,frame['x'],delta=1)
                    self.assertAlmostEqual(photo['x']+1069*scale,frame['x']+frame['width'],delta=1)
                    self.assertGreaterEqual(photo['y']+2*scale,frame['y']-1)
                    self.assertLessEqual(photo['y']+768*scale,frame['y']+frame['height']+1)
                    self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                    self.page.screenshot(path=str(results/f'compact-staff-{boss}-{width}x{height}.png'))
                self.page.evaluate('openRaidArchive()')
                for card in self.page.locator('.raid-archive-card').all():
                    visual = card.locator('.raid-card-visual')
                    frame = visual.bounding_box()
                    text = card.locator('.raid-card-details').bounding_box()
                    self.assertEqual(visual.evaluate('e=>getComputedStyle(e).borderTopWidth'),'0px')
                    self.assertEqual(visual.evaluate('e=>getComputedStyle(e).paddingLeft'),'0px')
                    if width > 600:
                        self.assertAlmostEqual(frame['y'],text['y'],delta=1)
                        self.assertLessEqual(text['x']-frame['x']-frame['width'],13)
                    self.assertTrue(card.locator('.raid-card-rewards').is_visible())
                    self.assertTrue(card.locator('.raid-card-personal-stamp').is_visible())
                self.page.screenshot(path=str(results/f'compact-raids-{width}x{height}.png'))
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,staffArchiveState,archive:readRaidArchive(),storage:{...localStorage}})'),before)

    def test_staff_forms_thumbnail_scale_and_prominent_personal_raid_stamps(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); openStaffArchive("doctor");')
        profile = self.page.evaluate('JSON.stringify({stats,staffArchiveState,storage:{...localStorage}})')
        self.page.get_by_role('button', name='Архівні документи', exact=True).click()
        text = self.page.locator('#staff-case-sheet').inner_text()
        self.assertNotRegex(text, r'5%|\d+/30|гаранті|drop chance|pity')
        self.assertIn('після успішного обстеження', text)
        self.page.get_by_role('button', name='Анкетні відомості', exact=True).click()
        self.assertEqual(self.page.locator('.staff-form-field dt').all_text_contents(),
                         ['Ім’я:','Номер справи:','Код:','Посада:','Поверх:','Відділення:','Локація:','Статус / примітка:'])
        self.assertEqual(self.page.locator('.staff-identity-note').count(),1)
        self.assertIn('КОНТАКТ ЗАФІКСОВАНО', self.page.locator('.staff-identity-header').inner_text())
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,staffArchiveState,storage:{...localStorage}})'),profile)
        results=ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openStaffArchive("doctor")')
                thumbnail=self.page.locator('.staff-case-photo')
                thumbnail.scroll_into_view_if_needed()
                self.assertGreaterEqual(thumbnail.bounding_box()['width'],69)
                self.assertEqual(self.page.locator('.staff-case-button.selected').evaluate('e=>getComputedStyle(e).gap'),'6px')
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                self.page.screenshot(path=str(results/f'personnel-form-{width}x{height}.png'))
                self.page.evaluate('openRaidArchive()')
                card=self.page.locator('.raid-archive-card').first
                stamp=card.locator(':scope > .raid-card-personal-stamp')
                self.assertEqual(stamp.count(),1)
                self.assertEqual(stamp.inner_text(),'MVP')
                self.assertIn('MVP: Пацієнт #404',card.inner_text())
                self.assertGreaterEqual(stamp.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'),30)
                self.assertGreaterEqual(stamp.evaluate('e=>parseInt(getComputedStyle(e).fontWeight)'),700)
                badge=stamp.bounding_box()
                if width>600:
                    detail=card.locator('.raid-card-details').bounding_box()
                    self.assertGreaterEqual(badge['x'],detail['x']+detail['width'])
                else:
                    photo=card.locator('.raid-card-visual').bounding_box()
                    self.assertGreaterEqual(badge['x'],photo['x']+photo['width'])
                self.assertGreaterEqual(badge['x'],0)
                self.assertLessEqual(badge['x']+badge['width'],width+1)
                self.page.screenshot(path=str(results/f'personal-mvp-{width}x{height}.png'))
        self.page.evaluate('''() => {
            startBossFight('nurse'); raidMembers[0].metrics.healing=1; callAllFriends(); Math.random=()=>0;
            for(let i=0;i<10;i++) friendsAutoAttackTick(); openRaidArchive();
        }''')
        card=self.page.locator('.raid-archive-card').first
        self.assertEqual(card.locator('.raid-card-personal-stamp').count(),0)
        self.assertIn('MVP: Сліпий Микола',card.inner_text())
        self.page.evaluate('startBossFight("nurse"); callAllFriends(); for(let i=0;i<10;i++) friendsAutoAttackTick(); openRaidArchive();')
        card=self.page.locator('.raid-archive-card').first
        self.assertEqual(card.locator('.raid-card-personal-stamp').count(),1)
        self.assertEqual(card.locator('.raid-card-personal-stamp').inner_text(),'УХИЛЯВСЯ ВІД ПРОЦЕДУРИ')
        self.assertEqual(card.locator('.raid-personal-mvp').count(),0)

    def test_partial_reward_save_recovers_without_duplicate_credit(self):
        self.context.add_init_script('''
            window.blockRewardSave=false;
            const originalSet=Storage.prototype.setItem;
            Storage.prototype.setItem=function(key,value) {
                if(window.blockRewardSave && key==='palata404_stats') throw new DOMException('Interrupted', 'QuotaExceededError');
                return originalSet.call(this,key,value);
            };
        ''')
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats(); startBossFight('nurse');
            window.blockRewardSave=true; performPlayerAttack();
        }''')
        self.assertEqual(self.state()['silver'], 181)
        self.assertTrue(self.page.locator('#victory-save-note').is_visible())
        self.assertEqual(self.page.evaluate('JSON.parse(localStorage.getItem("palata404_stats")).silver'),150)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['silver'],181)
        self.assertEqual(self.state()['exp'],52)
        self.assertEqual(self.state()['bossesKilled'],1)
        self.assertIsNone(self.page.evaluate('localStorage.getItem("palata404_pending_battle_reward")'))
        self.page.evaluate('openLastBattleResult(); handleVictory(); retryBattleResultSave();')
        self.assertEqual(self.state()['silver'],181)
        self.assertFalse(self.page.locator('#victory-save-note').is_visible())


if __name__ == '__main__':
    unittest.main()
