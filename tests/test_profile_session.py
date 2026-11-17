"""Real two-tab entry, saved collector result and session lifecycle. No save seeding."""
from pathlib import Path
import json
import unittest
from tests import test_game as support

OUT = Path('/dev/shm/floor10-next-20261117/session-browser')


class ProfileSessionTests(unittest.TestCase):
    setUpClass = classmethod(support.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(support.GameTests.tearDownClass.__func__)

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 800})
        self.context.route('https://**/*', lambda route: route.abort())
        self.errors = []
        OUT.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def page(self):
        page = self.context.new_page()
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        return page

    def load(self, page):
        page.goto(self.url.replace('index.html', 'play.html'), wait_until='networkidle')
        return self.game(page)

    def game(self, page):
        page.wait_for_function('PalataProfileSession.state().status === "owner"')
        game = page.locator('#game-canvas').element_handle().content_frame()
        game.wait_for_function('window.PalataQuestPrototype && document.querySelector(".hospital-hud")?.dataset.assetsReady === "true"')
        return game

    def room(self, game, room):
        if game.locator('#quest-location-screen').is_visible():
            game.locator('.quest-room-tools button').first.click()
        elif game.locator('#map-modal').is_hidden():
            game.locator('#location-card-box').click()
        overview = game.locator('#floor-map-overview')
        if overview.count() and overview.is_visible():
            game.locator('.floor-map-overview-toggle').click()
        game.locator(f'.quest-map-pin[data-room="{room}"]').click()
        game.locator(f'[data-enter-room="{room}"]').click()
        game.wait_for_function('room => PalataQuestPrototype.snapshot().room === room && !document.getElementById("quest-location-screen").classList.contains("hidden")', arg=room)

    def collect(self, game):
        self.room(game, 'collector')
        choices = game.locator('[data-scene-action="collect"], [data-action="collect"]')
        next(choice for choice in choices.all() if choice.is_visible()).click()

    def snapshot(self, game):
        return game.evaluate('''() => ({
          quest: PalataQuestPrototype.snapshot(), silver:stats.silver, pills:stats.pills,
          stored:JSON.parse(localStorage.getItem('palata404_floor10_progress:'+encodeURIComponent(raidArchiveOwnerId))),
          storedStats:JSON.parse(localStorage.getItem('palata404_stats'))
        })''')

    def test_second_tab_never_loads_stale_state_and_cannot_rollback_or_recollect(self):
        first, second = self.page(), self.page()
        game = self.load(first)
        initial = self.snapshot(game)
        second.goto(first.url, wait_until='networkidle')
        second.wait_for_function('PalataProfileSession.state().reason === "occupied"')
        self.assertIsNone(second.locator('#game-canvas').get_attribute('src'))
        self.assertTrue(second.locator('#profile-session-notice').is_visible())
        self.collect(game)
        earned = self.snapshot(game)
        self.assertEqual(earned['silver'], initial['silver'] + 15)
        self.assertEqual(earned['pills'], initial['pills'] + 1)
        self.assertEqual(earned['quest']['collectorCount'], 1)
        second.screenshot(path=str(OUT/'second-tab-blocked.png'))
        second.goto('about:blank')  # Actual pagehide of the second tab.
        after = self.snapshot(game)
        self.assertEqual(after['stored']['collectorCount'], 1)
        self.assertEqual(after['storedStats']['silver'], earned['silver'])
        first.close()  # Actual child pagehide saves while parent still owns lock.
        resumed = self.load(second)
        loaded = self.snapshot(resumed)
        self.assertEqual(loaded['quest']['collectorCount'], 1)
        self.assertEqual(loaded['silver'], earned['silver'])
        self.assertEqual(loaded['pills'], earned['pills'])
        self.room(resumed, 'collector')
        self.assertFalse(resumed.evaluate('PalataQuestEngine.actions(PalataQuestPrototype.snapshot()).some(action=>action.id==="collect")'))
        self.assertEqual(self.snapshot(resumed)['silver'], earned['silver'])
        (OUT/'two-tab-result.json').write_text(json.dumps({'initial':initial,'earned':earned,'loaded':loaded}, ensure_ascii=False, indent=2))

    def test_owner_reload_loads_latest_progress_and_keeps_the_full_minute_deadline(self):
        page = self.page()
        game = self.load(page)
        self.collect(game)
        before = self.snapshot(game)
        page.reload(wait_until='networkidle')
        after = self.snapshot(self.game(page))
        self.assertEqual(after['quest']['collectorAt'], before['quest']['collectorAt'])
        self.assertEqual(after['quest']['transaction'], before['quest']['transaction'])
        self.assertEqual(after['silver'], before['silver'])
        self.assertEqual(after['pills'], before['pills'])

    def test_naked_canvas_cannot_bypass_the_session_shell(self):
        page = self.page()
        page.goto(self.url+'?canvas=1', wait_until='networkidle')
        page.wait_for_url('**/play.html?canvas=1')
        self.game(page)
        self.assertTrue(page.evaluate('PalataProfileSession.state().status === "owner"'))

    def test_unsupported_lock_api_keeps_existing_save_bytes_untouched(self):
        page = self.page()
        game = self.load(page)
        self.collect(game)
        before = page.evaluate('Object.fromEntries(Object.keys(localStorage).map(k=>[k,localStorage.getItem(k)]))')
        page.close()
        # Diagnostic API compatibility fixture, not a claimed player walkthrough.
        self.context.add_init_script('Object.defineProperty(navigator,"locks",{value:undefined})')
        unsupported = self.page()
        unsupported.goto(self.url.replace('index.html','play.html'), wait_until='networkidle')
        unsupported.wait_for_function('PalataProfileSession.state().reason === "unsupported"')
        self.assertIsNone(unsupported.locator('#game-canvas').get_attribute('src'))
        after = unsupported.evaluate('Object.fromEntries(Object.keys(localStorage).map(k=>[k,localStorage.getItem(k)]))')
        self.assertEqual(after, before)

    def test_restored_child_is_fenced_before_any_later_pageshow_save(self):
        page = self.page()
        game = self.load(page)
        before = self.snapshot(game)
        # Simulated persisted lifecycle event covers child-before-parent ordering.
        result = game.evaluate('''() => {
          dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));
          return {allowed:profileWritesAllowed(),saved:saveGameProgress()};
        }''')
        self.assertEqual(result, {'allowed':False,'saved':False})
        self.assertEqual(page.evaluate('PalataProfileSession.state().reason'), 'restored')
        self.assertEqual(self.snapshot(game)['stored'], before['stored'])

    def test_visibility_resume_is_fenced_before_the_games_timer_handlers(self):
        page = self.page()
        game = self.load(page)
        # A deterministic lifecycle diagnostic; native ordering is checked by
        # the independent browser probe, not claimed by this synthetic event.
        result = game.evaluate('''() => {
          dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}));
          const finalSaveAllowed=profileWritesAllowed();
          document.dispatchEvent(new Event('visibilitychange'));
          return {finalSaveAllowed, resumeAllowed:profileWritesAllowed(), saved:saveGameProgress()};
        }''')
        self.assertEqual(result, {'finalSaveAllowed':True,'resumeAllowed':False,'saved':False})
        self.assertEqual(page.evaluate('PalataProfileSession.state().reason'), 'restored')


if __name__ == '__main__':
    unittest.main()
