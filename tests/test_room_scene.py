"""Room interactions use the real save, avatar renderer and existing dialogs."""
import io
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from tests import test_game


class RoomSceneTests(unittest.TestCase):
    setUpClass = classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass = classmethod(test_game.GameTests.tearDownClass.__func__)

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1672, 'height': 941})
        self.context.add_init_script('window.__PALATA_TEST_DIRECT__=true;')
        self.context.route('https://**/*', lambda route: route.abort())
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(self.url, wait_until='networkidle')
        self.page.evaluate('document.fonts.ready')
        self.page.evaluate('document.getElementById("character-paperdoll").paperDollReady')
        self.page.wait_for_function('Number(document.querySelector(".room-shadow-contact").dataset.soleSamples)>40')

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def freeze(self):
        self.page.evaluate('document.getAnimations().filter(a=>a.animationName).forEach(a=>{a.pause();a.currentTime=0})')

    def seek(self, name, time):
        self.page.evaluate('([name,time])=>{for(const a of document.getAnimations())if(a.animationName===name){a.pause();a.currentTime=time}}', [name, time])
        self.page.wait_for_timeout(80)

    @staticmethod
    def rgb(data, rect):
        return ImageStat.Stat(Image.open(io.BytesIO(data)).convert('RGB').crop(rect)).mean

    @staticmethod
    def pixels(image):
        raw = iter(image.tobytes())
        return zip(raw, raw, raw)

    def test_soft_rare_flicker_keeps_the_bulb_lit_and_night_outside(self):
        self.freeze()
        bright = self.page.screenshot()
        avatar = self.page.locator('.room-shadow-cast canvas').evaluate('e=>e.toDataURL()')
        values = self.page.locator('.hospital-hud').evaluate('''e=>{
            const a=e.getAnimations().find(a=>a.animationName==='room-light-supply');
            const values=[];for(let t=0;t<61000;t+=100){a.currentTime=t;values.push(Number(getComputedStyle(e).getPropertyValue('--room-light')))}
            a.currentTime=0;return values;
        }''')
        self.assertGreaterEqual(min(values), .59)
        self.assertLessEqual(min(values), .63)
        self.assertLess(sum(v < .999 for v in values)/len(values), .12)
        self.seek('room-light-supply', 3904)
        dim = self.page.screenshot()
        for rect in [(897,291,941,335), (1071,178,1100,220), (828,105,848,119)]:
            ratio = sum(self.rgb(dim, rect))/sum(self.rgb(bright, rect))
            self.assertGreater(ratio, .63)
            self.assertLess(ratio, .95)
        bulb = self.rgb(dim, (828,105,848,119))
        self.assertGreater(bulb[0]-bulb[2], 18)  # Warm emitter, no gray semicircle.
        self.assertGreater(sum(bulb)/3, 110)
        self.assertEqual(self.page.locator('.room-shadow-cast canvas').evaluate('e=>e.toDataURL()'), avatar)
        self.seek('room-light-supply', 0)
        self.seek('room-night-cycle', 0)
        dusk = sum(self.rgb(self.page.screenshot(), (709,238,737,260)))/3
        self.seek('room-night-cycle', 36000)
        outside = self.rgb(self.page.screenshot(), (709,238,737,260))
        self.assertLess(sum(outside)/3, dusk*.55)
        self.assertGreater(sum(outside)/3, 30)
        self.assertLess(max(outside)-min(outside), 28)
        self.seek('room-night-cycle', 72000)
        returned = sum(self.rgb(self.page.screenshot(), (709,238,737,260)))/3
        self.assertAlmostEqual(returned, dusk, delta=3)
        light = self.page.locator('.room-distant-left-low')
        self.seek('room-distant-switch', 0)
        before = float(light.evaluate('e=>getComputedStyle(e).opacity'))
        self.seek('room-distant-switch', 26000)
        self.assertGreater(abs(float(light.evaluate('e=>getComputedStyle(e).opacity'))-before), .5)

    def test_trip_button_plate_and_surrounding_wall_follow_room_exposure(self):
        self.freeze()
        self.page.mouse.move(700,730)
        self.page.evaluate('document.activeElement.blur()')
        self.page.wait_for_timeout(220)
        bright=self.page.screenshot()
        self.seek('room-light-supply',3904)
        dim=self.page.screenshot()
        regions={
            'plate corner':(1040,462,1045,468),
            'old lower wall patch':(1033,493,1075,499),
            'old left wall patch':(1031,461,1036,487),
            'neighboring wall':(1080,493,1090,499),
        }
        ratios={name:sum(self.rgb(dim,rect))/sum(self.rgb(bright,rect)) for name,rect in regions.items()}
        for name,ratio in ratios.items():
            with self.subTest(region=name):
                self.assertGreater(ratio,.68)
                self.assertLess(ratio,.90,'The button image or its wall patch stayed bright above the room lighting')
        self.assertLess(max(ratios.values())-min(ratios.values()),.12)
        self.seek('room-light-supply',0)
        self.page.locator('.room-trip-switch').hover()
        self.page.wait_for_timeout(250)
        hover=self.page.screenshot()
        self.assertGreater(sum(self.rgb(hover,(1047,468,1060,482)))/3-sum(self.rgb(bright,(1047,468,1060,482)))/3,5)
        for rect in [(1033,493,1075,499),(1031,461,1036,487)]:
            self.assertAlmostEqual(sum(self.rgb(hover,rect))/3,sum(self.rgb(bright,rect))/3,delta=2)

    def test_contact_shadow_supports_heel_and_toes_for_both_avatars(self):
        self.freeze()
        out = Path('test-results/hospital-room'); out.mkdir(parents=True, exist_ok=True)
        hashes = []
        for gender in ['male', 'female']:
            self.page.evaluate('g=>{setGender(g);updateUI();PalataRoomShadows.refresh()}', gender)
            self.page.evaluate('document.getElementById("character-paperdoll").paperDollReady')
            self.page.wait_for_timeout(250)
            contact = self.page.locator('.room-shadow-contact')
            self.assertGreater(int(contact.get_attribute('data-sole-samples')), 40)
            self.assertGreater(int(contact.get_attribute('data-sole-depth')), 8)
            self.assertEqual(contact.locator('canvas').evaluate('e=>getComputedStyle(e).transform'), 'none')
            self.assertIn('matrix3d', self.page.locator('.room-shadow-cast canvas').evaluate('e=>getComputedStyle(e).transform'))
            hashes.append(contact.locator('canvas').evaluate('e=>e.toDataURL()'))
            self.page.screenshot(path=str(out/f'{gender}.png'))
        self.assertNotEqual(*hashes)

    def test_distant_lights_leave_the_unlit_glass_and_grid_visible(self):
        self.freeze()
        # Expose both distant windows and isolate their light from foreground effects.
        self.page.add_style_tag(content='.hud-character-stage,.room-glass-mark{display:none!important}')
        lights = self.page.locator('.room-distant-light')
        lights.evaluate_all('es=>es.forEach(e=>{e.style.animation="none";e.style.opacity="0"})')
        for phase in [0, 36000]:
            self.seek('room-night-cycle', phase)
            for selector, source in [('.room-distant-left-low','window-left-unlit.webp'),('.room-distant-right-high','window-right-unlit.webp')]:
                with self.subTest(phase=phase, window=source):
                    light = self.page.locator(selector)
                    light.evaluate('e=>e.style.opacity="0"')
                    lit = Image.open(io.BytesIO(light.screenshot())).convert('RGB')
                    light.evaluate('e=>e.style.opacity="1"')
                    unlit = Image.open(io.BytesIO(light.screenshot())).convert('RGB')
                    original = Image.open(test_game.ROOT/'hud-art'/source).convert('RGB').resize(lit.size)
                    # Select cold foreground/grid pixels away from the orange emission.
                    delta = ImageChops.difference(lit, unlit)
                    cold = [sum(v)/3 for v,(r,g,b) in zip(self.pixels(delta),self.pixels(original)) if r-b < 24]
                    self.assertGreater(len(cold), 20)
                    self.assertLess(sum(cold)/len(cold), 3)
                    warm = [sum(v)/3 for v,(r,g,b) in zip(self.pixels(delta),self.pixels(original)) if r-b > 70]
                    self.assertGreater(len(warm), 15)
                    self.assertGreater(sum(warm)/len(warm), 4 if phase else 10)
                    # Extinguished glazing retains texture instead of becoming black.
                    self.assertGreater(sum(ImageStat.Stat(unlit).mean)/3, 20 if phase else 55)
                    light.evaluate('e=>e.style.opacity="0"')

    def test_fabric_cast_shadows_move_with_the_opaque_approved_cutouts(self):
        self.freeze()
        self.page.add_style_tag(content='.room-glass-mark{display:none!important}')
        fabrics = [('curtain',5400,(60,160)),('robe',21600,(75,206)),('bag',37260,(125,100))]
        for name, time, sample in fabrics:
            with self.subTest(fabric=name):
                selector = '.room-moving-'+name
                cloth = self.page.locator(selector)
                styles = cloth.evaluate('''e=>{const front=getComputedStyle(e,'::after'),shadow=getComputedStyle(e,'::before');return {front:front.backgroundImage,shadow:shadow.backgroundImage,frontOpacity:Number(front.opacity),shadowOpacity:Number(shadow.opacity),shadowFilter:shadow.filter,frontAnimation:front.animationName,shadowAnimation:shadow.animationName}}''')
                self.assertEqual(styles['front'], styles['shadow'])
                self.assertIn('room-'+name+'.svg', styles['front'])
                self.assertEqual(styles['frontOpacity'], 1)
                self.assertGreater(styles['shadowOpacity'], .1)
                self.assertIn('brightness(0)', styles['shadowFilter'])
                self.assertIn('blur(', styles['shadowFilter'])
                self.assertEqual((styles['frontAnimation'],styles['shadowAnimation']),('none','none'))
                self.seek('room-light-supply',3904)
                dim_opacity = float(cloth.evaluate('e=>getComputedStyle(e,"::before").opacity'))
                self.assertLess(dim_opacity, styles['shadowOpacity'])
                self.seek('room-light-supply',0)
                alpha = self.page.evaluate(r'''async ([name,x,y])=>{const im=new Image();im.src='hud-art/room-'+name+'.svg';await im.decode();const source=await (await fetch(im.src)).text();const svg=new DOMParser().parseFromString(source,'image/svg+xml').documentElement;const bounds=svg.getAttribute('viewBox').trim().split(/\s+/).map(Number);const c=document.createElement('canvas');c.width=bounds[2];c.height=bounds[3];const ctx=c.getContext('2d');ctx.drawImage(im,0,0,c.width,c.height);return [ctx.getImageData(x,y,1,1).data[3],ctx.getImageData(0,y,1,1).data[3]]}''',[name,*sample])
                self.assertEqual(alpha, [255,0])

                # Render only one cast shadow over the fixed wall: its pixels must move.
                rule = self.page.add_style_tag(content='.room-moving-curtain::after,.room-moving-robe::after,.room-moving-bag::after,.room-moving-curtain::before,.room-moving-robe::before,.room-moving-bag::before{opacity:0!important}'+selector+'::before{opacity:.4!important}')
                self.seek('room-'+name+'-draft',0)
                box=cloth.bounding_box(); rect=(max(0,int(box['x'])-20),max(0,int(box['y'])-20),min(1672,int(box['x']+box['width'])+20),min(941,int(box['y']+box['height'])+20))
                still=Image.open(io.BytesIO(self.page.screenshot())).convert('RGB').crop(rect)
                self.seek('room-'+name+'-draft',time)
                moved=Image.open(io.BytesIO(self.page.screenshot())).convert('RGB').crop(rect)
                changed=sum(1 for r,g,b in self.pixels(ImageChops.difference(still,moved)) if max(r,g,b)>3)
                self.assertGreater(changed, 30)
                rule.evaluate('e=>e.remove()')
                self.seek('room-'+name+'-draft',0)

    def test_cloths_take_turns_and_keep_quiet_gaps_between_them(self):
        self.freeze()
        phases = self.page.evaluate('''()=>{
            const names=['curtain','robe','bag'];
            const cloths=names.map(name=>document.querySelector('.room-moving-'+name));
            const animations=cloths.map((e,n)=>e.getAnimations().find(a=>a.animationName==='room-'+names[n]+'-draft'));
            return Array.from({length:217},(_,i)=>{
                const time=i*250;animations.forEach(a=>{a.pause();a.currentTime=time});
                const displacement=cloths.map(e=>{const s=getComputedStyle(e),m=new DOMMatrix(s.transform);const h=parseFloat(s.height);return Math.hypot(m.c*h,(m.d-1)*h)});
                return {time,active:names.filter((_,n)=>displacement[n]>.1),displacement};
            });
        }''')
        self.assertTrue(all(len(p['active']) <= 1 for p in phases), 'Fabric movements overlap')
        order=[]
        for phase in phases:
            if phase['active'] and (not order or order[-1] != phase['active'][0]):
                order.append(phase['active'][0])
        self.assertEqual(order, ['curtain','robe','bag'])
        for index in range(3):
            self.assertGreater(max(p['displacement'][index] for p in phases), 3)
        intervals=[]
        for name in order:
            times=[p['time'] for p in phases if p['active']==[name]]
            intervals.append((min(times),max(times)))
        self.assertGreater(intervals[1][0]-intervals[0][1], 3000)
        self.assertGreater(intervals[2][0]-intervals[1][1], 3000)

    def test_corridor_flickers_independently_and_stays_lit_and_sharp(self):
        self.freeze()
        self.page.add_style_tag(content='.room-door-leaf{display:none!important}')
        corridor = self.page.locator('.room-corridor-scene')
        cycle = corridor.evaluate('''e=>{
            const a=e.getAnimations().find(a=>a.animationName==='room-corridor-supply');
            const values=[];let lowest={time:0,value:1};
            for(let t=0;t<47000;t+=50){a.currentTime=t;const value=Number(getComputedStyle(e).getPropertyValue('--corridor-light'));values.push(value);if(value<lowest.value)lowest={time:t,value};}
            a.currentTime=0;return {values,lowest};
        }''')
        self.assertGreaterEqual(min(cycle['values']), .60)
        self.assertLessEqual(min(cycle['values']), .75)
        self.assertLess(sum(v < .999 for v in cycle['values'])/len(cycle['values']), .18)
        bright = self.page.screenshot()
        self.seek('room-corridor-supply',cycle['lowest']['time'])
        dim = self.page.screenshot()
        # The corridor walls dim while the room itself is held at full supply.
        ratio=sum(self.rgb(dim,(1150,440,1180,475)))/sum(self.rgb(bright,(1150,440,1180,475)))
        self.assertGreater(ratio,.55)
        self.assertLess(ratio,.85)
        self.assertGreater(sum(self.rgb(dim,(1150,440,1180,475)))/3,10)
        lit_pixels=list(self.pixels(Image.open(io.BytesIO(bright)).convert('RGB').crop((1110,278,1307,712))))
        dim_pixels=list(self.pixels(Image.open(io.BytesIO(dim)).convert('RGB').crop((1110,278,1307,712))))
        emitter=[sum(after)/3 for before,after in zip(lit_pixels,dim_pixels) if sum(before)/3>130]
        self.assertGreater(len(emitter),10)
        self.assertGreater(sum(emitter)/len(emitter),65)
        self.assertAlmostEqual(sum(self.rgb(dim,(1071,178,1100,220))),sum(self.rgb(bright,(1071,178,1100,220))),delta=2)
        self.assertNotIn('blur(',corridor.evaluate('e=>getComputedStyle(e).filter'))
        self.page.emulate_media(reduced_motion='reduce')
        self.assertAlmostEqual(float(corridor.evaluate('e=>getComputedStyle(e).getPropertyValue("--corridor-light")')),1)

    def test_circle_hover_and_all_task_links_use_the_same_read_only_dialog(self):
        self.freeze()
        switch = self.page.locator('.room-trip-switch')
        art = self.page.locator('.room-switch-art')
        plate_filter = art.evaluate('e=>getComputedStyle(e).filter')
        switch.hover(); self.page.wait_for_timeout(240)
        self.assertEqual(art.evaluate('e=>getComputedStyle(e).filter'), plate_filter)
        self.assertGreater(float(art.evaluate('e=>getComputedStyle(e,"::after").opacity')), .95)
        state = self.page.evaluate('JSON.stringify({stats,inventory,paperDollState})')
        action = self.page.locator('.room-tasks-action')
        action.hover(); self.page.wait_for_timeout(360)
        self.assertGreater(float(self.page.locator('.room-task-corner').evaluate('e=>getComputedStyle(e).opacity')), .95)
        for entry in [action, self.page.locator('.hud-task')]:
            entry.click()
            self.assertTrue(self.page.locator('#tasks-modal').is_visible())
            self.assertIn('Задания в разработке', self.page.locator('#tasks-modal').inner_text())
            self.page.keyboard.press('Escape')
            self.assertTrue(self.page.locator('#tasks-modal').is_hidden())
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,paperDollState})'), state)

    def test_door_closes_once_and_cabinet_reveals_the_real_wardrobe_after_both_leaves(self):
        for action, assembly, modal, close in [('.room-door-action','.room-door-assembly','#map-modal','toggleMapModal(false)'), ('.room-cabinet-action','.room-cabinet-assembly','#custom-modal','closeCustomization()')]:
            before = self.page.evaluate('JSON.stringify({inventory,paperDollState})')
            self.page.locator(action).click(); self.page.wait_for_timeout(100)
            self.assertTrue(self.page.locator(modal).is_hidden())
            if modal == '#custom-modal':
                self.assertEqual(self.page.locator('.room-cabinet-door-back').count(), 2)
                self.assertEqual(self.page.locator('.room-handle-grip').count(), 0)
                self.assertIn('original-handle-left.svg', self.page.locator('.room-cabinet-handle .room-handle-face').first.get_attribute('src'))
                self.assertIn('cabinet-inner-right.webp', self.page.locator('.room-cabinet-leaf-left .room-cabinet-door-back').evaluate('e=>getComputedStyle(e).backgroundImage'))
                self.assertEqual(self.page.locator('.room-cabinet-metal-return').count(), 8)
                self.assertEqual(self.page.locator('.room-cabinet-leaf-right').evaluate('e=>getComputedStyle(e,"::after").content'), 'none')
                self.assertGreater(self.page.locator('.room-handle-face').first.evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).m43'), 0)
                self.assertNotEqual(self.page.locator('.room-cabinet-leaf-left').evaluate('e=>getComputedStyle(e).transform'), 'none')
                self.assertFalse(self.page.evaluate('PalataRoom.openDoor()'))
            self.page.locator(modal).wait_for(state='visible')
            if modal == '#custom-modal':
                self.assertTrue(self.page.evaluate('Boolean(wardrobeSession)'))
                # Both doors pass 90 degrees, showing their inner metal surface.
                self.assertLess(self.page.locator('.room-cabinet-leaf-left').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).m11'), 0)
                self.assertLess(self.page.locator('.room-cabinet-leaf-right').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).m11'), 0)
            self.page.evaluate(close); self.page.wait_for_timeout(160)
            self.assertEqual(self.page.locator(assembly).get_attribute('data-state'), 'closing')
            self.assertTrue(self.page.locator(assembly).evaluate('e=>e.classList.contains("is-revealed")'))
            self.page.wait_for_function('s=>document.querySelector(s).dataset.state==="closed"', arg=assembly)
            self.assertFalse(self.page.locator(assembly).evaluate('e=>e.classList.contains("is-revealed")'))
            self.assertEqual(self.page.evaluate('JSON.stringify({inventory,paperDollState})'), before)

    def test_cabinet_hover_closes_without_a_late_dark_slit_or_flash(self):
        self.freeze()
        cabinet=self.page.locator('.room-cabinet-assembly')
        action=self.page.locator('.room-cabinet-action')
        portal=self.page.locator('.room-cabinet-portal')
        action.hover();self.page.wait_for_timeout(800)
        self.assertGreater(float(portal.evaluate('e=>getComputedStyle(e).opacity')),.99)
        self.page.mouse.move(700,730)
        # Seat both leaves while the delayed hover cleanup is still pending.
        # Finishing the browser transitions avoids racing a wall-clock timeout
        # on slower CI machines without skipping the actual closing styles.
        self.page.wait_for_timeout(100)
        self.page.evaluate('''()=>document.querySelectorAll('.room-cabinet-leaf').forEach(e=>{
            e.getAnimations().filter(a=>a.transitionProperty==='transform').forEach(a=>a.finish());
        })''')
        self.page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
        self.assertTrue(cabinet.evaluate('e=>e.classList.contains("is-revealed")'))
        self.assertLess(float(portal.evaluate('e=>getComputedStyle(e).opacity')),.001,
                        'The interior must already be gone when both doors meet, before the fallback timer runs')
        before=self.page.screenshot()
        self.page.wait_for_function('!document.querySelector(".room-cabinet-assembly").classList.contains("is-revealed")')
        after=self.page.screenshot()
        a=Image.open(io.BytesIO(before)).convert('RGB').crop((1350,260,1510,750))
        b=Image.open(io.BytesIO(after)).convert('RGB').crop((1350,260,1510,750))
        self.assertLessEqual(sum(max(abs(x-y) for x,y in zip(p,q))>6
                                 for p,q in zip(self.pixels(a),self.pixels(b))),50,
                             'Settling the hover state must not change the closed cabinet image')
        # Reverse an incomplete close, then leave again: exposure still follows
        # the rendered doors rather than the abandoned hover timeout.
        action.hover();self.page.wait_for_timeout(300)
        self.page.mouse.move(700,730);self.page.wait_for_timeout(180)
        action.hover();self.page.wait_for_timeout(200)
        self.assertGreater(float(portal.evaluate('e=>getComputedStyle(e).opacity')),.5)
        self.page.mouse.move(700,730);self.page.wait_for_timeout(1400)
        self.assertLess(float(portal.evaluate('e=>getComputedStyle(e).opacity')),.001)
        self.assertFalse(cabinet.evaluate('e=>e.classList.contains("is-revealed")'))

    def test_hover_opens_a_small_gap_and_presses_only_the_door_lever(self):
        self.freeze()
        for action, assembly, modal in [('.room-door-action','.room-door-assembly','#map-modal'),('.room-cabinet-action','.room-cabinet-assembly','#custom-modal')]:
            self.page.locator(action).hover(); self.page.wait_for_timeout(720)
            self.assertEqual(self.page.locator(assembly).get_attribute('data-state'), 'closed')
            self.assertTrue(self.page.locator(assembly).evaluate('e=>e.classList.contains("is-peeking")'))
            self.assertTrue(self.page.locator(modal).is_hidden())
            self.page.mouse.move(700,730); self.page.wait_for_timeout(1350)
            self.assertFalse(self.page.locator(assembly).evaluate('e=>e.classList.contains("is-revealed")'))
        self.page.locator('.room-door-action').hover(); self.page.wait_for_timeout(720)
        self.assertGreater(self.page.locator('.room-door-handle').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).b'), .1)
        self.page.locator('.room-door-action').click();self.page.locator('#map-modal').wait_for(state='visible')
        self.assertTrue(self.page.locator('.room-door-assembly').evaluate('e=>e.classList.contains("is-handle-pressed")'))
        self.page.evaluate('toggleMapModal(false)')
        self.page.mouse.move(700,730)
        self.page.locator('.room-door-action').evaluate('e=>e.blur()')
        self.page.wait_for_function('document.querySelector(".room-door-assembly").dataset.state==="closed"')
        self.page.wait_for_function('Math.abs(new DOMMatrix(getComputedStyle(document.querySelector(".room-door-handle")).transform).b)<.001')
        self.assertAlmostEqual(self.page.locator('.room-door-handle').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).b'),0,delta=.001)
        corridor = self.page.locator('.room-corridor-scene')
        self.assertIn('room-corridor.webp', corridor.evaluate('e=>getComputedStyle(e).backgroundImage'))
        self.assertNotIn('blur(', corridor.evaluate('e=>getComputedStyle(e).filter'))
        self.assertEqual(self.page.locator('.room-corridor-sight').count(), 0)
        self.assertGreater(float(self.page.locator('.room-door-portal').evaluate('e=>getComputedStyle(e).opacity')), .99)
        alpha = self.page.locator('.room-door-leaf>img').evaluate('''async e=>{
            await e.decode();const c=document.createElement('canvas');c.width=197;c.height=434;
            const ctx=c.getContext('2d');ctx.drawImage(e,0,0,197,434);
            return {glass:ctx.getImageData(98,92,1,1).data[3],paint:ctx.getImageData(90,150,1,1).data[3]};
        }''')
        self.assertLess(alpha['glass'], 5)  # A real aperture shows the fixed world behind it.
        self.assertGreater(alpha['paint'], 250)

    def test_contacts_visit_all_glass_and_steps_appear_in_order(self):
        self.freeze()
        for surface,count in [(0,12),(1,12),(2,6)]:
            positions=self.page.evaluate('([surface,count])=>Array.from({length:count},()=>PalataAtmosphere.showContact(surface).slot)',[surface,count])
            self.assertEqual(len(set(positions)),count)
        self.assertEqual(self.page.locator('.room-window-left .room-glass-mark').count(),12)
        self.assertEqual(self.page.locator('.room-window-right .room-glass-mark').count(),12)
        self.assertEqual(self.page.locator('.room-door-glass .room-glass-mark').count(),4)
        self.assertEqual(self.page.locator('.room-door-glass .is-hand').count(),3)
        self.assertEqual(self.page.locator('.room-door-glass .is-help').count(),1)
        self.seek('room-wet-step',8500)
        steps=self.page.locator('.room-floor-print')
        walking = steps.evaluate_all('''es=>es.map(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e),m=new DOMMatrix(s.transform);return {foot:e.dataset.foot,src:e.getAttribute('src'),x:r.x+r.width/2,y:r.y+r.height/2,dx:-m.c,dy:-m.d,width:parseFloat(s.width),height:parseFloat(s.height)}})''')
        self.assertGreaterEqual(len(walking), 4)
        for right, left in zip(walking[::2], walking[1::2]):
            self.assertEqual((right['foot'], left['foot']), ('right', 'left'))
            self.assertIn('wet-foot-right.webp', right['src'])
            self.assertIn('wet-foot-left.webp', left['src'])
            # Looking along the path, the left sole must lie to the walker's left.
            lateral = (left['x']-right['x'])*right['dy'] - (left['y']-right['y'])*right['dx']
            self.assertGreater(lateral, 8)
        for previous, following in zip(walking, walking[1:]):
            dx,dy=following['x']-previous['x'],following['y']-previous['y']
            forward=dx*previous['dx']+dy*previous['dy']
            self.assertGreater(forward,1.1*(previous['height']+following['height'])/2)
            lateral=dx*previous['dy']-dy*previous['dx']
            toward_next_foot=lateral if following['foot']=='left' else -lateral
            self.assertGreater(toward_next_foot,.75*(previous['width']+following['width'])/2)
        self.assertGreater(float(steps.first.evaluate('e=>getComputedStyle(e).opacity')),.2)
        self.assertEqual(float(steps.last.evaluate('e=>getComputedStyle(e).opacity')),0)
        self.seek('room-wet-step',12500)
        self.assertGreater(float(steps.last.evaluate('e=>getComputedStyle(e).opacity')),.2)
        self.seek('room-wet-step',35000)
        self.assertEqual(float(steps.first.evaluate('e=>getComputedStyle(e).opacity')),0)

    def test_hand_residue_cannot_paint_a_dark_halo_on_transparent_glass(self):
        self.freeze()
        # Keep the pane genuinely transparent. A gray background on the pane itself
        # would conceal the old screen-blend/isolated-layer bug being tested.
        self.page.add_style_tag(content='''
            .room-corridor-scene{background:#777!important;filter:none!important;animation:none!important}
            .room-door-wire,.room-door-glass::after{display:none!important}
            .room-glass-mark:not(.room-test-residue){display:none!important}
        ''')
        glass = self.page.locator('.room-door-glass')
        before = Image.open(io.BytesIO(glass.screenshot())).convert('RGB')
        contact = self.page.evaluate('PalataAtmosphere.showContact(2,"hand")')
        self.assertEqual(contact['kind'], 'hand')
        hand = self.page.locator('.room-glass-mark[data-generation="'+str(contact['generation'])+'"]')
        hand.evaluate('''async e=>{
            e.classList.add('room-test-residue');e.style.left='50%';e.style.top='50%';e.style.setProperty('--mark-turn','0deg');
            await Promise.all([...document.images].map(im=>im.decode().catch(()=>{})));
            for(const a of e.getAnimations({subtree:true})){a.pause();const t=a.effect.getTiming();a.currentTime=Number(t.delay)+Number(t.duration)*.4;}
        }''')
        self.page.wait_for_timeout(100)
        after = Image.open(io.BytesIO(glass.screenshot())).convert('RGB')
        differences = [sum(b)/3-sum(a)/3 for a,b in zip(self.pixels(before),self.pixels(after))]
        self.assertGreater(sum(d>3 for d in differences), 20, 'The pale residue should remain visible')
        self.assertLessEqual(sum(d < -3 for d in differences), 3, 'Residue painted a dark halo over the view behind the glass')

    def test_help_is_finger_written_into_fog_with_moving_condensation(self):
        self.freeze()
        self.page.add_style_tag(content='''
            .hud-character-stage{display:none!important}
            .room-window-scene,.room-corridor-scene{background:#777!important;filter:none!important;animation:none!important}
            .room-distant-light{display:none!important}
            .room-door-wire,.room-door-glass::after,.room-window-glass::after,.room-outside-bounce{display:none!important}
            .room-glass-mark:not(.room-test-residue){display:none!important}
        ''')
        for surface, selector in [(2,'.room-door-glass')]:
            with self.subTest(surface=surface):
                hand_info=self.page.evaluate('i=>PalataAtmosphere.showContact(i,"hand")',surface)
                hand=self.page.locator('.room-glass-mark[data-generation="'+str(hand_info['generation'])+'"]')
                hand_width=hand.evaluate('e=>parseFloat(e.style.width)')
                pane=self.page.locator(selector)
                background=Image.open(io.BytesIO(pane.screenshot())).convert('RGB')
                info=self.page.evaluate('i=>PalataAtmosphere.showContact(i,"help")',surface)
                self.assertEqual(info['kind'],'help')
                fog=self.page.locator('.room-glass-mark[data-generation="'+str(info['generation'])+'"]')
                self.assertGreater(fog.evaluate('e=>parseFloat(e.style.width)'), hand_width*(1.5 if surface==2 else 1.3))
                self.assertEqual(fog.locator('.room-glass-help').get_attribute('aria-label'),'HELP')
                fog.evaluate('''e=>{
                    e.classList.add('room-test-residue');e.style.left='50%';e.style.top='50%';e.style.setProperty('--mark-turn','0deg');
                    for(const a of e.getAnimations({subtree:true})){a.pause();a.currentTime=a.effect.target===e?Number(a.effect.getTiming().duration)*.4:0;}
                }''')
                self.page.wait_for_timeout(100)
                before=Image.open(io.BytesIO(pane.screenshot())).convert('RGB')
                writing=fog.evaluate('''e=>{
                    const paths=[...e.querySelectorAll('.room-help-stroke')];
                    const before=paths.map(p=>getComputedStyle(p).strokeDashoffset);
                    const animations=e.getAnimations({subtree:true}).filter(a=>a.effect.target.matches('.room-help-stroke'));
                    const timing=animations.map(a=>{const t=a.effect.getTiming();return {start:Number(t.delay),end:Number(t.delay)+Number(t.duration)}});
                    for(const a of animations){const t=a.effect.getTiming();a.pause();a.currentTime=Number(t.delay)+Number(t.duration);}
                    return {before,after:paths.map(p=>getComputedStyle(p).strokeDashoffset),span:Math.max(...timing.map(t=>t.end))-Math.min(...timing.map(t=>t.start))};
                }''')
                self.assertGreaterEqual(len(writing['before']),4)
                self.assertNotEqual(writing['before'],writing['after'])
                self.assertGreater(writing['span'],5000,'HELP should be written slowly enough to follow each letter')
                self.page.wait_for_timeout(100)
                after=Image.open(io.BytesIO(pane.screenshot())).convert('RGB')
                # Writing clears the condensation instead of painting black letters.
                cleared=[sum(a)/3-sum(b)/3 for a,b in zip(self.pixels(before),self.pixels(after))]
                self.assertGreater(sum(d>3 for d in cleared),40)
                darkened=[sum(a)/3-sum(b)/3 for a,b in zip(self.pixels(background),self.pixels(after))]
                self.assertLessEqual(sum(d>3 for d in darkened),3,'Finger wipes should reveal the real background, not paint black ink')
                drips=fog.evaluate('''e=>{
                    const drops=[...e.querySelectorAll('.room-condensation-drop')];
                    const before=drops.map(p=>{const t=getComputedStyle(p).transform;return t==='none'?0:new DOMMatrix(t).f;});
                    for(const a of e.getAnimations({subtree:true}))if(a.effect.target.matches('.room-condensation-drop,.room-condensation-trail')){const t=a.effect.getTiming();a.pause();a.currentTime=Number(t.delay)+Number(t.duration)*.55;}
                    return drops.map((p,n)=>{const s=getComputedStyle(p);return {before:before[n],y:new DOMMatrix(s.transform).f,opacity:Number(s.opacity)}});
                }''')
                self.assertGreaterEqual(len(drips),2)
                self.assertTrue(all(d['y']-d['before']>10 and d['opacity']>.1 for d in drips))
                fog.evaluate('e=>e.remove()')

    def test_main_windows_keep_only_hands_even_when_fog_or_help_is_requested(self):
        self.freeze()
        for surface, selector in [(0,'.room-window-left'),(1,'.room-window-right')]:
            with self.subTest(surface=surface):
                # Ordinary windows retain hand residue only, including forced
                # preview requests for the effects reserved for door glass.
                for requested in ['help','fog','hand']:
                    info=self.page.evaluate('([i,kind])=>PalataAtmosphere.showContact(i,kind)',[surface,requested])
                    self.assertEqual(info['kind'],'hand')
                    self.assertIn(info['variant'],range(3))
                    hand=self.page.locator('.room-glass-mark[data-generation="'+str(info['generation'])+'"]')
                    self.assertEqual(hand.evaluate('e=>e.tagName'),'IMG')
                    self.assertTrue(hand.evaluate('e=>e.classList.contains("is-hand")'))
                samples=self.page.evaluate('i=>Array.from({length:8},()=>PalataAtmosphere.showContact(i).kind)',surface)
                self.assertEqual(set(samples),{'hand'})
                pane=self.page.locator(selector)
                self.assertEqual(pane.locator('.is-help,.is-fog,.room-help-fog,.room-help-stroke,.room-condensation-drop,.room-condensation-trail').count(),0)

    def test_metal_returns_match_the_registered_door_contours(self):
        returns=self.page.locator('.room-cabinet-leaf-right .room-cabinet-metal-return')
        self.assertEqual(returns.count(),4)
        # The free edge runs from y9 to y453, rather than the full 465px rectangle.
        edge=returns.nth(3).evaluate('e=>{const m=new DOMMatrix(getComputedStyle(e).transform);const l=parseFloat(e.style.width);return {start:m.m42,end:m.m42+m.m12*l,depth:parseFloat(e.style.height)}}')
        self.assertAlmostEqual(edge['start'],453,delta=.6)
        self.assertAlmostEqual(edge['end'],9,delta=.6)
        self.assertAlmostEqual(edge['depth'],4,delta=.02)
        self.assertEqual(self.page.locator('.room-handle-side').count(),156)
        self.assertEqual(self.page.locator('.room-cabinet-handle').first.evaluate('e=>getComputedStyle(e).transform'),'none')
        for name,time in [('room-curtain-draft',5400),('room-robe-draft',21600),('room-bag-draft',37260)]:
            self.seek(name,time)
        for selector in ['.room-moving-curtain','.room-moving-robe','.room-moving-bag']:
            self.assertNotEqual(self.page.locator(selector).evaluate('e=>getComputedStyle(e).transform'),'none')

    def test_trip_is_real_and_entrances_honor_reduced_motion(self):
        self.page.emulate_media(reduced_motion='reduce')
        for madness in [100, 0]:
            self.page.locator('.room-trip-switch').click()
            self.assertEqual(self.page.evaluate('stats.madness'), madness)
            self.assertEqual(self.page.evaluate('paperDollState.activeViewMode'), 'combat' if madness else 'patient')
            self.page.locator('.room-door-action').click()
            self.assertTrue(self.page.locator('#map-modal').is_visible())
            self.page.evaluate('toggleMapModal(false)')
            self.page.wait_for_function('document.querySelector(".room-door-assembly").dataset.state==="closed"')
        self.page.locator('.room-cabinet-action').click()
        self.assertTrue(self.page.locator('#custom-modal').is_visible())
        self.page.evaluate('closeCustomization()')
        self.page.wait_for_function('document.querySelector(".room-cabinet-assembly").dataset.state==="closed"')
        self.assertEqual(float(self.page.locator('.hospital-hud').evaluate('e=>getComputedStyle(e).getPropertyValue("--room-light")')), 1)


if __name__ == '__main__':
    unittest.main()
