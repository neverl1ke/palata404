# Approved facial hair and weapon-state repair

Owner approved all ten facial-hair styles on each of M01–M16 and requested Main integration, the hairstyle color palette, and correct idle/knife/rifle transitions for both avatars.

- `integration-manifest.json`: 160 exact approved native PNG SHA256s and 10 derived thumbnails. The approved canvas remains 941×1672; bodies, faces and source artwork are unchanged.
- `M01-approval.json` … `M16-approval.json`: individual approval snapshots. M11's local lift applies only to M11.
- `runtime-receipt.json` and `before/`: exact previous and current runtime hashes, preserving historical approval checks without rewriting old manifests.
- `weapon-states.jpg`, individual pose screenshots, and mobile screenshots: actual game renderer evidence.

The appearance slot has independent saved beard selection and color across Patient/Trip outfits. It uses all 25 existing hairstyle palette choices. Beard color never changes hair or skin; recoloring preserves source alpha. A female selection hides facial hair and retains the saved male choice.

Male idle previously kept the rifle rig active. Female "no weapon" art also kept rifle-positioned arms. Idle now displays the approved neutral body, rifle retains the exact approved renderer, and knife has a separate relaxed state. The female knife uses the current approved neutral body and the complete shared knife, with original fingers in front of the grip. The empty archived female rig is not used as a body. Canceled appearance updates no longer leave a hidden canvas when a rapid change returns to the previous selection.

Tests cover exact asset provenance, 160 face/style resolutions, the complete color palette's alpha preservation, independent colors, both loadouts and genders, removal/reload, mobile controls, idle-body pixels, repeated and rapid knife/rifle/idle transitions, and approved rifle frames at breathing phases. Existing static-clothing fallback remains in place for outfits without authored weapon-pose sleeves.
