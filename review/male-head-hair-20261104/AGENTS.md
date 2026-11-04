# Preserved approval evidence

`Mxx-Hyy-approved.png` files are immutable approved reference compositions. Some are hardlinked to the preserved session originals. Never overwrite these files in place or change them to match a new renderer. Future changes require a new versioned approval folder.

`before/` contains exact runtime sources from the baseline commit, used to verify preservation and explicit approval history. Keep their bytes unchanged.

Browser proofs (`game-*.png`, `mobile-*.png`, check JSON files) may be regenerated from the real runtime. They must not replace the approved references. Runtime hair layers live separately under `assets/wardrobe/hair/male-reviewed/`.
