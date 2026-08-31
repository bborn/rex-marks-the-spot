# Scene 1, shot 1A at 720p: four takes, all four gated

Task #340. The first production-resolution footage in the Omni evaluation —
everything before this was 360p probes.

**Answer up front: yes, 720p Omni image_to_video from the validated v4 panel
holds the locked plate, and no, duration does not change that.** All four takes
PASS the continuity gate on every sampled frame, at 5 samples and again at 12.
The 10s push-in — the exact configuration that failed at 360p as `G3` — passes
at 720p with its worst frame at layout 0.790, a comfortable 0.24 above the
threshold.

The reason is not that the gate got kinder. It is that **at 720p the model moves
the camera about a fifth as far for the same prompt**, and it paces the move to
the clip length instead of continuing at a fixed rate. Measured below.

- **Spend: $3.1130** against a $4.00 cap. Four generations, no retries.
- Clips, frame grabs and every gate report:
  `r2:rex-assets/animation-tests/scene01-1A-720p/`
  ([public](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-1A-720p/T1.mp4))

---

## What was rendered

Source panel: `r2:rex-assets/storyboards/v4/scene-01/scene-01-1A-start.png` —
the validated v4 panel from the 9/9 PASS set, 1376x768. Confirmed on R2 with
`rclone lsf` before use; the pre-validation `storyboards/act1/` copies were not
touched.

A 2x2: camera motion crossed with duration.

| Take | Duration | Camera | Prompt |
|---|---|---|---|
| T1 | 5s | slow gentle push-in (the G2/G3 clause, verbatim) | A + PUSH-IN |
| T2 | 5s | held frame, slight handheld drift | A + HELD |
| T3 | 10s | slow gentle push-in | A + PUSH-IN |
| T4 | 10s | held frame, slight handheld drift | A + HELD |

Everything else is identical across the four: same panel as `<FIRST_FRAME>`,
same staging block, `image_to_video`, 720p, 16:9. Runner:
`scripts/video/run_scene01_1A_720p.py`, one take per invocation, cost checked
against the cap before each call.

```python
response_format={"type":"video","aspect_ratio":"16:9",
                 "resolution":"720p","duration":"5s"}   # "10s" for T3/T4
generation_config={"video_config":{"task":"image_to_video"}}
```

### Prompts, verbatim

All four prompts are `STAGING + <camera clause> + AUDIO`. Child-explicit by
design: Phases 0.5–0.7 measured that naming children is clear for everything
except children alone in a police vehicle, and this is a living room. Nothing
was filtered, blocked or softened on any of the four calls.

**STAGING** (identical in T1–T4; wardrobe from
`docs/process/continuity/bible/scene-01.json`, the negatives are the
do-not-invent list):

> Hold this exact composition, framing and art style. Mia, an 8-year-old girl
> with dark curly hair in a magenta polka-dot t-shirt and blue jeans, and her
> little brother Leo, a 5-year-old boy in green dinosaur-pattern pajamas holding
> a green plush dinosaur, are the two kids; both stay seated together on the
> couch in the middle of the frame. Their teenage babysitter Jenny, dark brown
> hair in a ponytail, stays in the armchair at screen right looking down at her
> phone. Their parents Nina, in an elegant black formal dress, and Gabe, in a
> black tuxedo, stay standing in the kitchen area behind the couch. The old TV
> at screen left keeps playing a colourful cartoon. Rain and a stormy sky
> continue outside the windows. The toy dinosaurs stay on the floor. The kids do
> not get off the couch and do not sit on the floor. Mia does not wear glasses.
> Leo stays in his dinosaur pajamas. No new characters enter. Nothing new
> appears on the windowsill; it stays empty.

**PUSH-IN** (T1, T3) — the G2/G3 motion clause unchanged:

> Camera only: a slow, gentle push-in.

**HELD** (T2, T4):

> Camera: hold this framing. No push-in, no zoom, no pan, no reframe - only a
> very slight handheld drift, as if the camera is breathing.

**AUDIO** (all four):

> No dialogue. No music. No sound effects. Silent.

---

## Gate results

`python check_video.py <clip>.mp4 --shot 1A`, run on the audio-stripped clips.
`frames` is one character per sample in time order: `P` pass, `F` fail. The
`--frames 12` column is a free extra pass at roughly 2.4x the sampling density,
because the G3 failure landed on a last frame and 5 samples over 10s is thin.

