# Scene 1 v4 audit (re-run, fixed validator) - Reference-Aware Shot Validation Report

Backend: `gemini`  |  Model: `gemini-3-flash-preview`  |  Validator: `scripts/validate/shot_validator.py`

Each keyframe was described by the vision model in a fixed attribute vocabulary - hair colour, length, texture, build, eyewear, facial hair, age, skin tone, styling, face shape - and that description was diffed **in code** against the locked identity sheet (`scripts/validate/identity-sheets.json`). The model is not shown the turnarounds and never emits an identity score; the score and the pass/fail gate are both computed by the validator. Every identity number below is traceable to the two attribute rows it came from.

Headline scores are the WORST keyframe, not the mean - a character off-model in one keyframe of three makes an off-model shot. Means are in the JSON under `*_mean`.

`no_reference` means identity was NOT VERIFIED - the character was not visible, or has no row in the identity sheet. It is not a pass.

## Validator findings (TL;DR)

- **1A - FAIL**: character identity drift; hair drift
- **1B - FAIL**: visible artifacts
- **1C - FAIL**: hair drift
- **1D - FAIL**: hair drift
- **1E - FAIL**: character identity drift
- **1F - PASS**: (no issues flagged)
- **1G - FAIL**: hair drift
- **1H - PASS**: (no issues flagged)
- **1I - FAIL**: character identity drift

## Summary

| Shot | Pass? | Presence | Location | Continuity | Artifacts | Identity (avg) | Wardrobe (avg) | # Reasons |
|------|-------|----------|----------|------------|-----------|----------------|----------------|-----------|
| 1A | **FAIL** | 1.00 | 1.00 | 1.00 | 1.00 | 0.55 | 1.00 | 2 |
| 1B | **FAIL** | 0.80 | 0.70 | 0.70 | 0.60 | 0.88 | 0.80 | 1 |
| 1C | **FAIL** | 1.00 | 0.80 | 1.00 | 0.90 | 0.42 | 1.00 | 2 |
| 1D | **FAIL** | 1.00 | 1.00 | 1.00 | 1.00 | 0.42 | 1.00 | 3 |
| 1E | **FAIL** | 0.70 | 0.70 | 0.70 | 0.70 | 0.40 | 0.70 | 1 |
| 1F | **PASS** | 1.00 | 0.80 | 0.80 | 0.70 | n/a | n/a | 0 |
| 1G | **FAIL** | 0.80 | 0.80 | 0.80 | 0.70 | 0.65 | 0.80 | 1 |
| 1H | **PASS** | 0.70 | 0.80 | 0.80 | 0.70 | 0.75 | 0.80 | 0 |
| 1I | **FAIL** | 1.00 | 1.00 | 1.00 | 1.00 | 0.42 | 1.00 | 1 |

**Total API usage:** 77,463 input tokens + 6,780 output tokens. **Estimated cost:** $0.0402.

## Per-Shot Breakdown

### Shot 1A - FAIL

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Mia: 0.75, Leo: 0.75, Jenny: 0.40, Nina: 0.75, Gabe: 0.10
- character_wardrobe: Mia: 1.00, Leo: 1.00, Jenny: 1.00, Nina: 1.00, Gabe: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

