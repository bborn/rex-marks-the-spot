# fal.ai as a video provider (MiniMax H3)

**Status:** live, verified end to end 31 Aug 2026 (task #343). Two paid renders,
**$0.50 total** against a $2.00 cap.
**Code:** `scripts/video/fal_video.py`, behind `video.base.VideoGenerator`.
**Tests:** `scripts/video/test_fal_video.py` (offline; the transport, ffmpeg and
the R2 uploader are all injected).

fal is our second video backend, alongside Gemini Omni Flash. It exists for two
things Omni cannot do, and it happens to be about half the price.

1. **First frame AND last frame in one call.** `image_url` + `end_image_url` on
   `minimax/h3/image-to-video`. Last-frame anchoring moved a failing shot from
   0.231 to 0.741 on the continuity gate, so this is the core workflow, not a
   nicety.
2. **It renders shots Google refuses.** Scene 17 (two children alone in a police
   car) is unmakeable on Omni in any wording. It rendered on H3 first try with
   `enable_safety_checker` left at its default `true`.

Everything in the "Parameters" section below was read off the live endpoint
schema, not inferred:

```
https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=minimax/h3/image-to-video
```

---

## Price table — image-to-video endpoints we might use

Published list rates, read from the fal model catalogue (`fal.ai/api/models`)
on 31 Aug 2026. Per second of generated video unless noted.

| Endpoint | 480p | 720/768p | 1080p / 2K | 4K | Notes |
|---|---|---|---|---|---|
| **`minimax/h3/image-to-video`** | **$0.05** | **$0.06** (768P) | $0.13 (2K) | $0.16 | **Our primary.** first+last frame. Not promotional. |
| `minimax/h3/text-to-video` | $0.05 | $0.06 | $0.13 | $0.16 | Same model, no frames. |
| `minimax/h3/reference-to-video` | $0.05 | $0.06 | $0.13 | $0.16 | Up to 9 ref images; first 5 free, then $0.08 each. |
| `minimax/h3-max/image-to-video` | $0.025 → **$0.05** | $0.04 → **$0.08** | — | — | **Promo expires 1 Sept 2026.** See below. |
| `fal-ai/minimax/hailuo-02/standard/image-to-video` | ~$0.017 (512P) | $0.045 (768P) | — | — | Older Hailuo; cheapest MiniMax. |
| `fal-ai/veo3.1/lite/first-last-frame-to-video` | — | $0.03 no audio / $0.05 with | $0.05 / $0.08 | — | Veo's own first+last, via fal. |
| `fal-ai/veo3.1/fast/first-last-frame-to-video` | — | $0.10 / $0.15 | same | $0.30+ | |
| `fal-ai/veo3.1/first-last-frame-to-video` | — | $0.20 / $0.40 | same | $0.40+ | |
| `alibaba/wan-3.0/image-to-video` | $0.05 | $0.10 | $0.20 | — | |
| `wan/v2.6/image-to-video/flash` | — | $0.05 | $0.075 | — | |
| `fal-ai/kling-video/v3/turbo/standard/image-to-video` | — | $0.112 | — | — | |
| `lightricks/ltx-2.5/image-to-video/fast` | — | $0.09 | $0.13 | $0.19 (1440p) | |
| `bytedance/seedance-2.0/image-to-video` | — | $0.3034 | $0.682 | — | Token-priced; expensive. |

For comparison: **Gemini Omni Flash measures at $0.104/s** at 720p (it bills by
output token, not by second — see `scripts/video/omni_flash.py`). H3 at 768P is
$0.06/s, so a 5s shot is $0.30 on fal vs $0.52 on Omni.

The rates the code actually charges against live in `USD_PER_SECOND` in
`scripts/video/fal_video.py`. An endpoint with no entry there **refuses to
render** rather than producing an unauditable clip.

### The h3-max promo trap

`minimax/h3-max/*` advertises $0.025/s at 480p and $0.04/s at 768p. Those are
50%-off launch rates and **the discount ends 1 September 2026**, after which
480p is $0.05/s and 768p is **$0.08/s** — i.e. h3-max at 768p becomes *more*
expensive than plain h3 at $0.06/s. Do not build the pipeline on h3-max.

The code encodes h3-max at its **post-promo** rates so an estimate can never come
in under the real bill, and `FalVideoGenerator` prints a warning if you construct
it against a promotional endpoint.

---

## Parameters (`minimax/h3/image-to-video`)

| Field | Type | Notes |
|---|---|---|
| `prompt` | string, required | Required even for image-to-video. Max 50,000 chars. |
| `image_url` | string | **First frame.** Public URL or `data:` URI. Omit and the request routes to text-to-video. |
| `end_image_url` | string | **Last frame.** The reason this provider exists. |
| `duration` | int | **Minimum 5**, maximum 15. See below. |
| `resolution` | enum | `480P`, `768P`, `2K`, `4K`. **API default is 2K** — see below. |
| `enable_safety_checker` | bool | Default `true`. Leave it there; Scene 17 rendered with it on. |
| `seed` | int | For reproducible retries. |
| `prompt_expansion_mode` | string | `fast` / `balanced` (default) / `quality`. |
| `sync_mode` | bool | Returns base64 instead of a CDN URL. Not used. |

`aspect_ratio` is **not** a parameter on image-to-video: the output follows the
input image, so we are not locked to 16:9 (our verification clip came back
864×480 from a 16:9 panel). The text- and reference-to-video endpoints *do* take
one, from `adaptive | 21:9 | 16:9 | 4:3 | 1:1 | 3:4 | 9:16`.

### The 5-second minimum

`duration` has a schema minimum of 5 and billing has the same floor: a 3s
request is a 5s bill. The wrapper raises a short request to 5, **says so on
stdout**, and records both `requested_duration_seconds` and
`billed_duration_seconds` in the sidecar. Trim in the edit, not in the request.

### The 2K default is a trap

fal's own default `resolution` is **2K at $0.13/s** — more than double 768P. The
wrapper therefore always sends an explicit resolution and defaults to `768P`.
Aliases `480p/720p/768p/2k/4k` normalise onto the enum; `720p` maps to `768P`
(the nearest native mode). **`1080p` is rejected**, not guessed: it sits between
768P and 2K and guessing upward would silently double the rate.

---

## Things that bite

### Output CDN URLs expire in ~7 days

fal returns the clip on `v3.fal.media`. Those URLs stop resolving after roughly
a week. The wrapper **downloads the file and pushes it to R2 as part of the
call** (`upload_to_r2=True`, default key `video/fal/<YYYYMMDD>/<name>.mp4`). The
sidecar records `fal_cdn_url`, `fal_cdn_fetched_at` and `fal_cdn_expires_after`
so a stale link is identifiable rather than mysterious. A clip we cannot fetch
next week is a clip we do not have.

### Audio cannot be disabled

Every H3 clip carries an AAC stream and there is no parameter to turn it off —
same as Omni. `strip_audio=True` (the default) remuxes on ingest:

```
ffmpeg -i in.mp4 -c:v copy -an out.mp4
```

Stream copy, no re-encode. Measured on the verification render: the fal CDN copy
is `h264 + aac`, the file we keep is video-only.

### Concurrency is capped at 2 on new accounts

`generate_batch(jobs, max_concurrency=2)` honours it and defaults to it; a wider
fan-out just collects server-side rejections. Raising the limit prints a warning.
A failing shot comes back as an Exception in the results list positionally, so
one moderation block does not throw away the clips that rendered.

### Queue, not sync

Submit `POST https://queue.fal.run/<endpoint>`, poll
`.../requests/<id>/status` until `COMPLETED`, then `GET .../requests/<id>` for
the result. fal retries server-side and **does not bill 5xx or cold starts**, so
an error that reaches us is a real rejection worth reading: moderation, a bad
parameter, or an exhausted balance.

### Local frames become data URIs

H3 takes `image_url` only — there is no multipart upload — so a local panel is
inlined as `data:image/png;base64,...`. Both paths are verified live. Panels
that already live on R2 should be passed as their **public R2 URL**: it is what
the pipeline will do at scale and it keeps the request body small.

---

## How to pick a backend

```python
from video import create_generator, FIRST_LAST_FRAME

gen = create_generator("fal-h3")          # minimax/h3/image-to-video
gen.supports(FIRST_LAST_FRAME)            # True

result = gen.image_to_video(
    "slow push in",
    "out/shot-1A.mp4",
    first_frame="https://pub-....r2.dev/storyboards/v4/scene-01/1A.png",
    last_frame="https://pub-....r2.dev/storyboards/v4/scene-01/1B.png",
    duration_seconds=5,
    resolution="768P",
    r2_path="video/scene-01/shot-1A.mp4",
)
```

`image_to_video(prompt, output_path, first_frame, last_frame=None)` is the
model-agnostic entry point on `VideoGenerator`. A backend that cannot honour a
last frame **raises** rather than dropping it — a silently dropped anchor looks
like a successful render right up until the continuity gate fails it.

Registered names: `fal-h3` (= `fal-h3-i2v`), `fal-h3-t2v`, `fal-h3-ref`,
alongside `omni-flash`, `veo-3.1`, `p-video`.

Rules of thumb:

| Situation | Backend |
|---|---|
| Shot defined by two storyboard panels (our default) | `fal-h3` at 768P, first+last frame |
| Shot Omni refuses (kids in custodial settings — Scenes 15, 17, 20, 22) | `fal-h3` |
| Non-16:9 shot | `fal-h3` — output follows the input panel |
| Cheap pass/fail probe, no quality judgement | `fal-h3` at 480P ($0.05/s), or Omni at 360p/3s ($0.10) if 3s matters — H3 cannot go under 5s |
| Character conditioning from turnarounds, no panel | `fal-h3-ref` (≤5 images free) or `omni-flash` reference_to_video |
| Needs a real audio bed from the model | Neither — we strip audio on both and score sound separately |

**Which is cheaper depends on length.** Omni can make a 3s clip; H3 cannot go
below 5s. A 3s 360p Omni probe is ~$0.10; the cheapest possible H3 clip is
5s × $0.05 = $0.25. Above 5s, H3 wins on every comparable resolution.

---

## Verification, 31 Aug 2026

Two renders, `scripts/video/run_fal_verify.py`, both 5s at 480P = $0.25 each,
**$0.50 total** against the $2.00 cap. These are **plumbing verification, not
gate-passing output** — nothing downstream should consume them, and no quality
comparison against Omni was made (that is task #342's identity validator first).

**Run A — first+last frame, local files → data URI.** Scene 1 v4 panels
`scene-01-1A-start.png` and `scene-01-1B-start.png`. The clip opens on the wide
living-room composition of 1A and lands on the medium of Leo from 1B. fal's own
`expanded_prompt` confirms the conditioning verbatim: *"Picture 1 … aligns with
the 0.00-second mark … Picture 2 … aligns with the 5.00-second mark"*. Output
864×480, 5.17s. Source on the CDN: `h264 + aac`. Kept copy: video only.
→ https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/video/fal-verify/fal_verify_A.mp4

**Run B — first frame only, public R2 URL passthrough.** Proves URL passthrough,
the R2 upload path and audio stripping on a second, independent request.
→ https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/video/fal-verify/fal_verify_B.mp4

The runner reads the sidecars already in its output directory and **refuses to
start a run that would push cumulative spend past $2.00**.

---

## Credentials

`FAL_KEY` lives in the environment (`~/.bashrc`). It is sent as an
`Authorization: Key <...>` header and is never printed, logged, or written to a
sidecar — there is a test for that.
