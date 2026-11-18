"""Real scaled-shell navigation and durable floor-consequence presentation.

Fresh gameplay uses real controls and public workbench evidence. Pure/legacy
state fixtures are deliberately confined to quest-state-view.test.cjs.
"""
from pathlib import Path
import json
import unittest

from tests import test_compact_map as compact
from tests import test_game
from tests.quest_ui_support import action, complete, operate


OUT = Path('/dev/shm/floor10-orientation-world-20261117/independent-tests')


class Floor10OrientationTests(unittest.TestCase):
    setUpClass = classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(test_game.GameTests.tearDownClass.__func__)

    open_game = compact.CompactMapTests.open_game
    progress = compact.CompactMapTests.progress
    ledger = compact.CompactMapTests.ledger
    assert_touch_target = compact.CompactMapTests.assert_touch_target
    assert_readable_font = compact.CompactMapTests.assert_readable_font
    plan = compact.CompactMapTests.plan
    open_map = compact.CompactMapTests.open_map
    native_pan = compact.CompactMapTests.native_pan
    back_to_map = compact.CompactMapTests.back_to_map

    def setUp(self):
        self.context = None
        self.errors = []
        self.measurements = []
        self.maxDiff = None

    def tearDown(self):
        try:
            self.capture()
        finally:
            if self.context:
                self.context.close()
        self.assertEqual(self.errors, [], 'Unexpected actual-shell runtime errors')

    def capture(self, suffix='last'):
        if not getattr(self, 'page', None) or self.page.is_closed():
            return
        OUT.mkdir(parents=True, exist_ok=True)
        viewport = self.page.viewport_size
        name = f'{self._testMethodName}-{viewport["width"]}x{viewport["height"]}-{suffix}'
        self.page.screenshot(path=str(OUT/(name+'.png')))
        data = {'viewport': viewport, 'measurements': self.measurements, 'pageErrors': self.errors}
        if getattr(self, 'game', None):
            data['progress'] = self.progress()
            data['ledger'] = self.ledger()
        OUT.joinpath(name+'.json').write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def close_workbench(self):
        close = self.game.locator('[data-work-focus="close"]')
        if close.count():
            close.click()

    def show_map(self):
        self.close_workbench()
        if self.game.locator('#quest-location-screen').is_visible():
            self.back_to_map()
        elif self.game.locator('#map-modal').is_hidden():
            self.open_map()
        else:
            self.plan()

    def room(self, destination):
        self.show_map()
        card = self.preview(destination)
        enter = card.locator(f'[data-enter-room="{destination}"]')
        self.assert_touch_target(enter, 'enter:'+destination)
        enter.tap()
        self.game.wait_for_function('''room=>PalataQuestPrototype.snapshot().room===room&&
            !document.querySelector('#quest-location-screen').classList.contains('hidden')''', arg=destination)

    def preview(self, destination):
        # The overview is a real popover over the plan. Deliberately dismiss it
        # before reaching a door beneath it; never bypass its hit testing.
        panel = self.game.locator('#floor-map-overview')
        if panel.count() and panel.is_visible():
            toggle = self.game.locator('.floor-map-overview-toggle')
            self.assert_touch_target(toggle, 'overview-close-before-door')
            toggle.tap()
            panel.wait_for(state='hidden')
        return compact.CompactMapTests.preview(self, destination)

    def story_action(self, identifier, choices=()):
        action(self.game, identifier)
        for choice in choices:
            mirror = self.game.locator(f'.scene-document-actions [data-scene-action="{choice}"]')
            visible = next((item for item in mirror.all() if item.is_visible()), None)
            (visible if visible is not None else self.game.locator(f'[data-choice="{choice}"]').first).click()

    def home(self):
        self.show_map()
        self.game.locator('#map-modal .btn-close-map').tap()
        self.game.locator('#map-modal').wait_for(state='hidden')

    def switch_mode(self, mode):
        self.home()
        self.game.locator('.room-trip-switch').tap()
        self.game.wait_for_function('mode=>PalataQuestPrototype.snapshot().mode===mode', arg=mode)

    def map_outcome(self, room, identifier, status, mark=None):
        self.show_map()
        pin = self.game.locator(f'.quest-map-pin[data-room="{room}"]')
        pin.scroll_into_view_if_needed()
        badge = pin.locator(f'.quest-map-outcome[data-room-outcome="{identifier}"]')
        self.assertEqual(badge.count(), 1, (room, identifier, status))
        self.assertEqual(badge.get_attribute('data-outcome-status'), status)
        if mark is not None:
            self.assertEqual(badge.inner_text(), mark)
        self.assertEqual(self.game.locator('.quest-map-pin[aria-current="location"]').count(), 1)
        self.assertEqual(self.game.locator('.quest-map-pin[aria-current="location"]').get_attribute('data-room'), self.progress()['room'])
        return badge

    def preview_outcome(self, room, identifier, status):
        self.show_map()
        before = self.progress()
        card = self.preview(room)
        outcome = card.locator(f'.quest-room-outcomes [data-room-outcome="{identifier}"]')
        self.assertEqual(outcome.count(), 1)
        self.assertEqual(outcome.get_attribute('data-outcome-status'), status)
        self.assertEqual(self.progress(), before, 'Inspecting a consequence must not travel or alter progress')
        return outcome

    def reload_home(self):
        before = self.progress()
        canonical_before = self.game.evaluate('PalataQuestEngine.restore(PalataQuestPrototype.snapshot())')
        economic = self.ledger()
        self.page.reload(wait_until='networkidle')
        self.game = self.page.locator('#game-canvas').element_handle().content_frame()
        self.game.wait_for_function('''window.PalataQuestPrototype&&
            document.querySelector('.hospital-hud')?.dataset.assetsReady==='true'&&
            document.documentElement.dataset.touchUi==='true' ''')
        self.assertTrue(self.game.locator('#quest-location-screen').is_hidden())
        self.assertTrue(self.game.locator('#map-modal').is_hidden())
        OUT.mkdir(parents=True, exist_ok=True)
        OUT.joinpath(self._testMethodName+'-reload-state.json').write_text(json.dumps({
            'before': before, 'after': self.progress(), 'economicBefore': economic,
            'economicAfter': self.ledger()}, ensure_ascii=False, indent=2))
        # The established save reader fills omitted false/zero fields, drops
        # obsolete interaction aliases and excludes transient log messages.
        # Compare that public canonical representation, retaining the raw pair
        # above so it cannot conceal lost work, world facts or paid progress.
        self.assertEqual(self.game.evaluate('PalataQuestEngine.restore(PalataQuestPrototype.snapshot())'), canonical_before)
        self.assertEqual(self.ledger(), economic)

    def overview(self):
        toggle = self.game.locator('.floor-map-overview-toggle')
        self.assert_touch_target(toggle, 'overview-toggle')
        if toggle.get_attribute('aria-expanded') != 'true':
            toggle.tap()
        self.game.locator('#floor-map-overview').wait_for(state='visible')
        self.game.wait_for_function('''()=>{
            const rect=document.querySelector('.floor-map-visible-area');
            return Number(rect?.getAttribute('width'))>0&&
                !!document.querySelector('.floor-map-current-marker')?.getAttribute('transform');
        }''')
        return self.game.locator('.floor-map-overview-plan')

    def assert_overview_geometry(self):
        # Scroll/resize listeners intentionally update the mini in the next
        # animation frame. Observe its painted result rather than sampling
        # between native scroll mutation and the scheduled rendering pass.
        self.game.evaluate('''async()=>{
            await new Promise(requestAnimationFrame);
            await new Promise(requestAnimationFrame);
        }''')
        geometry = self.game.evaluate('''()=>{
            const view=document.querySelector('.quest-blueprint-viewport'),
                plan=document.querySelector('.quest-blueprint'),
                mini=document.querySelector('.floor-map-overview-plan'),
                visible=mini.querySelector('.floor-map-visible-area'),
                current=mini.querySelector('.floor-map-current-marker'),
                vr=view.getBoundingClientRect(),pr=plan.getBoundingClientRect(),
                sx=vr.width/view.offsetWidth,sy=vr.height/view.offsetHeight,
                visibleRect=visible.getBBox(),matrix=current.transform.baseVal.consolidate()?.matrix,
                room=PalataQuestPrototype.snapshot().room,pin=PalataQuestEngine.pins[room];
            return {plan:{left:pr.left,top:pr.top,width:pr.width,height:pr.height,
                    scrollLeft:plan.scrollLeft,scrollTop:plan.scrollTop},
                window:{left:vr.left+view.clientLeft*sx,top:vr.top+view.clientTop*sy,
                    width:view.clientWidth*sx,height:view.clientHeight*sy},
                scroll:{left:view.scrollLeft,top:view.scrollTop,maxX:view.scrollWidth-view.clientWidth,
                    maxY:view.scrollHeight-view.clientHeight},
                visible:{x:visibleRect.x,y:visibleRect.y,width:visibleRect.width,height:visibleRect.height},
                marker:matrix?{x:matrix.e,y:matrix.f}:null,
                visibleAttributes:visible.getAttributeNames().reduce((result,key)=>(result[key]=visible.getAttribute(key),result),{}),
                visibleComputed:{x:getComputedStyle(visible).x,y:getComputedStyle(visible).y,
                    width:getComputedStyle(visible).width,height:getComputedStyle(visible).height},
                panelHidden:document.querySelector('#floor-map-overview').hidden,
                rootHidden:document.querySelector('.floor-map-navigation').hidden,
                miniDisplay:getComputedStyle(mini).display,
                expectedMarker:{x:pin[0]-70,y:pin[1]-280},
                currentPin:(()=>{const e=plan.querySelector('.quest-map-pin.is-current'),r=e.getBoundingClientRect();
                    return{room:e.dataset.room,inline:e.getAttribute('style'),left:getComputedStyle(e).left,
                        top:getComputedStyle(e).top,transform:getComputedStyle(e).transform,
                        rect:{left:r.left,top:r.top,width:r.width,height:r.height},
                        containingBlock:e.offsetParent?.className};})(),
                crop:mini.querySelector('svg').getAttribute('viewBox'),
                image:mini.querySelector('image').getAttribute('href'),
                panelCount:document.querySelectorAll('#floor-map-overview').length};
        }''')
        self.measurements.append({'label': 'overview-and-real-plan', 'geometry': geometry})
        self.assertEqual(geometry['crop'], '70 280 1610 850')
        self.assertEqual(geometry['image'], 'quest-plan.svg')
        self.assertEqual(geometry['panelCount'], 1)
        self.assertFalse(geometry['panelHidden'], geometry)
        self.assertFalse(geometry['rootHidden'], geometry)
        plan, window, actual = geometry['plan'], geometry['window'], geometry['visible']
        self.assertAlmostEqual(plan['scrollLeft'], 0, delta=.01,
            msg='The authored crop must not become a second horizontal scroll container')
        self.assertAlmostEqual(plan['scrollTop'], 0, delta=.01,
            msg='The authored crop must not become a second vertical scroll container')
        # Independently map the mini rectangle back onto the full plan. It must
        # describe the real viewport intersection, including both pan axes.
        left = max(plan['left'], window['left'])
        top = max(plan['top'], window['top'])
        right = min(plan['left']+plan['width'], window['left']+window['width'])
        bottom = min(plan['top']+plan['height'], window['top']+window['height'])
        reconstructed = {
            'left': plan['left']+actual['x']/1610*plan['width'],
            'top': plan['top']+actual['y']/850*plan['height'],
            'right': plan['left']+(actual['x']+actual['width'])/1610*plan['width'],
            'bottom': plan['top']+(actual['y']+actual['height'])/850*plan['height']}
        for edge, expected in [('left', left), ('top', top), ('right', right), ('bottom', bottom)]:
            self.assertAlmostEqual(reconstructed[edge], expected, delta=1,
                msg=f'Overview {edge} describes a different visible region: {geometry}')
        for axis in ['x', 'y']:
            self.assertAlmostEqual(geometry['marker'][axis], geometry['expectedMarker'][axis], delta=2,
                msg='Current marker must follow the authoritative room, not the selected preview')
        pin = geometry['currentPin']['rect']
        for axis, start, size, units in [('x', 'left', 'width', 1610), ('y', 'top', 'height', 850)]:
            normalized = (pin[start]+pin[size]/2-plan[start])/plan[size]*units
            self.assertAlmostEqual(normalized, geometry['expectedMarker'][axis], delta=2,
                msg='The actual door and minimap must share the same authored crop')
        return geometry

    def test_overview_native_pan_recenter_preview_and_reload_are_view_only(self):
        for width, height in [(640, 320), (844, 390)]:
            with self.subTest(viewport=(width, height)):
                self.open_game(width, height)
                self.open_map()
                before = self.progress()
                economic = self.ledger()
                self.native_pan()
                self.overview()
                first = self.assert_overview_geometry()
                mini = self.game.locator('.floor-map-overview-plan')
                bounds = mini.bounding_box()
                self.page.touchscreen.tap(bounds['x']+bounds['width']*.94,
                    bounds['y']+bounds['height']*.88)
                self.game.wait_for_function('''before=>{
                    const view=document.querySelector('.quest-blueprint-viewport');
                    return Math.abs(view.scrollLeft-before.left)>2||Math.abs(view.scrollTop-before.top)>2;
                }''', arg=first['scroll'])
                self.page.wait_for_timeout(40)
                after_pan = self.assert_overview_geometry()
                self.assertGreater(after_pan['scroll']['left'], first['scroll']['left'])
                self.assertGreater(after_pan['scroll']['top'], first['scroll']['top'])
                recenter = self.game.locator('.floor-map-recenter')
                self.assert_touch_target(recenter, 'current-room-recenter')
                recenter.tap()
                self.game.locator('#floor-map-overview').wait_for(state='hidden')
                self.assertTrue(self.game.locator('.floor-map-overview-toggle').evaluate('e=>e===document.activeElement'))
                self.overview()
                self.assert_overview_geometry()
                current = self.game.locator('.quest-map-pin[aria-current="location"]')
                fits = current.evaluate('''pin=>{
                    const p=pin.getBoundingClientRect(),v=pin.closest('.quest-blueprint-viewport').getBoundingClientRect();
                    return p.left>=v.left-1&&p.top>=v.top-1&&p.right<=v.right+1&&p.bottom<=v.bottom+1;
                }''')
                self.assertTrue(fits, 'Recenter did not expose the real current door')
                self.assertEqual(self.progress(), before)
                self.assertEqual(self.ledger(), economic)
                self.preview('nurse')
                self.assertTrue(self.game.locator('.floor-map-overview-toggle').is_hidden())
                self.assertEqual(self.progress(), before)
                self.assertEqual(self.ledger(), economic)
                last_position = self.last_plan_position
                self.plan()
                retained = self.game.locator('.quest-blueprint-viewport').evaluate('e=>({left:e.scrollLeft,top:e.scrollTop})')
                for axis in ['left', 'top']:
                    self.assertAlmostEqual(retained[axis], last_position[axis], delta=1,
                        msg='Preview changed the map pan origin')
                self.overview()
                self.assert_overview_geometry()
                self.capture('view-only')
                self.room('ward407')
                self.back_to_map()
                self.overview()
                self.assert_overview_geometry()
                self.assertEqual(self.game.locator('.floor-map-navigation').count(), 1)
                self.reload_home()
                self.open_map()
                self.overview()
                self.assert_overview_geometry()
                self.game.locator('.floor-map-recenter').tap()
                self.assertEqual(self.game.locator('.quest-map-pin[aria-current="location"]').get_attribute('data-room'), 'ward407')
                self.capture('after-reload')

    def test_trip_tool_and_passage_outcomes_follow_played_actions_and_modes(self):
        self.open_game(844, 390)
        for destination in ['A', 'B', 'collector']:
            self.show_map()
            self.assertEqual(self.game.locator(f'.quest-map-pin[data-room="{destination}"] .quest-map-outcome').count(), 0)
        self.room('A')
        self.story_action('inspectDoor', ['door', 'door'])
        self.room('collector')
        self.story_action('supplyNote', ['cabinet', 'cabinet'])
        self.room('procedure')
        self.story_action('record', ['record', 'copy'])
        self.room('doctor')
        self.story_action('observation', ['document', 'confirm'])
        self.switch_mode('trip')
        self.show_map()
        clues = self.progress()
        self.assertTrue(all(clues['flags'][key] for key in ['doorKnown', 'reserveKnown', 'cKeyKnown', 'cLockKnown']))
        self.assertFalse(clues['flags'].get('unlockB', False))
        self.assertFalse(clues['flags'].get('unlockC', False))
        self.assertEqual(self.game.locator('.quest-map-outcome').count(), 0, 'Knowledge is not physical completion')
        locked = self.preview('B')
        self.assertTrue(locked.locator('[data-enter-room="B"]').is_disabled())
        self.assertEqual(self.progress(), clues)
        self.room('collector')
        self.story_action('takeHandle', ['cabinet', 'cabinet'])
        self.map_outcome('collector', 'reserve:handle', 'collected', '↓')
        taken = self.preview_outcome('collector', 'reserve:handle', 'collected').inner_text()
        self.assertRegex(taken, 'взята.*резерва')
        self.assertNotIn('установлена', taken)
        self.room('A')
        self.story_action('unlockB', ['door', 'handle', 'door'])
        self.assertTrue(self.progress()['flags']['unlockB'])
        self.assertFalse(self.progress()['flags'].get('unlockC', False))
        self.assertTrue(self.game.locator('.quest-world-effect[data-world-effect="passage:AB"]').is_visible())
        self.assertEqual(self.game.locator('[data-art-preview="passage-tags"]').count(), 0,
            'Unapproved physical tags must stay out of normal gameplay')
        self.map_outcome('A', 'passage:AB', 'open', '✓')
        installed = self.preview_outcome('collector', 'reserve:handle', 'collected').inner_text()
        self.assertIn('установлена', installed)
        self.room('B')
        self.story_action('unlockC', ['tray', 'keyC', 'lock', 'frame'])
        self.assertTrue(self.progress()['flags']['unlockC'])
        self.assertTrue(self.game.locator('.quest-world-effect[data-world-effect="passage:BC"]').is_visible())
        self.assertEqual(self.game.locator('[data-art-preview="passage-tags"]').count(), 0)
        self.map_outcome('B', 'passage:BC', 'open', '✓')
        self.preview_outcome('B', 'passage:BC', 'open')
        self.capture('trip-opened')
        self.reload_home()
        self.map_outcome('A', 'passage:AB', 'open')
        self.map_outcome('B', 'passage:BC', 'open')
        for destination in ['B', 'C']:
            self.assertNotIn('is-locked', self.game.locator(f'.quest-map-pin[data-room="{destination}"]').get_attribute('class'))
        self.switch_mode('patient')
        self.show_map()
        for destination in ['A', 'B', 'collector']:
            self.assertEqual(self.game.locator(f'.quest-map-pin[data-room="{destination}"] .quest-map-outcome').count(), 0)
        self.assertTrue(self.progress()['flags']['unlockB'])
        self.assertTrue(self.progress()['flags']['unlockC'])
        self.capture('patient-provenance')

    def test_journal_target_and_inventory_filters_are_readable_and_read_only(self):
        for width, height in [(640, 320), (844, 390)]:
            with self.subTest(viewport=(width, height)):
                self.open_game(width, height)
                before = self.progress()
                economic = self.ledger()
                inventory_before = self.game.evaluate('JSON.parse(JSON.stringify(inventory))')
                self.game.locator('.hud-task').tap()
                journal = self.game.locator('#tasks-modal')
                journal.wait_for(state='visible')
                self.assert_readable_font(journal.locator('#tasks-title'), 18, 'journal-title')
                self.assert_readable_font(journal.locator('.quest-note').first, 14, 'journal-explanation')
                for category in ['story', 'nurse', 'doctor']:
                    tab = journal.locator(f'[data-quest-tab="{category}"]')
                    self.assert_touch_target(tab, 'journal-category:'+category)
                    tab.tap()
                    self.assertEqual(tab.get_attribute('aria-pressed'), 'true')
                    for mode in ['trip', 'patient']:
                        mode_tab = journal.locator(f'[data-task-mode="{mode}"]')
                        self.assert_touch_target(mode_tab, 'journal-mode:'+mode)
                        mode_tab.tap()
                        self.assertEqual(mode_tab.get_attribute('aria-pressed'), 'true')
                        self.assertEqual(self.progress(), before)
                        self.assertEqual(self.ledger(), economic)
                journal.locator('[data-quest-tab="nurse"]').tap()
                target = journal.locator('.quest-card[data-quest-id="k2"]').get_by_role('button', name='Показать на карте')
                self.assert_touch_target(target, 'journal-show-k2-on-map')
                target.tap()
                self.plan()
                self.assertEqual(self.progress(), before)
                self.assertEqual(self.ledger(), economic)
                self.overview()
                self.assert_overview_geometry()
                target_geometry = self.game.evaluate('''()=>{
                    const target=document.querySelector('.floor-map-target-marker'),
                        matrix=target.transform.baseVal.consolidate()?.matrix,
                        pin=PalataQuestEngine.pins.nurse;
                    return {display:getComputedStyle(target).display,
                        actual:matrix?{x:matrix.e,y:matrix.f}:null,
                        expected:{x:pin[0]-70,y:pin[1]-280},
                        targetRoom:document.querySelector('.quest-map-pin.is-target')?.dataset.room,
                        currentRoom:document.querySelector('.quest-map-pin.is-current')?.dataset.room};
                }''')
                self.measurements.append({'label': 'journal-target-vs-current', **target_geometry})
                self.assertNotEqual(target_geometry['display'], 'none')
                self.assertEqual(target_geometry['targetRoom'], 'nurse')
                self.assertEqual(target_geometry['currentRoom'], 'ward404')
                for axis in ['x', 'y']:
                    self.assertAlmostEqual(target_geometry['actual'][axis], target_geometry['expected'][axis], delta=2)
                self.capture('journal-target')
                self.home()
                self.game.locator('.hud-menu-tab[aria-label="Инвентарь"]').tap()
                bag = self.game.locator('#inventory-modal')
                bag.wait_for(state='visible')
                self.assert_readable_font(bag.locator('.modal-header h3'), 18, 'inventory-title')
                counts = self.game.evaluate('''()=>{
                    const counts={all:inventory.length};
                    for(const item of inventory)counts[item.category]=(counts[item.category]||0)+1;
                    return counts;
                }''')
                seen_empty = False
                for index, category in enumerate(['all', 'weapon', 'helmet', 'armor', 'mod', 'meds']):
                    tab = bag.locator('.filter-btn').nth(index)
                    self.assert_touch_target(tab, 'inventory-filter:'+category)
                    tab.tap()
                    self.assertIn('active', tab.get_attribute('class'))
                    count = counts.get(category, 0)
                    self.assertEqual(bag.locator('#stash-items .mc-slot[role="button"]').count(), count)
                    empty = bag.locator('#stash-items .inventory-empty-state')
                    self.assertEqual(empty.count(), 1 if count == 0 else 0)
                    if count == 0:
                        seen_empty = True
                        self.assert_readable_font(empty, 14, 'inventory-empty:'+category)
                    self.assertEqual(self.progress(), before)
                    self.assertEqual(self.ledger(), economic)
                    self.assertEqual(self.game.evaluate('JSON.parse(JSON.stringify(inventory))'), inventory_before)
                self.assertTrue(seen_empty, 'Fresh inventory should exercise a real empty category')
                close = bag.locator('.modal-header button')
                self.assert_touch_target(close, 'inventory-close')
                self.capture('inventory-filters')
                close.tap()
                bag.wait_for(state='hidden')
                self.assertEqual(self.progress(), before)
                self.assertEqual(self.ledger(), economic)
                self.assertEqual(self.game.evaluate('JSON.parse(JSON.stringify(inventory))'), inventory_before)

    def test_linen_and_calls_show_partial_serviced_and_confirmed_world_results(self):
        self.open_game(844, 390)
        self.show_map()
        for destination in ['ward406', 'ward407', 'ward408']:
            self.assertEqual(self.game.locator(f'.quest-map-pin[data-room="{destination}"] .quest-map-outcome').count(), 0,
                'Unobserved fresh seeds are not player discoveries')
        self.room('nurse')
        action(self.game, 'accept:k2')
        self.room('linen')
        complete(self.game, 'job:linen')
        self.room('ward406')
        action(self.game, 'job:deliver')
        operate(self.game, 'startBedPreparation')
        self.map_outcome('ward406', 'linen406', 'preparing', '0/2')
        self.preview_outcome('ward406', 'linen406', 'preparing')
        self.room('ward406')
        action(self.game, 'job:deliver')
        operate(self.game, 'chooseMethod', 'window')
        operate(self.game, 'selectPiece', 'sheet')
        operate(self.game, 'spreadSheet')
        self.map_outcome('ward406', 'linen406', 'preparing', '1/2')
        self.room('ward406')
        complete(self.game, 'job:deliver')
        self.assertTrue(self.game.locator('.quest-world-effect[data-world-effect="linen406"][data-world-prepared="true"]').is_visible())
        self.map_outcome('ward406', 'linen406', 'prepared', '✓')
        self.room('nurse')
        action(self.game, 'claim:k2')
        prior = self.progress()['world']['linen406']
        action(self.game, 'accept:k2')
        self.map_outcome('ward406', 'linen406', 'prepared')
        self.room('linen')
        complete(self.game, 'job:linen')
        self.map_outcome('ward406', 'linen406', 'prepared')
        self.room('ward406')
        action(self.game, 'job:deliver')
        operate(self.game, 'startBedPreparation')
        self.assertEqual(self.progress()['world']['linen406'], prior)
        self.map_outcome('ward406', 'linen406', 'preparing', '0/2')
        self.reload_home()
        self.map_outcome('ward406', 'linen406', 'preparing', '0/2')
        self.assertEqual(self.progress()['world']['linen406'], prior)
        self.capture('linen-repeat-start')

        self.room('doctor')
        action(self.game, 'accept:d1')
        initial_calls = {}
        for destination in ['ward407', 'ward408']:
            self.room(destination)
            complete(self.game, 'job:bell'+destination[-3:])
            self.map_outcome(destination, 'call:'+destination, 'attention', '!')
            initial_calls[destination] = self.progress()['world']['calls'][destination]
        self.room('doctor')
        self.assertEqual(self.game.locator('[data-action="job:callReview"]').count(), 0)
        self.assertIsNone(self.progress()['world']['doctorReview'])
        unpaid = self.game.evaluate('({silver:stats.silver,exp:stats.exp})')
        self.map_outcome('ward407', 'call:ward407', 'attention')
        for destination in ['ward407', 'ward408']:
            route = self.game.evaluate('PalataQuestEngine.jobStage(PalataQuestPrototype.snapshot(),"d1")')
            self.assertEqual(route['action'], 'job:callService'+destination[-3:])
            self.assertEqual(route['room'], destination)
            self.room(route['room'])
            complete(self.game, route['action'])
            self.map_outcome(destination, 'call:'+destination, 'retest', '?')
            self.preview_outcome(destination, 'call:'+destination, 'retest')
            self.room(destination)
            self.assertTrue(self.game.locator(f'.quest-world-effect[data-world-effect="call:{destination}"][data-world-needs-retest="true"]').is_visible())
            action(self.game, 'job:callRetest'+destination[-3:])
            operate(self.game, 'test')
            self.map_outcome(destination, 'call:'+destination, 'retest')
            self.room(destination)
            action(self.game, 'job:callRetest'+destination[-3:])
            operate(self.game, 'confirm')
            self.map_outcome(destination, 'call:'+destination, 'verified', '✓')
            self.room(destination)
            self.assertTrue(self.game.locator(f'.quest-world-effect[data-world-effect="call:{destination}"][data-world-verified="true"]').is_visible())
        self.assertIsNone(self.progress()['world']['doctorReview'])
        self.assertEqual(self.game.evaluate('({silver:stats.silver,exp:stats.exp})'), unpaid)
        self.room('doctor')
        self.assertTrue(self.game.evaluate('PalataQuestEngine.ready(PalataQuestPrototype.snapshot(),"d1")'))
        action(self.game, 'claim:d1')
        history = self.progress()['world']['doctorReview']
        self.assertEqual(history['order'], 'd1:1')
        self.assertEqual(history['calls'], {
            room: {**observation, 'reviewed': True} for room, observation in initial_calls.items()
        }, 'The original doctor findings are history rather than live outstanding maintenance')
        paid = {'silver': unpaid['silver']+10, 'exp': unpaid['exp']+20}
        self.assertEqual(self.game.evaluate('({silver:stats.silver,exp:stats.exp})'), paid)
        self.reload_home()
        self.assertEqual(self.progress()['world']['doctorReview'], history)
        for destination in ['ward407', 'ward408']:
            self.map_outcome(destination, 'call:'+destination, 'verified')
        self.assertEqual(self.game.evaluate('({silver:stats.silver,exp:stats.exp})'), paid)
        self.capture('calls-confirmed')
        self.switch_mode('trip')
        self.show_map()
        for destination in ['ward406', 'ward407', 'ward408']:
            self.assertEqual(self.game.locator(f'.quest-map-pin[data-room="{destination}"] .quest-map-outcome').count(), 0)


if __name__ == '__main__':
    unittest.main()
