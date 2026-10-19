"""Independent RGBA contracts and real index.html wardrobe regressions."""
import hashlib,importlib.util,json,unittest
from pathlib import Path
import numpy as np
from PIL import Image,ImageChops
from scipy import ndimage as ndi
import tests.test_game as game_support
from tests.asset_history import historical_asset
ROOT=game_support.ROOT

def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
audit=module('png_audit','tools/audit-paper-doll-png.py')

def digest(b):return hashlib.sha256(b).hexdigest()

class AuditAssetTests(unittest.TestCase):
 def test_hair_preserves_approved_strands_and_local_repair_contracts(self):
  contracts=json.loads((ROOT/'tests/fixtures/paper-doll-audit.json').read_text())
  for e in contracts['files']:
   if 'protected_alpha17_sha256' not in e:continue
   a=np.array(Image.open(ROOT/e['path']).convert('RGBA'))
   self.assertEqual(digest(np.where(a[:,:,3]>=17,a[:,:,3],0).astype('uint8').tobytes()),e['protected_alpha17_sha256'],e['path'])
   self.assertEqual(digest(a[:,:,:3][a[:,:,3]>=240].tobytes()),e['protected_opaque_rgb_sha256'],e['path'])

 def test_face_identity_and_body_registration_are_protected(self):
  for e in json.loads((ROOT/'tests/fixtures/paper-doll-audit.json').read_text())['files']:
   p=historical_asset(e['path']);self.assertEqual(digest(p.read_bytes()),e['sha256'])
   im=Image.open(p).copy();self.assertEqual(list(im.size),e['size'])
   if 'face_rgb_box' in e:self.assertEqual(digest(im.convert('RGB').crop(e['face_rgb_box']).tobytes()),e['face_rgb_sha256'],e['path'])
   if e['path'].startswith('base_'):
    a=np.array(im.getchannel('A'));box=audit.bbox(a>=128)
    self.assertTrue(all(abs(x-y)<=1 for x,y in zip(box,e['before_bbox128'])),e['path'])
    self.assertLess(abs(int((a>=128).sum())-e['before_area128'])/e['before_area128'],.001)

 def test_no_remote_faint_haze_or_detached_low_alpha_specks(self):
  for rel in audit.resources():
   if '/masks/' in rel or 'patient_tunic_' in rel:continue
   a=np.array(Image.open(ROOT/rel).getchannel('A'));roi=a[:215] if '/faces/' in rel else a
   d=ndi.distance_transform_edt(~(roi>=32));self.assertEqual(int(((roi>0)&(roi<=16)&(d>4)).sum()),0,rel)
   # Full silhouette labels avoid inventing a component at an ROI boundary.
   labels,n=ndi.label(a>0,np.ones((3,3)))
   if n:
    ids=np.unique(labels[:len(roi)][roi>0])
    peaks=ndi.maximum(a,labels,ids);self.assertFalse(np.any(peaks<=16),rel)

 def test_all_head_masks_hide_old_skull_and_join_without_holes(self):
  count=0
  for item in audit.catalog()['items']:
   if item['slot']!='face':continue
   for g,src in item['genderVariants'].items():
    count+=1;head=Image.open(ROOT/src.split('?')[0]).convert('RGBA');base=Image.open(ROOT/f'base_{g}.png').convert('RGBA');mask=Image.open(ROOT/item['bodyMaskByGender'][g].split('?')[0]).getchannel('A')
    self.assertIsNone(mask.crop((0,0,941,210)).getbbox(),'Old skull visible')
    b=base.copy();b.putalpha(ImageChops.multiply(base.getchannel('A'),mask));result=Image.alpha_composite(b,head);aa=np.array(result.getchannel('A'))
    self.assertEqual(ndi.label(aa>=128,np.ones((3,3)))[1],1,(item['id'],g,'Disconnected silhouette'))
    self.assertTrue(np.all(aa[250:288,445:505]>=np.array(base.getchannel('A'))[250:288,445:505]),(item['id'],g,'Neck hole'))
    self.assertIsNone(ImageChops.difference(result,base).crop((0,310,941,1672)).getbbox())
  self.assertEqual(count,16)  # Eight male plus eight unchanged female overlays.

 def test_rear_texture_closes_inner_ear_openings_without_covering_face(self):
  item=next(i for i in audit.catalog()['items'] if i['id']=='hair-shoulder-length');a=np.array(Image.open(ROOT/item['layers'][0]['genderVariants']['male'].split('?')[0]))
  self.assertFalse(np.any(a[:128,:,3]));self.assertFalse(np.any(a[218:,:,3]));self.assertFalse(np.any(a[:,435:510,3]))
  for x,y in [(408,180),(410,190),(536,180),(535,190)]:self.assertGreaterEqual(int(a[y,x,3]),220,(x,y))
  self.assertGreater(np.std(a[a[:,:,3]>240,:3]),12,'Rear must contain strand texture, not flat fill')

 def test_analyzer_detects_connected_alpha_one_noise_and_preserves_real_strands(self):
  import tempfile
  clean=module('edge_clean','tools/clean-paper-doll-edges.py');a=np.zeros((64,64,4),dtype='uint8');a[20:45,20:45]=[160,110,75,255];a[30,5:21]=[30,20,10,1];a[10:20,32]=[60,45,30,32];a[25,19]=[80,55,38,128]
  (ROOT/'test-results').mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=ROOT/'test-results') as tmp:
   p=Path(tmp)/'probe.png';Image.fromarray(a).save(p);result=audit.analyze(p);self.assertEqual(result['nonzero_components'],1);self.assertGreater(result['weak_remote_pixels'],0)
  b,stats=clean.clean(a,'hair');self.assertEqual(int(b[30,5,3]),0);self.assertTrue(np.array_equal(a[10:20,32],b[10:20,32]));self.assertGreater(stats['edge_rgb_corrected'],0);self.assertGreater(int(b[25,19,0]),120)

class AuditBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):game_support.GameTests.setUpClass()
 @classmethod
 def tearDownClass(cls):game_support.GameTests.tearDownClass()
 def setUp(self):self.t=game_support.GameTests();self.t.setUp();self.p=self.t.page;self.missing=[];self.p.on('response',lambda r:self.missing.append(r.url) if r.status>=400 else None);self.t.load()
 def tearDown(self):
  errors=self.t.errors[:];self.t.tearDown();self.assertEqual(errors,[]);self.assertEqual(self.missing,[])
 def settle(self):
  self.p.wait_for_function('''async()=>{for(const i of document.getElementById('wardrobe-paperdoll').querySelectorAll('img:not(.hidden)')){const r=i.paperHairRequest;if(!r)continue;const n=r.lastIndexOf('|'),s=r.slice(0,n),c=r.slice(n+1);if(i.getAttribute('src')!==(c==='original'?s:await coloredHairSource(s,c,i.paperHairColorReference))||!i.complete||!i.naturalWidth)return false}return true}''')
 def test_all_90_combinations_layers_backgrounds_and_reload(self):
  self.p.evaluate('openCustomization();setPaperDollView("combat");selectWardrobeCategory("appearance");selectWardrobeSlot("hair")');count=0
  before=self.p.evaluate('JSON.stringify({stats,inventory,equippedGear})')
  for gender in ['male','female']:
   self.p.evaluate('g=>setGender(g)',gender);styles=self.p.evaluate('wardrobeVisibleItems().map(i=>i.id)');self.assertEqual(len(styles),7 if gender=='male' else 8)
   for face in [None,'face-asian','face-young','face-exhausted','face-elder','face-alternative']:
    self.p.evaluate('f=>equipPaperDollItem("face",f)',face)
    for hair in styles:
     count+=1;self.p.evaluate('h=>equipPaperDollItem("hair",h)',hair)
     for color in ['original','white']:
      self.p.evaluate('c=>setHairColor(c)',color);self.settle()
      for bg in ['#fff','#555','#000','#00ff00']:
       self.p.locator('.wardrobe-stage').evaluate('(e,bg)=>{e.style.backgroundImage="none";e.style.backgroundColor=bg}',bg)
       self.assertEqual(self.p.locator('#wardrobe-layer-body').evaluate('i=>+getComputedStyle(i).zIndex'),0)
       if face:self.assertEqual(self.p.locator('#wardrobe-layer-face').evaluate('i=>+getComputedStyle(i).zIndex'),1)
       if hair!='hair-none':self.assertEqual(self.p.locator('#wardrobe-layer-hair').evaluate('i=>+getComputedStyle(i).zIndex'),9)
       rear=self.p.locator('#wardrobe-layer-hair-rear');self.assertEqual(rear.count(),1 if gender=='male' and hair=='hair-shoulder-length' else 0)
       if rear.count():self.assertEqual(rear.evaluate('i=>+getComputedStyle(i).zIndex'),-1)
  self.assertEqual(count,90);self.assertEqual(self.p.evaluate('JSON.stringify({stats,inventory,equippedGear})'),before)
  self.p.reload(wait_until='networkidle');self.assertEqual(self.p.evaluate('paperDollState.appearance.face'),'face-alternative');self.assertEqual(self.p.evaluate('paperDollState.appearance.hair'),'hair-shoulder-length');self.assertEqual(self.p.evaluate('paperDollState.appearance.hairColor'),'white')

 def test_rear_and_front_palette_preserve_alpha_for_five_colors(self):
  self.p.evaluate('setGender("male");equipPaperDollItem("hair","hair-shoulder-length");openCustomization()')
  for color in ['original','black','white','red','blue']:
   self.p.evaluate('c=>setHairColor(c)',color);self.settle()
   result=self.p.evaluate('''async c=>{const i=PAPER_DOLL_ITEMS.find(i=>i.id==='hair-shoulder-length'),part=i.layers[0],src=part.genderVariants.male;async function pixels(s){const im=new Image();im.src=s;await im.decode();const cv=document.createElement('canvas');cv.width=im.width;cv.height=im.height;const ctx=cv.getContext('2d');ctx.drawImage(im,0,0);return ctx.getImageData(0,0,cv.width,cv.height).data}const a=await pixels(src),b=await pixels(await coloredHairSource(src,c,part.colorReference));let n=0;for(let k=3;k<a.length;k+=4)if(a[k]!==b[k])n++;return n}''',color)
   self.assertEqual(result,0)
  self.p.evaluate('setGender("female")');self.assertEqual(self.p.locator('#wardrobe-layer-hair-rear').count(),0)

 def test_mobile_catalog_single_scroll_targets_palette_and_player_flow(self):
  out=ROOT/'test-results';out.mkdir(exist_ok=True)
  for width,height in [(320,568),(360,640),(390,844),(430,844),(768,844)]:
   self.p.set_viewport_size({'width':width,'height':height});self.p.evaluate('openCustomization()')
   for mode in ['patient','combat']:
    self.p.evaluate('m=>setPaperDollView(m)',mode)
    for category in self.p.locator('[data-wardrobe-category]').evaluate_all('es=>es.map(e=>e.dataset.wardrobeCategory)'):
     self.p.locator('[data-wardrobe-category="'+category+'"]').click()
     for slot in self.p.locator('[data-wardrobe-slot]').evaluate_all('es=>es.map(e=>e.dataset.wardrobeSlot)'):
      self.p.locator('[data-wardrobe-slot="'+slot+'"]').click();self.assertEqual(self.p.evaluate('wardrobeSlot'),slot)
      cards=self.p.locator('[data-wardrobe-card]')
      if cards.count():
       card=cards.first;card.scroll_into_view_if_needed();self.assertTrue(card.evaluate('e=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'),(width,mode,category,slot));card.click()
    self.p.locator('[data-wardrobe-category="appearance"]').click();self.p.locator('[data-paper-gender="female"]').click();self.p.locator('[data-wardrobe-slot="hair"]').click()
    self.assertEqual(self.p.locator('[data-palette-toggle]').get_attribute('aria-expanded'),'false');self.p.locator('[data-palette-toggle]').click();self.p.locator('[data-hair-color-group="natural"]').click();self.p.locator('[data-hair-color="black"]').click();self.p.locator('[data-palette-toggle]').click()
    self.p.locator('[data-wardrobe-card="hair-bob-bangs"]').click();button=self.p.locator('[data-wardrobe-action="hair-bob-bangs"]')
    if not button.is_disabled():button.click()
    self.assertEqual(self.p.evaluate('paperDollState.appearance.hair'),'hair-bob-bangs')
    self.assertEqual(self.p.locator('#wardrobe-container').evaluate('e=>getComputedStyle(e).overflowY'),'visible')
    self.assertTrue(self.p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    for selector in ['[data-palette-toggle]','[data-wardrobe-action="hair-bob-bangs"]','[data-paper-gender="female"]']:
     el=self.p.locator(selector);el.scroll_into_view_if_needed();box=el.bounding_box();self.assertGreaterEqual(box['height'],44)
     self.assertTrue(el.evaluate('e=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'),selector)
    self.p.screenshot(path=str(out/f'audit-mobile-{width}-{mode}.png'))
  self.p.evaluate('setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic");setPaperDollView("combat");equipPaperDollItem("upperBody",null);setPaperDollView("patient");setHairColor("black")');self.p.reload(wait_until='networkidle')
  self.assertEqual(self.p.evaluate('paperDollState.patientLoadout.upperBody'),'patient-tunic');self.assertIsNone(self.p.evaluate('paperDollState.combatLoadout.upperBody'));self.assertEqual(self.p.evaluate('paperDollState.appearance.hairColor'),'black')
