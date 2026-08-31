# Scene 1 panels, regenerated on-model (v5)

**Task 344 · 2026-08-31 · total spend $1.15 against a $4.00 cap**

The nine v4 Scene 1 panels had the wrong people in them. Task 342's repaired
validator scored `scene-01-1D-start.png` at Gabe 0.10, Jenny 0.10, Leo 0.40,
and re-running it over the whole v4 set gave **7 FAIL, 2 PASS**
(`reports/audit-v4/scene-01-audit-v2.md`). Every video shot is generated from
these panels, so all of it inherited the error.

All nine were regenerated, image-to-image from the locked turnarounds, keeping
the v4 staging. **Eight of nine now clear the identity gate. One does not, and
it is the same character failing on the same attribute in every version: Gabe's
glasses.**

- v5 panels: `r2:rex-assets/storyboards/v5/scene-01/`
- Contact sheet, v4 against v5:
  [`scene-01-v4-vs-v5.png`](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/v5/scene-01/scene-01-v4-vs-v5.png)
- Every rejected attempt is kept under `.../scene-01/attempts/`
- v4 is untouched.

---

## 1. Why v4 was off-model, when v4 was already image-to-image

This is the part worth writing down, because v4 was not a lazy text-prompt job.
`scripts/regen_scene01_v4.py` attached every character's locked turnaround as a
reference image and told the model to match it exactly. It still produced a
different cast.

The cause is in that script's own `CHAR_IDENTITY` blurbs. They contradict
`scripts/validate/identity-sheets.json` — the locked attribute sheet the
repaired validator grades against:

| Character | v4 prompt said | Locked sheet says | v4 audit result |
|---|---|---|---|
| Gabe | "ALWAYS wearing his **black-framed glasses** (signature feature)" | `eyewear: thin_wire_rectangular` | eyewear mismatch in **every** panel he appears in |
| Gabe | "soft build (a bit chubby around the middle)" | `build: heavy_set` | read as slim in 1G, 1I |
| Mia | "curly hair worn **DOWN** (never a bun or tight ponytail)" | `hair_styling: ponytail` | hair drift, 1A/1B/1D/1G/1H |
| Mia | "**light** skin" | `skin_tone: tan` | skin drift |
| Jenny | (skin tone not mentioned at all) | `skin_tone: medium_brown` | read as `light`, 1A/1C/1D/1E |

The generator was being instructed to draw the exact attributes the gate then
failed. Two locked artifacts described the same characters in incompatible
terms, and nobody had reconciled them.

**v5's fix is structural, not a better prompt.** `scripts/regen_scene01_v5.py`
renders every identity line *from* `identity-sheets.json` at run time, through a
`PHRASING` table that maps each enum value to one sentence. The generator and
the gate now read the same source. If a sheet row changes, the prompt changes
with it; they cannot drift apart again.

## 2. Keeping the staging while replacing the people

The task was explicit: the v4 staging passes the continuity gate, only the
characters are wrong. So each v5 panel is generated from **two** kinds of
reference — the character turnarounds, and the corresponding v4 panel as a
staging plate.

Three things were needed to make that work, and each was measured:

**Attaching the v4 panel at full resolution does not work.** The first pass
reproduced the staging perfectly and changed almost nothing about the people:
Gabe still slim and clean-shaven in heavy black frames, Nina still slender with
long waves. The frame in front of the model dominates its own instructions.

**Naming the errors explicitly does work.** A `STAGING_ERRORS` block that says
*"in the staging frame the man in the tuxedo is drawn slim, clean-shaven, in
thick black rectangular glasses; all three are wrong, make him heavy-set, give
him stubble, swap the glasses for thin metal wire"* moved Jenny from 0.40 to
0.75 and Gabe from 0.10 to 0.40 in one step. "Match the turnaround" reads to the
model as a description of a picture it can already see. A stated delta reads as
an edit.

**Downscaling the staging plate to 640px works better still, and it is the
lever that mattered most.** A storyboard's staging — camera, blocking,
furniture, prop placement, light direction — is low-frequency information and
survives a 2× downscale intact. An off-model face does not. With the staging
plate at 640px, attempt 1 of 1A came back Mia 1.00, Jenny 0.75, Nina 0.75,
Leo 0.75 with the composition untouched. Retries shrink it further (512, then
416). This is the single change that decoupled "keep the frame" from "keep the
faces".