| Take | Dur | Camera | Frames (5) | Frames (12) | Verdict | layout min–max | Failing checks |
|---|---:|---|:--|:--|---|---|---|
| **T1** | 5s | push-in | `PPPPP` | `PPPPPPPPPPPP` | **PASS** | 0.859 – 0.958 | – |
| **T2** | 5s | held | `PPPPP` | `PPPPPPPPPPPP` | **PASS** | 0.741 – 0.962 | – |
| **T3** | 10s | push-in | `PPPPP` | `PPPPPPPPPPPP` | **PASS** | 0.794 – 0.941 | – |
| **T4** | 10s | held | `PPPPP` | `PPPPPPPPPPPP` | **PASS** | 0.747 – 0.941 | – |
| *G2 (360p/5s, ref)* | 5s | push-in | `PPPPP` | – | *PASS* | 0.743 – 0.928 | – |
| *G3 (360p/10s, ref)* | 10s | push-in | `PPPPF` | – | *FAIL* | 0.543 – 0.885 | layout (last frame) |

The two reference rows are Phase 0's clips re-scored here with the same gate and
the same command, and they reproduce task #336's numbers exactly (G3 0.543 on
its last frame) — so the four PASSes above are not an artifact of a changed
harness.

`staging_orientation`, `couch_occupancy` and `wardrobe` passed on every sampled
frame of every take; no check was ever skipped except the three characters with
no usable swatch (Jenny, Nina, Gabe — dark costumes, see VIDEO-GATE §4).

### layout_match, frame by frame (5-sample run)

| Take | f1 | f2 | f3 | f4 | f5 |
|---|---|---|---|---|---|
| T1 (5s push) | 0.938 | 0.893 | 0.890 | 0.885 | 0.877 |
| T2 (5s held) | 0.932 | 0.828 | 0.761 | 0.746 | 0.744 |
| T3 (10s push) | 0.914 | 0.831 | 0.809 | 0.794 | 0.790 |
| T4 (10s held) | 0.762 | 0.892 | 0.856 | 0.863 | 0.865 |
| *G3 (10s push, 360p)* | 0.885 | 0.727 | 0.651 | 0.562 | **0.543** |

G3 decays 0.34 across its five samples and lands under the threshold. T3, the
same shot at 720p, decays 0.12 and flattens out.

### Other check scores (5-sample run)

| Take | staging margin | couch occupancy ratio | wardrobe ratio |
|---|---|---|---|
| T1 | 0.117 – 0.177 | 0.88 – 1.00 | 0.87 – 1.00 |
| T2 | 0.116 – 0.217 | 0.89 – 1.05 | 0.90 – 1.33 |
| T3 | 0.072 – 0.174 | 0.91 – 0.98 | 0.91 – 1.27 |
| T4 | 0.104 – 0.169 | 0.88 – 1.03 | 0.90 – 0.95 |

Thresholds: staging margin > 0.02, couch occupancy 0.45–2.20, wardrobe > 0.35.
Nothing is close to a boundary.

---

## The 0.50–0.60 band: what is actually in those frames

VIDEO-GATE says a clip scoring 0.50–0.60 on layout needs a human read. **No take
landed there** — the lowest clip-level layout score across all four is T2's
0.741, well clear. But three individual *regions* dipped into that band, so
those frames were pulled and looked at:

**T4 @ 1.00s — `chair=0.52`, `window=0.53`, layout 0.762
([frame](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-1A-720p/frames/T4-t100.jpg))**
A lightning flash. The window is blown to white and the flash throws cold light
across the right-hand third, including Jenny's armchair. Staging is the plate
exactly: TV screen-left, both kids on the couch in the correct wardrobe, Jenny
in the chair on her phone, Nina and Gabe in the kitchen. The storm is in the
manifest's own key props (`windows showing dark stormy sky`). **Not a
continuity break — this is the plate's weather, and the two low regions are the
gate measuring illumination rather than layout.** It is also the exact case
`--tolerate 1` exists for; it wasn't needed, the frame passed anyway.

