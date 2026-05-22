# Scene 1 storyboard regeneration: v3 -> v4

**Goal.** Regenerate the 9 Scene 1 storyboard panels on-model against the
locked Asset Bible turnarounds. The video pipeline draws every shot from
these panels, so on-model panels = on-model shots.

**Approach.**
- Audit v3 panels with `scripts/validate/shot_validator.py` against the locked turnarounds.
- Regenerate via image-to-image with `gemini-3-pro-image-preview`, feeding the locked
  turnaround of every manifest character as a reference and pulling wardrobe / camera /
  key_props straight from `asset-bible/manifests/scene-01.json` (see `scripts/regen_scene01_v4.py`).
- Re-validate v4 with the same validator; iterate panels that still drift (cap 3 attempts).

**Cost.** ~$0.69 total
- 16 image generations × ~$0.04 (gemini-3-pro-image-preview) = ~$0.64
- 2 validator runs (gemini-2.5-flash) = ~$0.047
- Well under the $2 budget; no video generation.

**Validator pass rate.**
- v3: 4/9 passed (`reports/audit-v3/scene-01-audit.md`)
- v4: 8/9 passed (`reports/audit-v4/scene-01-audit.md`)
- 1I (the only v4 fail) passes character_identity 1.0 / 1.0 and wardrobe 1.0 / 1.0;
  it fails only because the validator's fallback location plate is the 1A couch/TV
  view while shot 1I is intentionally set at the front door per the manifest camera.

## Before / after per shot

Local files: `storyboards/v4/scene-01/scene-01-{1A..1I}-start.png`
R2: `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/v4/scene-01/scene-01-<id>-start.png`

| Shot | v3 problem | v4 result |
|------|------------|-----------|
| 1A   | Mia drawn as a toddler with hair in a tight BUN in pink star pajamas; Jenny drawn with Mia's hair (curly down, no ponytail, light skin) | Mia: ~7-9, voluminous dark curly hair DOWN, magenta dotted top + jeans. Jenny: dark hair in ponytail, mid-brown skin, gray hoodie, on phone in armchair. All 5 characters present, lightning correctly OUTSIDE the window. PASS. |
| 1B   | Mia partial-frame still off-model (toddler proportions, bun) | Leo center hugging plush T-Rex in green dino PJs; Mia partial at left shows curly dark hair + magenta top. PASS. |
| 1C   | Acceptable but Nina hair smooth-straight instead of slightly wavy bob | Nina red wavy hair, fair skin, black formal dress, putting on earring, walking left-to-right. Gabe in background with glasses + tuxedo. Jenny on armchair. PASS. |
| 1D   | Gabe missing his signature glasses; previously also had Mia drift in background | Gabe with glasses + scruff in tuxedo, checking watch. Nina in formal dress. Kids on background couch, Jenny in armchair on phone. PASS. |
| 1E   | Jenny rendered with Mia's voluminous curly hair worn down + light skin (totally wrong identity) | Jenny: ponytail, mid-brown skin, gray hoodie, head tilted down at phone (cool blue phone glow). Pixar 3D style, not photoreal. PASS. |
| 1F   | TV-only insert was fine but tagged as artifact | TV insert with cartoon distortion, blue time-warp flash, lightning OUTSIDE through window. PASS. |
| 1G   | Acceptable OTS but tooling flagged it; first v4 attempt had a phantom adult and Gabe with dark skin | OTS from behind Mia (curly dark hair + magenta dotted top, jeans) and Leo (blond + green dino PJs). Background shows Nina (auburn hair, fair skin, black dress) + Gabe (fair skin, glasses, tuxedo). Exactly 4 people. PASS. |
| 1H   | Mia drawn with hair in a high PONYTAIL and pink star pajamas (wrong identity AND wardrobe); indoor-lightning artifact | Mia close-up: voluminous dark curly hair DOWN, magenta dotted top + jeans, big eyes looking up at off-screen parents. Lightning OUTSIDE through window. PASS. |
| 1I   | Acceptable v3 but Gabe lacked glasses | Gabe with black-framed glasses + scruff in tuxedo, conflicted; Nina in formal dress with sharp glare, front door area, lightning outside. Identity + wardrobe perfect; only validator location-plate mismatch (intended door area vs. fallback couch plate). |

## What changed in the code

- `scripts/regen_scene01_v4.py` — new image-to-image regen script. Reads the
  manifest, attaches the locked turnaround of every manifest character as a
  reference image, then synthesizes a prompt that says: identity comes from
  the turnaround, wardrobe / camera / key_props come from the manifest, style
  is the same Pixar/DreamWorks 3D look as the turnarounds, lightning stays
  outside the window. Pinning notes for Mia's hair-down / Gabe's glasses /
  fair skin to fight known drift patterns.
- `asset-bible/manifests/scene-01.json` — every `panel_url` repointed from
  `storyboards/v3/scene-01/...` to `storyboards/v4/scene-01/...`.
- `storyboards/v4/scene-01/scene-01-{1A..1I}-start.png` — 9 regenerated panels.
- `reports/audit-v3/`, `reports/audit-v4/` — before/after validator output.
