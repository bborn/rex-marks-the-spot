# Scene 1 (orchestrator real run) - Pipeline Orchestrator Run Report

- Generated: 2026-05-22T17:41:16+00:00
- Manifest: `asset-bible/manifests/scene-01.json`
- Generator: `existing_clips`
- Validator: `real`
- Run state file: `footage/scene-01-real-run/scene-01-state.json`
- Governor state file: `footage/scene-01-real-run/governor/run_scene-01-orchestrator-real.json`

## Budget summary

- Up-front estimate for this scene: **$3.5100** (generator + validator, one attempt per shot)
- Per-run cap: **$15.00**  -  actually spent so far: **$7.0200**  -  remaining: **$7.9800**
- Daily cap: **$40.00**  -  spent today: **$7.0200**

## Shot outcomes

- Approved: **2** / 9  -  Escalated: **7**  -  Pending (not yet attempted): **0**

| Shot | Status | Attempts | Last score | Last reasons |
|------|--------|----------|------------|--------------|
| 1A | **escalated** | 2 | 0.88 | per-shot cap 2 reached for shot '1A' |
| 1B | **escalated** | 2 | 0.62 | per-shot cap 2 reached for shot '1B' |
| 1C | **escalated** | 2 | 0.60 | per-shot cap 2 reached for shot '1C' |
| 1D | **escalated** | 2 | 0.73 | per-shot cap 2 reached for shot '1D' |
| 1E | **approved** | 2 | 0.93 |  |
| 1F | **escalated** | 2 | 0.80 | per-shot cap 2 reached for shot '1F' |
| 1G | **escalated** | 2 | 0.77 | per-shot cap 2 reached for shot '1G' |
| 1H | **approved** | 2 | 0.95 |  |
| 1I | **escalated** | 2 | 0.37 | per-shot cap 2 reached for shot '1I' |

## Escalations (for human review)

### 1A

- Reason: per-shot cap 2 reached for shot '1A'
- Last validator reasons:
  - Nina is missing from the shot.
  - Gabe is missing from the shot.
  - Mia's top has white stars, differing from the solid pink reference.
  - Leo's pajamas have a dinosaur pattern, differing from the solid green reference.
  - Mia's shirt pattern does not exactly match the reference.
  - Leo's shirt pattern does not exactly match the reference.
  - Mia's wardrobe does not match the expected casual home wear, instead wearing a pink star-patterned top.

### 1B

- Reason: per-shot cap 2 reached for shot '1B'
- Last validator reasons:
  - Leo's wardrobe does not match the expected green shirt and cargo shorts.
  - Mia's wardrobe does not match the expected pink shirt and jeans.
  - The TV content is a cartoon, not the storm warning from the location plate.
  - Mia is missing from the shot.
  - Leo's wardrobe does not match the expected green t-shirt and cargo shorts, instead wearing pajamas.
  - The TV content does not match the storm warning from the location plate.
  - Model output was truncated; structured fields are incomplete.

### 1C

- Reason: per-shot cap 2 reached for shot '1C'
- Last validator reasons:
  - Nina's wardrobe does not match the expected maroon sweater and jeans from her turnaround.
  - Gabe's identity is not verifiable due to the camera angle.
  - Jenny's wardrobe does not match the expected coral hoodie and gray leggings from her turnaround.
  - Nina's wardrobe does not match her turnaround reference.
  - Gabe's identity cannot be verified due to being obscured.
  - Jenny's identity cannot be verified due to being obscured.
  - Nina's wardrobe is incorrect.
  - Gabe's wardrobe is incorrect.

### 1D

- Reason: per-shot cap 2 reached for shot '1D'
- Last validator reasons:
  - Jenny, an expected character, is missing from the keyframe.
  - Model output was truncated; structured fields are incomplete.

### 1F

- Reason: per-shot cap 2 reached for shot '1F'
- Last validator reasons:
  - The location match score is too low because the keyframe only shows the TV screen, not the living room.
  - The continuity score is too low due to the drastic change in framing from the previous shot.

### 1G

- Reason: per-shot cap 2 reached for shot '1G'
- Last validator reasons:
  - An unexpected character, another girl, is present in the keyframe.
  - Mia's wardrobe does not perfectly match the expected casual home wear, as her top has stars.
  - Model output was truncated; structured fields are incomplete.

### 1I

- Reason: per-shot cap 2 reached for shot '1I'
- Last validator reasons:
  - Gabe's wardrobe does not match the turnaround reference.
  - Nina's wardrobe does not match the turnaround reference.
  - The location in the keyframe does not match the provided location plate.
  - The keyframe lacks continuity with the previous shot's setting and characters.
  - Gabe's identity does not match the turnaround.
  - Nina's identity does not match the turnaround.
  - The location does not match the reference plate.
  - The shot lacks continuity with the previous keyframe.

