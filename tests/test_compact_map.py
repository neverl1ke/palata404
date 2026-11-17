"""Physical touch geometry and real navigation in the scaled play.html iframe.

Bounds from Playwright are in the outer page's CSS pixels, rather than the
1280x720 source document. Progress is reached through native controls only.
"""
from pathlib import Path
import json
import time
import unittest

from tests import test_game

OUT=Path('/dev/shm/floor10-mobile-preview/tests')
VIEWPORTS=[(640,320),(844,390)]


class CompactMapTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)

    def setUp(self):
        self.context=None
        self.errors=[]
        self.measurements=[]

    def tearDown(self):
        OUT.mkdir(parents=True,exist_ok=True)
        OUT.joinpath(self._testMethodName+'.json').write_text(json.dumps({
            'measurements':self.measurements,'pageErrors':self.errors},ensure_ascii=False,indent=2))
        if self.context:
            try:
                self.capture()
                self.page.screenshot(path=str(OUT/(self._testMethodName+'-last.png')))
            finally:self.context.close()
        self.assertEqual(self.errors,[],'Unexpected runtime errors in the actual game shell')

    def capture(self):
        OUT.mkdir(parents=True,exist_ok=True)
        if not getattr(self,'page',None) or self.page.is_closed():return
        viewport=self.page.viewport_size or {}
        name=self._testMethodName+'-'+str(viewport.get('width'))+'x'+str(viewport.get('height'))
        self.page.screenshot(path=str(OUT/(name+'.png')))
        details={'viewport':viewport,'measurements':self.measurements,'pageErrors':self.errors}
        if getattr(self,'game',None):
            details['ui']=self.game.evaluate('''()=>({touch:document.documentElement.getAttribute('data-touch-ui'),scale:getComputedStyle(document.documentElement).getPropertyValue('--touch-ui-scale'),mapView:document.querySelector('#map-modal')?.dataset.compactView,room:window.PalataQuestPrototype?.snapshot().room})''')
        OUT.joinpath(name+'.json').write_text(json.dumps(details,ensure_ascii=False,indent=2))

    def open_game(self,width,height,touch=True):
        if self.context:
            self.capture();self.context.close()
        self.context=self.browser.new_context(viewport={'width':width,'height':height},
            is_mobile=touch,has_touch=touch,reduced_motion='reduce')
        self.context.route('https://**/*',lambda route:route.abort())
        self.page=self.context.new_page()
        self.page.on('pageerror',lambda error:self.errors.append(str(error)))
        self.page.goto(self.url+'play.html',wait_until='networkidle')
        self.game=self.page.locator('#game-canvas').element_handle().content_frame()
        self.assertIsNotNone(self.game)
        self.game.wait_for_function('window.PalataQuestPrototype&&document.querySelector(".hospital-hud")?.dataset.assetsReady==="true"')
        self.assertEqual(self.game.evaluate('[innerWidth,innerHeight]'),[1280,720])
        self.page.wait_for_function('document.body.dataset.rotate==="false"')
        if touch:
            self.game.wait_for_function('document.documentElement.dataset.touchUi==="true"')
            self.game.locator('.compact-map-launch').wait_for(state='visible')
        return self.game

    def progress(self):
        return self.game.evaluate('PalataQuestPrototype.snapshot()')

    def ledger(self):
        return self.game.evaluate('''()=>{const s=PalataQuestEngine.restore(PalataQuestPrototype.snapshot());return {
            jobs:s.jobs,flags:s.flags,cargo:s.cargo,transaction:s.transaction,
            silver:stats.silver,exp:stats.exp,pills:stats.pills,bucks:stats.bucks};}''')

    def assert_touch_target(self,locator,label,enabled=True):
        locator.scroll_into_view_if_needed()
        box=locator.bounding_box()
        frame=self.page.locator('#game-canvas').bounding_box()
        self.assertIsNotNone(box,label)
        self.assertIsNotNone(frame)
        x=box['x']+box['width']/2;y=box['y']+box['height']/2
        parent_hit=self.page.evaluate('([x,y])=>document.elementFromPoint(x,y)?.id==="game-canvas"',[x,y])
        child_hit=locator.evaluate('''e=>{const r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return !!hit&&(hit===e||e.contains(hit));}''')
        measured={'label':label,'viewport':self.page.viewport_size,'bounds':box,
            'iframeBounds':frame,'parentCenterHit':parent_hit,'childCenterHit':child_hit}
        self.measurements.append(measured)
        self.assertGreaterEqual(box['width'],43.9,measured)
        self.assertGreaterEqual(box['height'],43.9,measured)
        self.assertGreaterEqual(box['x'],max(0,frame['x'])-.5,measured)
        self.assertGreaterEqual(box['y'],max(0,frame['y'])-.5,measured)
        self.assertLessEqual(box['x']+box['width'],min(self.page.viewport_size['width'],frame['x']+frame['width'])+.5,measured)
        self.assertLessEqual(box['y']+box['height'],min(self.page.viewport_size['height'],frame['y']+frame['height'])+.5,measured)
        self.assertTrue(parent_hit and child_hit,measured)
        # Chromium increments its native tap count even for Playwright's trial tap.
        # Hit testing and enabled state check reachability without consuming a tap.
        if enabled:self.assertTrue(locator.is_enabled(),label+' is disabled')
        return box

    def assert_readable_font(self,locator,minimum,label):
        locator.scroll_into_view_if_needed()
        self.assertTrue(locator.evaluate('e=>e.scrollWidth<=e.clientWidth+1'),label+' text is horizontally clipped')
        metric=locator.evaluate('''e=>({font:parseFloat(getComputedStyle(e).fontSize),layoutWidth:e.offsetWidth,transformedWidth:e.getBoundingClientRect().width})''')
        frame=self.page.locator('#game-canvas').bounding_box()
        self.assertGreater(metric['layoutWidth'],0,label)
        physical=metric['font']*metric['transformedWidth']/metric['layoutWidth']*frame['width']/1280
        self.measurements.append({'label':label,'physicalFontPx':physical,'metric':metric,'viewport':self.page.viewport_size})
        self.assertGreaterEqual(physical,minimum-.15,(label,physical,metric))

    def plan(self):
        modal=self.game.locator('#map-modal')
        modal.wait_for(state='visible')
        if modal.get_attribute('data-compact-view')!='plan':
            tab=self.game.locator('[data-compact-map-view="plan"]')
            self.assert_touch_target(tab,'plan-tab');tab.tap()
        self.game.wait_for_function('document.querySelector("#map-modal").dataset.compactView==="plan"')
        return modal

    def open_map(self):
        launch=self.game.locator('.compact-map-launch')
        self.assert_touch_target(launch,'map-launch');launch.tap()
        return self.plan()

    def preview(self,room):
        pin=self.game.locator(f'.quest-map-pin[data-room="{room}"]')
        self.assert_touch_target(pin,'door:'+room)
        self.last_plan_position=self.game.locator('.quest-blueprint-viewport').evaluate('e=>({left:e.scrollLeft,top:e.scrollTop})')
        pin.tap()
        self.game.wait_for_function('document.querySelector("#map-modal").dataset.compactView==="details"')
        card=self.game.locator('.quest-room-preview')
        card.wait_for(state='visible')
        return card

    def assert_scene_unchanged_size(self):
        scene=self.game.locator('.quest-room-scene').bounding_box()
        frame=self.page.locator('#game-canvas').bounding_box()
        self.assertAlmostEqual(scene['width'],frame['width'],delta=1)
        self.assertAlmostEqual(scene['height'],frame['height'],delta=1)

    def back_to_map(self):
        back=self.game.locator('.quest-room-tools button').first
        self.assert_touch_target(back,'room-back');back.tap()
        self.game.locator('#quest-location-screen').wait_for(state='hidden')
        return self.plan()

    def native_pan(self):
        viewport=self.game.locator('.quest-blueprint-viewport')
        read="""e=>({left:e.scrollLeft,top:e.scrollTop,maxX:e.scrollWidth-e.clientWidth,maxY:e.scrollHeight-e.clientHeight,overflowX:getComputedStyle(e).overflowX,overflowY:getComputedStyle(e).overflowY})"""
        initial=viewport.evaluate(read)
        axes=[axis for axis,key in [('x','maxX'),('y','maxY')] if initial[key]>1]
        self.assertTrue(axes,initial)
        for axis in axes:
            before=viewport.evaluate(read)
            self.assertIn(before['overflowX' if axis=='x' else 'overflowY'],['auto','scroll'],before)
            box=viewport.bounding_box()
            direction=-1 if before['left' if axis=='x' else 'top']<before['maxX' if axis=='x' else 'maxY']-2 else 1
            start={'x':box['x']+box['width']*.5,'y':box['y']+box['height']*.5}
            origin='x' if axis=='x' else 'y';dimension='width' if axis=='x' else 'height'
            start[origin]=box[origin]+box[dimension]*(.75 if direction<0 else .25)
            end={**start};end[axis]+=direction*min(140,box[dimension]*.4)
            session=self.context.new_cdp_session(self.page)
            try:
                session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[start]})
                for step in range(1,9):
                    point={key:start[key]+(end[key]-start[key])*step/8 for key in ['x','y']}
                    session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[point]})
                    self.page.wait_for_timeout(24)
                # Finish a deliberate drag without a fling into a later tap.
                self.page.wait_for_timeout(80)
                session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
            finally:session.detach()
            self.game.wait_for_function('''({before,axis})=>{const e=document.querySelector('.quest-blueprint-viewport');return Math.abs((axis==='x'?e.scrollLeft:e.scrollTop)-(axis==='x'?before.left:before.top))>2;}''',arg={'before':before,'axis':axis},timeout=3000)
            after=viewport.evaluate('e=>({left:e.scrollLeft,top:e.scrollTop})')
            self.measurements.append({'label':'native-touch-pan','axis':axis,'before':before,'after':after})

    def native_pair_and_wait(self,x,y,room):
        # Observe actual browser delivery; a 70ms host wait is not proof that
        # a busy browser dispatched the two native taps 70ms apart.
        self.game.evaluate('''()=>{
            const events=[],types=['pointerdown','touchstart','touchend','click','dblclick'];
            const listener=event=>{
                const point=event.changedTouches?.[0]||event;
                const button=event.target.closest?.('button');
                events.push({type:event.type,timeStamp:event.timeStamp,now:performance.now(),detail:event.detail,
                    clientX:point.clientX,clientY:point.clientY,targetRoom:button?.dataset.room||null,
                    targetId:button?.id||null,targetClass:button?.className||null,
                    mapView:document.querySelector('#map-modal')?.dataset.compactView});
            };
            for(const type of types)document.addEventListener(type,listener,true);
            window.compactPairProbe={stop:()=>{for(const type of types)document.removeEventListener(type,listener,true);return events;}};
        }''')
        host={}
        try:
            host['beforeFirst']=time.monotonic()*1000
            self.page.touchscreen.tap(x,y)
            host['afterFirst']=time.monotonic()*1000
            self.page.wait_for_timeout(70)
            host['beforeSecond']=time.monotonic()*1000
            self.page.touchscreen.tap(x,y)
            host['afterSecond']=time.monotonic()*1000
            self.game.wait_for_function('''room=>PalataQuestPrototype.snapshot().room===room&&!document.querySelector('#quest-location-screen').classList.contains('hidden')''',arg=room,timeout=10000)
        finally:
            observed=self.game.evaluate('''()=>({events:compactPairProbe.stop(),room:PalataQuestPrototype.snapshot().room,mapView:document.querySelector('#map-modal')?.dataset.compactView})''')
            record={'label':'native-double-tap-delivery','viewport':self.page.viewport_size,
                'expectedRoom':room,'plannedMainPoint':{'x':x,'y':y},'requestedHostDelayMs':70,
                'hostMonotonicMs':host,**observed}
            for kind in ['pointerdown','touchstart','touchend','click']:
                events=[event for event in observed['events'] if event['type']==kind]
                if len(events)>=2:
                    record[kind+'DispatchGapMs']=events[1]['now']-events[0]['now']
                    record[kind+'TimestampGapMs']=events[1]['timeStamp']-events[0]['timeStamp']
            self.measurements.append(record)
            OUT.mkdir(parents=True,exist_ok=True)
            viewport=self.page.viewport_size
            OUT.joinpath(f'native-pair-{viewport["width"]}x{viewport["height"]}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))

    def test_touch_map_reaches_every_door_and_single_preview_does_not_travel(self):
        for width,height in VIEWPORTS:
            with self.subTest(viewport=(width,height)):
                self.open_game(width,height)
                # The extra launcher must not cover the approved full HUD card.
                # Use the original control and wait for its actual animation.
                self.page.emulate_media(reduced_motion='no-preference')
                toggle=self.game.locator('.hud-card-toggle')
                toggle.tap()
                self.game.wait_for_function('''()=>{const card=document.querySelector('#patient-card'),launch=document.querySelector('.compact-map-launch');return card?.dataset.cardMode==='full'&&!PalataHudCard.moving&&!card.hasAttribute('data-card-motion')&&launch?.hidden;}''')
                self.assertTrue(self.game.locator('.compact-map-launch').is_hidden())
                OUT.mkdir(parents=True,exist_ok=True)
                self.page.screenshot(path=str(OUT/f'hud-full-launcher-hidden-{width}x{height}.png'))
                self.game.locator('#location-card-box').tap()
                self.plan()
                self.game.locator('#map-modal .btn-close-map').tap()
                self.game.locator('#map-modal').wait_for(state='hidden')
                toggle.tap()
                self.game.wait_for_function('''()=>{const card=document.querySelector('#patient-card'),launch=document.querySelector('.compact-map-launch');return card?.dataset.cardMode==='compact'&&!PalataHudCard.moving&&!card.hasAttribute('data-card-motion')&&launch&&!launch.hidden;}''')
                self.assert_touch_target(self.game.locator('.compact-map-launch'),'map-launch-after-card-collapse')
                self.page.emulate_media(reduced_motion='reduce')
                self.open_map()
                original=self.progress()['room'];ledger=self.ledger()
                self.native_pan()
                names=self.game.locator('.quest-map-pin[data-room]').evaluate_all('nodes=>nodes.map(e=>e.dataset.room)')
                self.assertEqual(set(names),set(self.game.evaluate('Object.keys(PalataQuestEngine.rooms)')))
                self.assertEqual(len(names),17)
                for room in names:self.assert_touch_target(self.game.locator(f'.quest-map-pin[data-room="{room}"]'),'door:'+room)
                card=self.preview('nurse')
                self.assertEqual(self.progress()['room'],original)
                self.assertEqual(self.ledger(),ledger)
                self.assertTrue(self.game.locator('#quest-location-screen').is_hidden())
                self.assert_readable_font(card.locator('h4'),18,'preview-title')
                self.assert_readable_font(card.locator('p').first,14,'preview-description')
                enter=card.locator('[data-enter-room="nurse"]')
                self.assertFalse(enter.is_disabled());self.assert_touch_target(enter,'preview-enter')
                self.plan()
                close=self.game.locator('#map-modal .btn-close-map')
                self.assert_touch_target(close,'map-close');close.tap()
                self.game.locator('#map-modal').wait_for(state='hidden')
                self.assertEqual(self.progress()['room'],original)
                self.assertEqual(self.ledger(),ledger)

    def test_native_enter_double_tap_back_collapse_and_reload_preserve_progress(self):
        for width,height in VIEWPORTS:
            with self.subTest(viewport=(width,height)):
                self.open_game(width,height);self.open_map();ledger=self.ledger()
                card=self.preview('nurse');card.locator('[data-enter-room="nurse"]').tap()
                self.game.wait_for_function('PalataQuestPrototype.snapshot().room==="nurse"&&!document.querySelector("#quest-location-screen").classList.contains("hidden")')
                plan_position=self.last_plan_position
                self.assertTrue(plan_position['left']>0 or plan_position['top']>0,plan_position)
                self.assert_scene_unchanged_size();self.back_to_map()
                restored_position=self.game.locator('.quest-blueprint-viewport').evaluate('e=>({left:e.scrollLeft,top:e.scrollTop})')
                self.assertAlmostEqual(restored_position['left'],plan_position['left'],delta=1)
                self.assertAlmostEqual(restored_position['top'],plan_position['top'],delta=1)
                pin=self.game.locator('.quest-map-pin[data-room="ward407"]')
                box=self.assert_touch_target(pin,'double-tap-door')
                x=box['x']+box['width']/2;y=box['y']+box['height']/2
                self.native_pair_and_wait(x,y,'ward407')
                self.assert_scene_unchanged_size()
                paper=self.game.locator('.scene-paper')
                toggle=self.game.locator('[data-room-info-toggle]')
                self.assert_touch_target(toggle,'description-collapse');toggle.tap()
                self.assertTrue(paper.is_hidden());self.assert_scene_unchanged_size()
                self.assert_touch_target(toggle,'description-reopen');toggle.tap();paper.wait_for(state='visible')
                self.assert_readable_font(paper.locator('p').first,14,'room-description')
                self.assertEqual(self.ledger(),ledger)
                saved=self.progress()['room']
                self.page.reload(wait_until='networkidle')
                self.game=self.page.locator('#game-canvas').element_handle().content_frame()
                self.game.wait_for_function('document.querySelector(".hospital-hud")?.dataset.assetsReady==="true"&&document.documentElement.dataset.touchUi==="true"')
                self.assertTrue(self.game.locator('#quest-location-screen').is_hidden())
                self.assertTrue(self.game.locator('#map-modal').is_hidden())
                self.assertEqual(self.progress()['room'],saved)
                self.assertEqual(self.ledger(),ledger)
                self.open_map()
                self.assertIn('is-current',self.game.locator(f'.quest-map-pin[data-room="{saved}"]').get_attribute('class'))

    def test_trip_locked_preview_keeps_real_progression_gate(self):
        for width,height in VIEWPORTS:
            with self.subTest(viewport=(width,height)):
                self.open_game(width,height)
                self.game.locator('.room-trip-switch').tap()
                self.game.wait_for_function('PalataQuestPrototype.snapshot().mode==="trip"')
                state=self.progress();ledger=self.ledger()
                self.assertFalse(state['allSectionsUnlocked'])
                self.open_map();card=self.preview('nurse')
                enter=card.locator('[data-enter-room="nurse"]')
                self.assertTrue(enter.is_disabled())
                self.assert_touch_target(enter,'locked-enter',enabled=False)
                self.assertTrue(card.inner_text().strip())
                self.assertEqual(self.progress()['room'],state['room'])
                self.assertEqual(self.ledger(),ledger)
                self.assertTrue(self.game.locator('#quest-location-screen').is_hidden())
                self.game.locator('#map-modal .btn-close-map').tap()
                self.game.locator('.room-trip-switch').tap()
                self.game.wait_for_function('PalataQuestPrototype.snapshot().mode==="patient"')
                self.open_map();self.assertFalse(self.preview('nurse').locator('[data-enter-room="nurse"]').is_disabled())
                self.assertFalse(self.progress()['allSectionsUnlocked'])
                self.assertFalse(self.progress()['flags'].get('unlockB',False))
                self.assertEqual(self.ledger(),ledger)

    def test_synthetic_delayed_click_replay_respects_original_touch_and_invalid_intents(self):
        """Replay the recorded event timestamp/dispatch mismatch, not native CPU lag."""
        for width,height in VIEWPORTS:
            for scenario in ['valid','expired-timestamp','different-position','closed-intent']:
                with self.subTest(viewport=(width,height),synthetic_replay=scenario):
                    self.open_game(width,height);self.open_map()
                    original=self.progress()['room'];ledger=self.ledger()
                    self.game.evaluate('''()=>{
                        window.compactReplayFirst=null;
                        const listener=event=>{const pin=event.target.closest?.('.quest-map-pin[data-room="ward407"]');if(!pin)return;
                            compactReplayFirst={timeStamp:event.timeStamp,clientX:event.clientX,clientY:event.clientY,
                                detail:event.detail,isTrusted:event.isTrusted,room:pin.dataset.room};
                            document.removeEventListener('click',listener,true);
                        };
                        document.addEventListener('click',listener,true);
                    }''')
                    self.preview('ward407')
                    first=self.game.evaluate('compactReplayFirst')
                    self.assertTrue(first['isTrusted'],first)
                    self.assertEqual(first['detail'],1,first)
                    self.assertEqual(self.progress()['room'],original)
                    if scenario=='closed-intent':
                        self.page.keyboard.press('Escape')
                        self.game.locator('#map-modal').wait_for(state='hidden')
                        self.page.wait_for_timeout(350)
                        self.open_map()
                    # Synthetic delivery occurs after the real preview is visible,
                    # while its timestamp describes the second original native tap.
                    replay=self.game.evaluate('''({first,scenario})=>{
                        const scale=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--touch-ui-scale'))||1;
                        let x=first.clientX,y=first.clientY;
                        if(scenario==='different-position'){
                            const candidates=[[40,0],[-40,0],[0,40],[0,-40]];
                            const safe=candidates.map(([dx,dy])=>({x:x+dx*scale,y:y+dy*scale})).find(point=>{
                                const e=document.elementFromPoint(point.x,point.y);
                                return e&&e.closest('#map-modal')&&!e.closest('button,a,input,select,textarea,[role="button"]');
                            });
                            if(!safe)throw new Error('No non-action document point is available for the spatial replay');
                            x=safe.x;y=safe.y;
                        }
                        const target=document.elementFromPoint(x,y);
                        if(!target||!target.closest('#map-modal'))throw new Error('Replay point is outside the actual map UI');
                        if(scenario!=='closed-intent'&&target.closest('button,a,input,select,textarea,[role="button"]'))throw new Error('Replay point overlaps a legitimate document action');
                        const stamp=first.timeStamp+(scenario==='expired-timestamp'?1000:162);
                        const event=new MouseEvent('click',{bubbles:true,cancelable:true,view:window,
                            detail:2,button:0,buttons:0,clientX:x,clientY:y});
                        Object.defineProperty(event,'timeStamp',{value:stamp});
                        const metadata={synthetic:true,isTrusted:event.isTrusted,timeStamp:event.timeStamp,
                            elapsedMs:event.timeStamp-first.timeStamp,detail:event.detail,clientX:x,clientY:y,
                            physicalDistancePx:Math.hypot(x-first.clientX,y-first.clientY)/scale,
                            targetTag:target.tagName,targetId:target.id,targetClass:target.className,
                            targetRoom:target.closest('.quest-map-pin')?.dataset.room||null,
                            mapViewBefore:document.querySelector('#map-modal').dataset.compactView};
                        metadata.dispatchReturned=target.dispatchEvent(event);
                        metadata.defaultPrevented=event.defaultPrevented;
                        return metadata;
                    }''',{'first':first,'scenario':scenario})
                    self.assertFalse(replay['isTrusted'])
                    if scenario=='valid':
                        self.game.wait_for_function('PalataQuestPrototype.snapshot().room==="ward407"&&!document.querySelector("#quest-location-screen").classList.contains("hidden")')
                        self.assert_scene_unchanged_size()
                    else:
                        # Also let a normal single-preview timeout settle. This
                        # is a UI event replay, never a direct engine operation.
                        self.page.wait_for_timeout(350)
                        self.assertEqual(self.progress()['room'],original)
                        self.assertTrue(self.game.locator('#quest-location-screen').is_hidden())
                        self.assertTrue(self.game.locator('#map-modal').is_visible())
                    self.assertEqual(self.ledger(),ledger)
                    record={'label':'synthetic-delayed-click-replay','viewport':self.page.viewport_size,
                        'scenario':scenario,'firstNativeEvent':first,'replayedUiEvent':replay,
                        'finalRoom':self.progress()['room'],'ledgerUnchanged':self.ledger()==ledger}
                    self.measurements.append(record)
                    OUT.mkdir(parents=True,exist_ok=True)
                    OUT.joinpath(f'synthetic-replay-{scenario}-{width}x{height}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))

    def test_desktop_keeps_the_original_canvas_and_has_no_touch_layout(self):
        self.open_game(1280,720,touch=False)
        self.assertFalse(self.game.evaluate('document.documentElement.hasAttribute("data-touch-ui")'))
        self.assertEqual(self.game.locator('.compact-map-launch:visible').count(),0)
        self.game.locator('#location-card-box').click()
        self.game.locator('#map-modal').wait_for(state='visible')
        self.assertEqual(self.game.locator('.compact-map-tabs:visible').count(),0)
        self.assertFalse(self.game.evaluate('document.documentElement.hasAttribute("data-touch-ui")'))
        self.assertEqual(self.game.evaluate('[innerWidth,innerHeight]'),[1280,720])


if __name__=='__main__':unittest.main()