**Failure reasons:**
- Jenny identity 0.40 (significant_drift): off-model on skin_tone - skin_tone: turnaround medium_brown / frame light
- Gabe identity 0.10 (different_person): off-model on eyewear, facial_hair - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1A.png)
- presence: 1.00 (observed: Mia, Leo, Jenny, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: hair_colour: turnaround dark_brown / frame black; hair_length: turnaround mid_back / frame shoulder; skin_tone: turnaround tan / frame light; hair_styling: turnaround ponytail / frame worn_loose
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_colour | dark_brown | black |
  | hair_length | mid_back | shoulder |
  | skin_tone | tan | light |
  | hair_styling | ponytail | worn_loose |
- identity[Leo]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: hair_texture: turnaround wavy / frame straight
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_texture | wavy | straight |
- identity[Jenny]: 0.40 (significant_drift) - off-model on skin_tone - skin_tone: turnaround medium_brown / frame light
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_texture | curly | wavy |
  | skin_tone **(defining)** | medium_brown | light |
- identity[Nina]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: build: turnaround average / frame slim; face_shape: turnaround round / frame heart
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | build | average | slim |
  | face_shape | round | heart |
- identity[Gabe]: 0.10 (different_person) - off-model on eyewear, facial_hair - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_colour | dark_brown | black |
  | hair_texture | wavy | straight |
  | build | heavy_set | average |
  | eyewear **(defining)** | thin_wire_rectangular | heavy_dark_rectangular |
  | facial_hair **(defining)** | stubble | clean_shaven |
  | face_shape | round | square |
- wardrobe[Mia]: 1.00 (expected: casual home wear, legs tucked under on couch) - Mia is wearing a purple patterned shirt and jeans, which fits the casual home wear description.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas) - Leo is wearing green pajamas with a clear dinosaur pattern.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, on phone) - Jenny is wearing a blue hoodie and leggings, matching the casual teen description.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (date-night)) - Nina is wearing a long, elegant black formal dress.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (date-night, slightly rumpled)) - Gabe is wearing a black tuxedo with a bowtie.
- location: 1.00 - The keyframe is identical to the location plate provided.
- continuity: n/a (no prior shot or different location)
- artifacts: 1.00 - detected: none - No visible generation artifacts or physics violations detected.
- model commentary: All manifest characters are present and correctly dressed. | The location perfectly matches the provided reference plate. | No artifacts or anatomical errors are visible.
- keyframe overall_pass: False
  - Jenny identity 0.40 (significant_drift): off-model on skin_tone - skin_tone: turnaround medium_brown / frame light
  - Gabe identity 0.10 (different_person): off-model on eyewear, facial_hair - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven

</details>

### Shot 1B - FAIL

**Aggregate scores:**
- character_presence: 0.80
- character_identity: Leo: 1.00, Mia: 0.75
- character_wardrobe: Leo: 0.80, Mia: 0.80
- location_match: 0.70
- continuity: 0.70
- artifacts: 0.60

**Failure reasons:**
- artifacts 0.60 (couch tears, lighting bloom, blurry edges)

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1B.png)
- presence: 0.80 (observed: Leo, Mia | missing: none | unexpected: none)
- identity[Leo]: 1.00 (same_character) - every compared attribute matches the turnaround
- identity[Mia]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: skin_tone: turnaround tan / frame light; hair_styling: turnaround ponytail / frame worn_loose; face_shape: turnaround round / frame oval
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | skin_tone | tan | light |
  | hair_styling | ponytail | worn_loose |
  | face_shape | round | oval |
- wardrobe[Leo]: 0.80 (expected: green dinosaur-pattern pajamas, hugging plush T-Rex) - The pajamas match the manifest description and the plush T-Rex is present.
- wardrobe[Mia]: 0.80 (expected: casual home wear (partial frame edge)) - Mia is visible at the frame edge wearing casual clothing as described.
- location: 0.70 - The couch and window match the plate, though the couch shows new wear and tear.
- continuity: 0.70 [same location] - The storm and character wardrobe are consistent with the previous shot.
- artifacts: 0.60 - detected: couch tears, lighting bloom, blurry edges - There are significant texture anomalies on the couch and lighting inconsistencies.
- model commentary: The couch appears damaged with tears not present in the location plate. | Lighting on the characters is slightly inconsistent with the room's light sources. | Minor texture blurring on the background elements.
- keyframe overall_pass: False
  - artifacts 0.60 (couch tears, lighting bloom, blurry edges)

</details>

### Shot 1C - FAIL

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Nina: 0.75, Gabe: 0.10, Jenny: 0.40
- character_wardrobe: Nina: 1.00, Gabe: 1.00, Jenny: 1.00
- location_match: 0.80
- continuity: 1.00
- artifacts: 0.90

