# Scene 1 at 720p: does a last frame hold the composition?

Task #341. Follows #340 (shot 1A at 720p) and depends on #339's per-shot plates.

**Answer up front: yes, and by a lot — but only if the last frame you supply is
the locked plate.** Shot 1H is the demonstration. Same prompt, same push-in
clause, one variable:

| 1H, 5s, 720p, `image_to_video` | worst layout | verdict |
|---|---:|---|
| Take A — `<FIRST_FRAME>` only | **0.231** | **FAIL** (6 of 12 frames) |
| Take B — `<FIRST_FRAME>` + `<LAST_FRAME>` = the same locked plate | **0.741** | **PASS** (12 of 12) |
| Take C — `<LAST_FRAME>` = `panel-08-end`, an off-model pre-lock panel | **0.354** | **FAIL** (5 of 12) |

The last frame is not a hint. It is a hard target the model drives to, and it
drives there whether or not the target is on-model. Take C ends as literally a
different girl — straight hair in a ponytail, pink top, no window — because that
is the frame it was handed.

- **Spend: $3.6689** against a $4.00 cap. Seven generations of a nine
  allowance, no retries.
- Clips, frame grabs, gate reports and the raw measurements:
  `r2:rex-assets/animation-tests/scene01-720p/`
  ([1HA](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-720p/1HA.mp4) ·
  [1HB](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-720p/1HB.mp4) ·
  [1HC](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-720p/1HC.mp4) ·
  [A/B/C sheet](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-720p/sheets/1H-abc.png))

---

## 1. The panel-to-shot mapping, and the thing it turned up

The task asked for the mapping to be derived rather than assumed. It is
sequential — panel number `NN` is the `NN`th shot of the scene:

| panel | shot | | panel | shot | | panel | shot |
|---|---|---|---|---|---|---|---|
| `panel-01` | 1A | | `panel-04` | **1D** | | `panel-07` | 1G |
| `panel-02` | **1B** | | `panel-05` | 1E | | `panel-08` | **1H** |
| `panel-03` | 1C | | `panel-06` | **1F** | | `panel-09` | 1I |

Three independent sources agree:

1. `scripts/generate_scene01_all_panels.py` labels its own panels in its
   `PANELS` dict — `"02": {"desc": "1B: Medium shot Leo on couch..."}` through
   `"09": {"desc": "1I: Close-up Gabe hesitates"}`, with panel 01 handled
   separately as the 1A wide by `scripts/generate_scene01_panel01_video.py`.
2. `storyboards/act1/scene-01-home-evening.md` heads its nine sections
   "Panel 1A" … "Panel 1I" in that order.
3. Content. `panel-04` is the Gabe/Nina two-shot with Gabe checking his watch;
   `panel-06` is the TV insert; `panel-08` is the close-up on Mia. They match
   their manifest entries' `camera` and `characters` fields.

### The mapping is right and the panels are still not usable

`scene-01-1?-start.png` and `scene-01-panel-0?-start/end.png` share the
`storyboards/v4/scene-01/` prefix on R2, which makes it look like one set. They
are not. Check the metadata:

| | uploaded | size | source |
|---|---|---|---|
| `scene-01-1?-start.png` | **2026-05-22** | 520–715 KB | `regen_scene01_v4.py`, `gemini-3-pro-image-preview`, image-to-image off the locked turnarounds |
| `scene-01-panel-0?-*.png` | **2026-03-17** | 1.9–2.6 MB | the pre-lock March generation |

Not one byte is shared — every one of the 27 files has a distinct md5. **The
`panel-NN` pairs are the pre-v4-lock set**, which is why VIDEO-GATE's corpus
table fails every clip derived from them. Put each one through `check.py`
against the plate for the shot it maps to:

| end panel | shot | verdict | layout | staging | wardrobe |
|---|:--:|---|---:|---|---:|
| `panel-02-end` | 1B | **FAIL** | 0.472 | n/a | 0.280 |
| `panel-04-end` | 1D | **FAIL** | 0.581 | **mirrored** (−0.073) | 0.395 |
| `panel-06-end` | 1F | **INCONCLUSIVE** | 0.011 | n/a | – |
| `panel-08-end` | 1H | **FAIL** | 0.356 | n/a | 0.056 |

Zero of the four clear. Their *start* panels fail too (0.476 / 0.582 / 0.316 /
0.266), so this is not an end-frame artifact — the whole set is a different
living room. Side by side with the locked plates:

