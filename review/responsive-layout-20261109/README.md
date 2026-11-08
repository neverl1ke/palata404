# Responsive layout correction (unpublished)

## Scope

- Reflow the game HUD in landscape/short windows, keep sidebars scrollable,
  and bound ordinary dialogs to the usable viewport.
- Use a scrollable wardrobe body with stable header/footer, two columns where
  space permits, and stacked portrait panels on narrow phones.
- Open equipment details above the wardrobe in compact layouts. The Back
  control stays reachable while the approved paper illustration scrolls.
- Stop shrinking weapon documents to viewport height. Place their existing
  actions below the illustration with at least 44px-high touch targets.
- Preserve all image assets, avatar layers, state, combat and save mechanics.

The responsive overrides intentionally load after the existing style sheets.
No orientation lock or device-specific user-agent detection is used.

## Verification

Passed locally: 106 game-logic tests, 12 avatar-runtime tests, all root JavaScript
syntax checks, Python compileall, 11 existing asset integrity tests, and discovery
of 207 unique Python tests. The tracked-file dependency audit passed after the
new files were staged.

Browser verification is pending. Chromium in this executor fails before any
page loads with `process_singleton_posix.cc:297 socket() Operation not permitted`,
including after an approved escalated launch. This is not a browser test pass.
The complete Python/browser suite and actual iOS Safari/Android WebView checks
have not been completed. No screenshots are claimed as evidence. A second browser environment could not
reach this checkout’s local server, so it did not validate the changes either.

Run the new isolated regressions with:

    PALATA_BROWSER_PATH=/usr/bin/chromium python -m unittest tests.test_responsive_wardrobe tests.test_general_responsive -v

Then run the repository's complete checks from `.github/workflows/checks.yml`.
The new wardrobe test saves screenshots under `test-results/responsive/`.
It covers portrait-to-landscape resizing, short desktop windows, detail/back,
apply/close and actual center-point hit targets. The general test covers HUD,
sidebars and five common dialogs. The Python shard runner includes both classes.

## Integration

Review and visually validate the `fix/responsive-phone-layout` branch before
merging. This change is not deployed and does not alter the live game.
