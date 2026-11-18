"""D2/D3 revision4 gameplay solved independently from rendered evidence.

Only the explicitly named historical-save case seeds storage. New orders use
real scene/map/workbench controls, never E.apply or hidden answer generators.
"""
from pathlib import Path
import json
import re
import unittest

from tests import test_floor10_orientation as orientation
from tests import test_game
from tests.quest_ui_support import action, complete, operate

OUT = Path('/dev/shm/floor10-orientation-world-20261117/quest-revisions-tests')


class QuestRevisionTests(unittest.TestCase):
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
    switch_mode = orientation.Floor10OrientationTests.switch_mode
    story_action = orientation.Floor10OrientationTests.story_action

    def setUp(self):
        self.context = None
        self.errors = []
        self.measurements = []
        self.maxDiff = None

    def capture(self, suffix='last'):
        if not getattr(self, 'page', None) or self.page.is_closed():
            return
        OUT.mkdir(parents=True, exist_ok=True)
        stem = self._testMethodName+'-'+suffix
        self.page.screenshot(path=str(OUT/(stem+'.png')))
        OUT.joinpath(stem+'.json').write_text(json.dumps({
            'progress': self.progress(), 'ledger': self.ledger(),
            'measurements': self.measurements, 'errors': self.errors}, ensure_ascii=False, indent=2))

    def tearDown(self):
        if self.context:
            try:
                self.capture()
            finally:
                self.context.close()
        self.assertEqual(self.errors, [])

    def money(self):
        return self.game.evaluate('({exp:stats.exp,silver:stats.silver})')

    def reload_home(self, compare=True):
        canonical = self.game.evaluate('PalataQuestEngine.restore(PalataQuestPrototype.snapshot())')
        economic = self.ledger()
        self.page.reload(wait_until='networkidle')
        self.game = self.page.locator('#game-canvas').element_handle().content_frame()
        self.game.wait_for_function('''window.PalataQuestPrototype&&
            document.querySelector('.hospital-hud')?.dataset.assetsReady==='true'&&
            document.documentElement.dataset.touchUi==='true' ''')
        self.assertTrue(self.game.locator('#quest-location-screen').is_hidden())
        self.assertTrue(self.game.locator('#map-modal').is_hidden())
        if compare:
            self.assertEqual(self.game.evaluate('PalataQuestEngine.restore(PalataQuestPrototype.snapshot())'), canonical)
            self.assertEqual(self.ledger(), economic)

    def accept(self, identifier):
        self.room('doctor')
        action(self.game, 'accept:'+identifier)
        self.assertEqual(self.progress()['jobs'][identifier]['revision'], 4)

    def claim_once(self, identifier, exp, silver, count):
        if self.progress()['mode'] != 'patient':
            self.switch_mode('patient')
        self.room('doctor')
        before = self.money()
        action(self.game, 'claim:'+identifier)
        expected = {'exp': before['exp']+exp, 'silver': before['silver']+silver}
        self.assertEqual(self.money(), expected)
        self.assertEqual(self.progress()['jobs'][identifier]['count'], count)
        self.assertEqual(self.game.locator(f'[data-action="claim:{identifier}"],[data-scene-action="claim:{identifier}"]').count(), 0)
        self.reload_home()
        self.assertEqual(self.money(), expected)
        self.assertEqual(self.progress()['jobs'][identifier]['count'], count)

    def timeline_sources(self):
        return self.game.locator('.workbench-source-slip').evaluate_all('''nodes=>nodes.map(e=>{
            const time=e.querySelector('.workbench-source-time').textContent.trim();
            const unreadable=time==='Время не читается';
            return {
                id:e.dataset.slipId,time,timeState:unreadable?'unreadable':'readable',
                room:e.querySelector('strong').textContent.trim(),
                note:e.querySelector('p').textContent.trim(),
                reverse:unreadable?e.closest('.quest-workbench').querySelector('.workbench-route-reverse p')?.textContent.trim()||null:null
            };
        })''')

    def chronological_sources(self, cards):
        readable = sorted((card for card in cards if re.fullmatch(r'\d{2}:\d{2}', card['time'])), key=lambda card: card['time'])
        obscured = [card for card in cards if card['timeState'] == 'unreadable']
        self.assertEqual(len(readable), 3)
        self.assertEqual(len(obscured), 1)
        source = obscured[0]
        self.assertIsNotNone(source['reverse'])
        relation = re.fullmatch(r'После .+ палаты (\d+); до .+ палаты (\d+)\.', source['reverse'])
        self.assertIsNotNone(relation, 'Chronology must be justified by the visible reverse source')
        after = [card for card in readable if relation[1] in card['room']]
        before = [card for card in readable if relation[2] in card['room']]
        self.assertEqual(len(after), 1)
        self.assertEqual(len(before), 1)
        order = [card['id'] for card in readable]
        self.assertEqual(order.index(before[0]['id']), order.index(after[0]['id'])+1)
        order.insert(order.index(after[0]['id'])+1, source['id'])
        return order, source['id']

    def compared_fields(self):
        return self.game.locator('.workbench-compare-row').evaluate_all('''rows=>Object.fromEntries(rows.map(row=>{
            const values=[...row.querySelectorAll('.workbench-pair-value>span')].map(e=>e.textContent.trim());
            return[row.dataset.workField,{baseline:values[0],current:values[1],selected:row.getAttribute('aria-pressed')==='true'}];
        }))''')

    def scene_fields(self):
        sign = self.game.locator('.quest-observation-sign')
        self.assertTrue(sign.is_visible())
        return sign.locator('[data-observation-field]').evaluate_all('''nodes=>Object.fromEntries(nodes.map(e=>[
            e.dataset.observationField,e.textContent.slice(e.textContent.indexOf(':')+1).trim()]))''')

    def test_d2_reverse_source_partial_reload_and_single_original_payout(self):
        self.open_game(844, 390)
        self.accept('d2')
        accepted = self.money()
        action(self.game, 'job:log')
        self.assertEqual(self.game.locator('.quest-workbench').get_attribute('data-work-revision'), '4')
        sources = self.timeline_sources()
        obscured = [card for card in sources if card['timeState'] == 'unreadable']
        self.assertEqual(len(obscured), 1)
        self.assertIsNone(obscured[0]['reverse'])
        self.assertNotRegex(obscured[0]['time'], r'\d{2}:\d{2}')
        submit = self.game.locator('.workbench-submit')
        self.assertTrue(submit.is_disabled())
        reverse = self.game.locator('[data-work-op="readReverse"]')
        self.assert_touch_target(reverse, 'read-original-reverse')
        reverse.tap()
        sources = self.timeline_sources()
        desired, unknown_id = self.chronological_sources(sources)
        self.assertNotRegex(next(card for card in sources if card['id'] == unknown_id)['time'], r'\d{2}:\d{2}')
        for identifier in desired[:2]:
            operate(self.game, 'place', identifier)
        self.assertTrue(self.game.locator('.workbench-submit').is_disabled())
        partial = self.progress()['jobs']['d2']['work']
        self.assertEqual(partial['order'], desired[:2])
        self.capture('partial-two-sources')
        self.reload_home()
        self.assertEqual(self.progress()['jobs']['d2']['work'], partial)
        self.room('doctor')
        action(self.game, 'job:log')
        self.assertEqual(self.chronological_sources(self.timeline_sources())[0], desired)
        for identifier in desired[2:]:
            operate(self.game, 'place', identifier)
        unknown = self.game.locator(f'[data-ordered-slip="{unknown_id}"] > span')
        self.assertEqual(unknown.inner_text(), 'Время не установлено')
        operate(self.game, 'move', {'id': unknown_id, 'direction': 'down'})
        wrong = self.progress()['jobs']['d2']['work']
        operate(self.game, 'submit')
        self.assertEqual(self.progress()['jobs']['d2']['work'], wrong)
        self.assertNotIn('log', self.progress()['cargo'])
        self.assertEqual(self.money(), accepted)
        operate(self.game, 'move', {'id': unknown_id, 'direction': 'up'})
        self.assertEqual(len(self.timeline_sources()), 4, 'Assembled cards retain their evidence')
        self.capture('all-sources-supported')
        operate(self.game, 'submit')
        self.assertTrue(self.progress()['jobs']['d2']['done']['log'])
        self.assertIn('log', self.progress()['cargo'])
        self.assertRegex(self.game.evaluate('PalataQuestEngine.cargoDescription(PalataQuestPrototype.snapshot(),"log")'), '(?i)время.*не установлено')
        self.assertEqual(self.money(), accepted)
        self.claim_once('d2', 10, 5, 1)
        self.room('doctor')
        self.assertEqual(self.game.locator('[data-action="accept:d2"],[data-scene-action="accept:d2"]').count(), 0)
        self.capture('completed-no-reissue')

    def test_d3_three_real_orders_use_visible_zero_one_three_changes_and_frozen_evidence(self):
        self.open_game(844, 390)
        for cycle, expected_changes in enumerate([0, 1, 3]):
            self.accept('d3')
            unpaid = self.money()
            action(self.game, 'job:baseline')
            operate(self.game, 'chooseSubject', 'signA')
            self.assertNotIn('baseline', self.progress()['cargo'])
            self.room('A')
            baseline = self.scene_fields()
            action(self.game, 'job:baseline')
            self.assertTrue(self.game.locator('[data-work-op="record"]').is_disabled())
            operate(self.game, 'inspect')
            visible_baseline = self.game.locator('.workbench-observation-card dd').all_text_contents()
            self.assertEqual(visible_baseline, list(baseline.values()))
            operate(self.game, 'record')
            saved_baseline = self.progress()['jobs']['d3']['work']['baseline']
            self.assertEqual(saved_baseline, baseline)
            self.switch_mode('trip')
            self.room('A')
            current = self.scene_fields()
            action(self.game, 'job:difference')
            self.assertEqual(self.compared_fields(), {})
            operate(self.game, 'inspect')
            compared = self.compared_fields()
            self.assertEqual({key: row['baseline'] for key, row in compared.items()}, baseline)
            self.assertEqual({key: row['current'] for key, row in compared.items()}, current)
            changed = [key for key, row in compared.items() if row['baseline'] != row['current']]
            self.assertEqual(len(changed), expected_changes)
            self.assertTrue(self.game.locator('.workbench-submit').is_disabled())
            frozen = self.progress()['jobs']['d3']['work']
            observed_trip = frozen['observedTrip']
            self.capture('order-'+str(cycle)+'-visible-evidence')
            self.reload_home()
            self.assertEqual(self.progress()['jobs']['d3']['work'], frozen)
            self.room('A')
            action(self.game, 'job:difference')
            self.assertEqual(self.compared_fields(), compared)
            if cycle == 2:
                self.switch_mode('patient')
                self.switch_mode('trip')
                self.room('A')
                self.assertEqual(self.scene_fields(), current)
                self.assertEqual(self.progress()['jobs']['d3']['work']['observedTrip'], observed_trip)
                self.assertEqual(self.progress()['jobs']['d3']['work']['observed'], frozen['observed'])
                action(self.game, 'job:difference')
            if changed:
                operate(self.game, 'noChanges')
                wrong = self.progress()['jobs']['d3']['work']
                operate(self.game, 'submit')
                self.assertEqual(self.progress()['jobs']['d3']['work'], wrong)
                for index, identifier in enumerate(changed):
                    operate(self.game, 'mark', identifier)
                    self.assertFalse(self.progress()['jobs']['d3']['work']['noChanges'])
                    if index == 0 and len(changed) > 1:
                        partial = self.progress()['jobs']['d3']['work']
                        operate(self.game, 'submit')
                        self.assertEqual(self.progress()['jobs']['d3']['work'], partial)
            else:
                operate(self.game, 'mark', next(iter(compared)))
                wrong = self.progress()['jobs']['d3']['work']
                operate(self.game, 'submit')
                self.assertEqual(self.progress()['jobs']['d3']['work'], wrong)
                operate(self.game, 'noChanges')
                self.assertTrue(self.progress()['jobs']['d3']['work']['noChanges'])
                self.assertEqual(self.progress()['jobs']['d3']['work']['marked'], [])
            self.assertEqual(self.money(), unpaid)
            self.capture('order-'+str(cycle)+'-answer')
            operate(self.game, 'submit')
            self.assertTrue(self.progress()['jobs']['d3']['done']['difference'])
            self.assertIn('difference', self.progress()['cargo'])
            self.assertNotIn('baseline', self.progress()['cargo'])
            receipt = self.game.locator('.quest-cargo-panel [data-cargo="difference"]')
            self.assertIn('Карточка наблюдения · результат', receipt.inner_text())
            if not changed:
                self.assertRegex(self.game.evaluate('PalataQuestEngine.cargoDescription(PalataQuestPrototype.snapshot(),"difference")'), '(?i)различий не обнаружено')
            self.assertEqual(self.money(), unpaid)
            self.claim_once('d3', 20, 10, cycle+1)

    def test_explicit_legacy_issued_fixtures_keep_their_original_flow_and_completed_d2(self):
        for d2_revision, d3_revision in [(1, 2), (2, 1), (3, 3)]:
            with self.subTest(d2=d2_revision, d3=d3_revision):
                self.open_game(844, 390)
                fixture = self.game.evaluate('''({d2Revision,d3Revision})=>{
                    const revised=d2Revision===3;
                    const issuedD2={revision:d2Revision,variant:0,work:{order:['entry-a']}};
                    const issuedD3={revision:d3Revision,variant:0,work:{baselineCaptured:false,marked:[]}};
                    const envelope={active:true,count:0,startTrip:0,done:{}};
                    const raw={version:revised?9:8,mode:'patient',room:'doctor',trip:0,jobs:{
                        d2:{...envelope,...(revised?PalataQuestJobModel.restore('d2',issuedD2):issuedD2)},
                        d3:{...envelope,...(revised?PalataQuestJobModel.restore('d3',issuedD3):issuedD3)}},
                        cargo:d3Revision===1?['baseline']:[],flags:{unlockB:true,unlockC:true},
                        world:revised?PalataQuestEngine.initial().world:
                            {version:1,linen406:null,calls:{ward407:null,ward408:null},doctorReview:null}};
                    return{key:'palata404_floor10_progress:'+encodeURIComponent(raidArchiveOwnerId),raw:JSON.stringify(raw),supported:PalataQuestEngine.supportsSave(raw)};
                }''', {'d2Revision': d2_revision, 'd3Revision': d3_revision})
                self.assertTrue(fixture['supported'])
                # The sole intentional historical storage seed in this module.
                self.context.add_init_script('if(!sessionStorage.getItem("questRevisionLegacySeeded")){'
                    f'localStorage.setItem({json.dumps(fixture["key"])},{json.dumps(fixture["raw"])});'
                    'sessionStorage.setItem("questRevisionLegacySeeded","1");}')
                self.reload_home(compare=False)
                self.assertEqual(self.progress()['jobs']['d2']['revision'], d2_revision)
                self.assertEqual(self.progress()['jobs']['d3']['revision'], d3_revision)
                self.room('doctor')
                if d2_revision == 1:
                    self.story_action('job:log', ['order407'])
                else:
                    complete(self.game, 'job:log')
                self.claim_once('d2', 10, 5, 1)
                self.room('doctor')
                self.assertEqual(self.game.locator('[data-action="accept:d2"],[data-scene-action="accept:d2"]').count(), 0)
                if d3_revision >= 2:
                    self.room('A')
                    complete(self.game, 'job:baseline')
                self.switch_mode('trip')
                self.room('A')
                if d3_revision == 1:
                    self.story_action('job:difference', ['changedTime'])
                else:
                    complete(self.game, 'job:difference')
                self.claim_once('d3', 20, 10, 1)
                self.room('doctor')
                action(self.game, 'accept:d3')
                self.assertEqual(self.progress()['jobs']['d3']['revision'], 4)
                self.assertEqual(self.progress()['jobs']['d3']['count'], 1)
                self.assertEqual(self.progress()['jobs']['d2']['count'], 1)
                self.capture('legacy-'+str(d2_revision)+'-'+str(d3_revision))


if __name__ == '__main__':
    unittest.main()
