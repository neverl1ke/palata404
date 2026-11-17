"""Real UI consequences: partial work, world records, repeat orders and recovery.

Only the explicitly named compatibility case seeds a previous persisted save.
Every other quest state is reached through actual game controls.
"""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import unittest

from tests import test_game
from tests import test_quest_workbenches as previous
from tests import quest_ui_support as ui

OUT=Path('/dev/shm/quest-world-20261117')
OUT.mkdir(parents=True,exist_ok=True)


class QuestWorldTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
    setUp=previous.QuestWorkbenchTests.setUp
    tearDown=test_game.GameTests.tearDown
    load=test_game.GameTests.load
    accept=previous.QuestWorkbenchTests.accept
    progress=previous.QuestWorkbenchTests.progress
    ledger=previous.QuestWorkbenchTests.ledger
    reload_home=previous.QuestWorkbenchTests.reload_home

    def world(self):
        return self.progress()['world']

    def packed_linen(self):
        self.accept('k2')
        ui.room(self.page,'linen');ui.complete(self.page,'job:linen')
        self.assertIn('linen',self.ledger()['cargo'])

    def finish_linen_order(self):
        ui.room(self.page,'ward406');ui.complete(self.page,'job:deliver')
        ui.room(self.page,'nurse');ui.action(self.page,'claim:k2')

    def effect(self,id):
        return self.page.locator(f'.quest-world-effect[data-world-effect="{id}"]')

    def assert_room_art(self,mode):
        expected=f'assets/quest-world/ward406-{mode}.webp'
        self.assertEqual(self.page.locator('.scene-painting').get_attribute('src'),expected)
        self.page.wait_for_function('document.querySelector(".scene-painting")?.complete&&document.querySelector(".scene-painting").naturalWidth>0')
        self.assertEqual(self.page.locator('.scene-painting').evaluate('e=>[e.naturalWidth,e.naturalHeight]'),[1536,1024])
        self.assertTrue(self.page.locator('.quest-room-scene').evaluate('e=>e.classList.contains("paired-art")'))
        self.assertEqual(self.page.locator('.scene-painting').evaluate('e=>getComputedStyle(e).filter'),'none')

    def test_bed_uses_both_real_parcel_pieces_and_survives_claim_repeat_reload(self):
        self.load();self.packed_linen();before=self.ledger()
        ui.room(self.page,'ward406');self.assert_room_art('patient')
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').count(),1)
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').get_attribute('data-pending-pieces'),'sheet,pillowcase')
        self.assertEqual(self.page.locator('[data-world-item="prepared-linen"]').count(),0)
        ui.action(self.page,'job:deliver')
        board=ui.board(self.page,'job:deliver')
        self.assertEqual(board['kind'],'bedmaking')
        self.assertEqual({item['id'] for item in board['items']},{'sheet','pillowcase'})
        self.assertEqual(board['placed'],[])
        self.assertFalse(self.world()['linen406'])
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').count(),1)
        self.page.set_viewport_size({'width':844,'height':390})
        # The game's viewport/orientation handler rebuilds the compact view
        # asynchronously. Check its actual ready geometry, not a fixed sleep.
        self.page.wait_for_function('''()=>{const e=document.querySelector('.quest-workbench');if(!e)return false;const top=e.querySelector('.workbench-scroll').getBoundingClientRect().top,bottom=e.querySelector('.workbench-footer').getBoundingClientRect().top,buttons=[...e.querySelectorAll('[data-work-op="selectPiece"],[data-work-op="place"]')];return buttons.length===4&&buttons.every(b=>{const r=b.getBoundingClientRect();return r.top>=top&&r.bottom<=bottom&&r.left>=0&&r.right<=innerWidth&&r.height>=44})}''',timeout=3000)
        geometry=self.page.locator('.quest-workbench').evaluate('''e=>{const top=e.querySelector('.workbench-scroll').getBoundingClientRect().top,bottom=e.querySelector('.workbench-footer').getBoundingClientRect().top;return[...e.querySelectorAll('[data-work-op="selectPiece"],[data-work-op="place"]')].map(b=>{const r=b.getBoundingClientRect();return{operation:b.dataset.workOp,top:r.top,bottom:r.bottom,left:r.left,right:r.right,visible:r.top>=top&&r.bottom<=bottom&&r.left>=0&&r.right<=innerWidth,height:r.height}})}''')
        self.assertEqual(len(geometry),4,geometry)
        self.assertTrue(all(button['visible'] and button['height']>=44 for button in geometry),geometry)
        self.page.set_viewport_size({'width':1280,'height':800})
        ui.operate(self.page,'selectPiece','sheet')
        wrong=ui.board(self.page,'job:deliver');world_before=self.world()
        ui.operate(self.page,'place','pillowZone')
        self.assertEqual(ui.board(self.page,'job:deliver'),wrong)
        self.assertEqual(self.world(),world_before)
        self.assertEqual(self.ledger(),before)
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').get_attribute('data-pending-pieces'),'sheet,pillowcase')
        ui.operate(self.page,'place','sheetZone')
        self.assertEqual(ui.board(self.page,'job:deliver')['placed'],['sheet'])
        self.assertIn('linen',self.ledger()['cargo'])
        self.assertNotIn('delivery',self.ledger()['cargo'])
        self.assertFalse(self.world()['linen406'])
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').count(),1)
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').get_attribute('data-pending-pieces'),'pillowcase')
        self.assertIn('простыня уже размещена',self.page.locator('[data-world-item="pending-bed-linen"]').get_attribute('aria-label'))
        saved_work=copy.deepcopy(self.progress()['jobs']['k2']['work'])
        self.reload_home()
        self.assertEqual(self.progress()['jobs']['k2']['work'],saved_work)
        self.assertEqual(self.ledger(),before)
        ui.room(self.page,'ward406');ui.action(self.page,'job:deliver')
        self.assertEqual(ui.board(self.page,'job:deliver')['placed'],['sheet'])
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').get_attribute('data-pending-pieces'),'pillowcase')
        ui.operate(self.page,'selectPiece','pillowcase');ui.operate(self.page,'place','pillowZone')
        self.assertEqual(self.page.locator('.quest-workbench').count(),0)
        self.assertNotIn('linen',self.ledger()['cargo']);self.assertIn('delivery',self.ledger()['cargo'])
        prepared=copy.deepcopy(self.world()['linen406'])
        self.assertTrue(prepared['prepared']);self.assertTrue(prepared['delivered'])
        self.assertEqual(prepared['order'],'k2:1')
        self.assertEqual(self.effect('linen406').count(),1)
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').count(),0)
        self.assertEqual(self.page.locator('[data-world-item="prepared-linen"]').count(),1)
        self.assert_room_art('patient')
        self.assertEqual(self.page.locator('[data-action="job:deliver"]').count(),0)
        ui.room(self.page,'nurse');ui.action(self.page,'claim:k2')
        claimed=self.ledger()
        self.assertEqual(claimed['silver']-before['silver'],8)
        self.assertEqual(claimed['exp']-before['exp'],15)
        self.assertEqual(claimed['medkits']-before['medkits'],1)
        for key in ['order','prepared','delivered','mark','items']:
            self.assertEqual(self.world()['linen406'][key],prepared[key])
        self.assertTrue(self.world()['linen406']['reviewed'])
        prepared=copy.deepcopy(self.world()['linen406'])
        self.accept('k2')
        self.assertEqual(self.world()['linen406'],prepared)
        self.reload_home();self.assertEqual(self.world()['linen406'],prepared)
        ui.room(self.page,'ward406')
        self.assertEqual(self.effect('linen406').count(),1)
        self.assertEqual(self.page.locator('[data-world-item="prepared-linen"]').count(),1)
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').count(),0)
        self.assertNotIn('linen',self.ledger()['cargo'])
        self.assertEqual(self.page.locator('[data-action="claim:k2"]').count(),0)
        # Use the shipped accessibility switch for a real visit in both modes;
        # it opens sections without altering this unfinished order or rewards.
        before_mode=self.ledger();ui.return_home(self.page)
        self.page.locator('#quest-unlock-all').click()
        self.page.locator('.room-trip-switch').click();ui.room(self.page,'ward406')
        self.assert_room_art('trip')
        self.assertEqual(self.effect('linen406').count(),0)
        self.assertEqual(self.page.locator('[data-world-item="prepared-linen"]').count(),0)
        self.assertEqual(self.world()['linen406'],prepared)
        ui.return_home(self.page);self.page.locator('.room-trip-switch').click();ui.room(self.page,'ward406')
        self.assert_room_art('patient')
        self.assertEqual(self.page.locator('[data-world-item="prepared-linen"]').count(),1)
        self.assertEqual(self.ledger(),before_mode)
        original=Path(__file__).resolve().parents[1]/'assets/quest-scenes/ward406.webp'
        reference=subprocess.check_output(['git','show','47eedf3:assets/quest-scenes/ward406.webp'],cwd=original.parents[2])
        self.assertEqual(hashlib.sha256(original.read_bytes()).digest(),hashlib.sha256(reference).digest())

    def test_missing_pillow_requires_real_clara_permission_for_matching_reserve(self):
        self.load();self.packed_linen();self.finish_linen_order()
        self.accept('k2');self.assertEqual(self.progress()['jobs']['k2']['variant'],1)
        ui.room(self.page,'linen');ui.action(self.page,'job:linen')
        packing=ui.board(self.page,'job:linen')
        self.assertTrue(packing['request']['missingComponent'])
        self.assertTrue(any(item.get('unavailable') for item in packing['items']))
        self.assertFalse(self.progress()['jobs']['k2']['work']['reserveGranted'])
        before=self.ledger();ui.operate(self.page,'noteShortage')
        self.assertTrue(self.progress()['jobs']['k2']['work']['shortageNoted'])
        self.page.locator('[data-work-focus="close"]').click()
        ui.return_home(self.page);self.page.locator('.hud-task').click()
        self.page.locator('[data-quest-tab="nurse"]').click()
        card=self.page.locator('[data-quest-id="k2"]')
        self.assertIn('Клар',card.inner_text())
        card.get_by_role('button',name='Показать на карте',exact=True).click()
        ui.room(self.page,'nurse');ui.action(self.page,'job:linenReserve')
        request=ui.board(self.page,'job:linenReserve')
        self.assertEqual(request['kind'],'clarification')
        bad=next(item for item in request['options'] if item['measure']!=request['request']['neededMeasure'])
        ui.operate(self.page,'select',bad['id']);before_wrong=ui.board(self.page,'job:linenReserve')
        ui.operate(self.page,'submit')
        self.assertEqual(ui.board(self.page,'job:linenReserve'),before_wrong)
        self.assertFalse(self.progress()['jobs']['k2']['work']['reserveGranted'])
        self.assertEqual(self.ledger(),before)
        good=next(item for item in request['options'] if item['measure']==request['request']['neededMeasure'])
        ui.operate(self.page,'select',good['id']);ui.operate(self.page,'submit')
        self.assertTrue(self.progress()['jobs']['k2']['work']['reserveGranted'])
        self.assertNotIn('linen',self.ledger()['cargo'])
        self.reload_home();self.assertTrue(self.progress()['jobs']['k2']['work']['reserveGranted'])
        ui.room(self.page,'linen');ui.action(self.page,'job:linen')
        authorized=ui.board(self.page,'job:linen')
        self.assertTrue(authorized.get('authorizedSubstitution'))
        self.assertIn(request['request']['neededMeasure'],self.page.locator('.quest-workbench').inner_text())
        ui.complete(self.page,'job:linen',open_board=False)
        self.assertIn('linen',self.ledger()['cargo'])
        self.finish_linen_order()
        after=self.ledger()
        self.assertEqual(after['silver']-before['silver'],8)
        self.assertEqual(after['exp']-before['exp'],15)
        self.assertEqual(after['medkits']-before['medkits'],1)
        self.assertEqual(self.progress()['jobs']['k2']['count'],2)
        self.assertEqual(self.world()['linen406']['order'],'k2:2')

    def test_doctor_reviews_observed_calls_without_automatically_repairing_them(self):
        self.load();self.accept('d1');before=self.ledger();observations={}
        for room in ['ward407','ward408']:
            action='job:bell'+room[-3:]
            ui.room(self.page,room);ui.action(self.page,action)
            ui.operate(self.page,'inspect','connector');ui.operate(self.page,'test')
            board=ui.board(self.page,action)
            observations[room]=copy.deepcopy(board)
            record=self.world()['calls'][room]
            self.assertTrue(record['tested'])
            self.assertEqual(record['connected'],board['connector']['connected'])
            self.assertEqual(record['indicator'],board['indicator'])
            self.assertFalse(self.world()['doctorReview'])
            self.assertNotEqual(self.page.locator(f'[data-call-room="{room}"]').inner_text(),'✓')
            ui.complete(self.page,action,open_board=False)
            self.assertEqual(self.effect('call:'+room).count(),1)
            expected='disconnected' if not board['connector']['connected'] else 'working' if 'вызов принят' in board['response'] else 'noResponse'
            self.assertEqual(self.world()['calls'][room]['report'],expected)
            self.assertEqual(self.page.locator(f'[data-call-room="{room}"]').inner_text(),'✓' if expected=='working' else '!')
        ui.room(self.page,'doctor');ui.action(self.page,'claim:d1')
        review=copy.deepcopy(self.world()['doctorReview'])
        self.assertEqual(review['order'],'d1:1')
        self.assertTrue(review['maintenance'])
        self.assertEqual(self.effect('doctorReview').count(),1)
        visible=self.effect('doctorReview').evaluate('''e=>{const r=e.getBoundingClientRect(),paper=e.closest('.scene-paper').getBoundingClientRect();return{top:r.top,bottom:r.bottom,clipTop:Math.max(0,paper.top),clipBottom:Math.min(innerHeight,paper.bottom)}}''')
        self.assertGreaterEqual(visible['top'],visible['clipTop'],visible)
        self.assertLessEqual(visible['bottom'],visible['clipBottom'],visible)
        self.assertIn('408',self.effect('doctorReview').inner_text())
        self.assertEqual(self.world()['calls']['ward408']['connected'],False)
        self.assertEqual(self.world()['calls']['ward408']['indicator'],'off')
        after=self.ledger()
        self.assertEqual(after['silver']-before['silver'],10)
        self.assertEqual(after['exp']-before['exp'],20)
        self.reload_home();self.assertEqual(self.world()['doctorReview'],review)
        self.accept('d1')
        self.assertEqual(self.world()['doctorReview'],review)
        ui.room(self.page,'ward407');ui.action(self.page,'job:bell407')
        ui.operate(self.page,'inspect','connector');ui.operate(self.page,'test')
        self.assertEqual(self.world()['calls']['ward407']['order'],'d1:2')
        self.assertEqual(self.world()['doctorReview'],review)
        self.assertEqual(self.world()['doctorReview']['order'],'d1:1')

    def test_failed_final_placement_rolls_back_world_cargo_and_work_together(self):
        self.load();self.packed_linen();ui.room(self.page,'ward406');ui.action(self.page,'job:deliver')
        # The opposite placement order must show only the actual unused sheet.
        ui.operate(self.page,'selectPiece','pillowcase');ui.operate(self.page,'place','pillowZone')
        ui.operate(self.page,'selectPiece','sheet')
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').get_attribute('data-pending-pieces'),'sheet')
        self.assertIn('наволочка уже размещена',self.page.locator('[data-world-item="pending-bed-linen"]').get_attribute('aria-label'))
        before={'world':self.world(),'work':self.progress()['jobs']['k2']['work'],'ledger':self.ledger()}
        self.page.evaluate('''()=>{window.worldOriginalSet=safeStorageSet;safeStorageSet=(k,v)=>String(k).startsWith('palata404_floor10_reward:')?false:worldOriginalSet(k,v);}''')
        ui.operate(self.page,'place','sheetZone')
        self.assertIn('Не удалось сохранить',self.page.locator('.workbench-status').inner_text())
        self.assertEqual({'world':self.world(),'work':self.progress()['jobs']['k2']['work'],'ledger':self.ledger()},before)
        self.assertEqual(self.effect('linen406').count(),0)
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').count(),1)
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').get_attribute('data-pending-pieces'),'sheet')
        self.assertEqual(self.page.locator('[data-world-item="prepared-linen"]').count(),0)
        self.page.evaluate('()=>{safeStorageSet=worldOriginalSet;}')
        ui.operate(self.page,'place','sheetZone')
        self.assertTrue(self.world()['linen406']['prepared'])
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').count(),0)
        self.assertEqual(self.page.locator('[data-world-item="prepared-linen"]').count(),1)
        self.assertIn('delivery',self.ledger()['cargo'])
        self.assertNotIn('linen',self.ledger()['cargo'])
        ui.room(self.page,'nurse');ui.action(self.page,'claim:k2')
        claimed={'world':self.world(),'ledger':self.ledger()}
        self.reload_home();self.assertEqual({'world':self.world(),'ledger':self.ledger()},claimed)

    def test_explicit_v7_active_v2_parcel_keeps_original_delivery_and_no_fake_bed(self):
        self.load()
        fixture=self.page.evaluate('''()=>{const old={...PalataQuestEngine.initial(),version:7,
            room:'ward406',flags:{unlockB:true,unlockC:true},cargo:['linen'],
            jobs:{k2:{active:true,done:{linen:true},count:2,startTrip:0,revision:2,variant:2,work:{selected:['linen-0','linen-1']}}},
            interactions:{'job:linen':1}};delete old.world;
            return {key:'palata404_floor10_progress:'+encodeURIComponent(raidArchiveOwnerId),raw:JSON.stringify(old)};}''')
        self.context.add_init_script('if(!sessionStorage.getItem("worldLegacyFixtureSeeded")){'
            f'localStorage.setItem({json.dumps(fixture["key"])},{json.dumps(fixture["raw"])});'
            'sessionStorage.setItem("worldLegacyFixtureSeeded","1");}')
        self.reload_home()
        self.assertEqual(self.progress()['version'],8)
        self.assertEqual(self.progress()['jobs']['k2']['revision'],2)
        self.assertFalse(self.world()['linen406'])
        before=self.ledger();ui.room(self.page,'ward406');ui.action(self.page,'job:deliver')
        self.assertEqual(ui.board(self.page,'job:deliver')['kind'],'delivery')
        ui.operate(self.page,'deliver')
        if self.world()['linen406']:
            self.assertFalse(self.world()['linen406']['prepared'])
        self.assertEqual(self.page.locator('[data-world-item="prepared-linen"]').count(),0)
        self.assertEqual(self.page.locator('[data-world-item="delivered-linen"]').count(),1)
        self.assertEqual(self.page.locator('[data-world-item="pending-bed-linen"]').count(),0)
        self.assertNotIn('linen',self.ledger()['cargo']);self.assertIn('delivery',self.ledger()['cargo'])
        ui.room(self.page,'nurse');ui.action(self.page,'claim:k2')
        self.assertEqual(self.ledger()['silver']-before['silver'],8)
        self.assertEqual(self.ledger()['exp']-before['exp'],15)
        self.assertEqual(self.progress()['jobs']['k2']['count'],3)
        self.reload_home();self.assertEqual(self.progress()['jobs']['k2']['revision'],2)
        self.accept('k2');self.assertEqual(self.progress()['jobs']['k2']['revision'],3)


if __name__=='__main__':
    unittest.main()
