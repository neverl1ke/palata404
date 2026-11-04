"""Accepted male review exports: transparency, registration and provenance."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/male-head-hair-20261104'
class MaleReviewAssets(unittest.TestCase):
 def test_all48_approved_fits_have_native_transparent_layers_and_versioned_sources(self):
  data=json.loads((REPORT/'integration.json').read_text());self.assertEqual(len(data['records']),48)
  self.assertEqual(len({(x['head'],x['number']) for x in data['records']}),48)
  for entry in data['records']:
   with self.subTest(head=entry['head'],hair=entry['number']):
    self.assertLess(entry['mean_abs_error'],.5)
    self.assertLessEqual(entry['central_face_error'],1)
    for part in entry['layers']:
     self.assertIsInstance(part['renderOrder'],int)
     path,version=part['source'].split('?v=');raw=(ROOT/path).read_bytes()
     self.assertEqual(hashlib.sha256(raw).hexdigest()[:8],version)
     im=Image.open(ROOT/path);self.assertEqual(im.size,(941,1672));self.assertEqual(im.mode,'RGBA')
     a=np.array(im)[:,:,3];self.assertFalse(a[360:].any());self.assertFalse(a[:,:300].any());self.assertFalse(a[:,645:].any())
     self.assertFalse(a[120:265,439:507].any(),'Central face must not be copied into a hair or edge layer')
     if part['id']=='skin-edge':self.assertIs(part['recolor'],False);self.assertLess((a>0).sum(),3000)
 def test_body_and_head_rgb_are_preserved(self):
  data=json.loads((REPORT/'integration.json').read_text())
  for gender,digest in data['body_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/f'base_{gender}.png').read_bytes()).hexdigest(),digest)
  cat=json.loads(__import__('subprocess').check_output(['node','-e',"const fs=require('fs'),vm=require('vm');console.log(vm.runInNewContext(fs.readFileSync('paper-doll-data.js','utf8')+';JSON.stringify(PAPER_DOLL_ITEMS)'))"],cwd=ROOT,text=True))
  for face,source in data['config']['headSources'].items():
   original=next(x for x in cat if x['id']==face)['genderVariants']['male'].split('?')[0]
   a=np.array(Image.open(ROOT/original).convert('RGBA'));b=np.array(Image.open(ROOT/source.split('?')[0]).convert('RGBA'))
   self.assertTrue(np.array_equal(a[:,:,:3],b[:,:,:3]));self.assertTrue(np.array_equal(a[:205],b[:205]));self.assertTrue(np.array_equal(a[286:],b[286:]))