Retries also feed the validator's own failure strings back into the next
prompt, plus an explicit instruction that the staging was **not** the reason for
rejection — without that line, a retry fixes the character by pushing the camera
in, which is a different kind of failure.

## 3. Results

Identity is scored per character against the locked sheet by
`scripts/validate/shot_validator.py` on `gemini-3-flash-preview`. The gate is
0.60; the headline is the worst character in the panel. v4 numbers are the
task-342 re-audit, not the voided original.

| Shot | Attempts | v4 worst | v5 worst | v5 identity, per character | v5 wardrobe | Identity gate | Full gate |
|---|---|---|---|---|---|---|---|
| 1A | 3 | 0.10 | **0.75** | Mia 1.00 · Leo 0.75 · Jenny 0.75 · Nina 0.75 · Gabe 0.75 | all 1.00 | PASS | PASS |
| 1B | 1 | 0.75 | 0.75 | Leo 1.00 · Mia 0.75 | all 1.00 | PASS | PASS |
| 1C | 1 | 0.10 | **0.75** | Nina 0.75 · Gabe 0.75 · Jenny 0.75 | all 0.80 | PASS | PASS |
| 1D | 2 | 0.10 | **0.75** | Gabe 0.75 · Nina 0.75 · Mia 0.75 · Leo 0.75 · Jenny 0.75 | all 1.00 | PASS | PASS |
| 1E | 1 | 0.40 | **0.75** | Jenny 0.75 | 0.70 | PASS | PASS |
| 1F | 1 | n/a | n/a | no cast (TV insert) | n/a | PASS (vacuous) | FAIL - artifacts 0.60 |
| 1G | 1 | 0.10 | **0.75** | Mia 0.75 · Leo 0.75 · Nina 0.75 · Gabe 0.75 | all 1.00 | PASS | PASS |
| 1H | 1 | 0.75 | **1.00** | Mia 1.00 | 0.80 | PASS | FAIL - presence 0.50 |
| 1I | 3 | 0.10 | 0.40 | Gabe **0.40** · Nina 0.75 | all 1.00 | **FAIL** | FAIL |
| 1I *(rebuilt, §8)* | 4 | 0.10 | **1.00** | Gabe 1.00 · Nina 0.75 | all 1.00 | **PASS** | FAIL - location 0.50 |

**Identity gate: 8 of 9 pass in this run; 9 of 9 after the §8 rebuild of 1I.** Six v4 panels failed on identity (1A, 1C, 1D,
1E, 1G, 1I); **five of those six pass in this run and the sixth passes after
the §8 rebuild**, and no panel regressed. Every character that was scoring 0.10
or 0.40 in v4 — Gabe in 1A/1C/1D/1G, Jenny in 1A/1C/1D/1E, Leo in 1D — is now
at or above 0.75.

Wardrobe holds at 0.70-1.00 across the set. Jenny is in her coral hoodie with
her phone in every panel she appears in, which is the standing do-not-invent
rule and was broken in all four of her v4 panels.

### Attempts and cost

26 image generations in total. **15 belong to the graded run** over the nine
panels (14 saved attempts plus one empty response on 1F, see below); the other
11 were spent working out the approach in §2 — the full-resolution-staging pass
that changed nothing, and the staging-fidelity wording that over-corrected.
23 validation calls.

| | Unit | Count | Cost |
|---|---|---|---|
| Image generation, `gemini-3-pro-image-preview` | $0.04 | 26 | $1.040 |
| Validation, `gemini-3-flash-preview` | ~$0.0049 | 23 | $0.112 |
| | | **Total** | **$1.152** |

One 1F call returned a candidate with no content parts and crashed the driver
with `TypeError: 'NoneType' object is not iterable`. `generate_panel` now
reports `finish_reason` and returns False instead, and the loop resumes from a
partial `summary.json` rather than starting over.

Against a $4.00 cap. The budget guard in `run_scene01_v5_gate.py` refuses to
start an attempt that would cross the cap; it never fired.

---

## 4. The one panel that would not come good: Gabe's glasses in 1I

> **Superseded by §8.** Task 345 rebuilt 1I without the staging plate and it
> now passes the identity gate at Gabe 1.00. The diagnosis below was right
> about the plate; its recommended inpaint fix turned out not to be needed.

