# Paper weapon rarity cards — 2026-11-06

Replaced the previous leather/fabric rarity frames in the weapon catalogue and on the weapon tablet with the four supplied paper-card designs.

- I / gray stripe → common.
- II / olive stripe → improved.
- III / teal stripe → rare.
- IV / burgundy stripe → experimental.

Each is a separate tightly cropped RGBA PNG with transparent corners. Prepared via imagegen background removal from the supplied references, then technical alpha cleanup and transparent-margin trim. Generated source PNGs remain in the workspace; output sizes, source names and SHA-256 hashes are in `assets/ui/wardrobe/rarity-cards/provenance.json`.

The final layout follows the user's subsequent corrections:

- All six catalogue weapon records have identical displayed dimensions, using a 3.1:1 format. At the verified 1800px viewport each is about 342×110px. Mobile records are 280×90px, including in the expanded catalogue.
- The tablet's paper card gets approximately 20% more vertical space than its source proportions when space allows. Earlier excessive stretching and the subsequent overly thin version are replaced.
- The rifle is shifted right: projected stock clearance is at least 8% of the frame width for all four rarities, leaving the colored left strip visible.
- Live item names, availability, selection, upgrades, filters and saved instances remain functional. The supplied printed rarity marks remain part of the card artwork; duplicate visible rarity text is avoided while the live rarity stays available to assistive technology.
- Nonweapon equipment portraits retain the preceding surface. Avatar art, held-weapon sprites, clipboard backing, institution banner, signature and approved seal are unchanged.
- Mobile filter tabs use a horizontal strip and the catalogue reserves a visible row for the uniformly sized cards.

Validation: four focused production browser scenarios passed across the final run and responsive correction rerun: four rarities/one approved sprite, tablet fitting and stock size, responsive catalogue/details/upgrades, and filters/resources/visibility. Responsive checks cover six viewport sizes from 320×568 to 1680×1000. A separate browser check verified equal dimensions for all six cards, all four background mappings, and stock clearance. PNG checks confirm RGBA, transparent corners and tightly trimmed bounds. JavaScript syntax and whitespace checks passed. No broad gameplay test suite was rerun for this artwork/CSS change.

The initial responsive check found an auto-height card collapse in the narrow horizontal flex catalogue. Explicit mobile cross-size and a single-line filter strip corrected it; the responsive test then passed. The image-size assertion now waits for the thumbnail to finish loading before measuring it.

[Common](desktop-common.png) · [Improved](desktop-improved.png) · [Rare](desktop-rare.png) · [Experimental](desktop-experimental.png) · [Mobile tablet](mobile-tablet.png)

[Geometry and stock clearances](geometry-final.json)

PNG exports: [I — Common](../../assets/ui/wardrobe/rarity-cards/common.png) · [II — Improved](../../assets/ui/wardrobe/rarity-cards/improved.png) · [III — Rare](../../assets/ui/wardrobe/rarity-cards/rare.png) · [IV — Experimental](../../assets/ui/wardrobe/rarity-cards/experimental.png)