- **1B** — the locked plate has a grey couch against a window bank with a
  bookshelf at screen left. `panel-02` has a tan couch, framed pictures, a blank
  white rectangle where the window should be, and a large brown T-Rex plush that
  is not in the manifest.
- **1D** — **the two-shot is reversed.** Locked: Gabe screen-left, Nina
  screen-right. `panel-04`: Nina left, Gabe right. Plus a flat-panel TV where
  the locked room has none. This is the exact break VIDEO-GATE recorded for
  `04-shot-1D`.
- **1F** — the locked plate is a wood-cabinet CRT with dials, filling frame.
  `panel-06` is a modern flat panel on a white plinth. Its `-end` is that panel
  blown out by a flash, which is why it scores 0.011 against everything.
- **1H** — locked Mia has voluminous dark curly hair worn down and a magenta
  star-print tee. `panel-08` Mia has straight hair in a ponytail with a scrunchie
  and a pale pink star top, against a bare wall with no window. Again, exactly
  the `06-shot-1H` break in VIDEO-GATE.

The positive control rules out "the gate just dislikes storyboard art". Run the
same matrix over the locked v4 panels and it is diagonal and emphatic
(`scripts/video/map_panels_to_shots.py`, $0.00):

| image | 1A | 1B | 1C | 1D | 1E | 1F | 1G | 1H | 1I | best |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|
| `1B-start` | 0.464 | **0.991** | 0.565 | 0.451 | 0.417 | 0.258 | 0.373 | 0.398 | 0.440 | 1B PASS |
| `1D-start` | 0.339 | 0.426 | 0.568 | **0.993** | 0.684 | 0.517 | 0.440 | 0.161 | 0.623 | 1D PASS |
| `1F-start` | 0.331 | 0.242 | 0.285 | 0.397 | 0.334 | **0.985** | 0.290 | 0.132 | 0.246 | 1F PASS |
| `1H-start` | 0.248 | 0.463 | 0.238 | 0.200 | 0.183 | 0.098 | 0.120 | **0.974** | 0.334 | 1H PASS |
| `panel-02-end` | 0.478 | *0.472* | 0.586 | 0.632 | 0.548 | 0.415 | 0.421 | 0.243 | 0.528 | 1D FAIL |
| `panel-04-end` | 0.479 | 0.574 | 0.603 | *0.581* | 0.595 | 0.465 | 0.370 | 0.269 | 0.655 | 1I INCONCLUSIVE |
| `panel-06-end` | 0.001 | 0.002 | 0.004 | 0.000 | 0.000 | *0.011* | 0.037 | 0.000 | 0.003 | 1G INCONCLUSIVE |
| `panel-08-end` | 0.287 | 0.379 | 0.464 | 0.362 | 0.458 | 0.254 | 0.154 | *0.356* | 0.377 | 1C INCONCLUSIVE |

Every locked panel scores 0.97–0.99 on its own plate. **Not one of the four end
panels scores highest against the shot it maps to** — each is closer to some
other shot's plate than to its own, which is what a different room looks like to
a hue histogram. Full cross-scores for all 27 panels:
`gate/panel-to-shot-scores.json` on R2.

**So the literal Take B the task specified could not be run as production work.**
CLAUDE.md's Validation Gates rule is explicit: "before generating from ANY
artifact, confirm that artifact passed its validation gate… A storyboard panel is
not trusted because it exists." Using these as a production `<LAST_FRAME>` would
have anchored four clips to a different room, and — worse for the actual research
question — would have made the A/B unanswerable, because the last frame would be
off-composition by construction and "does anchoring help fidelity" could only
ever come back "it hurts."

Two substitutions were made instead, both stated here rather than quietly:

- **Take B anchors on the shot's own locked v4 panel** as `<LAST_FRAME>`. Both
  ends are then validated artifacts and any score change is attributable to the
  binding.
- **Take C, once, on 1H only, uses `panel-08-end` as a labelled probe.** It is
  not production footage. It exists because binding two *identical* images cannot
  by itself distinguish "the anchor held the composition" from "the model ignored
  a redundant tag" — one clip with a genuinely different last frame is what makes
  the Take B result readable. It is worth its $0.52 twice over; see §4.

No other shot's panel was substituted for any shot.

---

## 2. What was rendered

