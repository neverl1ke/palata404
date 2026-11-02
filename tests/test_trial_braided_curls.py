"""Specific regressions for the isolated, removable female trial hairstyle."""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from tests.asset_history import accepted_catalog_snapshot, approved_current_hash

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
        expected=accepted_catalog_snapshot(before);ids={i['id'] for i in expected};self.assertEqual([i for i in after if i['id'] in ids],expected)
        protected=json.loads((ROOT/'review/female-head-standard/manifest.json').read_text())['protected_sha256']
        for path,digest in protected.items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),approved_current_hash(path,digest),path)
        old_hash=hashlib.sha256(subprocess.check_output(['git','show','adffd71:paper-doll.js'],cwd=ROOT)).hexdigest();self.assertEqual(hashlib.sha256((ROOT/'paper-doll.js').read_bytes()).hexdigest(),approved_current_hash('paper-doll.js',old_hash))

    def test_removed_trial_is_absent_but_original_resource_is_retained(self):
        self.assertFalse(any(i['id']==TRIAL for i in catalog((ROOT/'paper-doll-data.js').read_text())))
        entry=json.loads((REPORT/'registration.json').read_text())
        path=ROOT/entry['output']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),entry['sha256'])
        with Image.open(path) as image:self.assertEqual(image.size,(941,1672))

    def test_alpha_margin_and_central_face_opening_are_clear(self):
        entry=json.loads((REPORT/'registration.json').read_text())
        with Image.open(ROOT/entry['output']) as image:
            self.assertEqual(image.mode,'RGBA');self.assertEqual(image.size,(941,1672));a=np.array(image)[:,:,3]
        # A nonzero safe margin proves that no generated tips hit a canvas edge.
        self.assertFalse(a[:3].any());self.assertFalse(a[-3:].any());self.assertFalse(a[:,:3].any());self.assertFalse(a[:,-3:].any())
        # The user explicitly restored the initial source/side-curl shape.
        # Do not enforce the discarded outward-curl edit as an artistic baseline.
        # The central nose/lip opening must still be completely transparent.
        for x,y,right,bottom in [(452,166,497,228)]:
            self.assertFalse(a[y:bottom,x:right].any())
        self.assertFalse(((a>0)&(a<=16)&(ndi.distance_transform_edt(a<32)>4)).any())

    def test_local_edit_preserves_approved_texture_outside_explicit_mask(self):
        source=REPORT/'approved-texture-source.png'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                         '34920119dd7eccfeaa4e1f5054d235cd908b0caadda9559ade3f64aff45c42a6')
        approved=np.array(Image.open(source).convert('RGBA'))
        corrected=np.array(Image.open(REPORT/'generated-source.png').convert('RGBA'))
        mask=np.array(Image.open(REPORT/'local-edit-mask.png').convert('L'))
        self.assertEqual(approved.shape,corrected.shape)
        self.assertTrue(np.array_equal(approved[mask==0],corrected[mask==0]))
        self.assertGreater(np.count_nonzero(np.any(approved!=corrected,axis=2)),1000)
        entry=json.loads((REPORT/'registration.json').read_text())
        self.assertEqual(entry['source_registration'],{'scale':0.3,'x':325.5,'y':-6,'part_axis_x':490})

    def test_contour_edit_preserves_canvas_lower_tresses_and_all_pixels_outside_roi(self):
        before=np.array(Image.open(REPORT/'before-contour-source.png').convert('RGBA'))
        after=np.array(Image.open(REPORT/'generated-source.png').convert('RGBA'))
        mask=np.array(Image.open(REPORT/'contour-edit-mask.png').convert('L'))
        self.assertEqual(before.shape,after.shape)
        self.assertTrue(np.array_equal(before[mask==0],after[mask==0]))
        self.assertTrue(np.array_equal(before[:570],after[:570]))
        self.assertTrue(np.array_equal(before[1120:],after[1120:]))
        self.assertGreater(np.count_nonzero(np.any(before!=after,axis=2)),1000)

    def test_saved_browser_evidence_covers_all_female_heads(self):
        result=json.loads((REPORT/'browser-check.json').read_text())
        self.assertEqual(len(result['female_faces_checked']),17)
        self.assertEqual(result['js_errors'],[]);self.assertEqual(result['http_errors'],[])
        for key in ['real_ui_selection','reload','male_exclusion','unequip','patient_trip_independent','protected_game_state_unchanged']:
            self.assertTrue(result[key],key)


if __name__=='__main__': unittest.main()

