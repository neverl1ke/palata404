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

    def accept(self,id):
        ui.room(self.page,'nurse' if id.startswith('k') else 'doctor')
        ui.action(self.page,'accept:'+id)
        job=self.progress()['jobs'][id]
        self.assertTrue(job['active'])
        self.assertEqual(job['revision'],2)

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
                ui.room(self.page,room);ui.complete(self.page,'job:bell'+room[-3:])
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
        self.assertEqual(self.page.locator('[data-world-item="delivered-linen"]').count(),1)
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
        ui.complete(self.page,'job:difference')
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
        self.assertEqual(repeated['revision'],2);self.assertEqual(repeated['count'],4)
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


if __name__=='__main__':unittest.main()