Shots **1B, 1D, 1F, 1H** only. 1A was done in #340. 1C/1E/1G/1I are
`can_clear: no` in `scene-01-plate.json` — their plates can convict a clip but
cannot acquit one, so footage for them could not be cleared.

All takes: 720p, 16:9, 5s, `image_to_video`, `gemini-omni-1.1-flash`.

```python
response_format={"type":"video","aspect_ratio":"16:9",
                 "resolution":"720p","duration":"5s"}
generation_config={"video_config":{"task":"image_to_video"}}
```

| Take | `<FIRST_FRAME>` | `<LAST_FRAME>` |
|---|---|---|
| `1BA` `1DA` `1FA` `1HA` | that shot's locked `scene-01-1?-start.png` | – |
| `1BB` `1HB` | same locked panel | **the same locked panel** |
| `1HC` | locked `1H-start` | `panel-08-end` (probe) |

The prompt text is **byte-identical between a shot's A, B and C takes**. The only
difference is the media binding. Runner:
`scripts/video/run_scene01_first_last.py`, one take per invocation, cap checked
against the billed running total before every call.

Take B was run on 1B and 1H rather than all four because four B takes plus the
four A takes would have been $4.19, over the cap. 1H was chosen because its Take
A failed — the case where an anchor should matter most — and 1B as the control on
a shot whose Take A passed.

### Prompts, verbatim

Every prompt is `STAGING + <camera clause> + AUDIO`. Child-explicit by design:
Phases 0.5–0.7 measured that naming children reads clear for everything except
children alone in a police vehicle, and this is a living room. **Nothing was
filtered, blocked or softened on any of the seven calls.**

Wardrobe is from `asset-bible/manifests/scene-01.json`. The negatives are the
do-not-invent clauses, stated in the prompt because that is the only place the
model reads them. (`docs/process/do-not-invent.md` and
`docs/process/scene-01-manifest.json`, both named in the task, do not exist in
this repo or any of its branches; the manifest is at
`asset-bible/manifests/scene-01.json` with a pinned copy at
`docs/process/continuity/bible/scene-01.json`, and #340 derived its negatives
inline the same way. See §8.)

**Camera clauses** — `PUSH_IN` and `HELD` are copied verbatim from
`run_scene01_1A_720p.py` so these numbers are comparable with #340's. Each shot
gets the clause its own manifest entry asks for:

> **PUSH_IN** (1B "STATIC with slight PUSH", 1H "SLOW PUSH"):
> Camera only: a slow, gentle push-in.
>
> **HELD** (1D, 1F):
> Camera: hold this framing. No push-in, no zoom, no pan, no reframe - only a
> very slight handheld drift, as if the camera is breathing.
>
> **AUDIO** (all seven):
> No dialogue. No music. No sound effects. Silent.

1D's manifest camera is "STATIC with occasional REFRAMES" and was given `HELD`
anyway: a reframe is precisely what the gate cannot tell apart from drift
(VIDEO-GATE limit 2), and #340 measured that the held clause is the one that
keeps the plate.

**STAGING, 1B:**

> Hold this exact composition, framing and art style. Leo, a 5-year-old boy with
> tousled blond hair and blue eyes, in green dinosaur-pattern pajamas, stays
> sitting cross-legged in the middle of the grey couch, hugging his small green
> plush dinosaur. He keeps watching the television off-screen; the TV glow stays
> on his face. His big sister Mia, an 8-year-old girl with dark curly hair in a
> magenta star-print t-shirt and blue jeans, stays partly out of frame at the
> extreme left edge. The plastic toy dinosaurs stay exactly where they are on the
> couch: the brown T-Rex on the cushion to his left, the reddish Triceratops and
> the pterodactyl on the cushion to his right. The bookshelf, the lit floor lamp
> and the armchair stay in the background at screen left. Rain and a stormy sky
> with lightning continue outside the windows behind the couch. Leo does not get
> off the couch and does not stand up. Leo stays in his dinosaur pajamas and does
> not change clothes. Mia does not walk into the frame. No new characters enter.
> The television is never visible in frame. Nothing new appears on the couch or
> the windowsill.

**STAGING, 1D:**

