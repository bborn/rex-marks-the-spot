# Character Animation Test Report

**Date:** 2026-02-25
**Pod:** L40S (48GB VRAM), RunPod Community Cloud ($0.79/hr)
**ComfyUI:** v0.15.0 with PyTorch 2.6.0+cu124

## Summary

8 tests run, 6 produced actual videos (33 frames each), 2 produced single images (TI2I mode).
All outputs uploaded to R2 at `comfyui-tests/character-tests/`.

## Test Results

### Video Generation Tests (33 frames, ~2 seconds each)

| # | Test | Model | Resolution | Time | Size | R2 URL |
|---|------|-------|-----------|------|------|--------|
| 1 | Mia jungle walk (prompt) | Wan 2.1 T2V 1.3B | 480x320 | 18s | 119KB | [link](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/character-tests/mia_wan_t2v_mia_wan_t2v_00001.mp4) |
| 2 | Mia jungle walk (prompt) | Capybara v01 T2V | 848x480 | 224s | 236KB | [link](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/character-tests/mia_capybara_t2v_mia_capybara_t2v_00001.mp4) |
| 3 | Mia animation (from turnaround) | Capybara v01 TV2V | 848x480 | 143s | 393KB | [link](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/character-tests/mia_capybara_tv2v_mia_capybara_tv2v_00001.mp4) |
| 4 | Gabe & Nina date night (prompt) | Wan 2.1 T2V 1.3B | 480x320 | 12s | 114KB | [link](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/character-tests/gabe_nina_wan_t2v_gabe_nina_wan_t2v_00001.mp4) |
| 5 | Gabe & Nina date night (prompt) | Capybara v01 T2V | 848x480 | 207s | 280KB | [link](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/character-tests/gabe_nina_capybara_t2v_gabe_nina_capybara_t2v_00001.mp4) |
| 6 | Storyboard panel animation | Capybara v01 TV2V | 848x480 | 143s | 111KB | [link](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/character-tests/storyboard_capybara_tv2v_storyboard_capybara_tv2v_00001.mp4) |

### Image-only Tests (TI2I mode = single frame)

| # | Test | Model | Resolution | Time | Note |
|---|------|-------|-----------|------|------|
| 7 | Mia from turnaround | Capybara TI2I | 640x640 | 45s | Single frame, not video |
| 8 | Storyboard stylize | Capybara TI2I | 848x480 | 39s | Single frame, not video |

## Quality Assessment

### Wan 2.1 T2V (1.3B model)
- **Speed:** Excellent (12-18s per clip)
- **Resolution:** Low (480x320)
- **Motion quality:** Basic but coherent movement
- **Character fidelity:** Generic - no character reference, relies on text prompt only
- **Style:** Somewhat cartoon-like but not consistently Pixar quality
- **Best for:** Quick prototyping, motion tests, storyboard previews

### Capybara T2V
- **Speed:** Slow (3-4 minutes first run, includes model loading)
- **Resolution:** Good (848x480)
- **Motion quality:** Smooth, natural movement
- **Character fidelity:** Generic from text prompt alone
- **Style:** Higher quality, more consistent style
- **Best for:** Final-quality text-to-video generation

### Capybara TV2V (video-to-video)
- **Speed:** ~2.5 minutes per clip
- **Resolution:** Good (848x480)
- **Character fidelity:** Uses actual character turnaround as reference (best character match!)
- **Style transformation:** Can convert reference image into animated video while preserving character design
- **Best for:** Animating existing character art or storyboard panels

### Capybara TI2I (image-to-image)
- **Note:** Produces single frames, NOT video. Useful for style transfer on single images.
- **Not suitable** for animation - use TV2V instead.

## Comparison vs Higgsfield

| Feature | RunPod/ComfyUI | Higgsfield |
|---------|---------------|------------|
| Character reference | TV2V preserves design | Direct character reference |
| Speed | 12s-4min depending on model | ~30s typically |
| Resolution | 480x320 (Wan) / 848x480 (Capybara) | Up to 1080p |
| Duration | ~2s (33 frames @ 16fps) | 4-8s typical |
| Cost | $0.79/hr pod + usage time | Per-generation pricing |
| Flexibility | Full workflow customization | Limited to presets |
| IP-Adapter | Available but not for video models | Built-in character ref |

### Key Differences
- **Higgsfield** has simpler workflow and built-in character reference support
- **RunPod/ComfyUI** offers more control, ability to chain workflows, and use IP-Adapter/ControlNet
- **Capybara TV2V** is the best approach for character-referenced video on ComfyUI
- **Wan I2V model** (14B) would enable direct image-to-video but needs ~30GB download

## Recommendations

1. **For quick tests:** Use Wan T2V 1.3B (12-18s, good enough for motion tests)
2. **For character animation:** Use Capybara TV2V with turnaround sheet as input video
3. **For storyboard animation:** Use Capybara TV2V with storyboard panels as input
4. **For higher quality:** Download Wan I2V 14B model for native image-to-video
5. **Production pipeline:** Blender render -> Capybara TV2V for style transfer

## Pod Setup Notes

After restarting the pod, PyTorch needs to be 2.6+ and several packages need to be compatible:
- `torch==2.6.0+cu124` (required for `torch.int1` used by diffusers/transformers)
- `torchao>=0.8` (compatible with torch 2.6)
- `transformers>=4.50` (supports `qwen2_5_vl` architecture needed by Capybara)
- `diffusers>=0.33.0` (Capybara and WanVideoWrapper compatible)

ComfyUI must be started manually after pod restart:
```bash
cd /workspace/ComfyUI && python main.py --listen 0.0.0.0 --port 8188
```

## Files Generated

All outputs at: `https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/comfyui-tests/character-tests/`