**T2 @ 2.50–4.50s — `couch=0.53–0.55`, layout 0.744–0.761
([frame](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-1A-720p/frames/T2-t271.jpg))**
Sub-frame drift, nothing more. The handheld clause creeps the camera in about
2.3% over the 5 seconds, which slides the plate's fixed couch band (normalised
0.19–0.65 x, 0.50–0.82 y) down and left of where the couch actually sits. Both
kids are on the couch, seated, in the right clothes; Mia's red sneakers, Leo's
plush dinosaur and the pterodactyl on the cushion are all where the panel put
them. The couch *occupancy* check, which is a ratio rather than a histogram,
reads 0.99–1.05 on those same frames. **The region score is measuring the band
edge, not the content.**

**T3 @ 9.00s — `chair=0.59`, layout 0.790
([frame](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-1A-720p/frames/T3-tlast.jpg))**
This is the frame that matters — the direct 720p answer to G3. After a full 10
seconds of push-in the TV, the lamp, the couch, both kids, Nina, Gabe, Jenny's
armchair, the kitchen and the toys on the floor are **all still in frame**. The
chair region has softened because the push has cropped the armchair's outer edge
and Jenny now sits nearer the frame border, not because anything left. Compare
[G3](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/omni-1.1-flash-phase0/G3_image_to_video.mp4)
at 360p, which by 10s has pushed into a tight two-shot of Mia and Leo with the TV,
the chair, the kitchen and the floor all gone.

---

## Why duration stopped mattering: measured camera travel

Affine ECC registration of each sampled frame against the clip's own first
frame, downsampled to 640x360. `scale` is how much the frame has zoomed in
relative to frame 0; the shift is the residual translation in 640x360 pixels.
Raw numbers: `gate/camera-travel.json` on R2.

| Take | 0% | 25% | 50% | 75% | end | end shift | zoom rate |
|---|---|---|---|---|---|---|---|
| T1 (720p, 5s, push) | 1.000 | 1.011 | 1.029 | 1.047 | **1.065** | (−20, −9) | 1.3%/s |
| T3 (720p, 10s, push) | 1.000 | 1.031 | 1.058 | 1.069 | **1.083** | (−28, −14) | 0.8%/s |
| T2 (720p, 5s, held) | 1.000 | 1.004 | 1.011 | 1.017 | **1.023** | (−7, −3) | 0.5%/s |
| T4 (720p, 10s, held) | 1.000 | 1.000 | 0.999 | 0.999 | **0.999** | (0, 0) | 0.0%/s |
| *G2 (360p, 5s, push)* | 1.000 | 1.052 | 1.147 | 1.282 | **1.385** | – | 7.7%/s |

Three things fall out of that table:

1. **The same push-in prompt travels ~6x less at 720p than at 360p.** G2 zoomed
   to 1.385x in five seconds; T1 reaches 1.065x. That, not any change to the
   gate, is why the 720p clips stay on the plate.
2. **The 10s push is paced, not extended.** T3 covers 1.083x over ten seconds —
   only slightly more total travel than T1's five, at roughly two-thirds the
   rate. The model reads "slow, gentle" against the clip length. G3 at 360p did
   the opposite: it kept going until the wide plate was gone.
3. **"Held" really is held at 10s, and only nearly held at 5s.** T4 is locked
   off to within a pixel for the whole ten seconds. T2, same prompt at 5s,
   creeps 2.3% — which is where its layout decay comes from. Odd, and on one
   sample per cell it may be nothing but variance.

One clip per cell. These are single samples, not rates: the 720p/360p gap is
large enough to act on, the T2/T4 difference is not.

---

## Cost

Billed from each response's own token usage (`cost_from_usage`), not estimated.

| Take | Duration | Video output tokens | tok/s | Input tokens | Gen time | **Billed** |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 5s | 28,960 | 5,792 | 1,341 | 31.1s | **$0.5238** |
| T2 | 5s | 28,960 | 5,792 | 1,365 | 33.6s | **$0.5258** |
| T3 | 10s | 57,920 | 5,792 | 1,341 | 35.8s | **$1.0307** |
| T4 | 10s | 57,920 | 5,792 | 1,365 | 39.1s | **$1.0327** |
| | **30s** | **173,760** | | | | **$3.1130** |

**$3.1130 of a $4.00 cap. 4 generations of a 5-generation allowance, no
retries.**

720p bills at **exactly 5,792 video tokens per second** — Google's published
figure, and exactly 3.00x the 1,931 tok/s measured at 360p, so the task's "~3x
the 360p rate" is right on the nose. At $17.50 per 1M output tokens that is
**$0.1014 per second of 720p**, plus about $0.002 per call of input. The
per-second cost is flat in duration: a 10s clip costs exactly twice a 5s one,
with no discount and no setup premium.