> Hold this exact composition, framing and art style. Gabe, the dad, dark brown
> hair, black-framed glasses and light stubble, in a black tuxedo with a white
> shirt and black bow tie, stays standing left of centre looking down at the
> wristwatch on his wrist. His wife Nina, auburn wavy shoulder-length hair, in an
> elegant sleeveless black formal dress, stays standing at his right, turned
> towards him. Neither of them moves out of the frame or swaps sides. In the
> background at screen left their two kids stay seated together on the grey
> couch: Mia, an 8-year-old girl with dark curly hair in a magenta star-print
> t-shirt and blue jeans holding an open book, and her little brother Leo, a
> 5-year-old boy in green dinosaur-pattern pajamas holding a green plush dinosaur.
> In the background at screen right their teenage babysitter Jenny, dark brown
> hair in a high ponytail and a grey long-sleeved top, stays sitting in the
> armchair looking down at her phone. Rain and a stormy sky with lightning
> continue outside the windows at the far left; the lamps stay lit. Gabe and Nina
> do not change places. The kids do not get off the couch and do not sit on the
> floor. Mia does not wear glasses. Leo stays in his dinosaur pajamas. Jenny does
> not put her phone down. No new characters enter. Nothing new appears on the
> furniture.

**STAGING, 1F:**

> Hold this exact composition, framing and art style. The old boxy wood-cabinet
> television keeps filling most of the frame, its rounded glass screen at
> centre-left and its two round dials and speaker grille on the wood panel at its
> right. On the screen a colourful cartoon keeps playing, smeared and broken up
> by rolling horizontal scan lines and static, with the blue electrical flash
> flickering across the middle of the picture. Behind the set at screen right,
> rain and lightning continue outside the window, the table lamp stays lit, and
> the knitted throw stays over the arm of the chair in the bottom right corner.
> The television stays an old boxy cabinet set and never becomes a flat panel
> screen. No people enter the frame; there are no characters in this shot.
> Nothing new appears in the room.

**STAGING, 1H:**

> Hold this exact composition, framing and art style. Mia, an 8-year-old girl
> with voluminous dark brown curly hair worn down, big brown eyes and freckles,
> in a magenta star-print t-shirt and blue jeans, stays seated in the centre of
> the frame looking up and to her left at her parents off-screen. Her expression
> stays worried and hopeful. Her hair stays curly and worn down. The warm table
> lamp stays lit at screen left with the framed picture on the wall behind it,
> and rain and a bright lightning flash continue outside the window at screen
> right. The soft out-of-focus foreground shapes at the extreme left and right
> edges of the frame stay exactly where they are and stay out of focus. Mia stays
> in the magenta t-shirt and does not change clothes. Mia's hair does not become
> straight and is not tied back. Mia does not wear glasses. Mia does not stand up
> or leave the frame. No new characters enter and nothing in the foreground comes
> into focus.

---

## 3. Gate results

`python check_video.py <clip>.mp4 --shot <ID>`, on the audio-stripped clips.
`frames` is one character per sample in time order: `P` pass, `F` fail. The
12-sample column is a free extra pass at 2.4x the density.

| Take | Shot | Camera | Last frame | Frames (5) | Frames (12) | Verdict | layout min–max (12) | Failing |
|---|:--:|---|---|:--|:--|---|---|---|
| **1BA** | 1B | push | – | `PPPPP` | `PPPPPPPPPPPP` | **PASS** | 0.794 – 0.983 | – |
| **1BB** | 1B | push | locked plate | `PPPPP` | `PPPPPPPPPPPP` | **PASS** | 0.789 – 0.981 | – |
| **1DA** | 1D | held | – | `PPPPP` | `PPPPPPPPPPPP` | **PASS** | 0.717 – 0.988 | – |
| **1FA** | 1F | held | – | `PPPPP` | `PPPPPPPPPPPP` | **PASS** | 0.834 – 0.967 | – |
| **1HA** | 1H | push | – | `PPPFF` | `PPFPPPFFFFFF` | **FAIL** | 0.231 – 0.895 | layout_match |
| **1HB** | 1H | push | locked plate | `PPPPP` | `PPPPPPPPPPPP` | **PASS** | 0.741 – 0.905 | – |
| **1HC** | 1H | push | `panel-08-end` | `PPPFF` | `PPPPPPPFFFFF` | **FAIL** | 0.354 – 0.859 | layout_match |

**5 of 7 clips pass. Both failures are shot 1H, and neither is the anchored take.**

### layout_match frame by frame — the whole finding in two rows

12-sample run, evenly spaced across the 5 seconds:

