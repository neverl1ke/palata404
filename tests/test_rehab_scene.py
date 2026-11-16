"""Approved art, real scene targets, local motion and animation lifecycle."""
import json
from pathlib import Path
import unittest
from tests import test_game

OUT=Path(__file__).resolve().parents[1]/'test-results/level-rehab/integrated';OUT.mkdir(parents=True,exist_ok=True)
class RehabSceneTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
    setUp=test_game.GameTests.setUp
    tearDown=test_game.GameTests.tearDown
    load=test_game.GameTests.load

    def gym(self):
        self.page.locator('#location-card-box').click()
        self.page.locator('.quest-map-pin[data-room="gym"]').dblclick(delay=40)
        self.page.wait_for_function('document.querySelector("[data-scene-room=gym]")?.dataset.rehabRenderer==="webgl"')
        return self.page.locator('[data-scene-room="gym"]')

    def test_modes_all_four_real_targets_and_hover_are_local(self):
        self.load()
        results=[]
        for mode in ['patient','trip']:
            if mode=='trip':
                self.page.locator('.quest-room-tools button').first.click()
                self.page.locator('#map-modal .btn-close-map').click()
                self.page.locator('.room-trip-switch').click()
            scene=self.gym()
            self.assertTrue(self.page.locator('.scene-paper').is_hidden())
            self.assertIn('/'+mode+'.png',scene.locator('.scene-painting').get_attribute('src'))
            before=self.page.evaluate('JSON.stringify({stats,inventory})')
            for i,id in enumerate(['rope','pullup','bench','bag']):
                target=self.page.locator('[data-rehab-equipment="'+id+'"]')
                target.hover()
                if id in ['rope','bag']:
                    self.page.wait_for_function('i=>Math.abs(Number(document.querySelector("[data-scene-room=gym]").dataset.rehabMotion.split(",")[i]))>.01',arg=i)
                else:
                    self.page.wait_for_timeout(150)
                    self.assertEqual(float(scene.get_attribute('data-rehab-motion').split(',')[i]),0)
                self.assertEqual(target.evaluate('e=>getComputedStyle(e).outlineStyle'),'none')
                movement=json.loads(self.page.evaluate('JSON.stringify(document.querySelector("[data-scene-room=gym]").dataset.rehabMotion.split(",").map(Number))'))
                target.click()
                selector='.rehab-boxing' if id=='bag' else '.rehab-pullups' if id=='pullup' else '.rehab-exercise'
                self.page.locator(selector).wait_for(state='visible')
                self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory})'),before)
                self.page.locator('[data-boxing-back]' if id=='bag' else '[data-pullup-back]' if id=='pullup' else '[data-exercise-back]').click()
                results.append({'mode':mode,'equipment':id,'hoverMotion':movement,'cardAccessible':True})
            self.page.mouse.move(0,0)
            self.page.screenshot(path=str(OUT/(mode+'-full-room.png')))
        (OUT/'targets-check.json').write_text(json.dumps(results,indent=2))

    def test_neutral_pixels_ambient_reduced_motion_pause_and_context_fallback(self):
        self.load();scene=self.gym()
        pixels=self.page.evaluate('''()=>{
            const image=document.querySelector('[data-scene-room=gym] .scene-painting');
            const c=document.createElement('canvas');c.width=image.naturalWidth;c.height=image.naturalHeight;const ctx=c.getContext('2d');ctx.drawImage(image,0,0);const expected=ctx.getImageData(0,0,c.width,c.height).data;
            PalataRehabScene.drawNeutral();ctx.clearRect(0,0,c.width,c.height);ctx.drawImage(document.querySelector('.rehab-live-canvas'),0,0);const actual=ctx.getImageData(0,0,c.width,c.height).data;
            let max=0,different=0;for(let i=0;i<actual.length;i++){const d=Math.abs(actual[i]-expected[i]);max=Math.max(max,d);if(d>1)different++;}return{max,different};
        }''')
        self.assertLessEqual(pixels['max'],1,pixels)
        local=self.page.evaluate('''()=>{
            const canvas=document.querySelector('.rehab-live-canvas'),gl=canvas.getContext('webgl');
            const read=()=>{const a=new Uint8Array(canvas.width*canvas.height*4);gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,a);return a;};
            PalataRehabScene.sample(1000);const before=read();
            const target=document.querySelector('[data-rehab-equipment=rope]');target.dispatchEvent(new Event('pointerenter'));
            for(let i=0;i<20;i++)PalataRehabScene.sample(1000);const after=read();target.dispatchEvent(new Event('pointerleave'));
            let inside=0,outside=0;for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++){
                const k=(y*canvas.width+x)*4;let changed=false;for(let c=0;c<3;c++)if(before[k+c]!==after[k+c])changed=true;
                if(changed){const py=canvas.height-1-y;if(x>=12&&x<=110&&py>=260&&py<=590)inside++;else outside++;}
            }return {inside,outside};
        }''')
        self.assertGreater(local['inside'],0,local)
        self.assertEqual(local['outside'],0,local)
        self.assertLess(self.page.evaluate('()=>{PalataRehabScene.sample(8000);return Number(document.querySelector("[data-scene-room=gym]").dataset.rehabLamp)}'),0)
        ambient=self.page.evaluate('()=>{PalataRehabScene.sample(4000);return {...document.querySelector("[data-scene-room=gym]").dataset}}')
        self.assertEqual(float(ambient['rehabLamp']),0)
        self.assertTrue(any(float(x)>0 for x in ambient['rehabWindows'].split(',')))
        self.page.emulate_media(reduced_motion='reduce')
        # Wait for the neutral reduced-motion frame, not an arbitrary delay:
        # the media-query event may be queued behind a busy graphics process.
        self.page.wait_for_function('document.querySelector("[data-scene-room=gym]").dataset.rehabWindows==="0,0,0"')
        frames=scene.get_attribute('data-rehab-frames');self.page.wait_for_timeout(200)
        self.assertEqual(scene.get_attribute('data-rehab-frames'),frames)
        self.assertEqual(scene.get_attribute('data-rehab-motion'),'0.000,0.000,0.000,0.000')
        self.page.emulate_media(reduced_motion='no-preference')
        self.page.wait_for_function('n=>Number(document.querySelector("[data-scene-room=gym]").dataset.rehabFrames)>n',arg=int(frames))
        self.page.evaluate('document.querySelector(".rehab-live-canvas").getContext("webgl").getExtension("WEBGL_lose_context").loseContext()')
        self.page.wait_for_function('document.querySelector("[data-scene-room=gym]").dataset.rehabRenderer==="static"')
        self.assertTrue(scene.locator('.scene-painting').is_visible())
        self.page.locator('[data-rehab-equipment="rope"]').click()
        self.assertTrue(self.page.locator('.rehab-exercise').is_visible())
        (OUT/'renderer-check.json').write_text(json.dumps({'neutralPixels':pixels,'localHoverPixels':local,'reducedMotion':True,'contextLossFallback':True,'ambientSampled':True},indent=2))

    def test_window_lights_preserve_daylight_and_do_not_black_out_frames(self):
        self.load()
        results=[]
        for mode in ['patient','trip']:
            if mode=='trip':
                self.page.locator('.quest-room-tools button').first.click()
                self.page.locator('#map-modal .btn-close-map').click()
                self.page.locator('.room-trip-switch').click()
            self.gym()
            pixels=self.page.evaluate('''()=>{
                const c=document.querySelector('.rehab-live-canvas'),g=c.getContext('webgl'),program=g.getParameter(g.CURRENT_PROGRAM);
                const read=()=>{const a=new Uint8Array(c.width*c.height*4);g.readPixels(0,0,c.width,c.height,g.RGBA,g.UNSIGNED_BYTE,a);return a};
                PalataRehabScene.drawNeutral();const original=read();
                g.uniform1f(g.getUniformLocation(program,'ambient'),1);
                g.uniform3f(g.getUniformLocation(program,'windows'),0,0,0);g.drawArrays(g.TRIANGLE_STRIP,0,4);const off=read();
                g.uniform3f(g.getUniformLocation(program,'windows'),1,1,1);g.drawArrays(g.TRIANGLE_STRIP,0,4);const on=read();
                let daylightDarkened=0,coolOrDarkDetailsChanged=0,protectedCount=0,changing=0,onDifference=0;
                for(let y=280;y<430;y++)for(let x=215;x<336;x++){
                    const i=((c.height-1-y)*c.width+x)*4;
                    const difference=(a,b)=>Math.max(...[0,1,2].map(k=>Math.abs(a[i+k]-b[i+k])));
                    if([0,1,2].some(k=>off[i+k]<original[i+k]-1))daylightDarkened++;
                    if(original[i]-original[i+2]<=25||Math.max(original[i],original[i+1],original[i+2])<=61){
                        protectedCount++;if(difference(off,original)>1)coolOrDarkDetailsChanged++;
                    }
                    if(difference(on,off)>1)changing++;
                    onDifference=Math.max(onDifference,difference(on,original));
                }
                return{daylightDarkened,coolOrDarkDetailsChanged,protectedCount,changing,onDifference};
            }''')
            self.assertGreater(pixels['changing'],20,pixels)
            self.assertGreater(pixels['protectedCount'],100,pixels)
            if mode=='patient':self.assertEqual(pixels['daylightDarkened'],0,pixels)
            else:
                self.assertEqual(pixels['coolOrDarkDetailsChanged'],0,pixels)
                self.assertLessEqual(pixels['onDifference'],1,pixels)
            results.append({'mode':mode,**pixels})
        (OUT/'window-lights-check.json').write_text(json.dumps(results,indent=2))
