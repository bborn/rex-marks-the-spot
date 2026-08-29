# google-genai SDK split: 1.61.0 vs 2.x — decision

**Date:** 2026-08-29
**Task:** #337 — Resolve google-genai SDK split
**Decision:** **Upgrade to `google-genai==2.20.0` repo-wide.**
**API spend on this task: $0.00.** Every test below runs against a stubbed
`httpx` transport. No generation call left the machine.

---

## 1. The problem, restated

`scripts/video/omni_flash.py` drives Gemini Omni through
`client.interactions.create()`. On `google-genai` 1.61.0 every Omni call fails:

> The legacy Interactions API schema is no longer supported. Please upgrade your
> google-genai Python SDK to version >= 2.0.0

(Background: `docs/research/omni-1.1-flash-phase0.md` §1.)

There was a second, quieter problem underneath it: **the repo had no pin at
all.** There was no `requirements.txt`, no `pyproject.toml`, no lockfile. The
"pinned 1.61.0" everyone referred to was simply whatever happened to be sitting
in the task server's `~/.local/lib/python3.12/site-packages`. Omni's Phase
0/05/06 work ran from a throwaway `/tmp` venv that no longer exists on disk.

So this task had to produce the pin before it could bump it.

---

## 2. Dependency inventory

### 2a. `google-genai` (the SDK in question) — 35 files

**Live pipeline (must not break):**

| File | Surface used |
|---|---|
| `scripts/pipeline/orchestrator.py` | `generate_content`, `Part.from_bytes` |
| `scripts/validate/shot_validator.py` | `generate_content`, `Part.from_bytes`, `ThinkingConfig`, `GenerateContentConfig(response_mime_type=…)` |
| `scripts/video/omni_flash.py` | `interactions.create` — **2.x only** |
| `scripts/video/veo_generator.py` | `generate_videos`, `GenerateVideosConfig`, `Image.from_file` |

**Storyboard / character / panel generation — all `generate_content`:**

`fix_nina_scene1.py`, `fix_panel_04.py`, `fix_panel07_beard_wardrobe.py`,
`generate_act1_remaining.py`, `generate_act2_sketch_storyboards.py`,
`generate_act2_storyboards.py`, `generate_act3_storyboards.py`,
`generate_character_concepts.py`, `generate_expression_sheets.py`,
`generate_leo_turnaround_v3ef.py`, `generate_mia_turnaround_v2.py`,
`generate_music.py`, `generate_nina_turnaround.py`,
`generate_scene01_all_panels.py`, `generate_scene01_panel01_video.py`,
`generate_scene01_storyboards.py`, `generate_sketch_storyboards.py`,
`generate_storyboards.py`, `generate_trailer_storyboard.py`,
`regenerate_act2_rough_sketches.py`, `regenerate_consistency_panels.py`,
`regenerate_missing_act3.py`, `regenerate_scene01_bw_to_3d.py`,
`regenerate_tv_panel.py`, `regen_scene01_panel09.py`, `regen_scene01_v4.py`,
`regen_scenes_8_10.py`

**Used the Imagen `generate_images` path — the only 2.x casualty (4 files):**

`generate_environment_art.py`, `generate_environment_variations.py`,
`generate_turnaround_sheets.py`, `generate_nina_turnaround_v3.py` (fallback only)

### 2b. `google-generativeai` — 9 files, a *different* package

`google-generativeai==0.8.6` is Google's older, separately-deprecated library.
It is **not affected by this decision** — it has its own version line and its own
end-of-life. Nine Feb–May 2026 one-shot scripts still import it:

`fix_panel07_extra_kids.py`, `gen_asset_bible_ruben.py`,
`generate_character_turnaround.py`, `generate_dinosaur_concepts.py`,
`generate_gabe_turnaround_v4.py`, `generate_nina_turnaround_v4.py`,
`generate_nina_turnaround_v5.py`, `generate_scene1_panels_img2img.py`,
`regenerate_scenes_5_7_consistency.py`