| Take | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|--|--|--|--|--|--|--|--|--|--|--|--|
| 1HA (no anchor) | 0.90 | 0.81 | 0.45 | 0.76 | 0.70 | 0.66 | **0.23** | **0.28** | **0.33** | **0.37** | **0.35** | **0.34** |
| 1HB (anchored) | 0.90 | 0.90 | 0.90 | 0.74 | 0.75 | 0.88 | 0.88 | 0.88 | 0.89 | 0.89 | 0.90 | **0.91** |
| 1HC (off-model anchor) | 0.86 | 0.84 | 0.79 | 0.72 | 0.65 | 0.60 | 0.57 | **0.53** | **0.52** | **0.49** | **0.47** | **0.35** |
| 1BA (no anchor) | 0.98 | 0.97 | 0.89 | 0.84 | 0.84 | 0.85 | 0.88 | 0.86 | 0.84 | 0.83 | 0.82 | 0.79 |
| 1BB (anchored) | 0.98 | 0.97 | 0.95 | 0.90 | 0.88 | 0.79 | 0.79 | 0.89 | 0.88 | 0.88 | 0.88 | **0.98** |

Three distinct shapes:

- **No anchor** decays and stays down (1HA), or decays gently (1BA).
- **Anchored on the plate** dips and comes back up, ending at or above where it
  started (1HB 0.90 → 0.91; 1BB 0.98 → 0.98).
- **Anchored off-model** decays *monotonically and further* — 1HC has no dip-and-
  recover at all, it walks steadily away from the plate for the entire clip.

### Other checks

| Take | staging margin | couch occupancy | wardrobe |
|---|---|---|---|
| 1BA | 0.515 – 0.780 | 0.96 – 1.18 | 1.07 – 2.02 |
| 1BB | 0.527 – 0.768 | 0.98 – 1.05 | 0.82 – 1.57 |
| 1DA | 0.150 – 0.277 | 0.96 – 0.99 | 0.86 – 1.03 |
| 1FA | 0.453 – 0.490 | n/a | n/a (no characters in 1F) |
| 1HA | 0.654 – 0.847 | n/a | 0.94 – 1.24 |
| 1HB | 0.672 – 0.867 | n/a | 0.97 – 0.99 |
| 1HC | 0.645 – 0.846 | n/a | 0.93 – 1.22 |

Thresholds: staging margin > 0.02, couch occupancy 0.45–2.20, wardrobe > 0.35.
Nothing came near a boundary, and **`staging_orientation`, `couch_occupancy` and
`wardrobe` passed on every sampled frame of every clip including the two
failures.** Note especially that 1HC's wardrobe reads 0.93–1.22 — a healthy pass
— on a clip that ends with Mia in the wrong top and the wrong hair. See §6.

---

## 4. What the failing frames actually contain

**`1HA` — a reframe, not a break
([sheet](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-720p/sheets/1H-abc.png), top row).**
The push-in crops the two out-of-focus foreground silhouettes off both edges of
frame — those are the plate's `gabe_edge` and `nina_edge` regions, and both go to
**0.00** — and pushes past Mia's torso so the `mia_top` region reads 0.00 as well.
Mia herself is on-model in every frame: dark curly hair worn down, magenta
star-print tee, the worried look up. The lamp, the window and the rain are all
still there. This is VIDEO-GATE limit 2 — the gate cannot tell reframed-by-design
from drifted-off-model — but it is not the marginal case G3 was. 0.231 against a
0.55 threshold is not a near miss, and by the last third of the clip the shot
genuinely is not the plate's framing any more.

**`1HB` — the plate, for five seconds** (middle row). Both foreground
silhouettes stay at both edges, the lamp stays put, the lightning stays in the
window. There is nothing to look at, which is the point.

**`1HC` — the model renders the frame you give it** (bottom row). t=0.10s through
t=3.75s look like a slightly pushed-in 1H. The final grab is a **different girl**:
straight dark hair pulled into a ponytail, pale pink star-print top, seated
against a beige couch, no window frame, the lightning floating on a blue wall.
It has interpolated all the way into `panel-08-end`. This is the single most
useful frame in the task — it is the direct proof that `<LAST_FRAME>` is an
enforced target rather than a suggestion, and it is why the Take B result can be
trusted as an effect rather than dismissed as a redundant tag being ignored.

---

