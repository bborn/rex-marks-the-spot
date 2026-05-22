# Scene 1 (Seedance mitte animatic) - Reference-Aware Shot Validation Report

Backend: `gemini`  |  Model: `gemini-2.5-flash`  |  Validator: `scripts/validate/shot_validator.py`

Each shot's first/middle/last keyframe was scored by the vision model against the locked character turnarounds (Gabe, Jenny, Leo, Mia, Nina) and a provisional living-room plate (shot 1A storyboard panel). Continuity uses the previous shot's last keyframe as the comparison frame.

Note: when a manifest character is **not visible** in a keyframe, the model reports them as `no_reference` for identity (it can't compare a face that isn't there). The fact that they are missing is still flagged separately in `character_presence.missing` and drives the presence-score failure - that is the real signal for missing/swapped characters.

## Validator findings (TL;DR)

- **1A - FAIL**: missing characters: Gabe, Nina; wardrobe drift
- **1B - FAIL**: wardrobe drift; hair drift
- **1C - FAIL**: wardrobe drift; continuity break; location drift
- **1D - FAIL**: missing characters: Jenny, Leo, Mia; wardrobe drift
- **1G - PASS**: (no issues flagged)
- **1H - FAIL**: unexpected/extra character(s); location drift
- **1I - FAIL**: wardrobe drift; continuity break

## Summary

| Shot | Pass? | Presence | Location | Continuity | Artifacts | Identity (avg) | # Reasons |
|------|-------|----------|----------|------------|-----------|----------------|-----------|
| 1A | **FAIL** | 0.60 | 0.90 | 1.00 | 1.00 | 0.91 | 5 |
| 1B | **FAIL** | 1.00 | 0.93 | 0.80 | 0.97 | 0.93 | 4 |
| 1C | **FAIL** | 0.77 | 0.77 | 0.00 | 1.00 | 0.57 | 11 |
| 1D | **FAIL** | 0.47 | 0.87 | 0.80 | 1.00 | 0.66 | 12 |
| 1G | **PASS** | 1.00 | 0.97 | 0.93 | 1.00 | 0.97 | 0 |
| 1H | **FAIL** | 0.90 | 0.83 | 0.73 | 1.00 | 0.90 | 2 |
| 1I | **FAIL** | 1.00 | 0.80 | 0.00 | 1.00 | 0.77 | 8 |

**Total API usage:** 52,071 input tokens + 7,739 output tokens. **Estimated cost:** $0.0350.

## Per-Shot Breakdown

### Shot 1A - FAIL

**Aggregate scores:**
- character_presence: 0.60
- character_identity: Mia: 0.90, Leo: 0.93, Jenny: 0.90
- character_identity (no reference, not scored): Gabe, Nina
- location_match: 0.90
- continuity: 1.00
- artifacts: 1.00

**Failure reasons:**
- Nina is missing from the shot.
- Gabe is missing from the shot.
- Mia's top is a solid pink instead of pink with stars.
- Jenny's hoodie color is slightly off.
- Mia's wardrobe does not match the expected pajamas.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (01-shot-1A-first.jpg)
- presence: 0.60 (observed: Mia, Leo, Jenny | missing: Nina, Gabe | unexpected: none)
- identity[Mia]: 0.90 - Mia's hair and general appearance match the turnaround, but her top is a solid pink instead of pink with stars.
- identity[Leo]: 1.00 - Leo's appearance and green dinosaur pajamas perfectly match the turnaround.
- identity[Jenny]: 0.90 - Jenny's hair, skin tone, and general appearance match the turnaround, but her hoodie is a slightly different shade of pink.
- identity[Nina]: no reference - Nina is not present in the keyframe.
- identity[Gabe]: no reference - Gabe is not present in the keyframe.
- location: 0.90 - The living room layout, furniture, and general ambiance closely match the location plate, though the TV content is different and the storm outside is less dramatic.
- continuity: n/a (no prior shot)
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Nina is missing from the shot.
  - Gabe is missing from the shot.
  - Mia's top is a solid pink instead of pink with stars.
  - Jenny's hoodie color is slightly off.

