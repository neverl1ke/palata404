# Avatar shoulders, beard layering and complete-frame loading

The owner requested three Main fixes: restore the female rifle trapezius silhouette, draw facial hair beneath scalp hair, and stop default/partial avatars appearing while loading saved or newly selected appearance.

The rifle PNG is unchanged. Its neutral-head body mask now preserves the original authored shoulder coverage below the neck transition. Coverage is checked on all female heads. Beard source PNGs are also unchanged; catalog order is 8, below front hair (9+).

The animated renderer prepares changes offscreen and publishes a complete frame once ready. Until then its previous frame remains visible. Static clothing holds cloned previous layers until the selected images, recoloring and body masks decode and the replacements can be painted. Startup has no default male `src` in HTML. Both paths discard superseded requests.

Tests intentionally delay head, hair and mask requests and monitor displayed frames during swaps/reload. They also check actual pixels where hair overlaps beard, all female rifle shoulder coverage, both weapon cycles, the restored female wrist, appearance persistence and mobile controls. Runtime before/after receipts retain the prior approved records.

Validation: 17 Python browser/asset tests passed, 94 game logic tests passed, 12 avatar math tests passed. Delayed-network frame traces, saved appearance reload, all female rifle shoulder coverage, beard/hair overlap, weapon cycles and the female knife grip passed.

The project reference audit also passed with zero missing static references.
