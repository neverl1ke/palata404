"""Actual task work, evidence, submission and save recovery through game controls.

The solver reads only the same public evidence rendered on each work surface.
Only the explicitly named legacy-save test seeds an old persisted fixture; all
remaining progress uses real controls, without E.apply calls or forced clicks.
"""
from pathlib import Path
import json
import unittest

from tests import test_game
from tests import quest_ui_support as ui

OUT=Path('/dev/shm/palata404-new-quest-tests')
OUT.mkdir(parents=True,exist_ok=True)


class QuestWorkbenchTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
    tearDown=test_game.GameTests.tearDown
    load=test_game.GameTests.load

    def setUp(self):
        test_game.GameTests.setUp(self)
        self.page.emulate_media(reduced_motion='reduce')

    def progress(self):
        return self.page.evaluate('PalataQuestPrototype.snapshot()')

    def ledger(self):
        return self.page.evaluate('''()=>({silver:stats.silver,exp:stats.exp,level:stats.level,
            pills:stats.pills,bucks:stats.bucks,
            medkits:inventory.filter(x=>x.name===MEDICAL_ITEMS.hp_10.name&&x.category==='meds').reduce((n,x)=>n+x.count,0),
            cargo:inventory.filter(x=>x.questCargo).map(x=>x.questCargo).sort()})''')

    def assert_paired_fields(self,source,current):
        """Each comparison presents both observations together, never an answer key."""
        rows=self.page.locator('[data-work-field][data-work-op="mark"]')
        self.assertEqual(rows.count(),len(source))
        other={field['id']:field for field in current}
        for field in source:
            row=self.page.locator(f'[data-work-field="{field["id"]}"]')
            self.assertEqual(row.get_attribute('data-work-value'),field['id'])
            self.assertEqual(row.locator('.workbench-pair-field strong').inner_text(),field['label'])
            values=row.locator('.workbench-pair-value > span')
            self.assertEqual(values.count(),2)
            self.assertEqual(values.nth(0).inner_text(),field['value'] or '—')
            self.assertEqual(values.nth(1).inner_text(),other[field['id']]['value'] or '—')
            self.assertEqual(row.get_attribute('aria-pressed'),'false')

    def accept(self,id):
        ui.room(self.page,'nurse' if id.startswith('k') else 'doctor')
        ui.action(self.page,'accept:'+id)
        job=self.progress()['jobs'][id]
        self.assertTrue(job['active'])
        self.assertEqual(job['revision'],4 if id in ['k2','d1'] else 2)

    def reload_home(self):
        self.page.reload(wait_until='networkidle')
        self.page.wait_for_function('document.querySelector(".hospital-hud")?.dataset.assetsReady==="true"')
        self.page.locator('#scene-loading').wait_for(state='hidden')
        self.assertTrue(self.page.locator('#quest-location-screen').is_hidden())
        self.assertTrue(self.page.locator('#map-modal').is_hidden())
        self.assertEqual(self.page.locator('.quest-workbench').count(),0)

    def switch_mode(self):
        ui.return_home(self.page)
        self.page.locator('.room-trip-switch').click()

    def work_job(self,id):
        if id=='k1':
            ui.room(self.page,'procedure');ui.complete(self.page,'job:tag')
        elif id=='k2':
            ui.room(self.page,'linen');ui.complete(self.page,'job:linen')
            self.assertIn('linen',self.ledger()['cargo'])
            ui.room(self.page,'ward406');ui.complete(self.page,'job:deliver')
            self.assertNotIn('linen',self.ledger()['cargo'])
        elif id=='k3':
            ui.room(self.page,'procedure');ui.complete(self.page,'job:copies')
        elif id=='d1':
            for room in ['ward407','ward408']:
                action='job:bell'+room[-3:]
                ui.room(self.page,room);ui.action(self.page,action)
                self.assertEqual(self.page.locator('.workbench-connector-view').count(),0)
                self.assertTrue(self.page.locator('[data-work-op="test"]').is_disabled())
                ui.operate(self.page,'inspect','connector');ui.operate(self.page,'test')
                observed=ui.board(self.page,action)
                response=self.page.locator('.workbench-call-response')
                self.assertIn(observed['response'],response.inner_text())
                visible=response.evaluate('''e=>{const r=e.getBoundingClientRect(),board=e.closest('.quest-workbench'),top=board.querySelector('.workbench-scroll').getBoundingClientRect().top,bottom=board.querySelector('.workbench-footer').getBoundingClientRect().top;return{top:r.top,bottom:r.bottom,clipTop:top,clipBottom:bottom}}''')
                self.assertGreaterEqual(visible['top'],visible['clipTop'],visible)
                self.assertLessEqual(visible['bottom'],visible['clipBottom'],visible)
                ui.complete(self.page,action,open_board=False)
            ui.complete_call_cycle(self.page)
        elif id=='d2':
            ui.complete(self.page,'job:log')
        elif id=='d3':
            self.assertNotIn('baseline',self.ledger()['cargo'])
            ui.room(self.page,'A');ui.complete(self.page,'job:baseline')
            self.assertIn('baseline',self.ledger()['cargo'])
            self.switch_mode();self.assertEqual(self.progress()['mode'],'trip')
            ui.room(self.page,'A');ui.complete(self.page,'job:difference')
            self.assertNotIn('baseline',self.ledger()['cargo'])
            self.switch_mode();self.assertEqual(self.progress()['mode'],'patient')
        else:
            self.fail('Unknown job '+id)

    def test_all_six_jobs_complete_real_work_and_pay_once_with_existing_rewards(self):
        self.load()
        rewards={'k1':(10,5,0),'k2':(15,8,1),'k3':(15,8,0),'d1':(20,10,0),'d2':(10,5,0),'d3':(20,10,0)}
        evidence={'k1':['tag'],'k2':['delivery'],'k3':['copies'],'d1':['bell407','bell408'],'d2':['log'],'d3':['difference']}
        results=[]
        for id,(exp,silver,medkits) in rewards.items():
            with self.subTest(job=id):
                self.accept(id)
                before=self.ledger()
                self.work_job(id)
                worked=self.ledger()
                self.assertEqual(worked['silver'],before['silver'])
                self.assertEqual(worked['exp'],before['exp'])
                self.assertEqual(worked['pills'],before['pills'])
                self.assertEqual(worked['bucks'],before['bucks'])
                self.assertEqual(worked['medkits'],before['medkits'])
                for item in evidence[id]:self.assertIn(item,worked['cargo'])
                ui.room(self.page,'nurse' if id.startswith('k') else 'doctor')
                ui.action(self.page,'claim:'+id)
                after=self.ledger()
                self.assertEqual(after['exp']-before['exp'],exp)
                self.assertEqual(after['silver']-before['silver'],silver)
                self.assertEqual(after['medkits']-before['medkits'],medkits)
                self.assertEqual(after['pills'],before['pills'])
                self.assertEqual(after['bucks'],before['bucks'])
                for item in evidence[id]:self.assertNotIn(item,after['cargo'])
                job=self.progress()['jobs'][id]
                self.assertFalse(job['active']);self.assertEqual(job['count'],1)
                self.assertEqual(self.page.locator(f'[data-action="claim:{id}"]').count(),0)
                results.append({'job':id,'exp':exp,'silver':silver,'medkits':medkits,'proofConsumed':True})
        before=self.ledger();self.reload_home()
        self.assertEqual(self.ledger(),before)
        self.assertTrue(all(self.progress()['jobs'][id]['count']==1 for id in rewards))
        (OUT/'six-jobs-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))

    def test_parcel_survives_mid_delivery_reload_then_becomes_receipt(self):
        self.load();self.accept('k2')
        before=self.ledger()
        ui.room(self.page,'linen')
        self.assertEqual(self.page.locator('[data-world-item="linen"]').count(),0)
        ui.complete(self.page,'job:linen')
        saved=self.progress()['jobs']['k2']
        self.assertIn('linen',self.ledger()['cargo'])
        self.reload_home()
        self.assertEqual(self.progress()['jobs']['k2'],saved)
        self.assertIn('linen',self.ledger()['cargo'])
        ui.room(self.page,'ward406');ui.complete(self.page,'job:deliver')
        self.assertNotIn('linen',self.ledger()['cargo']);self.assertIn('delivery',self.ledger()['cargo'])
        self.assertTrue(self.progress()['world']['linen406']['prepared'])
        self.assertEqual(self.page.locator('[data-world-effect="linen406"]').count(),1)
        ui.room(self.page,'nurse');ui.action(self.page,'claim:k2')
        after=self.ledger()
        self.assertEqual(after['silver']-before['silver'],8)
        self.assertEqual(after['exp']-before['exp'],15)
        self.assertEqual(after['medkits']-before['medkits'],1)
        self.reload_home();self.assertEqual(self.ledger(),after)
        self.assertEqual(self.progress()['jobs']['k2']['count'],1)

    def test_observation_uses_actual_scene_and_journal_guides_mode_and_claim(self):
        self.load();self.accept('d3');ui.room(self.page,'A')
        initial=ui.board(self.page,'job:baseline')
        self.assertIsNotNone(initial)
        for field in initial['details']:
            self.assertTrue(self.page.locator(f'[data-observation-field="{field["id"]}"]').inner_text().endswith(field['value']))
        ui.complete(self.page,'job:baseline')
        before_trip=self.progress()['jobs']['d3']
        self.assertTrue(before_trip['work']['baselineCaptured'])
        self.assertIn('baseline',self.ledger()['cargo'])
        ui.return_home(self.page);self.page.locator('.hud-task').click()
        self.page.locator('[data-quest-tab="doctor"]').click()
        card=self.page.locator('[data-quest-id="d3"]')
        self.assertIn('Активно: 1/2',card.inner_text())
        self.assertIn('Трип',card.locator('.quest-mode-requirement').inner_text())
        card.get_by_role('button',name='К переключателю состояния',exact=True).click()
        self.page.wait_for_function('document.activeElement.classList.contains("room-trip-switch")')
        self.assertEqual(self.page.evaluate('document.activeElement.classList.contains("room-trip-switch")'),True)
        self.assertEqual(self.progress()['mode'],'patient')
        self.page.locator('.room-trip-switch').click();ui.room(self.page,'A')
        current=ui.board(self.page,'job:difference')
        self.assertEqual(current['baseline'],initial['details'])
        for field in current['current']:
            self.assertTrue(self.page.locator(f'[data-observation-field="{field["id"]}"]').inner_text().endswith(field['value']))
        ui.action(self.page,'job:difference')
        self.assert_paired_fields(current['baseline'],current['current'])
        ui.complete(self.page,'job:difference',open_board=False)
        self.assertIn('difference',self.ledger()['cargo']);self.assertNotIn('baseline',self.ledger()['cargo'])
        ui.return_home(self.page);self.page.locator('.hud-task').click()
        self.page.locator('[data-quest-tab="doctor"]').click()
        card=self.page.locator('[data-quest-id="d3"]')
        self.assertIn('Наблюдение записано',card.inner_text())
        self.assertFalse(card.locator('h4').inner_text().startswith('✓'))
        self.assertIn('Пациент',card.locator('.quest-mode-requirement').inner_text())
        card.get_by_role('button',name='К переключателю состояния',exact=True).click()
        self.page.wait_for_function('document.activeElement.classList.contains("room-trip-switch")')
        self.page.locator('.room-trip-switch').click();ui.room(self.page,'doctor')
        before=self.ledger();ui.action(self.page,'claim:d3');after=self.ledger()
        self.assertEqual(after['silver']-before['silver'],10)
        self.assertEqual(after['exp']-before['exp'],20)
        ui.return_home(self.page);self.page.locator('.hud-task').click()
        self.page.locator('[data-quest-tab="doctor"]').click()
        self.assertTrue(self.page.locator('[data-quest-id="d3"] h4').inner_text().startswith('✓'))
        # The next real order uses the existing stripe/cross variant. Its
        # non-written mark must physically change with the recorded evidence.
        self.page.get_by_role('button',name='Закрыть задания',exact=True).click()
        self.accept('d3');ui.room(self.page,'A')
        self.assertEqual(self.page.locator('[data-observation-mark]').get_attribute('data-observation-mark'),'Полоса')
        patient_shape=self.page.locator('[data-observation-mark] path').get_attribute('d')
        ui.complete(self.page,'job:baseline');self.switch_mode();ui.room(self.page,'A')
        self.assertEqual(self.page.locator('[data-observation-mark]').get_attribute('data-observation-mark'),'Крест')
        trip_shape=self.page.locator('[data-observation-mark] path').get_attribute('d')
        self.assertNotEqual(patient_shape,trip_shape)
        ui.action(self.page,'job:difference')
        physical=ui.board(self.page,'job:difference')
        self.assertEqual(next(field['value'] for field in physical['baseline'] if field['id']=='mark'),'Полоса')
        self.assertEqual(next(field['value'] for field in physical['current'] if field['id']=='mark'),'Крест')

    def test_wrong_inspection_and_packing_keep_progress_and_saved_variant(self):
        self.load();self.accept('k1');ui.room(self.page,'procedure');ui.action(self.page,'job:tag')
        for item in ui.board(self.page,'job:tag')['items']:ui.operate(self.page,'inspect',item['id'])
        inspected=ui.board(self.page,'job:tag')
        wrong=next(x for x in inspected['items'] if x['details']['kit']!=inspected['request']['kit'] or x['details']['lot']!=inspected['request']['lot'] or x['details']['seal']!='целая')
        ui.operate(self.page,'select',wrong['id'])
        saved_board=ui.board(self.page,'job:tag');saved_job=self.progress()['jobs']['k1'];before=self.ledger()
        ui.operate(self.page,'submit')
        self.assertIn('не соответствует',self.page.locator('.workbench-status').inner_text())
        self.assertEqual(ui.board(self.page,'job:tag'),saved_board)
        self.assertEqual(self.ledger(),before)
        self.reload_home();ui.room(self.page,'procedure');ui.action(self.page,'job:tag')
        self.assertEqual(self.progress()['jobs']['k1'],saved_job)
        self.assertEqual(ui.board(self.page,'job:tag'),saved_board)
        ui.complete(self.page,'job:tag',open_board=False)
        self.assertIn('tag',self.ledger()['cargo'])
        self.accept('k2');ui.room(self.page,'linen');ui.action(self.page,'job:linen')
        packing=ui.board(self.page,'job:linen')
        bad=next(x for x in packing['items'] if x['condition']!='чистая упаковка')
        ui.operate(self.page,'select',bad['id']);before=self.ledger();selected=ui.board(self.page,'job:linen')
        ui.operate(self.page,'submit')
        self.assertIn('чистых целых упаковках',self.page.locator('.workbench-status').inner_text())
        self.assertEqual(self.ledger(),before)
        self.assertEqual(ui.board(self.page,'job:linen'),selected)
        self.assertNotIn('linen',self.ledger()['cargo'])

    def test_denied_journal_rolls_back_partial_work_and_claim_without_payment(self):
        self.load();self.accept('k1');ui.room(self.page,'procedure');ui.action(self.page,'job:tag')
        before_board=ui.board(self.page,'job:tag');before=self.ledger()
        self.page.evaluate('()=>{window.questOriginalSet=safeStorageSet;safeStorageSet=(k,v)=>k.startsWith("palata404_floor10_reward:")?false:questOriginalSet(k,v)}')
        ui.operate(self.page,'inspect',before_board['items'][0]['id'])
        self.assertIn('Не удалось сохранить',self.page.locator('.workbench-status').inner_text())
        self.assertEqual(ui.board(self.page,'job:tag'),before_board)
        self.assertEqual(self.ledger(),before)
        self.page.evaluate('()=>{safeStorageSet=questOriginalSet}')
        ui.complete(self.page,'job:tag',open_board=False);ui.room(self.page,'nurse')
        before=self.ledger();before_job=self.progress()['jobs']['k1']
        self.page.evaluate('()=>{safeStorageSet=(k,v)=>k.startsWith("palata404_floor10_reward:")?false:questOriginalSet(k,v)}')
        ui.action(self.page,'claim:k1')
        self.assertEqual(self.ledger(),before)
        self.assertEqual(self.progress()['jobs']['k1'],before_job)
        self.assertIn('tag',self.ledger()['cargo'])
        self.page.evaluate('()=>{safeStorageSet=questOriginalSet}')
        ui.action(self.page,'claim:k1');after=self.ledger()
        self.assertEqual(after['silver']-before['silver'],5)
        self.assertEqual(after['exp']-before['exp'],10)
        self.reload_home();self.assertEqual(self.ledger(),after)
        self.assertEqual(self.progress()['jobs']['k1']['count'],1)

    def test_mobile_keyboard_focus_escape_and_controls_remain_accessible(self):
        self.load();self.accept('k3');ui.room(self.page,'procedure');ui.action(self.page,'job:copies')
        self.assertEqual(self.page.evaluate('document.activeElement.hasAttribute("data-work-heading")'),True)
        for viewport in [{'width':390,'height':844},{'width':844,'height':390}]:
            self.page.set_viewport_size(viewport)
            if not self.page.locator('.quest-workbench').count():ui.action(self.page,'job:copies')
            geometry=self.page.locator('.quest-workbench').evaluate('''e=>{const r=e.getBoundingClientRect(),back=e.querySelector('.workbench-back').getBoundingClientRect(),footer=e.querySelector('.workbench-footer').getBoundingClientRect();return{overflow:e.scrollWidth>e.clientWidth,x:r.x,y:r.y,right:r.right,bottom:r.bottom,backVisible:back.x>=0&&back.right<=innerWidth&&back.y>=0&&back.bottom<=innerHeight,footerVisible:footer.y>=0&&footer.bottom<=innerHeight,smallButtons:[...e.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().height<43.9).length}}''')
            self.assertFalse(geometry['overflow'],geometry)
            self.assertTrue(geometry['backVisible'],geometry)
            self.assertTrue(geometry['footerVisible'],geometry)
            self.assertEqual(geometry['smallButtons'],0,geometry)
            button=self.page.locator('[data-work-op="mark"]').first
            field=button.get_attribute('data-work-value');button.focus();self.page.keyboard.press('Space')
            self.assertEqual(self.page.evaluate('document.activeElement.dataset.workOp'),'mark')
            self.assertEqual(self.page.evaluate('document.activeElement.dataset.workValue'),field)
            self.page.keyboard.press('Tab')
            self.assertTrue(self.page.locator('.quest-workbench').evaluate('e=>e.contains(document.activeElement)'))
            self.page.screenshot(path=str(OUT/f'keyboard-{viewport["width"]}.jpg'),type='jpeg',quality=90)
            self.page.keyboard.press('Escape')
            self.assertEqual(self.page.locator('.quest-workbench').count(),0)
            self.assertEqual(self.page.evaluate('document.activeElement.dataset.sceneAction||document.activeElement.dataset.action'),'job:copies')
            self.assertFalse(self.page.locator('.scene-paper').evaluate('e=>e.inert'))
        self.page.set_viewport_size({'width':1280,'height':800})
        self.accept('k1');ui.room(self.page,'procedure')
        ui.action(self.page,'job:tag')
        self.page.keyboard.press('Escape')
        self.assertEqual(self.page.evaluate('document.activeElement.dataset.sceneAction'),'job:tag')
        self.page.locator('[data-room-info-toggle]').click()
        self.assertEqual(self.page.locator('[data-room-info-toggle]').get_attribute('aria-expanded'),'false')
        self.page.locator('[data-action="job:tag"]').click()
        self.assertTrue(self.page.locator('.quest-workbench').is_visible())
        self.page.keyboard.press('Escape')
        self.assertEqual(self.page.locator('.quest-workbench').count(),0)
        self.assertEqual(self.page.evaluate('document.activeElement.dataset.action'),'job:tag')

    def test_legacy_v6_parcel_finishes_old_flow_then_repeat_uses_workbench(self):
        self.load()
        # Explicit compatibility fixture: an existing v6 player already carrying
        # linen on their fourth accepted run. No new mechanics are bypassed.
        fixture=self.page.evaluate('''()=>{const old={...PalataQuestEngine.initial(),version:6,
            room:'ward406',flags:{unlockB:true,unlockC:true},cargo:['linen'],
            jobs:{k2:{active:true,done:{linen:true},count:3,startTrip:0}},
            interactions:{'job:linen':1}};
            return {key:'palata404_floor10_progress:'+encodeURIComponent(raidArchiveOwnerId),raw:JSON.stringify(old)};}''')
        # Seed at next document startup, after the outgoing page has saved its
        # own checkpoint. Later reloads must retain the real migrated progress.
        self.context.add_init_script('if(!sessionStorage.getItem("questLegacyFixtureSeeded")){'
            f'localStorage.setItem({json.dumps(fixture["key"])},{json.dumps(fixture["raw"])});'
            'sessionStorage.setItem("questLegacyFixtureSeeded","1");}')
        self.reload_home()
        current=self.progress()
        self.assertEqual(current['jobs']['k2']['revision'],1)
        self.assertEqual(current['jobs']['k2']['count'],3)
        self.assertTrue(current['flags']['unlockB']);self.assertTrue(current['flags']['unlockC'])
        self.assertIn('linen',self.ledger()['cargo'])
        before=self.ledger()
        ui.room(self.page,'ward406');ui.action(self.page,'job:deliver')
        self.assertEqual(self.page.locator('.quest-workbench').count(),0)
        choice=self.page.locator('[data-scene-action="bed"]')
        (choice if choice.count() else self.page.locator('[data-choice="bed"]')).click()
        self.assertNotIn('linen',self.ledger()['cargo']);self.assertIn('delivery',self.ledger()['cargo'])
        ui.room(self.page,'nurse');ui.action(self.page,'claim:k2')
        claimed=self.ledger()
        self.assertEqual(claimed['silver']-before['silver'],8)
        self.assertEqual(claimed['exp']-before['exp'],15)
        self.assertEqual(claimed['medkits']-before['medkits'],1)
        self.assertEqual(self.progress()['jobs']['k2']['count'],4)
        self.assertEqual(self.page.locator('[data-action="claim:k2"]').count(),0)
        self.reload_home();self.assertEqual(self.ledger(),claimed)
        self.accept('k2')
        repeated=self.progress()['jobs']['k2']
        self.assertEqual(repeated['revision'],4);self.assertEqual(repeated['count'],4)
        self.assertEqual(repeated['variant'],1);self.assertEqual(repeated['done'],{})
        ui.room(self.page,'linen');ui.action(self.page,'job:linen')
        self.assertEqual(ui.board(self.page,'job:linen')['kind'],'packing')
        self.assertTrue(self.page.locator('.quest-workbench').is_visible())
        ui.complete(self.page,'job:linen',open_board=False)
        ui.room(self.page,'ward406');ui.complete(self.page,'job:deliver')
        ui.room(self.page,'nurse');ui.action(self.page,'claim:k2')
        after=self.ledger()
        self.assertEqual(after['silver']-claimed['silver'],8)
        self.assertEqual(after['exp']-claimed['exp'],15)
        self.assertEqual(after['medkits']-claimed['medkits'],1)
        self.assertEqual(self.progress()['jobs']['k2']['count'],5)
        self.reload_home();self.assertEqual(self.ledger(),after)

    def test_order_purpose_precedes_acceptance_and_partial_work_keeps_last_receipt(self):
        self.load();self.page.locator('.hud-task').click()
        self.page.locator('[data-quest-tab="nurse"]').click()
        brief=self.page.evaluate('PalataQuestEngine.jobBrief("k1")')
        card=self.page.locator('[data-quest-id="k1"]')
        self.assertIn(brief['purpose'],card.locator('.quest-order-purpose').inner_text())
        self.assertIn(brief['deliverable'],card.locator('.quest-order-deliverable').inner_text())
        self.assertFalse(self.progress()['jobs'].get('k1',{}).get('active',False))
        self.page.locator('#tasks-modal .modal-header button').click()
        ui.room(self.page,'nurse')
        offer=self.page.locator('[data-action="accept:k1"]')
        description=offer.get_attribute('aria-describedby')
        self.assertTrue(description)
        self.assertIn(brief['purpose'],self.page.locator('#'+description).inner_text())
        ui.action(self.page,'accept:k1');ui.room(self.page,'procedure')
        self.page.locator('[data-room-info-toggle]').click()
        self.assertEqual(self.page.locator('[data-room-info-toggle]').get_attribute('aria-expanded'),'false')
        self.page.locator('[data-action="job:tag"]').click()
        self.page.locator('#custom-toast-notification').wait_for(state='hidden')
        board=ui.board(self.page,'job:tag')
        self.assertIn(brief['purpose'],self.page.locator('.workbench-brief').inner_text())
        before_receipt=self.progress()['lastReceipt'];before=self.ledger()
        item=board['items'][0]['id']
        ui.operate(self.page,'inspect',item);ui.operate(self.page,'select',item)
        self.assertEqual(self.progress()['lastReceipt'],before_receipt)
        self.assertEqual(self.ledger(),before)
        self.assertTrue(self.page.locator('#custom-toast-notification').is_hidden())
        self.assertTrue(self.page.locator('.workbench-status').inner_text())
        saved_work=self.progress()['jobs']['k1']['work']
        self.reload_home();ui.room(self.page,'procedure')
        self.page.locator('[data-room-info-toggle]').click()
        self.page.locator('[data-action="job:tag"]').click()
        self.assertEqual(self.progress()['jobs']['k1']['work'],saved_work)
        self.assertEqual(self.progress()['lastReceipt'],before_receipt)
        ui.complete(self.page,'job:tag',open_board=False)
        receipt=self.progress()['lastReceipt']
        self.assertNotEqual(receipt,before_receipt)
        self.assertIn(board['request']['lot'],receipt)
        self.assertIn(board['request']['kit'].lower(),receipt.lower())
        self.assertIn('пломб',receipt.lower())
        self.assertEqual(self.page.locator('[data-room-info-toggle]').get_attribute('aria-expanded'),'true')
        visible=self.page.locator('.quest-receipt').evaluate('''e=>{const r=e.getBoundingClientRect(),paper=e.closest('.scene-paper').getBoundingClientRect();return{top:r.top,bottom:r.bottom,clipTop:Math.max(0,paper.top),clipBottom:Math.min(innerHeight,paper.bottom)}}''')
        self.assertGreaterEqual(visible['top'],visible['clipTop'],visible)
        self.assertLessEqual(visible['bottom'],visible['clipBottom'],visible)
        self.assertIn(board['request']['lot'],self.page.locator('.quest-receipt').inner_text())
        self.assertTrue(self.page.locator('#custom-toast-notification').is_hidden())
        self.assertIn('tag',self.ledger()['cargo'])
        self.assertEqual(self.ledger()['exp'],before['exp'])
        self.assertEqual(self.ledger()['silver'],before['silver'])

    def test_comparison_pairs_readable_sources_on_phone_and_landscape_without_answer_highlights(self):
        self.load();self.accept('k3');ui.room(self.page,'procedure');ui.action(self.page,'job:copies')
        board=ui.board(self.page,'job:copies')
        self.page.locator('#custom-toast-notification').wait_for(state='hidden')
        for width,height in [(1280,800),(390,844),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.assert_paired_fields(board['documents'][0]['fields'],board['documents'][1]['fields'])
                geometry=self.page.locator('.workbench-pairing').evaluate('''e=>({overflow:e.scrollWidth>e.clientWidth,rows:[...e.querySelectorAll('[data-work-field]')].map(row=>{const r=row.getBoundingClientRect();return{x:r.x,right:r.right,height:r.height}})})''')
                self.assertFalse(geometry['overflow'],geometry)
                for row in geometry['rows']:
                    self.assertGreaterEqual(row['x'],0,geometry)
                    self.assertLessEqual(row['right'],width,geometry)
                    self.assertGreaterEqual(row['height'],44,geometry)
                if height==390:
                    self.page.locator('.workbench-scroll').evaluate('e=>{e.scrollTop=0}')
                    visible=self.page.locator('.quest-workbench').evaluate('''e=>{const top=e.querySelector('.workbench-scroll').getBoundingClientRect().top,bottom=e.querySelector('.workbench-footer').getBoundingClientRect().top;return[...e.querySelector('[data-work-field]').querySelectorAll('.workbench-pair-value')].map(value=>{const r=value.getBoundingClientRect();return{top:r.top,bottom:r.bottom,visible:r.top>=top&&r.bottom<=bottom}})}''')
                    self.assertTrue(all(value['visible'] for value in visible),visible)
                if width==390:
                    self.page.locator('.workbench-brief summary').click()
                    self.page.locator('[data-work-field="signature"]').focus()
                    scroll_before_wheel=self.page.locator('.workbench-scroll').evaluate('e=>e.scrollTop')
                    self.page.locator('.workbench-scroll').hover();self.page.mouse.wheel(0,260)
                    # Focus already scrolls this field into view. scrollTop>0
                    # therefore passes before Chromium processes the wheel.
                    # Wait for the actual scroll input and stable paint frames
                    # before comparing it with a background refresh.
                    self.page.wait_for_function('before=>document.querySelector(".workbench-scroll").scrollTop>before',arg=scroll_before_wheel)
                    self.page.evaluate('''()=>new Promise(resolve=>{
                        const scroller=document.querySelector('.workbench-scroll');
                        let previous=scroller.scrollTop,stable=0,frames=0;
                        const settled=()=>{
                            const current=scroller.scrollTop;
                            stable=current===previous?stable+1:0;previous=current;
                            if(++frames>=3&&stable>=3){resolve();return;}
                            requestAnimationFrame(settled);
                        };
                        requestAnimationFrame(settled);
                    })''')
                    view='''()=>({scroll:document.querySelector('.workbench-scroll').scrollTop,briefOpen:document.querySelector('.workbench-brief').open,focus:document.activeElement.dataset.workFocus||null,work:PalataQuestPrototype.snapshot().jobs.k3.work})'''
                    before_view=self.page.evaluate(view);before_ledger=self.ledger()
                    # Energy and other background updates use this real refresh path.
                    self.page.evaluate('updateUI()')
                    self.page.wait_for_function('document.activeElement.dataset.workFocus==="mark:signature"')
                    self.assertEqual(self.page.evaluate(view),before_view)
                    self.assertEqual(self.ledger(),before_ledger)
                    self.page.locator('.workbench-brief summary').click()
                field=board['documents'][0]['fields'][0]['id']
                row=self.page.locator(f'[data-work-field="{field}"]')
                row.focus();self.page.keyboard.press('Space')
                self.assertEqual(self.page.locator(f'[data-work-field="{field}"]').get_attribute('aria-pressed'),'true')
                self.assertEqual(self.page.evaluate('document.activeElement.dataset.workField'),field)
                self.page.keyboard.press('Space')
                self.assertEqual(ui.board(self.page,'job:copies')['marked'],[])
                self.assertNotIn('copies',self.ledger()['cargo'])

    def test_linen_labels_dimensions_and_unvalidated_bundle_remain_auditable(self):
        self.load();self.accept('k2');ui.room(self.page,'linen');ui.action(self.page,'job:linen')
        board=ui.board(self.page,'job:linen');before=self.ledger()
        self.assertIn('Маркировка комплекта',self.page.locator('.workbench-request').inner_text())
        note=self.page.locator('.workbench-marking-note').evaluate('e=>({width:e.getBoundingClientRect().width,request:e.parentElement.getBoundingClientRect().width})')
        self.assertGreaterEqual(note['width'],note['request']*.75,note)
        first_row=self.page.locator('.quest-workbench').evaluate('''e=>{const top=e.querySelector('.workbench-scroll').getBoundingClientRect().top,bottom=e.querySelector('.workbench-footer').getBoundingClientRect().top;return[...e.querySelectorAll('[data-work-item]')].slice(0,3).map(card=>{const value=card.querySelector('.workbench-condition span').getBoundingClientRect(),pick=card.querySelector('[data-work-op="select"]').getBoundingClientRect();return{condition:value.top>=top&&value.bottom<=bottom,pick:pick.top>=top&&pick.bottom<=bottom,conditionBottom:value.bottom,pickBottom:pick.bottom,footer:bottom}})}''')
        self.assertTrue(all(item['condition'] and item['pick'] for item in first_row),first_row)
        for item in board['items']:
            card=self.page.locator(f'[data-work-item="{item["id"]}"]')
            self.assertIn(item['size'],card.locator('.workbench-kit-mark').inner_text())
            self.assertIn(item['measure'],card.locator('.workbench-linen-measure').inner_text())
            self.assertEqual(card.locator('.workbench-condition span').inner_text(),item['condition'])
        wrong=[item for item in board['items'] if item['type']=='Простыня'][:2]
        for item in wrong:ui.operate(self.page,'select',item['id'])
        packed=self.page.locator('.workbench-packing-list')
        self.assertEqual(packed.locator('.workbench-picked').count(),2)
        for item in wrong:
            summary=next(text for text in packed.locator('.workbench-picked').all_inner_texts() if item['measure'] in text)
            for value in [item['type'],item['size'],item['measure'],item['condition']]:self.assertIn(value,summary)
        selected=ui.board(self.page,'job:linen')
        ui.operate(self.page,'submit')
        self.assertEqual(ui.board(self.page,'job:linen'),selected)
        self.assertEqual(self.ledger(),before)
        self.assertNotIn('linen',self.ledger()['cargo'])
        self.assertIn('чистых целых упаковках',self.page.locator('.workbench-status').inner_text())

    def test_mobile_map_panning_preview_and_room_documents_remain_readable(self):
        self.page.set_viewport_size({'width':390,'height':844})
        self.load();self.page.locator('#location-card-box').click()
        geometry=self.page.locator('#map-floors-view').evaluate('''e=>{
            const plan=e.querySelector('.quest-blueprint').getBoundingClientRect(),
                metadata=e.querySelector('.quest-map-sidebar').getBoundingClientRect();
            return {planBottom:plan.bottom,metadataTop:metadata.top,
                headings:[...document.querySelectorAll('.quest-official-header .document-ministry,.quest-official-header .document-institution,.quest-official-header .document-department')].map(n=>({text:n.innerText,width:n.clientWidth,scrollWidth:n.scrollWidth,height:n.clientHeight,scrollHeight:n.scrollHeight}))};
        }''')
        self.assertLessEqual(geometry['planBottom'],geometry['metadataTop'],geometry)
        self.assertEqual(len(geometry['headings']),3,geometry)
        for heading in geometry['headings']:
            self.assertTrue(heading['text'].strip(),heading)
            self.assertLessEqual(heading['scrollWidth'],heading['width'],heading)
            self.assertLessEqual(heading['scrollHeight'],heading['height'],heading)

        # Native UI scroll and keyboard focus must survive an ordinary HUD refresh.
        pan=self.page.locator('.quest-blueprint-viewport');pan.focus()
        pan.evaluate('e=>e.scrollLeft=250')
        self.page.evaluate('updateUI()')
        self.assertEqual(pan.evaluate('e=>e.scrollLeft'),250)
        self.assertTrue(pan.evaluate('e=>document.activeElement===e'))
        self.page.keyboard.press('ArrowRight')
        self.page.wait_for_function('document.querySelector(".quest-blueprint-viewport").scrollLeft>250')

        # A single click reveals the room description below the panned plan.
        self.page.locator('.quest-map-pin[data-room="nurse"]').click()
        self.page.wait_for_function('''()=>{
            const card=document.querySelector('.quest-room-preview');if(!card)return false;
            const r=card.getBoundingClientRect(),frame=card.closest('.quest-floor').getBoundingClientRect();
            return r.top>=frame.top-1&&r.bottom<=frame.bottom+1;
        }''')
        self.page.locator('[data-enter-room="nurse"]').click()
        self.page.wait_for_function('PalataQuestPrototype.snapshot().room==="nurse"&&!document.getElementById("quest-location-screen").classList.contains("hidden")')
        paper=self.page.locator('.scene-paper')
        self.assertLessEqual(paper.evaluate('e=>e.scrollWidth'),paper.evaluate('e=>e.clientWidth'))
        for control in paper.locator('h3,button').all():
            if not control.is_visible():continue
            self.assertLessEqual(control.evaluate('e=>e.scrollWidth'),control.evaluate('e=>e.clientWidth'),control.inner_text())
        for control in paper.locator('button').all():
            if not control.is_visible():continue
            control.evaluate('e=>e.scrollIntoView({block:"center"})')
            control.click(trial=True,timeout=3000)

        paper.get_by_role('button',name='Открыть задания',exact=True).click()
        self.assertTrue(self.page.locator('#tasks-modal').is_visible())
        self.page.locator('#tasks-modal [onclick="closeTasks()"]').click()
        paper.get_by_role('button',name='Вернуться к карте',exact=True).click()
        self.assertTrue(self.page.locator('#map-modal').is_visible())
        self.assertTrue(self.page.locator('#quest-location-screen').is_hidden())
        # The existing fast double-click route remains usable too.
        ui.room(self.page,'ward404')
        self.assertEqual(self.progress()['room'],'ward404')


if __name__=='__main__':unittest.main()