**Keyframe mid** (01-shot-1A-mid.jpg)
- presence: 0.60 (observed: Mia, Leo, Jenny | missing: Nina, Gabe | unexpected: none)
- identity[Mia]: 0.90 - Mia's hair and general appearance match the turnaround, but her wardrobe is different from the expected pajamas.
- identity[Leo]: 0.90 - Leo's appearance and green dinosaur pajamas match the turnaround and expected wardrobe.
- identity[Jenny]: 0.90 - Jenny's appearance and casual teen wardrobe match the turnaround and expected description.
- location: 0.90 - The living room layout, furniture, and general ambiance closely match the location plate, though the lighting is slightly different.
- continuity: n/a (no prior shot)
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Nina is missing from the shot.
  - Gabe is missing from the shot.
  - Mia's wardrobe does not match the expected pajamas.

**Keyframe last** (01-shot-1A-last.jpg)
- presence: 0.60 (observed: Mia, Leo, Jenny | missing: Nina, Gabe | unexpected: none)
- identity[Mia]: 0.90 - Mia's hair and clothing match the turnaround, though her pajamas are pink with stars instead of the solid pink shown in the reference.
- identity[Leo]: 0.90 - Leo's hair and clothing match the turnaround, and he is holding his plush T-Rex.
- identity[Jenny]: 0.90 - Jenny's hair and clothing match the turnaround, and she is on her phone.
- identity[Nina]: no reference - Nina is not present in the keyframe.
- identity[Gabe]: no reference - Gabe is not present in the keyframe.
- location: 0.90 - The living room set, furniture, and layout closely match the location plate, including the stormy sky outside the window.
- continuity: n/a (no prior shot)
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Nina is missing from the shot.
  - Gabe is missing from the shot.

</details>

### Shot 1B - FAIL

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Leo: 0.93, Mia: 0.93
- location_match: 0.93
- continuity: 0.80
- artifacts: 0.97

**Failure reasons:**
- Mia's wardrobe does not match the previous shot's keyframe.
- Leo's pajamas are a different shade of green compared to the previous shot.
- Leo's hair color is slightly off from the turnaround reference.
- Mia's top has a star pattern not seen in the previous shot or expected wardrobe.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (02-shot-1B-first.jpg)
- presence: 1.00 (observed: Leo, Mia | missing: none | unexpected: none)
- identity[Leo]: 1.00 - Leo's appearance, including hair, face, and wardrobe, perfectly matches the provided turnaround reference.
- identity[Mia]: 1.00 - Mia's appearance, including hair, face, and wardrobe, perfectly matches the provided turnaround reference.
- location: 1.00 - The living room set, including furniture, layout, and lighting, is consistent with the location plate.
- continuity: 0.90 - The room state, wardrobe, and general lighting are consistent with the previous shot, though the TV content has changed.
- artifacts: 1.00 - detected: none - No visible generation artifacts such as extra limbs, melting, or garbled features were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe mid** (02-shot-1B-mid.jpg)
- presence: 1.00 (observed: Leo, Mia | missing: none | unexpected: none)
- identity[Leo]: 0.90 - Leo's hair color is slightly lighter than the reference, and his pajamas are green with a dinosaur, but not the exact pattern.
- identity[Mia]: 0.90 - Mia's hair and skin tone match, but her wardrobe is different from the expected casual home wear, wearing a pink top with stars instead of the solid pink from the previous shot.
- location: 0.90 - The living room matches the location plate well, with similar furniture and layout, though the lighting is slightly different due to the TV glow on Leo's face.
- continuity: 0.70 - The room state and time of day are consistent, but Mia's wardrobe has changed from a solid pink top to a star-patterned one, and Leo's pajamas are a different shade of green.
- artifacts: 0.90 - detected: none - There are no significant generation artifacts, though the TV glow on Leo's face is a bit intense and colorful.
- keyframe overall_pass: False
  - Mia's wardrobe does not match the previous shot's keyframe.
  - Leo's pajamas are a different shade of green compared to the previous shot.
  - Leo's hair color is slightly off from the turnaround reference.
  - Mia's top has a star pattern not seen in the previous shot or expected wardrobe.

