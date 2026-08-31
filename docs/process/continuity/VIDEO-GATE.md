# The video continuity gate

`check_video.py` scores a video shot against the locked Scene 1 plate. It exists
because CLAUDE.md's Validation Gates rule requires that "every shot is validated
against the bible before it can be stitched", and until now that validation was
a human squinting at a clip — which makes any model bake-off a matter of opinion.

**Cost: $0.00 per clip.** OpenCV and ffmpeg. No vision API, no network, nothing
billable. Run it on everything.

---

## Quick start

```bash
pip install opencv-python-headless numpy      # plus ffmpeg on PATH

cd docs/process/continuity
python check_video.py /path/to/shot.mp4 --shot 1A
echo $?     # 0 pass, 1 fail or inconclusive, 2 usage error
```

Gating a pipeline:

```bash
for f in shots/*.mp4; do
    python check_video.py "$f" --shot 1A || { echo "BLOCKED: $f"; exit 1; }
done
```

Machine-readable, for the orchestrator:

```bash
python check_video.py shot.mp4 --shot 1A --json > report.json
jq -r '.verdict, .failing_checks[]' report.json
```

---

## Files

| File | What it is |
|---|---|
| `check.py` | The still-frame gate. All the geometry lives here. |
| `check_video.py` | Samples frames from a clip and runs `check.py` on each. Wrapper only — it reimplements none of the geometry. |
| `scene-01-plate.json` | Where to look in the plate and how close is close enough. Regions, colour swatches, thresholds. |
| `plate/scene-01-1A-plate.jpg` | Pinned 512px copy of the locked plate. |
| `bible/scene-01.json` | Pinned copy of the Scene 1 manifest. |
| `score_corpus.py` | Reproduces the table below. |
| `test_continuity_gate.py` | 54 tests. `python -m pytest test_continuity_gate.py -v` |

The plate and the manifest are **pinned snapshots** of the locked originals, so
the gate runs with no flags and no network. Refresh them when the bible changes:

```bash
rclone copy r2:rex-assets/asset-bible/manifests/scene-01.json bible/
rclone copy r2:rex-assets/storyboards/v4/scene-01/scene-01-1A-start.png /tmp/
ffmpeg -i /tmp/scene-01-1A-start.png -vf scale=512:-2 -q:v 3 plate/scene-01-1A-plate.jpg
```

---

## Flags

| Flag | Default | What it does |
|---|---|---|
| `--frames N` | `5` | How many evenly spaced frames to sample. Times are slice midpoints, so neither the very first nor the very last frame is used — the first frame of an image-to-video clip is just the source panel and would pass trivially. |
| `--tolerate N` | `0` | Allow N *failing* frames before the clip fails. For the case where one sample lands on a lightning flash. It cannot rescue an INCONCLUSIVE clip. |
| `--shot ID` | none | Manifest shot id (`1A`, `1B`, …). Enables the wardrobe check and tells the gate the intended framing. |
| `--plate PATH` | pinned copy | Override the locked plate. |
| `--plate-spec PATH` | `scene-01-plate.json` | Override regions and thresholds. |
| `--bible PATH` | pinned copy | Override the manifest. |
| `--json` | off | Emit JSON instead of text. |
| `--keep-frames DIR` | off | Write the sampled frames out so you can look at what the gate looked at. |
| `--allow-inconclusive` | off | Exit 0 instead of 1 when nothing could be measured. |
| `-v` | off | Show passing frames and passing checks too. |

Each of `--plate`, `--plate-spec` and `--bible` also reads from the environment
(`CONTINUITY_PLATE`, `CONTINUITY_PLATE_SPEC`, `CONTINUITY_BIBLE`). Resolution
order is CLI flag → environment → pinned repo copy.

---

## The four checks