## 5. Measured: what the anchor does to the camera

Affine ECC registration of each frame against the clip's own first frame,
downsampled to 640x360. `scale` > 1 means zoomed in. Script:
`scripts/video/camera_travel.py` (new here; #340 used this method but never
committed the code). Raw numbers: `gate/camera-travel*.json` on R2.

| Take | Camera | Anchor | 10% | 30% | 50% | 70% | 90% | **100%** | zoom rate |
|---|---|---|---|---|---|---|---|---|---|
| 1BA | push | – | 1.016 | 1.062 | 1.136 | 1.244 | 1.325 | **1.367** | 7.4%/s |
| 1BB | push | plate | 1.005 | 1.048 | 1.108 | 1.177 | 1.195 | **1.000** | 0.0%/s |
| 1HA | push | – | 1.005 | 1.032 | 1.091 | 1.131 | 1.183 | **1.207** | 4.2%/s |
| 1HB | push | plate | 1.001 | 1.005 | 1.010 | 1.011 | 1.004 | **1.001** | 0.0%/s |
| 1HC | push | off-model | 1.009 | 1.062 | 1.143 | 1.222 | 1.226 | **n/c** | – |
| 1DA | held | – | – | – | 1.009 | – | – | **1.018** | 0.4%/s |
| 1FA | held | – | – | – | 1.004 | – | – | **1.014** | 0.3%/s |

`n/c` = the affine model would not converge. 1HC's final frame cannot be
registered against its own first frame at all, because it is a different room.

Four things fall out:

1. **The anchor is satisfied exactly.** Both anchored takes land on 1.000 /
   1.001 with a residual shift of (0.0, 0.0) and (−0.4, −0.2) pixels at 640x360.
   Not approximately the plate — the plate.
2. **A push-in on a close-up travels three times as far as on a wide.** 1HA
   reaches 1.207 in five seconds against #340's T1 (the 1A wide, same clause,
   same duration) at 1.065. Same words, much bigger move, and it is what breaks
   1H. Worth carrying into every close-up in the film.
3. **The model has two different ways of satisfying the anchor, and one of them
   is bad.** On 1H it simply *did not push* — 1.011 peak, a locked-off shot. On
   1B it ran the full push out to 1.195 and then **jump-cut back**:

   | 1BB frame | 4.71s | 4.75s | 4.79s | **4.83s** | 4.88s | 4.92s |
   |---|---|---|---|---|---|---|
   | scale | 1.193 | 1.193 | 1.193 | **1.000** | 1.000 | 1.000 |

   That is a single-frame cut on frame 116 of 120, not a decelerating return. It
   is a visible artifact and an editor would reject it — **and the gate rewarded
   it**, scoring that final frame 0.98, its best of the clip. One sample, but a
   sharp one.
4. **"Held" is held.** 1DA and 1FA drift 1.8% and 1.4% over five seconds,
   consistent with #340's T2/T4.

---

## 6. The A/B, stated plainly

**Does supplying a last frame improve composition fidelity, hurt it, or make no
measurable difference?**

**It improves it, decisively, when the last frame is the locked plate — and the
size of the improvement depends entirely on whether the shot was going to drift
in the first place.** Two paired samples:

| Shot | worst layout, A | worst layout, B | Δ | final frame, A | final frame, B | verdict change |
|---|---:|---:|---:|---:|---:|---|
| **1H** (close-up, push) | 0.231 | **0.741** | **+0.510** | 0.34 | **0.91** | **FAIL → PASS** |
| **1B** (medium, push) | 0.794 | 0.789 | −0.005 | 0.79 | **0.98** | PASS → PASS |

- On **1H**, where the unanchored push walked the framing off the plate, the
  anchor is the difference between a clip that fails six of twelve frames and one
  that passes twelve of twelve. **+0.510 on the worst frame.**
- On **1B**, where the unanchored take already held, the anchor made **no
  measurable difference to the floor** (−0.005, noise) and improved only the
  final frame (+0.19) — by jump-cutting, which is worse footage, not better.
- And the direction is not automatic. **1HC scores 0.354 — worse than nothing.**
  An anchor on an off-model frame is actively harmful: 1HC's decay is monotonic
  where 1HA's at least wobbles, because the model is steering somewhere wrong on
  purpose.

So the mechanism is not "a last frame stabilises video." It is **"the model
lands on the last frame you give it."** That helps exactly as much as the frame
you supply is worth, and hurts when it is not.