**1I used all three attempts and failed all three, identically:**

> `Gabe identity 0.40 (significant_drift): off-model on eyewear - eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular`

This is a real defect, not a validator artifact, and it is worth separating from
the wide shots because the two behave differently.

**In the wide shots the validator was over-calling it.** In 1A attempt 1 the
rendered Gabe has visibly thin metal rims — cropped and enlarged, you can see
the skin of his brow through the frame — and the validator still returned
`heavy_dark_rectangular`. At the scale Gabe occupies in a five-person wide shot
his rims are a few pixels and read as a dark line. Those panels came good on a
later attempt.

**In 1I the validator is right.** 1I is a close two-shot; Gabe's head fills a
sixth of the frame. He is drawn in unmistakably thick black plastic frames in
all three attempts. The generator would not let go of them at close range —
almost certainly because his v4 staging plate shows heavy black frames at large
scale, and the downscale that defeats that anchor in a wide shot does not defeat
it when the face is that big in the source.

Everything else in 1I is right: Nina 0.75, wardrobe 1.00 both, presence 1.00,
no artifacts. It is one attribute on one character.

Per the task's three-attempt cap, this was stopped and reported rather than
chased. **Recommended next step for whoever picks it up:** a targeted inpaint /
edit pass on the glasses region alone, rather than another whole-frame
regeneration — the panel is otherwise good and re-rolling it risks the
composition.

## 5. Three findings that are not panel defects

These fail the *full* gate but are not things to fix in the art. Flagging them
so nobody regenerates good panels chasing them.

**1F fails artifacts 0.60 for "indoor lightning, distorted screen graphics".**
The distorted screen graphics are the shot. The manifest's own `key_props` for
1F ask for "cartoon imagery distorted by static", "horizontal scan lines", "blue
time-warp flash" and "lightning flash reflected in screen". The validator is
penalising the brief. Either the artifacts rubric needs a per-shot exemption
when the manifest asks for distortion, or 1F needs a manifest note. It is a
validator/manifest disagreement, not a bad panel.

**1H fails presence 0.50 for "unexpected: Adult Male, Adult Female".** The
manifest lists only Mia for 1H. The approved v4 panel has both parents as
out-of-focus over-the-shoulder foreground shapes, and v5 preserved them because
preserving the staging was the instruction. The same v4 frame scored presence
0.70 in the task-342 audit, so this is partly run-to-run variance in the
validator too. **This needs Bruno's call:** either the manifest's `characters`
list for 1H gains the two OTS parents, or the staging drops them. v5 changed
nothing here.

**1I fails location 0.50 because there is no entryway plate in the bible.** 1I
is the front hall, the manifest says so explicitly in its camera note, and the
validator falls back to comparing against the living-room plate. `asset-bible/`
has four location plates and none of them is the entryway. That is a gap in the
bible, and it will fail every entryway shot in the film until a plate is locked.

## 6. Residual drift the gate tolerates

Worth knowing before these panels are used as video keyframes.

**Nina still reads slimmer and longer-haired than her turnaround** in 1A, 1C and
1D — `build` and `face_shape` come back as soft mismatches in every panel she
is in. This is the known miss documented in
`docs/research/identity-validator-repair.md` §7: her sheet row is `average`,
she reads between `slim` and `heavy_set`, the ladder has no rung there, and
promoting the row was deliberately not done. v5 improved her hair length
materially (the v4 mid-back glamour waves are gone; she is at or near the
shoulder bob now) but her build is still a one-step drift the gate accepts. If
Bruno wants Nina's build genuinely locked, the ladder needs a rung, not a
better prompt.

**Run-to-run variance on the same prompt is large.** In the graded run, 1A's
three attempts came from a byte-identical prompt on attempts 1 and 2 and
returned Gabe at 0.10, then 0.10, then 0.75 on the third (which carried the
retry note). Attempt 1 of 1A was generated five times across the session from
four prompt variants and returned Gabe at 0.40, 0.40, 0.40, 0.40 and 0.10. A
single attempt is not evidence about a prompt, and the three-attempt loop is
doing real work: three of the nine panels needed more than one attempt.

## 7. Reproducing this