It is pinned in `requirements.txt` so those scripts still import, and verified
to coexist with google-genai 2.20.0 (`pip check` clean). Migrating them off it
is a separate follow-up, not this task.

---

## 3. What actually changed between 1.61.0 and 2.20.0

Two venvs, `google-genai==1.61.0` and `==2.20.0`, otherwise identical. Transitive
dependency footprint differs by exactly one line (`websockets` 15.0.1 → 16.1.1).

Every symbol our scripts touch — `genai.Client`, `models.generate_content`,
`models.generate_videos`, `models.generate_images`, `types.GenerateContentConfig`,
`GenerateImagesConfig`, `GenerateVideosConfig`, `Part`, `Image`, `ImageConfig`,
`ThinkingConfig` — exists on both, with the same call signatures. The differences
are all below the Python surface.

### 3a. `generate_content` — identical, byte for byte ✅

The same source produces the same request bytes on both versions. Image-to-image
with `Part.from_bytes`:

```json
{"contents": [{"parts": [{"inlineData": {"data": "…", "mimeType": "image/png"}},
                         {"text": "Match the reference character."}],
               "role": "user"}],
 "generationConfig": {"responseModalities": ["Text", "Image"]}}
```

Same on 1.61.0 and 2.20.0. Same for the validator's config
(`responseMimeType`, `temperature`, `maxOutputTokens`, `thinkingConfig`). Response
parsing (`response.candidates[0].content.parts[…].inline_data.data`,
`usage_metadata.prompt_token_count` / `.candidates_token_count`,
`finish_reason`) is unchanged.

**This is ~31 of the 35 files, including the entire live pipeline.**

### 3b. `generate_videos` (Veo) — identical request ✅, with a warning ⚠️

```json
{"instances": [{"image": {"bytesBase64Encoded": "…", "mimeType": "image/png"},
                "prompt": "…"}],
 "parameters": {"aspectRatio": "16:9", "durationSeconds": 8, "sampleCount": 1}}
```

Identical on both. But 2.20.0 emits:

> DeprecationWarning: The generate_videos method with prompt/image/video
> arguments is deprecated and will be removed in a future major release (not
> before 2026-07-31). Please use the `source` argument instead.

That removal date has already passed, so `veo_generator.py` is on borrowed time.
It still works on 2.20.0. This is the main reason the pin is exact rather than
`>=2.0.0`.

### 3c. `interactions.create` (Omni) — **the break** ❌

Running the *real* `OmniFlashGenerator.generate()` against a stub transport:

| | `input` array on the wire |
|---|---|
| **1.61.0** | `[{"text": "A dinosaur farts a rainbow.", "type": "text"}]` |
| **2.20.0** | `[{"type": "user_input", "content": [{"type": "text", "text": "A dinosaur farts a rainbow."}]}]` |

The 1.x form is the retired legacy schema. Same source code, different bytes —
this is the split, reproduced offline for $0.

It is worse than a rejected request. The **response model differs too**:

```
1.61.0  Interaction fields: agent created id model outputs previous_interaction_id role status updated usage
2.20.0  Interaction fields: … output_audio output_image output_text output_video … (+17 more)
```

`omni_flash.py` reads `interaction.output_video.data`. That field does not exist
on 1.x, so even a hypothetical 200 would be dropped on the floor. **Omni is
structurally impossible on 1.x** — no amount of request tweaking fixes it.

End-to-end against the stub transport: `generate()` returns a `VideoResult` and
writes the mp4 on 2.20.0; raises `RuntimeError: No video payload in the response`
on 1.61.0.

### 3d. `generate_images` (Imagen) — **the one regression** ❌

On 2.20.0 the method raises before building any request:

```
ValueError: This method is only supported in Gemini Enterprise Agent Platform
mode, not in Gemini Developer API mode.
```