**Keyframe last** (02-shot-1B-last.jpg)
- presence: 1.00 (observed: Leo, Mia | missing: none | unexpected: none)
- identity[Leo]: 0.90 - Leo's hair color is slightly lighter than the reference, and his pajamas are green with a dinosaur pattern, but he is not hugging the plush T-Rex.
- identity[Mia]: 0.90 - Mia's hair and facial features match, and her wardrobe is consistent with casual home wear, though the specific pattern on her shirt is not visible.
- location: 0.90 - The living room set, furniture, and overall layout match the location plate, with consistent lighting and window view.
- continuity: 0.80 - The room state, wardrobe, and general lighting are consistent with the previous shot, though the camera angle and character positions have changed.
- artifacts: 1.00 - detected: none - No visible generation artifacts such as extra limbs, melting, text-in-frame, or garbled hands were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1C - FAIL

**Aggregate scores:**
- character_presence: 0.77
- character_identity: Nina: 0.67, Gabe: 0.47, Jenny: 0.57
- location_match: 0.77
- continuity: 0.00
- artifacts: 1.00

**Failure reasons:**
- Continuity break: Nina's wardrobe is different from the previous shot.
- Continuity break: Gabe's wardrobe is different from the previous shot.
- Continuity break: The lighting and time of day are inconsistent with the previous shot.
- Continuity break: Wardrobe for all characters is inconsistent with the previous shot.
- Continuity break: The time of day and lighting have changed drastically from the previous shot.
- Nina's wardrobe does not match her turnaround reference.
- Gabe's wardrobe does not match his turnaround reference.
- Gabe and Jenny are missing from the shot.
- Nina's wardrobe does not match the expected formal dress, instead she is wearing a casual sweater and jeans.
- The location does not match the reference plate, with a different layout and missing window.
- The shot lacks continuity with the previous keyframe regarding characters, wardrobe, and room state.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (03-shot-1C-first.jpg)
- presence: 1.00 (observed: Nina, Gabe, Jenny | missing: none | unexpected: none)
- identity[Nina]: 0.80 - Nina's hair color is slightly lighter and her dress is a different style than the turnaround, but her facial features are consistent.
- identity[Gabe]: 0.80 - Gabe's hair and glasses match, but his wardrobe is a tuxedo instead of the expected plaid shirt and khakis from his turnaround.
- identity[Jenny]: 0.90 - Jenny's appearance is consistent with her turnaround, including her hair and casual attire.
- location: 0.90 - The living room layout, furniture, and window view are largely consistent with the location plate, though some minor decor differences exist.
- continuity: 0.00 - The wardrobe for Nina and Gabe, as well as the overall lighting and time of day, are completely different from the previous shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Continuity break: Nina's wardrobe is different from the previous shot.
  - Continuity break: Gabe's wardrobe is different from the previous shot.
  - Continuity break: The lighting and time of day are inconsistent with the previous shot.

**Keyframe mid** (03-shot-1C-mid.jpg)
- presence: 1.00 (observed: Nina, Gabe, Jenny | missing: none | unexpected: none)
- identity[Nina]: 0.60 - Nina's hair color is slightly off, and her wardrobe is a black formal dress instead of the expected maroon sweater and jeans from her turnaround.
- identity[Gabe]: 0.60 - Gabe's wardrobe is a black tuxedo, which is different from his turnaround reference, but his facial features and hair are consistent.
- identity[Jenny]: 0.80 - Jenny's appearance is mostly consistent with her turnaround, though her hair is down instead of in a ponytail.
- location: 0.90 - The living room set matches the location plate very well, with consistent furniture, layout, and overall ambiance.
- continuity: 0.00 - The wardrobe for Nina, Gabe, and Jenny is completely different from the previous shot, and the overall mood and time of day have changed significantly.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Continuity break: Wardrobe for all characters is inconsistent with the previous shot.
  - Continuity break: The time of day and lighting have changed drastically from the previous shot.
  - Nina's wardrobe does not match her turnaround reference.
  - Gabe's wardrobe does not match his turnaround reference.

