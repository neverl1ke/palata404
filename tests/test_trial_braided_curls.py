"""Specific regressions for the isolated, removable female trial hairstyle."""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'review/trial-braided-curls'
TRIAL = 'hair-trial-braided-curls'


def catalog(text):
    script = "const vm=require('vm'),fs=require('fs');console.log(vm.runInNewContext(fs.readFileSync(0,'utf8')+';JSON.stringify(PAPER_DOLL_ITEMS)'))"
    return json.loads(subprocess.check_output(['node','-e',script],input=text,text=True,cwd=ROOT))


class TrialBraidedCurlsTests(unittest.TestCase):
    def test_existing_catalog_and_approved_art_are_unchanged(self):
        before = catalog(subprocess.check_output(['git','show','adffd71:paper-doll-data.js'],text=True,cwd=ROOT))
        after = catalog((ROOT/'paper-doll-data.js').read_text())
        self.assertEqual([i for i in after if i['id']!=TRIAL],before)
        protected=json.loads((ROOT/'review/female-head-standard/manifest.json').read_text())['protected_sha256']
        for path,digest in protected.items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
        self.assertEqual((ROOT/'paper-doll.js').read_bytes(),subprocess.check_output(['git','show','adffd71:paper-doll.js'],cwd=ROOT))

    def test_trial_is_female_only_full_canvas_and_cache_version_matches_bytes(self):
        items=catalog((ROOT/'paper-doll-data.js').read_text());item=next(i for i in items if i['id']==TRIAL)
        self.assertEqual(item['genders'],['female']);self.assertEqual(item['renderOrder'],9)
        self.assertEqual(item['placementByGender']['female'],{'x':0,'y':0,'width':941,'height':1672})
        path,version=item['genderVariants']['female'].split('?v=')
        self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()[:8],version)
        self.assertTrue(item['availableByDefault']);self.assertTrue(item['fittedToGender'])

    def test_alpha_margin_and_reference_eyes_are_clear(self):
        entry=json.loads((REPORT/'registration.json').read_text())
        with Image.open(ROOT/entry['output']) as image:
            self.assertEqual(image.mode,'RGBA');self.assertEqual(image.size,(941,1672));a=np.array(image)[:,:,3]
        # A nonzero safe margin proves that no generated tips hit a canvas edge.
        self.assertFalse(a[:3].any());self.assertFalse(a[-3:].any());self.assertFalse(a[:,:3].any());self.assertFalse(a[:,-3:].any())
        # These are the reference pupil/iris regions; actual screenshots additionally
        # check the outer eyelids, ears and natural face-framing curls.
        for x,y,right,bottom in [(435,138,443,146),(504,138,512,146)]:
            self.assertFalse(a[y:bottom,x:right].any())
        self.assertFalse(((a>0)&(a<=16)&(ndi.distance_transform_edt(a<32)>4)).any())

    def test_saved_browser_evidence_covers_all_female_heads(self):
        result=json.loads((REPORT/'browser-check.json').read_text())
        self.assertEqual(len(result['female_faces_checked']),17)
        self.assertEqual(result['js_errors'],[]);self.assertEqual(result['http_errors'],[])
        for key in ['real_ui_selection','reload','male_exclusion','unequip','patient_trip_independent','protected_game_state_unchanged']:
            self.assertTrue(result[key],key)


if __name__=='__main__': unittest.main()
