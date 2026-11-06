# Wardrobe refinement — 2026-11-06

Implemented on the production archive wardrobe with live text and the approved avatar renderer.

- Generated four visibly different material surfaces: scuffed common brown leather, improved olive hospital leather/brass, rare scorched charcoal leather/steel, experimental burgundy velvet. Each catalogue tile now uses its surface behind the weapon AND labels. Artwork sources and SHA-256 hashes are in `assets/ui/wardrobe/provenance.json`.
- Rifle contact shadows follow the transparent weapon silhouette in the tablet and catalogue.
- Main document aligned with the weapon catalogue header, wider content column, paper action labels with actual generated paperclip/thumbtack artwork, torn corners and red edge stains. Keyboard focus and 44px minimum target retained.
- Removed Inspect action and moved its description, damage explanation and critical multiplier to the approval sheet, followed by the approved signature and red seal. Text remains HTML.
- Appearance rails replace equipment rails using the prepared face/hair/beard icons and a return control. Both genders keep identical full-body geometry across appearance tabs. The engine's wider rifle canvas now respects its native scale and the body frame stays centered. Removed the inherited bottom margin that cropped the hair.
- Catalogue groups legacy AKS duplicates to one representative per rarity, preferring the inspected/equipped/upgraded copy. Inventory instances and progress are preserved, not deleted. Other weapon models remain available.
- No base avatar, head, hairstyle, beard, weapon sprite or rig asset was edited. Before/after runtime receipt preserves the two changed historically tracked files.

Validation: 118 Node tests passed. Six existing production browser scenarios passed (both genders and weapon poses, draft/apply/reload, upgrades/modules/Absolute, manual battle, six viewport sizes from 320×568 to 1680×1000). Two new browser scenarios passed for unchanged full-body geometry/rail replacement and legacy duplicate grouping/inline description/document bounds. Responsive and grouping scenarios also passed again after the pinned labels and full-tile surfaces were added. JavaScript syntax and `git diff --check` passed. The broad historical browser suite was not rerun for this UI refinement.

An initial new-test assertion assumed an AKS substring in the approved sprite filename; corrected to assert the actual four rarity records and six total weapon cards. The source sprite filename is intentionally unchanged.

Screenshots: [desktop](desktop-rare.png), [female appearance](appearance-female.png), [male appearance](appearance-male.png), [mobile appearance](mobile-appearance.png). Mobile screenshot documents appearance mode; weapon details remain an explicit drawer on narrow screens. Short desktop viewports may scroll the info document to retain readable type.
