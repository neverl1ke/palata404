"""Persisted evidence copies through actual game controls, without seeded saves.

These checks inspect DOM and public snapshots for assertions only. No solver,
forced pointer events, engine dispatch or storage write is used by the driver.
"""
from pathlib import Path
import json
import unittest

from tests import test_game
from tests import test_floor10_orientation as orientation
from tests import test_floor10_quest_revisions as revisions
from tests.quest_ui_support import action, operate

OUT = Path('/dev/shm/quest-depth-20261117/notes-check/browser')


class QuestNotesTests(unittest.TestCase):
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
    reload_home = revisions.QuestRevisionTests.reload_home

    def setUp(self):
        self.context = None
        self.errors = []
        self.measurements = []
        self.notes = []
        self.maxDiff = None

    def capture(self, suffix='last'):
        if not getattr(self, 'page', None) or self.page.is_closed():
            return
        OUT.mkdir(parents=True, exist_ok=True)
        viewport = self.page.viewport_size
        stem = f'{self._testMethodName}-{viewport["width"]}x{viewport["height"]}-{suffix}'
        self.page.screenshot(path=str(OUT/(stem+'.png')))
        OUT.joinpath(stem+'.json').write_text(json.dumps({
            'viewport': viewport, 'progress': self.progress(), 'ledger': self.ledger(),
            'notes': self.notes, 'measurements': self.measurements, 'pageErrors': self.errors,
        }, ensure_ascii=False, indent=2))

    def tearDown(self):
        if self.context:
            try:
                self.capture()
            finally:
                self.context.close()
        self.assertEqual(self.errors, [])

    def journal(self, identifier, category):
        self.home()
        self.game.locator('.hud-task').tap()
        self.game.locator('#tasks-modal').wait_for(state='visible')
        self.game.locator(f'[data-quest-tab="{category}"]').tap()
        card = self.game.locator(f'[data-quest-id="{identifier}"]')
        detail = card.locator(f'details[data-quest-notes="{identifier}"]')
        self.assertEqual(detail.count(), 1)
        return card, detail

    def read_notes(self, identifier, category):
        card, detail = self.journal(identifier, category)
        summary = detail.locator('summary')
        self.assert_touch_target(summary, 'notes-toggle:'+identifier)
        if not detail.evaluate('e=>e.open'):
            summary.tap()
        self.assertTrue(detail.evaluate('e=>e.open'))
        self.assert_readable_font(detail.locator('p').first, 14, 'notes-scope')
        return card, detail

    def close_journal(self):
        self.game.locator('#tasks-modal .modal-header button').tap()
        self.game.locator('#tasks-modal').wait_for(state='hidden')

    def assert_reading_is_view_only(self, detail, rounds=3):
        before = self.progress()
        economic = self.ledger()
        for _ in range(rounds):
            summary = detail.locator('summary')
            summary.tap()
            summary.tap()
            self.assertTrue(detail.evaluate('e=>e.open'))
        self.assertEqual(self.progress(), before)
        self.assertEqual(self.ledger(), economic)
        self.assertEqual(detail.locator('button,[data-work-op],[data-action],[data-choice]').count(), 0,
                         'the notebook must not contain a second action/claim route')

    def test_story_notes_require_completed_source_steps_and_survive_reload(self):
        self.open_game(844, 390)
        _, empty = self.read_notes('С1', 'story')
        self.assertEqual(empty.locator('[data-quest-note]').count(), 0)
        self.assertIn('после осмотра предмета', empty.inner_text())
        self.assert_reading_is_view_only(empty)
        self.capture('unread-sources-remain-empty')
        self.close_journal()
        self.room('A')
        action(self.game, 'inspectDoor')
        mirror = self.game.locator('.scene-document-actions [data-scene-action="door"]')
        (mirror if mirror.count() else self.game.locator('[data-choice="door"]').first).tap()
        self.assertEqual(self.progress()['interactions']['inspectDoor'], 1)
        _, detail = self.read_notes('С1', 'story')
        self.assertEqual(detail.locator('[data-quest-note]').count(), 1)
        self.assertEqual(detail.locator('[data-quest-note="inspectDoor:0"]').count(), 1)
        self.assertEqual(detail.locator('[data-quest-note="inspectDoor:1"]').count(), 0)
        original = detail.locator('[data-quest-note]').inner_text()
        self.assertIn('обычная ручка убирает язычок', original)
        self.assert_reading_is_view_only(detail)
        self.game.locator('[data-quest-tab="story"]').tap()
        detail = self.game.locator('details[data-quest-notes="С1"]')
        self.assertTrue(detail.evaluate('e=>e.open'), 'ordinary journal re-render should keep an open source readable')
        self.capture('one-completed-source')
        self.close_journal()
        self.reload_home()
        _, restored = self.read_notes('С1', 'story')
        self.assertEqual(restored.locator('[data-quest-note]').count(), 1)
        self.assertEqual(restored.locator('[data-quest-note]').inner_text(), original)
        self.assertEqual(self.progress()['interactions']['inspectDoor'], 1)
        self.assert_reading_is_view_only(restored)
        self.capture('source-after-real-reload')

    def test_inspected_container_is_readable_from_journal_on_both_phone_sizes_without_progress(self):
        for width, height in [(640, 320), (844, 390)]:
            with self.subTest(viewport=(width, height)):
                self.open_game(width, height)
                self.room('nurse')
                action(self.game, 'accept:k1')
                _, empty = self.read_notes('k1', 'nurse')
                self.assertEqual(empty.locator('[data-quest-note]').count(), 0)
                self.close_journal()
                self.room('procedure')
                action(self.game, 'job:tag')
                operate(self.game, 'inspect', 'pack-1')
                self.close_workbench()
                _, detail = self.read_notes('k1', 'nurse')
                self.assertEqual(detail.locator('[data-quest-note]').count(), 2)
                self.assertEqual(detail.locator('[data-quest-note="pack-1"]').count(), 1)
                self.assertEqual(detail.locator('[data-quest-note="pack-0"],[data-quest-note="pack-2"],[data-quest-note="pack-3"]').count(), 0)
                contents = detail.locator('[data-quest-note="pack-1"]').inner_text()
                self.assertIn('Пломба:', contents)
                self.assertIn('Партия:', contents)
                self.assert_reading_is_view_only(detail)
                sheet = self.game.locator('#tasks-modal .quest-sheet')
                self.assertTrue(sheet.evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
                detail.locator('[data-quest-note="pack-1"]').scroll_into_view_if_needed()
                self.capture('inspected-pack-in-journal')
                self.close_journal()
                self.reload_home()
                _, restored = self.read_notes('k1', 'nurse')
                self.assertEqual(restored.locator('[data-quest-note="pack-1"]').inner_text(), contents)
                self.assertEqual(self.progress()['jobs']['k1']['work']['inspected'], ['pack-1'])
                self.assertEqual(self.progress()['jobs']['k1']['done'], {})
                self.assertEqual(self.ledger()['cargo'], [])
                self.assert_reading_is_view_only(restored)
                self.capture('inspected-pack-after-real-reload')


if __name__ == '__main__':
    unittest.main()