**These are single clips per cell, not rates.** Two A/B pairs and one probe. The
1H result is a 0.510 swing that flips a verdict and is corroborated by an
independent measurement (camera travel 1.207 → 1.011) and by eye on the frames,
so it is safe to act on. The 1B non-result is one sample and should not be read
as "anchoring does nothing on medium shots." The jump-cut is one occurrence of
one failure mode.

### The cost of an anchor

| | video output tokens | input tokens | billed |
|---|---:|---:|---:|
| Take A (first frame only) | 28,960 | ~1,340 | ~$0.5233 |
| Take B/C (first + last) | 28,960 | ~2,450 | ~$0.5252 |

A last frame adds about 1,100 input tokens — the second image — and **$0.0017
per clip**. Video output tokens are identical. Composition fidelity is, for
practical purposes, free.

---

## 7. Recommendation

**Adopt last-frame anchoring for Scene 1 production renders, on this rule:**

> `<LAST_FRAME>` may only ever be a panel that has passed its own shot's
> validation gate. Today, for every Scene 1 shot, the only such panel is that
> shot's own `scene-01-1?-start.png`.

Concretely:

1. **Use it on every close-up and every shot with a camera move.** That is where
   the unanchored push drifts (1H: 1.207 zoom in 5s) and where the anchor pays
   (+0.510). 1H is the emotional anchor of the scene; it is not a shot to leave
   to drift.
2. **Do not use `scene-01-panel-0?-end.png` as a last frame, for any shot.**
   They are the March pre-lock set: wrong room, wrong TV, wrong wardrobe, and in
   1D's case a mirrored two-shot. 1HC is what that produces. They should
   arguably be moved out of the `v4/` prefix on R2 — sharing it with the locked
   set is what made this task's premise wrong, and it will mislead the next
   agent too.
3. **Watch for the jump-cut.** Anchoring guarantees the final frame, not a
   graceful arrival at it. Check the last ~5 frames of every anchored clip; if
   the ECC scale steps rather than eases (`camera_travel.py --samples 10`),
   either re-roll or trim the tail. **The gate will not catch this — it scored
   1BB's cut frame 0.98.**
4. **The real prize is still ahead and this task did not reach it.** The May 23
   post wanted start-plus-end frames so *character action* becomes renderable.
   That needs a validated end panel that differs from the start — a v4-quality
   "Leo turns to look" or "Gabe lowers his watch" — which does not exist for any
   Scene 1 shot. Anchoring on the start panel buys composition stability, and
   1HB proves the machinery works, but it necessarily buys a shot that ends where
   it began. **Generating a validated v4 end panel for one shot is the obvious
   next task**, and 1HC says the payoff is real: the model will hit whatever
   target you give it.

Two limits to carry with that:

- **The gate cannot see identity.** Five passes mean the room is the locked room
  and the costume colours are right. They do not mean Mia is Mia — 1HC's wardrobe
  check read 0.93–1.22 (a comfortable pass) on frames where Mia has the wrong
  hair and the wrong top, because a pink top is close enough to magenta by hue
  coverage. Before any of this is cut into the film it needs
  `scripts/validate/shot_validator.py` (~$0.02/shot) on top.
- **1C, 1E, 1G and 1I remain unrenderable-with-confidence.** Unchanged from #339.
  Nothing here moves them; that needs the paid vision validator.

---

## 8. Notes on the task's premises

Three things in the task brief did not match the repo, recorded so the next
agent does not re-derive them:

- **`docs/process/scene-01-manifest.json` and `docs/process/do-not-invent.md` do
  not exist** — not in this branch, not in `main`, not in any of #336/#337/#339/
  #340. The manifest lives at `asset-bible/manifests/scene-01.json`, with a
  pinned copy for the gate at `docs/process/continuity/bible/scene-01.json`.
  Those two have drifted: the pinned copy still has v3 `panel_url`s and puts 1I
  in `living_room`, while the current manifest has v4 urls and 1I in
  `front_entryway`. The gate reads the pinned copy, so this does not affect any
  score here, but **the pinned copy is stale and should be refreshed** with the
  recipe in VIDEO-GATE §Files. Prompts in this task used the current manifest.