`omni_flash.py`'s pre-flight `estimate_cost()` predicted $0.5068 / $1.0136 and
came in 3.4% low against the billed figure, the difference being input tokens it
does not model. Fine for cap arithmetic.

---

## Audio

Phase 0 established there is no audio parameter and that populated shots come
back loud despite a "Silent." instruction. Every clip was stripped on ingest
with `ffmpeg -i in.mp4 -c:v copy -an out.mp4`; both versions are on R2 (`raw/`
holds the untouched downloads).

Measured on the raw files, and it split by camera clause rather than by content:

| Take | Camera | mean | peak |
|---|---|---|---|
| T1 | push-in | −91.0 dB | −84.3 dB |
| T3 | push-in | −91.0 dB | −84.3 dB |
| T2 | held | −31.0 dB | −9.1 dB |
| T4 | held | −31.9 dB | −8.7 dB |

All four are the same five characters in the same room, so "populated shots come
back loud" does not explain this. The two push-in takes are digitally silent —
below any room-tone floor. **Strip unconditionally; the "Silent." instruction is
not a control, and whatever does drive it, it is not the cast.** Not worth a
paid experiment to chase.

---

## Recommendation on shot duration

**Render 1A-style wide establishers at 720p, and take the 10s clip.**

- 10s passes the gate as cleanly as 5s (worst frame 0.790 vs 0.877) and costs
  exactly double for exactly double the footage — there is no per-second penalty
  and no quality penalty to buy length.
- A 10s take at 720p gives an editor real trim room on a shot the bible marks as
  an 8s static wide. Two 5s clips would need a cut or a stitch to cover the same
  beat, and the stitch is a second continuity risk the gate would have to clear.
- The camera-travel numbers say the model paces a "slow, gentle push-in" to the
  clip length rather than running it at a fixed rate, so asking for 10s does not
  buy 2x the drift. This is the opposite of the 360p behaviour and it is the
  finding that changes the production default.

On camera clause, for this shot: **the bible calls 1A "STATIC" and T4 delivers
exactly that** — locked to within a pixel for ten seconds, with the storm and
the characters carrying the life. That is the take to build from. T3's push is
usable and passes, but it is motion the shot list did not ask for.

Two limits worth stating with that recommendation:

1. **The gate cannot see identity.** Four PASSes mean the room is the locked
   room, the staging is the locked staging, and the costume colours are right.
   They do not mean Mia is Mia. Before any of this is cut into the film it needs
   `scripts/validate/shot_validator.py` (~$0.02/shot) on top.
2. **This is one clip per cell.** The 720p-vs-360p travel gap is a 6x effect on
   a consistent prompt and is safe to act on. Anything smaller in these tables —
   T2 creeping where T4 does not, T1 scoring above T3 — is one sample and should
   not be built on.

The obvious follow-up, unchanged from #336: 1A is still the only shot with a
plate. Everything here says nothing about 1B–1I, which the gate cannot measure.

---

## Reproducing

```bash
./scripts/setup_python_env.sh
rclone copy r2:rex-assets/storyboards/v4/scene-01/scene-01-1A-start.png work/in/

.venv/bin/python scripts/video/run_scene01_1A_720p.py T1 work/   # one take per call
ffmpeg -i work/out/T1_raw.mp4 -c:v copy -an work/out/T1.mp4

cd docs/process/continuity
../../../.venv/bin/python check_video.py ../../../work/out/T1.mp4 --shot 1A -v
```

## Files

| Where | What |
|---|---|
| `r2:.../scene01-1A-720p/T{1..4}.mp4` | the four takes, audio stripped |
| `r2:.../scene01-1A-720p/raw/T{1..4}_raw.mp4` | untouched downloads, audio intact |
| `r2:.../scene01-1A-720p/frames/` | 13 frame grabs, including every frame read above |
| `r2:.../scene01-1A-720p/gate/T*-gate*.json` | gate reports, 5-sample and 12-sample |
| `r2:.../scene01-1A-720p/gate/T*.json` | generation sidecars: prompt, usage, billed cost |
| `r2:.../scene01-1A-720p/gate/camera-travel.json` | the ECC registration measurements |
| `scripts/video/run_scene01_1A_720p.py` | the runner |
