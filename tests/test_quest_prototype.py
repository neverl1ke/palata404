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
        page.get_by_role('button', name='Задания', exact=True).click()
        self.assertTrue(page.get_by_text('С1 Свой маршрут', exact=False).is_visible())
        page.locator('[data-task-mode=trip]').click()
        self.assertEqual(page.locator('#quest-list .quest-card').count(),4)
        page.locator('#quest-list .quest-card').first.get_by_role('button',name='Перейти к заданию').click()
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().mode'),'patient')
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().room'),'ward404')
        out=ROOT/'test-results'/'quest-prototype';out.mkdir(parents=True,exist_ok=True)
        page.locator('.quest-blueprint-image').wait_for(state='visible')
        page.wait_for_function("document.querySelector('.quest-blueprint-image').naturalWidth>0")
        self.assertEqual(page.locator('.quest-map-pin').count(),17)
        self.assertEqual(page.locator('.quest-plan-label').count(),14)
        self.assertIn('quest-plan.svg',page.locator('.quest-blueprint-image').get_attribute('src'))
        self.assertTrue(page.locator('.quest-official-header .document-emblem').is_visible())
        page.screenshot(path=str(out/'map-patient-desktop.png'))
        def room(id):
            back=page.get_by_role('button',name='Вернуться к карте',exact=True)
            if back.is_visible(): back.click()
            page.locator(f'[data-room="{id}"]').click()
        def action(id):
            page.locator(f'[data-action="{id}"]').click()
            choices={'markerA':['sign','A','trace'],'markerB':['frame','AB','trace'],'unlockB':['A','AB','B'],'exercise':['L','R','M'],'record':['record','copy'],'observation':['clock','note'],'unlockC':['record','note','door'],'stairsPatient':['sign','mark'],'exit':['lock','sign']}
            for choice in choices.get(id,[]): page.locator(f'[data-choice="{choice}"]').click()
        room('gym')
        self.assertEqual(page.locator('[data-scene-room="gym"]').count(),1)
        self.assertTrue(page.locator('#map-modal').is_hidden())
        self.assertTrue(page.locator('#quest-location-screen').is_visible())
        page.wait_for_function("document.querySelector('.scene-painting').naturalWidth > 0")
        page.screenshot(path=str(out/'scene-gym.png'))
        action('exercise')
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().exerciseCount'),1)
        for destination in ['ward405','collector','toilet','A','B','nurse','technical','linen','ward406','B','C','ward407','ward408','stairs','C','B','A','ward404']:
            room(destination)
            self.assertEqual(page.locator('[data-scene-room="'+destination+'"]').count(),1)
            page.wait_for_function("document.querySelector('.scene-painting').naturalWidth > 0")
        page.get_by_role('button',name='Вернуться к карте',exact=True).click()
        page.emulate_media(reduced_motion='no-preference')
        room('A')
        page.locator('.quest-traveller').wait_for(state='visible')
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().room'),'ward404')
        page.get_by_role('button',name='Вернуться к карте',exact=True).wait_for(state='visible')
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().room'),'A')
        page.screenshot(path=str(out/'location-arrival.png'))
        page.emulate_media(reduced_motion='reduce')
        page.locator('[data-action="markerA"]').click()
        page.locator('[data-choice="bench"]').click()
        self.assertFalse(page.evaluate('!!PalataQuestPrototype.snapshot().flags.markerA'))
        page.locator('[data-choice="sign"]').focus();page.locator('[data-choice="sign"]').press('Enter')
        page.reload();page.wait_for_function('!!window.PalataQuestPrototype')
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().interactions.markerA'),1)
        page.locator('#nav-map-btn').click();room('A')
        page.locator('[data-action="markerA"]').click()
        page.locator('[data-choice="A"]').click();page.locator('[data-choice="trace"]').click()
        for kind, value in [('room','B'),('action','markerB'),('room','procedure'),('action','record'),('room','B'),('room','C'),('room','doctor'),('action','observation'),('room','stairs'),('action','stairsPatient'),('room','C'),('room','B'),('room','A'),('room','ward404')]:
            (room if kind == 'room' else action)(value)
        page.get_by_role('button',name='Вернуться к карте',exact=True).click()
        page.locator('#map-modal .btn-close-map').click()
        page.locator('.room-trip-switch').click()
        page.locator('#nav-map-btn').click()
        self.assertEqual(page.locator('.quest-locked-zone').count(),2)
        room('B')
        self.assertIn('оттиски',page.locator('.quest-floor>.quest-note').inner_text())
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().room'),'ward404')
        page.screenshot(path=str(out/'map-trip-locked.png'))
        room('A');
        page.get_by_role('button',name='Вернуться к карте',exact=True).click()
        page.locator('#map-modal .btn-close-map').click()
        page.locator('.room-trip-switch').click()
        self.assertTrue(page.locator('[data-room="ward404"]').evaluate("e=>e.classList.contains('is-target')"))
        room('ward404')
        page.locator('.quest-location').get_by_role('button',name='Выйти из Трипа',exact=True).click()
        self.assertEqual(page.evaluate('PalataQuestPrototype.snapshot().mode'),'patient')
        page.locator('.quest-location').get_by_role('button',name='Войти в Трип',exact=True).click()
        room('A'); action('unlockB');
        page.get_by_role('button',name='Вернуться к карте',exact=True).click()
        self.assertEqual(page.locator('[data-section="B"]').count(),0)
        self.assertEqual(page.locator('[data-section="C"]').count(),1)
        room('B'); action('unlockC'); room('C'); room('doctor')
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
        page.get_by_role('button', name='Задания', exact=True).click()
        out=ROOT/'test-results'/'quest-prototype';out.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(out/'quests-desktop.png'))
        page.set_viewport_size({'width':844,'height':390})
        page.goto(base+'/quest-play.html')
        frame=page.frame_locator('#game-canvas')
        frame.locator('#nav-map-btn').click()
        frame.locator('.quest-blueprint-image').wait_for(state='visible')
        frame.locator('#map-modal').get_by_role('button',name='Выйти из Трипа',exact=True).click()
        self.assertIn('Пациент',frame.locator('.quest-floor h3').inner_text())
        frame.locator('#map-modal').get_by_role('button',name='Открыть задания',exact=True).click()
        self.assertEqual(frame.locator('[data-task-mode=patient]').get_attribute('aria-pressed'),'true')
        frame.locator('[data-task-mode=trip]').click()
        frame.locator('#quest-list .quest-card').first.get_by_role('button',name='Перейти к заданию').click()
        self.assertIn('другого режима',frame.locator('.quest-floor>.quest-note').inner_text())
        self.assertIn('Пациент',frame.locator('.quest-floor h3').inner_text())
        page.screenshot(path=str(out/'map-mobile-landscape.png'))
        frame.locator('[data-room="gym"]').click()
        frame.locator('[data-action="exercise"]').click()
        frame.locator('[data-choice="L"]').click()
        page.screenshot(path=str(out/'scene-mobile-landscape.png'))
        frame.get_by_role('button',name='Вернуться к карте',exact=True).click()
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(out/'map-mobile-portrait-shell.png'))
        self.assertEqual(errors, [])
        context.close()

if __name__ == '__main__':
    unittest.main()
