# Scene 1 (Seedance mitte animatic) - Reference-Aware Shot Validation Report

Backend: `gemini`  |  Model: `gemini-2.5-flash`  |  Validator: `scripts/validate/shot_validator.py`

Each shot's first/middle/last keyframe was scored by the vision model against the locked character turnarounds (Gabe, Jenny, Leo, Mia, Nina) and a provisional living-room plate (shot 1A storyboard panel). Continuity uses the previous shot's last keyframe as the comparison frame.

Note: when a manifest character is **not visible** in a keyframe, the model reports them as `no_reference` for identity (it can't compare a face that isn't there). The fact that they are missing is still flagged separately in `character_presence.missing` and drives the presence-score failure - that is the real signal for missing/swapped characters.

## Validator findings (TL;DR)

- **1A - FAIL**: missing character(s); wardrobe mismatch (vs manifest)
- **1B - FAIL**: unexpected/extra character(s); wardrobe mismatch (vs manifest)
- **1C - FAIL**: missing characters: Gabe, Jenny
- **1D - FAIL**: missing characters: Jenny, Leo, Mia
- **1G - PASS**: (no issues flagged)
- **1H - FAIL**: environment artifact (indoor lightning)
- **1I - PASS**: (no issues flagged)

## Summary

| Shot | Pass? | Presence | Location | Continuity | Artifacts | Identity (avg) | Wardrobe (avg) | # Reasons |
|------|-------|----------|----------|------------|-----------|----------------|----------------|-----------|
| 1A | **FAIL** | 0.60 | 0.90 | 1.00 | 0.97 | 1.00 | 0.83 | 4 |
| 1B | **FAIL** | 0.83 | 1.00 | 0.83 | 1.00 | 1.00 | 0.83 | 3 |
| 1C | **FAIL** | 0.77 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 2 |
| 1D | **FAIL** | 0.60 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 | 3 |
| 1G | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1H | **FAIL** | 1.00 | 1.00 | 1.00 | 0.80 | 1.00 | 1.00 | 1 |
| 1I | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |

**Total API usage:** 96,219 input tokens + 13,317 output tokens. **Estimated cost:** $0.0622.

## Per-Shot Breakdown

### Shot 1A - FAIL

**Aggregate scores:**
- character_presence: 0.60
- character_identity: Mia: 1.00, Leo: 1.00, Jenny: 1.00
- character_identity (no reference, not scored): Gabe, Nina
- character_wardrobe: Mia: 0.50, Leo: 1.00, Jenny: 1.00
- character_wardrobe (not visible, not scored): Gabe, Nina
- location_match: 0.90
- continuity: 1.00
- artifacts: 0.97

**Failure reasons:**
- Characters Nina and Gabe are missing from the shot.
- Mia's pose does not match the manifest description of 'legs tucked under on couch'.
- Two expected characters, Nina and Gabe, are missing from the keyframe.
- Mia's pose does not fully match the wardrobe description regarding her legs.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (01-shot-1A-first.jpg)
- presence: 0.60 (observed: Mia, Leo, Jenny | missing: Nina, Gabe | unexpected: none)
- identity[Mia]: 1.00 - Mia's identity matches the turnaround reference.
- identity[Leo]: 1.00 - Leo's identity matches the turnaround reference.
- identity[Jenny]: 1.00 - Jenny's identity matches the turnaround reference.
- identity[Nina]: not visible - Nina is not visible in the keyframe.
- identity[Gabe]: not visible - Gabe is not visible in the keyframe.
- wardrobe[Mia]: 0.50 (expected: casual home wear, legs tucked under on couch) - Mia is wearing casual home wear, but her legs are not tucked under on the couch.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas) - Leo is wearing green dinosaur-pattern pajamas as expected.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, on phone) - Jenny is dressed as a casual teen with dark brown hair and is on her phone.
- wardrobe[Nina]: not visible - Nina is not visible in the keyframe.
- wardrobe[Gabe]: not visible - Gabe is not visible in the keyframe.
- location: 0.80 - The living room matches the location plate, but the lighting and atmosphere are different.
- continuity: n/a (no prior shot or different location)
- artifacts: 0.90 - detected: none - No significant artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Characters Nina and Gabe are missing from the shot.
  - Mia's pose does not match the manifest description of 'legs tucked under on couch'.

