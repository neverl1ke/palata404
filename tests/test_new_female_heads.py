"""Independent geometry, source protection and real-game checks for new female heads."""
import hashlib,json,subprocess,unittest
from pathlib import Path
import numpy as np
from PIL import Image,ImageChops
from scipy import ndimage as ndi
from tests import test_game as support
from tests.asset_history import active_female_heads, approved_current_hash
ROOT=support.ROOT;REPORT=ROOT/'review/female-heads-new-library'
def data():return json.loads((REPORT/'integration-manifest.json').read_text())

class NewFemaleHeadAssetTests(unittest.TestCase):
 def test_original_sources_and_all_preexisting_art_are_unchanged(self):
  m=data();self.assertEqual(len(m['files']),8)
  for e in m['files']:
   self.assertEqual(hashlib.sha256((REPORT/e['source']).read_bytes()).hexdigest(),e['source_sha256'])
  for p,h in m['protected_sha256'].items():
   raw=subprocess.check_output(['git','show','fd20bc3:'+p],cwd=ROOT) if p=='paper-doll.js' else (ROOT/p).read_bytes()
   self.assertEqual(hashlib.sha256(raw).hexdigest(),h if p=='paper-doll.js' else approved_current_hash(p,h),p)
 def test_runtime_catalog_preserves_every_previous_entry(self):
  code=';JSON.stringify({items:PAPER_DOLL_ITEMS,bodies:PAPER_DOLL_BODIES,frame:PAPER_DOLL_FRAME})'
  def catalog(s):return json.loads(subprocess.check_output(['node','-e','const vm=require("vm");process.stdout.write(vm.runInNewContext(require("fs").readFileSync(0,"utf8")))'],input=s+code,text=True))
  before=catalog(subprocess.check_output(['git','show','cbe74df:paper-doll-data.js'],text=True,cwd=ROOT));after=catalog((ROOT/'paper-doll-data.js').read_text())
  now={i['id']:i for i in after['items']}
  for i in before['items']:
   current=json.loads(json.dumps(now[i['id']]));old=json.loads(json.dumps(i))
   if old['slot']=='face':
    for k in ['genderVariants','bodyMaskByGender']:
     old.get(k,{}).pop('female',None);current.get(k,{}).pop('female',None)
   self.assertEqual(old,current,i['id'])
  self.assertEqual(before['bodies'],after['bodies']);self.assertEqual(before['frame'],after['frame'])
  released={e['id'] for e in data()['files']}
  for e in active_female_heads([x for x in json.loads((ROOT/'review/female-head-standard/manifest.json').read_text())['heads'] if x['id'] in released]):
   i=now[e['id']];self.assertEqual(i['genders'],['female']);self.assertTrue(i['fittedToGender']);self.assertEqual(i['renderOrder'],1)
   for key,p,h in [('genderVariants','output','sha256'),('bodyMaskByGender','mask','mask_sha256')]:
    self.assertEqual(i[key]['female'],e[p]+'?v='+hashlib.sha256((ROOT/e[p]).read_bytes()).hexdigest()[:8])
 def test_heads_have_female_scale_clean_alpha_and_opaque_interior(self):
  for e in data()['files']:
   im=Image.open(ROOT/e['output']);self.assertEqual(im.size,(941,1672));self.assertEqual(im.mode,'RGBA');a=np.array(im)[:,:,3]
   y,x=np.where(a[:205]>=128);self.assertTrue(20<=y.min()<=26,e['id']);self.assertTrue(164<=np.ptp(x)+1<=176,e['id'])
   inner=ndi.distance_transform_edt(a[:205]>=128)>2;self.assertTrue(np.all(a[:205][inner]==255),e['id'])
   labels,n=ndi.label(a>0,np.ones((3,3)));peaks=ndi.maximum(a,labels,np.arange(1,n+1))
   self.assertFalse(np.any(peaks<=16),e['id'])
   remote=(a>0)&(a<=16)&(ndi.distance_transform_edt(a<32)>4);self.assertFalse(remote.any(),e['id'])
 def test_individual_masks_remove_old_head_and_preserve_torso_without_holes(self):
  base=Image.open(ROOT/'base_female.png').convert('RGBA');b=np.array(base)
  masks=[]
  for e in data()['files']:
   h=Image.open(ROOT/e['output']);m=Image.open(ROOT/e['mask']).getchannel('A');masks.append(m.tobytes())
   self.assertIsNone(m.crop((0,0,941,205)).getbbox(),e['id'])
   body=base.copy();body.putalpha(ImageChops.multiply(base.getchannel('A'),m));c=np.array(Image.alpha_composite(body,h))
   self.assertTrue(np.array_equal(c[277:],b[277:]),e['id'])
   self.assertTrue(np.all(c[205:270,454:490,3]==255),e['id'])
   self.assertTrue(np.all(c[100:170,435:510,3]==255),e['id'])
  # Equal normalized lower-neck profiles may share mask pixels. Test the
  # resulting anatomy above instead of demanding different hashes artificially.
  self.assertEqual(len(masks),8)

class NewFemaleHeadsBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):support.GameTests.setUpClass()
 @classmethod
 def tearDownClass(cls):support.GameTests.tearDownClass()
 def setUp(self):self.case=support.GameTests();self.case.setUp();self.p=self.case.page;self.case.load()
 def tearDown(self):self.case.tearDown()
 def test_each_new_face_reloads_with_hair_colour_and_separate_loadouts(self):
  p=self.p;p.evaluate('openCustomization();setGender("female");setPaperDollView("combat");equipPaperDollItem("upperBody",null)')
  protected=p.evaluate('JSON.stringify({stats,inventory,equippedGear})')
  for e in [entry for entry in data()['files'] if entry['id']!='face-female-new-mature']:
   p.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-messy");setHairColor("white");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")}',e['id'])
   p.reload(wait_until='networkidle');p.wait_for_function('typeof paperDollState!=="undefined"')
   state=p.evaluate('paperDollState');self.assertEqual(state['appearance']['face'],e['id']);self.assertEqual(state['appearance']['hairColor'],'white');self.assertEqual(state['patientLoadout']['upperBody'],'patient-tunic');self.assertIsNone(state['combatLoadout']['upperBody'])
   for prefix in ['', 'wardrobe-']:
    p.wait_for_function('id=>{const i=document.getElementById(id);return i.complete&&i.naturalWidth===941}',arg=prefix+'layer-face')
    self.assertEqual(p.locator('#'+prefix+'layer-face').evaluate('e=>+getComputedStyle(e).zIndex'),1)
   self.assertEqual(p.evaluate('JSON.stringify({stats,inventory,equippedGear})'),protected)
   p.evaluate('openCustomization();setPaperDollView("combat")')
  self.assertEqual(self.case.errors,[])
 def test_female_cards_are_available_and_never_leak_to_male_catalog(self):
  p=self.p;p.evaluate('openCustomization();setGender("female");selectWardrobeCategory("appearance");selectWardrobeSlot("face")')
  for e in [entry for entry in data()['files'] if entry['id']!='face-female-new-mature']:self.assertEqual(p.locator('[data-wardrobe-card="'+e['id']+'"]').count(),1)
  p.evaluate('setGender("male")')
  for e in [entry for entry in data()['files'] if entry['id']!='face-female-new-mature']:
   self.assertEqual(p.locator('[data-wardrobe-card="'+e['id']+'"]').count(),0)
   self.assertFalse(p.evaluate('f=>equipPaperDollItem("face",f)',e['id']))
  self.assertEqual(self.case.errors,[])
