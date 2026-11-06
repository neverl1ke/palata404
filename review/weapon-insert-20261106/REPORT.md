# Wardrobe visual revision

Implemented the user's follow-up corrections after the intermediate review:

- Russian-only document copy; no language picker and no saved-locale effect. Both reusable header variants remain real UI text over approved artwork.
- Original anatomical banner paper, emblem, clamp, seal, autograph, weapon sprite and avatars remain unchanged. Header-left rules restored on the original banner.
- Independent I–IV badges have thicker ink, larger Russian rarity labels and separate spacing; no skew. All catalogue cards keep one size, rifle stock clears the left colored stripe.
- Weapon and Roman upgrade scale moved upward, two descriptive rows replace the temporarily removed module-counter button. Module installation logic remains intact.
- Lower insert retains its reviewed dimensions. Larger round seal, building engraving, archived case/character fields and handwritten annotations follow the supplied reference. Signature uses a proportional SVG window over the exact approved autograph. Fields constrain long text rather than overlapping neighbours.
- Aged leather under catalogue; deeply battered wood with fingernail gouges, old paint and red stains inside the exposed original steel perimeter.

Validation: 118 Node tests passed. Fifteen distinct browser/material tests passed across full and focused reruns. The first full browser run had one obsolete all-typewriter-font assertion; that assertion now permits only the explicitly requested handwriting fields, and its focused rerun passed. Six viewport sizes (1800, 1680, 1280, 1024, 390 and 320), four rarity mappings, uniform card geometry, stock clearance, stamp-label spacing, field bounds, no tablet scrolling, upgrades/modules/absolute, draft/apply/reload and both avatar genders were exercised. Graphic hashes and cache keys verified. See logs and screenshots in this folder.

The later user request deferred localization; previous multilingual demo expectations were replaced with Russian-only / ignored-saved-locale assertions. No full-game translation was attempted.

Static project audit passed with zero missing resource references.
