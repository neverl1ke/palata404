"""Player guidance follows real work, handoffs and native scaled-shell targets.

No state seeds or forced pointer actions. Workbench helpers use their public
evidence; this is a technical check, not the separate blind-player audit.
"""
from pathlib import Path
import json
import unittest

from tests import test_game
from tests import test_floor10_orientation as orientation
from tests import test_floor10_quest_revisions as revisions
from tests.quest_ui_support import action, complete

OUT = Path('/dev/shm/quest-playability-audit-20261117/technical/guidance-tests')


class QuestPlayerGuidanceTests(unittest.TestCase):
    setUpClass = classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(test_game.GameTests.tearDownClass.__func__)
    open_game = orientation.Floor10OrientationTests.open_game
    progress = orientation.Floor10OrientationTests.progress
    ledger = orientation.Floor10OrientationTests.ledger
    assert_touch_target = orientation.Floor10OrientationTests.assert_touch_target
    assert_readable_font = orientation.Floor10OrientationTests.assert_readable_font
    plan = orientation.Floor10OrientationTests.plan
    open_map = orientation.Floor10OrientationTests.open_map
    preview = orientation.Floor10OrientationTests.preview
    close_workbench = orientation.Floor10OrientationTests.close_workbench
    back_to_map = orientation.Floor10OrientationTests.back_to_map
    show_map = orientation.Floor10OrientationTests.show_map
    room = orientation.Floor10OrientationTests.room
    home = orientation.Floor10OrientationTests.home
    story_action = orientation.Floor10OrientationTests.story_action
    reload_home = revisions.QuestRevisionTests.reload_home

    def setUp(self):
        self.context = None
        self.errors = []
        self.measurements = []
        self.notes = []
        self.maxDiff = None

    def capture(self, label='last'):
        if not getattr(self, 'page', None) or self.page.is_closed():
            return
        OUT.mkdir(parents=True, exist_ok=True)
        viewport = self.page.viewport_size
        stem = f'{self._testMethodName}-{viewport["width"]}x{viewport["height"]}-{label}'
        self.page.screenshot(path=str(OUT/(stem+'.png')))
        OUT.joinpath(stem+'.json').write_text(json.dumps({
            'progress': self.progress(), 'ledger': self.ledger(), 'notes': self.notes,
            'measurements': self.measurements, 'errors': self.errors}, ensure_ascii=False, indent=2))

    def tearDown(self):
        if self.context:
            try:
                self.capture()
            finally:
                self.context.close()
        self.assertEqual(self.errors, [], 'Unexpected actual-game runtime error')

    def journal_card(self, identifier):
        self.home()
        self.game.locator('.hud-task').tap()
        self.game.locator('#tasks-modal').wait_for(state='visible')
        self.game.locator('[data-task-mode="patient"]').tap()
        tab = 'doctor' if identifier.startswith('d') else 'nurse'
        self.game.locator(f'[data-quest-tab="{tab}"]').tap()
        card = self.game.locator(f'[data-quest-id="{identifier}"]')
        card.scroll_into_view_if_needed()
        return card

    def assert_target_exposed_without_test_scroll(self, destination):
        # Do not call scrollIntoView/assert_touch_target on this pin: the game
        # itself must expose it after the journal CTA.
        self.game.evaluate('''async()=>{
            await new Promise(requestAnimationFrame);
            await new Promise(requestAnimationFrame);
        }''')
        target = self.game.locator('.quest-map-pin.is-target')
        self.assertEqual(target.count(), 1)
        self.assertEqual(target.get_attribute('data-room'), destination)
        record = target.evaluate('''pin=>{
            const r=pin.getBoundingClientRect(),view=pin.closest('.quest-blueprint-viewport'),
                v=view.getBoundingClientRect(),hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
            return{pin:{left:r.left,top:r.top,right:r.right,bottom:r.bottom},
                view:{left:v.left,top:v.top,right:v.right,bottom:v.bottom},
                centerHit:!!hit&&(hit===pin||pin.contains(hit)),
                pan:{x:view.scrollLeft,y:view.scrollTop},
                nestedPan:{x:pin.parentElement.scrollLeft,y:pin.parentElement.scrollTop}};
        }''')
        self.notes.append({'label': 'game-centered-target', 'destination': destination, **record})
        for edge in ['left', 'top']:
            self.assertGreaterEqual(record['pin'][edge], record['view'][edge]-1, record)
        for edge in ['right', 'bottom']:
            self.assertLessEqual(record['pin'][edge], record['view'][edge]+1, record)
        self.assertTrue(record['centerHit'], record)
        self.assertEqual(record['nestedPan'], {'x': 0, 'y': 0})

    def giver_actions(self):
        # The room keeps both mirrored physical actions and original paper
        # actions. Priority may promote an original before the mirror group.
        # Compare their complete visible document order, preserving handlers.
        controls = self.game.locator('.scene-paper button[data-action],.scene-paper button[data-scene-action]')
        evidence = controls.evaluate_all('''buttons=>buttons.map(button=>({
            id:button.dataset.action||button.dataset.sceneAction,
            text:button.textContent.trim(),parent:button.parentElement.className,
            visible:!!button.getClientRects().length}))''')
        self.notes.append({'label': 'all-giver-controls-in-document-order', 'controls': evidence})
        return [item['id'] for item in evidence if item['visible']]

    def test_ready_and_completed_nonrepeat_orders_match_real_offers_and_handoffs(self):
        self.open_game(844, 390)
        for identifier, destination, work_id, giver in [
                ('k1', 'procedure', 'job:tag', 'nurse'),
                ('k3', 'procedure', 'job:copies', 'nurse'),
                ('d2', 'doctor', 'job:log', 'doctor')]:
            self.room(giver)
            action(self.game, 'accept:'+identifier)
            self.room(destination)
            complete(self.game, work_id)
            card = self.journal_card(identifier)
            self.assertIn('Готово к сдаче', card.locator('p').first.inner_text())
            self.assertNotIn('Взять у', card.locator('p').first.inner_text())
            before = self.progress()
            economic = self.ledger()
            card.get_by_role('button', name='Показать на карте').tap()
            self.plan()
            self.assert_target_exposed_without_test_scroll(giver)
            self.assertEqual(self.progress(), before)
            self.assertEqual(self.ledger(), economic)
            self.room(giver)
            order = self.giver_actions()
            self.notes.append({'ready': identifier, 'giverActionOrder': order})
            self.assertTrue(order)
            self.assertEqual(order[0], 'claim:'+identifier)
            before_money = self.game.evaluate('({exp:stats.exp,silver:stats.silver})')
            reward = self.game.evaluate('id=>PalataQuestEngine.payouts[id]', identifier)
            action(self.game, 'claim:'+identifier)
            self.assertEqual(self.game.evaluate('({exp:stats.exp,silver:stats.silver})'), {
                'exp': before_money['exp']+reward['exp'], 'silver': before_money['silver']+reward['silver']})
            card = self.journal_card(identifier)
            detail = card.locator('p').first.inner_text()
            self.notes.append({'completed': identifier, 'detail': detail, 'card': card.inner_text()})
            self.assertIn('Поручение выполнено', detail)
            self.assertNotIn('Взять у', detail)
            self.assertEqual(card.get_by_role('button', name='Показать на карте').count(), 0)
            self.assertFalse(self.game.evaluate('id=>PalataQuestEngine.actions({...PalataQuestPrototype.snapshot(),room:PalataQuestEngine.jobs[id].giver}).some(a=>a.id==="accept:"+id)', identifier))
            self.capture(identifier+'-completed')
            self.game.locator('#tasks-modal .modal-header button').tap()
            self.reload_home()

    def test_touch_filters_target_centering_and_requested_offer_remain_reachable(self):
        for width, height in [(640, 320), (844, 390)]:
            with self.subTest(viewport=(width, height)):
                self.open_game(width, height)
                before = self.progress()
                economic = self.ledger()
                self.game.locator('.hud-task').tap()
                journal = self.game.locator('#tasks-modal')
                journal.wait_for(state='visible')
                cue = journal.locator('.quest-mobile-scroll-cue')
                self.assertTrue(cue.is_visible())
                self.assert_readable_font(journal.locator('.quest-note').first, 14, 'journal-scroll-instruction')
                row = journal.locator('.quest-filter-row')
                self.assertEqual(row.locator('button').count(), 5)
                for selector in ['[data-quest-tab="story"]', '[data-quest-tab="nurse"]',
                        '[data-quest-tab="doctor"]', '[data-task-mode="trip"]', '[data-task-mode="patient"]']:
                    control = row.locator(selector)
                    self.assert_touch_target(control, 'journal-filter:'+selector)
                    control.tap()
                    self.assertEqual(self.progress(), before)
                    self.assertEqual(self.ledger(), economic)
                self.assertTrue(journal.locator('.quest-sheet').evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
                tops = row.locator('button').evaluate_all('buttons=>buttons.map(button=>button.getBoundingClientRect().top)')
                self.assertLessEqual(max(tops)-min(tops), 1)
                card = journal.locator('[data-quest-id="d2"]')
                card.get_by_role('button', name='Показать на карте').tap()
                self.plan()
                self.assert_target_exposed_without_test_scroll('doctor')
                self.assertEqual(self.progress(), before)
                self.assertEqual(self.ledger(), economic)
                self.capture('doctor-target-view-only')
                self.room('doctor')
                self.assertEqual(self.giver_actions()[0], 'accept:d2')
                instruction = self.game.locator('.scene-paper>.quest-note').first.inner_text()
                self.assertIn('Коснитесь', instruction)
                self.assertNotIn('Enter', instruction)
                action(self.game, 'accept:d2')
                self.assertTrue(self.progress()['jobs']['d2']['active'])
                self.assertFalse(self.progress()['jobs'].get('d1', {}).get('active', False))
                self.assertFalse(self.progress()['jobs'].get('d3', {}).get('active', False))
                self.assertEqual(self.game.evaluate('({exp:stats.exp,silver:stats.silver})'), {
                    'exp': economic['exp'], 'silver': economic['silver']})
                self.capture('requested-d2-offer')

    def test_early_stair_inspection_and_real_sector_visit_preserve_route_on_reload(self):
        self.open_game(844, 390)
        self.room('stairs')
        self.story_action('stairsPatient', ['sign'])
        partial = self.progress()
        # A real wrong choice at this stage must not erase the first saved step.
        wrong = self.game.locator('[data-scene-action="descend"]')
        if not wrong.count():
            wrong = self.game.locator('[data-choice="descend"]')
        wrong.click()
        self.assertEqual(self.progress(), partial)
        mirror = self.game.locator('[data-scene-action="mark"]')
        (mirror if mirror.count() else self.game.locator('[data-choice="mark"]')).click()
        self.assertTrue(self.progress()['flags']['stairsSeen'])
        self.assertFalse(self.progress()['visited'].get('B', False))
        economic = self.ledger()
        self.room('B')
        self.assertTrue(self.progress()['flags']['route'])
        after = self.ledger()
        for key in ['jobs', 'cargo', 'transaction', 'silver', 'exp', 'pills', 'bucks']:
            self.assertEqual(after[key], economic[key])
        self.assertFalse(self.progress()['flags'].get('unlockB', False))
        self.assertFalse(self.progress()['flags'].get('unlockC', False))
        self.reload_home()
        self.assertTrue(self.progress()['flags']['route'])
        self.room('stairs')
        self.assertEqual(self.game.locator('[data-action="stairsPatient"],[data-scene-action="stairsPatient"]').count(), 0)
        self.capture('route-derived-without-unrelated-action')


if __name__ == '__main__':
    unittest.main()
