from tests.avatar_revision_contract import assert_female_donor_revision
from tests.avatar_revision_contract import assert_ownership_only,OWNERSHIP_PATHS
"""Historical a6 derivative pass. Its immutable dd61b2d runtime is the fixture;
current reference-arm behavior has separate source-point and Canvas tests.
Original PNG bytes and derivative alpha limits remain checked in this checkout."""
import hashlib,json,subprocess,unittest
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
class ExactReferenceTests(unittest.TestCase):
 def test_every_original_png_and_rig_is_unchanged(self):
  for line in subprocess.check_output(['git','ls-tree','-r','02cae62','avatar-core/assets','avatar-core/rigs','base_male.png','base_female.png'],cwd=ROOT,text=True).splitlines():
   meta,path=line.split('\t')
   if path in OWNERSHIP_PATHS:assert_ownership_only(self,path,'02cae62');continue
   if path=='avatar-core/rigs/female_rig.json':
    assert_female_donor_revision(self,json.loads(subprocess.check_output(['git','show','02cae62:'+path],cwd=ROOT)),json.loads((ROOT/path).read_text()));continue
   data=(subprocess.check_output(['git','show','dd61b2d:'+path],cwd=ROOT) if path=='avatar-core/rigs/male_rig.json' else (ROOT/path).read_bytes());self.assertEqual(hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest(),meta.split()[2],path)
 def test_changes_only_remove_true_eight_connected_low_alpha_islands(self):
  records=json.loads((ROOT/'review/male-exact-reference-pass/alpha-cleanup.json').read_text());total=0
  for r in records:
   a=np.array(Image.open(ROOT/r['source']));b=np.array(Image.open(ROOT/r['output']));self.assertEqual(a.shape,b.shape)
   labels,n=ndi.label(a[:,:,3]>0,structure=np.ones((3,3)));expected=a.copy()
   for i in range(1,n+1):
    mask=labels==i
    if mask.sum()<=20 and a[:,:,3][mask].max()<=8:expected[mask]=0
   self.assertTrue(np.array_equal(expected,b));changed=np.any(a!=b,axis=2);total+=int(changed.sum());self.assertTrue(np.array_equal(a[~changed],b[~changed]));self.assertLessEqual(int(a[:,:,3][changed].max()),8)
  self.assertEqual(total,41)
 def test_archived_a6_runtime_changes_only_surfaces_and_the_new_male_knife(self):
  old=json.loads(subprocess.check_output(['git','show','02cae62:avatar-core/male-preview.json'],cwd=ROOT));new=json.loads(subprocess.check_output(['git','show','dd61b2d:avatar-core/male-preview.json'],cwd=ROOT));overrides=new.pop('poseArtSurfaces');new['weapons']['melee']=old['weapons']['melee'];self.assertEqual(old,new)
  self.assertEqual(set(overrides),{'art-front-pistol-right','art-rifle-left'})
  original=json.loads(subprocess.check_output(['git','show','02cae62:avatar-core/male-preview.json'],cwd=ROOT))['weapons']['melee'];knife=json.loads(subprocess.check_output(['git','show','dd61b2d:avatar-core/male-preview.json'],cwd=ROOT))['weapons']['melee']
  for key in ['size','primary','image','scale','angle','art']:original.pop(key,None);knife.pop(key,None)
  self.assertEqual(original,knife,'IDs, class, ordering, support and other knife settings must remain unchanged')
  engine=subprocess.check_output(['git','show','02cae62:avatar-core/engine.mjs'],cwd=ROOT,text=True)
  engine=engine.replace('this.image(art.image).then(',"this.image(malePreview?.poseArtSurfaces?.['art-' + pose + '-' + side] || art.image).then(").replace('this.image(art.frontImage).then(',"this.image(malePreview?.poseArtSurfaces?.['art-front-' + pose + '-' + side] || art.frontImage).then(")
  self.assertEqual(engine,subprocess.check_output(['git','show','dd61b2d:avatar-core/engine.mjs'],cwd=ROOT,text=True))
 def test_archived_independent_knife_anchor_is_inside_opaque_handle_and_blade_points_down(self):
  cfg=json.loads(subprocess.check_output(['git','show','dd61b2d:avatar-core/male-preview.json'],cwd=ROOT))['weapons']['melee'];im=Image.open(ROOT/'avatar-core'/cfg['image']);self.assertEqual(im.mode,'RGBA');self.assertEqual(list(im.size),cfg['size']);a=np.array(im);x,y=map(round,cfg['primary']);self.assertGreaterEqual(int(a[y,x,3]),240);self.assertEqual(cfg['angle']+195,335);self.assertIsNone(cfg['support']);self.assertGreater(im.height,im.width*3);self.assertTrue(np.all(a[a[:,:,3]==0]==0))
 def test_reference_pixels_are_not_runtime_assets(self):
  for p in (ROOT/'avatar-core/assets/male/exact-pass').glob('*.png'):
   self.assertIn(hashlib.sha256(p.read_bytes()).hexdigest(),[r['output_sha256'] for r in json.loads((ROOT/'review/male-exact-reference-pass/alpha-cleanup.json').read_text())])
if __name__=='__main__':unittest.main()
