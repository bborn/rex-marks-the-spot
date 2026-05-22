# Scene 1 v4 audit - Reference-Aware Shot Validation Report

Backend: `gemini`  |  Model: `gemini-2.5-flash`  |  Validator: `scripts/validate/shot_validator.py`

Each shot's first/middle/last keyframe was scored by the vision model against the locked character turnarounds (Gabe, Jenny, Leo, Mia, Nina) and a provisional living-room plate (shot 1A storyboard panel). Continuity uses the previous shot's last keyframe as the comparison frame.

Note: when a manifest character is **not visible** in a keyframe, the model reports them as `no_reference` for identity (it can't compare a face that isn't there). The fact that they are missing is still flagged separately in `character_presence.missing` and drives the presence-score failure - that is the real signal for missing/swapped characters.

## Validator findings (TL;DR)

- **1A - PASS**: (no issues flagged)
- **1B - PASS**: (no issues flagged)
- **1C - PASS**: (no issues flagged)
- **1D - PASS**: (no issues flagged)
- **1E - PASS**: (no issues flagged)
- **1F - PASS**: (no issues flagged)
- **1G - PASS**: (no issues flagged)
- **1H - PASS**: (no issues flagged)
- **1I - PASS**: (no issues flagged)

## Summary

| Shot | Pass? | Presence | Location | Continuity | Artifacts | Identity (avg) | Wardrobe (avg) | # Reasons |
|------|-------|----------|----------|------------|-----------|----------------|----------------|-----------|
| 1A | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1B | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1C | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1D | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1E | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1F | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | n/a | n/a | 0 |
| 1G | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1H | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1I | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |

**Total API usage:** 35,683 input tokens + 5,171 output tokens. **Estimated cost:** $0.0236.

## Per-Shot Breakdown

### Shot 1A - PASS

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Mia: 1.00, Leo: 1.00, Jenny: 1.00, Nina: 1.00, Gabe: 1.00
- character_wardrobe: Mia: 1.00, Leo: 1.00, Jenny: 1.00, Nina: 1.00, Gabe: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1A.png)
- presence: 1.00 (observed: Mia, Leo, Jenny, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Leo]: 1.00 - Leo's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Jenny]: 1.00 - Jenny's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Mia]: 1.00 (expected: casual home wear, legs tucked under on couch) - Mia is wearing casual home wear, and her legs are tucked under on the couch as expected.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas) - Leo is wearing green dinosaur-pattern pajamas as specified in the manifest.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, on phone) - Jenny is dressed in casual teen attire, has dark brown hair in a ponytail, and is on her phone.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (date-night)) - Nina is wearing an elegant black formal dress, consistent with a date-night outfit.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (date-night, slightly rumpled)) - Gabe is wearing a black tuxedo, which appears slightly rumpled, matching the date-night description.
- location: 1.00 - The living room set, including the TV, couch, armchair, and windows showing a stormy sky, perfectly matches the description.
- continuity: n/a (no prior shot or different location)
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1B - PASS

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Leo: 1.00, Mia: 1.00
- character_wardrobe: Leo: 1.00, Mia: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1B.png)
- presence: 1.00 (observed: Leo, Mia | missing: none | unexpected: none)
- identity[Leo]: 1.00 - Leo's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference, despite being partially visible.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas, hugging plush T-Rex) - Leo is wearing green dinosaur-pattern pajamas and hugging a plush T-Rex, matching the manifest.
- wardrobe[Mia]: 1.00 (expected: casual home wear (partial frame edge)) - Mia is wearing casual home wear, consistent with the manifest description for a partial frame edge view.
- location: 1.00 - The living room set, including the couch, window, and overall lighting, matches the previous shot and expected location.
- continuity: 1.00 [same location] - The location, time of day (stormy night), and Leo's wardrobe are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1C - PASS

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Nina: 1.00, Gabe: 1.00, Jenny: 1.00
- character_wardrobe: Nina: 1.00, Gabe: 1.00, Jenny: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1C.png)
- presence: 1.00 (observed: Nina, Gabe, Jenny | missing: none | unexpected: none)
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build are consistent with the turnaround reference.
- identity[Jenny]: 1.00 - Jenny's face, hair, skin tone, and build are consistent with the turnaround reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress, putting on earrings) - Nina is wearing an elegant black formal dress and is putting on earrings as expected.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background)) - Gabe is wearing a black tuxedo that matches the wardrobe consistency reference.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail (background, on phone)) - Jenny is wearing casual teen attire and has her dark brown hair in a ponytail, consistent with the manifest.
- location: 1.00 - The living room set, furniture, and window view with the storm are consistent with the reference images.
- continuity: 1.00 [same location] - The location and time of day are consistent with the prior shot, despite different characters being present.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1D - PASS

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Gabe: 1.00, Nina: 1.00, Mia: 1.00, Leo: 1.00, Jenny: 1.00
- character_wardrobe: Gabe: 1.00, Nina: 1.00, Mia: 1.00, Leo: 1.00, Jenny: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1D.png)
- presence: 1.00 (observed: Gabe, Nina, Mia, Leo, Jenny | missing: none | unexpected: none)
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Leo]: 1.00 - Leo's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Jenny]: 1.00 - Jenny's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (slightly rumpled), checking watch) - Gabe is wearing a black tuxedo, which matches the manifest description.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress) - Nina is wearing an elegant black formal dress, consistent with the manifest and prior shot reference.
- wardrobe[Mia]: 1.00 (expected: casual home wear (background, on couch)) - Mia is wearing casual home wear, consistent with the manifest and prior shot reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas (background, on couch)) - Leo is wearing green dinosaur-pattern pajamas, consistent with the manifest and prior shot reference.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, on phone (background, oblivious)) - Jenny is wearing casual teen attire with her hair in a ponytail, consistent with the manifest and prior shot reference.
- location: 1.00 - The living room set, furniture, and window view with the storm are consistent with the location plate.
- continuity: 1.00 [same location] - The location, time of day, and wardrobe for returning characters are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1E - PASS

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Jenny: 1.00
- character_wardrobe: Jenny: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1E.png)
- presence: 1.00 (observed: Jenny | missing: none | unexpected: none)
- identity[Jenny]: 1.00 - Jenny's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, head tilted down at phone) - Jenny's casual attire and ponytail match the manifest description.
- location: 1.00 - The living room set, including the window with the storm, lamps, and couch, is consistent with the previous shot and location plate.
- continuity: 1.00 [same location] - The location, time of day (stormy night), and Jenny's wardrobe are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1F - PASS

