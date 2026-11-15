"""Actual click-driven boxing, contact timing, persistence and cancellation."""
import json
from pathlib import Path
import unittest
from tests import test_game
OUT=Path('/workspace/artifacts/level-rehab/boxing-live');OUT.mkdir(parents=True,exist_ok=True)
class RehabBoxingTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
    setUp=test_game.GameTests.setUp
    tearDown=test_game.GameTests.tearDown
    load=test_game.GameTests.load

    def gym(self):
        self.page.locator('#location-card-box').click()
        self.page.locator('.quest-map-pin[data-room="gym"]').dblclick(delay=40)
        self.page.wait_for_function('document.querySelector("[data-scene-room=gym]")?.dataset.rehabRenderer==="webgl"')
        self.page.locator('[data-rehab-equipment=bag]').click()
        self.page.locator('.rehab-boxing').wait_for(state='visible')
        self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingReady==="true"')
        self.page.wait_for_timeout(650)

    def hit(self,hand,count):
        self.page.locator('.boxing-stage').click(position={'x':300,'y':250})
        self.assertEqual(self.page.locator('.rehab-boxing').get_attribute('data-boxing-hand'),hand)
        self.page.wait_for_function('n=>Number(document.querySelector(".rehab-boxing").dataset.boxingHits)===n',arg=count)
        self.assertEqual(self.page.locator('.rehab-boxing').get_attribute('data-boxing-impact'),hand)

    def test_both_modes_alternation_contact_direction_and_no_free_rewards(self):
        self.load();rows=[]
        for mode in ['patient','trip']:
            if mode=='trip':
                self.page.locator('.quest-room-tools button').first.click();self.page.locator('#map-modal .btn-close-map').click();self.page.locator('.room-trip-switch').click()
            self.gym();dialog=self.page.locator('.rehab-boxing')
            before=self.page.evaluate('JSON.stringify({stats,inventory})')
            self.assertEqual(dialog.get_attribute('data-mode'),mode)
            self.assertEqual(self.page.locator('[data-boxing-target]').evaluate('e=>getComputedStyle(e).outlineStyle'),'none')
            self.page.screenshot(path=str(OUT/(mode+'-ready.png')))
            self.hit('right',1)
            self.page.wait_for_function('Number(document.querySelector(".rehab-boxing").dataset.boxingAngle)>.02')
            self.page.screenshot(path=str(OUT/(mode+'-right-contact.png')))
            self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingPhase==="ready"')
            self.hit('left',2)
            self.page.wait_for_function('Number(document.querySelector(".rehab-boxing").dataset.boxingAngle)<-.02')
            self.page.screenshot(path=str(OUT/(mode+'-left-contact.png')))
            self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingPhase==="ready"')
            self.page.locator('.boxing-stage').click(position={'x':300,'y':250},click_count=3,delay=10)
            self.page.wait_for_timeout(550)
            self.assertEqual(dialog.get_attribute('data-boxing-hits'),'3')
            self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory})'),before)
            self.page.keyboard.press('Escape');self.assertEqual(self.page.locator('.rehab-boxing').count(),0)
            rows.append({'mode':mode,'order':['right','left','right'],'rightMovesLeft':True,'leftMovesRight':True,'spamIgnored':True,'practicePreservesStats':True})
        (OUT/'click-results.json').write_text(json.dumps(rows,indent=2))

    def test_training_completion_and_cancel_preserve_accounting(self):
        self.load();self.page.evaluate('stats.energy=100;stats.maxEnergy=100;saveGameProgress()');self.gym()
        self.page.locator('[data-boxing-start]').click();self.assertTrue(self.page.locator('[data-boxing-start]').is_disabled())
        self.hit('right',1);self.page.wait_for_timeout(550);self.hit('left',2)
        self.page.wait_for_function('stats.rehabTraining?.bag?.completed===1',timeout=15000)
        self.assertEqual(self.page.evaluate('stats.energy'),92)
        self.page.locator('[data-boxing-back]').click();self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('stats.rehabTraining.bag.completed'),1)
        self.assertEqual(self.page.evaluate('stats.energy'),92)
        self.page.evaluate('stats.rehabTraining.bag.lastCompletedAt=0;stats.rehabTraining.rope.lastCompletedAt=0')
        self.page.locator('[data-rehab-equipment=bag]').click();self.page.locator('[data-boxing-start]').click();self.assertTrue(self.page.locator('[data-boxing-start]').is_disabled());self.page.wait_for_timeout(500);self.page.keyboard.press('Escape');self.page.wait_for_timeout(500)
        self.assertEqual(self.page.evaluate('stats.rehabTraining.bag.completed'),1)
        self.assertEqual(self.page.evaluate('stats.energy'),92)

    def test_phone_reduced_motion_and_closing_mid_punch(self):
        self.load();self.gym();self.page.set_viewport_size({'width':390,'height':844});self.page.wait_for_timeout(250)
        box=self.page.locator('[data-boxing-target]').bounding_box()
        self.assertGreaterEqual(box['y'],0);self.assertLessEqual(box['y']+box['height'],844)
        self.page.screenshot(path=str(OUT/'patient-phone.png'))
        self.page.emulate_media(reduced_motion='reduce')
        self.page.locator('[data-boxing-target]').press('Enter')
        self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingHits==="1"')
        self.assertEqual(self.page.locator('.boxing-fist.right').evaluate('e=>getComputedStyle(e).transform'),'none')
        self.assertEqual(self.page.locator('[data-boxing-target]').evaluate('e=>getComputedStyle(e).transform'),'none')
        self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingPhase==="ready"')
        self.page.emulate_media(reduced_motion='no-preference');self.page.locator('[data-boxing-target]').press('Enter');self.page.keyboard.press('Escape')
        self.page.wait_for_timeout(600);self.assertEqual(self.page.locator('.rehab-boxing').count(),0)
        self.page.wait_for_function('Number(document.querySelector("[data-scene-room=gym]").dataset.rehabFrames)>2')

    def test_missing_layer_blocks_punches_and_training_without_spending(self):
        self.load();self.page.route('**/assets/rehabilitation/boxing-fists-painted.png',lambda route:route.abort());self.gym_without_ready()
        self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingReady==="error"')
        before=self.page.evaluate('JSON.stringify(stats)')
        self.assertTrue(self.page.locator('[data-boxing-start]').is_disabled())
        self.assertTrue(self.page.locator('[data-boxing-target]').is_disabled())
        self.page.locator('.boxing-stage').click(position={'x':300,'y':250});self.page.wait_for_timeout(300)
        self.assertIsNone(self.page.locator('.rehab-boxing').get_attribute('data-boxing-hits'))
        self.assertEqual(self.page.evaluate('JSON.stringify(stats)'),before)
        self.page.locator('[data-boxing-back]').click()

    def gym_without_ready(self):
        self.page.locator('#location-card-box').click();self.page.locator('.quest-map-pin[data-room="gym"]').dblclick(delay=40)
        self.page.wait_for_function('document.querySelector("[data-scene-room=gym]")?.dataset.rehabRenderer==="webgl"')
        self.page.locator('[data-rehab-equipment=bag]').click()

    def test_breath_windup_contact_and_one_second_rest_after_pair(self):
        self.load();self.gym();dialog=self.page.locator('.rehab-boxing')
        before=self.page.locator('.boxing-fist.right').bounding_box()
        self.page.wait_for_timeout(250)
        after=self.page.locator('.boxing-fist.right').bounding_box()
        self.assertGreater(abs(before['x']-after['x'])+abs(before['y']-after['y']),.1)
        self.page.locator('.boxing-stage').click(position={'x':300,'y':250})
        self.assertEqual(dialog.get_attribute('data-boxing-phase'),'windup')
        self.page.wait_for_timeout(85)
        back=self.page.locator('.boxing-fist.right').bounding_box()
        self.assertGreater(back['x'],after['x']+10)
        self.assertGreater(back['y'],after['y']+10)
        self.page.screenshot(path=str(OUT/'painted-windup.png'))
        self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingHits==="1"')
        self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingPhase==="ready"')
        self.hit('left',2)
        self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingPhase==="cooldown"')
        self.page.locator('.boxing-stage').click(position={'x':300,'y':250})
        self.page.wait_for_timeout(200)
        self.assertEqual(dialog.get_attribute('data-boxing-hits'),'2')
        self.page.wait_for_function('document.querySelector(".rehab-boxing").dataset.boxingPhase==="ready"')
        elapsed=self.page.evaluate('performance.now()-Number(document.querySelector(".rehab-boxing").dataset.boxingRestStarted)')
        self.assertGreaterEqual(elapsed,1000)
        self.page.wait_for_timeout(250)
        self.assertEqual(dialog.get_attribute('data-boxing-hits'),'2')
        self.hit('right',3)
        self.page.keyboard.press('Escape')

    def test_painted_arm_edges_stay_outside_frame_and_contact_effect_is_visible(self):
        self.load();self.gym()
        for width,height in [(1280,800),(390,844)]:
            self.page.set_viewport_size({'width':width,'height':height});self.page.wait_for_timeout(300)
            result=self.page.evaluate('''async()=>{
   const img=new Image();img.src='assets/rehabilitation/boxing-fists-painted.png';await img.decode();const c=document.createElement('canvas');c.width=img.width;c.height=img.height;const ctx=c.getContext('2d');ctx.drawImage(img,0,0);const a=ctx.getImageData(0,0,c.width,c.height).data,points=[];
   const add=(x,y)=>{if(a[(y*c.width+x)*4+3]>200)points.push([x,y])};
   for(let x=0;x<c.width;x+=4)add(x,c.height-1);for(let y=0;y<c.height;y+=4){add(0,y);add(c.width-1,y)}
   const stage=document.querySelector('.boxing-stage'),left=document.querySelector('.boxing-fist.left'),right=document.querySelector('.boxing-fist.right');let bad=[],effectSeen=false,frames=0;const start=performance.now();stage.click();
   await new Promise(resolve=>{function sample(now){frames++;const r=stage.getBoundingClientRect(),lm=left.getScreenCTM(),rm=right.getScreenCTM();
    for(const [x,y] of points){const p=new DOMPoint(x,y).matrixTransform(x<c.width/2?lm:rm);if(p.x>r.left+2&&p.x<r.right-2&&p.y>r.top+2&&p.y<r.bottom-2&&bad.length<5)bad.push({x:p.x,y:p.y,t:now-start,source:[x,y]});}
    if(Number(getComputedStyle(document.querySelector('.boxing-impact')).opacity)>.1)effectSeen=true;
    if(now-start<750)requestAnimationFrame(sample);else resolve();}requestAnimationFrame(sample)});return{frames,effectSeen,bad};
  }''')
            self.assertGreater(result['frames'],5)
            self.assertTrue(result['effectSeen'])
            self.assertEqual(result['bad'],[],str((width,height)))
