"""Native avatar animation pauses behind actual game overlays, without changing art.

Run with PALATA_BROWSER_PATH=/usr/bin/chromium python -m unittest
tests.test_avatar_visibility -v. Each test uses a disposable game profile.
"""
import functools
import os
from pathlib import Path
import threading
import unittest
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class AvatarVisibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
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
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 900})
        self.context.add_init_script('window.__PALATA_TEST_DIRECT__=true;')
        self.context.route('https://**/*', lambda route: route.abort())
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(f'http://127.0.0.1:{self.server.server_port}/index.html?canvas=1')
        self.page.wait_for_function('window.PalataQuestPrototype && document.querySelector(".hospital-hud").dataset.assetsReady==="true"')
        self.page.evaluate('''() => {
            equipPaperDollItem('upperBody', 'patient-pajama-top');
            equipPaperDollItem('pants', 'patient-pajama-pants');
            equipPaperDollItem('footwear', 'patient-pajama-slippers');
        }''')
        self.page.wait_for_function('''() => {
            const host=document.getElementById('character-paperdoll');
            const state=avatarCoreGamePreview.instances.get(host);
            return host.dataset.pajamaParts==='footwear pants top' && !state.running && !state.pending && state.live;
        }''')

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [], 'Unexpected browser errors')

    def state(self, host='character-paperdoll'):
        return self.page.evaluate('''id => {
            const s=avatarCoreGamePreview.instances.get(document.getElementById(id));
            return {paused:s.engine.paused, time:s.engine.time};
        }''', host)

    def assert_paused(self, host='character-paperdoll'):
        self.page.wait_for_function('id => avatarCoreGamePreview.instances.get(document.getElementById(id)).engine.paused', arg=host)
        before = self.state(host)['time']
        self.page.wait_for_timeout(180)
        self.assertEqual(self.state(host)['time'], before, 'Covered avatar continued advancing')

    def assert_running(self, host='character-paperdoll'):
        self.page.wait_for_function('id => !avatarCoreGamePreview.instances.get(document.getElementById(id)).engine.paused', arg=host)
        before = self.state(host)['time']
        self.page.wait_for_function('''([id,time]) => avatarCoreGamePreview.instances.get(document.getElementById(id)).engine.time>time''', arg=[host, before])

    def test_map_and_full_room_pause_then_resume(self):
        self.assert_running()
        self.page.evaluate('toggleMapModal(true)')
        self.assertTrue(self.page.locator('#map-modal').is_visible())
        self.assert_paused()
        self.page.locator('[data-room="ward404"]').dblclick()
        self.assertTrue(self.page.locator('#quest-location-screen').is_visible())
        self.assert_paused()
        self.page.locator('.quest-room-tools').get_by_role('button', name='До карти', exact=True).click()
        self.assertTrue(self.page.locator('#map-modal').is_visible())
        self.assert_paused()
        self.page.evaluate('toggleMapModal(false)')
        self.assert_running()
        self.page.evaluate('''() => {
            const engine=avatarCoreGamePreview.instances.get(document.getElementById('character-paperdoll')).engine;
            const pause=engine.pause.bind(engine);window.avatarTestPauseCalls=0;
            engine.pause=value=>{window.avatarTestPauseCalls++;return pause(value);};
            const glass=document.querySelector('.room-door-glass');
            for(let i=0;i<30;i++)glass.style.setProperty('--avatar-test',String(i));
        }''')
        self.page.wait_for_timeout(120)
        self.assertEqual(self.page.evaluate('window.avatarTestPauseCalls'), 0, 'Unrelated RAF style writes triggered overlay scans')

    def test_wardrobe_and_covering_dialog_stack(self):
        self.page.evaluate('openCustomization()')
        self.page.wait_for_function('''() => {
            const s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll'));
            return s?.engine && s.live && !s.running && !s.pending;
        }''')
        self.assert_paused()
        self.assert_running('wardrobe-paperdoll')
        self.page.evaluate('showWeaponDialog("Проверка", "<p>Подтверждение поверх гардероба</p>", [["Закрыть", hideWeaponDialog]])')
        self.assertTrue(self.page.locator('#weapon-dialog').is_visible())
        self.assert_paused('wardrobe-paperdoll')
        self.page.evaluate('hideWeaponDialog()')
        self.assert_running('wardrobe-paperdoll')
        # A lower layer with the same z-index must not cover the wardrobe.
        self.page.evaluate('document.getElementById("settings-modal").classList.remove("hidden")')
        self.assert_running('wardrobe-paperdoll')
        self.page.evaluate('document.getElementById("settings-modal").classList.add("hidden");closeCustomization()')
        self.assert_running()
        self.assert_paused('wardrobe-paperdoll')

    def test_dynamic_overlays_visibility_and_reduced_motion(self):
        self.assert_running()
        self.page.evaluate('''() => {
            const overlay=document.createElement('section');overlay.id='avatar-test-overlay';
            overlay.setAttribute('role','dialog');overlay.style.cssText='position:fixed;inset:0;z-index:2000;background:#222';
            document.body.append(overlay);
        }''')
        self.assert_paused()
        self.page.evaluate('document.getElementById("avatar-test-overlay").remove()')
        self.assert_running()
        # Exercise the document visibility event deterministically in headless.
        self.page.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))')
        self.assert_paused()
        self.page.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))')
        self.assert_running()
        self.page.emulate_media(reduced_motion='reduce')
        self.assert_paused()
        self.page.evaluate('toggleMapModal(true)')
        self.page.emulate_media(reduced_motion='no-preference')
        self.assert_paused()
        self.page.evaluate('toggleMapModal(false)')
        self.assert_running()
        # Loading must still allow a first native frame. It is not a modal blocker.
        self.page.evaluate('''() => {
            const loading=document.getElementById('scene-loading');loading.hidden=false;
            loading.classList.remove('is-ready');loading.style.transition='none';
        }''')
        self.assertTrue(self.page.locator('#scene-loading').is_visible())
        self.assert_running()