**Keyframe mid** (01-shot-1A-mid.jpg)
- presence: 0.60 (observed: Mia, Leo, Jenny | missing: Nina, Gabe | unexpected: none)
- identity[Mia]: 1.00 - Mia's identity matches the turnaround reference perfectly.
- identity[Leo]: 1.00 - Leo's identity matches the turnaround reference perfectly.
- identity[Jenny]: 1.00 - Jenny's identity matches the turnaround reference perfectly.
- identity[Nina]: not visible - Nina is not visible in the keyframe.
- identity[Gabe]: not visible - Gabe is not visible in the keyframe.
- wardrobe[Mia]: 0.50 (expected: casual home wear, legs tucked under on couch) - Mia is wearing casual home wear, but her legs are not tucked under on the couch.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas) - Leo's green dinosaur-pattern pajamas match the manifest description.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, on phone) - Jenny's casual teen attire and ponytail match the manifest description.
- wardrobe[Nina]: not visible - Nina is not visible in the keyframe.
- wardrobe[Gabe]: not visible - Gabe is not visible in the keyframe.
- location: 0.90 - The living room matches the location plate, though the TV content is different and the lighting is slightly brighter.
- continuity: n/a (no prior shot or different location)
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: False
  - Two expected characters, Nina and Gabe, are missing from the keyframe.
  - Mia's pose does not fully match the wardrobe description regarding her legs.

**Keyframe last** (01-shot-1A-last.jpg)
- presence: 0.60 (observed: Mia, Leo, Jenny | missing: Nina, Gabe | unexpected: none)
- identity[Mia]: 1.00 - Mia's identity matches the turnaround reference.
- identity[Leo]: 1.00 - Leo's identity matches the turnaround reference.
- identity[Jenny]: 1.00 - Jenny's identity matches the turnaround reference.
- identity[Nina]: not visible - Nina is not visible in the keyframe.
- identity[Gabe]: not visible - Gabe is not visible in the keyframe.
- wardrobe[Mia]: 0.50 (expected: casual home wear, legs tucked under on couch) - Mia is wearing casual home wear, but her legs are not tucked under on the couch.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas) - Leo is wearing green dinosaur-pattern pajamas as expected.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, on phone) - Jenny is wearing casual teen attire with her hair in a ponytail and is on her phone.
- wardrobe[Nina]: not visible - Nina is not visible in the keyframe.
- wardrobe[Gabe]: not visible - Gabe is not visible in the keyframe.
- location: 1.00 - The living room set matches the location plate, including furniture, layout, and the stormy window view.
- continuity: n/a (no prior shot or different location)
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected.
- keyframe overall_pass: False
  - Characters Nina and Gabe are missing from the shot.
  - Mia's pose does not fully match the wardrobe description regarding her legs.

</details>

### Shot 1B - FAIL

**Aggregate scores:**
- character_presence: 0.83
- character_identity: Leo: 1.00, Mia: 1.00
- character_wardrobe: Leo: 1.00, Mia: 0.67
- location_match: 1.00
- continuity: 0.83
- artifacts: 1.00

