"""Independent observable contracts; never import the asset preparation code.

These tests cannot certify artistic anatomy. They detect a confirmed neck-fringe
regression, incomplete compositing and accidental edits outside the repair ROI.
"""
import hashlib
import json
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
KINDS = ['asian','young','exhausted','elder','alternative',
         'ginger_soft','goth_septum','goth_black_lips']


def composite(kind):
    base=Image.open(ROOT/'base_female.png').convert('RGBA')
    head=Image.open(ROOT/f'assets/wardrobe/faces/female_{kind}_head.png').convert('RGBA')
    mask=Image.open(ROOT/f'assets/wardrobe/faces/masks/female_{kind}_body.png').getchannel('A')
    body=base.copy()
    body.putalpha(ImageChops.multiply(base.getchannel('A'),mask))
    return np.array(Image.alpha_composite(body,head))


def neck_reversals(alpha):
    # A plain neck cross-section has one skin interval, with an outward-fading
    # AA edge. A second alpha rise >8/255 outside it is a separate visible rim.
    # ROI excludes ears, piercing, jaw and garment straps; 8 allows integer AA
    # quantisation, not a second line (confirmed rises reach 255/255).
    a=alpha.astype('int16')
    right=np.diff(a[218:255,474:570],axis=1)>8
    left=np.diff(a[218:255,375:475],axis=1)<-8
    return int(right.sum()+left.sum())


def neck_steps(alpha):
    bounds=[np.flatnonzero(row>=128)[[0,-1]] for row in alpha[218:281]]
    return int(np.max(np.abs(np.diff(np.array(bounds),axis=0))))


class IndependentFemaleFaceTests(unittest.TestCase):
    def test_repaired_necks_do_not_have_a_second_alpha_rim(self):
        for kind in ['ginger_soft','goth_septum']:
            self.assertEqual(neck_reversals(composite(kind)[:,:,3]),0,kind)

    def test_neck_detector_rejects_the_real_pre_fix_regression(self):
        # Real old bytes, not a generated fake tailored to the cleanup code.
        root=ROOT/'review/female-faces-independent-audit/before-assets'
        base=Image.open(ROOT/'base_female.png').convert('RGBA')
        for kind in ['ginger_soft','goth_septum']:
            head=Image.open(root/f'female_{kind}_head.png').convert('RGBA')
            mask=Image.open(ROOT/f'assets/wardrobe/faces/masks/female_{kind}_body.png').getchannel('A')
            body=base.copy();body.putalpha(ImageChops.multiply(base.getchannel('A'),mask))
            self.assertGreater(neck_reversals(np.array(Image.alpha_composite(body,head))[:,:,3]),20)

    def test_all_neck_silhouettes_have_no_abrupt_join_steps(self):
        # The immutable body's own largest step in this neck/trapezius ROI is
        # 3px. The former joins jumped 5..15px, unrelated to artistic ear detail.
        for kind in KINDS:
            self.assertLessEqual(neck_steps(composite(kind)[:,:,3]),3,kind)
        root=ROOT/'review/female-faces-independent-audit/before-assets'
        base=Image.open(ROOT/'base_female.png').convert('RGBA')
        for kind in ['asian','young','exhausted','elder','alternative','ginger_soft']:
            head=Image.open(root/f'female_{kind}_head.png').convert('RGBA')
            mask=Image.open(ROOT/f'assets/wardrobe/faces/masks/female_{kind}_body.png').getchannel('A')
            body=base.copy();body.putalpha(ImageChops.multiply(base.getchannel('A'),mask))
            self.assertGreater(neck_steps(np.array(Image.alpha_composite(body,head))[:,:,3]),3,kind)

    def test_each_actual_mask_preserves_solid_neck_and_lower_body(self):
        base=np.array(Image.open(ROOT/'base_female.png').convert('RGBA'))
        for kind in KINDS:
            a=composite(kind)
            self.assertTrue(np.array_equal(a[286:],base[286:]),kind)
            self.assertEqual(ndi.label(a[:300,:,3]>=128,np.ones((3,3)))[1],1,kind)
            self.assertTrue(np.all(a[225:250,450:500,3]==255),kind)
            # The approved immutable base itself has alpha=253 below y259.
            # Demand no *additional* transparency there, not a covert body edit.
            self.assertTrue(np.all(a[250:286,450:500,3]>=base[250:286,450:500,3]),kind)
            # Four background checks use independently computed source-over.
            for color in [(255,255,255),(85,85,85),(0,0,0),(0,255,0)]:
                alpha=a[225:250,450:500,3:4]/255
                rgb=np.rint(a[225:250,450:500,:3]*alpha+np.array(color)*(1-alpha))
                self.assertTrue(np.array_equal(rgb,a[225:250,450:500,:3]),(kind,color))

    def test_repairs_preserve_approved_portraits_and_all_protected_assets(self):
        report=ROOT/'review/female-faces-independent-audit'
        changes=json.loads((report/'repair-manifest.json').read_text())
        for entry in changes['repairs']:
            old=np.array(Image.open(report/entry['before']))
            current=np.array(Image.open(ROOT/entry['path']))
            changed=np.any(old!=current,axis=2)
            allowed=np.zeros(changed.shape,bool);allowed[218:286,405:541]=True
            self.assertFalse(np.any(changed&~allowed),entry['path'])
            common=(current[:,:,3]>0)&(old[:,:,3]>0)
            self.assertTrue(np.array_equal(old[:,:,:3][common],current[:,:,:3][common]),entry['path'])
            self.assertTrue(np.array_equal(old[:218],current[:218]),entry['path'])
        for path,digest in changes['protected_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)


if __name__=='__main__': unittest.main()