| Check | Measures | Catches |
|---|---|---|
| `staging_orientation` | Frame's left band vs the plate's TV band and right band vs the plate's chair band, then the same comparison crossed. | The room mirrored — Jenny's chair landing screen-left of the TV. |
| `layout_match` | Mean hue/saturation-histogram correlation across eight named plate regions. | "This is a different living room." |
| `couch_occupancy` | Share of the couch band that is not bare upholstery, as a ratio of the plate's own. | Kids vanished, or a crowd added. |
| `wardrobe` | Per-character costume-colour coverage vs the plate. | Leo out of his dinosaur pajamas, Mia out of the magenta top. |

Each returns PASS, FAIL or **n/a**. n/a is not a pass — see below.

### Three verdicts, not two

- **PASS** — at least one check ran and nothing failed.
- **FAIL** — more frames failed than `--tolerate` allows.
- **INCONCLUSIVE** — no check could be applied to any frame. Exits 1. A clip
  nobody measured has not been cleared, and reporting that as PASS is exactly
  the failure the Validation Gates rule exists to prevent.

---

## Scored: every Scene 1 clip on R2

24 clips, 5 frames each, run 2026-08-29. Full JSON:
`reports/continuity-video-gate-2026-08-29.json`. Reproduce with
`score_corpus.py` (rclone lines are in its docstring).

`frames` is one character per sample, in time order: `P` pass, `F` fail.

| Family | Clip | Shot | Frames | Verdict | Failing |
|---|---|---|:--:|---|---|
| Phase 0 Omni | `G1_text_to_video.mp4` | – | `FFFFF` | FAIL | layout, wardrobe |
| Phase 0 Omni | `G2_image_to_video.mp4` | 1A | `PPPPP` | **PASS** | – |
| Phase 0 Omni | `G3_image_to_video.mp4` | 1A | `PPPPF` | FAIL | layout (last frame only) |
| Phase 0 Omni | `G4_reference_to_video.mp4` | – | `FFFFF` | FAIL | layout, wardrobe |
| Phase 0 Omni | `PROBE_12refs.mp4` | 1A | `FFFFF` | FAIL | layout, wardrobe |
| Seedance/mitte | `01-shot-1A.mp4` | 1A | `FFFFF` | FAIL | layout, wardrobe |
| Seedance/mitte | `02-shot-1B.mp4` | 1B | `PPPPP` | **PASS** | – (see caveat) |
| Seedance/mitte | `03-shot-1C.mp4` | 1C | `PPPPP` | INCONCLUSIVE | nothing measurable |
| Seedance/mitte | `04-shot-1D.mp4` | 1D | `PPPPP` | INCONCLUSIVE | nothing measurable |
| Seedance/mitte | `05-shot-1G.mp4` | 1G | `PPPPP` | INCONCLUSIVE | nothing measurable |
| Seedance/mitte | `06-shot-1H.mp4` | 1H | `PPPPP` | INCONCLUSIVE | nothing measurable |
| Seedance/mitte | `07-shot-1I.mp4` | 1I | `PPPPP` | INCONCLUSIVE | nothing measurable |
| Seedance/mitte | `scene-01-parents-leaving.mp4` | 1A | `FFFFF` | FAIL | layout, wardrobe |
| Google Flow | `flow-veo-1A.mp4` | 1A | `FFFFF` | FAIL | layout, wardrobe |
| Google Flow | `flow-veo-1A-frames.mp4` | 1A | `FFFFF` | FAIL | layout, wardrobe, staging |
| Google Flow | `flow-veo-1C.mp4` | 1C | `PPPPP` | INCONCLUSIVE | nothing measurable |
| Google Flow | `flow-omni-1D.mp4` | 1D | `PPPPP` | INCONCLUSIVE | nothing measurable |
| Veo panel-01 | `…veo2-v1.mp4` | 1A | `FFFFF` | FAIL | layout |
| Veo panel-01 | `…veo2-v2.mp4` | 1A | `FFFFF` | FAIL | layout, wardrobe |
| Veo panel-01 | `…veo3-v1.mp4` | 1A | `FFFFF` | FAIL | layout |
| Veo panel-01 | `…veo3-v2-stable.mp4` | 1A | `FFFFF` | FAIL | layout |
| Veo panel-01 | `…veo3-v3-ultrastable.mp4` | 1A | `FFFFF` | FAIL | layout |
| Veo panel-01 | `…veo3-v4-anchored.mp4` | 1A | `FFFFF` | FAIL | layout |
| Veo panel-01 | `…veo31-v1.mp4` | 1A | `FFFFF` | FAIL | layout, wardrobe |