**Failure reasons:**
- An unexpected character, Jenny, is present in the shot.
- Mia's wardrobe does not match the expected wardrobe for this shot.
- Mia's wardrobe is inconsistent with the previous shot.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (02-shot-1B-first.jpg)
- presence: 1.00 (observed: Leo, Mia | missing: none | unexpected: none)
- identity[Leo]: 1.00 - Leo's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas, hugging plush T-Rex) - Leo is wearing green dinosaur-pattern pajamas and hugging a plush T-Rex, matching the manifest.
- wardrobe[Mia]: 1.00 (expected: casual home wear (partial frame edge)) - Mia is wearing casual home wear, consistent with the manifest description.
- location: 1.00 - The living room set, including the couch, TV, window with storm, and lamp, perfectly matches the location plate.
- continuity: 1.00 [same location] - The location, time of day, and visible character wardrobes are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe mid** (02-shot-1B-mid.jpg)
- presence: 0.50 (observed: Mia, Leo, Jenny | missing: none | unexpected: Jenny)
- identity[Leo]: 1.00 - Leo's identity matches the turnaround reference perfectly.
- identity[Mia]: 1.00 - Mia's identity matches the turnaround reference perfectly.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas, hugging plush T-Rex) - Leo is wearing green dinosaur-pattern pajamas and hugging a plush T-Rex, matching the manifest.
- wardrobe[Mia]: 0.00 (expected: casual home wear (partial frame edge)) - Mia is wearing a pink t-shirt with stars and blue jeans, which does not match the 'casual home wear' description from the prior shot's manifest.
- location: 1.00 - The living room set, furniture, and window view match the location plate reference.
- continuity: 0.50 [same location] - Mia's wardrobe is inconsistent with the previous shot, where she was wearing casual home wear, not a pink t-shirt and jeans.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: False
  - An unexpected character, Jenny, is present in the shot.
  - Mia's wardrobe does not match the expected wardrobe for this shot.
  - Mia's wardrobe is inconsistent with the previous shot.

**Keyframe last** (02-shot-1B-last.jpg)
- presence: 1.00 (observed: Leo, Mia | missing: none | unexpected: none)
- identity[Leo]: 1.00 - Leo's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas, hugging plush T-Rex) - Leo is wearing green dinosaur-pattern pajamas and hugging a plush T-Rex, matching the manifest.
- wardrobe[Mia]: 1.00 (expected: casual home wear (partial frame edge)) - Mia is wearing casual home wear, consistent with the manifest description.
- location: 1.00 - The living room set, furniture, and window view with the storm match the location plate exactly.
- continuity: 1.00 [same location] - The location, time of day, and character wardrobes are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1C - FAIL

**Aggregate scores:**
- character_presence: 0.77
- character_identity: Nina: 1.00, Gabe: 1.00, Jenny: 1.00
- character_identity (no reference, not scored): Gabe, Jenny
- character_wardrobe: Nina: 1.00, Gabe: 1.00, Jenny: 1.00
- character_wardrobe (not visible, not scored): Gabe, Jenny
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

**Failure reasons:**
- Gabe is missing from the shot.
- Jenny is missing from the shot.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (03-shot-1C-first.jpg)
- presence: 1.00 (observed: Nina, Gabe, Jenny | missing: none | unexpected: none)
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Gabe]: 1.00 - Gabe's identity, including face, hair, skin tone, and build, is consistent with the turnaround.
- identity[Jenny]: 1.00 - Jenny's identity, including face, hair, skin tone, and build, is consistent with the turnaround.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress, putting on earrings) - Nina is wearing an elegant black formal dress and appears to be putting on earrings, matching the manifest.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background)) - Gabe is wearing a black tuxedo, consistent with the manifest and the wardrobe consistency reference.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail (background, on phone)) - Jenny is dressed in casual teen attire, matching the manifest description.
- location: 1.00 - The living room set, including furniture, layout, and window view, perfectly matches the location plate.
- continuity: 1.00 [same location] - The location and time of day are consistent with the previous shot, despite different characters being present.
- artifacts: 1.00 - detected: none - No visual artifacts, physics violations, or unexpected background figures were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe mid** (03-shot-1C-mid.jpg)
- presence: 1.00 (observed: Nina, Gabe, Jenny | missing: none | unexpected: none)
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Jenny]: 1.00 - Jenny's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress, putting on earrings) - Nina is wearing an elegant black formal dress and appears to be putting on earrings, matching the manifest.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background)) - Gabe is wearing a black tuxedo, consistent with the manifest and the wardrobe consistency reference.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail (background, on phone)) - Jenny is wearing casual clothing and has dark brown hair in a ponytail, matching the manifest.
- location: 1.00 - The living room set, including furniture, layout, and the view outside the window, perfectly matches the location plate.
- continuity: 1.00 [same location] - The location and time of day are consistent with the prior shot, with appropriate changes in characters and their positions.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe last** (03-shot-1C-last.jpg)
- presence: 0.30 (observed: Nina | missing: Gabe, Jenny | unexpected: none)
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Gabe]: not visible - Gabe is not visible in the keyframe.
- identity[Jenny]: not visible - Jenny is not visible in the keyframe.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress, putting on earrings) - Nina is wearing an elegant black formal dress, matching the manifest description.
- wardrobe[Gabe]: not visible - Gabe is not visible in the keyframe.
- wardrobe[Jenny]: not visible - Jenny is not visible in the keyframe.
- location: 1.00 - The living room set, including the lamp and wall decor, matches the location plate perfectly.
- continuity: 1.00 [same location] - The location and time of day are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: False
  - Gabe is missing from the shot.
  - Jenny is missing from the shot.

