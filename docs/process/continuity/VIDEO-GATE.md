# The video continuity gate

`check_video.py` scores a video shot against the locked plate for its shot. It
exists because CLAUDE.md's Validation Gates rule requires that "every shot is
validated against the bible before it can be stitched", and until now that
validation was a human squinting at a clip — which makes any model bake-off a
matter of opinion.

**Cost: $0.00 per clip.** OpenCV and ffmpeg. No vision API, no network, nothing
billable. Run it on everything.

## One plate per shot

The first version of this gate had exactly one plate — the 1A wide — and 7 of
24 clips came back INCONCLUSIVE because a close-up does not contain the TV, the
armchair or the couch band. Every Scene 1 shot already has a validated v4
storyboard panel in the 9/9 PASS set at `r2:rex-assets/storyboards/v4/scene-01/`,
and those panels are locked, approved artifacts. **A shot's plate is now its own
panel.** Nothing was drawn or generated for the gate; `scene-01-plate.json` grew
from one hardcoded entry to nine registered ones.

A check runs only where that shot's entry gives it the inputs it needs. A close-up
gets no couch check rather than a bogus one, and the output names what ran and
what did not on every clip.

---

## Quick start

```bash
pip install opencv-python-headless numpy      # plus ffmpeg on PATH

cd docs/process/continuity
python check_video.py /path/to/shot.mp4 --shot 1A
echo $?     # 0 pass, 1 fail or inconclusive, 2 usage error
```

Gating a pipeline — pass each clip **its own** shot id, or it is scored against
the wrong plate:

```bash
for f in shots/*.mp4; do
    shot=$(basename "$f" .mp4 | grep -o '1[A-I]$')
    python check_video.py "$f" --shot "$shot" || { echo "BLOCKED: $f"; exit 1; }
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
| `scene-01-plate.json` | One entry per shot: which panel is its plate, where to look in it, how close is close enough. |
| `plate/scene-01-1?-plate.jpg` | Pinned 512px copies of the nine locked panels, 1A through 1I. |
| `bible/scene-01.json` | Pinned copy of the Scene 1 manifest. |
| `score_corpus.py` | Reproduces the corpus table below, and `--cross-shot` reproduces the discrimination matrix. |
| `test_continuity_gate.py` | 111 tests. `python -m pytest test_continuity_gate.py -v` |

The plates and the manifest are **pinned snapshots** of the locked originals, so
the gate runs with no flags and no network. Refresh them when the bible changes:

```bash
rclone copy r2:rex-assets/asset-bible/manifests/scene-01.json bible/
rclone copy r2:rex-assets/storyboards/v4/scene-01/ /tmp/panels/ --include 'scene-01-1?-start.png'
for s in 1A 1B 1C 1D 1E 1F 1G 1H 1I; do
    ffmpeg -i /tmp/panels/scene-01-$s-start.png -vf scale=512:-2 -q:v 3 plate/scene-01-$s-plate.jpg
