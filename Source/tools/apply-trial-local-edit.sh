#!/usr/bin/env bash
# Blend only explicitly approved curl/ear regions, leaving all other source pixels intact.
set -euo pipefail
cd "$(dirname "$0")/.."
r=review/trial-braided-curls
magick -size 979x1606 xc:black -fill white -draw 'roundrectangle 150,425 280,680 20,20 roundrectangle 710,425 830,680 20,20 roundrectangle 285,570 440,1220 15,15 roundrectangle 540,570 710,1220 15,15' -blur 0x8 -depth 8 "$r/local-edit-mask.png"
# Mix straight RGBA, including alpha: source-over would leave the old curl visible.
magick "$r/approved-texture-source.png" "$r/local-jaw-ear-edit.png" "$r/local-edit-mask.png" -channel RGBA -fx 'u[0]*(1-u[2].r)+u[1]*u[2].r' -depth 8 "$r/generated-source.png"
python tools/prepare-trial-braided-curls.py