</details>

### Shot 1D - FAIL

**Aggregate scores:**
- character_presence: 0.60
- character_identity: Gabe: 1.00, Nina: 1.00
- character_identity (no reference, not scored): Jenny, Leo, Mia
- character_wardrobe: Gabe: 1.00, Nina: 1.00
- character_wardrobe (not visible, not scored): Jenny, Leo, Mia
- location_match: 0.97
- continuity: 1.00
- artifacts: 1.00

**Failure reasons:**
- Mia is missing from the shot.
- Leo is missing from the shot.
- Jenny is missing from the shot.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (04-shot-1D-first.jpg)
- presence: 0.60 (observed: Gabe, Nina | missing: Mia, Leo, Jenny | unexpected: none)
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Mia]: not visible - Mia is not visible in the keyframe.
- identity[Leo]: not visible - Leo is not visible in the keyframe.
- identity[Jenny]: not visible - Jenny is not visible in the keyframe.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (slightly rumpled), checking watch) - Gabe is wearing a black tuxedo and checking his watch, matching the manifest description.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress) - Nina is wearing an elegant black formal dress, consistent with the manifest and prior shot reference.
- wardrobe[Mia]: not visible - Mia is not visible in the keyframe.
- wardrobe[Leo]: not visible - Leo is not visible in the keyframe.
- wardrobe[Jenny]: not visible - Jenny is not visible in the keyframe.
- location: 1.00 - The living room set, including furniture, layout, and window view, perfectly matches the location plate.
- continuity: 1.00 [same location] - The location, time of day, and visible wardrobe elements are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: False
  - Mia is missing from the shot.
  - Leo is missing from the shot.
  - Jenny is missing from the shot.

**Keyframe mid** (04-shot-1D-mid.jpg)
- presence: 0.60 (observed: Gabe, Nina | missing: Mia, Leo, Jenny | unexpected: none)
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Mia]: not visible - Mia is not visible in the keyframe.
- identity[Leo]: not visible - Leo is not visible in the keyframe.
- identity[Jenny]: not visible - Jenny is not visible in the keyframe.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (slightly rumpled), checking watch) - Gabe is wearing a black tuxedo and checking his watch, matching the manifest description.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress) - Nina is wearing an elegant black formal dress, consistent with the manifest and prior shot reference.
- wardrobe[Mia]: not visible - Mia is not visible in the keyframe.
- wardrobe[Leo]: not visible - Leo is not visible in the keyframe.
- wardrobe[Jenny]: not visible - Jenny is not visible in the keyframe.
- location: 0.90 - The living room set matches the location plate, though the background is slightly out of focus.
- continuity: 1.00 [same location] - The location, time of day, and wardrobe for Nina and Gabe are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: False
  - Mia is missing from the shot.
  - Leo is missing from the shot.
  - Jenny is missing from the shot.

