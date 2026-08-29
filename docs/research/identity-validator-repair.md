# Repairing the identity validator

**Task 342 · 2026-08-29 · total spend $0.63 against a $6.00 cap**

`scripts/validate/shot_validator.py` is the gate that CLAUDE.md's Validation
Gates rule depends on: *"every panel MUST pass validation against the
turnarounds before any video is generated from it."* It could not fail.

---

## 1. What it did before

The validator sent the vision model the character turnarounds as real image
parts, a ~400-line rubric, and a JSON schema with a `score` field, and asked it
to rate identity 0.0–1.0. On the v4 Scene 1 panel set
(`reports/audit-v4/scene-01-audit.md`, now voided) it returned **1.00 on every
character, every shot, every metric, with zero reasons flagged**, and
per-character notes that were boilerplate with the name swapped:

> *"Mia's face, hair, skin tone, and build perfectly match the turnaround reference."*
> *"Leo's face, hair, skin tone, and build perfectly match the turnaround reference."*
> *"Jenny's face, hair, skin tone, and build perfectly match the turnaround reference."*

Also visible in that JSON, and worth stating plainly: `location_ref` was `null`
on all nine panels and `location_match` was **1.00** on all nine. It scored a
comparison it had been handed nothing to compare against.

## 2. Proving it, before changing anything

An adversarial control set was built and the **unmodified** validator run
against it. Eleven cases, ground truth established by a human looking at the
images: the real 1D panel, a deliberate mislabel, the seven `panel-01 MVP` Veo
clips in which Jenny is blonde, and a true positive.

**Result: identity 1.00 on 11 of 11 cases.** Including the mislabel — where
Jenny's turnaround was supplied as the file named `nina_turnaround_APPROVED.png`
— which came back *"Nina's face, hair, skin tone, and build perfectly match the
turnaround reference."*

Two cases returned overall FAIL, and neither was for an identity reason: one on
presence (unexpected characters), one on Leo's wardrobe. The identity path never
fired once.

Raw: `reports/validator-controls/BEFORE-gemini-2.5-flash.json`.

## 3. Diagnosis

The task listed four candidates. Three were tested and eliminated; the fourth
was the bug, and a fifth was found on the way.

**Not the images.** The same model, the same `_encode_image` path, the same
bytes — asked to *describe* rather than *score* — got it right immediately:

> *"IMAGE A: dark brown, high ponytail with loose curls, coral hooded
> sweatshirt, medium brown skin. IMAGE C: blonde, high ponytail. Is C the same
> person as A? **No.** The person in IMAGE C has blonde hair, while the person
> in IMAGE A has dark brown hair."*

Turnarounds arrive at 1408×768 after downscaling, which is ample. Image
delivery was never broken.

**Not primarily the model.** `gemini-2.5-flash` — the model that had just
returned 1.00 across the board — produced that correct free-form comparison
with thinking disabled. It could see the difference the whole time. It was
never asked to look.

**The bug: the task shape.** A model shown a reference, shown a frame, and
asked for a number will produce the agreeable number. Four hundred lines of
"be honest, false-pass is worse than false-fail" did not move it, because
nothing in the output structure forced it to state a single specific
observation before scoring.

**And a fifth thing, found while fixing it: reference images anchor the
answer.** This one was a surprise and it drove the final architecture. Twice,
measurably:

- With Gabe's turnaround in context, the model reported him wearing *thin wire
  glasses and stubble* in a Veo clip where he is plainly clean-shaven with **no
  glasses at all** (verified by cropping the frame). Without the turnaround, it
  read `eyewear: none` correctly.
- With a prior shot's keyframe attached as a wardrobe-consistency reference, it
  read Leo as blonde in panel 1D — where he is **brown-haired and brown-eyed**.
  Without it, `hair_colour: dark_brown`.

Anything the grader can agree with, it will agree with. The fix is not to warn
it more sternly; it is to take away the thing it is agreeing with.

**Aggregation was a real second bug.** Identity was averaged across a shot's
three keyframes. A character off-model in one keyframe scored
`(0.10 + 1.00 + 1.00) / 3 = 0.70` and cleared the 0.60 gate. A genuine
per-keyframe failure could not survive to the report.

## 4. What changed

**The model no longer emits an identity score.** It fills in one table of
enumerated observations — what each character *actually looks like in this
frame* — and the diff, the classification and the score are computed in Python
against a locked attribute sheet. A grader that never emits a score cannot
rubber-stamp one.

**The identity observation is its own API call, and the keyframe is the only
image in it.** No turnarounds, no location plate, no prior keyframe, no
wardrobe references. Nothing to agree with. The rest of the rubric — presence,
wardrobe, location, continuity, artifacts — stays in the second call with its
references, because those checks genuinely need them.

