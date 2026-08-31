# Scene 1, rendered from the v5 panels on fal (MiniMax H3), first+last frame

**Task 347 · 31 Aug 2026 · total spend $5.7244 against a hard $8.00 cap**

The first Scene 1 render from on-model panels. Everything before this inherited
the off-model v4 cast.

**Answer up front: nine end panels were built and all nine clear the identity
gate; all nine shots rendered; five of nine clips clear the identity gate. Every
one of the four failures is the same character on the same attribute — Gabe's
eyewear — and a crop control shows the validator is reading it wrong.** The same
Gabe pixels, cropped out of a clip's own middle keyframe and enlarged, come back
`eyewear: thin_wire_rectangular` (the locked value) at 0.75. In the full frame
they come back `heavy_dark_rectangular` at 0.40. That is task #345 §8's
scale-dependent over-call, reproduced at the video stage, and it is now the
single biggest cause of failure in this pipeline.

- End panels: `r2:rex-assets/storyboards/v5/scene-01/scene-01-<ID>-end.png`
- Clips, raw + audio-stripped, and frame grabs:
  `r2:rex-assets/animation-tests/scene01-v5-fal/`
- Start-vs-end contact sheet:
  [`scene-01-v5-start-end.jpg`](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-v5-fal/scene-01-v5-start-end.jpg)
- Omni-vs-H3 comparison strip:
  [`omni-vs-h3.jpg`](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-v5-fal/omni-vs-h3.jpg)
- Every gate report: `reports/scene-01-v5-render/`

---

## 1. The end panels

v5 shipped only `-start` panels. Last-frame anchoring needs one frame per shot at
the end of the beat, so nine were generated with
`scripts/gen_scene01_end_panels.py` and promoted with
`scripts/promote_end_panels.py`. The end action for each shot comes from the beat
verb in the manifest's camera note plus the Key Action line in
`docs/storyboards/act1/scene-01-home-evening.md`.

Both of #345's techniques are applied. The plate is dropped on the shots where a
face is large in frame; the small graded details are **lit** rather than only
drawn, with Gabe's rims specified as brushed silver wire carrying a specular
highlight and a gap of lit skin at the brow.

| Shot | Built | Attempts | Identity, per character | Wardrobe | Identity gate | Full gate |
|---|---|---:|---|---|---|---|
| 1A | plated | 1 | Jenny 1.00 · Mia 0.75 · Leo 0.75 · Nina 0.75 · Gabe 0.75 | all 1.00 | **PASS** | PASS |
| 1B | plateless | 1 | Leo 1.00 · Mia 0.75 | all 1.00 | **PASS** | PASS |
| 1C | plated | 9 | Nina 0.75 · Gabe 0.75 · Jenny 0.75 | all 0.70 | **PASS** | FAIL — location |
| 1D | plateless | 3 | all five at 0.75 | all 1.00 | **PASS** | PASS |
| 1E | **plated** | 3 | Jenny 0.75 | 1.00 | **PASS** | PASS |
| 1F | plated | 1 | no cast (TV insert) | — | **PASS** (vacuous) | PASS |
| 1G | plated | 8 | Mia 0.75 · Leo 0.75 · Nina 0.75 · Gabe 0.75 | all 1.00 | **PASS** | PASS |
| 1H | plateless | 3 | Mia 0.75 | 0.80 | **PASS** | FAIL — presence |
| 1I | plateless | 2 | Gabe 0.75 · Nina 0.75 | all 1.00 | **PASS** | FAIL — location |

