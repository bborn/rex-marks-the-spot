# AI Voice Generation Research for Character Voices

**Date:** February 2026
**Purpose:** Find the best pipeline for creating consistent, high-quality character voices for "Fairy Dinosaur Date Night"

## Current Status

**We already have a working ElevenLabs integration** with the `ELEVENLABS_API_KEY` configured. Sample voice files have been generated for all 5 main characters (25 total samples in `audio/voices/`).

---

## Tools Evaluated

### 1. ElevenLabs ⭐ RECOMMENDED (Currently Integrated)
**Website:** https://elevenlabs.io

| Aspect | Details |
|--------|---------|
| **Quality** | Industry standard, "scarily human" |
| **Voice Cloning** | Instant (1 min audio) + Professional (with consent) |
| **Languages** | 70+ languages supported |
| **API** | Full API with Python SDK |
| **Cost** | Free: 10k chars/mo, Creator: $22/mo (100k chars), Pro: $99/mo (500k chars) |
| **Model** | eleven_multilingual_v2, v3 for emotional control |

**Pros:**
- Best audio fidelity in the market
- Voice Design feature creates new voices from text prompts
- Sound effects generation built-in
- We already have it integrated and working
- Voices "breathe, pause, and intonate just like real people"
- Community voice library with cartoon/animation voices

**Cons:**
- Credit-based pricing can get expensive for full movie
- ~1 credit = 2 characters
- Professional voice cloning requires consent verification

**BEST FOR:** High-quality production audio, our primary tool

---

### 2. Fish Audio ⭐ STRONG ALTERNATIVE
**Website:** https://fish.audio

| Aspect | Details |
|--------|---------|
| **Quality** | Excellent, especially for character voices |
| **Voice Cloning** | Just 10 seconds of audio required |
| **Languages** | 8 languages (strong Chinese) |
| **API** | Pay-as-you-go API access |
| **Cost** | Plus: $11/mo, Pro: $75/mo |
| **Model** | F-Series (free cloning), M-Series (emotional) |

**Pros:**
- Requires only 10 seconds for cloning (vs 1 min for ElevenLabs)
- Popular for anime/character voices and gaming
- More generous free tier
- Emotion control via tag-based markup
- Good value for budget-conscious projects

**Cons:**
- Fewer languages than ElevenLabs
- Less established platform
- May need more tuning for English performance

**BEST FOR:** Anime/character voices, rapid prototyping, budget projects

---

### 3. Murf AI
**Website:** https://murf.ai

| Aspect | Details |
|--------|---------|
| **Quality** | Good, user-friendly |
| **Voice Cloning** | AI voice changer (Pro+) |
| **Languages** | 20+ languages, 200+ voices |
| **API** | Available |
| **Cost** | Free: 10 min, Basic: $19/mo, Pro: $26/mo, Enterprise: $75/mo |
| **Model** | Gen2 model |

**Pros:**
- Most user-friendly interface
- Animation sync support built-in
- Can sync voiceover with animations/transitions
- Great for presentations/explainers
- 8000+ licensed soundtracks included

**Cons:**
- Voice cloning less advanced than ElevenLabs
- Not as natural for character dialogue
- More suited for narration than acting

**BEST FOR:** Presentations, narration, beginners

---

### 4. Resemble AI
**Website:** https://www.resemble.ai

| Aspect | Details |
|--------|---------|
| **Quality** | Good for real-time applications |
| **Voice Cloning** | Rapid (10-15 sec) + Professional (10 min) |
| **Languages** | 150+ languages |
| **API** | Most flexible API for developers |
| **Cost** | Creator: $30/mo, Professional: $60/mo, Pay-as-you-go: $0.018/min |

**Pros:**
- Excellent real-time API for games
- Good for interactive/conversational AI
- Emotional nuance capture in professional clones
- Deepfake detection built-in

**Cons:**
- Less natural than ElevenLabs for pre-recorded content
- Better suited for real-time than offline rendering
- Requires more audio for best quality clones

**BEST FOR:** Games, interactive characters, real-time agents

---

### 5. PlayHT ⚠️ NOT RECOMMENDED
**Website:** https://play.ht

| Aspect | Details |
|--------|---------|
| **Status** | **SHUTTING DOWN December 2025** |
| **Quality** | Was above average |
| **Languages** | 800+ voices, 142 languages |
| **Cost** | Was $31-$99/mo |

**Why Not:**
- Platform shutting down - users must export data before deadline
- Inconsistent service reliability
- Questionable billing practices reported
- No long-term viability

**DO NOT USE** for any new projects

---

## Comparison Matrix

