#!/usr/bin/env bash
# Local inner-contour edit only; retain the accepted cap, outer shape and lower tresses.
set -euo pipefail
cd "$(dirname "$0")/.."
r=review/trial-braided-curls
magick -size 979x1606 xc:black -fill white -draw 'roundrectangle 295,600 435,1070 20,20 roundrectangle 550,600 685,1070 20,20' -blur 0x8 -depth 8 "$r/contour-edit-mask.png"
magick "$r/before-contour-source.png" "$r/contour-edit-source.png" "$r/contour-edit-mask.png" -channel RGBA -fx 'u[0]*(1-u[2].r)+u[1]*u[2].r' -depth 8 "$r/generated-source.png"
python tools/prepare-trial-braided-curls.py
python - <<'PY'
import json,hashlib
from pathlib import Path
r=Path('review/trial-braided-curls');p=r/'registration.json';d=json.loads(p.read_text());d['contour_edit']={'base':'review/trial-braided-curls/before-contour-source.png','base_sha256':hashlib.sha256((r/'before-contour-source.png').read_bytes()).hexdigest(),'patch':'review/trial-braided-curls/contour-edit-source.png','mask':'review/trial-braided-curls/contour-edit-mask.png','rebuild':'bash tools/apply-trial-contour-edit.sh','scope':'inner side mass and foreground strand separation; cap, ears and lower tresses retained from previous source'};p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
PY
