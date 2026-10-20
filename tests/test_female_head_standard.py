"""Reference-size geometry and rendered-native compatibility, independent audits."""
import hashlib,json,subprocess,unittest
from pathlib import Path
import numpy as np
from PIL import Image,ImageChops
from scipy import ndimage as ndi
from tests import test_game as support
ROOT=support.ROOT;D=ROOT/'review/female-head-standard'
def manifest():return json.loads((D/'manifest.json').read_text())

class FemaleStandardAssetTests(unittest.TestCase):
 def test_reference_all_sources_bodies_male_art_and_hair_are_unchanged(self):
  m=manifest();self.assertEqual(len(m['heads']),17)
  for p,h in m['protected_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)
  e=next(e for e in m['heads'] if e['reference']);self.assertEqual(e['id'],'face-young');self.assertEqual(e['output'],e['source']);self.assertEqual(e['sha256'],e['source_sha256'])
 def test_every_female_head_has_exact_reference_width_top_and_centre(self):
  for e in manifest()['heads']:
   im=Image.open(ROOT/e['output']);self.assertEqual(im.size,(941,1672));a=np.array(im)[:,:,3]>=128;y,x=np.where(a[:218]);self.assertEqual((int(y.min()),int(x.min()),int(x.max())),(33,385,560),e['id'])
   widths=a[100:190].sum(axis=1);row=100+int(np.argmax(widths));xx=np.where(a[row])[0];self.assertEqual((int(xx.max()-xx.min()+1),float((xx.min()+xx.max())/2)),(176,472.5),e['id'])
 def test_uniform_transform_preserves_portrait_rgb_above_neck_join(self):
  for e in manifest()['heads']:
   if e['reference']:continue
   im=Image.open(ROOT/e['source']).convert('RGBA');p=e['registration'];s,tx,ty=p['scale'],p['x'],p['y'];scaled=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS);sx,sy=scaled.width/im.width,scaled.height/im.height
   registered=np.array(scaled.transform((941,1672),Image.Transform.AFFINE,(sx/s,0,-tx*sx/s,0,sy/s,-ty*sy/s),Image.Resampling.BICUBIC))[:245];out=np.array(Image.open(ROOT/e['output']))[:245];visible=(out[:,:,3]>0)&(registered[:,:,3]>0)
   self.assertTrue(np.array_equal(out[:,:,:3][visible],registered[:,:,:3][visible]),e['id'])
 def test_paired_masks_preserve_original_torso_and_neck_opacity(self):
  base=Image.open(ROOT/'base_female.png').convert('RGBA');original=np.array(base)
  for e in manifest()['heads']:
   body=base.copy();mask=Image.open(ROOT/e['mask']).getchannel('A');self.assertIsNone(mask.crop((0,0,941,210)).getbbox());body.putalpha(ImageChops.multiply(body.getchannel('A'),mask));out=np.array(Image.alpha_composite(body,Image.open(ROOT/e['output']).convert('RGBA')))
   self.assertTrue(np.array_equal(out[300:],original[300:]),e['id']);self.assertTrue(np.all(out[250:288,445:505,3]>=original[250:288,445:505,3]),e['id']);self.assertEqual(ndi.label(out[:,:,3]>=128,np.ones((3,3)))[1],1,e['id'])
 def test_no_detached_weak_alpha_or_remote_faint_pixels_in_new_derivatives(self):
  for e in manifest()['heads']:
   if e['reference']:continue
   a=np.array(Image.open(ROOT/e['output']))[:,:,3];remote=(a>0)&(a<=16)&(ndi.distance_transform_edt(a<32)>4);self.assertFalse(remote.any(),e['id']);lab,n=ndi.label(a>0,np.ones((3,3)));self.assertFalse(np.any(ndi.maximum(a,lab,np.arange(1,n+1))<=16),e['id'])
 def test_template_matches_actual_unchanged_reference(self):
  e=next(e for e in manifest()['heads'] if e['reference']);t=json.loads((D/'template/hair-template.json').read_text());self.assertEqual(t['head_mount'],{'left_x':385,'right_x':560,'width':176,'crown_y':33,'center_x':472.5,'threshold_alpha':128});self.assertEqual((D/'template/reference-head.png').read_bytes(),(ROOT/e['source']).read_bytes())
  with Image.open(D/'template/reference-head-4x.png') as im:self.assertEqual(im.size,(1080,1680))
 def test_all_seventeen_catalog_resources_and_cache_hashes_are_registered(self):
  code='const fs=require("fs"),vm=require("vm");console.log(vm.runInNewContext(fs.readFileSync("paper-doll-data.js","utf8")+`;JSON.stringify({items:PAPER_DOLL_ITEMS,native:PAPER_DOLL_NATIVE_HEADS})`))'
  catalog=json.loads(subprocess.check_output(['node','-e',code],cwd=ROOT,text=True))
  for e in manifest()['heads']:
   item=catalog['native']['female'] if e['id'] is None else next(i for i in catalog['items'] if i['id']==e['id'])
   for key,path,h in [('genderVariants','output','sha256'),('bodyMaskByGender','mask','mask_sha256')]:
    self.assertEqual(hashlib.sha256((ROOT/e[path]).read_bytes()).hexdigest(),e[h]);self.assertEqual(item[key]['female'],e[path]+'?v='+e[h][:8])
   self.assertEqual(item['placementByGender']['female'],{'x':0,'y':0,'width':941,'height':1672})
 def test_male_renderer_pixels_match_previous_release_on_every_combination(self):
  if not (D/'geometry/result.json').exists():self.fail('Capture the real game geometry matrix before the release checks')
  records=[json.loads(s) for s in (D/'geometry/records.jsonl').read_text().splitlines()];male=[r for r in records if r['gender']=='male'];self.assertEqual(len(male),63)
  for r in male:
   before=ROOT/'review/female-heads-new-library/geometry'/r['key'];before=before.with_suffix('.webp');after=D/r['path'];self.assertIsNone(ImageChops.difference(Image.open(before).convert('RGB'),Image.open(after).convert('RGB')).getbbox(),r['key'])

class FemaleStandardBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):support.GameTests.setUpClass()
 @classmethod
 def tearDownClass(cls):support.GameTests.tearDownClass()
 def setUp(self):self.case=support.GameTests();self.case.setUp();self.case.load();self.p=self.case.page
 def tearDown(self):self.case.tearDown()
 def test_native_head_is_rendered_but_stays_null_in_saves_and_clears_on_male(self):
  p=self.p;p.evaluate('openCustomization();setGender("female");equipPaperDollItem("face",null)');expected=next(e for e in manifest()['heads'] if e['id'] is None)
  self.assertIsNone(p.evaluate('paperDollState.appearance.face'));self.assertEqual(p.evaluate('PAPER_DOLL_ITEMS.some(i=>i.id==="native-female-head")'),False)
  for prefix in ['', 'wardrobe-']:
   self.assertEqual(p.locator('#'+prefix+'layer-face').get_attribute('src'),expected['output']+'?v='+expected['sha256'][:8]);self.assertEqual(p.locator('#'+prefix+'layer-face').evaluate('e=>+getComputedStyle(e).zIndex'),1)
  p.reload(wait_until='networkidle');self.assertIsNone(p.evaluate('paperDollState.appearance.face'));p.evaluate('setGender("male")');self.assertIsNone(p.locator('#layer-face').get_attribute('src'));self.assertEqual(p.locator('#layer-body').evaluate('e=>e.style.maskImage'),'')
 def test_every_female_choice_restores_face_hair_colour_and_separate_outfits(self):
  p=self.p;p.evaluate('openCustomization();setGender("female");setPaperDollView("combat");equipPaperDollItem("upperBody",null)');protected=p.evaluate('JSON.stringify({stats,inventory,equippedGear})')
  for e in manifest()['heads']:
   p.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-textured-short");setHairColor("white");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")}',e['id']);p.reload(wait_until='networkidle');p.wait_for_function('typeof paperDollState!=="undefined"');s=p.evaluate('paperDollState');self.assertEqual(s['appearance'],{'face':e['id'],'hair':'hair-textured-short','hairColor':'white'});self.assertEqual(s['patientLoadout']['upperBody'],'patient-tunic');self.assertIsNone(s['combatLoadout']['upperBody']);self.assertEqual(p.evaluate('JSON.stringify({stats,inventory,equippedGear})'),protected);p.evaluate('openCustomization();setPaperDollView("combat")')
  self.assertEqual(self.case.errors,[])