**Keyframe last** (04-shot-1D-last.jpg)
- presence: 0.60 (observed: Gabe, Nina | missing: Mia, Leo, Jenny | unexpected: none)
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Mia]: not visible - Mia is not visible in the keyframe.
- identity[Leo]: not visible - Leo is not visible in the keyframe.
- identity[Jenny]: not visible - Jenny is not visible in the keyframe.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (slightly rumpled), checking watch) - Gabe is wearing a black tuxedo, consistent with the manifest.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress) - Nina is wearing an elegant black formal dress, consistent with the manifest and prior shot.
- wardrobe[Mia]: not visible - Mia is not visible in the keyframe.
- wardrobe[Leo]: not visible - Leo is not visible in the keyframe.
- wardrobe[Jenny]: not visible - Jenny is not visible in the keyframe.
- location: 1.00 - The living room set, including the couch, lamp, and window with storm, matches the location plate.
- continuity: 1.00 [same location] - The location, time of day, and Nina's wardrobe are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: False
  - Mia is missing from the shot.
  - Leo is missing from the shot.
  - Jenny is missing from the shot.

</details>

### Shot 1G - PASS

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Mia: 1.00, Leo: 1.00, Nina: 1.00, Gabe: 1.00
- character_wardrobe: Mia: 1.00, Leo: 1.00, Nina: 1.00, Gabe: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (05-shot-1G-first.jpg)
- presence: 1.00 (observed: Mia, Leo, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's identity matches the turnaround reference perfectly.
- identity[Leo]: 1.00 - Leo's identity matches the turnaround reference perfectly.
- identity[Nina]: 1.00 - Nina's identity matches the turnaround reference perfectly.
- identity[Gabe]: 1.00 - Gabe's identity matches the turnaround reference perfectly.
- wardrobe[Mia]: 1.00 (expected: casual home wear (OTS, back of head visible)) - Mia's casual home wear matches the manifest and consistency reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas (OTS, PJs visible)) - Leo's green dinosaur-pattern pajamas match the manifest and consistency reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (background, preparing)) - Nina's elegant black formal dress matches the manifest and consistency reference.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background, preparing)) - Gabe's black tuxedo matches the manifest and consistency reference.
- location: 1.00 - The living room set matches the location plate with all key landmarks present and consistent.
- continuity: 1.00 [same location] - Continuity with the prior shot is maintained, including location, time of day, and character wardrobe.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe mid** (05-shot-1G-mid.jpg)
- presence: 1.00 (observed: Mia, Leo, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's identity matches the turnaround reference perfectly.
- identity[Leo]: 1.00 - Leo's identity matches the turnaround reference perfectly.
- identity[Nina]: 1.00 - Nina's identity matches the turnaround reference perfectly.
- identity[Gabe]: 1.00 - Gabe's identity matches the turnaround reference perfectly.
- wardrobe[Mia]: 1.00 (expected: casual home wear (OTS, back of head visible)) - Mia's casual home wear matches the manifest description and consistency reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas (OTS, PJs visible)) - Leo's green dinosaur-pattern pajamas match the manifest description and consistency reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (background, preparing)) - Nina's elegant black formal dress matches the manifest description and consistency reference.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background, preparing)) - Gabe's black tuxedo matches the manifest description and consistency reference.
- location: 1.00 - The living room set matches the location plate with all key landmarks present and consistent.
- continuity: 1.00 [same location] - Continuity with the prior shot is maintained; the location, time of day, and character wardrobes are consistent.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe last** (05-shot-1G-last.jpg)
- presence: 1.00 (observed: Mia, Leo, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's identity matches the turnaround reference perfectly, with consistent facial features, hair, skin tone, and build.
- identity[Leo]: 1.00 - Leo's identity matches the turnaround reference perfectly, with consistent facial features, hair, skin tone, and build.
- identity[Nina]: 1.00 - Nina's identity matches the turnaround reference perfectly, with consistent facial features, hair, skin tone, and build.
- identity[Gabe]: 1.00 - Gabe's identity matches the turnaround reference perfectly, with consistent facial features, hair, skin tone, and build.
- wardrobe[Mia]: 1.00 (expected: casual home wear (OTS, back of head visible)) - Mia's casual home wear matches the manifest description and the wardrobe consistency reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas (OTS, PJs visible)) - Leo's green dinosaur-pattern pajamas match the manifest description and the wardrobe consistency reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (background, preparing)) - Nina's elegant black formal dress matches the manifest description and the wardrobe consistency reference.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background, preparing)) - Gabe's black tuxedo matches the manifest description and the wardrobe consistency reference.
- location: 1.00 - The living room set matches the location plate, including furniture, layout, and the stormy window view.
- continuity: 1.00 [same location] - Continuity with the prior shot is maintained; the location, time of day, and character wardrobes are consistent.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1H - FAIL

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Mia: 1.00
- character_wardrobe: Mia: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 0.80