**Aggregate scores:**
- character_presence: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1F.png)
- presence: 1.00 (observed: none | missing: none | unexpected: none)
- location: 1.00 - The living room with the lamp, window, and general layout matches the previous shot and manifest.
- continuity: 1.00 [same location] - The location, time of day, and storm outside the window are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

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

**Keyframe first** (scene-01-1G.png)
- presence: 1.00 (observed: Mia, Leo, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's identity matches the turnaround reference, with consistent facial features, hair, skin tone, and build.
- identity[Leo]: 1.00 - Leo's identity matches the turnaround reference, with consistent facial features, hair, skin tone, and build.
- identity[Nina]: 1.00 - Nina's identity matches the turnaround reference, with consistent facial features, hair, skin tone, and build.
- identity[Gabe]: 1.00 - Gabe's identity matches the turnaround reference, with consistent facial features, hair, skin tone, and build.
- wardrobe[Mia]: 1.00 (expected: casual home wear (OTS, back of head visible)) - Mia's casual home wear matches the manifest description and the wardrobe consistency reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas (OTS, PJs visible)) - Leo's green dinosaur-pattern pajamas match the manifest description and the wardrobe consistency reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (background, preparing)) - Nina's elegant black formal dress matches the manifest description and the wardrobe consistency reference.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background, preparing)) - Gabe's black tuxedo matches the manifest description and the wardrobe consistency reference.
- location: 1.00 - The living room set, furniture, and window view are consistent with the location plate.
- continuity: 1.00 [same location] - The location, time of day, and general environment are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1H - PASS

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Mia: 1.00
- character_wardrobe: Mia: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1H.png)
- presence: 1.00 (observed: Mia | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Mia]: 1.00 (expected: casual home wear, looking up at off-screen parents) - Mia is wearing a pink t-shirt with white polka dots and blue jeans, which aligns with casual home wear.
- location: 1.00 - The living room set, including the window with the storm, lamp, and couch, is consistent with the reference image.
- continuity: 1.00 [same location] - The location, time of day, and Mia's wardrobe are consistent with the previous shot.
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

**Keyframe first** (scene-01-1I.png)
- presence: 1.00 (observed: Gabe, Nina | missing: none | unexpected: none)
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (conflicted expression)) - Gabe is wearing a black tuxedo that matches the wardrobe consistency reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (sharp glare)) - Nina is wearing an elegant black formal dress that matches the wardrobe consistency reference.
- location: 1.00 - The front entryway location is consistent with the description, featuring a coat rack, console table, and a stormy window.
- continuity: 1.00 - This shot is in a different location than the prior shot, so continuity is not applicable.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>