**Failure reasons:**
- Gabe identity 0.10 (different_person): off-model on eyewear, facial_hair - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven
- Jenny identity 0.40 (significant_drift): off-model on hair_texture - hair_texture: turnaround curly / frame straight

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1C.png)
- presence: 1.00 (observed: Nina, Gabe, Jenny | missing: none | unexpected: none)
- identity[Nina]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: build: turnaround average / frame slim; face_shape: turnaround round / frame heart
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | build | average | slim |
  | face_shape | round | heart |
- identity[Gabe]: 0.10 (different_person) - off-model on eyewear, facial_hair - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_texture | wavy | straight |
  | build | heavy_set | average |
  | eyewear **(defining)** | thin_wire_rectangular | heavy_dark_rectangular |
  | facial_hair **(defining)** | stubble | clean_shaven |
  | face_shape | round | oval |
- identity[Jenny]: 0.40 (significant_drift) - off-model on hair_texture - hair_texture: turnaround curly / frame straight
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_texture **(defining)** | curly | straight |
  | face_shape | oval | round |
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress, putting on earrings) - Nina is wearing a black formal dress and is shown putting on earrings as described.
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (background)) - Gabe's tuxedo matches the manifest and is consistent with the wardrobe reference image.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail (background, on phone)) - Jenny is wearing casual clothing with her hair in a ponytail while using a phone.
- location: 0.80 - The room is recognizably the same living room, though the camera has tracked to a different angle near the front door.
- continuity: 1.00 [same location] - The storm outside and the general room lighting are consistent with the previous shot.
- artifacts: 0.90 - detected: none - Minor blurring on Gabe's face in the background, but no major artifacts detected.
- model commentary: The location matches the plate despite the camera movement toward the door. | All characters are present and wearing the correct manifest-defined wardrobe. | Gabe's tuxedo is consistent with the provided wardrobe reference image. | The storm continuity is maintained through the window.
- keyframe overall_pass: False
  - Gabe identity 0.10 (different_person): off-model on eyewear, facial_hair - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven
  - Jenny identity 0.40 (significant_drift): off-model on hair_texture - hair_texture: turnaround curly / frame straight

</details>

### Shot 1D - FAIL

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Gabe: 0.10, Nina: 0.75, Mia: 0.75, Leo: 0.40, Jenny: 0.10
- character_wardrobe: Gabe: 1.00, Nina: 1.00, Mia: 1.00, Leo: 1.00, Jenny: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

**Failure reasons:**
- Gabe identity 0.10 (different_person): off-model on eyewear, facial_hair - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven
- Leo identity 0.40 (significant_drift): off-model on hair_colour - hair_colour: turnaround blonde / frame dark_brown
- Jenny identity 0.10 (different_person): off-model on hair_texture, skin_tone - hair_texture: turnaround curly / frame straight; skin_tone: turnaround medium_brown / frame light

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1D.png)
- presence: 1.00 (observed: Gabe, Nina, Mia, Leo, Jenny | missing: none | unexpected: none)
- identity[Gabe]: 0.10 (different_person) - off-model on eyewear, facial_hair - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_texture | wavy | straight |
  | build | heavy_set | average |
  | eyewear **(defining)** | thin_wire_rectangular | heavy_dark_rectangular |
  | facial_hair **(defining)** | stubble | clean_shaven |
  | face_shape | round | long_and_narrow |
- identity[Nina]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: build: turnaround average / frame slim; face_shape: turnaround round / frame oval
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | build | average | slim |
  | face_shape | round | oval |
- identity[Mia]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: hair_length: turnaround mid_back / frame shoulder; skin_tone: turnaround tan / frame medium_brown; hair_styling: turnaround ponytail / frame worn_loose
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_length | mid_back | shoulder |
  | skin_tone | tan | medium_brown |
  | hair_styling | ponytail | worn_loose |