**Failure reasons:**
- Lightning is depicted inside the room, which is a significant physical artifact.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (06-shot-1H-first.jpg)
- presence: 1.00 (observed: Mia | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Mia]: 1.00 (expected: casual home wear, looking up at off-screen parents) - Mia is wearing casual home wear, which matches the manifest description.
- location: 1.00 - The living room set, including the couch, lamp, and window, matches the location plate reference.
- continuity: 1.00 [same location] - The location and time of day are consistent with the previous shot, and Mia's wardrobe is appropriate for the continuity.
- artifacts: 1.00 - detected: none - No visual artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe mid** (06-shot-1H-mid.jpg)
- presence: 1.00 (observed: Mia | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Mia]: 1.00 (expected: casual home wear, looking up at off-screen parents) - Mia is wearing casual home wear, consistent with the manifest description.
- location: 1.00 - The living room set, including the couch, lamp, and window with a storm, matches the location plate.
- continuity: 1.00 [same location] - The location and time of day are consistent with the previous shot.
- artifacts: 0.40 - detected: lightning inside room - A lightning bolt is visible inside the room, overlapping the wall and lamp, which is a physical impossibility.
- keyframe overall_pass: False
  - Lightning is depicted inside the room, which is a significant physical artifact.

**Keyframe last** (06-shot-1H-last.jpg)
- presence: 1.00 (observed: Mia | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Mia]: 1.00 (expected: casual home wear, looking up at off-screen parents) - Mia is wearing casual home wear, consistent with the manifest description.
- location: 1.00 - The background elements visible are consistent with the living room location plate, including the lamp and general room ambiance.
- continuity: 1.00 [same location] - The time of day and general room dressing are consistent with the prior shot, which also took place in the living room.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1I - PASS

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Gabe: 1.00, Nina: 1.00
- character_wardrobe: Gabe: 1.00, Nina: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (07-shot-1I-first.jpg)
- presence: 1.00 (observed: Gabe, Nina | missing: none | unexpected: none)
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (conflicted expression)) - Gabe is wearing a black tuxedo that matches the wardrobe consistency reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (sharp glare)) - Nina is wearing an elegant black formal dress that matches the wardrobe consistency reference.
- location: 1.00 - The living room set, furniture, and window view with the storm outside perfectly match the location plate.
- continuity: 1.00 [same location] - The location and time of day are consistent with the prior shot, which also took place in the living room during a storm.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe mid** (07-shot-1I-mid.jpg)
- presence: 1.00 (observed: Gabe, Nina | missing: none | unexpected: none)
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (conflicted expression)) - Gabe is wearing a black tuxedo that matches the wardrobe consistency reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (sharp glare)) - Nina is wearing an elegant black formal dress that matches the wardrobe consistency reference.
- location: 1.00 - The living room set, including the couch, TV, lamp, and window with a storm outside, matches the location plate.
- continuity: 1.00 [same location] - The location and time of day (night with a storm) are consistent with the prior shot, which also showed the living room at night.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe last** (07-shot-1I-last.jpg)
- presence: 1.00 (observed: Gabe, Nina | missing: none | unexpected: none)
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (conflicted expression)) - Gabe is wearing a black tuxedo that matches the wardrobe consistency reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (sharp glare)) - Nina is wearing an elegant black formal dress that matches the wardrobe consistency reference.
- location: 1.00 - The living room set, including the couch, TV, lamp, and window with the storm, matches the location plate.
- continuity: 1.00 [same location] - The location and general ambiance are consistent with the prior shot, maintaining the stormy night setting.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>
