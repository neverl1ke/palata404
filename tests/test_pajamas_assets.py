"""Protect approved art, unchanged avatar anatomy and full-canvas registration.

Derivative geometry may improve after visual fitting; these contracts deliberately
avoid fixing a garment's contour or an intermediate extraction's checksum.
"""
import hashlib
import json
from pathlib import Path
import unittest

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'review' / 'pajamas-implementation-20261111'
RUNTIME = ROOT / 'assets' / 'wardrobe' / 'clothing' / 'patient' / 'pajamas'
FINISH = ROOT / 'review/pajama-art-release-20261114'
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


def registered_art(gender, name):
    return FINISH / 'originals' / gender / (name + '.png')


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
                    path = registered_art(gender, name)
                    with Image.open(path) as image:
                        self.assertEqual(image.format, 'PNG')
                        self.assertEqual(image.size, FRAME)
                        if name == 'mask-footwear':
                            # Rear cloth surrounds the unchanged foot. There is
                            # deliberately no native-body erasure in this mask.
                            alpha = image.getchannel('A')
                            self.assertIsNone(alpha.getbbox())
                        else:
                            alpha = self.assert_transparent_rgba(image, str(path))
                        self.assertIsNone(alpha.crop((0, 0, FRAME[0], 220)).getbbox(),
                                          str(path) + ' includes pixels over the original head')
        # Approved shirts use the exact PNG bytes. Browser WebP decoders can
        # quantize translucent-edge RGB even when the stored image is lossless.
        expected = sorted(f'{g}/{p.name}' for g in APPROVED_BODIES
                          for p in (FINISH / 'candidate' / g).glob('*.png'))
        self.assertEqual(sorted(str(path.relative_to(RUNTIME)) for path in RUNTIME.rglob('*.png')), expected)

    def test_runtime_layers_preserve_registration_and_thumbnails_have_real_transparency(self):
        for gender in APPROVED_BODIES:
            for name in REGISTERED:
                with self.subTest(gender=gender, runtime=name):
                    path = RUNTIME / gender / (name + '.png')
                    with Image.open(path) as image:
                        self.assertEqual(image.format, 'PNG')
                        if name == 'mask-footwear':
                            self.assertIsNone(image.getchannel('A').getbbox())
                            continue
                        alpha = self.assert_transparent_rgba(image, str(path))
                        self.assertAlmostEqual(image.width / image.height, FRAME[0] / FRAME[1], delta=.002)
                        runtime_bounds = solid_bounds(alpha)
                        with Image.open(registered_art(gender, name)) as original:
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

    def test_historical_approved_shirt_masters_are_preserved_exactly(self):
        approval = json.loads((ROOT / 'review/shirt-approved-20261113/approval.json').read_text())
        records = approval['artwork']
        self.assertEqual(len(records), 12)
        self.assertEqual({(r['gender'], r['part'], r['pose']) for r in records},
                         {(g, part, pose) for g in APPROVED_BODIES
                          for part in ('top', 'back') for pose in ('idle', 'melee', 'rifle')})
        for record in records:
            with self.subTest(layer=record['runtime']):
                master = ROOT / record['master']
                self.assertEqual(digest(master), record['sourceSha256'])
                original = FINISH / 'originals' / record['gender'] / master.name
                self.assertEqual(original.read_bytes(), master.read_bytes())

    def test_native_finish_preserves_all_source_geometry_and_shipped_png_bytes(self):
        finish = json.loads((FINISH / 'finish-manifest.json').read_text())
        release = json.loads((FINISH / 'release-manifest.json').read_text())
        self.assertEqual(len(finish['records']), 20)
        self.assertEqual(len(release['artwork']), 26)
        for record in finish['records']:
            source, candidate = ROOT / record['source'], ROOT / record['candidate']
            runtime = RUNTIME / record['gender'] / (record['part'] + '.png')
            self.assertEqual(digest(source), record['sourceSha256'])
            self.assertEqual(digest(candidate), record['candidateSha256'])
            self.assertEqual(runtime.read_bytes(), candidate.read_bytes())
            with Image.open(source) as before, Image.open(runtime) as after:
                self.assertEqual(after.size, FRAME)
                self.assertEqual(before.mode, 'RGBA')
                self.assertEqual(after.mode, 'RGBA')
                self.assertIsNone(ImageChops.difference(before.getchannel('A'), after.getchannel('A')).getbbox())
                # A cloth finish must not replace the design or lighting with
                # a broad recolour, or introduce light contour fringes.
                diff = ImageChops.difference(before.convert('RGB'), after.convert('RGB'))
                self.assertLessEqual(max(v[1] for v in diff.getextrema()), 8)
        for g in APPROVED_BODIES:
            for pose in ('idle', 'melee', 'rifle'):
                with Image.open(RUNTIME / g / f'keep-pants-{pose}.png') as mask:
                    self.assertEqual(mask.size, FRAME)
                    alpha = mask.getchannel('A')
                    cutoff = 801 if g == 'female' else 841
                    self.assertEqual(alpha.crop((0, cutoff, FRAME[0], FRAME[1])).getextrema(), (255, 255))
                    self.assertEqual(alpha.crop((350, 0, 600, FRAME[1])).getextrema(), (255, 255))


if __name__ == '__main__':
    unittest.main()