The `_GenerateImagesConfig_to_mldev` / `_GenerateImagesParameters_to_mldev`
converters that exist in 1.61.0's `models.py` are simply gone from 2.20.0.
Google's own deprecation notice on the method says to use `generate_content`
with an image model instead.

Four scripts used it. **All four have been migrated** (§4).

---

## 4. What was changed

### `scripts/genai_compat.py` (new)

One helper, `generate_image(client, prompt, model=…, aspect_ratio=…)`, that does
the Imagen job through `generate_content` and returns `(image_bytes, model_text)`.
It emits a **byte-identical request on 1.61.0 and 2.20.0**:

```json
{"contents": [{"parts": [{"text": "…"}], "role": "user"}],
 "generationConfig": {"imageConfig": {"aspectRatio": "16:9"},
                      "responseModalities": ["Text", "Image"]}}
```

So the migration is safe independently of which SDK is installed — it is not a
bet on the upgrade.

### The four migrated call sites

| Script | Was | Now |
|---|---|---|
| `generate_environment_art.py` | `imagen-4.0-generate-001` | `gemini-2.5-flash-image` |
| `generate_environment_variations.py` | `imagen-4.0-generate-001` | `gemini-2.5-flash-image` |
| `generate_turnaround_sheets.py` | `imagen-4.0-generate-001` | `gemini-2.5-flash-image` |
| `generate_nina_turnaround_v3.py` (fallback) | `imagen-4.0-generate-001` | `gemini-3-pro-image-preview` |