**2 PASS, 15 FAIL, 7 INCONCLUSIVE.**

### What the failures actually are

A frame was pulled from all 15 failing clips and looked at. Verdicts on the
verdicts:

**True positives — the clip really is off the locked plate (14 of 15).**

- `01-shot-1A` (Seedance) — a completely different living room: the TV is a
  flat-panel standing centre frame in front of the windows rather than a CRT at
  screen-left, the couch is a dark grey sectional shot from behind, the lamp,
  the floor and the kitchen are all different. The gate also called it
  *mirrored*, which is the correct read of that staging against the plate.
- `flow-veo-1A` — **three** kids on the couch instead of two, no TV in frame at
  all, popcorn strewn across the rug, Leo in a striped tee rather than dinosaur
  pajamas, and a visible Veo watermark. A textbook continuity break.
- The seven `panel-01 MVP` Veo clips all render one and the same different
  room — cream rolled-arm couch, blue armchair, an open-plan kitchen through an
  arch at centre-left, the TV a huge flat panel hard against the left edge — and
  in all seven **Jenny is blonde**, contradicting the locked turnaround (dark
  brown hair). They predate the v4 plate lock, so failing them is right. Worth
  noting that `v3-stable`, `v3-ultrastable` and `v4-anchored` — the prompt
  variants that were meant to hold composition — score 0.437, 0.440 and 0.368.
  Prompt engineering did not move them toward the plate.
- `flow-veo-1A-frames` — again the wrong room, plus Mia in pink pajamas rather
  than the magenta tee and jeans, Jenny in a coral hoodie, and a Veo watermark.
- `PROBE_12refs` — the cast lined up facing camera with Ruben and Jetplane
  present. Ruben is not in Scene 1 at all. Correct fail.
- `G1_text_to_video` (empty room by design) and `G4_reference_to_video` (a
  two-character reference probe) are not Scene 1 staging and were never meant to
  be. Correct fail, but uninteresting.
- `scene-01-parents-leaving` is a 30s multi-shot assembly. Scoring an assembly
  against a single shot's plate is the wrong question; the FAIL is right but the
  clip should be split before it is gated.

**False positive — 1 of 15.**

- `G3_image_to_video` fails on the **last frame only** (`PPPPF`), with a layout
  score of **0.543 against a 0.55 threshold** — it misses by 0.007. Looking at
  that frame: G3's prompt asked for "a slow, gentle push-in", and over 10 seconds
  (twice G2's duration) the push travels far enough that the TV, the armchair,
  Jenny, the kitchen and the floor have all left frame. Mia and Leo are still
  perfectly on-model. **The shot is fine; the gate is measuring "is the wide
  plate still in frame", and it correctly isn't.** This is the gate's central
  blind spot: it cannot tell reframed-by-design from drifted-off-model. Running
  it with `--tolerate 1` passes G3, which for a push-in shot is the right call.

**False negative — the one that should worry us.**

- `02-shot-1B` **PASSES**, and it should not. It is a medium shot, so all three
  geometry checks are n/a and the verdict rests on a single number: Leo's green
  covering 1.67× the plate's amount. But that green is a **green T-shirt**, not
  the manifest's "green dinosaur-pattern pajamas" — and the room behind him is
  the wrong room. A colour histogram cannot tell a tee from pyjamas. **A PASS
  from this gate on a non-wide shot means very little.** Read `not measured:` in
  the output before trusting a pass.

---

## Honest note on the false-positive rate

On the 17 clips where at least one check applied, the gate raised 15 flags and
**one of them was a false positive (G3) — about 7%** — against **one false
negative out of two passes (1B)**. Two passes is not a sample. Treat both
numbers as an order of magnitude, not a rate.

The layout threshold is the weakest part of that. Measured per frame across the
1A-framed clips:

| | layout_match range |
|---|---|
| The plate itself | 1.000 |
| G2 (from the validated panel) | 0.743 – 0.928 |
| G3 (same panel, longer push-in) | **0.543** – 0.885 |
| Wrong-room clips | 0.163 – **0.556** |

G3's floor (0.543) sits *below* the highest wrong-room frame (0.556, on
`flow-veo-1A-frames`). **The two populations overlap**, so no single threshold
separates them cleanly; 0.55 was chosen to sit in that overlap. A clip scoring
in the 0.50–0.60 band should be looked at by a human rather than trusted either
way.