- identity[Leo]: 0.40 (significant_drift) - off-model on hair_colour - hair_colour: turnaround blonde / frame dark_brown
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_colour **(defining)** | blonde | dark_brown |
  | hair_texture | wavy | straight |
- identity[Jenny]: 0.10 (different_person) - off-model on hair_texture, skin_tone - hair_texture: turnaround curly / frame straight; skin_tone: turnaround medium_brown / frame light
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_colour | dark_brown | black |
  | hair_texture **(defining)** | curly | straight |
  | skin_tone **(defining)** | medium_brown | light |
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (slightly rumpled), checking watch) - Gabe is wearing a black tuxedo with a bow tie and is checking his wristwatch as described.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress) - Nina's black formal dress matches the manifest and is consistent with the wardrobe reference image.
- wardrobe[Mia]: 1.00 (expected: casual home wear (background, on couch)) - Mia is wearing the same purple star-patterned shirt seen in the wardrobe reference.
- wardrobe[Leo]: 1.00 (expected: green dinosaur-pattern pajamas (background, on couch)) - Leo's green dinosaur pajamas are a perfect match for the wardrobe reference image.
- wardrobe[Jenny]: 1.00 (expected: casual teen, dark brown hair in ponytail, on phone (background, oblivious)) - Jenny's grey hoodie and ponytail match the wardrobe reference and manifest description.
- location: 1.00 - The living room set matches the location plate, including the couch, armchair, and window with lightning.
- continuity: 1.00 [same location] - The scene is perfectly continuous with the previous shot in terms of lighting, weather, and character outfits.
- artifacts: 1.00 - detected: none - No significant generation artifacts or physics violations are detected in this frame.
- model commentary: All characters are present and correctly dressed according to the manifest and consistency references. | The location is consistent with the provided plate and the previous shot. | Gabe's interaction with the wristwatch prop is correctly depicted. | The background characters maintain their established positions and activities.
- keyframe overall_pass: False
  - Gabe identity 0.10 (different_person): off-model on eyewear, facial_hair - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven
  - Leo identity 0.40 (significant_drift): off-model on hair_colour - hair_colour: turnaround blonde / frame dark_brown
  - Jenny identity 0.10 (different_person): off-model on hair_texture, skin_tone - hair_texture: turnaround curly / frame straight; skin_tone: turnaround medium_brown / frame light

</details>

### Shot 1E - FAIL

**Aggregate scores:**
- character_presence: 0.70
- character_identity: Jenny: 0.40
- character_wardrobe: Jenny: 0.70
- location_match: 0.70
- continuity: 0.70
- artifacts: 0.70

**Failure reasons:**
- Jenny identity 0.40 (significant_drift): off-model on skin_tone - skin_tone: turnaround medium_brown / frame light

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1E.png)
- presence: 0.70 (observed: Jenny | missing: none | unexpected: none)
- identity[Jenny]: 0.40 (significant_drift) - off-model on skin_tone - skin_tone: turnaround medium_brown / frame light
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_texture | curly | wavy |
  | skin_tone **(defining)** | medium_brown | light |
  | face_shape | oval | heart |
- wardrobe[Jenny]: 0.70 (expected: casual teen, dark brown hair in ponytail, head tilted down at phone) - The character wears a grey hoodie which fits the casual teen description, though it is darker than the previous shot.
- location: 0.70 - The background shows the same couch and window with storm lighting, though heavily blurred as requested.
- continuity: 0.70 [same location] - The storm and room lighting remain consistent with the previous shot, though the hoodie color appears slightly more muted.
- artifacts: 0.70 - detected: none - The image is clean with no major physical violations or indoor lightning artifacts.
- model commentary: The hoodie color is a darker grey compared to the previous shot's blue-grey tone. | The shallow depth of field correctly isolates the character as per the camera instructions.
- keyframe overall_pass: False
  - Jenny identity 0.40 (significant_drift): off-model on skin_tone - skin_tone: turnaround medium_brown / frame light

</details>

### Shot 1F - PASS