- **"the v4 panel set has start/end pairs" is not the case.** §1.
- **The audio split #340 reported does not reproduce.** #340 found its two
  push-in takes digitally silent and its two held takes loud, and suggested the
  camera clause drove it. Here:

  | Take | Camera | mean | peak |
  |---|---|---|---|
  | 1HA | push | −90.3 dB | −64.7 dB |
  | 1HB | push | −91.0 dB | −84.3 dB |
  | 1BA | push | −26.1 dB | −4.3 dB |
  | 1BB | push | −23.9 dB | −2.6 dB |
  | 1HC | push | −20.7 dB | −1.8 dB |
  | 1DA | held | −28.2 dB | −8.9 dB |
  | 1FA | held | −24.3 dB | −2.6 dB |

  Four push-in takes are loud and two are silent, on the same clause. It is not
  the camera clause and it is not the cast. **Whatever drives it, "Silent." is
  not a control — strip unconditionally**, which is what #340 concluded anyway.
  Not worth a paid experiment.

---

## 9. Cost

Billed from each response's own token usage (`cost_from_usage`), not estimated.

| Take | Shot | Kind | Video tokens | Input tokens | Gen time | **Billed** |
|---|:--:|---|---:|---:|---:|---:|
| 1BA | 1B | first only | 28,960 | 1,374 | 33.6s | **$0.5238** |
| 1DA | 1D | first only | 28,960 | 1,441 | 32.9s | **$0.5244** |
| 1FA | 1F | first only | 28,960 | 1,312 | 36.6s | **$0.5233** |
| 1HA | 1H | first only | 28,960 | 1,335 | 29.8s | **$0.5217** |
| 1HB | 1H | first + last | 28,960 | 2,440 | 38.7s | **$0.5247** |
| 1BB | 1B | first + last | 28,960 | 2,479 | 34.0s | **$0.5260** |
| 1HC | 1H | first + last (probe) | 28,960 | 2,440 | 32.4s | **$0.5249** |
| | | **35s** | **202,720** | | | **$3.6689** |

**$3.6689 of a $4.00 cap. 7 generations of a 9 allowance. No retries, no
failed calls, nothing blocked or filtered.**

720p bills at exactly 5,792 video output tokens per second, confirming #340 on a
second set of shots — 28,960 tokens for every 5s clip regardless of shot, camera
clause or frame binding. At $17.50/1M that is $0.1014 per second of 720p. All
gating, frame extraction, camera-travel measurement and panel scoring was
OpenCV/ffmpeg: **$0.00**.

Nothing was re-rolled. 1HA and 1HC failed their gate and are reported as failures
rather than regenerated — 1HA because its failure is the finding, and 1HC because
it is a probe that did exactly what it was meant to.

---

## 10. Reproducing

```bash
./scripts/setup_python_env.sh
mkdir -p work/in
rclone copy r2:rex-assets/storyboards/v4/scene-01/ work/in/ \
    --include 'scene-01-1?-start.png' --include 'scene-01-panel-0?-end.png'

.venv/bin/python scripts/video/run_scene01_first_last.py 1HA work/   # one per call
ffmpeg -i work/out/1HA_raw.mp4 -c:v copy -an work/out/1HA.mp4

cd docs/process/continuity
../../../.venv/bin/python check_video.py ../../../work/out/1HA.mp4 --shot 1H -v

cd ../../..
.venv/bin/python scripts/video/camera_travel.py work/out/1H?.mp4 --samples 10
```

## 11. Files

| Where | What |
|---|---|
| `r2:.../scene01-720p/1{BA,BB,DA,FA,HA,HB,HC}.mp4` | the seven takes, audio stripped |
| `r2:.../scene01-720p/raw/*_raw.mp4` | untouched downloads, audio intact |
| `r2:.../scene01-720p/frames/` | 40 frame grabs, including every frame read in §4 |
| `r2:.../scene01-720p/sheets/` | the three comparison sheets |
| `r2:.../scene01-720p/gate/*-gate5.json`, `*-gate12.json` | gate reports at both densities |
| `r2:.../scene01-720p/gate/1??.json` | generation sidecars: prompt, usage, billed cost |
| `r2:.../scene01-720p/gate/camera-travel*.json` | ECC registration measurements |
| `r2:.../scene01-720p/gate/panel-to-shot-scores.json` | every panel against every shot's plate (§1) |
| `scripts/video/run_scene01_first_last.py` | the runner |
| `scripts/video/camera_travel.py` | the camera-travel measurement |