The new models are the ones `CLAUDE.md` already mandates for image generation
("`gemini-2.5-flash-image` (minimum) or `gemini-3-pro-image-preview`
(preferred)"), so this also brings four stragglers onto the project standard.

All four are Feb 2026 one-shot scripts. None is referenced by the orchestrator,
the validator, or any Omni/Veo runner — their outputs are long since approved and
on R2.

### `requirements.txt` (new)

The pin that did not previously exist. `google-genai==2.20.0`, exact.

### `scripts/setup_python_env.sh` (new)

Creates `.venv`, installs `requirements.txt`, asserts the SDK major version, and
runs the offline compatibility suite. This is the replacement for the `/tmp`
venv. `--check` verifies an existing environment without installing.

### `scripts/test_sdk_compat.py` (new)

The regression test that would have caught this in the first place.

The existing suites (`video/test_omni_flash.py`, `video/test_video_generators.py`,
`pipeline/test_*.py`) mock the SDK *client object*, so they pass on 1.61.0 and
2.20.0 alike and are completely blind to the wire-format split. The new suite
stubs `httpx` one layer lower and asserts on the bytes: the `user_input`
envelope, `Interaction.output_video`, the `generate_content` body, the Veo body,
the `generate_images` removal, and an AST scan that fails if anyone reintroduces
`generate_images()` anywhere under `scripts/`.

---

## 5. Test results

All offline. Stubbed transport, fake key, no network.

| Suite | 1.61.0 | 2.20.0 |
|---|---|---|
| `scripts/video/` (57 tests) | 57 passed | 57 passed |
| `scripts/pipeline/` (43 tests) | 43 passed | 43 passed |
| `scripts/test_sdk_compat.py` (9 tests) | **5 failed**, 4 passed | **9 passed** |

The pre-existing suites being version-blind is the point: 100 tests could not
tell the two SDKs apart. The new suite fails on 1.61.0 exactly where the real
API does — `test_sdk_is_2x`, `test_interaction_model_carries_video_output`,
`test_omni_request_uses_user_input_envelope`, `test_omni_writes_the_returned_video`.

Additionally verified against the stub transport, for $0:

- Each of the four migrated call sites runs its real function, hits the right
  model URL, and writes correct bytes to disk.
- All four migrated scripts, and `genai_compat.py`, import cleanly under 2.20.0.
- `pip check` is clean with google-genai 2.20.0 and google-generativeai 0.8.6
  installed side by side.
- `./scripts/setup_python_env.sh` was run end to end from a clean state.

---

## 6. What could NOT be verified without spending

Stated plainly, because these are real gaps:

1. **That any of it generates a good image.** Every check here is structural:
   the client builds the request we expect and parses the response we expect. No
   image, video, or token was actually generated. Request shape ≠ output quality.
2. **That the four migrated scripts produce images comparable to Imagen 4.**
   `gemini-2.5-flash-image` is a different model with a different look. The
   request is correct; the aesthetics are unverified. If anyone re-runs those
   four scripts, treat the first output as a review gate, not a drop-in.
3. **Whether `imagen-4.0-generate-001` still serves requests at all.** 1.61.0
   builds a valid `:predict` request, but Google has deprecated the Imagen
   models on the Developer API. It is entirely possible the path we "preserved"
   on 1.61.0 was already dead. Checking costs money.
4. **That `generate_videos(prompt=…, image=…)` still works server-side.** The
   request bytes are unchanged and 2.20.0 still builds them, but its own
   deprecation window closed on 2026-07-31. The next real Veo run is the test.
5. **Live Omni on 2.20.0 beyond what Phases 0/05/06 already paid for.** Those
   phases did run against the live API on 2.20.0 and worked; nothing new was
   spent here.
6. **Content-filter behaviour.** Unchanged by an SDK bump in principle, but not
   re-probed.

---

## 7. Reasoning

The decision rule in the task was: if the image scripts work on 2.x, bump; if
they break, keep the pin and formalise a separate Omni venv.

They work, with one exception that turned out to be fixable in a
version-independent way:

- **31 of 35 files send byte-identical requests.** Not "probably compatible" —
  the same bytes, diffed. That includes the whole live pipeline: orchestrator,
  shot validator, Veo.
- **The one regression (`generate_images`) affects 4 unreferenced Feb-2026
  one-shot scripts**, on an API surface Google itself has deprecated in favour
  of the exact method we already use everywhere else.
- **The fix for that regression doesn't depend on the upgrade.** `genai_compat`
  emits identical bytes on both SDKs. Migrating those four is an improvement
  whether or not the pin moves — which turns "don't break the image scripts"
  from a constraint in tension with the upgrade into an independent win.
- **The alternative institutionalises the split.** Keeping 1.61.0 and giving
  Omni its own environment means two Python environments forever, a dead SDK
  under the entire image pipeline, and the standing risk that someone runs an
  Omni script in the wrong one and gets a confusing server error. The task was
  explicit that a scratch-directory venv is not a production state; a second
  *documented* venv is only marginally better.
- **The remaining risk is bounded and now has a tripwire.** `test_sdk_compat.py`
  fails loudly on a wrong SDK version instead of surfacing as a runtime API
  error mid-generation.

The pin is **exact** (`==2.20.0`), not `>=2.0.0`, because 2.20.0 already warns
that the `generate_videos` form `veo_generator.py` uses is scheduled for
removal. The next SDK bump should be deliberate and re-verified, not silent.

---

## 8. Follow-ups

1. **Migrate `veo_generator.py` to `generate_videos(source=…)`** before the
   deprecated `prompt=`/`image=` form is removed. Structurally verifiable for $0
   with the same stub-transport technique used here.
2. **Migrate the nine `google.generativeai` scripts to `google-genai`**, then
   drop `google-generativeai` from `requirements.txt`.
3. **First real run of any migrated Imagen script is a review gate** — check the
   `gemini-2.5-flash-image` output against the Asset Bible before trusting it.
4. **Point the task server at `.venv`.** The host's `~/.local` still has
   1.61.0; nothing outside this repo was modified. Anything invoked as a bare
   `python3 scripts/…` will still pick up the old SDK — use
   `.venv/bin/python` or `source .venv/bin/activate`.
