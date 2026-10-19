"""Independent bounds, continuity, pigment and facial-feature regressions for 8bcf183 fixes."""
import hashlib,importlib.util,json,unittest
from pathlib import Path
import numpy as np
from PIL import Image,ImageChops
from scipy import ndimage as ndi
import tests.test_paper_doll_audit as support
from tests.asset_history import historical_asset
ROOT=support.ROOT
spec=importlib.util.spec_from_file_location('targeted_refine',ROOT/'tools/refine-paper-doll-targeted.py');refine=importlib.util.module_from_spec(spec);spec.loader.exec_module(refine)
def read(p):return np.array(Image.open(p).convert('RGBA'))
def digest(b):return hashlib.sha256(b).hexdigest()
def reference(g,k):
 a=np.zeros((1672,941,4),dtype='uint8');a[20:285,365:585]=read(ROOT/f'tests/fixtures/targeted-face-references/{g}_{k}.png');return a
class TargetedAssetTests(unittest.TestCase):
 def test_only_authorized_pixels_change_and_all_other_assets_remain_exact(self):
  fixture=json.loads((ROOT/'tests/fixtures/paper-doll-targeted-fix.json').read_text());self.assertEqual(len(fixture['files']),37)
  for e in fixture['files']:
   with self.subTest(path=e['path']):
    p=historical_asset(e['path']);a=read(p);self.assertEqual([a.shape[1],a.shape[0]],e['size']);self.assertEqual(digest(p.read_bytes()),e['sha256'])
    if not e['changed']:self.assertEqual(e['before_sha256'],e['sha256'])
    for field,c in [('alpha',3),('rgb',slice(0,3))]:
     allowed=np.zeros(a.shape[:2],bool)
     for y,l,r in e['allowed_'+field+'_runs']:allowed[y,l:r]=True
     self.assertEqual(digest(a[:,:,c][~allowed].tobytes()),e['outside_'+field+'_sha256'],field)
    if 'core_rgb_sha256' in e:self.assertEqual(digest(a[90:205,435:515,:3].tobytes()),e['core_rgb_sha256'])
 def test_historical_asian_scale_is_small_registered_and_head_edges_have_narrow_antialiasing(self):
  before=reference('male','asian');a=read(ROOT/'assets/wardrobe/faces/male_asian_head.png')
  def width(z):
   yy,xx=np.where(z[30:218,:,3]>=128);return int(xx.max()-xx.min()+1)
  ratio=width(a)/width(before);self.assertGreater(ratio,1.02);self.assertLess(ratio,1.055)
  top=lambda z:int(np.where(z[:,:,3]>=128)[0].min());self.assertLessEqual(abs(top(a)-top(before)),1)
  for g in ['male','female']:
   for kind in ['asian','young','exhausted','elder','alternative']:
    z=read(historical_asset(f'assets/wardrobe/faces/{g}_{kind}_head.png'))[:,:,3]
    for y in range(90,211):
     xs=np.where(z[y]>=128)[0]
     for x in [xs[0],xs[-1]]:
      band=z[y,max(0,x-4):x+5];self.assertLessEqual(int(((band>16)&(band<240)).sum()),2,(g,kind,y))
 def test_historical_exhausted_neck_restores_base_without_holes_or_abrupt_side_jumps(self):
  base=Image.open(historical_asset('base_female.png')).convert('RGBA');mask=Image.open(historical_asset('assets/wardrobe/faces/masks/female_exhausted_body.png')).getchannel('A');body=base.copy();body.putalpha(ImageChops.multiply(base.getchannel('A'),mask));head=Image.open(historical_asset('assets/wardrobe/faces/female_exhausted_head.png')).convert('RGBA');result=Image.alpha_composite(body,head)
  self.assertIsNone(ImageChops.difference(result,base).crop((0,272,941,1672)).getbbox())
  aa=np.array(result.getchannel('A'));self.assertTrue(np.all(aa[225:288,445:505]>=np.array(base.getchannel('A'))[225:288,445:505]))
  edges=[]
  for y in range(225,265):
   row=aa[y]/255;xs=np.where(row>=.5)[0];l,r=xs[0],xs[-1];edges.append([l-1+(.5-row[l-1])/(row[l]-row[l-1]),r+(.5-row[r])/(row[r+1]-row[r])])
  self.assertLess(np.abs(np.diff(np.array(edges),axis=0)).max(),2.5)
 def test_historical_alternative_tones_move_toward_body_and_original_features_remain(self):
  for g in ['male','female']:
   old=reference(g,'alternative');new=read(historical_asset(f'assets/wardrobe/faces/{g}_alternative_head.png'));body=read(historical_asset(f'base_{g}.png'));target=refine.skin_median(body);oldlab=refine.skin_median(old);newlab=refine.skin_median(new)
   scale=np.array([100/255,1,1]);self.assertLess(np.linalg.norm((newlab-target)*scale),np.linalg.norm((oldlab-target)*scale),g)
   if g=='female':self.assertLess(np.linalg.norm((newlab-oldlab)*scale),3)
  old=reference('male','alternative');new=read(ROOT/'assets/wardrobe/faces/male_alternative_head.png')
  for box in [(425,130,458,148),(488,128,521,146),(463,163,487,187),(455,199,495,211)]:
   x0,y0,x1,y1=box;a=old[y0:y1,x0:x1,:3]@np.array([.2126,.7152,.0722]);b=new[y0:y1,x0:x1,:3]@np.array([.2126,.7152,.0722]);self.assertGreater(np.corrcoef(a.ravel(),b.ravel())[0,1],.90,box)
 def test_thigh_correction_preserves_alpha_and_skin_texture(self):
  old=read(ROOT/'tests/fixtures/targeted-face-references/female_inner_thighs.png');new=read(historical_asset('base_female.png'))[823:1105,340:605];self.assertTrue(np.array_equal(old[:,:,3],new[:,:,3]));delta=new[:,:,:3].astype(int)-old[:,:,:3].astype(int)
  self.assertTrue(np.all(delta>=0));self.assertTrue(np.all(delta<=np.array([14,10,7])));changed=np.any(delta,axis=2);self.assertGreater(changed.sum(),5000);self.assertGreater(np.mean(delta[changed,0]),3)
  a=old[:,:,:3].astype(float).mean(2);b=new[:,:,:3].astype(float).mean(2);core=ndi.binary_erosion(changed,iterations=3)
  before=(a-ndi.gaussian_filter(a,1))[core];after=(b-ndi.gaussian_filter(b,1))[core];self.assertGreater(np.std(after)/np.std(before),.95)
 def test_male_ear_cuts_are_local_and_approved_placements_and_rear_stay(self):
  fixture=json.loads((ROOT/'tests/fixtures/paper-doll-targeted-fix.json').read_text());catalog=support.audit.catalog();self.assertEqual({i['id']:i.get('placementByGender') for i in catalog['items'] if i['slot']=='hair'},fixture['hair_placements_before'])
  for e in fixture['files']:
   if '/hair/' not in e['path']:continue
   if e['changed']:
    a=read(ROOT/e['path']);old_alpha=np.array(Image.open(ROOT/'tests/fixtures/targeted-face-references'/ (Path(e['path']).stem+'-alpha.png')))
    self.assertTrue(np.all(a[:,:,3]<=old_alpha));self.assertEqual(digest(a[:,:,:3][a[:,:,3]>0].tobytes()),e['retained_source_rgb_sha256'])
    allowed=np.zeros(a.shape[:2],bool)
    for y,l,r in e['allowed_alpha_runs']:allowed[y,l:r]=True
    self.assertLess(a[:,:,3][allowed].sum(),old_alpha[allowed].sum()*.95)
    # Original upper hair/forehead silhouette must remain byte-exact.
    i=next(i for i in catalog['items'] if i.get('genderVariants',{}).get('male','').split('?')[0]==e['path']);p=i['placementByGender']['male'];yy=np.arange(a.shape[0])[:,None]
    self.assertTrue(all(y>=int((125-p['y'])*a.shape[0]/p['height'])-2 for y,l,r in e['allowed_alpha_runs']))
   elif e['path'].endswith('_rear.png'):self.assertEqual(e['sha256'],e['before_sha256'])