```bash
# fetch the locked bible + the v4 staging plates
rclone copy r2:rex-assets/asset-bible/characters/ asset-bible/characters/
rclone copy r2:rex-assets/asset-bible/locations/  asset-bible/locations/
rclone copy r2:rex-assets/storyboards/v4/scene-01/ work/v4/ --include "*-start.png"
cp asset-bible/locations/living_room.png work/locations/storyboard-1A.png

# generate -> validate -> retry, 3 attempts per panel, hard budget cap
python3 scripts/run_scene01_v5_gate.py --max-attempts 3 --budget 4.00

# v4-vs-v5 contact sheet
python3 scripts/make_scene01_contact_sheet.py --out work/scene-01-v4-vs-v5.png
```

| File | What it does |
|---|---|
| `scripts/regen_scene01_v5.py` | Builds the prompt from `identity-sheets.json` + the manifest, attaches the downscaled v4 staging plate and the turnarounds, generates one panel. |
| `scripts/run_scene01_v5_gate.py` | The gate loop: generate, validate, feed failures back, cap at 3, stop at the budget. Keeps a spend ledger. |
| `scripts/make_scene01_contact_sheet.py` | The v4-vs-v5 sheet, with both versions' scores printed on it. |
| `scripts/regen_scene01_v5.py --no-staging-plate` | Plateless build (§8): no v4 panel attached, staging carried as prose from `PLATELESS_STAGING`. |
| `scripts/run_1I_plateless.py` | The §8 gate loop for 1I: 4 attempts, $1.00 cap, `--start-attempt` to stop and look at the pixels mid-run. |
| `scripts/eyewear_control.py` | Validates an arbitrary image as if it were a panel. Used in §8 to prove the eyewear over-call by re-scoring a crop of the same panel. |

Two notes for the next agent. `docs/process/do-not-invent.md` and
`docs/process/scene-01-manifest.json`, both named in the task, **do not exist in
this repo on any branch** — the manifest lives at
`asset-bible/manifests/scene-01.json`, and the do-not-invent rules are stated in
`asset-bible/BIBLE.md` "How to use" plus the task text (Jenny is hoodie +
phone). And this branch merges `task/342-fix-the-identity-validator-cap-6`,
because the repaired validator this work is gated on had not landed on `main`.

---

## 8. 1I, rebuilt without the staging plate (task 345)

**Task 345 · 2026-08-31 · spend $0.180 against a $1.00 cap · 4 attempts**

Section 4 above stopped 1I at 0.40 on Gabe's eyewear and blamed the v4 staging
plate: heavy black frames at large scale in a close two-shot, where the
downscale that defeats that anchor in a wide shot does not. That diagnosis was
right, and dropping the plate fixed it.

**1I now passes the identity gate at Gabe 1.00, Nina 0.75.** Every one of
Gabe's ten graded attributes matches the locked turnaround, eyewear included:

> `"notes": "every compared attribute matches the turnaround"`

| | v4 | v5 (§4, with plate) | v5.1 (this run, plateless) |
|---|---|---|---|
| Gabe identity | 0.10 | 0.40 | **1.00** |
| Nina identity | 0.40 | 0.75 | 0.75 |
| Gabe / Nina wardrobe | - | 1.00 / 1.00 | 1.00 / 1.00 |
| presence · continuity · artifacts | - | 1.00 · 1.00 · 1.00 | 1.00 · 1.00 · 0.90 |
| location_match | - | 0.50 | 0.50 |
| **Identity gate** | FAIL | **FAIL** | **PASS** |
| Full gate | FAIL | FAIL | FAIL - location only |

The one remaining full-gate failure is `location_match 0.50`, which is §5's
missing entryway plate, not a defect in the art: the validator says so in as
many words — *"the keyframe shows a foyer/entryway which is a different
sub-location than the living room shown in the location plate."* Nothing in
this panel will move that number until an entryway plate is locked in the
bible.

- Panel: `r2:rex-assets/storyboards/v5/scene-01/scene-01-1I-start.png`
- Rejected attempts: `.../attempts/scene-01-1I-start-plateless-p{1,2,3}.png`
  (the three plated attempts from §4 stay at `...-a{1,2,3}.png`)
- Validator JSON, controls and ledger: `reports/scene-01-1I-plateless/`

### What changed

