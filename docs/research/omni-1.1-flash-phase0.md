# Phase 0 — Gemini Omni 1.1 Flash smoke test

**Date:** 2026-08-28
**Scope:** cheap capability probe, 360p only. Not a quality evaluation.
**Budget:** cap raised mid-run to $2.50. **Actual spend: $1.81.**
**Clips generated:** 6 (4 planned + 2 unintended, both documented below).

Artifacts: `r2:rex-assets/animation-tests/omni-1.1-flash-phase0/`
Public: `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/omni-1.1-flash-phase0/<file>`

---

## Headline

**The child-character safety filter did NOT fire.** A prompt naming Mia and Leo,
giving their ages (8 and 5), and using the words "kids" and "siblings" generated
normally. The Veo 3.1 `no_media_generated` failure mode we worked around in May
2026 does not reproduce here. **We can drop the depersonalization workaround for
this model** — pending a wider probe across the more sensitive beats.

Second headline, less good: **audio cannot be reliably switched off**, and there
is no parameter for it. See "Audio".

---

## 1. Confirmed model ID

**`gemini-omni-1.1-flash`** — this is the one to use.

Both candidate IDs are live and both are accepted by the Interactions video
path (verified by sending a deliberately corrupt image, which fails at image
decode *after* the model is resolved, so a bad model ID would have 404'd first):

| ID | `models.get` | video path | display name |
|---|---|---|---|
| `gemini-omni-1.1-flash` | resolves | accepted | Gemini Omni 1.1 Flash |
| `gemini-omni-flash-preview` | resolves | accepted | Gemini Omni Flash Preview |

They are **distinct model entries, not aliases.** `gemini-omni-1.1-flash` is
the canonical one: an unknown ID 404s with
`Model 'gemini-omni-9.9-flash' not found. Did you mean 'gemini-omni-1.1-flash'?`
All six generations below used `gemini-omni-1.1-flash`.

### Blocker worth knowing: the SDK must be >= 2.0.0

The repo's pinned `google-genai==1.61.0` sends the legacy Interactions wire
format, and **every** call fails with:

> The legacy Interactions API schema is no longer supported. Please upgrade your
> google-genai Python SDK to version >= 2.0.0

The May 2026 breaking change retired it. This work ran against **2.20.0** in a
throwaway venv, because bumping the pin repo-wide would touch every existing
image-generation script. **Follow-up:** decide whether to upgrade globally or
keep Omni on its own venv (see "Follow-ups").

---

## 2. Does the safety filter block child characters? — **No.**

G2 and G3 are the identical shot from the identical validated panel. The only
variable is how the characters are described.

| | G2 (control) | G3 (safety probe) |
|---|---|---|
| Wording | "figures", "characters" — no ages, no "kids" | "Mia, an 8-year-old girl", "her little brother Leo, a 5-year-old boy", "the two kids", "the siblings" |
| Result | generated | **generated** |
| Cost | $0.1825 | $0.3572 |

G3 prompt, verbatim:

> Hold this exact composition, framing and art style. Mia, an 8-year-old girl,
> and her little brother Leo, a 5-year-old boy, are the two kids sitting
> together on the couch; the siblings stay seated while their teenage babysitter
> remains in the background. Camera only: a slow, gentle push-in. No dialogue.
> No music. No sound effects. Silent.

No error, no `no_media_generated`, no RAI filter count, no content warning. The
output is visually indistinguishable from the G2 control — same composition,
same characters, same framing.

**Caveat before we act on this:** one prompt, one panel, one calm beat. It does
not clear the model for the whole film. The beats most likely to trip a filter
are the ones with a child in apparent jeopardy (the storm, the abduction beat,
anything with Jetplane looming over Leo), and none of those were probed. Worth a
targeted follow-up probe on 2–3 of the tensest Act 2 panels before we commit the
pipeline to un-depersonalized prompts.

---

## 3. Can audio be turned off? — **No. And it's a problem.**

**There is no audio parameter.** `response_format` accepts only `type`,
`aspect_ratio`, `resolution`, `duration`, `delivery`, `gcs_uri`;
`generation_config.video_config` accepts only `task`. Nothing for audio.

**Every clip ships an AAC stereo 48 kHz track.** ffprobe confirms an audio
stream in all 6 outputs. The negative prompt instruction
("No dialogue. No music. No sound effects. Silent.") was present in *every*
prompt, and it does **not** remove the track. What it does is inconsistent:

| Clip | duration | audio stream | mean dB | max dB | verdict |
|---|---|---|---|---|---|
| G1 text_to_video (empty room) | 10.005s | yes | −48.1 | −34.6 | effectively silent |
| G2 image_to_video (depersonalized) | 5.013s | yes | **−28.1** | **−8.2** | **loud content** |
| G3 image_to_video (child-explicit) | 10.005s | yes | **−27.7** | **−5.3** | **loud content** |
| G4 reference_to_video | 5.013s | yes | −51.9 | −32.6 | effectively silent |
| PROBE 12 refs | 10.005s | yes | −28.1 | −3.6 | **loud content** |

The pattern: shots with **people in them** get loud generated audio regardless
of the silence instruction; empty/static shots come back as near-silent room
tone. So prompt-based suppression is not a control — it is a coincidence that
holds only when there is nothing in frame to make noise.

**Recommendation:** treat every Omni output as having an unwanted audio track
and strip it unconditionally on ingest:

```bash
ffmpeg -i in.mp4 -c:v copy -an out.mp4
```

This is a one-line pipeline step, so it is not a blocker — but it must be
mandatory, not best-effort, or Seedance's content-filter incident repeats.

---

## 4. Did the panel-as-first-frame hold composition? — **Yes, strongly.**

This is the capability Omni Flash lacked in the Google Flow UI, and it works.

G2/G3 used `image_to_video` with the validated v4 panel 1A as `<FIRST_FRAME>`.
Both outputs preserve the panel's staging essentially intact: couch centred,
Mia and Leo seated in the same positions, Jenny on the right in the armchair on
her phone, Gabe and Nina mid-ground by the kitchen, the storm window and
lightning behind, the TV at left, and the scattered dinosaur toys in the same
spots on the rug. Lighting, colour palette and the render style all carry over.

Compare `G2_image_to_video_frame.png` against the source panel
`r2:rex-assets/storyboards/v4/scene-01/scene-01-1A-start.png` — it reads as the
same shot, not a reinterpretation.

**Panel used — note a deviation from the task brief.** The brief pointed at
`r2:rex-assets/storyboards/act1/scene-01/`. Those are the older pre-validation
panels. Per the Validation Gates rule in CLAUDE.md ("before generating from ANY
artifact, confirm that artifact passed its validation gate"), I used the v4
panel instead: `r2:rex-assets/storyboards/v4/scene-01/scene-01-1A-start.png`,
which is from the 9/9 PASS set (`reports/audit-v4/scene-01-audit.md`).

---

## 5. Max reference images — **at least 12. No low cap exists.**

Sources claiming 3, 6 or 7 are all wrong for this API.

A `reference_to_video` request carrying **12 real reference images** (the seven
locked character turnarounds plus the 1A panel, cycled to 12) was accepted and
generated normally: `PROBE_12refs.mp4`. No count error at any point.

I did not push past 12 — it stopped being a useful question once it was clear
the cap is well above the 2–7 we would ever use in a shot.

Method note, since the brief asked for this to be probed with free failed calls:
that technique does **not** work here. Sending N corrupt images returns
`Unable to process input image` for every N up to 12 — image decode runs
*before* any count validation, so the decode error masks the count check
permanently. Establishing the real limit therefore requires valid images, and a
valid within-limit request generates video. That cost one unplanned clip
($0.3808), which is how `PROBE_12refs` exists.

### Character consistency (G4)

`reference_to_video` with just the Mia and Leo turnarounds produced both
characters clearly on-model: Mia's dark curly hair, pink top and jeans; Leo
blond with the green T-Rex plush. Recognisably our characters, not generic kids.
Encouraging for the consistency problem, though wardrobe drifted (Leo appears in
a green tee and shorts rather than his dinosaur pajamas) — reference images
carry *identity* but do not pin *costume*, so wardrobe still has to be stated in
the prompt from the manifest.

---

## 6. Watermark — **none visible.**

Bottom-right corners of all four frame grabs were cropped and upscaled 3×. No
visible watermark, logo or text overlay in any clip. (SynthID is imperceptible
by design and would not show up this way — this finding is only about a
*visible* mark.)

---

## 7. Exact dollars spent — **$1.81**

Billing is by **output token**, not per second. Published rates:
input $1.50/1M, video output $17.50/1M.

At 360p a clip is **1,931 video tokens per second** (≈$0.0338/s) — measured, and
consistent with Google's stated 5,792 tokens/s for 720p at ≈$0.10/s.

| Run | video tok | other out | input tok | USD |
|---|---|---|---|---|
| G1 `text_to_video` (10s) | 19,310 | 805 | 50 | 0.3521 |
| PROBE 12 refs (10s, unplanned) | 19,310 | 1,322 | 13,139 | 0.3808 |
| G2 `image_to_video` (5s) | 9,655 | 676 | 1,161 | 0.1825 |
| G3 `image_to_video` (10s) | 19,310 | 997 | 1,189 | 0.3572 |
| G4 `reference_to_video` (5s) | 9,655 | 729 | 2,230 | 0.1851 |
| ACCIDENTAL `duration_seconds=999` probe (10s, unplanned) | 19,310 | 805 | 50 | 0.3521 |
| **TOTAL** | | | | **$1.8097** |

All rejected requests (400/404) were free.

**Two clips were unplanned and I should flag them plainly:**

1. **The `duration_seconds=999` probe.** I probed for a duration parameter by
   sending a speculative key under `video_config`. The API **silently ignores
   unknown keys in `video_config`** rather than rejecting them, so instead of a
   free 400 it generated a full-length 10s clip and billed for it. Its usage
   was not captured (the probe did not save the response), so its cost is
   modelled on G1, which is the identical request shape. This is the single
   most expensive mistake in the run and the reason for the warning in the
   wrapper's docstring.
2. **The 12-reference probe**, explained in §5 — unavoidable given that the
   free-rejection technique cannot reach the count check.

At the original $1.50 cap these two would have forced G4 to be dropped.

---

## 8. Confirmed API surface

Everything here was established against the live API, mostly via free rejected
requests that echo the supported set back in the 400 message.

```python
from google import genai                      # google-genai >= 2.0.0
client = genai.Client()                       # GEMINI_API_KEY from env

interaction = client.interactions.create(
    model="gemini-omni-1.1-flash",
    input=[
        {"type": "image", "data": <base64>, "mime_type": "image/png"},
        {"type": "text",  "text": "<FIRST_FRAME> slow push-in, hold composition."},
    ],
    response_format={
        "type": "video",
        "aspect_ratio": "16:9",   # only "16:9" | "9:16"
        "resolution": "360p",     # "360p" | "720p" | "1080p" | "4k"
        "duration": "5s",         # STRING, 3s-10s, defaults to 10s if omitted
    },
    generation_config={"video_config": {"task": "image_to_video"}},
)
video_bytes = base64.b64decode(interaction.output_video.data)
```

**`duration` lives on `response_format`, as a string, and is easy to get wrong.**
`generation_config.video_config` accepts **only** `task`. A
`duration_seconds` int placed there is accepted and silently ignored, and you
are billed for a 10s clip — verified, expensively. Confirmed bounds:

- `"999s"` → `Requested video duration 999s 0ns exceeds the maximum allowed 10s 0ns`
- `"0.5s"`/`"1s"`/`"2s"` → `is less than the minimum allowed 3s 0ns`
- Range is continuous (fractional seconds parse), **not** an enum of 4/6/8/10.
- Verified end-to-end: `duration="5s"` → ffprobe reports **5.013s**.

| Surface | Confirmed values |
|---|---|
| `video_config.task` | `text_to_video`, `image_to_video`, `reference_to_video`, `edit`, `extend` |
| `response_format.resolution` | `360p`, `720p`, `1080p`, `4k` |
| `response_format.aspect_ratio` | `16:9`, `9:16` — **no 4:3, no 2.39:1** |
| `response_format.duration` | `"3s"`–`"10s"`, default `10s` |
| Output | 640×360 @ 24fps h264 + AAC stereo at 360p |
| Response | `interaction.output_video.data` (base64), plus `steps[]` and `usage` |

Prompt tags bind media to roles: `<FIRST_FRAME>`, `<LAST_FRAME>`,
`<IMAGE_REF_0..n>`, `<VIDEO_REF_0>`. **Binding is by tag, not by position** — an
untagged prompt silently ignores its images. The wrapper auto-prepends any
missing tag for supplied media.

---

## 9. Verdict

Omni 1.1 Flash clears every bar this task was meant to test:

- Real API. No browser automation needed.
- First-frame anchoring from our validated storyboard panels works well — the
  main reason we cared.
- Reference images work with the locked turnarounds and carry character identity.
- The child-character filter does not fire on a normal scene description.
- No visible watermark.
- ~$0.034/s at 360p, ~$0.10/s at 720p.

Two things to design around: **audio must be stripped unconditionally**, and
**clips are capped at 10s**, so anything longer needs the `extend` task
(documented to reach 40s total, untested here).

Recommend proceeding to a costed bake-off against the current pipeline.

---

## Follow-ups

1. **Probe the tense beats.** One calm panel is not proof the safety filter is
   clear. Run the same G2/G3 A/B on 2–3 of the highest-jeopardy Act 2 panels
   before dropping depersonalization pipeline-wide.
2. **Decide the SDK story.** `google-genai>=2.0.0` is required for Omni, but the
   repo pins 1.61.0 and many image scripts depend on it. Either upgrade globally
   and regression-test the image scripts, or keep Omni in its own venv.
3. **Make audio stripping mandatory** (`ffmpeg -an`) in whatever ingests video.
4. **Test `extend`** for shots longer than 10s, and `edit` for fix-ups.
5. **Check 720p pricing empirically** before the bake-off — $0.10/s is 3× the
   360p rate and will dominate the budget.
