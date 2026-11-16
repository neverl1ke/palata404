"""Manual bench UI, selective skin tone, protected scenery and window ambience."""
import unittest
from pathlib import Path
from tests import test_game
OUT=Path(__file__).resolve().parents[1]/'test-results/rehab-final';OUT.mkdir(parents=True,exist_ok=True)
class RehabExercisesTests(unittest.TestCase):
 setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
 tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
 setUp=test_game.GameTests.setUp
 tearDown=test_game.GameTests.tearDown
 load=test_game.GameTests.load
 def gym(self,kind=None):
  self.page.locator('#location-card-box').click();self.page.locator('.quest-map-pin[data-room=gym]').dblclick(delay=40);self.page.wait_for_function('document.querySelector("[data-scene-room=gym]")?.dataset.rehabRenderer==="webgl"')
  if kind:self.page.locator(f'[data-rehab-equipment={kind}]').click();self.page.wait_for_function('document.querySelector(".rehab-exercise")?.dataset.exerciseReady==="true"')
 def test_bench_requires_input_full_reps_and_charges_once(self):
  self.load();self.gym('bench');self.page.clock.install();self.page.clock.pause_at((self.page.evaluate('Date.now()')+100)/1000);self.page.locator('[data-exercise-start]').click();self.page.clock.run_for(2000)
  self.assertEqual(self.page.evaluate('stats.energy'),100);self.assertEqual(self.page.locator('.rehab-exercise').get_attribute('data-exercise-count'),'0')
  view=self.page.locator('[data-exercise-view]');view.press('Space');self.page.clock.run_for(500);self.assertEqual(self.page.locator('.rehab-exercise').get_attribute('data-exercise-count'),'0')
  for rep in range(5):
   view.focus();self.page.keyboard.down('Space');self.page.clock.run_for(1800);self.assertEqual(self.page.locator('.rehab-exercise').get_attribute('data-exercise-phase'),'top')
   self.page.keyboard.up('Space');self.page.clock.run_for(1800)
  self.page.clock.run_for(1200);self.assertEqual(self.page.evaluate('stats.energy'),90);self.assertEqual(self.page.evaluate('stats.rehabTraining.bench.completed'),1)
  self.assertEqual(self.page.locator('.rehab-exercise').get_attribute('data-exercise-stage'),'rack');self.page.screenshot(path=str(OUT/'bench-completed.jpg'),type='jpeg',quality=93);self.page.clock.resume();self.page.locator('[data-exercise-back]').click();self.page.reload(wait_until='networkidle');self.assertEqual(self.page.evaluate('stats.rehabTraining.bench.completed'),1);self.assertEqual(self.page.evaluate('stats.energy'),90)
 def test_patient_skin_alpha_cloth_and_hardware_preserved(self):
  self.load();self.gym('bench')
  result=self.page.evaluate('''async()=>{const im=new Image();im.src='assets/rehabilitation/bench-hands.png';await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);const a=x.getImageData(0,0,c.width,c.height).data,g=PalataRehabSkinTone.grade(im).getContext('2d').getImageData(0,0,c.width,c.height).data;let alpha=0,cloth=0,metal=0,skin=0;for(let y=0;y<c.height;y++)for(let z=0;z<c.width;z++){const i=(y*c.width+z)*4,changed=a[i]!==g[i]||a[i+1]!==g[i+1]||a[i+2]!==g[i+2];if(a[i+3]!==g[i+3])alpha++;if(changed&&y>=500)cloth++;if(changed&&y>=278&&y<=327&&(z<265||z>990||(z>445&&z<804)))metal++;if(changed)skin++;}return{alpha,cloth,metal,skin}}''')
  self.assertEqual((result['alpha'],result['cloth'],result['metal']),(0,0,0));self.assertGreater(result['skin'],10000)
  self.page.screenshot(path=str(OUT/'bench-patient-tone.jpg'),type='jpeg',quality=93)
 def test_missing_art_blocks_training_and_returns_focus_without_spending(self):
  for kind in ['bench','rope']:
   self.page.route('**/assets/rehabilitation/'+kind+'-hands.png',lambda route:route.abort())
  self.load();self.gym()
  before=self.page.evaluate('JSON.stringify({stats,inventory})')
  for kind in ['bench','rope']:
   self.page.locator(f'[data-rehab-equipment={kind}]').click()
   self.page.wait_for_function('document.querySelector(".rehab-exercise")?.dataset.exerciseReady==="error"')
   self.assertTrue(self.page.locator('[data-exercise-start]').is_disabled());self.assertTrue(self.page.locator('[data-exercise-view]').is_disabled())
   self.page.wait_for_timeout(150);self.assertEqual(self.page.locator('.rehab-exercise').get_attribute('data-exercise-ready'),'error')
   self.page.locator('[data-exercise-back]').click()
   self.assertEqual(self.page.evaluate('document.activeElement.dataset.rehabEquipment'),kind)
   self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory})'),before)
 def test_trip_hover_protects_cabinet_pipe_and_weather_frames(self):
  self.load();self.page.locator('.room-trip-switch').click();self.gym()
  result=self.page.evaluate('''()=>{const canvas=document.querySelector('.rehab-live-canvas'),gl=canvas.getContext('webgl'),read=()=>{const a=new Uint8Array(canvas.width*canvas.height*4);gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,a);return a};PalataRehabScene.sample(1000);const before=read();const target=document.querySelector('[data-rehab-equipment=bag]');target.dispatchEvent(new Event('pointerenter'));for(let i=0;i<20;i++)PalataRehabScene.sample(1000);const after=read();let changed=0,protectedPixels=0;for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++){const i=((canvas.height-1-y)*canvas.width+x)*4,d=before[i]!==after[i]||before[i+1]!==after[i+1]||before[i+2]!==after[i+2];if(d)changed++;if(d&&((x>=1430&&x<1478&&y>=240&&y<720)||(x>=103&&x<130&&y>=535&&y<710)))protectedPixels++;}target.dispatchEvent(new Event('pointerleave'));PalataRehabScene.sample(0);const clear=document.querySelector('[data-scene-room=gym]').dataset.rehabWeather;PalataRehabScene.sample(24000);const rain=document.querySelector('[data-scene-room=gym]').dataset.rehabWeather;PalataRehabScene.sample(14000);const silhouette=document.querySelector('[data-scene-room=gym]').dataset.rehabSilhouette;return{changed,protectedPixels,clear,rain,silhouette}}''')
  self.assertGreater(result['changed'],0);self.assertEqual(result['protectedPixels'],0);self.assertEqual((result['clear'],result['rain'],result['silhouette']),('clear','rain','passing'))
  self.page.screenshot(path=str(OUT/'trip-room-ambient.jpg'),type='jpeg',quality=93)