`scripts/regen_scene01_v5.py` gains a plateless path (`--no-staging-plate`).
With it, the v4 panel is not attached at any resolution — **the only images the
generator sees are the locked turnarounds** — and the staging travels as prose
in `PLATELESS_STAGING`, written by reading the v4 frame: camera height and
distance, figure scale, both poses, the set left to right, the floor, and the
direction and colour of the light. Everything else is unchanged from §2, so 1I
is built from the same identity sheet, the same wardrobe block and the same
style block as the other eight. `scripts/run_1I_plateless.py` is the gate loop,
capped at 4 attempts and $1.00.

### Is it the technique, or was it the fourth roll of the dice?

Both, and the split matters, because §6 already warns that a single attempt is
not evidence about a prompt.

**What the plate removal bought on its own** is the *body*, immediately and on
every attempt. Gabe comes back genuinely heavy-set — the paunch, the wide
chest, the round full face — from attempt 1, where three plated attempts had
all read `build: average` with `face_shape` soft-mismatched. That is the plate's
grip being gone, and it is not luck: it held across all four plateless rolls.

**The glasses took one more thing.** Plateless attempts 1-3 scored an identical
Gabe 0.40 on `eyewear: heavy_dark_rectangular`, exactly as the plated ones had.
So before spending the last attempt, both controls in
`reports/scene-01-1I-plateless/` were run — `scripts/eyewear_control.py`, which
feeds the validator an image as if it were a panel:

| Control panel | Gabe score | Frame eyewear read |
|---|---|---|
| The locked Gabe turnaround, front view, cropped | 0.75 | `thin_wire_rectangular` |
| **The same Gabe pixels cropped out of plateless attempt 1** | **1.00** | `thin_wire_rectangular` |
| Plateless attempt 1, whole panel | 0.40 | `heavy_dark_rectangular` |

The second row is the finding. Attempt 1's Gabe scores a perfect 1.00 with the
eyewear read correctly when he is cropped out of his own panel and shown to the
same validator — the identical pixels, only larger in frame. **The glasses were
already right and the validator was over-calling at panel scale**, which is
§4's wide-shot behaviour appearing in a two-shot as well, at a head height of
about a sixth of the frame.

Knowing that, attempt 4 was aimed at the readout rather than at the drawing: it
asked for the rims as brushed silver wire with a specular highlight along the
top, a clear gap of lit skin between rim and brow, and more warm key on Gabe's
face. That is not a departure from the sheet — `thin_wire_rectangular` already
says "catching a small metallic highlight" — it is the same frames drawn so
they survive being small. It scored 1.00 first time.

### Is this worth reusing?

**Yes, for close shots, and it is worth doing before the first attempt rather
than after three failures.** Two separate reusable lessons:

1. **Drop the staging plate on any shot where a face is large in frame.** The
   plate is a good lever on a wide shot (§2) and a bad one here: what it
   contributes — camera, blocking, set dressing, light — is exactly the part
   that survives being written down, while what it costs is the part that gets
   copied off an off-model face. Writing the staging as prose took one careful
   look at the v4 frame and cost nothing per attempt. Every close-up and
   two-shot in the film should be built this way; 1A-1H, all wider, are fine as
   they are and were not touched.
2. **Light the graded detail, don't just draw it.** A hairline rim drawn
   correctly and then lost in a dim warm key reads to the validator as a solid
   dark frame. Asking for the specular highlight and the gap of lit skin is
   what moved 0.40 to 1.00 on pixels that were already correct. This applies to
   any small high-contrast graded attribute — rims, earrings, freckles — and it
   is a cheaper fix than another whole-frame regeneration.

Section 4's recommended next step was a targeted inpaint of the glasses region.
That was not needed and is not the general answer; the panel was regenerated
whole, four times, for $0.18.

### A validator issue this leaves open, and it is not 1I's

The gate reads `heavy_dark_rectangular` off pixels it reads as
`thin_wire_rectangular` when the same character is larger in the frame. 1I
worked around it by lighting the rims. That works, but it means the eyewear
score is partly a function of how big the head is, and §4 already recorded the
same over-call on the wide shots. **Worth a task of its own:** either the
identity pass should crop to each detected character before grading them, or
`eyewear` should be scored as a soft rather than a defining attribute below
some head-height threshold. Until then, expect small-in-frame Gabe to cost
extra attempts, and check a crop before believing an eyewear failure.
