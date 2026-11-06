# Document system — 2026-11-06

Reusable native HTML components, a central RU/UK/EN text registry, real supplied paper artwork, and production adapters for the wardrobe and detailed battle protocol.

## Final user corrections applied

- The wardrobe's previous artistic banner, anatomical illustration and original clip remain. Its text now uses the reusable left header and live localization.
- The original clipboard backing, metal clamp, clip, stapled tab, worn borders, reddish stains, approved emblem, doctor signature and approved red seal remain. Hardware is displayed through precise SVG clipping of the original atlas, not regenerated.
- The supplied new paper is an independent layer on BOTH sheets inside that backing. It does not replace the clipboard itself.
- The weapon sheet uses a large CENTER header. The approval/modification sheet is compressed to 150px while retaining its description, weapon damage, damage with permanent character bonuses, critical multiplier, per-instance modification explanation, responsible doctor, redaction, signature and seal.
- Header rows are compact like the supplied example; released height is used for the weapon preview. The signature is raised completely inside the clean paper area, with a verified lower margin. No scrolling is needed inside the weapon tablet at the six verified viewport sizes. The item catalogue remains independently scrollable.
- Only the approved round seal is used. Its rasterized historical inscription stays unchanged, as explicitly requested; rectangular service/status stamps and their live labels localize normally. No substitute round seal is generated.

## Deliverables

- `DocumentHeader`: `document-header`, left/center variants, department, document type, controlled scale, optional stamps.
- `DocumentPaper`: `document-paper`, 9-slice edges and separately proportional center material.
- `DocumentStamp`: `document-stamp`, localized rectangular stamps and the exact approved round seal.
- `DocumentLayout`: `document-layout`, creates a header from attributes and preserves the supplied body content.
- `localization.js`: central registry, `PalataI18n.t`, `setLocale`, locale event, safe dynamic interpolation, persisted independent language preference.
- `document-demo.html`: both variants, three languages, widths 320/640/960px, standard/custom departments, and a full document.
- `docs/DOCUMENT_SYSTEM.md`: integration instructions, API examples, resources, approved-art exception and future consumers.
- `assets/ui/documents/provenance.json`: source SHA-256 and unchanged approved graphic hashes.

## Demonstration

[HEADER-LEFT, RU](header-left-ru.png) · [UK](header-left-uk.png) · [EN](header-left-en.png)

[HEADER-CENTER, RU](header-center-ru.png) · [UK](header-center-uk.png) · [EN](header-center-en.png)

[Full demo, RU](demo-ru.png) · [UK](demo-uk.png) · [EN](demo-en.png)

[Wardrobe, 1800×1070](wardrobe-1800x1070.png) · [1680×1000](wardrobe-1680x1000.png) · [1280×800](wardrobe-1280x800.png) · [1024×768](wardrobe-1024x768.png) · [390×844](wardrobe-390x844.png) · [320×568](wardrobe-320x568.png)

[Applied detailed battle protocol](battle-protocol.png). The compact reward summary retains its existing layout and actions.

`geometry.json` records actual browser geometry and scroll sizes. Browser tests additionally cover 1024×768 and all three locales. Demo text, department names and status stamps remain HTML text; assets do not change with language.

## Verification

- 118 Node logic/avatar tests passed.
- 16 distinct browser scenarios passed across the final run and focused correction reruns: four document-system cases, nine wardrobe/weapon integration cases, compact victory layout, detailed protocol mobile controls, and archived-result reopening.
- The document case exercises both headers × 3 locales × 3 widths, fixed emblem placement, controlled text bounds, literal custom text/XSS handling, long department labels, layout API, locale persistence, unchanged game state, and production integration.
- The no-scroll case checks both sheets, description, doctor/signature area, seal and actions for RU/UK/EN at 1800×1070, 1680×1000, 1280×800, 1024×768, 390×844 and 320×568.
- Material integrity test passed: recorded resources match SHA-256, approved originals are unchanged, and the SVG center contains the exact supplied JPEG bytes.
- Static project audit passed with zero missing references. JavaScript syntax, Python compilation, and `git diff --check` passed.

The broad run caught the rotated seal extending 3px into its reserved fold margin. Its position was corrected by 4px and the affected test plus all document cases passed on rerun. Earlier Russian-only assertions were changed to assert the selected locale after localization was introduced.

Physical mobile devices, Firefox/Safari, and Telegram WebView were not tested. Other game text and saved story/item names have not been mass translated. Other dossiers/archives are ready to adopt these components but were not rewritten in this stage.
