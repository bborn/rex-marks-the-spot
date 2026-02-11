# Trailer Audio Plan

## Music Brief (for Suno AI)

### Track Requirements
- **Duration:** 45 seconds
- **Style:** Upbeat, whimsical, cinematic orchestral with electronic elements
- **Mood progression:**
  - 0-4s: Warm, inviting (piano/strings)
  - 4-8s: Magical swell (shimmer, bells, crescendo)
  - 8-18s: Playful adventure theme (pizzicato strings, light percussion)
  - 18-24s: Dramatic tension build (deeper brass, timpani hit)
  - 24-30s: Techy/futuristic underlay (synth arps, electronic pulse)
  - 30-39s: Building energy, combining orchestral + electronic
  - 39-45s: Resolving finale with big hit on "SUBSCRIBE" beat
- **Tempo:** 120-130 BPM
- **Key:** Major key (C or G major for brightness)
- **Reference tracks:** Pixar short film scores, Lego Movie trailer energy

### Suno Prompt (suggested)
```
Cinematic trailer music, 45 seconds, upbeat whimsical orchestral with electronic elements,
starts warm piano then builds to adventure theme with pizzicato strings and light percussion,
dramatic brass hit at 18 seconds, transitions to synth arps and electronic pulse,
builds to energetic finale, family-friendly Pixar vibes, 125 BPM, C major
```

### Alternate Suno Prompt (simpler)
```
Whimsical cinematic trailer, 45 seconds, orchestral adventure meets electronic,
Pixar-style family movie energy, building excitement, magical shimmer sounds,
upbeat and fun, resolves with a big finish
```

---

## Narration Approach

### Recommended: No narration for v1
- The trailer is visual-first with text overlays
- Music + text carries the storytelling
- Keeps production simpler and avoids uncanny AI voice issues

### Future consideration: AI voice narration
- **Tool:** ElevenLabs or Google Cloud TTS
- **Voice style:** Warm, enthusiastic narrator (think movie trailer voice but friendly)
- **Script would be:** "What happens when a simple date night... becomes a Jurassic adventure? Meet the family behind Fairy Dinosaur Date Night - an animated movie made entirely with AI."
- **Add in v2** once the visual trailer is validated

---

## SFX Plan

| Timestamp | SFX | Source |
|-----------|-----|--------|
| 0-4s | Soft ambience, page turn | Freesound.org |
| 4s | Magical shimmer/sparkle | Suno or Freesound |
| 8-12s | Gentle whoosh (character entries) | Generated |
| 18s | Thunder crack / dramatic hit | Freesound |
| 24s | Digital/tech glitch | Generated |
| 39s | Comedic boing/pop | Freesound |
| 44s | Final impact/button press | Generated |

---

## Timing / Sync Notes

- Music beat drops should align with scene transitions
- The dramatic hit at ~18s syncs with "went VERY wrong" text
- Subscribe button appearance at ~42s should have a distinct musical beat
- Keep 2-3 frames of silence at the very start and end for YouTube processing
- Mix music at -6dB to leave headroom for future narration track

## File Delivery
- Music: WAV 48kHz 16-bit (for Remotion import)
- SFX: Individual WAV files per effect
- Final mix: Done in Remotion composition via `<Audio>` components