done
```

That recipe is exactly how the committed jpgs were made — re-running it
reproduces `plate/scene-01-1A-plate.jpg` byte for byte.

---

## Flags

| Flag | Default | What it does |
|---|---|---|
| `--frames N` | `5` | How many evenly spaced frames to sample. Times are slice midpoints, so neither the very first nor the very last frame is used — the first frame of an image-to-video clip is just the source panel and would pass trivially. |
| `--tolerate N` | `0` | Allow N *failing* frames before the clip fails. For the case where one sample lands on a lightning flash. It cannot rescue an INCONCLUSIVE clip. |
| `--shot ID` | `1A` | Manifest shot id (`1A`, `1B`, …). **Selects that shot's plate**, its regions and its wardrobe map. Without it the gate falls back to the spec's `default_shot`. |
| `--plate PATH` | the shot's own | Override the locked plate. Still wins over the shot entry. |
| `--plate-spec PATH` | `scene-01-plate.json` | Override plates, regions and thresholds. A flat spec with no `shots` key still works — that is the pre-per-shot shape. |
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
| `staging_orientation` | Frame's left band vs the plate's left band and right vs right, then the same comparison crossed. On 1A that is the TV band against the armchair band; each shot names its own. | The room mirrored — Jenny's chair landing screen-left of the TV. |
| `layout_match` | Mean hue/saturation-histogram correlation across that shot's named plate regions (6–9 of them). | "This is a different living room." |
| `couch_occupancy` | Share of the couch band that is not bare upholstery, as a ratio of the plate's own. Only 1A, 1B and 1D have a couch band. | Kids vanished, or a crowd added. |
| `wardrobe` | Per-character costume-colour coverage vs the plate, for the characters the manifest puts in this shot. | Leo out of his dinosaur pajamas, Mia out of the magenta top. |

Each returns PASS, FAIL or **n/a**. n/a is not a pass — see below. Which of the
four a given shot actually gets is in the coverage table.

### Three verdicts, and two ways to be INCONCLUSIVE

- **PASS** — enough checks ran and nothing failed.
- **FAIL** — more frames failed than `--tolerate` allows.
- **INCONCLUSIVE** — the clip was not measured well enough to clear. Exits 1. A
  clip nobody measured has not been cleared, and reporting that as PASS is
  exactly the failure the Validation Gates rule exists to prevent.

A clip lands on INCONCLUSIVE for one of two reasons, and the output says which:

1. **The plate is too thin.** Fewer than `min_applied_checks` (scene default: 2)
   could be applied. This rule exists because of `02-shot-1B`: the old gate
   passed it on one number, Leo's green covering 1.67× the plate's amount, while
   the room behind him was the wrong room. One measurement is an anecdote.
2. **The plate cannot clear.** For four shots, another Scene 1 panel walks
   straight through the gate — see the discrimination matrix below. Those plates
   can still **fail** a clip, because a failing measurement is evidence of a real
   break either way. They cannot clear one, because a clip of the wrong shot
   would clear them too.

### Coverage: what each shot's plate can actually prove

`✓` measured, `–` not available in that framing.

| Shot | Framing | staging | layout | couch | wardrobe | Can clear a clip? |
|---|---|:--:|:--:|:--:|:--:|---|
| 1A | wide establishing, static | ✓ | ✓ | ✓ | ✓ Mia, Leo | **yes** |
| 1B | medium on Leo | ✓ | ✓ | ✓ | ✓ Leo | **yes** |
| 1C | medium tracking | ✓ | ✓ | – | – | no — 1B, 1D, 1I panels pass it |
| 1D | two-shot Gabe/Nina | ✓ | ✓ | ✓ | ✓ Mia, Leo, Jenny | **yes** |
| 1E | close-up Jenny | ✓ | ✓ | – | – | no — 1D panel passes it |
| 1F | close-up TV insert | ✓ | ✓ | – | – (no characters) | **yes** |
| 1G | OTS behind the kids | ✓ | ✓ | – | – | no — 1A panel passes it |
| 1H | close-up Mia, slow push | ✓ | ✓ | – | ✓ Mia | **yes** |
| 1I | close-up to two-shot | ✓ | ✓ | – | – | no — 1C panel passes it |

The wardrobe blanks are not laziness, they are the light. Nina's black dress,
Gabe's black tux, Jenny's grey-olive hoodie and — in the dim OTS and hallway
framings — even Mia's magenta and Leo's green each cover 20–44% of their own
plate, because in a dark room those colours are most of the frame. The gate
disqualifies any swatch over 5% of the plate and reports the character as
`no swatch` with its measured coverage, rather than passing it on a meaningless
number. The swatches stay listed in the spec so the reason they are skipped is
visible rather than absent.

### The discrimination matrix — the honest limit of a per-shot plate

Run `python score_corpus.py --cross-shot` (no clips needed, $0.00). It puts
every shot's locked panel through every shot's gate. The diagonal must pass.
Anything off the diagonal that also passes is a plate that cannot tell its own
shot from a sibling:

```
  plate\panel   1A   1B   1C   1D   1E   1F   1G   1H   1I
  1A             P    F    F    F    F    F    F    F    F
  1B             F    P    F    F    F    F    F    F    F
  1C             F    p    p    p    F    F    F    F    p
  1D             F    F    F    P    F    F    F    F    F
  1E             F    F    F    p    p    F    F    F    F
  1F             F    F    F    F    F    P    F    F    F
  1G             p    F    F    F    F    F    p    F    F
  1H             F    F    F    F    F    F    F    P    F
  1I             F    F    p    F    F    F    F    F    p
