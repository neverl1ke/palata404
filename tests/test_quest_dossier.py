"""Actual UI lifecycle for the approved case and read-only quest dossier.

Native controls, no forced clicks, seeded saves, solver, engine dispatch or
storage write. DOM facts determine the three approved case conclusions.
"""
from pathlib import Path
import json
import re
import unittest
from tests import test_game
from tests import test_floor10_orientation as orientation
from tests import test_floor10_quest_revisions as revisions
from tests import test_quest_player_guidance as guidance
from tests.quest_ui_support import action, operate

OUT = Path('/dev/shm/quest-depth-20261117/k3-save/browser')


class QuestDossierTests(unittest.TestCase):
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
    assert_target_exposed_without_test_scroll = guidance.QuestPlayerGuidanceTests.assert_target_exposed_without_test_scroll

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

    def open_dossier(self, identifier):
        self.home()
        self.game.locator('.hud-task').tap()
        self.game.locator('#tasks-modal').wait_for(state='visible')
        self.game.locator('[data-quest-tab="'+('doctor' if identifier.startswith('d') else 'nurse')+'"]').tap()
        launch = self.game.locator(f'[data-open-dossier="{identifier}"]')
        self.assert_touch_target(launch, 'open-dossier:'+identifier)
        launch.tap()
        dossier = self.game.locator(f'section[data-quest-dossier="{identifier}"]')
        self.assertTrue(dossier.is_visible())
        self.assert_touch_target(dossier.locator('[data-dossier-back]'), 'dossier-back')
        self.assert_touch_target(dossier.locator('[data-dossier-close]'), 'dossier-close')
        return dossier

    def no_overflow(self, dossier):
        self.assertTrue(dossier.evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
        self.assertTrue(dossier.locator('.quest-dossier-body').evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
        self.assertTrue(self.game.locator('#tasks-modal .quest-sheet').evaluate('e=>e.scrollWidth<=e.clientWidth+1'))

    def choice(self, field, choice):
        control = self.game.locator(f'[data-case-field="{field}"] [data-case-choice="{choice}"]')
        self.assert_touch_target(control, 'case-choice:'+field+':'+choice)
        control.tap()
        self.assertEqual(control.get_attribute('aria-pressed'), 'true')

    def source_facts(self):
        return self.game.locator('[data-case-source]').evaluate_all('''cards=>Object.fromEntries(cards.map(card=>[
            card.dataset.caseSource,Object.fromEntries([...card.querySelectorAll('dt')].map(term=>[
                term.textContent.trim(),term.nextElementSibling.textContent.trim()]))]))''')

    def test_new_k3_case_wrong_conclusions_partial_reload_dossier_and_single_original_reward(self):
        self.open_game(844, 390)
        self.room('nurse')
        action(self.game, 'accept:k3')
        self.assertEqual(self.progress()['jobs']['k3']['revision'], 3)
        before = self.ledger()
        dossier = self.open_dossier('k3')
        self.assertEqual(dossier.locator('[data-dossier-record]').count(), 0)
        self.assertFalse(self.progress()['jobs']['k3']['work']['sourcesRead'])
        self.assertEqual(self.ledger(), before)
        dossier.locator('[data-dossier-close]').tap()
        self.room('procedure')
        action(self.game, 'job:copies')
        self.game.wait_for_function('PalataQuestPrototype.snapshot().jobs.k3.work.sourcesRead===true')
        self.assertEqual(self.game.locator('.quest-workbench').get_attribute('data-work-kind'), 'caseCompare')
        self.assertEqual(self.game.locator('[data-case-source]').count(), 3)
        facts = self.source_facts()
        self.assertEqual(facts['source-1']['Палата'], facts['source-2']['Палата'])
        self.assertNotEqual(facts['source-2']['Палата'], facts['source-3']['Палата'])
        self.assertEqual(facts['source-2']['Факт'], facts['source-3']['Факт'])
        self.assertNotEqual(facts['source-1']['План'], facts['source-2']['Факт'])
        self.assertEqual(facts['source-2']['Подпись'], 'Неразборчива')
        self.notes.append({'renderedSourceFacts': facts})
        # Deliberately confuse planned/actual time and overclaim the unreadable
        # author. These are real visible choices, not malformed engine payloads.
        self.choice('room', 'differs')
        self.choice('time', 'error')
        self.choice('author', 'clara')
        partial = self.progress()['jobs']['k3']
        before_reject = self.ledger()
        operate(self.game, 'submit')
        self.assertEqual(self.progress()['jobs']['k3'], partial)
        self.assertEqual(self.ledger(), before_reject)
        self.assertTrue(self.game.locator('.quest-workbench').is_visible())
        self.assertNotIn('copies', self.progress()['cargo'])
        feedback = self.game.locator('.workbench-status').inner_text()
        self.assertRegex(feedback, 'план|факт|подпись|подтвержд|вывод')
        self.notes.append({'wrongConclusionFeedback': feedback})
        self.capture('wrong-conclusion-preserved')
        self.reload_home()
        self.assertEqual(self.progress()['jobs']['k3'], partial)
        dossier = self.open_dossier('k3')
        self.assertGreaterEqual(dossier.locator('[data-dossier-record]').count(), 4)
        reading = self.ledger()
        record = dossier.locator('[data-dossier-record]').filter(has_text='Направление').first
        self.assert_touch_target(record, 'dossier-source-direction')
        record.tap()
        copy = dossier.locator('[data-dossier-note]')
        self.assertIn(facts['source-1']['План'], copy.inner_text())
        self.assertIn('План', copy.inner_text())
        self.assertEqual(self.ledger(), reading)
        self.assertEqual(dossier.locator('[data-work-op],[data-action],[data-choice]').count(), 0)
        self.no_overflow(dossier)
        self.capture('sources-readable-after-reload')
        target = dossier.locator('[data-dossier-map]')
        self.assert_touch_target(target, 'dossier-map-view-only')
        target.tap()
        self.plan()
        self.assert_target_exposed_without_test_scroll('procedure')
        self.assertEqual(self.ledger(), reading)
        self.room('procedure')
        action(self.game, 'job:copies')
        self.assertEqual(self.progress()['jobs']['k3'], partial)
        self.choice('time', 'matchesActual')
        self.choice('author', 'unknown')
        operate(self.game, 'submit')
        self.assertTrue(self.progress()['jobs']['k3']['done']['copies'])
        self.assertIn('copies', self.progress()['cargo'])
        self.assertEqual(self.game.evaluate('({exp:stats.exp,silver:stats.silver})'), {'exp': before['exp'], 'silver': before['silver']})
        self.room('nurse')
        action(self.game, 'claim:k3')
        expected = {'exp': before['exp']+15, 'silver': before['silver']+8}
        self.assertEqual(self.game.evaluate('({exp:stats.exp,silver:stats.silver})'), expected)
        self.assertEqual(self.progress()['jobs']['k3']['count'], 1)
        self.assertFalse(self.progress()['jobs']['k3']['active'])
        self.assertNotIn('copies', self.progress()['cargo'])
        dossier = self.open_dossier('k3')
        self.assertIn('ПОРУЧЕНИЕ СДАНО', dossier.inner_text())
        result = dossier.locator('[data-dossier-record="result:copies"]')
        self.assertEqual(result.count(), 1)
        result.tap()
        qualified = dossier.locator('[data-dossier-note="result:copies"]').inner_text()
        self.assertIn('не подтверждено оригиналом', qualified)
        self.assertIn('перенесено верно', qualified)
        self.assertEqual(dossier.locator('[data-dossier-map]').count(), 0)
        self.capture('qualified-result-after-payout')
        dossier.locator('[data-dossier-close]').tap()
        self.reload_home()
        self.assertEqual(self.game.evaluate('({exp:stats.exp,silver:stats.silver})'), expected)
        self.assertEqual(self.progress()['jobs']['k3']['count'], 1)
        self.room('nurse')
        self.assertEqual(self.game.locator('[data-action="accept:k3"],[data-scene-action="accept:k3"],[data-action="claim:k3"],[data-scene-action="claim:k3"]').count(), 0)
        self.capture('nonrepeat-reload-no-extra-reward')

    def test_cta_contrast_and_case_source_reference_remain_view_only(self):
        self.open_game(640, 320)
        self.room('nurse')
        action(self.game, 'accept:k3')
        dossier = self.open_dossier('k3')
        target = dossier.locator('[data-dossier-map]')
        self.assert_touch_target(target, 'final-dossier-map-contrast')
        get_contrast = r"""e=>{
            const css=getComputedStyle(e),rgb=value=>value.match(/[\d.]+/g).slice(0,3).map(Number),
                luminance=value=>rgb(value).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4})
                    .reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0),
                foreground=luminance(css.color),background=luminance(css.backgroundColor);
            return{color:css.color,backgroundColor:css.backgroundColor,backgroundImage:css.backgroundImage,
                contrast:(Math.max(foreground,background)+.05)/(Math.min(foreground,background)+.05)};
        }"""
        style = target.evaluate(get_contrast)
        self.notes.append({'finalCtaStyle': style})
        self.assertEqual(style['backgroundImage'], 'none')
        self.assertGreaterEqual(style['contrast'], 4.5)
        self.capture('final-640-cta-readable')
        before = self.progress()
        economic = self.ledger()
        target.tap()
        self.plan()
        self.assert_target_exposed_without_test_scroll('procedure')
        self.assertEqual(self.progress(), before)
        self.assertEqual(self.ledger(), economic)
        self.room('procedure')
        action(self.game, 'job:copies')
        self.game.wait_for_function('PalataQuestPrototype.snapshot().jobs.k3.work.sourcesRead===true')
        before = self.progress()
        economic = self.ledger()
        self.game.locator('#custom-toast-notification').wait_for(state='hidden')
        jump = self.game.get_by_role('button', name='К выводам ↓', exact=True)
        self.assert_touch_target(jump, 'case-jump-to-verdicts')
        jump_style = jump.evaluate(get_contrast)
        self.assertEqual(jump_style['backgroundImage'], 'none')
        self.assertGreaterEqual(jump_style['contrast'], 4.5)
        jump.tap()
        self.game.wait_for_function('document.activeElement?.dataset.caseField==="room"')
        time_verdict = self.game.locator('[data-case-field="time"]')
        facts = self.source_facts()
        self.assertEqual(time_verdict.locator('.workbench-case-excerpt').all_text_contents(), [
            'План · '+facts['source-1']['План'],
            'Факт · '+facts['source-2']['Факт'],
            'Факт · '+facts['source-3']['Факт'],
        ])
        self.capture('case-evidence-by-verdict')
        source = time_verdict.locator('[data-case-source-link="source-2"]')
        self.assert_touch_target(source, 'case-source-reference')
        source.tap()
        self.game.wait_for_function('document.activeElement?.dataset.caseSource==="source-2"')
        self.assertEqual(self.progress(), before)
        self.assertEqual(self.ledger(), economic)
        self.capture('case-reference-is-navigation-only')
        back = self.game.get_by_role('button', name='Вернуться к выводу', exact=True)
        self.assert_touch_target(back, 'case-return-from-source')
        self.page.keyboard.press('Tab')
        self.assertTrue(back.evaluate('button=>document.activeElement===button'))
        self.page.keyboard.press('Enter')
        self.assertTrue(source.evaluate('link=>document.activeElement===link'))
        self.assertEqual(self.progress(), before)
        self.assertEqual(self.ledger(), economic)

    def test_dossier_reading_selection_back_context_and_close_are_native_view_only(self):
        for width, height in [(640, 320), (844, 390)]:
            with self.subTest(viewport=(width, height)):
                self.open_game(width, height)
                self.room('nurse')
                action(self.game, 'accept:k1')
                self.room('procedure')
                action(self.game, 'job:tag')
                operate(self.game, 'inspect', 'pack-1')
                self.close_workbench()
                dossier = self.open_dossier('k1')
                self.assertEqual(dossier.locator('[data-dossier-record]').count(), 2)
                before = self.progress()
                economic = self.ledger()
                for note in ['pack-1', 'request', 'pack-1']:
                    control = dossier.locator(f'[data-dossier-record="{note}"]')
                    self.assert_touch_target(control, 'dossier-copy-selector:'+note)
                    control.tap()
                    copy = dossier.locator(f'[data-dossier-note="{note}"]')
                    self.assertTrue(copy.is_visible())
                    self.assertEqual(control.get_attribute('aria-pressed'), 'true')
                    self.assertEqual(self.progress(), before)
                    self.assertEqual(self.ledger(), economic)
                    self.assert_readable_font(copy.locator('p').first, 14, 'dossier-source-provenance')
                self.no_overflow(dossier)
                self.capture('copied-marking-readable')
                back = dossier.locator('[data-dossier-back]')
                back.tap()
                self.assertTrue(dossier.is_hidden())
                self.game.wait_for_function('document.activeElement?.dataset.openDossier==="k1"')
                self.assertTrue(self.game.locator('[data-quest-tab="nurse"]').get_attribute('aria-pressed') == 'true')
                self.assertEqual(self.ledger(), economic)
                self.game.locator('[data-open-dossier="k1"]').tap()
                dossier = self.game.locator('section[data-quest-dossier="k1"]')
                self.game.locator('[data-dossier-back]').focus()
                self.page.keyboard.press('Escape')
                self.assertTrue(dossier.is_hidden())
                self.assertTrue(self.game.locator('#tasks-modal').is_visible())
                self.game.locator('[data-open-dossier="k1"]').tap()
                self.game.locator('[data-dossier-close]').tap()
                self.assertTrue(self.game.locator('#tasks-modal').is_hidden())
                self.assertEqual(self.progress(), before)
                self.assertEqual(self.ledger(), economic)
                self.capture('back-and-close-preserve-context')


if __name__ == '__main__':
    unittest.main()
