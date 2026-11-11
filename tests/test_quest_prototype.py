"""Full isolated flow, real browser UI and raid persistence (no personal profile)."""
import functools
import http.server
import os
from pathlib import Path
import threading
import unittest
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
class QuestBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT)))
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.pw=sync_playwright().start()
        kw={'headless':True}
        if os.getenv('PALATA_BROWSER_PATH'): kw['executable_path']=os.environ['PALATA_BROWSER_PATH']
        cls.browser=cls.pw.chromium.launch(**kw)
    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close()
    def test_floor_audit(self):
        ctx=self.browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce')
        p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.on('dialog',lambda d:d.dismiss())
        base=f'http://127.0.0.1:{self.server.server_port}'
        out=ROOT/'test-results/quest-prototype';out.mkdir(parents=True,exist_ok=True)
        p.goto(base+'/quest-test.html');p.wait_for_function('!!window.PalataQuestPrototype')
        p.evaluate("localStorage.setItem('audit-marker','keep')")
        def state(): return p.evaluate('PalataQuestPrototype.snapshot()')
        def map_open(): p.evaluate('toggleMapModal(true)')
        def room(id):
            map_open();p.locator(f'[data-room="{id}"]').click()
            p.locator(f'[data-scene-room="{id}"]').wait_for(state='visible')
            self.assertEqual(state()['room'],id)
        def action(id):
            p.locator(f'[data-action="{id}"]').click()
            # Drive actual rendered object targets, use the engine only as an oracle.
            while p.locator('[data-choice]').count():
                snap=state();steps=p.evaluate('(id)=>PalataQuestEngine.interactions[id]?.steps',id)
                if not steps: break
                i=snap['interactions'].get(id,0)
                if i>=len(steps): break
                p.locator(f'[data-choice="{steps[i]["answer"]}"]').click()
                if id=='exercise' and state()['exerciseCount']>0: break
        p.get_by_role('button',name='Задания',exact=True).click()
        p.locator('#quest-list .quest-card').first.get_by_role('button',name='Перейти к заданию').click()
        p.locator('[data-scene-room="A"]').wait_for(state='visible')
        self.assertTrue(p.locator('#map-modal').is_hidden())
        p.locator('[data-action="markerA"]').click();p.locator('[data-choice="bench"]').click()
        self.assertFalse(state()['flags'].get('markerA',False))
        p.locator('[data-choice="sign"]').focus();p.locator('[data-choice="sign"]').press('Enter')
        p.reload();p.wait_for_function('!!window.PalataQuestPrototype');self.assertEqual(state()['room'],'A');self.assertEqual(state()['interactions']['markerA'],1)
        room('A');action('markerA')
        # Direct travel, including both directions between distant sections.
        for dest in ['doctor','ward405','stairs','collector','ward408','nurse','technical','linen','ward406','ward407','toilet','gym']:
            room(dest);p.wait_for_function("document.querySelector('.scene-painting').naturalWidth>0")
        action('exercise');self.assertEqual(state()['exerciseCount'],1)
        p.screenshot(path=str(out/'patient-gym.png'))
        room('B');action('markerB');room('procedure');action('record');room('doctor');action('observation');room('stairs');action('stairsPatient')
        room('nurse');action('accept:k2');room('linen');action('job:linen');room('ward406');action('job:deliver');room('nurse');action('claim:k2')
        self.assertEqual(state()['materials'],2)
        self.assertEqual(p.locator('[data-action="claim:k2"]').count(),0)
        action('accept:k2');self.assertFalse(state()['jobs']['k2']['done'])
        p.screenshot(path=str(out/'patient-nurse-art-blocker.png'))
        room('ward404');map_open()
        self.assertEqual(p.locator('#map-modal').get_by_role('button',name='Войти в Трип',exact=True).count(),0)
        p.screenshot(path=str(out/'map-patient.png'))
        p.locator('#map-modal .btn-close-map').click();p.locator('.room-trip-switch').click();map_open()
        p.locator('[data-room="doctor"]').click();self.assertEqual(state()['room'],'ward404')
        self.assertEqual(p.locator('.quest-locked-zone').count(),2);p.screenshot(path=str(out/'map-trip-locked.png'))
        p.emulate_media(reduced_motion='no-preference');p.locator('[data-room="A"]').click();p.locator('.quest-traveller').wait_for(state='visible');self.assertEqual(state()['room'],'ward404')
        p.locator('[data-scene-room="A"]').wait_for(state='visible');p.emulate_media(reduced_motion='reduce');action('unlockB')
        room('nurse');action('boss:nurse');self.assertTrue(p.evaluate('isBattleActive'))
        p.evaluate('performPlayerAttack()');identity=p.evaluate('currentBattleSession.id');hp=p.evaluate('bossCurrentHp');end=p.evaluate('raidEndsAt')
        p.reload();p.wait_for_function('!!window.PalataQuestPrototype');self.assertTrue(p.evaluate('isBattleActive'));self.assertEqual(p.evaluate('currentBattleSession.id'),identity);self.assertEqual(p.evaluate('bossCurrentHp'),hp);self.assertEqual(p.evaluate('raidEndsAt'),end)
        p.screenshot(path=str(out/'raid-resumed.png'))
        p.evaluate('bossCurrentHp=0;handleVictory()');silver=p.evaluate('stats.silver');p.evaluate('handleVictory()');self.assertEqual(p.evaluate('stats.silver'),silver);self.assertFalse(state()['flags'].get('unlockC',False))
        p.evaluate('victoryContinueToMap()');room('nurse');action('boss:nurse');self.assertNotEqual(p.evaluate('currentBattleSession.id'),identity)
        p.evaluate('bossCurrentHp=0;handleVictory();victoryContinueToMap()');self.assertGreater(p.evaluate('stats.silver'),silver)
        room('B');action('unlockC');room('doctor');action('boss:doctor');p.evaluate('bossCurrentHp=0;handleVictory();victoryContinueToMap()')
        room('stairs');action('exit');before=state();action('descend');self.assertEqual(state(),before)
        p.reload();p.wait_for_function('!!window.PalataQuestPrototype');self.assertEqual(state()['room'],'stairs');self.assertTrue(state()['flags']['exit'])
        room('ward404');p.locator('.quest-location').get_by_role('button',name='Выйти из Трипа',exact=True).click();room('stairs');self.assertEqual(p.locator('[data-action="descend"]').count(),0)
        p.set_viewport_size({'width':844,'height':390});p.goto(base+'/quest-play.html');f=p.frame_locator('#game-canvas');f.get_by_role('button',name='Вернуться к карте',exact=True).click();f.locator('[data-room="gym"]').click();f.locator('[data-scene-room="gym"]').wait_for(state='visible');p.screenshot(path=str(out/'mobile-gym.png'))
        self.assertEqual(errors,[]);ctx.close()
if __name__=='__main__':unittest.main()