```

`p` is a pass the `can_clear: false` rule downgrades to INCONCLUSIVE. Six
wrong-shot passes, in four rows: 1C is cleared by the 1B, 1D and 1I panels; 1E by
1D; 1G by the 1A wide; 1I by 1C. All four are shots where every costume colour is
unmeasurable and there is no couch band, so `layout_match` is carrying the whole
verdict alone — and a hue histogram of one dim living room looks much like a hue
histogram of the same dim living room from four feet to the left. 1I scores
**0.764** on the 1C panel against a 0.55 threshold.

The flags in `scene-01-plate.json` are set from this measurement, not from
judgement, and both `--cross-shot` and the test suite fail loudly if the two
drift apart. Re-run it after touching any region, band or swatch.

---

## Scored: every Scene 1 clip on R2

24 clips, 5 frames each. Re-run 2026-08-29 with per-shot plates. Full JSON:
`reports/continuity-video-gate-per-shot-2026-08-29.json` (the single-plate run it
replaces is still there as `reports/continuity-video-gate-2026-08-29.json`).
Reproduce with `score_corpus.py` — rclone lines are in its docstring.

`frames` is one character per sample, in time order: `P` pass, `F` fail.
`layout` is the worst layout_match score across the five samples.

| Clip | Shot | Before | After | Frames | layout | Failing |
|---|:--:|---|---|:--:|--:|---|
| `G1_text_to_video.mp4` | – | FAIL | FAIL | `FFFFF` | 0.176 | layout, wardrobe |
| `G2_image_to_video.mp4` | 1A | **PASS** | **PASS** | `PPPPP` | 0.743 | – |
| `G3_image_to_video.mp4` | 1A | FAIL | FAIL | `PPPPF` | 0.543 | layout (last frame only) |
| `G4_reference_to_video.mp4` | – | FAIL | FAIL | `FFFFF` | 0.163 | layout, wardrobe |
| `PROBE_12refs.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.480 | layout, wardrobe |
| `01-shot-1A.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.369 | layout, wardrobe |
| `02-shot-1B.mp4` | 1B | PASS | **FAIL** ▲ | `FFFFF` | 0.288 | layout |
| `03-shot-1C.mp4` | 1C | INCONCLUSIVE | **FAIL** ▲ | `FFFFF` | 0.171 | layout |
| `04-shot-1D.mp4` | 1D | INCONCLUSIVE | **FAIL** ▲ | `FFFFF` | 0.351 | layout, wardrobe |
| `05-shot-1G.mp4` | 1G | INCONCLUSIVE | **FAIL** ▲ | `FFFFF` | 0.169 | layout |
| `06-shot-1H.mp4` | 1H | INCONCLUSIVE | **FAIL** ▲ | `FFFFF` | 0.156 | layout, wardrobe |
| `07-shot-1I.mp4` | 1I | INCONCLUSIVE | **FAIL** ▲ | `FFFFF` | 0.391 | layout |
| `scene-01-parents-leaving.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.283 | layout, wardrobe |
| `flow-veo-1A.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.396 | layout, wardrobe |
| `flow-veo-1A-frames.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.416 | layout, wardrobe, staging |
| `flow-veo-1C.mp4` | 1C | INCONCLUSIVE | **FAIL** ▲ | `FFFFF` | 0.262 | layout |
| `flow-omni-1D.mp4` | 1D | INCONCLUSIVE | **FAIL** ▲ | `FFFFF` | 0.512 | layout, wardrobe |
| `…veo2-v1.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.438 | layout |
| `…veo2-v2.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.341 | layout, wardrobe |
| `…veo3-v1.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.415 | layout |
| `…veo3-v2-stable.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.437 | layout |
| `…veo3-v3-ultrastable.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.440 | layout |
| `…veo3-v4-anchored.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.368 | layout |
| `…veo31-v1.mp4` | 1A | FAIL | FAIL | `FFFFF` | 0.277 | layout, wardrobe |

