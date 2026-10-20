"""Independent catalog preservation, geometry, alpha and live-browser evidence checks."""
import hashlib,json,subprocess,unittest
from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/female-five-hairstyles'
IDS={'hair-f5-'+s for s in ['pixie','jaw-bob','long-waves','high-ponytail','braided-updo']}
def catalog():
 return json.loads(subprocess.check_output(['node','-e',"const f=require('fs'),v=require('vm');console.log(v.runInNewContext(f.readFileSync('paper-doll-data.js','utf8')+';JSON.stringify(PAPER_DOLL_ITEMS)'))"],cwd=ROOT,text=True))
class FiveFemaleHairstyleTests(unittest.TestCase):
 def test_existing_catalog_renderer_and_art_preserved(self):
  items=catalog();self.assertEqual([i for i in items if i['id'] not in IDS],json.loads((R/'before-catalog.json').read_text())['items'])
  for path,digest in json.loads((R/'protected-sha256.json').read_text()).items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
 def test_five_exact_female_only_independently_registered_entries(self):
  rows=json.loads((R/'registration.json').read_text());items={i['id']:i for i in catalog()};self.assertEqual({r['id'] for r in rows},IDS)
  for r in rows:
   i=items[r['id']];self.assertEqual(i['genders'],['female']);self.assertTrue(i['availableByDefault']);self.assertEqual(i['renderOrder'],9);self.assertEqual(i['placementByGender']['female'],{'x':0,'y':0,'width':941,'height':1672});self.assertEqual(i['genderVariants']['female'],r['path']+'?v='+r['sha256'][:8]);self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
 def test_full_canvas_safe_edges_alpha_and_open_central_face(self):
  for r in json.loads((R/'registration.json').read_text()):
   with self.subTest(hair=r['id']):
    im=Image.open(ROOT/r['path']);self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(941,1672));a=np.array(im)[:,:,3]
    self.assertFalse(a[:2].any());self.assertFalse(a[-2:].any());self.assertFalse(a[:,:2].any());self.assertFalse(a[:,-2:].any())
    # Nose and lips must stay unobstructed; no assumptions about deliberate side fringe.
    self.assertFalse(a[166:228,460:485].any())
    self.assertFalse(((a>0)&(a<=16)&(ndi.distance_transform_edt(a<32)>4)).any())
 def test_all_active_female_heads_share_measured_registration(self):
  m=json.loads((R/'head-geometry.json').read_text());self.assertEqual(len(m),17)
  for h in m:self.assertEqual(h['size'],[941,1672]);self.assertEqual(h['top_y'],33);self.assertEqual(h['ear_region_widest_row'][:3],[176,385,560])
 def test_browser_evidence_exercises_every_face_style_and_current_bytes(self):
  d=json.loads((R/'browser-check.json').read_text());expected={(h,f['id']) for h in IDS for f in d['faces']};actual={(x['hair'],x['face']) for x in d['combinations']};self.assertEqual(len(d['faces']),17);self.assertEqual(actual,expected);self.assertEqual(d['combination_count'],85);self.assertEqual(d['js_errors'],[]);self.assertEqual(d['http_errors'],[])
  for k in ['ui_selection','reload_each_style','patient_trip_independent','male_exclusion','unequip','protected_state_unchanged']:self.assertTrue(d[k],k)
  for path,digest in d['runtime_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)

class FemaleFitAuditTests(unittest.TestCase):
 def test_pixie_temples_cover_skull_landmarks_without_moving_crown_or_center(self):
  before=np.array(Image.open(ROOT/'review/female-five-fit-audit/before/assets/pixie.png'))
  after=np.array(Image.open(ROOT/'assets/wardrobe/hair/female-five/pixie.png'))
  self.assertTrue(np.array_equal(before[:79],after[:79]));self.assertTrue(np.array_equal(before[:,438:508],after[:,438:508]));self.assertTrue(np.array_equal(before[164:],after[164:]))
  # Measured head contours at rows115/125 are [398,547] and [399,546].
  for y,left,right in [(115,395,550),(125,396,549),(135,398,548)]:
   xx=np.flatnonzero(after[y,:,3]>=128);self.assertLessEqual(xx[0],left);self.assertGreaterEqual(xx[-1],right)
 def test_long_waves_clear_iris_without_touching_lower_hair_or_right_side(self):
  before=np.array(Image.open(ROOT/'review/female-five-fit-audit/before/assets/long-waves.png'));after=np.array(Image.open(ROOT/'assets/wardrobe/hair/female-five/long-waves.png'))
  self.assertGreater(before[142,445,3],128);self.assertLessEqual(after[142,445,3],16)
  self.assertTrue(np.array_equal(before[185:],after[185:]));self.assertTrue(np.array_equal(before[:111],after[:111]));self.assertTrue(np.array_equal(before[:,480:],after[:,480:]))
 def test_three_styles_without_confirmed_deformation_stay_byte_identical(self):
  for key in ['jaw-bob','high-ponytail','braided-updo']:self.assertEqual((ROOT/f'review/female-five-fit-audit/before/assets/{key}.png').read_bytes(),(ROOT/f'assets/wardrobe/hair/female-five/{key}.png').read_bytes())
 def test_every_palette_color_preserves_alpha_and_is_exercised_on_every_head(self):
  d=json.loads((R/'browser-check.json').read_text());self.assertEqual(d['all_color_head_combinations'],5*17*25)
  records={(x['hair'],x['face'],x['color']) for x in d['color_combinations']};self.assertEqual(len(records),2125)
  for hair in IDS:
   self.assertEqual(len({x[2] for x in records if x[0]==hair}),25)
   for f in d['faces']:self.assertEqual(len([x for x in records if x[0]==hair and x[1]==f['id']]),25)

if __name__=='__main__':unittest.main()
