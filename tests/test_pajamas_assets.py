"""Protect approved art, unchanged avatar anatomy and full-canvas registration.

Derivative geometry may improve after visual fitting; these contracts deliberately
avoid fixing a garment's contour or an intermediate extraction's checksum.
"""
import hashlib
import json
from pathlib import Path
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'review' / 'pajamas-implementation-20261111'
RUNTIME = ROOT / 'assets' / 'wardrobe' / 'clothing' / 'patient' / 'pajamas'
FRAME = (941, 1672)
GARMENTS = ('top-idle', 'top-melee', 'top-rifle', 'pants', 'footwear')
REGISTERED = (*GARMENTS, 'mask-footwear')
THUMBNAILS = ('thumb-top', 'thumb-pants', 'thumb-footwear')
APPROVED_BOARDS = {
    'male': ('approved-male-concept.png',
             '1943dc7c37aa15bff0cda043d37d80845b92a894045b6ba720197a278c2c5885'),
    'female': ('approved-source.png',
               '6a48666ca4650bb37e120b83eaff16edce3225c2c6aeb0b8070d031a6981d669'),
}
APPROVED_BODIES = {
    'male': 'b40a31b26dcf9aeea1dad02091228377330c9bb3af3a4b9669cfcc67247fc41d',
    'female': 'a27b499c03fc15c4788ae3a651483a36463f28b1f034178feccdaa852e7e50f9',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solid_bounds(alpha):
    return alpha.point(lambda value: 255 if value >= 128 else 0).getbbox()


class PajamasAssetTests(unittest.TestCase):
    def assert_transparent_rgba(self, image, label):
        self.assertEqual(image.mode, 'RGBA', label)
        alpha = image.getchannel('A')
        self.assertEqual(alpha.getextrema(), (0, 255), label)
        self.assertIsNotNone(solid_bounds(alpha), label + ' has no substantial artwork')
        return alpha

    def test_original_approved_boards_and_avatar_anatomy_are_preserved_exactly(self):
        capture = json.loads((REVIEW / 'references' / 'capture-metadata.json').read_text())
        for gender, (filename, expected) in APPROVED_BOARDS.items():
            with self.subTest(gender=gender, kind='approved board'):
                self.assertEqual(digest(REVIEW / gender / filename), expected)
            with self.subTest(gender=gender, kind='unchanged avatar'):
                self.assertEqual(capture['approvedBaseSha256']['base_' + gender + '.png'],
                                 APPROVED_BODIES[gender])
                path = ROOT / ('base_' + gender + '.png')
                self.assertEqual(digest(path), APPROVED_BODIES[gender])
                with Image.open(path) as image:
                    self.assertEqual(image.size, FRAME)
                    self.assertEqual(image.mode, 'RGBA')

    def test_registered_garments_and_owned_foot_masks_keep_the_original_full_canvas(self):
        for gender in APPROVED_BODIES:
            for name in REGISTERED:
                with self.subTest(gender=gender, image=name):
                    path = REVIEW / gender / 'registered' / (name + '.png')
                    with Image.open(path) as image:
                        self.assertEqual(image.format, 'PNG')
                        self.assertEqual(image.size, FRAME)
                        alpha = self.assert_transparent_rgba(image, str(path))
                        self.assertIsNone(alpha.crop((0, 0, FRAME[0], 220)).getbbox(),
                                          str(path) + ' includes pixels over the original head')
        # Large originals belong to review. Publishing another PNG copy of each
        # registered layer needlessly duplicates the compact runtime artwork.
        self.assertEqual(sorted(str(path.relative_to(RUNTIME)) for path in RUNTIME.rglob('*.png')), [])

    def test_runtime_layers_preserve_registration_and_thumbnails_have_real_transparency(self):
        for gender in APPROVED_BODIES:
            for name in REGISTERED:
                with self.subTest(gender=gender, runtime=name):
                    path = RUNTIME / gender / (name + '.webp')
                    with Image.open(path) as image:
                        self.assertEqual(image.format, 'WEBP')
                        alpha = self.assert_transparent_rgba(image, str(path))
                        self.assertAlmostEqual(image.width / image.height, FRAME[0] / FRAME[1], delta=.002)
                        runtime_bounds = solid_bounds(alpha)
                        with Image.open(REVIEW / gender / 'registered' / (name + '.png')) as original:
                            source_bounds = solid_bounds(original.getchannel('A'))
                        # Compare the registered position independently of WebP
                        # resolution. Two output pixels allow resampling edges.
                        for index, (actual, expected) in enumerate(zip(runtime_bounds, source_bounds)):
                            runtime_dimension = image.width if index % 2 == 0 else image.height
                            source_dimension = FRAME[index % 2]
                            self.assertAlmostEqual(actual / runtime_dimension, expected / source_dimension,
                                                   delta=2 / runtime_dimension,
                                                   msg=str(path) + ' moved or cropped the registered artwork')
            for name in THUMBNAILS:
                with self.subTest(gender=gender, thumbnail=name):
                    path = RUNTIME / gender / (name + '.webp')
                    with Image.open(path) as image:
                        self.assertEqual(image.format, 'WEBP')
                        self.assertEqual(image.size, (256, 256))
                        self.assert_transparent_rgba(image, str(path))


if __name__ == '__main__':
    unittest.main()
