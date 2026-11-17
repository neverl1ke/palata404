"""Real clicks through the scaled game shell, including formerly covered targets.

No forced pointer actions, quest-state injection or collapsing-paper workaround.
"""
import unittest

from tests import test_game
from tests.quest_ui_support import complete, complete_call_cycle


class QuestDocumentActionTests(unittest.TestCase):
    setUpClass = classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(test_game.GameTests.tearDownClass.__func__)

    def setUp(self):
        self.errors = []
        self.context = self.browser.new_context(
            viewport={'width': 844, 'height': 390},
            reduced_motion='reduce', is_mobile=True, has_touch=True)
        self.context.route('https://**/*', lambda route: route.abort())
        self.page = self.context.new_page()
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(self.url + 'play.html')
        self.game = self.page.frames[1]
        self.ready()

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def ready(self):
        self.game.wait_for_function('window.PalataQuestPrototype && '
            'document.querySelector(".hospital-hud").dataset.assetsReady==="true"')
        self.page.wait_for_timeout(220)

    def room(self, room):
        if self.game.locator('.quest-room-tools').is_visible():
            self.game.locator('.quest-room-tools button').first.click()
        elif not self.game.locator('#map-modal').is_visible():
            self.game.locator('#location-card-box').click()
        self.game.locator(f'.quest-map-pin[data-room="{room}"]').dblclick(delay=40)
        self.game.wait_for_function('r=>PalataQuestPrototype.snapshot().room===r && '
            '!document.getElementById("quest-location-screen").classList.contains("hidden")', arg=room)

    def click_action(self, action, choice=False):
        mirror = self.game.locator(f'.scene-document-actions [data-scene-action="{action}"]')
        original = self.game.locator(f'[data-{"choice" if choice else "action"}="{action}"]').first
        (mirror if mirror.count() else original).click()

    def action(self, action, choices=()):
        self.click_action(action)
        for choice in choices:
            self.click_action(choice, choice=True)

    def test_trip_key_chain_is_reachable_with_document_open(self):
        # Prerequisite supplied by playing the normal patient clue, not by flags.
        self.room('A')
        self.action('inspectDoor', ['door', 'door'])
        self.room('collector')
        self.action('supplyNote', ['cabinet', 'cabinet'])
        self.room('procedure')
        self.action('record', ['record', 'copy'])
        self.room('doctor')
        self.action('observation', ['document', 'confirm'])
        self.game.locator('.quest-room-tools button').first.click()
        self.game.locator('#map-modal .btn-close-map').click()
        self.game.locator('.room-trip-switch').click()
        self.room('collector')
        self.action('takeHandle', ['cabinet', 'cabinet'])
        self.room('A')
        self.action('unlockB', ['door', 'handle', 'door'])
        self.room('B')
        self.action('unlockC')
        self.assertTrue(self.game.locator('.scene-paper:not(.is-collapsed)').is_visible())
        tray = self.game.locator('.scene-document-actions [data-scene-action="tray"]')
        tray.click()
        self.click_action('keyC', choice=True)
        self.click_action('lock', choice=True)
        self.click_action('frame', choice=True)
        self.assertTrue(self.game.evaluate('PalataQuestPrototype.snapshot().flags.unlockC'))
        self.page.reload()
        self.game = self.page.frames[1]
        self.ready()
        self.assertTrue(self.game.evaluate('PalataQuestPrototype.snapshot().flags.unlockC'))

    def test_call_workbench_opens_from_collapsed_paper_and_redeems_once(self):
        self.room('doctor')
        self.action('accept:d1')
        self.room('ward407')
        self.game.locator('[data-room-info-toggle]').click()
        self.assertEqual(self.game.locator('.scene-paper.is-collapsed').count(), 1)
        self.assertTrue(self.game.locator('.scene-paper').is_hidden())
        # The actual bell opens a work surface even when the side paper is shut.
        self.game.locator('[data-action="job:bell407"]').click()
        self.assertTrue(self.game.locator('.quest-workbench').is_visible())
        complete(self.game,'job:bell407',open_board=False)
        self.room('ward408')
        complete(self.game,'job:bell408')
        self.room('doctor')
        before = self.game.evaluate('({silver:stats.silver,exp:stats.exp})')
        # Two primary observations cannot finish a revision4 service order.
        self.assertFalse(self.game.evaluate('PalataQuestEngine.ready(PalataQuestPrototype.snapshot(),"d1")'))
        self.assertEqual(self.game.locator('[data-action="claim:d1"],[data-scene-action="claim:d1"]').count(), 0)
        self.assertFalse(self.game.evaluate('PalataQuestEngine.actions(PalataQuestPrototype.snapshot()).some(a=>a.id==="claim:d1")'))
        complete_call_cycle(self.game)
        self.assertEqual(self.game.evaluate('({silver:stats.silver,exp:stats.exp})'), before)
        self.assertTrue(self.game.evaluate('''()=>{
            const state=PalataQuestPrototype.snapshot(),job=state.jobs.d1;
            return job.revision===4&&job.active&&job.count===0&&job.work.authorized&&
                ['ward407','ward408'].every(room=>job.work.initial[room].condition==='working'||
                    job.work.services[room].performed&&job.work.services[room].tested&&job.work.services[room].confirmed)&&
                PalataQuestEngine.ready(state,'d1');
        }'''))
        self.room('doctor')
        self.action('claim:d1')
        self.assertEqual(self.game.evaluate('PalataQuestPrototype.snapshot().jobs.d1.count'), 1)
        after = self.game.evaluate('({silver:stats.silver,exp:stats.exp})')
        self.assertEqual(after, {'silver': before['silver'] + 10, 'exp': before['exp'] + 20})
        self.assertEqual(self.game.locator('[data-action="claim:d1"]').count(), 0)
        self.page.reload()
        self.game = self.page.frames[1]
        self.ready()
        self.assertEqual(self.game.evaluate('({silver:stats.silver,exp:stats.exp})'), after)


if __name__ == '__main__':
    unittest.main()