**Keyframe last** (03-shot-1C-last.jpg)
- presence: 0.30 (observed: Nina | missing: Gabe, Jenny | unexpected: none)
- identity[Nina]: 0.60 - Nina's face and hair are consistent with the turnaround, but her wardrobe is a black formal dress instead of the expected maroon sweater and jeans.
- identity[Gabe]: 0.00 - Gabe is not present in the keyframe.
- identity[Jenny]: 0.00 - Jenny is not present in the keyframe.
- location: 0.50 - The room shares some elements like the lamp and general wall color, but the layout and specific furniture are different from the location plate, and the window is missing.
- continuity: 0.00 - The keyframe shows Nina in a formal dress in a different room layout, while the previous shot showed the children and Jenny in pajamas in the living room with a storm outside.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Gabe and Jenny are missing from the shot.
  - Nina's wardrobe does not match the expected formal dress, instead she is wearing a casual sweater and jeans.
  - The location does not match the reference plate, with a different layout and missing window.
  - The shot lacks continuity with the previous keyframe regarding characters, wardrobe, and room state.

</details>

### Shot 1D - FAIL

**Aggregate scores:**
- character_presence: 0.47
- character_identity: Gabe: 0.90, Nina: 0.90, Mia: 0.50, Leo: 0.50, Jenny: 0.50
- character_identity (no reference, not scored): Jenny, Leo, Mia
- location_match: 0.87
- continuity: 0.80
- artifacts: 1.00

**Failure reasons:**
- Gabe's wardrobe does not match the expected black tuxedo; he is wearing a plaid shirt and khakis in the turnaround.
- Nina's wardrobe does not match the expected elegant black formal dress; she is wearing a maroon sweater and jeans in the turnaround.
- Mia's identity score is low due to blurriness and unclear wardrobe.
- Leo's identity score is low due to blurriness and unclear wardrobe.
- Jenny's identity score is low due to blurriness and unclear wardrobe.
- Mia is missing from the shot.
- Leo is missing from the shot.
- Jenny is missing from the shot.
- Gabe's wardrobe does not match the expected casual home wear.
- Nina's wardrobe does not match the expected casual home wear.
- Gabe's wardrobe is a tuxedo, not a rumpled black tuxedo as expected.
- Nina's dress is a formal black dress, not an elegant black formal dress as expected.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (04-shot-1D-first.jpg)
- presence: 0.60 (observed: Gabe, Nina, Mia, Leo, Jenny | missing: none | unexpected: none)
- identity[Gabe]: 0.90 - Gabe's face, hair, and general build match the turnaround, but his wardrobe is a tuxedo instead of the expected plaid shirt and khakis.
- identity[Nina]: 0.90 - Nina's face, hair, and general build match the turnaround, but her wardrobe is an elegant black formal dress instead of the expected maroon sweater and jeans.
- identity[Mia]: 0.50 - Mia is present in the background, but her appearance is very blurry and her wardrobe is not clearly discernible as casual home wear.
- identity[Leo]: 0.50 - Leo is present in the background, but his appearance is very blurry and his green dinosaur-pattern pajamas are not clearly visible.
- identity[Jenny]: 0.50 - Jenny is present in the background, but her appearance is very blurry and her casual teen wardrobe is not clearly visible.
- location: 0.90 - The living room set, including the couch, armchair, and general layout, matches the location plate well, though the lighting is different due to the time of day change.
- continuity: 0.60 - The location and Nina's wardrobe are consistent with the previous shot, but Gabe's presence and wardrobe are new, and the background characters are also new.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Gabe's wardrobe does not match the expected black tuxedo; he is wearing a plaid shirt and khakis in the turnaround.
  - Nina's wardrobe does not match the expected elegant black formal dress; she is wearing a maroon sweater and jeans in the turnaround.
  - Mia's identity score is low due to blurriness and unclear wardrobe.
  - Leo's identity score is low due to blurriness and unclear wardrobe.
  - Jenny's identity score is low due to blurriness and unclear wardrobe.

