# Identity validator: grading each character on their own crop

**Task 346 · 2026-08-31 · spend $0.38 against a $4.00 cap**

Tasks 344 and 345 both lost attempts to the same thing and both worked around
it instead of fixing it:

> The gate reads `heavy_dark_rectangular` off pixels it reads as
> `thin_wire_rectangular` when the same character is larger in the frame.
> — [`scene01-v5-panels.md` §8](scene01-v5-panels.md)

The identity pass now crops to each character before grading them. On the
control set that takes it from **11/13 to 13/13**, and the false FAIL that
started this is gone and stays gone across repeats.

---

## 1. The diagnosis

The identity pass sends the whole keyframe in one call and asks the model to
fill in a ten-attribute row for every character in the manifest. That is one
call, which is cheap, and it is why the check works at all — but it means a
character who is a fourteenth of the frame tall is described from a few hundred
pixels while a character in close-up is described from a few hundred thousand.

The attributes do not degrade evenly. Colour families and build survive at
small scale; the small, high-contrast ones do not. Spectacle rims are the worst
case, because at a few pixels wide a thin dark wire rim and a heavy plastic one
are the same dark line, and the model resolves the ambiguity towards the more
common object.

**This was not run-to-run noise, it was deterministic.** Task 344's 1A attempt
1 — a five-person wide shot, Gabe in the kitchen doorway with a head 55 px tall
in a 1376×768 frame — was validated three times on the whole frame and three
times on a per-character crop:

| | eyewear read | Gabe identity |
|---|---|---|
| whole frame, 3 runs | `heavy_dark_rectangular` ×3 | 0.10 ×3 |
| per-character crop, 3 runs | `thin_wire_rectangular` ×3 | 0.75 ×3 |

Raw runs: [`reports/scale-fix/1A-a1-repeatability.json`](../../reports/scale-fix/1A-a1-repeatability.json).

The panel was correct. Enlarged 6×, lit skin and eyebrow are plainly visible
*through* the rim and the rim is a hairline next to the width of his brow — that
is the locked `thin_wire_rectangular`. The panel was thrown away and regenerated
twice more because the validator could not read it, which is the concrete cost
of this bug: two wasted generations on a panel that was already on-model, and a
trained habit of not believing eyewear failures.

The whole-frame read got two more of Gabe's attributes wrong at the same time
and for the same reason — `hair_colour: black` for dark brown, and
`facial_hair: clean_shaven` for visible stubble. Eyewear was just the one that
crossed a defining threshold.

---

## 2. What changed

All of it in `scripts/validate/shot_validator.py`.

**The whole-frame observation call now also localises.** `head_box_2d` and
`figure_box_2d` were added to `FRAME_OBSERVATION_SCHEMA` as
`[ymin, xmin, ymax, xmax]` in 0–1000 normalised coordinates. They are
**optional** in the schema on purpose: a backend that cannot localise still
returns the attribute table, and the crop pass degrades to the old behaviour
rather than failing. This costs no extra call — it rides on the call that was
already being made.