**The reference is a locked attribute sheet, not an image.**
`scripts/validate/identity-sheets.json` holds each character's turnaround
expressed in the validator's vocabulary — a bible artifact in exactly the sense
CLAUDE.md means. `build-sheets` drafts it from the turnarounds one character at
a time (one image per call, nothing to anchor to); a human then reads it against
the turnarounds and corrects it. Five corrections were made to the draft, and
one deliberate non-correction is recorded in the file itself.

**Ten attributes on ordinal ladders, with tolerance where reality demands it.**
Each attribute declares the distance at which a difference stops being
explicable by lighting or pose:

| Attribute | Defining at | Why |
|---|---|---|
| `eyewear`, `facial_hair` | 1 step | Design elements. Glasses are not a lighting effect. |
| `apparent_age` | 1 step | Wide bands, read reliably — and see below. |
| `hair_colour` | non-adjacent families | Warm lamplight really does read a shade darker. Blonde↔light brown is lighting; blonde↔dark brown is a different character. |
| `hair_length`, `hair_texture`, `build`, `skin_tone` | 2 steps | One step is drift; two is a redesign. |
| `hair_styling`, `face_shape` | never alone | Hair goes up and down between shots; a face reads differently at 3/4. |

Score: no mismatches → 1.00; soft only → 0.75; one defining → 0.40; two or more
→ 0.10. The gate passes at 0.60, so **one defining mismatch fails a character**.

**The gate is computed in Python.** `overall_pass` was removed from the schema
entirely. The model used to score everything 1.00 *and* declare itself passing.

**Worst keyframe, not mean.** Headline scores are now the minimum across
keyframes; means are still reported under `*_mean` because the spread is
informative.

**A missing location plate is reported, not scored.** `location_match` can now
return `no_reference`, which surfaces as *"location not verified — this is a gap
in the bible, not a pass."* Same for a character with no sheet row.

**Model:** `gemini-2.5-flash` → `gemini-3-flash-preview`, with thinking capped
at `low` (letting it think freely cost up to 38,000 thought tokens on a single
keyframe without improving the answer). 2.5-flash was retested under the new
architecture and still smoothed differences away; 2.5-pro was accurate on the
adversarial cases but failed the true positive, marking on-model Mia as drifted.

## 5. Before and after, same control set

Identity scores per character. The gate is 0.60.

| Case | Truth | Before (2.5-flash) | After (3-flash) |
|---|---|---|---|
| `adv-1D-real` | FAIL | PASS — all five **1.00** | **FAIL** — Gabe 0.10, Jenny 0.10, Leo 0.40 · Mia 0.75 ✓ |
| `adv-1D-mislabel-nina-is-jenny` | FAIL | Nina **1.00** | **FAIL** — Nina 0.10 |
| `tp-1B-panel` (true positive) | PASS | 1.00 (agreeing, not seeing) | **Leo 1.00, Mia 0.75** — both clear the gate |
| `adv-veo2-v1` | FAIL | all **1.00** | **FAIL** — Jenny 0.10, Gabe 0.10 |
| `adv-veo2-v2` | FAIL | all **1.00** | **FAIL** — Jenny 0.10, Gabe 0.10 |
| `adv-veo3-v1` | FAIL | all **1.00** | **FAIL** — Jenny 0.10, Gabe 0.10 |
| `adv-veo3-v2-stable` | FAIL | all **1.00** | **FAIL** — Jenny 0.10, Gabe 0.10 |
| `adv-veo3-v3-ultrastable` | FAIL | all **1.00** | **FAIL** — Jenny 0.10, Gabe 0.10 |
| `adv-veo3-v4-anchored` | FAIL | all **1.00** | **FAIL** — Jenny 0.10, Gabe 0.10 |
| `adv-veo31-v1` | FAIL | all **1.00** | **FAIL** — Jenny 0.10, Gabe 0.10 |
| **11/11 match ground truth** | | **1/11** | **11/11** |

The true positive is the load-bearing row. Without it, "fails everything" would
look identical to "fixed".

Reproduce: `python scripts/validate/controls/run_controls.py --fetch`.
Raw: `reports/validator-controls/{BEFORE-gemini-2.5-flash,AFTER-gemini-3-flash}.json`.

## 6. Cost

Two calls per image — one observation, one rubric.

| | Before | After |
|---|---|---|
| Model | gemini-2.5-flash | gemini-3-flash-preview |
| Control set, 11 images | 41,270 in / 8,455 out | 54,729 in / 11,863 out |
| **Per image** | **$0.0030** | **$0.0042** |
| Scene 1, 9 panels | $0.0236 | $0.0402 |
| A 3-keyframe video shot | ~$0.009 | ~$0.013 |