| | PASS | FAIL | INCONCLUSIVE |
|---|:--:|:--:|:--:|
| Before (1A plate only) | 2 | 15 | **7** |
| After (per-shot plates) | 1 | 23 | **0** |

**Every 1A clip scores identically to before**, check for check, to three
decimals. That is asserted in the test suite, not just observed: the 1A entry's
regions, bands, swatches, wardrobe map and thresholds are pinned in
`TestPlateSpecShape`, and the plate's own layout (1.000) and staging gap (0.275)
are pinned too.

### The eight clips whose verdict changed — all eight verified by eye

A verdict that only moved because the plate got thinner would be a regression,
so a mid-clip frame was pulled from each of the eight and compared to its panel.
All eight are true positives.

- **`02-shot-1B`: PASS → FAIL.** This is the false negative VIDEO-GATE flagged
  last time, and it is fixed. The clip is a two-shot of both kids in a different
  living room — flat-panel TV instead of the CRT, Leo in a plain **green
  T-shirt** rather than dinosaur pyjamas, Mia in a pink star tee with a straight
  ponytail against the locked curly hair, Jenny in a coral hoodie and not in 1B's
  manifest at all. The old gate cleared it on Leo's green alone; against 1B's own
  plate it now scores 0.288 on layout. **Correct, and the single most valuable
  change here.**
- **`03-shot-1C` and `flow-veo-1C`: INCONCLUSIVE → FAIL.** Locked 1C is the front
  door area: white panelled door, coat rack, Gabe waiting by it. Both clips are
  the living room instead, with a flat-panel TV against the windows and a grey
  sectional. `flow-veo-1C` also carries a Veo watermark and an extra child.
  Layout 0.171 and 0.262. **Correct.**
- **`04-shot-1D`: INCONCLUSIVE → FAIL.** Different room, and the two-shot is
  **swapped** — the locked plate has Gabe screen-left and Nina screen-right, the
  clip reverses them. No kids' couch under the stormy window, no Jenny in her
  armchair. Layout 0.351. **Correct.** (`staging_orientation` correctly reported
  n/a rather than piling a second reason on: below the layout threshold the
  band comparison is noise.)
- **`flow-omni-1D`: INCONCLUSIVE → FAIL.** The closest call in the whole run at
  **0.512 against 0.55**. Looked at directly: it is a different living room with
  a flat-panel TV where the window bank should be, the parents are swapped the
  same way, Gabe's build is much heavier than the locked turnaround, and Jenny is
  absent. **Correct — but a clip in the 0.50–0.60 band still deserves a human.**
- **`05-shot-1G`: INCONCLUSIVE → FAIL.** Right idea, wrong room: two kids OTS
  watching a flat-panel TV on a media console, Gabe screen-left where the locked
  plate has Nina, no lightning, Mia's hair straight instead of curly. Layout
  0.169. **Correct.**
- **`06-shot-1H`: INCONCLUSIVE → FAIL.** Mia has straight brown hair in a
  ponytail and freckles against the locked dark curly hair, the lightning floats
  on a bare wall with no window frame, and her top is pink rather than the locked
  magenta — which is why wardrobe fires here as well as layout (0.156). **Correct,
  and 1H is the one close-up the gate handles well:** its plate is the best
  separated of the nine, with a worst off-diagonal of 0.409.
