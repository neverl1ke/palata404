# Female knife wrist restoration

The owner reported that the previous weapon-state fix lost the female wrist pose. The neutral open hand was incorrectly reused for the knife.

Restore the original authored right-arm, closed-hand and foreground-grip PNGs byte-for-byte from the historical source revision recorded in `sources.json`. The existing female rig's calibrated mesh registers the wrist and knife together. Only that arm and the shared complete knife are rendered over the current neutral body, after removing its original arm with the original arm-coverage mask. The composed pose shares one breathing surface. Idle and rifle stay unchanged.

`wrist-before-after.jpg` compares actual native game renders, `female-melee-restored.jpg` shows the full pose, and `restored-wrist-reference.png` protects the closed hand from returning to the neutral open-hand shape. Six tests verify source identity, the exact wrist image after weapon changes, unchanged other body regions, neutral restoration, rifle reference frames, reload and breathing. `runtime-receipt.json` preserves the previous runtime hashes.
