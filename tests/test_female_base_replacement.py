"""Current approved base: independent source/portrait/join regression checks."""
import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'review/female-base-replacement'
KINDS = ['asian','young','exhausted','elder','alternative',
         'ginger_soft','goth_septum','goth_black_lips']


def read(path): return np.array(Image.open(path).convert('RGBA'))


def composite(kind):
    base = Image.open(ROOT/'base_female.png').convert('RGBA')
    head = Image.open(ROOT/f'assets/wardrobe/faces/female_{kind}_head.png').convert('RGBA')
    mask = Image.open(ROOT/f'assets/wardrobe/faces/masks/female_{kind}_body.png').getchannel('A')
    body = base.copy(); body.putalpha(ImageChops.multiply(base.getchannel('A'), mask))
    return np.array(Image.alpha_composite(body, head))


class FemaleBaseReplacementTests(unittest.TestCase):
    def test_supplied_original_and_all_non_noise_pixels_are_preserved(self):
        source = REPORT/'source/approved-base.png'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
            '9d4fda6cb00ca911d7dc6a29fe10204b7ba44012ffc7b5734a2c63e6c0eed0ae')
        old, new = read(source), read(ROOT/'base_female.png')
        self.assertEqual(new.shape, (1672,941,4))
        changed = np.any(old != new, axis=2)
        self.assertGreater(changed.sum(), 4000)  # real contaminated input
        self.assertTrue(np.all(old[:,:,3][changed] <= 5))
        self.assertTrue(np.all(new[changed] == 0))
        self.assertTrue(np.array_equal(new[~changed], old[~changed]))

    def test_new_body_has_no_detached_faint_pixels_or_saturated_export_fringe(self):
        a = read(ROOT/'base_female.png'); alpha = a[:,:,3]
        labels, n = ndi.label(alpha > 0, np.ones((3,3)))
        self.assertFalse(np.any(ndi.maximum(alpha, labels, np.arange(1,n+1)) <= 16))
        rgb = a[:,:,:3].astype(int); r,g,b = rgb.transpose(2,0,1)
        bad = (alpha > 0)&(alpha <= 16)&(((r>180)&(g<85)&(b<85))|((r>170)&(g>145)&(b<90)&(g>b*2)))
        self.assertEqual(int(bad.sum()), 0)
        self.assertEqual(int(((alpha>0)&(alpha<=16)&(ndi.distance_transform_edt(alpha<32)>3)).sum()),0)

    def test_all_eight_faces_ears_and_piercings_keep_exact_released_pixels(self):
        for kind in KINDS:
            rel = f'assets/wardrobe/faces/female_{kind}_head.png'
            before, current = read(REPORT/'before-assets'/rel), read(ROOT/rel)
            self.assertTrue(np.array_equal(before[:218],current[:218]), kind)
            changed = np.any(before != current,axis=2)
            ys, xs = np.where(changed)
            self.assertGreaterEqual(int(ys.min()),218,kind)
            self.assertLess(int(ys.max()),286,kind)
            self.assertTrue(np.all((xs>=405)&(xs<=541)),kind)

    def test_all_necks_have_single_rim_and_restore_the_actual_new_body(self):
        base = read(ROOT/'base_female.png')
        def steps(alpha):
            bounds = [np.flatnonzero(row>=128)[[0,-1]] for row in alpha[218:281]]
            return int(np.max(np.abs(np.diff(bounds,axis=0))))
        # The new supplied trapezius has a natural 4px/row slope. Demand no
        # worse transition than that actual source, not the old body's shape.
        source_step = steps(base[:,:,3])
        self.assertEqual(source_step,4)
        for kind in KINDS:
            a = composite(kind); alpha = a[:,:,3].astype(int)
            self.assertTrue(np.array_equal(a[286:],base[286:]),kind)
            self.assertLessEqual(steps(alpha),source_step,kind)
            self.assertEqual(int((np.diff(alpha[218:255,474:570],axis=1)>8).sum()),0,kind)
            self.assertEqual(int((np.diff(alpha[218:255,375:475],axis=1)<-8).sum()),0,kind)
            self.assertTrue(np.all(alpha[225:250,450:500]==255),kind)
            self.assertTrue(np.all(alpha[250:286,450:500]>=base[250:286,450:500,3]),kind)

    def test_released_masks_and_heads_are_versioned_and_other_art_is_unchanged(self):
        manifest = json.loads((REPORT/'replacement-manifest.json').read_text())
        catalog = (ROOT/'paper-doll-data.js').read_text()
        self.assertEqual(len(manifest['files']),17)
        for entry in manifest['files']:
            digest = hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()
            self.assertEqual(digest,entry['sha256'],entry['path'])
            self.assertIn(entry['path']+'?v='+digest[:8],catalog)
        self.assertEqual(len(manifest['protected_sha256']),30)  # 47 art files minus the 17 authorised replacements
        self.assertIn('base_male.png',manifest['protected_sha256'])
        self.assertIn('assets/wardrobe/faces/male_asian_head.png',manifest['protected_sha256'])
        for path,digest in manifest['protected_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)


if __name__ == '__main__': unittest.main()
