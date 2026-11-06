# Weapon presentation and archive controls — 2026-11-06

User-requested follow-up to the rarity artwork refinement:

- AKS previews are larger in both catalogue and info tablet. The approved thumbnail is unchanged; CSS now sizes by width instead of constraining its transparent canvas to a short image box. Catalogue rifle records have additional image height. The avatar and its held weapon are untouched.
- Added All / Rifles / Pistols / Melee filters. Filtering changes only the visible catalogue; it does not equip, remove, delete or change a weapon instance. Switching filters selects a valid record and closes the narrow-screen detail drawer.
- Moved the live silver/parts/experimental-component counters into Form 404 in the header. Three generated transparent icons use matching archive inventory art. Values update from the existing resources on every render; the duplicate footer counter was removed.
- Enlarged institution logo and text on the info tablet.
- The approval sheet displays the approved signature at a readable size, with a black redaction beside the responsible doctor label. The original red seal moved up/left onto clear paper. Neither signature/seal artwork nor the paper's folded corner was changed. On short desktop viewports the info sheet can scroll.
- Equipment visibility buttons show a centered light eye when visible, a crossed gray eye when hidden, and remain operable to show the item again. Existing temporary visibility state and aria-pressed semantics are preserved.
- Scrollbars across the wardrobe use dark metal tracks, brass double borders and aged-material thumbs in Chromium/WebKit. Firefox receives the matching native scrollbar colors. Stable gutters reserve space on the catalogue and details.

Validation: all 9 `tests.test_weapon_archive` production browser scenarios passed, including all three filters, live resource values, eye hide/show, draft/apply/reload, upgrades/modules/Absolute, weapon poses for both genders, full-body framing, legacy-instance grouping and responsive layouts at 1680×1000, 1280×800, 1024×768, 768×1024, 390×844 and 320×568. Final changes after this run are the full melee tab label and scrollbar gutter/display only; responsive and filter checks rerun separately. JavaScript syntax and whitespace checks passed. No avatar image or rig was edited; no broad historical test suite was rerun for these UI changes.

[Desktop](desktop-rare.png) · [Female appearance](appearance-female.png) · [Male appearance](appearance-male.png) · [Mobile appearance](mobile-appearance.png)