- **`07-shot-1I`: INCONCLUSIVE → FAIL.** Living room with a flat-panel TV instead
  of the hallway with the coat rack; Nina's hair is curly brown against the locked
  auburn. Layout 0.391. **Correct.**

Note what did **not** happen: no clip moved *toward* a pass. Not one of the eight
was cleared by giving it a plate, and the one clip that used to pass on a single
thin measurement now fails. The gate got stricter in every direction.

### What the other failures actually are

These were looked at during the single-plate run and their verdicts have not
moved. Kept here because they are the evidence behind the thresholds.

**True positives — the clip really is off the locked plate.**

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

**False positive — one, and it is still the only one.**

- `G3_image_to_video` fails on the **last frame only** (`PPPPF`), with a layout
  score of **0.543 against a 0.55 threshold** — it misses by 0.007. Looking at
  that frame: G3's prompt asked for "a slow, gentle push-in", and over 10 seconds
  (twice G2's duration) the push travels far enough that the TV, the armchair,
  Jenny, the kitchen and the floor have all left frame. Mia and Leo are still
  perfectly on-model. **The shot is fine; the gate is measuring "is the wide
  plate still in frame", and it correctly isn't.** This is the gate's central
  blind spot: it cannot tell reframed-by-design from drifted-off-model. Running
  it with `--tolerate 1` passes G3, which for a push-in shot is the right call.

**False negative — fixed.**

- `02-shot-1B` used to **PASS** on a single number: Leo's green covering 1.67×
  the 1A plate's amount, with all three geometry checks n/a because it is a
  medium shot. But that green is a **green T-shirt**, not the manifest's "green
  dinosaur-pattern pajamas", and the room behind him is the wrong room. Two
  changes close it: 1B is now scored on 1B's own plate (layout 0.288, a clear
  fail), and `min_applied_checks: 2` means a lone colour measurement can no
  longer clear anything at all.

---

## Honest note on the false-positive rate

23 of 24 clips now fail, which looks alarming until you look at the corpus: it
is almost entirely pre-v4-lock output plus deliberate probes. There is **one
on-model clip in it** (`G2`), and it passes. Do not read a 96% failure rate as a
gate that fails everything — read it as a corpus that predates the lock.

The one number worth quoting: **one false positive in 23 flags (G3, ~4%)**,
against **zero known false negatives**. The false-negative side is still not a
sample — one clip passes.

For a positive control that does not depend on the corpus, every one of the nine
locked panels goes through its own gate without a failing check; that is asserted
per shot in the test suite.

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

1. **It can fail nine shots but only clear five.** Per-shot plates removed the
   INCONCLUSIVE-by-default problem — every Scene 1 shot is now measurable, and no
   clip in the corpus comes back unmeasured. But 1C, 1E, 1G and 1I have plates
   that another Scene 1 panel walks straight through, so they are wired to
   convict and not to acquit. Making them clear a clip needs something a hue
   histogram cannot give: those four framings differ from their neighbours in
   composition and identity, not in colour distribution. **This is the honest
   ceiling of a free OpenCV gate on this scene** — the next real step for those
   four is the paid vision validator, not more regions.
2. **It cannot distinguish a deliberate camera move from drift.** G3 is the
   proof. A shot with a real push-in or track will leave the plate's framing on
   purpose. `--tolerate 1` is the blunt workaround; per-shot camera-aware
   tolerance is the real fix.
3. **It does not check identity.** It cannot tell Mia from another dark-haired
   girl in a magenta top. That is the paid vision validator's job
   (`scripts/validate/shot_validator.py`, ~$0.02/shot). This gate is the free
   pre-filter that runs first and stops obvious breaks before anyone pays.