**Each visible character is then cropped, enlarged and re-described.**
`character_crop_rect()` builds a head-and-upper-body rectangle from the head
box — half a head-height of headroom, 2.6 head-heights of body below the chin,
clipped by the figure box so it does not run past a seated or half-occluded
figure — and `make_character_crop()` writes it out enlarged (LANCZOS, up to 8×,
long edge 1600 px, which is the encoder's ceiling anyway). That crop goes back
to the same model as a fresh observation call with the manifest cut down to
that one character. The crop's reading is what gets graded.

Across the control set the crops magnify by **2.1× to 8.0×, median 5.2×**.

**The prompt tells the model what a crop is.** The crop call says the image was
enlarged from a small region, that the softness is an artefact of enlargement
and not a property of the artwork, and — since rims are the attribute this
exists for — what a thin rim looks like close up versus a heavy one (skin
visible through the frame and a specular highlight, versus a solid opaque band).
It also says to grade the person in the middle and to report `visible=false`
rather than describe someone clipped at the edge.

**Every fallback lands on the old behaviour, never on "pass".** No box, a
degenerate box, a head too small to recover, a crop that would not materially
enlarge the head, or a crop the model says contains nobody — each of those keeps
the whole-frame reading and records why in `character_identity[*].crop.reason`.

**Nothing about the gate changed.** `GATE`, `IDENTITY_ATTRIBUTES`,
`defining_at`, the ordinal ladders, the verdict scores and `_gate_keyframe` are
untouched. This is a change to *what the model is shown*, not to what fails.
`test_crop_pass_does_not_change_the_gate` pins that: a defining mismatch scores
identically whether it came from a crop or from the whole frame.

**It is auditable and it is reversible.** Every scored character now carries
`graded_on` (`crop` / `whole_frame`), the crop rectangle, the magnification, and
`crop_changed` — the list of readings the crop overturned, with the whole-frame
values kept under `wholeframe_attributes`. `--no-identity-crop` on
`validate-shot`, `validate-panel`, `validate-scene` and `run_controls.py`
reproduces the old behaviour exactly, which is how the table below was made.

---

## 3. Before / after on the full control set

Both columns are the same 13 cases, the same fixtures and the same model
(`gemini-3-flash-preview`); the only difference is `--no-identity-crop`.
Raw: [`controls-before.json`](../../reports/scale-fix/controls-before.json),
[`controls-after.json`](../../reports/scale-fix/controls-after.json).

| Case | Kind | Whole frame | Per-character crop |
|---|---|---|---|
| adv-1D-real | adversarial | **REGRESSION** (Leo 0.75, missed) | ok |
| adv-1D-mislabel-sheet-nina-is-jenny | adversarial | ok | ok |
| tp-1B-panel | true-positive | ok | ok |
| known-weakness-1D-single-character-manifest | known-weakness | ok | ok |
| adv-veo2-v1 | adversarial | ok | ok |
| adv-veo2-v2 | adversarial | ok | ok |
| adv-veo3-v1 | adversarial | ok | ok |
| adv-veo3-v2-stable | adversarial | ok | ok |
| adv-veo3-v3-ultrastable | adversarial | ok | ok |
| adv-veo3-v4-anchored | adversarial | ok | ok |
| adv-veo31-v1 | adversarial | ok | ok |
| **scale-1A-a1-gabe-small-correct** | true-positive | **REGRESSION** (Gabe 0.10, `heavy_dark_rectangular`) | **ok** (Gabe 0.75, `thin_wire_rectangular`) |
| **scale-veo3-v1-gabe-small-wrong** | adversarial | ok (Gabe 0.10) | **ok (Gabe 0.10)** |
| | | **11/13** | **13/13** |

Both guards still hold in the crop run: not every case passes (rubber-stamp
guard), and at least one case scores every visible character at or above the
gate (`tp-1B-panel`, clean-pass guard).

### The two new cases

`scale-1A-a1-gabe-small-correct` is 344's 1A attempt 1 — the false FAIL itself.
It asserts `Gabe >= 0.6` **and** that his eyewear was read as
`thin_wire_rectangular`, because a score can come out right for the wrong
reason and an attribute cannot. `expect_frame_attribute` is new in the harness
for this.

`scale-veo3-v1-gabe-small-wrong` is its mirror and the reason the pair means
anything. Same problem shape — Gabe in the far background of a 1280×720 Veo
frame, head about 40 px, *smaller* than the case above — but here he is
genuinely the wrong man: slim, clean-shaven, no glasses at all. The manifest is
cut down to Gabe alone so nothing else can carry the FAIL. He stays at 0.10.
Enlarging pixels of a man with no glasses does not produce glasses.

The blonde-Jenny Veo clips already in the set carry the same load at five
characters a frame: Jenny 0.10 and Gabe 0.10 on all seven, before and after,
unmoved.

### What the crop actually moved

Across the 13 cases there are 50 character readings. The crop changed at least
one attribute in 35 of them, and moved 9 scores:

| Direction | Count | Cases |
|---|---|---|
| up | 5 | scale-1A-a1 Gabe 0.10→0.75; adv-1D-real Gabe 0.10→0.40; adv-veo3-v1 Mia 0.10→0.75; adv-veo2-v2 Mia 0.75→1.00; tp-1B Leo 0.75→1.00 |
| down | 4 | adv-1D-real Leo 0.75→0.40; scale-1A-a1 Leo 0.75→0.40 and Jenny 0.75→0.40; scale-1A-a1 Mia 1.00→0.75 |
| unchanged | 41 | |

Which attributes it overturned, across those 50 readings: `face_shape` 15,
`hair_colour` 12, `hair_texture` 11, `hair_length` 9, `skin_tone` 4,
`facial_hair` 2, `hair_styling` 2, `build` 1, `apparent_age` 1, `eyewear` 1.
The two most-changed are both non-defining, so most of that churn never reaches
the gate.

**adv-1D-real Leo 0.75 → 0.40 is a fix, not a regression**, and it is why the
before column reads 11/13 rather than 12/13. That case's ground truth says in
as many words that Leo's dark brown hair in 1D is *"visible only when you crop
in, and missed on the first human read of this panel"*. On the whole frame the
model called it `light_brown`, one step from blonde, soft, pass. On the crop it
called it `dark_brown`, two steps, defining, fail — which is what the human saw
after cropping in. Same mechanism as Gabe's rims, opposite sign: a small face
being read generously.

---

## 4. What it costs, and what it costs us

`gemini-3-flash-preview`, priced at the 2.5-Flash rate (see the note in
`PRICING`; token counts below are exact, only the dollar conversion is an
assumption).

| | whole frame | per-character crop | × |
|---|---|---|---|
| Control set, 13 images | $0.0597 | $0.1058 | 1.77 |
| **Per image, mean** | **$0.0046** | **$0.0081** | **1.77** |
| 1-character frame | ~$0.0030 | ~$0.0038 | 1.29 |
| 2-character frame | $0.0034 | $0.0051 | 1.52 |
| 5-character frame | ~$0.0050 | ~$0.0097 | 1.93 |

The shape is `1 + N` observation calls per keyframe instead of 1, but the crops
are small images so the marginal call is cheaper than the first one. In
practice:

- **A still panel gate** (1 keyframe): a five-person wide shot goes from half a
  cent to one cent. A nine-panel scene like Scene 1 goes from about **$0.05 to
  about $0.09**.
- **A video shot** (3 keyframes) with 5 characters: from about **$0.015 to about
  $0.029**.
- **A 40-shot act** at 3 keyframes and 3 characters average: roughly **$0.35
  instead of $0.20**.

Set against that: 344's 1A cost three generation attempts, and at least one of
them was spent on a panel the gate had misread. A storyboard panel regeneration
is far more than a third of a cent. The crop pass pays for itself the first time
it prevents one.

It also writes one JPEG per character per keyframe into
`<keyframes-dir>/identity-crops/`. They are small and they are the evidence
behind the score, which is worth keeping for a failed shot.

---

## 5. Two things this made worse, stated plainly

The crop makes the model see more, and it sees more in both directions. On
`scale-1A-a1` two readings moved *below* the gate that were above it before.
Neither is asserted by that case — it asserts Gabe — but neither should be
buried.

**Jenny's skin tone, and it is systematic.** Whole frame reads `tan` (one step
from the locked `medium_brown`, soft, passes) 3 runs out of 3; the crop reads
`light` (two steps, defining, fails) 3 runs out of 3. The likely mechanism is
that skin tone is a *relative* judgement and the crop throws away the frame-wide
exposure it was being judged against: her face carries the warm key light and
the crop is mostly her face and a bright kitchen. Note that §3 of the v5 report
already lists "Jenny read as `light`" as a recurring problem in 1A/1C/1D/1E and
traces it to the bible — her locked description never mentions skin tone at all,
so the generator draws her light. The crop did not invent this; it moved a
pre-existing bible gap one step further and across the gate.

