"""The wet-foot visitor shakes only the original handle, within the footprint hold."""
import unittest
from tests import test_game
from tests import test_room_scene as room_support


class DoorRattleTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
    setUp=room_support.RoomSceneTests.setUp
    tearDown=room_support.RoomSceneTests.tearDown
    freeze=room_support.RoomSceneTests.freeze
    seek=room_support.RoomSceneTests.seek

    def at(self,time):
        self.seek('room-wet-step',time)
        self.page.evaluate('PalataDoorRattle.sync()')

    def test_irregular_pulls_start_at_arrival_stop_at_first_fade_and_never_open_leaf(self):
        self.freeze();self.at(9000)
        self.assertFalse(self.page.evaluate('PalataDoorRattle.active'))
        samples=self.page.evaluate('''()=>{
            const feet=[...document.querySelectorAll('.room-floor-print')],door=document.querySelector('.room-door-assembly'),handle=door.querySelector('.room-door-handle'),leaf=door.querySelector('.room-door-leaf');
            const result=[];for(let time=9580;time<13200;time+=65){for(const foot of feet)foot.getAnimations().find(a=>a.animationName==='room-wet-step').currentTime=time;PalataDoorRattle.sync();const m=new DOMMatrix(getComputedStyle(handle).transform);result.push({angle:Math.atan2(m.b,m.a)*180/Math.PI,leaf:new DOMMatrix(getComputedStyle(leaf).transform).m11,state:door.dataset.state,revealed:door.classList.contains('is-revealed')})}return result;
        }''')
        self.assertGreater(max(s['angle'] for s in samples),10)
        self.assertGreater(len({round(s['angle'],1) for s in samples}),12)
        self.assertTrue(all(s['state']=='closed' and not s['revealed'] and abs(s['leaf']-1)<.0001 for s in samples))
        self.assertTrue(self.page.locator('#map-modal').is_hidden())
        self.at(13200)
        self.assertFalse(self.page.evaluate('PalataDoorRattle.active'))
        self.assertAlmostEqual(self.page.locator('.room-door-handle').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).b'),0,delta=.001)
        self.at(11000)
        first=self.page.locator('.room-door-handle').evaluate('e=>e.getAnimations().find(a=>!a.animationName).effect.getKeyframes()')
        self.at(59000)
        second=self.page.locator('.room-door-handle').evaluate('e=>e.getAnimations().find(a=>!a.animationName).effect.getKeyframes()')
        self.assertNotEqual(first,second)

    def test_pause_reduced_motion_and_manual_door_action_take_precedence(self):
        self.freeze();self.at(11200)
        before=self.page.locator('.room-door-handle').evaluate('e=>getComputedStyle(e).transform')
        self.page.evaluate('openTasks()');self.page.wait_for_timeout(200)
        self.assertEqual(self.page.locator('.room-door-handle').evaluate('e=>getComputedStyle(e).transform'),before)
        self.page.keyboard.press('Escape');self.at(11200)
        self.page.locator('.room-door-action').hover()
        self.assertFalse(self.page.evaluate('PalataDoorRattle.active'))
        self.page.locator('.room-door-action').click()
        self.page.locator('#map-modal').wait_for(state='visible')
        self.assertFalse(self.page.evaluate('PalataDoorRattle.active'))
        self.page.keyboard.press('Escape');self.page.mouse.move(700,730);self.page.locator('.room-door-action').evaluate('e=>e.blur()')
        self.page.wait_for_function('document.querySelector(".room-door-assembly").dataset.state==="closed"')
        self.at(11200);self.page.emulate_media(reduced_motion='reduce')
        self.page.wait_for_function('!PalataDoorRattle.active')
        self.assertFalse(self.page.evaluate('PalataDoorRattle.active'))
        self.assertEqual(self.page.locator('.room-door-assembly').get_attribute('data-state'),'closed')


if __name__=='__main__':
    unittest.main()
