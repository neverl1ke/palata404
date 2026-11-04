"""Approved two-part hair must follow the selected head, color, save and gender."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image
from tests import test_game as game_tests
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/female-two-approved-20261104'
IDS=['hair-female-braids','hair-female-curls']
class FemaleTwoApprovedAssets(unittest.TestCase):
 def test_exact_approved_bytes_and_native_frames(self):
  receipt=json.loads((REPORT/'integration.json').read_text());self.assertEqual(len(receipt['records']),64)
  self.assertEqual(len({(r['face'],r['style']) for r in receipt['records']}),32)
  for r in receipt['records']:
   path,version=r['source'].split('?v=');raw=(ROOT/path).read_bytes();digest=hashlib.sha256(raw).hexdigest();self.assertEqual(digest,r['sha256']);self.assertEqual(version,digest[:8])
   with Image.open(ROOT/path) as im:self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(941,1672))
  for entry in receipt['palette_references']+receipt['heads']:self.assertEqual(hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(),entry['sha256'])
  for g,digest in receipt['bodies'].items():self.assertEqual(hashlib.sha256((ROOT/f'base_{g}.png').read_bytes()).hexdigest(),digest)
class FemaleTwoApprovedBrowser(unittest.TestCase):
 @classmethod
 def setUpClass(cls):game_tests.GameTests.setUpClass.__func__(cls)
 @classmethod
 def tearDownClass(cls):game_tests.GameTests.tearDownClass.__func__(cls)
 setUp=game_tests.GameTests.setUp
 tearDown=game_tests.GameTests.tearDown
 load=game_tests.GameTests.load
 def wait_hair(self):
  self.page.wait_for_function('''async()=>{const parts=paperDollItemLayers(selectedPaperDollItem('hair'),'female');for(const part of parts){const expected=await coloredHairSource(part.genderVariants.female,paperDollState.appearance.hairColor,part.colorReference);for(const prefix of ['', 'wardrobe-']){const im=document.getElementById(prefix+'layer-hair'+(part.id==='front'?'':'-'+part.id));if(!im||im.getAttribute('src')!==expected||!im.complete||!im.naturalWidth||im.classList.contains('hidden'))return false}}return true}''')
 def test_every_head_modes_and_palette_use_approved_fit(self):
  self.load();self.page.evaluate('openCustomization();setGender("female")')
  records=json.loads((REPORT/'integration.json').read_text())
  for hair in IDS:
   for face in dict.fromkeys(r['face'] for r in records['records']):
    with self.subTest(hair=hair,face=face):
     self.page.evaluate('([h,f])=>{equipPaperDollItem("face",f==="@native"?null:f);equipPaperDollItem("hair",h)}',[hair,face])
     for mode,color in [('patient','original'),('combat','white'),('patient','blue')]:
      self.page.evaluate('([m,c])=>{setPaperDollView(m);setHairColor(c)}',[mode,color]);self.wait_hair()
     actual=self.page.evaluate('paperDollItemLayers(selectedPaperDollItem("hair"),"female").map(p=>p.genderVariants.female)')
     expected=[r['source'] for r in records['records'] if r['face']==face and r['style']==hair.removeprefix('hair-female-')];self.assertEqual(actual,expected)
     self.assertIsNone(self.page.evaluate('femaleHairFitFor("female",paperDollState.appearance.face,paperDollState.appearance.hair)'))
  self.assertEqual(self.page.evaluate('[...failedPaperDollImages]'),[])
 def test_ui_reload_mobile_gender_and_unequip(self):
  self.page.set_viewport_size({'width':390,'height':844});self.load();self.page.evaluate('openCustomization();setGender("female");selectWardrobeCategory("appearance");selectWardrobeSlot("hair")')
  for hair in IDS:
   self.page.locator(f'[data-wardrobe-card="{hair}"]').click();self.page.locator('#wardrobe-item-detail [data-wardrobe-action]').click();self.wait_hair()
   self.page.evaluate('setHairColor("white")');self.wait_hair();self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.wait_hair();self.assertEqual(self.page.evaluate('paperDollState.appearance.hair'),hair)
   self.page.evaluate('setGender("male")');self.assertEqual(self.page.locator('[data-paper-extra][id$="layer-hair-rear"]').count(),0);self.assertFalse(self.page.evaluate('h=>equipPaperDollItem("hair",h)',hair))
   self.page.evaluate('setGender("female");selectWardrobeCategory("appearance");selectWardrobeSlot("hair")')
  self.page.evaluate('equipPaperDollItem("hair","hair-none")');self.assertEqual(self.page.locator('[data-paper-extra][id$="layer-hair-rear"]').count(),0)