**Aggregate scores:**
- character_presence: 1.00
- location_match: 0.80
- continuity: 0.80
- artifacts: 0.70

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1F.png)
- presence: 1.00 (observed: none | missing: none | unexpected: none)
- location: 0.80 - The TV model and surrounding furniture match the location plate, though the angle is much tighter.
- continuity: 0.80 [same location] - The storm lighting and room layout are consistent with the previous shot's background.
- artifacts: 0.70 - detected: indoor lightning overlap, distorted scan lines - The lightning bolt appears to be rendered on top of the window frame rather than behind it.
- model commentary: Lightning bolt overlaps the window frame, breaking depth. | TV screen distortion is slightly inconsistent with the plate's cartoon style. | The blue time-warp flash is present as requested. | Scan lines and flickering effects are well-executed.
- keyframe overall_pass: True

</details>

### Shot 1G - FAIL

**Aggregate scores:**
- character_presence: 0.80
- character_identity: Mia: 0.75, Leo: 1.00, Nina: 0.75, Gabe: 0.10
- character_wardrobe: Mia: 0.80, Leo: 0.80, Nina: 0.80, Gabe: 0.80
- location_match: 0.80
- continuity: 0.80
- artifacts: 0.70

**Failure reasons:**
- Gabe identity 0.10 (different_person): off-model on build, eyewear, facial_hair - build: turnaround heavy_set / frame slim; eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1G.png)
- presence: 0.80 (observed: Mia, Leo, Nina, Gabe | missing: none | unexpected: none)
- identity[Mia]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: hair_length: turnaround mid_back / frame shoulder; hair_texture: turnaround curly / frame tightly_curled; skin_tone: turnaround tan / frame medium_brown; hair_styling: turnaround ponytail / frame worn_loose
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_length | mid_back | shoulder |
  | hair_texture | curly | tightly_curled |
  | skin_tone | tan | medium_brown |
  | hair_styling | ponytail | worn_loose |
- identity[Leo]: 1.00 (same_character) - every compared attribute matches the turnaround
- identity[Nina]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: build: turnaround average / frame slim; skin_tone: turnaround light / frame pale; face_shape: turnaround round / frame heart
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | build | average | slim |
  | skin_tone | light | pale |
  | face_shape | round | heart |
- identity[Gabe]: 0.10 (different_person) - off-model on build, eyewear, facial_hair - build: turnaround heavy_set / frame slim; eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_texture | wavy | straight |
  | build **(defining)** | heavy_set | slim |
  | eyewear **(defining)** | thin_wire_rectangular | heavy_dark_rectangular |
  | facial_hair **(defining)** | stubble | clean_shaven |
  | face_shape | round | long_and_narrow |
- wardrobe[Mia]: 0.80 (expected: casual home wear (OTS, back of head visible)) - The purple shirt with white stars matches the consistency reference perfectly.
- wardrobe[Leo]: 0.80 (expected: green dinosaur-pattern pajamas (OTS, PJs visible)) - The green pajamas with dinosaur print are consistent with the established reference.
- wardrobe[Nina]: 0.80 (expected: elegant black formal dress (background, preparing)) - The black formal dress matches the style and color of the date-night reference.
- wardrobe[Gabe]: 0.80 (expected: black tuxedo (background, preparing)) - The tuxedo with bow tie is consistent with the provided wardrobe reference.
- location: 0.80 - The living room layout, including the TV, window with storm, and lamps, matches the location plate.
- continuity: 0.80 [same location] - The storm outside and the living room setting are consistent with the previous shot.
- artifacts: 0.70 - detected: minor lighting anomalies - Minor lighting inconsistencies on the characters' hair, but no major physical violations.
- model commentary: Character presence and wardrobe are highly consistent with the manifest and references. | The location matches the plate with correct furniture and environmental effects. | Continuity is maintained from the previous shot in the same room. | No significant artifacts or physics violations were detected.
- keyframe overall_pass: False
  - Gabe identity 0.10 (different_person): off-model on build, eyewear, facial_hair - build: turnaround heavy_set / frame slim; eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven

