"""Derive full-resolution colour/detail finishes without changing garment geometry.

Use the registered PNG masters, never earlier processed candidates. Luminance
detail is bounded and alpha-aware; no resampling or invented weave is used.
"""
from pathlib import Path
import hashlib
import json
import shutil
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parents[1]
D = R / 'review/pajama-art-release-20261114'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sources = json.loads((D / 'sources.json').read_text())
records = []
for gender, parts in sources['sources'].items():
    for part, path in parts.items():
        original = D / f'originals/{gender}/{part}.png'
        assert sha(original) == sources['sha256'][path]
        src = np.array(Image.open(original).convert('RGBA'))
        dst = src.copy()
        if part != 'mask-footwear':
            rgb = src[:, :, :3].astype(np.float32) / 255
            alpha = src[:, :, 3].astype(np.float32) / 255
            lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
            luma = rgb @ np.array([.2126, .7152, .0722], np.float32)
            saturation = rgb.max(2) - rgb.min(2)
            cloth = np.clip((.23 - saturation) / .10, 0, 1)
            is_shoe = 'footwear' in part
            if is_shoe:
                # Preserve warm rubber and stitching; cool only the grey upper.
                cloth *= np.clip((12 - lab[:, :, 2]) / 7, 0, 1)
                if part == 'footwear':
                    yy = np.arange(src.shape[0])[:, None]
                    bottom = np.max(np.where(alpha > .5, yy, 0), axis=0)
                    cloth *= np.clip((bottom[None, :] - yy - 7) / 3, 0, 1)
                da, db = -.35, -1.9
                strength, limit = 0., 0.
            elif part == 'pants':
                da, db = -.20, (-.8 if gender == 'male' else -1.2)
                strength = .10 if gender == 'male' else .05
                limit = 2.
            else:
                da, db = -.15, -.35
                strength, limit = ((.10 if part == 'top-rifle' else .18), 2.) if part.startswith('top-') else (0., 0.)
            lab[:, :, 1] += da * cloth
            lab[:, :, 2] += db * cloth
            graded = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            if strength:
                # Normalized opaque neighbourhood cannot pull background RGB in.
                blur_a = cv2.GaussianBlur(alpha, (0, 0), .62)
                low = cv2.GaussianBlur(luma * alpha, (0, 0), .62) / np.maximum(blur_a, .001)
                distance = cv2.distanceTransform((alpha > .98).astype(np.uint8), cv2.DIST_L2, 3)
                interior = np.clip((distance - 1) / 2, 0, 1)
                detail = (luma - low) * 255
                # Leave sub-level noise alone, retain existing stripes and folds.
                detail = np.sign(detail) * np.maximum(np.abs(detail) - .5, 0)
                delta = np.clip(detail * strength, -limit, limit) * interior
                graded += delta[:, :, None] / 255
            dst[:, :, :3] = np.rint(np.clip(graded, 0, 1) * 255).astype('uint8')
            dst[src[:, :, 3] == 0, :3] = src[src[:, :, 3] == 0, :3]
        assert np.array_equal(dst[:, :, 3], src[:, :, 3])
        out = D / f'candidate/{gender}/{part}.png'
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(dst).save(out)
        visible = src[:, :, 3] > 0
        diff = np.abs(dst[:, :, :3].astype(int) - src[:, :, :3].astype(int))
        records.append({'gender': gender, 'part': part, 'source': str(original.relative_to(R)),
                        'historicalSource': path,
                        'sourceSha256': sha(original), 'candidate': str(out.relative_to(R)),
                        'candidateSha256': sha(out), 'size': list(src.shape[1::-1]),
                        'alphaExact': True, 'noResampling': True,
                        'gradeLabAB': [da, db] if part != 'mask-footwear' else [0, 0],
                        'detailGain': strength if part != 'mask-footwear' else 0,
                        'visibleRGBMaxChange': int(diff[visible].max()) if visible.any() else 0,
                        'visibleRGBMeanChange': float(diff[visible].mean()) if visible.any() else 0})

# Carry forward only the reviewed geometry; no new body-erasing mask is made.
for g in ('male', 'female'):
    for pose in ('idle', 'melee', 'rifle'):
        src = D / f'originals/{g}/keep-pants-{pose}.png'
        dst = D / f'candidate/{g}/keep-pants-{pose}.png'
        shutil.copy2(src, dst)
(D / 'finish-manifest.json').write_text(json.dumps({
    'authorization': 'User requested artistic quality/tone finishing followed by main integration.',
    'method': 'Original native PNG -> small Lab cloth-only colour correction + bounded existing luminance detail. Exact alpha/coordinates; no resize, repaint, grain synthesis or deblur claim.',
    'records': records
}, ensure_ascii=False, indent=2))

font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
board = Image.new('RGB', (1800, 1280), '#e8e2d3')
draw = ImageDraw.Draw(board)
for row, g in enumerate(('male', 'female')):
    for col, (part, box) in enumerate((('top-idle', (360, 410, 610, 700)),
                                      ('pants', (330, 900, 580, 1190)),
                                      ('footwear', (495, 1490, 745, 1672)))):
        for side, stage in enumerate(('originals', 'candidate')):
            x = col * 600 + side * 295 + 7
            y = row * 620 + 42
            draw.text((x, y - 28), g + ' ' + part + (' до' if side == 0 else ' після'), font=font, fill='#362e26')
            im = Image.open(D / f'{stage}/{g}/{part}.png').convert('RGBA').crop(box)
            bg = Image.new('RGBA', im.size, '#e8e2d3'); bg.alpha_composite(im)
            board.paste(bg.convert('RGB'), (x, y))
board.save(D / 'native-detail-before-after.png')
print('Prepared 20 native PNG layers and six unchanged keep masks; alpha exact')