## Stitched output

- `reports/scene-01-stitched.mp4` (approved clips only)

## Per-shot attempt log

### 1A - escalated

| # | passed | score | gen $ | val $ | error | reasons |
|---|--------|-------|-------|-------|-------|---------|
| 0 | no | 0.81 | $0.2400 | $0.1500 |  | Nina is missing from the shot.; Gabe is missing from the shot. |
| 1 | no | 0.88 | $0.2400 | $0.1500 |  | Nina is missing from the shot.; Gabe is missing from the shot. |

### 1B - escalated

| # | passed | score | gen $ | val $ | error | reasons |
|---|--------|-------|-------|-------|-------|---------|
| 0 | no | 0.62 | $0.2400 | $0.1500 |  | Leo's wardrobe does not match the expected green shirt and cargo shorts.; Mia's wardrobe does not match the expected pink shirt and jeans. |
| 1 | no | 0.62 | $0.2400 | $0.1500 |  | Leo's wardrobe does not match the expected green shirt and cargo shorts.; Mia's wardrobe does not match the expected pink shirt and jeans. |

### 1C - escalated

| # | passed | score | gen $ | val $ | error | reasons |
|---|--------|-------|-------|-------|-------|---------|
| 0 | no | 0.60 | $0.2400 | $0.1500 |  | Nina's wardrobe does not match the expected maroon sweater and jeans from her turnaround.; Gabe's identity is not verifiable due to the camera angle. |
| 1 | no | 0.60 | $0.2400 | $0.1500 |  | Nina's wardrobe does not match the expected maroon sweater and jeans from her turnaround.; Gabe's identity is not verifiable due to the camera angle. |

### 1D - escalated

| # | passed | score | gen $ | val $ | error | reasons |
|---|--------|-------|-------|-------|-------|---------|
| 0 | no | 0.93 | $0.2400 | $0.1500 |  | Jenny, an expected character, is missing from the keyframe.; Gabe's wardrobe does not match the turnaround reference. |
| 1 | no | 0.73 | $0.2400 | $0.1500 |  | Jenny, an expected character, is missing from the keyframe.; Model output was truncated; structured fields are incomplete. |

### 1E - approved

| # | passed | score | gen $ | val $ | error | reasons |
|---|--------|-------|-------|-------|-------|---------|
| 0 | no | 0.93 | $0.2400 | $0.1500 |  | Jenny's hair is down and curly, not in a ponytail as specified in the expected wardrobe. |
| 1 | yes | 0.93 | $0.2400 | $0.1500 |  |  |

### 1F - escalated

| # | passed | score | gen $ | val $ | error | reasons |
|---|--------|-------|-------|-------|-------|---------|
| 0 | no | 0.80 | $0.2400 | $0.1500 |  | The location match score is too low because the keyframe only shows the TV screen, not the living room.; The continuity score is too low due to the drastic change in framing from the previous shot. |
| 1 | no | 0.80 | $0.2400 | $0.1500 |  | The location match score is too low because the keyframe only shows the TV screen, not the living room.; The continuity score is too low due to the drastic change in framing from the previous shot. |

### 1G - escalated

| # | passed | score | gen $ | val $ | error | reasons |
|---|--------|-------|-------|-------|-------|---------|
| 0 | no | 0.96 | $0.2400 | $0.1500 |  | An unexpected character is present in the keyframe.; Nina's wardrobe does not match the expected elegant black formal dress. |
| 1 | no | 0.77 | $0.2400 | $0.1500 |  | An unexpected character, another girl, is present in the keyframe.; Mia's wardrobe does not perfectly match the expected casual home wear, as her top has stars. |

### 1H - approved

| # | passed | score | gen $ | val $ | error | reasons |
|---|--------|-------|-------|-------|-------|---------|
| 0 | no | 0.90 | $0.2400 | $0.1500 |  | Mia's wardrobe does not match the reference turnaround.; The lighting in the keyframe is significantly brighter than the location plate, and the TV is not present as expected. |
| 1 | yes | 0.95 | $0.2400 | $0.1500 |  |  |

### 1I - escalated

| # | passed | score | gen $ | val $ | error | reasons |
|---|--------|-------|-------|-------|-------|---------|
| 0 | no | 0.37 | $0.2400 | $0.1500 |  | Gabe's wardrobe does not match the turnaround reference.; Nina's wardrobe does not match the turnaround reference. |
| 1 | no | 0.37 | $0.2400 | $0.1500 |  | Gabe's wardrobe does not match the turnaround reference.; Nina's wardrobe does not match the turnaround reference. |
