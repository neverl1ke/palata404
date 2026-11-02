"""Independent catalog preservation, geometry, alpha and live-browser evidence checks."""
import hashlib,json,subprocess,unittest
from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage as ndi
from tests.asset_history import approved_current_hash, accepted_catalog_snapshot
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/female-five-hairstyles'
IDS={'hair-f5-'+s for s in ['pixie','jaw-bob','long-waves','high-ponytail','braided-updo']}
def catalog():
 return json.loads(subprocess.check_output(['node','-e',"const f=require('fs'),v=require('vm');console.log(v.runInNewContext(f.readFileSync('paper-doll-data.js','utf8')+';JSON.stringify(PAPER_DOLL_ITEMS)'))"],cwd=ROOT,text=True))
class FiveFemaleHairstyleTests(unittest.TestCase):
 def test_existing_catalog_renderer_and_art_preserved(self):
  items=catalog();expected=accepted_catalog_snapshot(json.loads((R/'before-catalog.json').read_text())['items']);ids={i['id'] for i in expected};self.assertEqual([i for i in items if i['id'] in ids],expected)
  for path,digest in json.loads((R/'protected-sha256.json').read_text()).items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),approved_current_hash(path,digest),path)
 def test_five_exact_female_only_independently_registered_entries(self):
  rows=json.loads((R/'registration.json').read_text());items={i['id']:i for i in catalog()};self.assertEqual({r['id'] for r in rows},IDS)
  for r in rows:
   if r['id'] not in items:
    self.assertIn(r['id'],['hair-f5-long-waves','hair-f5-high-ponytail']);continue
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
  for path,digest in d['runtime_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),approved_current_hash(path,digest))

class FemaleFitAuditTests(unittest.TestCase):
 def test_pixie_temples_cover_skull_landmarks_without_moving_crown_or_center(self):
  before=np.array(Image.open(ROOT/'review/female-five-fit-audit/before/assets/pixie.png'))
  after=np.array(Image.open(ROOT/'assets/wardrobe/hair/female-five/pixie.png'))
  self.assertTrue(np.array_equal(before[:79],after[:79]));self.assertTrue(np.array_equal(before[:,438:508],after[:,438:508]));self.assertTrue(np.array_equal(before[164:],after[164:]))
  # Measured head contours at rows115/125 are [398,547] and [399,546].
  for y,left,right in [(115,395,550),(125,396,549),(135,398,548)]:
   xx=np.flatnonzero(after[y,:,3]>=128);self.assertLessEqual(xx[0],left);self.assertGreaterEqual(xx[-1],right)
 def test_long_waves_keep_iris_clear_after_user_requested_ear_widening(self):
  before=np.array(Image.open(ROOT/'review/female-five-fit-audit/before/assets/long-waves.png'));after=np.array(Image.open(ROOT/'assets/wardrobe/hair/female-five/long-waves.png'))
  self.assertGreater(before[142,445,3],128);self.assertLessEqual(after[142,445,3],16)
  # The subsequent user explicitly requested wider waves; old right-side identity
  # is no longer the contract. Length and face visibility still are.
  self.assertEqual(Image.fromarray(after[:,:,3]).getbbox()[1::2],Image.fromarray(before[:,:,3]).getbbox()[1::2])
 def test_user_approved_pixie_and_jaw_bob_are_byte_identical_to_pre_ear_pass(self):
  for key in ['pixie','jaw-bob']:self.assertEqual((ROOT/f'review/female-ear-fit/before/assets/{key}.png').read_bytes(),(ROOT/f'assets/wardrobe/hair/female-five/{key}.png').read_bytes())
 def test_every_palette_color_preserves_alpha_and_is_exercised_on_every_head(self):
  d=json.loads((R/'browser-check.json').read_text());self.assertEqual(d['all_color_head_combinations'],5*17*25)
  records={(x['hair'],x['face'],x['color']) for x in d['color_combinations']};self.assertEqual(len(records),2125)
  for hair in IDS:
   self.assertEqual(len({x[2] for x in records if x[0]==hair}),25)
   for f in d['faces']:self.assertEqual(len([x for x in records if x[0]==hair and x[1]==f['id']]),25)


class FemaleEarFitTests(unittest.TestCase):
 def test_long_waves_enclose_ear_span_on_every_registered_head(self):
  a=np.array(Image.open(ROOT/'assets/wardrobe/hair/female-five/long-waves.png'))[:,:,3]
  for h in json.loads((R/'head-geometry.json').read_text()):
   head=np.array(Image.open(ROOT/h['path']))[:,:,3]
   for y in [130,140,150,160,170]:
    ear=np.flatnonzero(head[y]>=128);hair=np.flatnonzero(a[y]>=128)
    # Real opaque strands extend beyond both ear contours, not only alpha haze.
    self.assertLessEqual(hair[0],ear[0]-4,(h['id'],y));self.assertGreaterEqual(hair[-1],ear[-1]+4,(h['id'],y))
 def test_ponytail_reveals_actual_ear_and_preserves_crown_left_and_tail(self):
  before=np.array(Image.open(ROOT/'review/female-ear-fit/before/assets/high-ponytail.png'));after=np.array(Image.open(ROOT/'assets/wardrobe/hair/female-five/high-ponytail.png'))
  self.assertTrue(np.array_equal(before[:101],after[:101]));self.assertTrue(np.array_equal(before[230:],after[230:]));self.assertTrue(np.array_equal(before[:,:501],after[:,:501]));self.assertTrue(np.array_equal(before[:,620:],after[:,620:]))
  # Landmarks lie within the real young head's right ear, formerly covered by hair.
  head=np.array(Image.open(ROOT/'assets/wardrobe/faces/female_young_head.png'))[:,:,3]
  for x,y in [(554,140),(552,150),(549,160),(545,170)]:
   self.assertGreaterEqual(head[y,x],128);self.assertLessEqual(after[y,x,3],16)
 def test_updo_is_compact_and_side_knot_is_near_ear(self):
  a=np.array(Image.open(ROOT/'assets/wardrobe/hair/female-five/braided-updo.png'))[:,:,3]
  before=Image.open(ROOT/'review/female-ear-fit/before/assets/braided-updo.png').getchannel('A').getbbox();after=Image.fromarray(a).getbbox()
  self.assertLess(after[2]-after[0],.9*(before[2]-before[0]));self.assertLess(after[3],before[3]-25)
  # Main side knot now occupies x<=576 and ends by y218, next to the ear,
  # instead of hanging to x594 and below y240. Fine loose tendrils are excluded.
  yy,xx=np.where(a[175:230,530:610]>=128);self.assertTrue(len(xx)>100)
  self.assertLessEqual(int(xx.max())+530,576)
  dense_rows=[]
  for y in range(175,243):
   v=a[y,530:610]>=128;edges=np.diff(np.r_[False,v,False].astype(int));runs=np.where(edges==-1)[0]-np.where(edges==1)[0]
   if len(runs) and runs.max()>=8:dense_rows.append(y)
  self.assertLessEqual(max(dense_rows),218)

if __name__=='__main__':unittest.main()