| Tool | Quality | Character Voices | Voice Cloning | API | Cost/mo | Recommendation |
|------|---------|-----------------|---------------|-----|---------|----------------|
| **ElevenLabs** | Excellent | Excellent | 1 min | Yes | $22-99 | **PRIMARY** |
| **Fish Audio** | Good | Excellent | 10 sec | Yes | $11-75 | **BACKUP** |
| **Murf AI** | Good | Good | Limited | Yes | $19-75 | Narration only |
| **Resemble AI** | Good | Good | 10 sec | Best | $30-60 | Games/realtime |
| **PlayHT** | N/A | N/A | N/A | N/A | N/A | **SHUTDOWN** |

---

## Our Current Integration

### ElevenLabs Setup (Working)

**Script:** `scripts/generate_voices.py`

**Character Voice Mapping:**
| Character | Voice ID | Voice Name | Settings |
|-----------|----------|------------|----------|
| Gabe | pNInz6obpgDQGcFmaJgB | Adam | Deep, authoritative dad |
| Nina | EXAVITQu4vr4xnSDxMaL | Sarah | Warm, intelligent mom |
| Mia | cgSgspJ2msm6clMCkdW9 | Jessica | Playful 8-year-old |
| Leo | N2lVS1w4EtoT3dr4eOWO | Callum | Energetic 5-year-old |
| Ruben | onwK4e9ZLuTAKqWW03F9 | Daniel | World-weary fairy |

**Generated Samples:** 25 files in `audio/voices/` (5 per character)

**Usage:**
```bash
# Generate all character voices
ELEVENLABS_API_KEY=your-key python scripts/generate_voices.py

# Generate single character
python scripts/generate_voices.py gabe

# List available voices
python scripts/generate_voices.py --list-voices
```

---

## Recommendations for Production

### Phase 1: Current (Voice Testing)
- Continue using **ElevenLabs** with pre-made voices
- Adjust voice settings (stability, similarity_boost, style) per character
- Test with more dialogue from screenplay

### Phase 2: Voice Refinement
- Consider **Professional Voice Cloning** for hero characters if needed
- May clone Bruno/team voices for custom characters
- Requires Creator plan ($22/mo) minimum

### Phase 3: Full Production
- Estimate total character count (all dialogue)
- Calculate credit requirements:
  - ~1 credit = 2 characters
  - Average screenplay ~100k characters
  - Estimated cost: $50-200 for full movie audio

### Alternative: Hybrid Approach
- Use **ElevenLabs** for main characters (Mia, Leo, Ruben, Jetplane)
- Use **Fish Audio** for background/minor characters (cheaper)
- Use **Murf** for any narration/documentary segments

---

## Voice Consistency Tips

For character voice consistency across scenes:

1. **Keep same voice_id** for each character
2. **Lock voice settings** (stability, similarity_boost, style)
3. **Use consistent model** (eleven_multilingual_v2 recommended)
4. **Batch similar emotional scenes** together
5. **Save character profiles** in config (already done in our script)

---

## Cost Analysis (Full Movie)

Assuming ~15 minute animated short with dialogue:

| Plan | Credits/mo | Est. Coverage | Monthly Cost |
|------|-----------|---------------|--------------|
| Free | 10,000 | ~5k characters | $0 |
| Starter | 30,000 | ~15k characters | $5 |
| Creator | 100,000 | ~50k characters | $22 |
| Pro | 500,000 | ~250k characters | $99 |

**Recommendation:** Start with **Creator plan** ($22/mo) for full production.

---

## Missing: Jetplane's Voice

Note: We don't have a voice configured for **Jetplane** (the dinosaur). Options:

1. **Non-verbal sounds** - Roars, chirps, farting sounds (sound effects)
2. **Baby/creature voice** - Search ElevenLabs library for creature voices
3. **Sound effects only** - Use ElevenLabs sound effects API

Jetplane is described as a "color-farting dinosaur" who likely communicates through sounds rather than speech.

---

## Action Items

- [x] ElevenLabs integration working
- [x] Character voice mapping defined
- [x] Sample voices generated
- [ ] Test with full screenplay scenes
- [ ] Decide on Jetplane's audio approach
- [ ] Generate Act 1 dialogue audio
- [ ] Consider custom voice cloning if needed

---

## References

- [ElevenLabs Pricing](https://elevenlabs.io/pricing)
- [ElevenLabs Voice Cloning](https://elevenlabs.io/voice-cloning)
- [ElevenLabs Animation Voices](https://elevenlabs.io/voice-library/animation)
- [Fish Audio](https://fish.audio/)
- [Murf AI](https://murf.ai/)
- [Resemble AI](https://www.resemble.ai/)
- [Curious Refuge: Best AI Voice Generator 2026](https://curiousrefuge.com/blog/best-ai-voice-generator-for-2026)