The specific limits, in the order they will bite:

1. **It only really works on wide establishing shots.** The plate is the 1A
   wide. 7 of 24 clips came back INCONCLUSIVE because a close-up or a medium
   simply does not contain the TV, the armchair or the couch band. Those shots
   need their own plates before they can be gated — the single highest-value
   follow-up.
2. **It cannot distinguish a deliberate camera move from drift.** G3 is the
   proof. A shot with a real push-in or track will leave the plate's framing on
   purpose. `--tolerate 1` is the blunt workaround; per-shot camera-aware
   tolerance is the real fix.
3. **It does not check identity.** It cannot tell Mia from another dark-haired
   girl in a magenta top. That is the paid vision validator's job
   (`scripts/validate/shot_validator.py`, ~$0.02/shot). This gate is the free
   pre-filter that runs first and stops obvious breaks before anyone pays.
4. **Dark costumes are unmeasurable.** Nina's black dress, Gabe's black tux and
   Jenny's grey-blue hoodie each cover 23–26% of the *plate*, because in a dim
   room those colours are most of the frame. The gate disqualifies any swatch
   covering more than 5% of the plate and reports those characters as `no
   swatch` rather than passing them on a meaningless number. Only Mia's magenta
   (0.16% of plate) and Leo's green (0.85%) are real signals.
5. **`staging_orientation` needs `layout_match` to pass first.** Measured on the
   veo3-v4 clips: a correctly staged but entirely different room scored
   straight=0.582 / crossed=0.597 and was called mirrored. Below the layout
   threshold the left/right comparison is noise, so it now reports n/a instead
   of stacking a bogus second reason onto one real break.
6. **`couch_occupancy` is coarse.** It passed `flow-veo-1A`, which has three
   kids on the couch instead of two. It catches an empty couch, not a miscount.

### Where the thresholds came from

`scene-01-plate.json`, tuned against the plate itself plus the clips above:

| Threshold | Value | Why |
|---|---|---|
| `layout_match` | 0.55 | Plate 1.00, G2 0.74–0.93, wrong-room clips 0.16–0.56. The populations overlap; 0.55 sits inside the overlap. |
| `staging_margin` | 0.02 | Straight must beat crossed by this. The plate's own gap is 0.275. |
| `wardrobe_min_ratio` | 0.35 | G2/G3 score 1.2–1.7; the wrong-costume clips 0.19–0.33. |
| `swatch_max_plate_coverage` | 0.05 | Above this a "costume colour" is measuring the room. |
| `couch_occupancy` | 0.45–2.20 | Deliberately wide. This check is a backstop, not a discriminator. |

Re-tune by editing that file — no code change needed — and re-run
`score_corpus.py` to see what moved.

---

## A note on provenance

The task that commissioned this described `check.py` as already existing and
hardcoding `/workspace/...` paths. **It is not in this repo and not in any
branch or commit in its history** — it appears to have been written in a sandbox
that was never committed. So `check.py` here was written fresh to the behaviour
the task described (chair screen-right of the TV, wardrobe, couch occupancy),
with the path handling done properly from the start: CLI flag → environment →
pinned repo default, no absolute paths and no `sys.path` venv insertion. There
was no existing still-image behaviour to preserve, so nothing was broken; but
that also means the still gate is new code that has not been reviewed before.
