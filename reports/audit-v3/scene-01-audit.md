# Scene 1 v3 audit - Reference-Aware Shot Validation Report

Backend: `gemini`  |  Model: `gemini-2.5-flash`  |  Validator: `scripts/validate/shot_validator.py`

Each shot's first/middle/last keyframe was scored by the vision model against the locked character turnarounds (Gabe, Jenny, Leo, Mia, Nina) and a provisional living-room plate (shot 1A storyboard panel). Continuity uses the previous shot's last keyframe as the comparison frame.

Note: when a manifest character is **not visible** in a keyframe, the model reports them as `no_reference` for identity (it can't compare a face that isn't there). The fact that they are missing is still flagged separately in `character_presence.missing` and drives the presence-score failure - that is the real signal for missing/swapped characters.

## Validator findings (TL;DR)

- **1A - FAIL**: missing character(s)
- **1B - PASS**: (no issues flagged)
- **1C - PASS**: (no issues flagged)
- **1D - PASS**: (no issues flagged)
- **1E - FAIL**: unexpected/extra character(s)
- **1F - FAIL**: (generic failure)
- **1G - PASS**: (no issues flagged)
- **1H - FAIL**: environment artifact (indoor lightning)
- **1I - PASS**: (no issues flagged)

## Summary

| Shot | Pass? | Presence | Location | Continuity | Artifacts | Identity (avg) | Wardrobe (avg) | # Reasons |
|------|-------|----------|----------|------------|-----------|----------------|----------------|-----------|
| 1A | **FAIL** | 0.60 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 2 |
| 1B | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1C | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1D | **PASS** | 0.80 | 1.00 | 1.00 | 1.00 | 0.88 | 1.00 | 0 |
| 1E | **FAIL** | 1.00 | 1.00 | 0.70 | 1.00 | 1.00 | 1.00 | 2 |
| 1F | **FAIL** | 1.00 | 1.00 | 1.00 | 0.70 | n/a | n/a | 1 |
| 1G | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |
| 1H | **FAIL** | 1.00 | 1.00 | 1.00 | 0.40 | 1.00 | 1.00 | 1 |
| 1I | **PASS** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0 |

**Total API usage:** 35,628 input tokens + 5,030 output tokens. **Estimated cost:** $0.0233.

## Per-Shot Breakdown

### Shot 1A - FAIL

**Aggregate scores:**
- character_presence: 0.60
- character_identity: Mia: 1.00, Leo: 1.00, Jenny: 1.00
- character_identity (no reference, not scored): Gabe, Nina
- character_wardrobe: Mia: 1.00, Leo: 1.00, Jenny: 1.00
- character_wardrobe (not visible, not scored): Gabe, Nina
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

**Failure reasons:**
- Two expected characters, Nina and Gabe, are missing from the keyframe.
- Character presence score is below the passing threshold due to missing characters.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1A.png)
- presence: 0.60 (observed: Mia, Leo, Jenny | missing: Nina, Gabe | unexpected: none)
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Leo]: 1.00 - Leo's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Jenny]: 1.00 - Jenny's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: not visible - Nina is not visible in the keyframe.
- identity[Gabe]: not visible - Gabe is not visible in the keyframe.
- wardrobe[Mia]: 1.00 (expected: casual home wear, legs tucked under on couch) - Mia is wearing casual home wear, consistent with the manifest.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas) - Leo is wearing green dinosaur-pattern pajamas, consistent with the manifest.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, on phone) - Jenny is wearing casual teen attire, consistent with the manifest.
- wardrobe[Nina]: not visible - Nina is not visible in the keyframe.
- wardrobe[Gabe]: not visible - Gabe is not visible in the keyframe.
- location: 1.00 - The living room set, including the TV, couch, armchair, and window with a stormy sky, matches the description perfectly.
- continuity: n/a (no prior shot or different location)
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: False
  - Two expected characters, Nina and Gabe, are missing from the keyframe.
  - Character presence score is below the passing threshold due to missing characters.

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
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas, hugging plush T-Rex) - Leo is wearing green dinosaur-pattern pajamas and hugging a plush T-Rex, matching the manifest.
- wardrobe[Mia]: 1.00 (expected: casual home wear (partial frame edge)) - Mia is wearing casual home wear, consistent with the manifest description.
- location: 1.00 - The living room set, including the couch, TV, and window, matches the previous shot and location plate perfectly.
- continuity: 1.00 [same location] - The location, time of day, and character wardrobes for Leo and Mia are consistent with the prior shot.
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
- identity[Gabe]: 1.00 - Gabe's identity is consistent with the turnaround, despite being partially obscured.
- identity[Jenny]: 1.00 - Jenny's identity is consistent with the turnaround, despite being partially obscured.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress, putting on earrings) - Nina is wearing an elegant black formal dress and appears to be putting on earrings, matching the manifest.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background)) - Gabe is wearing a black tuxedo, consistent with the manifest and the wardrobe consistency reference.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail (background, on phone)) - Jenny is wearing casual teen attire with her dark brown hair in a ponytail, matching the manifest.
- location: 1.00 - The living room set, including furniture, layout, and the stormy window, matches the reference images.
- continuity: 1.00 [same location] - The location and time of day are consistent with the previous shot, showing the same living room at night with a storm outside.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1D - PASS