**Keyframe mid** (04-shot-1D-mid.jpg)
- presence: 0.40 (observed: Gabe, Nina | missing: Mia, Leo, Jenny | unexpected: none)
- identity[Gabe]: 0.90 - Gabe's facial features, hair, and glasses match the turnaround, but his wardrobe is a black tuxedo instead of the expected plaid shirt and khakis.
- identity[Nina]: 0.90 - Nina's facial features, hair, and general appearance match the turnaround, but her wardrobe is an elegant black formal dress instead of the expected maroon sweater and jeans.
- identity[Mia]: no reference - Mia is not present in the keyframe.
- identity[Leo]: no reference - Leo is not present in the keyframe.
- identity[Jenny]: no reference - Jenny is not present in the keyframe.
- location: 0.80 - The living room layout, furniture, and general ambiance match the location plate, though the TV content is different and the background is slightly blurred.
- continuity: 0.90 - The keyframe maintains continuity with the previous shot regarding Nina's wardrobe and the overall lighting, though Gabe is newly present.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Mia is missing from the shot.
  - Leo is missing from the shot.
  - Jenny is missing from the shot.
  - Gabe's wardrobe does not match the expected casual home wear.
  - Nina's wardrobe does not match the expected casual home wear.

**Keyframe last** (04-shot-1D-last.jpg)
- presence: 0.40 (observed: Gabe, Nina | missing: Mia, Leo, Jenny | unexpected: none)
- identity[Gabe]: 0.90 - Gabe's face, hair, and glasses match the turnaround, but his wardrobe is a tuxedo instead of the expected rumpled black tuxedo.
- identity[Nina]: 0.90 - Nina's face, hair, and general appearance match the turnaround, but her dress is a formal black dress instead of the expected elegant black formal dress.
- identity[Mia]: no reference - Mia is not present in the keyframe.
- identity[Leo]: no reference - Leo is not present in the keyframe.
- identity[Jenny]: no reference - Jenny is not present in the keyframe.
- location: 0.90 - The living room matches the location plate, including the couch, lamp, and window with a storm outside.
- continuity: 0.90 - The room state, wardrobe, and lighting are consistent with the previous shot keyframe, showing Nina in the same dress and the same general setting.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Mia is missing from the shot.
  - Leo is missing from the shot.
  - Jenny is missing from the shot.
  - Gabe's wardrobe is a tuxedo, not a rumpled black tuxedo as expected.
  - Nina's dress is a formal black dress, not an elegant black formal dress as expected.

</details>