**About 40% more, and it is four tenths of a cent an image.** A 1,000-shot
feature validates for about $13. This is nowhere near the $0.30-a-shot figure
that would have changed the pipeline's economics.

One honest caveat on the dollars: Gemini 3 Flash preview pricing was not on a
rate card we could cite, so it is costed at the 2.5 Flash rate. Token counts in
every report are exact; only the conversion is an assumption. If it prices like
2.5 Pro instead, multiply by ~4 — still under two cents a panel.

## 7. What it still gets wrong

Stated plainly, because a validator whose limits are undocumented is one nobody
can calibrate against.

**Nina in panel 1D is off-model and the validator passes her (0.75).** She is
slender with mid-back waves; the turnaround is a fuller build with a
shoulder-length bob. Both drifts are *one step* on their ladders, and one step
is the tolerance that stops lighting and pose from failing on-model art. This
was left as a known miss rather than tuned away: promoting Nina's sheet row from
`average` to `heavy_set` would have made 1D fail on build — the answer we
wanted — which is exactly why it was not done. The non-correction is recorded in
`identity-sheets.json` under `_review.left_alone`.

**Figure-to-name assignment weakens as the manifest gets less constraining.**
With the turnarounds withheld, the model matches figures to names using the
manifest's cast list and wardrobe lines. Given a manifest listing only Mia
against a five-person frame, it described Jenny and filed her under Mia. On the
same image with the full cast listed, Mia is assigned correctly. This is the
price of withholding the references, it does not bite in the pipeline (shot
manifests list their whole cast), and it is pinned as a characterization test —
`known-weakness-1D-single-character-manifest` — so a change in either direction
is noticed.

**A single wrong attribute read fails a shot.** Min-across-keyframes plus a
one-defining-mismatch gate is deliberately jumpy: for a gate, a false pass is
worse than a false fail. The mitigation is that every failure now prints the two
attribute rows it came from, so a human can overrule it in seconds:

> `Gabe identity 0.10 (different_person): eyewear: turnaround thin_wire_rectangular / frame heavy_dark_rectangular; facial_hair: turnaround stubble / frame clean_shaven`

**The sheet is only as good as its review.** Identity is now graded against ten
enumerated values per character. If a row is wrong, the validator is confidently
wrong in a way no amount of vision-model quality can rescue. `build-sheets`
prints a review demand for this reason, and
`test_locked_cast_is_pairwise_distinguishable` fails if any two characters'
rows are close enough to be confused — it already caught Mia and Jenny scoring
0.75 against each other, an 8-year-old and a 15-year-old the validator could not
have told apart.

**This is not face recognition.** It compares ten coarse attributes. A character
redrawn with the right hair, build, age and eyewear but a genuinely different
face will pass. Catching that needs a different technique and a different
budget.

## 8. Regression protection

- `scripts/validate/controls/control-set.json` — 11 cases with written ground
  truth, fixtures pulled from R2 on demand.
- `scripts/validate/controls/run_controls.py` — exits non-zero on any deviation,
  **and** guards both degenerate ends: it fails if every case returns PASS
  (rubber-stamping) and it fails if no case scores every character above the
  gate (failing everything).
- `scripts/validate/controls/test_identity_scoring.py` — 20 unit tests, $0.00,
  no network. Covers the ladders, the colour adjacency graph, the gate, the
  min-aggregation fix, and the shipped sheet's internal consistency.

The mislabel control had to be re-pointed during the repair, and that is worth
recording: mislabelling a turnaround *image file* no longer probes anything,
because the fixed validator never sends turnaround images to the grader. The
mislabel moved to the surface that now carries the reference — a sheet row named
Nina holding Jenny's attributes. It fails, 0.10.

## 9. The honest v4 verdict

Re-running the fixed validator over the nine v4 Scene 1 panels:
**7 FAIL, 2 PASS** (`reports/audit-v4/scene-01-audit-v2.md`). The old 9/9 report
is marked VOID in the file itself.

**Gabe is off-model in every panel he appears in** — 1A, 1C, 1D, 1G, 1I — always
the same way: heavy black rectangular frames where the turnaround has thin wire
ones, clean-shaven where the turnaround has stubble, and in 1G and 1I slim where
the turnaround is heavy-set. **Jenny is off-model in 1A, 1C, 1D and 1E**: much
paler than her locked medium-brown skin, and sleek-straight where the turnaround
is curly. **Leo is brown-haired and brown-eyed in 1D** while blonde everywhere
else. 1B fails on the artifacts rubric alone; its identity is clean. 1F (a prop
insert with no characters) and 1H pass.

Per the task, the panels were **not** touched. Regenerating art is a creative
decision and a separate job.