**Aggregate scores:**
- character_presence: 0.80
- character_identity: Gabe: 1.00, Nina: 1.00, Mia: 0.80, Leo: 0.80, Jenny: 0.80
- character_wardrobe: Gabe: 1.00, Nina: 1.00, Mia: 1.00, Leo: 1.00, Jenny: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1D.png)
- presence: 0.80 (observed: Gabe, Nina, Mia, Leo, Jenny | missing: none | unexpected: none)
- identity[Gabe]: 1.00 - Gabe's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Nina]: 1.00 - Nina's face, hair, skin tone, and build perfectly match the turnaround reference.
- identity[Mia]: 0.80 - Mia's identity is consistent with the turnaround, though she is partially obscured in the background.
- identity[Leo]: 0.80 - Leo's identity is consistent with the turnaround, though he is partially obscured in the background.
- identity[Jenny]: 0.80 - Jenny's identity is consistent with the turnaround, though she is partially obscured in the background.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (slightly rumpled), checking watch) - Gabe is wearing a black tuxedo and is checking his watch, matching the manifest description.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress) - Nina is wearing an elegant black formal dress, consistent with the manifest and prior shot reference.
- wardrobe[Mia]: 1.00 (expected: casual home wear (background, on couch)) - Mia is wearing casual home wear, consistent with the manifest and prior shot reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas (background, on couch)) - Leo is wearing green dinosaur-pattern pajamas, consistent with the manifest and prior shot reference.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, on phone (background, oblivious)) - Jenny is wearing casual teen attire with her hair in a ponytail and is on her phone, matching the manifest and prior shot reference.
- location: 1.00 - The living room set, including the couch, armchair, TV, and window, is consistent with the reference images.
- continuity: 1.00 [same location] - The location, time of day, and wardrobe for Nina and Jenny are consistent with the prior shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1E - FAIL

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Jenny: 1.00
- character_wardrobe: Jenny: 1.00
- location_match: 1.00
- continuity: 0.70
- artifacts: 1.00

**Failure reasons:**
- Unexpected characters Mia and Leo are visible in the background, which were not listed in the expected characters for this shot.
- The character presence score is below the passing threshold due to unexpected characters.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1E.png)
- presence: 1.00 (observed: Jenny, Mia, Leo | missing: none | unexpected: Mia, Leo)
- identity[Jenny]: 1.00 - Jenny's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, head tilted down at phone) - Jenny is wearing a casual hoodie and her dark brown hair is in a ponytail, consistent with the manifest.
- location: 1.00 - The living room set, including the couch and window with the storm, is consistent with the reference image.
- continuity: 0.70 [same location] - The location and time of day (stormy night) are consistent, but Mia and Leo are now visible in the background, which was not explicitly stated in the prior shot's manifest.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: False
  - Unexpected characters Mia and Leo are visible in the background, which were not listed in the expected characters for this shot.
  - The character presence score is below the passing threshold due to unexpected characters.

</details>

### Shot 1F - FAIL

**Aggregate scores:**
- character_presence: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 0.70

**Failure reasons:**
- The lightning flash is not reflected in the TV screen as expected.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1F.png)
- presence: 1.00 (observed: none | missing: none | unexpected: none)
- location: 1.00 - The living room set, including the window and the TV, matches the expected location.
- continuity: 1.00 [same location] - The location and time of day are consistent with the prior shot.
- artifacts: 0.70 - detected: missing lightning reflection - The blue time-warp flash and horizontal scan lines are present, but the lightning flash is not reflected in the screen.
- keyframe overall_pass: False
  - The lightning flash is not reflected in the TV screen as expected.

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
- identity[Mia]: 1.00 - Mia's identity matches the turnaround reference in face, hair, skin tone, and build.
- identity[Leo]: 1.00 - Leo's identity matches the turnaround reference in face, hair, skin tone, and build.
- identity[Nina]: 1.00 - Nina's identity matches the turnaround reference in face, hair, skin tone, and build.
- identity[Gabe]: 1.00 - Gabe's identity matches the turnaround reference in face, hair, skin tone, and build.
- wardrobe[Mia]: 1.00 (expected: casual home wear (OTS, back of head visible)) - Mia's casual home wear matches the established look from shot 1B.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas (OTS, PJs visible)) - Leo's green dinosaur-pattern pajamas match the established look from shot 1A.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (background, preparing)) - Nina's elegant black formal dress matches the established look from shot 1A.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background, preparing)) - Gabe's black tuxedo matches the established look from shot 1A.
- location: 1.00 - The living room set, including the couch, TV, window, and lamp, matches the reference plate.
- continuity: 1.00 [same location] - The location, time of day, and general ambiance are consistent with the prior shot.
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
- artifacts: 0.40

**Failure reasons:**
- A lightning bolt is incorrectly depicted inside the living room, violating physical realism.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1H.png)
- presence: 1.00 (observed: Mia | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's face, hair, skin tone, and build perfectly match the turnaround reference.
- wardrobe[Mia]: 1.00 (expected: casual home wear, looking up at off-screen parents) - Mia is wearing casual home wear, which matches the manifest description.
- location: 1.00 - The living room set, including the couch, lamp, and window with a storm, is consistent with the reference image.
- continuity: 1.00 [same location] - The location and time of day (stormy night) are consistent with the previous shot.
- artifacts: 0.40 - detected: lightning bolt inside room - A lightning bolt is visible inside the room, which is a physical impossibility and a significant artifact.
- keyframe overall_pass: False
  - A lightning bolt is incorrectly depicted inside the living room, violating physical realism.

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
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (conflicted expression)) - Gabe is wearing a black tuxedo, consistent with the manifest and the wardrobe consistency reference.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (sharp glare)) - Nina is wearing an elegant black formal dress, consistent with the manifest and the wardrobe consistency reference.
- location: 1.00 - The living room set, including the couch, lamp, and window with the storm, is consistent with the reference images.
- continuity: 1.00 [same location] - The location and time of day are consistent with the previous shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations were detected in the keyframe.
- keyframe overall_pass: True

</details>