4. **Dark costumes are unmeasurable, and dark *shots* more so.** On the 1A wide,
   Nina's black dress, Gabe's black tux and Jenny's grey-blue hoodie each cover
   23–26% of the plate, because in a dim room those colours are most of the
   frame; only Mia's magenta (0.16%) and Leo's green (0.85%) are real signals.
   Per-shot plates did **not** fix this — they made it visible. In 1G's OTS
   framing every costume, Mia's magenta included, covers 25–44% of the plate; in
   1E Jenny's hoodie covers 33%. Five of the nine shots therefore have no
   wardrobe check at all. The gate disqualifies any swatch over 5% of the plate
   and names the character with its measured coverage rather than passing it on a
   meaningless number.
5. **`staging_orientation` needs `layout_match` to pass first.** Measured on the
   veo3-v4 clips: a correctly staged but entirely different room scored
   straight=0.582 / crossed=0.597 and was called mirrored. Below the layout
   threshold the left/right comparison is noise, so it now reports n/a instead
   of stacking a bogus second reason onto one real break.
6. **`couch_occupancy` is coarse.** It passed `flow-veo-1A`, which has three
   kids on the couch instead of two. It catches an empty couch, not a miscount.

### Where the thresholds came from

`scene-01-plate.json`, tuned against the plates themselves plus the clips above.
These are **scene-wide** — a shot entry may override any of them under its own
`thresholds` key, and none currently does. Nothing was loosened for per-shot
plates; the only two additions tighten the gate.

| Threshold | Value | Why |
|---|---|---|
| `layout_match` | 0.55 | Plate 1.00, G2 0.74–0.93, wrong-room clips 0.16–0.56. The populations overlap; 0.55 sits inside the overlap. |
| `staging_margin` | 0.02 | Straight must beat crossed by this. The 1A plate's own gap is 0.275; the nine plates range 0.134 (1E) to 0.991 (1H). |
| `wardrobe_min_ratio` | 0.35 | G2/G3 score 1.2–1.7; the wrong-costume clips 0.19–0.33. |
| `swatch_max_plate_coverage` | 0.05 | Above this a "costume colour" is measuring the room. Disqualifies 5 of the 9 shots' entire wardrobe. |
| `swatch_min_plate_coverage` | 0.001 | **New.** The floor at the other end: below this the ratio is noise. Nothing currently registered trips it — Mia's magenta on 1A is the closest at 0.0016. |
| `min_applied_checks` | 2 | **New.** Fewer measurements than this is INCONCLUSIVE, not PASS. This is the `02-shot-1B` rule. |
| `couch_occupancy` | 0.45–2.20 | Deliberately wide. This check is a backstop, not a discriminator. |

The layout threshold was deliberately **not** re-tuned per shot. A moving-camera
shot (1C tracks, 1H pushes, 1I pulls) will drift off its plate by design, and
lowering its threshold to compensate would buy passes with no evidence — there is
no on-model clip for any of those shots to calibrate against. They keep 0.55 and
they fail honestly when the framing leaves.

Re-tune by editing that file — no code change needed — then re-run
`score_corpus.py` for the corpus, `score_corpus.py --cross-shot` for the
discrimination matrix, and the test suite, which pins the 1A numbers and checks
the `can_clear` flags against what is actually measured.

---

## A note on provenance

The per-shot plates in this directory are 512px jpg copies of the nine locked v4
panels. No art was generated for the gate — task #339 was registration and
plumbing. The `ffmpeg` recipe under **Files** reproduces them exactly.


The task that commissioned this described `check.py` as already existing and
hardcoding `/workspace/...` paths. **It is not in this repo and not in any
branch or commit in its history** — it appears to have been written in a sandbox
that was never committed. So `check.py` here was written fresh to the behaviour
the task described (chair screen-right of the TV, wardrobe, couch occupancy),
with the path handling done properly from the start: CLI flag → environment →
pinned repo default, no absolute paths and no `sys.path` venv insertion. There
was no existing still-image behaviour to preserve, so nothing was broken; but
that also means the still gate is new code that has not been reviewed before.