</details>

### Shot 1H - PASS

**Aggregate scores:**
- character_presence: 0.70
- character_identity: Mia: 0.75
- character_wardrobe: Mia: 0.80
- location_match: 0.80
- continuity: 0.80
- artifacts: 0.70

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1H.png)
- presence: 0.70 (observed: Mia, Nina, Gabe | missing: none | unexpected: Nina, Gabe)
- identity[Mia]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: hair_colour: turnaround dark_brown / frame black; skin_tone: turnaround tan / frame medium_brown; hair_styling: turnaround ponytail / frame worn_loose
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_colour | dark_brown | black |
  | skin_tone | tan | medium_brown |
  | hair_styling | ponytail | worn_loose |
- wardrobe[Mia]: 0.80 (expected: casual home wear, looking up at off-screen parents) - Mia is wearing a pink patterned t-shirt and jeans, which aligns with the casual home wear description.
- location: 0.80 - The living room set matches the location plate, featuring the same window, lamp, and storm atmosphere.
- continuity: 0.80 [same location] - The lighting, storm, and Mia's wardrobe are consistent with the previous shot in the same location.
- artifacts: 0.70 - detected: unexpected background characters, minor lighting bleed - The lightning bolt appears to overlap the window frame slightly, and the parents' presence is unexpected.
- model commentary: Unexpected characters Nina and Gabe are visible in the frame despite the manifest only listing Mia. | The lightning effect slightly overlaps the window pane geometry. | The camera framing is a close-up as requested, but includes partial figures of other characters.
- keyframe overall_pass: True

</details>

### Shot 1I - FAIL

**Aggregate scores:**
- character_presence: 1.00
- character_identity: Gabe: 0.10, Nina: 0.75
- character_wardrobe: Gabe: 1.00, Nina: 1.00
- location_match: 1.00
- continuity: 1.00
- artifacts: 1.00

**Failure reasons:**
- Gabe identity 0.10 (different_person): off-model on build, eyewear - build: turnaround heavy_set / frame slim; eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular

<details><summary>Per-keyframe detail</summary>

**Keyframe first** (scene-01-1I.png)
- presence: 1.00 (observed: Gabe, Nina | missing: none | unexpected: none)
- identity[Gabe]: 0.10 (different_person) - off-model on build, eyewear - build: turnaround heavy_set / frame slim; eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | hair_texture | wavy | straight |
  | build **(defining)** | heavy_set | slim |
  | eyewear **(defining)** | thin_wire_rectangular | heavy_dark_rectangular |
  | face_shape | round | long_and_narrow |
- identity[Nina]: 0.75 (minor_drift) - on-model; differs only on pose/lighting-sensitive attributes: build: turnaround average / frame slim; face_shape: turnaround round / frame heart
  | attribute | turnaround sheet | this frame |
  |---|---|---|
  | build | average | slim |
  | face_shape | round | heart |
- wardrobe[Gabe]: 1.00 (expected: black tuxedo (conflicted expression)) - The tuxedo matches the manifest and is consistent with the wardrobe reference image.
- wardrobe[Nina]: 1.00 (expected: elegant black formal dress (sharp glare)) - The black formal dress matches the manifest and the wardrobe reference image.
- location: 1.00 - The entryway matches the location plate perfectly, including the coat rack, console table, and window.
- continuity: 1.00 - The storm and lighting are consistent with the previous shot, despite the change in sub-location.
- artifacts: 1.00 - detected: none - No visible artifacts or physics violations detected.
- model commentary: Character presence and wardrobe are perfectly aligned with the manifest and references. | The location matches the provided plate with high fidelity. | Lighting and environmental effects are consistent with the established scene context.
- keyframe overall_pass: False
  - Gabe identity 0.10 (different_person): off-model on build, eyewear - build: turnaround heavy_set / frame slim; eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular

</details>
