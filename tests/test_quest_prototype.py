"""Isolated Chromium scenario. Run directly; never loads a user's browser profile."""
import functools
import http.server
import os
from pathlib import Path
import threading
import unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class QuestPrototypeBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.pw = sync_playwright().start()
        kwargs = {'headless': True}
        if os.getenv('PALATA_BROWSER_PATH'):
            kwargs['executable_path'] = os.environ['PALATA_BROWSER_PATH']
        cls.browser = cls.pw.chromium.launch(**kwargs)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def test_route_and_real_battle(self):
        context = self.browser.new_context(viewport={'width':1440,'height':900}, reduced_motion='reduce')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('dialog', lambda dialog: dialog.dismiss())
        base = f'http://127.0.0.1:{self.server.server_port}'
        page.goto(base + '/quest-test.html')
        page.wait_for_function('!!window.PalataQuestPrototype')
        page.get_by_role('button', name='Завдання', exact=True).click()
        self.assertTrue(page.get_by_text('С1 Власний маршрут', exact=False).is_visible())
        page.locator('[data-task-mode=trip]').click()
        self.assertEqual(page.locator('#quest-list .quest-card').count(),4)
        page.locator('#quest-list .quest-card').first.get_by_role('button',name='Перейти до завдання').click()
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().mode'),'patient')
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().room'),'ward404')
        out=ROOT/'test-results'/'quest-prototype';out.mkdir(parents=True,exist_ok=True)
        page.locator('.quest-blueprint-image').wait_for(state='visible')
        page.wait_for_function("document.querySelector('.quest-blueprint-image').naturalWidth>0")
        self.assertEqual(page.locator('.quest-map-pin').count(),17)
        page.screenshot(path=str(out/'map-patient-desktop.png'))
        def room(id): page.locator(f'[data-room="{id}"]').click()
        def action(id): page.locator(f'[data-action="{id}"]').click()
        for kind, value in [('room','A'),('action','markerA'),('room','B'),('action','markerB'),('room','procedure'),('action','record'),('room','B'),('room','C'),('room','doctor'),('action','observation'),('room','stairs'),('action','stairsPatient'),('room','C'),('room','B'),('room','A'),('room','ward404')]:
            (room if kind == 'room' else action)(value)
        page.locator('#map-modal .btn-close-map').click()
        page.locator('.room-trip-switch').click()
        page.locator('#nav-map-btn').click()
        self.assertEqual(page.locator('.quest-locked-zone').count(),2)
        room('B')
        self.assertIn('Зіставити',page.locator('.quest-floor>.quest-note').inner_text())
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().room'),'ward404')
        page.screenshot(path=str(out/'map-trip-locked.png'))
        room('A');
        page.locator('#map-modal .btn-close-map').click()
        page.locator('.room-trip-switch').click()
        self.assertTrue(page.locator('[data-room="ward404"]').evaluate("e=>e.classList.contains('is-target')"))
        room('ward404')
        page.locator('.quest-actions').get_by_role('button',name='Вийти з Трипу',exact=True).click()
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().mode'),'patient')
        page.locator('.quest-actions').get_by_role('button',name='Увійти в Трип',exact=True).click()
        room('A'); action('unlockB'); room('B'); action('unlockC'); room('C'); room('doctor')
        # Deterministic test fixture: retain real combat entry/victory/reward code,
        # but remove combat randomness and waiting from this progression test.
        page.evaluate('stats.baseDamage=10000;recalculateEquipmentStats();Math.random=()=>0.5;updateUI()')
        action('boss:doctor')
        self.assertTrue(page.evaluate('isBattleActive'))
        page.evaluate('performPlayerAttack()')
        page.wait_for_function('window.PalataQuestPrototype.snapshot().flags.doctorWon===true')
        page.evaluate('victoryContinueToMap()')
        room('stairs'); action('exit'); action('descend')
        self.assertTrue(page.evaluate('window.PalataQuestPrototype.snapshot().flags.exit'))
        page.reload()
        page.wait_for_function('!!window.PalataQuestPrototype')
        self.assertEqual(page.evaluate('window.PalataQuestPrototype.snapshot().room'), 'ward404')
        self.assertTrue(page.evaluate('window.PalataQuestPrototype.snapshot().flags.exit'))
        page.get_by_role('button', name='Завдання', exact=True).click()
        out=ROOT/'test-results'/'quest-prototype';out.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(out/'quests-desktop.png'))
        page.set_viewport_size({'width':844,'height':390})
        page.goto(base+'/quest-play.html')
        frame=page.frame_locator('#game-canvas')
        frame.locator('#nav-map-btn').click()
        frame.locator('.quest-blueprint-image').wait_for(state='visible')
        page.screenshot(path=str(out/'map-mobile-landscape.png'))
        self.assertEqual(errors, [])
        context.close()

if __name__ == '__main__':
    unittest.main()
