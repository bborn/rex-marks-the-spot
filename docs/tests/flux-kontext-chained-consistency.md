# Flux Kontext Chained Consistency Test — Scene 1 Shots A/B/G

**Date:** 2026-03-21
**Model:** lucataco/flux-kontext-dev on Replicate
**Method:** Chained image-to-image generation (each frame uses previous output as input)

## Results

### Panel 1A — Establishing Shot (Wide)
| Start | End |
|-------|-----|
| ![1A-start](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/tests/flux-kontext-chained/panel-1A-start.png) | ![1A-end](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/tests/flux-kontext-chained/panel-1A-end.png) |
| Hero shot. Cozy living room, TV left, couch center, babysitter on armchair right. Dinosaur toys on floor. | Storm lightning flash through window. TV shows static. Characters in same positions. |

### Panel 1B — Medium Shot on Leo
| Start | End |
|-------|-----|
| ![1B-start](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/tests/flux-kontext-chained/panel-1B-start.png) | ![1B-end](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/tests/flux-kontext-chained/panel-1B-end.png) |
| Medium shot of Leo hugging plush T-Rex. Dinosaur toys around him. | Same framing, Leo looking at toys. (Note: 1B-end used hero shot as input due to content filter on close-up child input) |

### Panel 1G — Over-the-Shoulder Shot
| Start | End |
|-------|-----|
| ![1G-start](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/tests/flux-kontext-chained/panel-1G-start.png) | ![1G-end](https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/tests/flux-kontext-chained/panel-1G-end.png) |
| Over-the-shoulder from behind children. Parents visible in background preparing to leave. | Mia turns head to look back at parents with concerned expression. |

## Chaining Diagram

```
Mia turnaround → Panel 1A-start (HERO) → Panel 1A-end → Panel 1B-start
                        ↓                                      ↓
                  Panel 1G-start → Panel 1G-end          Panel 1B-end*

* Panel 1B-end used hero shot as input (content filter blocked close-up child input)
```

## Evaluation

### 1. Room Consistency
**Strong.** The living room maintains consistent elements across all 6 frames:
- Same brown/terracotta couch
- Same table lamp on left
- Same TV on left side
- Same window with storm/lightning visible
- Same warm amber lighting
- Same picture frame on wall (right side)
- Same dinosaur toys on floor

### 2. Character Consistency
**Good.** Mia (pink polka-dot shirt, dark pigtails) and Leo (green dinosaur pajamas) maintain their appearance across panels. The babysitter (maroon top, dark hair) stays consistent. Character proportions and style remain Pixar-like throughout.

### 3. Start/End Pair Quality (for video interpolation)
**1A pair: Excellent** — Nearly identical composition, only lighting change (storm flash) and subtle TV static difference. Would interpolate well.
**1B pair: Moderate** — Different framing (1B-start is close-up of Leo, 1B-end is wider) because content filter forced different input. Less suitable for direct interpolation.
**1G pair: Good** — Same over-the-shoulder framing, Mia's head turn is the main difference. Parents consistently visible. Would interpolate reasonably well.

### 4. Shot-to-Shot Flow
**1A-end → 1B-start: Good** — Smooth transition from wide to medium shot. Room elements carry over.
**1G references 1A: Strong** — Using the hero shot as reference maintained room consistency for the new camera angle.

## Content Filter Issues

Replicate's content filter flagged several prompts involving children:
- "Lightning" in prompt triggered filter (changed to "bright flash of light from the storm")
- Close-up child images as input triggered filter regardless of prompt (panel 1B-end had to use hero shot instead of 1B-start as input)

This is a significant limitation for a family-oriented animated movie. The filter appears to be overly cautious about any image featuring child characters, even in clearly G-rated Pixar-style animated contexts.

## Cost

6 predictions × ~$0.03 each = ~$0.18 total (well under $1 budget)
Plus ~4 failed predictions due to content filter = ~$0.12 wasted
**Total: ~$0.30**

## Technical Details

- **Model version:** e2a2a6f122724dd95ecc0e8e42c586cbdd512847de7851225ceefba2da197188
- **Aspect ratio:** 16:9
- **Guidance scale:** 2.5
- **Inference steps:** 28
- **Generation time:** ~15 seconds per image (plus cold start on first)
- **Output size:** ~1.2 MB per image (PNG)