**Leo's apparent age, and it is unstable.** The crop reads `toddler` in 2 runs
of 3 where the whole frame reads `child` 3 of 3. `apparent_age` is
`defining_at: 1`, so `toddler` vs `child` is a hard fail. Magnified, Leo as
drawn in this panel genuinely does read as a two-year-old — round cheeks,
enormous eyes, tiny nose. This is a real risk for a character who is five and
drawn babyish, and it will recur.

Neither was tuned away. Loosening `apparent_age` would have made both numbers
look better and is exactly the move this validator was repaired to stop; the
`toddler`/`child` step defends nothing in the current cast, but changing it on
the strength of one observation is how gates get soft. Both are follow-ups, in
§7.

---

## 6. Why this is not the fallback the task allowed

The task offered a fallback — demote `eyewear` below a head-height threshold —
and said to label it a workaround. That was not needed and would have been
worse: it fixes one attribute, it fixes it only by refusing to check it, and it
leaves `hair_colour`, `facial_hair` and the rest failing the same way (which
they were: Gabe's hair and stubble were both misread on the same frame).

The crop is the class fix. It is also strictly *more* information than the gate
had before, not less — the same pixels, larger. Nothing about it makes a wrong
character easier to pass, and `scale-veo3-v1-gabe-small-wrong` exists to keep
proving that at a head height smaller than the case it was built to fix.

---

## 7. Follow-ups this leaves open

1. **Lock Jenny's skin tone in the bible.** Her locked description does not
   mention it, the generator draws her light, and the sheet says
   `medium_brown`. Until those agree she will keep scoring 0.40 on skin tone at
   any scale. This is a bible fix, not a validator fix, and it needs Bruno.
2. **`apparent_age` on young children.** `toddler` vs `child` is a defining
   step that separates nobody in the current cast — the pair the ladder actually
   defends is Mia (child) against Jenny (teenager), two steps apart. Worth
   revisiting *with a control case that pins it*, not on the strength of one
   panel.
3. **Localisation quality is now load-bearing.** A swapped box means grading the
   wrong person. `known-weakness-1D-single-character-manifest` already shows the
   model picking the wrong figure when the manifest is thin, and cropping will
   act on that mistake rather than blur past it. It still fails there, so
   nothing is hidden, but a box-accuracy control would be worth building.
4. **Cropping per keyframe of a video re-localises from scratch each time.**
   Boxes could be tracked across the three keyframes of a shot instead. Cheap,
   not urgent.

---

## Reproducing this

```bash
# arithmetic half - 34 unit tests, $0.00, no network
python3 -m pytest scripts/validate/controls/test_identity_scoring.py -q

# vision half - 13 cases, needs GEMINI_API_KEY + rclone + ffmpeg
python3 scripts/validate/controls/run_controls.py --fetch \
    --json reports/scale-fix/controls-after.json          # ~$0.11, crop on
python3 scripts/validate/controls/run_controls.py --no-identity-crop \
    --json reports/scale-fix/controls-before.json         # ~$0.06, crop off
echo $?    # 0 = every case matched its written ground truth
```

**Spend for this task: $0.38** — $0.046 establishing the pre-change baseline,
$0.060 + $0.106 for the before/after table, $0.046 for the six repeatability
runs, $0.107 re-running the 13 cases against the final code, and about $0.02 in
one-off probes.
Ledger: [`reports/scale-fix/spend-ledger.json`](../../reports/scale-fix/spend-ledger.json).