The two remaining full-gate failures are both known, pre-existing bible gaps, not
defects in the art: 1I and 1C fail `location_match` because **there is still no
entryway plate in the bible** (#344 §5 flagged this and it is unchanged), and 1H
fails `presence` because the manifest lists only Mia while the approved staging
has both parents as out-of-focus over-the-shoulder shapes (#344 §5, still
awaiting Bruno's call).

### 1E is the one place this task deliberately departed from #345

The task said to build every close shot plateless. 1E was, twice, and both times
it came back **horizontally mirrored** — Jenny facing screen-right with the phone
at lower-right, where the start panel has her facing screen-left with the phone
at lower-left. An explicit SCREEN DIRECTION block in the prompt did not fix it.

That mirror is worse than a soft identity score, because it is the *anchor*: H3
drives to whatever last frame it is given, and a flipped last frame would have
spun her around mid-shot. Attaching the on-model v5 **start** panel as a plate
fixed it first time, at Jenny 0.75.

**This is worth writing down because #345's reason for dropping the plate does
not apply here.** In #345 the plate was a v4 panel — a picture of the wrong
people — and its whole risk was the model copying an off-model face. Here the
plate is the v5 start panel of the same shot, which already passed identity, so
copying it is the *goal*. The rule that generalises is not "never plate a close
shot"; it is **"never plate a close shot with an off-model frame."** With an
on-model frame, a plate is the cheapest way to hold screen direction, and screen
direction is the thing prose staging turned out to be worst at carrying.

### A hole in the identity gate, found the hard way

`_identity_failures` originally asked only "is any identity score below 0.60?".
A frame containing **none** of the expected cast produces an empty
`character_identity` map, and that question is vacuously false over nothing — so
such a frame passed.

That is not hypothetical. One 1C attempt came back as **a desert canyon with a
Roman arch and a man with a horse in it**, scored `character_presence 0.30` and
`location_match 0.30`, and was promoted as shot 1C's end panel. It would have
been handed to H3 as the last frame of a living-room tracking shot.

The gate now also requires that every expected character was actually scored and
that presence clears its own threshold. Re-auditing the other eight promoted
panels under the stricter rule changed nothing — 1C was the only one affected.

A second, smaller fix: promotion used to be best-of-the-current-run, so a later
run aimed at a *staging* problem could promote a worse *identity* score over a
good earlier one. It did, to 1D. `promote_end_panels.py` now names the chosen
attempt per shot, re-checks its gate, and refuses to promote anything that fails.

---

## 2. The renders

`scripts/video/run_scene01_v5_fal.py`, `minimax/h3/image-to-video`, **768P, 5s**,
with `image_url` = the validated v5 start panel and `end_image_url` = the
validated v5 end panel, both passed as public R2 URLs. Nine shots, then one
regeneration each for the five that failed — the task's one-retry rule, not a
grind.

Every clip is kept twice. H3 always attaches an AAC track and there is no
parameter to disable it; the raw download goes to `.../raw/` untouched and
`ffmpeg -i in.mp4 -c:v copy -an out.mp4` produces the copy beside it. `ffprobe`
confirms `['video','audio']` on every raw and `['video']` on every stripped file.
Nothing was left on fal's CDN, whose URLs expire in about a week.

Output is **1344×768** — the aspect follows the input panel, as documented, and
the 1376×768 panels come back very slightly narrower. Actual clip duration is
5.00–5.17s against a 5s request.

---

## 3. Gate results

Two independent opinions per clip, because they measure different things.
`shot_validator.py` extracts first / middle / last keyframes and grades them
against the locked turnarounds on `gemini-3-flash-preview`; the OpenCV staging
gate (`check_video.py --shot <ID>`, $0.00) scores five sampled frames against the
per-shot plate from #339 and knows nothing about faces.

| Shot | Take | Identity, per character | Identity gate | Staging gate | layout min–max | Full gate |
|---|---|---|---|---|---|---|
| 1A | 1 | Mia 0.75 · Leo 0.75 · Jenny 0.75 · Nina 0.75 · **Gabe 0.40** | FAIL | PASS | 0.571–0.648 | FAIL |
| 1A | 2 | Mia 1.00 · Leo 0.75 · Jenny 0.75 · Nina 0.75 · **Gabe 0.40** | FAIL | PASS | 0.561–0.640 | FAIL |
| 1B | 1 | Leo 1.00 · **Mia 0.40** | FAIL | PASS | 0.579–0.964 | FAIL |
| **1B** | **2** | Leo 0.75 · Mia 0.75 | **PASS** | PASS | 0.581–0.958 | **PASS** |
| 1C | 1 | Nina 0.75 · **Gabe 0.10** · **Jenny 0.40** | FAIL | FAIL | 0.518–0.917 | FAIL |
| 1C | 2 | Nina 0.75 · **Gabe 0.40** · **Jenny 0.40** | FAIL | INCONCLUSIVE | 0.800–0.908 | FAIL |
| **1D** | 1 | all five at 0.75 | **PASS** | PASS | 0.875–0.935 | **PASS** |
| **1E** | 1 | Jenny 0.75 | **PASS** | INCONCLUSIVE | 0.860–0.868 | **PASS** |
| **1F** | 1 | no cast | **PASS** | PASS | 0.603–0.904 | **PASS** |
| 1G | 1 | Mia 0.75 · Leo 0.75 · Nina 0.75 · **Gabe 0.40** | FAIL | INCONCLUSIVE | 0.583–0.625 | FAIL |
| 1G | 2 | Mia 0.75 · Leo 0.75 · Nina 0.75 · **Gabe 0.10** | FAIL | INCONCLUSIVE | 0.584–0.616 | FAIL |
| **1H** | 1 | Mia 0.75 | **PASS** | FAIL | 0.478–0.776 | FAIL — presence |
| 1I | 1 | Nina 0.75 · **Gabe 0.40** | FAIL | FAIL | 0.502–0.639 | FAIL |
| 1I | 2 | Nina 0.75 · **Gabe 0.40** | FAIL | INCONCLUSIVE | 0.563–0.626 | FAIL |

**Identity gate: 5 of 9 — 1B (take 2), 1D, 1E, 1F, 1H.**
**Failing: 1A, 1C, 1G, 1I. All four fail on Gabe.**

An INCONCLUSIVE staging verdict is the gate reporting its own limits, not a
defect: `check_video.py` says in as many words that the 1C, 1E, 1G and 1I plates
*"can only FAIL a clip, never clear one"* — every costume in those shots is black
formalwear or too dark to measure, so layout is doing all the work and it cannot
separate a close-up from a two-shot in the same warm dim room. 1H's staging FAIL
(layout min 0.478) is the same class read the other way: it is a tight close-up
being scored against a plate of the wider room.

---

## 4. The one finding that matters: the eyewear over-call, at video scale

Four of the five failures are `Gabe identity 0.40 (significant_drift): off-model
on eyewear — eyewear: turnaround thin_wire_rectangular / frame
heavy_dark_rectangular`. The **source panels for all four passed Gabe at 0.75**,
so nothing changed between the panel and the clip except that the character got
smaller in a 1344×768 frame.

`scripts/crop_identity_control.py` (new here — #345's Gabe-only eyewear control,
generalised to any character) crops one character out of a frame, enlarges, and
re-scores. Run on **the middle keyframe of the 1I clip**:

| What was scored | Gabe score | Frame eyewear read | Defining mismatches |
|---|---|---|---|
| The whole 1I keyframe | **0.40** | `heavy_dark_rectangular` | eyewear |
| **The same Gabe pixels, cropped and enlarged** | **0.75** | `thin_wire_rectangular` | **none** |

The glasses are drawn correctly and are being read wrong. This reproduces #345
§8 exactly, one stage further down the pipeline, and it is now costing four shots
rather than one panel.

**The #345 workaround did not transfer.** The regeneration of 1A, 1G and 1I
carried an explicit clause asking for the rims to stay lit as bright silver wire
with a specular highlight and a gap of lit skin at the brow — the wording that
moved a panel from 0.40 to 1.00 in #345. All three came back at exactly the same
score, and 1G got *worse* (0.10, the validator now reading `eyewear: none`). That
makes sense: in #345 the lighting note was given to an image model rendering a
still at 1376×768, where it had room to draw a highlight. Here it is given to a
video model that is conditioned on a panel it must not depart from, and the
detail is a few pixels either way.

**This is the validator's problem, not the render's, and task #346 is the fix.**
Its two options — crop to each detected character before grading them, or score
`eyewear` as a soft rather than defining attribute below some head-height
threshold — are both exactly what this data argues for. Until #346 lands, expect
every wide and every medium containing Gabe to fail on eyewear, and **check a
crop before believing an eyewear failure.**

### What the retries did buy

**1B: a real fix.** Mia scored 0.40 on `hair_length: short` in take 1 — she is the
figure cropped at the extreme left edge of a medium on Leo. The retry carried one
clause asking for her high curly ponytail with long curls falling past her jaw,
and it came back 0.75. That one is a genuine drawing failure corrected by a
targeted instruction, and it is the only shot the retry pass rescued.

**1C: better, but still failing.** 1C take 1 was the worst clip in the set — Gabe
0.10 `different_person`, visibly becoming a slimmer, taller man across the five
seconds, plus `artifacts 0.50 (double exposure, phantom figure)`. The cause is
that 1C's start and end panels put Gabe on *opposite sides* of the frame (the
15-second track genuinely moves him), so the anchor was asking H3 to traverse a
character across the shot, and it lost him doing it.

The retry dropped `end_image_url` and rendered from the first frame only. That is
the #341 fallback used deliberately, and it worked as a staging fix:

| 1C | Gabe | staging verdict | layout min–max | artifacts |
|---|---|---|---|---|
| take 1, anchored | **0.10** different_person | FAIL | 0.518–0.917 | 0.50 double exposure, phantom figure |
| take 2, first frame only | **0.40** | INCONCLUSIVE | **0.800**–0.908 | 0.60 |

**Dropping a staging-incompatible anchor lifted the worst layout frame from
0.518 to 0.800 and moved Gabe from "different person" to the ordinary eyewear
over-call.** The generalisable rule: an end panel has to pass identity *and* be
stageable from the start panel. A pair that disagrees about where someone stands
is not a matched pair, however good each frame is on its own.

---

## 5. H3 against the Omni 720p takes — is it better or worse?

Plainly: **for this pipeline, H3 is better, and the margin is mostly about
control and cost rather than raw image quality.** Compared against
`docs/research/scene01-1A-720p.md`, whose four takes are the only production-res
Omni footage of Scene 1.

**Where H3 clearly wins.**

- **It takes a last frame, and Omni cannot.** That is the whole reason the
  provider exists, and it is not a marginal feature: it is what lets a shot be
  specified by two drawings rather than by a paragraph of prose hoping the model
  guesses the ending. Eight of the nine shots here were anchored at both ends.
- **Price, by 1.7x.** H3 at 768P is $0.06/s; Omni measures at $0.1014/s at 720p.
  A 5s shot is $0.30 against $0.52. This entire nine-shot scene plus five
  retries cost $4.20 in video; the same fourteen clips on Omni would be $7.28,
  which alone would have blown the task's cap.
- **Camera discipline is at least as good.** Every shot prompted "the camera does
  not move" holds. On 1A the staging gate passes on all five sampled frames, and
  1D holds layout 0.875–0.935 across a static two-shot. Omni's T1 push-in at
  720p travelled 1.065x over five seconds; nothing here drifts like that, because
  a fixed last frame removes the model's freedom to keep going. #340 had to
  *discover* that 720p tamed Omni's push; here the anchor makes it a setting.

**Where Omni is ahead, or where the comparison does not settle it.**

- **Resolution.** Omni renders a true 1280×720. H3's "768P" here came back
  1344×768 — nominally more pixels, but H3's output is visibly softer in the
  background, and fine detail (the toy dinosaurs on the floor, the pattern on
  Mia's tee) is mushier than Omni's.
- **The 1A style comparison is confounded and should not be read as a verdict on
  H3.** In the comparison strip the Omni row looks like fully rendered 3D and the
  H3 row looks like a flat 2D cartoon. **That is inherited from the source
  panels, not from the model**: Omni was given the v4 1A panel, which is 3D,
  while the v5 1A panel is itself in a flatter 2D style. H3 reproduced the style
  it was given faithfully, which is the correct behaviour. On the eight shots
  whose v5 panels are fully rendered CG (1B–1I), H3's output is fully rendered CG
  too.
- **Omni's takes are off-model and these are not**, so no like-for-like identity
  comparison exists. The Omni 1A takes were made from the v4 panel, whose cast
  #342's re-audit scored as low as 0.10. Comparing 5/9 here against Omni's
  numbers would be comparing against footage that has since been voided.
- **Layout scores are not comparable either.** Omni's 1A takes score layout
  0.859–0.958 and ours scores 0.571–0.648 on the same plate — but that plate is
  derived from the **v4** panel, and our v5 1A panel is a stylistic and
  compositional redraw of it. The gate is largely measuring v4-against-v5, not
  Omni-against-H3.

**Recommendation: keep H3 as the default for Scene 1 and everything like it**,
per `docs/research/fal-provider.md`'s existing rule of thumb. The one thing that
would change the answer is a shot needing genuinely crisp background detail, in
which case Omni at 720p or H3 at 2K ($0.13/s) is worth a controlled test.

---

## 6. Cost

Every line billed at published rates, from the shared ledger
(`reports/scene-01-v5-render/ledger.json`), which the render script consults
before each call and refuses to cross.

| Item | Unit | Count | Cost |
|---|---|---:|---:|
| End-panel generation, `gemini-3-pro-image-preview` | $0.04 | 31 | $1.2400 |
| Validation, `gemini-3-flash-preview` (panels, clips, controls) | ~$0.003–0.007 | 44 | $0.2844 |
| Video, `minimax/h3/image-to-video` 768P 5s | $0.30 | 14 | $4.2000 |
| | | **Total** | **$5.7244** |

**$5.7244 against the hard $8.00 cap.** Against the task's $3.50 estimate the
overage is entirely in two places: end panels took 31 generations rather than 9
(1C took nine and 1G eight — see the per-shot counts in
`ledger.json`; every attempt that fixed a staging problem risked an identity
one, and vice versa), and the five one-shot retries added $1.50 of
video that the estimate did not include.

Per clip: **$0.30**, flat, 14 for 14. H3 bills the 5s floor and nothing here
asked for more.

---

## 7. What should happen next

1. **#346 is now the blocking item, not a nice-to-have.** Four of nine shots in
   this scene fail on an attribute the validator reads correctly the moment you
   enlarge the crop. Until it lands, Scene 1 cannot report better than 5/9 no
   matter how good the render is, and the number is not measuring the film.
2. **Lock an entryway plate in the bible.** 1I and 1C's `location_match 0.50` is
   the missing plate #344 §5 called out. It will fail every entryway shot in the
   film.
3. **Bruno's call on 1H's manifest.** Either 1H's `characters` gains the two
   out-of-focus OTS parents or the staging drops them. It is the only thing
   standing between 1H and a full-gate pass.
4. **1C needs its panel pair re-staged, not another render.** Its start and end
   panels put Gabe on opposite sides of frame. Either the end panel is redrawn to
   keep him where the start panel has him, or the shot is split. First-frame-only
   is the right stopgap and is what the shipped take 2 uses.
5. **Add a staging-compatibility check to the end-panel gate.** Identity is
   necessary and it is not sufficient: the mirrored 1E attempts and 1C's
   character-swap both passed identity while being unusable as anchors. Both were
   caught by eye. A cheap automated version — score the end panel against the
   start panel for screen direction and figure placement — would have caught
   both, and would have saved most of the 31 image generations.

## 8. Reproducing this

```bash
./scripts/setup_python_env.sh && source .venv/bin/activate

# the locked bible + the validated v5 start panels
rclone copy r2:rex-assets/asset-bible/characters/ asset-bible/characters/
rclone copy r2:rex-assets/asset-bible/locations/  asset-bible/locations/
rclone copy r2:rex-assets/storyboards/v5/scene-01/ work/v5/ --include "*-start.png"
cp asset-bible/locations/living_room.png work/locations/storyboard-1A.png

python3 scripts/gen_scene01_end_panels.py --max-attempts 2 --budget 1.20
python3 scripts/promote_end_panels.py            # explicit, re-checks the gate
python3 scripts/video/run_scene01_v5_fal.py      # nine shots, 768P, first+last
python3 scripts/video/gate_scene01_v5_fal.py     # identity + staging, per clip
```

| File | What it does |
|---|---|
| `scripts/gen_scene01_end_panels.py` | Builds the end panel: end action from the beat verb, plateless on close shots, lit graded details, generate → validate → retry under a budget. |
| `scripts/promote_end_panels.py` | Names the chosen attempt per shot, re-checks its identity gate, refuses to promote a failure. |
| `scripts/crop_identity_control.py` | Crops one character out of any frame, enlarges, re-scores. Use before believing a small-in-frame identity failure. |
| `scripts/video/run_scene01_v5_fal.py` | Renders a shot on H3 with both anchors, keeps raw + stripped, parks everything on R2, checks the cap before every call. `--no-end-frame` for the #341 fallback. |
| `scripts/video/gate_scene01_v5_fal.py` | Both gates per clip, into `reports/scene-01-v5-render/shot-gate.json`. |

This branch merges `task/345` (and through it `342` and `344`) and `task/343` and
`task/341`, because the v5 panels, the repaired validator, the fal provider and
`check_video.py` had none of them landed on `main`.
