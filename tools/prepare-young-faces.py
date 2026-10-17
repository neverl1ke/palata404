"""Clean the supplied young head/neck overlays; never synthesize face pixels.
Usage: python tools/prepare-young-faces.py /path/to/palata404_young_faces_preview.zip
Dependencies: Pillow, numpy, scipy. Full source canvas and RGB detail are preserved.
"""
import argparse, hashlib, json, zipfile
from io import BytesIO
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]

def prepare(archive, gender, shift_x):
    name = f'{gender}_young_head_full_canvas.png'
    raw = archive.read(name)
    im = Image.open(BytesIO(raw)).convert('RGBA')
    if im.size != (941, 1672):
        raise ValueError(f'{name}: unexpected canvas {im.size}')
    rgba = np.array(im)
    alpha = rgba[:, :, 3].astype(float) / 255
    # Retain only the connected head, remove the supplied chest/shoulder mask.
    alpha[263:] = 0
    labels, _ = ndi.label(alpha > .5)
    head = labels == labels[100, 470]
    head = ndi.binary_opening(ndi.binary_fill_holes(head), iterations=1)
    # Restrict smoothing to the alpha boundary, leaving the opaque face intact.
    smooth = ndi.gaussian_filter(head.astype(float), sigma=.85)
    smooth = np.clip((smooth - .08) / .84, 0, 1)
    core = ndi.binary_erosion(head, iterations=3)
    smooth[core] = 1
    # Only neck remains below y=245; feather before the clavicles begin.
    left, right = ((427, 542) if gender == 'male' else (443, 540))
    smooth[245:, :left] = 0
    smooth[245:, right:] = 0
    ramp = np.clip((263 - np.arange(1672)) / 18, 0, 1)
    smooth *= ramp[:, None]
    # Remove dark matte contamination only at semi-transparent outer pixels.
    # Copy nearest opaque source colour, never blur or repaint facial detail.
    _, indices = ndi.distance_transform_edt(~core, return_indices=True)
    nearest = rgba[indices[0], indices[1], :3]
    edge = (smooth > 0) & ~core
    lum = rgba[:, :, :3].mean(axis=2)
    dirty = edge & (lum < nearest.mean(axis=2) * .85)
    rgba[dirty, :3] = nearest[dirty]
    rgba[:, :, 3] = np.rint(smooth * 255).astype('uint8')
    rgba[rgba[:, :, 3] == 0] = 0
    cleaned = Image.fromarray(rgba)
    # Integer registration, no resampling or changes to approved body geometry.
    result = Image.new('RGBA', (941, 1672))
    result.paste(cleaned, (shift_x, 0))
    path = ROOT / 'assets/wardrobe/faces' / f'{gender}_young_head.png'
    result.save(path, optimize=True)
    return dict(gender=gender,source=name,source_sha256=hashlib.sha256(raw).hexdigest(),
        output=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        registration=dict(x=shift_x,y=0,scale=1),bbox=result.getbbox(),
        matte_pixels_cleaned=int(dirty.sum()))

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('archive');args=parser.parse_args()
    with zipfile.ZipFile(args.archive) as archive:
        print(json.dumps([prepare(archive,'male',-10),prepare(archive,'female',-18)],indent=2))