### Shot 1G - PASS

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Mia: 0.97, Leo: 0.97, Nina: 0.97, Gabe: 0.97
- location_match: 0.97
- continuity: 0.93
- artifacts: 1.00

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (05-shot-1G-first.jpg)
- presence: 1.00 (observed: Mia, Leo, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's appearance, including her hair, skin tone, and casual home wear, perfectly matches her turnaround reference.
- identity[Leo]: 1.00 - Leo's hair, skin tone, and green dinosaur pajamas are consistent with his turnaround reference.
- identity[Nina]: 1.00 - Nina's hair, skin tone, and elegant black formal dress are consistent with her turnaround reference and the previous shot.
- identity[Gabe]: 1.00 - Gabe's appearance, including his hair, glasses, and black tuxedo, matches his turnaround reference and the previous shot.
- location: 1.00 - The living room set, including furniture, layout, and window view, perfectly matches the provided location plate.
- continuity: 1.00 - The room state, wardrobe of Nina and Gabe, and overall lighting are consistent with the previous shot keyframe.
- artifacts: 1.00 - detected: none - No visible generation artifacts such as extra limbs, melting, text-in-frame, or garbled hands were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe mid** (05-shot-1G-mid.jpg)
- presence: 1.00 (observed: Mia, Leo, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 0.90 - Mia's hair and general appearance match the turnaround, though her top is pink with stars instead of plain pink.
- identity[Leo]: 0.90 - Leo's hair and general appearance match the turnaround, and his green pajamas are consistent.
- identity[Nina]: 0.90 - Nina's hair and facial features are consistent with the turnaround, and her black dress matches the expected wardrobe.
- identity[Gabe]: 0.90 - Gabe's appearance, including his glasses and tuxedo, matches the turnaround and expected wardrobe.
- location: 0.90 - The living room layout, furniture, and general ambiance are consistent with the location plate, though the lighting is different due to the time of day.
- continuity: 0.80 - The characters' wardrobe and the general setting are consistent with the previous shot, showing Nina and Gabe in formal wear.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: True

**Keyframe last** (05-shot-1G-last.jpg)
- presence: 1.00 (observed: Mia, Leo, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 1.00 - Mia's hair and general appearance match the turnaround, and her casual home wear is appropriate for the shot.
- identity[Leo]: 1.00 - Leo's hair and pajamas match the turnaround, and his overall appearance is consistent.
- identity[Nina]: 1.00 - Nina's hair, facial features, and black formal dress match the turnaround and expected wardrobe.
- identity[Gabe]: 1.00 - Gabe's appearance, including his glasses, hair, and tuxedo, matches the turnaround and expected wardrobe.
- location: 1.00 - The living room set, including furniture, layout, and lighting, perfectly matches the provided location plate.
- continuity: 1.00 - The room state, wardrobe for Nina and Gabe, and overall lighting are consistent with the previous shot keyframe.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1H - FAIL

**Aggregate scores:**
- character_presence: 0.90
- character_identity: Mia: 0.90
- location_match: 0.83
- continuity: 0.73
- artifacts: 1.00

**Failure reasons:**
- An unexpected character is partially visible in the background.
- The lightning is depicted inside the room, which is a significant deviation from the location plate.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (06-shot-1H-first.jpg)
- presence: 1.00 (observed: Mia | missing: none | unexpected: none)
- identity[Mia]: 0.90 - Mia's face, hair, and wardrobe are consistent with the turnaround, though her expression is different.
- location: 0.90 - The living room set matches the location plate, with consistent furniture and overall ambiance.
- continuity: 0.80 - Mia's wardrobe is consistent with the previous shot, but the lighting has changed to reflect the lightning outside.
- artifacts: 1.00 - detected: none - No visible generation artifacts are present in the keyframe.
- keyframe overall_pass: True

**Keyframe mid** (06-shot-1H-mid.jpg)
- presence: 0.70 (observed: Mia, unidentified character | missing: none | unexpected: unidentified character)
- identity[Mia]: 0.90 - Mia's appearance is consistent with the turnaround, though her expression is different due to the scene's context.
- location: 0.80 - The living room matches the location plate, including the couch and lamp, but the window view is different and there's a lightning flash inside.
- continuity: 0.70 - Mia's wardrobe is consistent with the previous shot, but the lighting has changed significantly due to the lightning flash.
- artifacts: 1.00 - detected: none - No visible generation artifacts are present in the keyframe.
- keyframe overall_pass: False
  - An unexpected character is partially visible in the background.
  - The lightning is depicted inside the room, which is a significant deviation from the location plate.

**Keyframe last** (06-shot-1H-last.jpg)
- presence: 1.00 (observed: Mia | missing: none | unexpected: none)
- identity[Mia]: 0.90 - Mia's facial features and hair match the turnaround, but her freckles are more prominent in the keyframe.
- location: 0.80 - The living room setting is consistent with the location plate, though the specific angle and lighting differ due to the close-up shot and lightning flash.
- continuity: 0.70 - Mia's wardrobe is consistent with the previous shot, but the lighting has changed significantly due to the lightning flash.
- artifacts: 1.00 - detected: none - No visible generation artifacts are detected in the keyframe.
- keyframe overall_pass: True

</details>

### Shot 1I - FAIL

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Gabe: 0.77, Nina: 0.77
- location_match: 0.80
- continuity: 0.00
- artifacts: 1.00

**Failure reasons:**
- Gabe's wardrobe does not match his turnaround reference.
- Nina's wardrobe does not match her turnaround reference.
- The continuity score is too low due to significant changes from the previous shot.
- The wardrobe and character expressions are inconsistent with the previous shot.
- Gabe's wardrobe does not match the turnaround reference.
- Nina's wardrobe does not match the turnaround reference.
- The keyframe shows different characters and wardrobe compared to the previous shot.
- The time of day and lighting are inconsistent with the previous shot.

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (07-shot-1I-first.jpg)
- presence: 1.00 (observed: Gabe, Nina | missing: none | unexpected: none)
- identity[Gabe]: 0.60 - Gabe's face shape and hair are consistent, but his wardrobe is a black tuxedo instead of the expected plaid shirt and khakis.
- identity[Nina]: 0.60 - Nina's face and hair are consistent, but her wardrobe is an elegant black formal dress instead of the expected maroon sweater and jeans.
- location: 0.80 - The living room matches the reference plate, but the lighting is different, suggesting a different time of day or mood.
- continuity: 0.00 - The characters, their wardrobe, and the overall lighting and mood are completely different from the previous shot.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Gabe's wardrobe does not match his turnaround reference.
  - Nina's wardrobe does not match her turnaround reference.
  - The continuity score is too low due to significant changes from the previous shot.

**Keyframe mid** (07-shot-1I-mid.jpg)
- presence: 1.00 (observed: Gabe, Nina | missing: none | unexpected: none)
- identity[Gabe]: 0.80 - Gabe's face and hair match the turnaround, but his wardrobe is a black tuxedo instead of the expected plaid shirt and khakis.
- identity[Nina]: 0.80 - Nina's face and hair match the turnaround, but her wardrobe is an elegant black formal dress instead of the expected maroon sweater and jeans.
- location: 0.80 - The living room matches the location plate, though the lighting is different and the TV is showing a different image, which is acceptable for a new shot.
- continuity: 0.00 - The characters' wardrobe and expressions are completely different from the previous shot, indicating a significant time jump or scene change.
- artifacts: 1.00 - detected: none - No visible generation artifacts are present in the keyframe.
- keyframe overall_pass: False
  - Gabe's wardrobe does not match his turnaround reference.
  - Nina's wardrobe does not match her turnaround reference.
  - The wardrobe and character expressions are inconsistent with the previous shot.

**Keyframe last** (07-shot-1I-last.jpg)
- presence: 1.00 (observed: Gabe, Nina | missing: none | unexpected: none)
- identity[Gabe]: 0.90 - Gabe's facial features, hair, and glasses match the turnaround, but his wardrobe is a black tuxedo instead of the expected plaid shirt and khakis.
- identity[Nina]: 0.90 - Nina's facial features, hair, and general build match the turnaround, but her wardrobe is an elegant black formal dress instead of the expected maroon sweater and jeans.
- location: 0.80 - The living room layout, furniture, and window view are consistent with the location plate, though the lighting is different, suggesting a later time of day.
- continuity: 0.00 - The characters, their wardrobe, and the overall lighting/time of day are completely different from the previous shot, which showed children in pajamas during a storm.
- artifacts: 1.00 - detected: none - No visible generation artifacts were detected in the keyframe.
- keyframe overall_pass: False
  - Gabe's wardrobe does not match the turnaround reference.
  - Nina's wardrobe does not match the turnaround reference.
  - The keyframe shows different characters and wardrobe compared to the previous shot.
  - The time of day and lighting are inconsistent with the previous shot.

</details>
