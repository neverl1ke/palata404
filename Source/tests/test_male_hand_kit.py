"""Independent authoring-kit invariants; deliberately does not certify hand anatomy."""
from pathlib import Path
import hashlib,importlib.util,json,tempfile,unittest
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];KIT=ROOT/'review/male-hand-art-kit';CORE=ROOT/'avatar-core'
spec=importlib.util.spec_from_file_location('delivery',ROOT/'tools/validate-male-hand-delivery.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class MaleHandKitTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.contract=json.loads((KIT/'hand-contract.json').read_text());cls.rig=json.loads((CORE/'rigs/male_rig.json').read_text())
 def test_archived_kit_hashes_match_its_historical_runtime_7854994(self):
  rows=json.loads((KIT/'protected-runtime.json').read_text());self.assertGreater(len(rows),100)
  for r in rows:
   import subprocess
   archived=subprocess.check_output(['git','show','7854994:'+r['path']],cwd=ROOT)
   self.assertEqual(hashlib.sha256(archived).hexdigest(),r['sha256'],r['path'])
 def test_all_masks_and_templates_keep_exact_canvas_and_new_art_count_is_zero(self):
  self.assertEqual(self.contract['new_art_count'],0);self.assertEqual(len(self.contract['cases']),3)
  for c in self.contract['cases']:
   folder=KIT/'Hands'/c['id']
   for name in ['edit-region.png','wrist-blend-weight.png','old-skin-remove-mask.png']:
    im=Image.open(folder/name);self.assertEqual(im.size,(941,1672));self.assertEqual(im.mode,'L')
   for path in c['candidate_paths']:
    im=Image.open(KIT/path);self.assertEqual(im.size,(941,1672));self.assertEqual(im.mode,'RGBA');self.assertIsNone(im.getbbox(),path)
 def test_masks_include_wrist_grip_and_protect_shoulder_elbow(self):
  for c in self.contract['cases']:
   region=np.array(Image.open(KIT/'Hands'/c['id']/'edit-region.png'))
   for key in ['wrist','grip']:
    x,y=np.rint(c['anchors_pose'][key]).astype(int);self.assertEqual(int(region[y,x]),255,(c['id'],key))
   for key in ['shoulder','elbow']:
    x,y=np.rint(c['anchors_pose'][key]).astype(int);self.assertEqual(int(region[y,x]),0,(c['id'],key))
 def test_skin_removal_and_protected_alpha_conserve_reference_without_repaint(self):
  for c in self.contract['cases']:
   folder=KIT/'Hands'/c['id'];a=np.array(Image.open(folder/'reference-arm-full.png'));b=np.array(Image.open(folder/'protected-arm-reference.png'));remove=np.array(Image.open(folder/'old-skin-remove-mask.png')).astype(int);reg=np.array(Image.open(folder/'edit-region.png'))
   self.assertLessEqual(int(np.abs(a[:,:,3].astype(int)-b[:,:,3].astype(int)-remove).max()),1)
   self.assertTrue(np.array_equal(a[reg==0],b[reg==0]));v=b[:,:,3]>0;self.assertTrue(np.array_equal(a[:,:,:3][v],b[:,:,:3][v]))
 def test_bind_maps_actual_source_wrist_and_grip_and_seam_follows_forearm(self):
  for c in self.contract['cases']:
   m=c['bind_hand'];mat=np.array([[m[0],m[2],m[4]],[m[1],m[3],m[5]],[0,0,1]])
   self.assertTrue(np.allclose(mat@np.array(c['inverse_bind_hand']),np.eye(3),atol=1e-9))
   for key in ['wrist','grip']:self.assertTrue(np.allclose((mat@np.r_[c['source_'+key],1])[:2],c['anchors_pose'][key],atol=1e-6),(c['id'],key))
   axis=np.array(c['anchors_pose']['wrist'])-c['anchors_pose']['elbow'];axis/=np.linalg.norm(axis);self.assertTrue(np.allclose(axis,c['forearm_axis']))
 def test_validator_rejects_empty_or_cropped_or_alpha1_outside_region(self):
  result=mod.validate(KIT,KIT);self.assertFalse(result['technical_valid']);self.assertEqual(sum('empty placeholder' in e for e in result['errors']),6)
  with tempfile.TemporaryDirectory() as td:
   delivery=Path(td);c=self.contract['cases'][0];p=delivery/c['candidate_paths'][0];p.parent.mkdir(parents=True)
   Image.new('RGBA',(10,10)).save(p);self.assertTrue(any('941x1672' in e for e in mod.validate(KIT,delivery)['errors']))
   a=Image.new('RGBA',(941,1672));a.putpixel((0,0),(1,1,1,1));a.save(p);self.assertTrue(any('including alpha1' in e for e in mod.validate(KIT,delivery)['errors']))
if __name__=='__main__':unittest.main()
