# Audio Pipeline Research: Voice, Music & Sound Effects

**Research Date:** February 2026
**Status:** Ready for Director Review

---

## Executive Summary

This document outlines research findings and recommendations for the complete audio pipeline for "Fairy Dinosaur Date Night" including AI voice generation, music composition, sound effects, and lip sync integration with Blender.

### Recommended Stack

| Component | Primary Tool | Backup/Alternative | Est. Monthly Cost |
|-----------|--------------|-------------------|-------------------|
| **Voice Generation** | ElevenLabs (Pro) | Fish Audio | $99/mo |
| **Music Composition** | AIVA (Pro) | Beatoven.ai | €49/mo (~$53) |
| **Sound Effects** | Adobe Firefly + Freesound | ElevenLabs SFX | ~$23/mo (CC subscription) |
| **Lip Sync** | Rhubarb Lip Sync + Blender addon | Parrot Lipsync | Free |

**Estimated Total:** ~$175/month during production

---

## 1. AI Voice Generation

### Top Contenders Evaluated

#### **ElevenLabs** ⭐ Recommended
- **Quality:** Industry-leading realism and emotional depth
- **Voice Cloning:** Instant cloning on Starter+, Professional Voice Cloning on Creator+
- **Languages:** 29+ languages supported
- **Pricing:**
  - Free: 20 mins/month (non-commercial)
  - Starter: $5/mo (30 mins, 3 custom voices)
  - Creator: $22/mo (100 mins, 10 custom voices)
  - **Pro: $99/mo (500 mins, 30 custom voices)** ← Recommended
  - Scale: $330/mo (2000 mins, 160 custom voices)
- **Commercial License:** Yes, on paid plans
- **Pros:** Best quality, extensive customization, good API
- **Cons:** Most expensive option

#### **Fish Audio (Open Audio S1)**
- **Quality:** #1 ranked on TTS-Arena leaderboard (surpassed ElevenLabs in blind tests)
- **Pricing:** $9.99/mo for 200 mins OR $15 per 1M characters
- **Pros:** Exceptional quality at fraction of ElevenLabs cost
- **Cons:** Newer platform, smaller community

#### **Chatterbox (by Resemble AI)**
- **Quality:** 63.8% preferred over ElevenLabs in blind tests
- **Pricing:** 100% FREE (MIT License)
- **Pros:** Free, open-source, commercial-ready
- **Cons:** Requires 8GB+ VRAM to run locally, self-hosted

#### **Resemble AI**
- **Quality:** Enterprise-grade, real-time speech-to-speech
- **Best For:** Large-scale deployments, on-premise needs
- **Pricing:** Custom enterprise pricing

### Voice Cloning for Characters

For our 5 main characters (Gabe, Nina, Mia, Leo, Ruben + Jetplane), we need distinct voices:

| Character | Voice Profile Recommendation |
|-----------|------------------------------|
| **Gabe** (dad) | Warm baritone, reassuring |
| **Nina** (mom) | Confident alto, nurturing |
| **Mia** (girl, ~8-10) | Bright, curious child voice |
| **Leo** (boy, ~6-8) | Energetic, slightly younger |
| **Ruben** (fairy godfather) | Theatrical, magical quality |
| **Jetplane** (dinosaur) | Playful growls/vocalizations with personality |

**Recommendation:** Use ElevenLabs Pro ($99/mo) which provides:
- 500 minutes/month (ample for dialogue recording)
- 30 custom voices (enough for all characters + variations)
- Professional Voice Cloning for creating unique character voices

---

## 2. Music & Score

### AI Composition Tools Evaluated

#### **AIVA** ⭐ Recommended for Film Score
- **Specialization:** Emotional soundtracks for films, documentaries, trailers
- **Pricing:**
  - Free: 3 downloads/mo, non-commercial, credit required
  - Standard: €15/mo (15 downloads, YouTube/TikTok monetization)
  - **Pro: €49/mo (300 downloads, FULL COPYRIGHT OWNERSHIP)** ← Recommended
- **Key Feature:** Pro plan = you own full copyright, no restrictions, no credit required
- **Output:** MP3, WAV, MIDI (can edit in DAW)
- **Genres:** Classical, cinematic, ambient, electronic

#### **Suno**
- **Quality:** Excellent for full songs with vocals
- **Recent News:** $500M settlement with Warner Music Group (Nov 2025)
- **Licensing Concerns:**
  - Free plan: Suno owns the output, NOT commercial
  - Pro plan: You can download but "may not be eligible for copyright protection"
- **Best For:** Ideation, demos (not final production)

#### **Udio**
- **Recent News:** Pivoted to "fan engagement platform" after UMG settlement
- **Current State:** "Walled garden" - creations cannot leave the platform
- **Verdict:** Not suitable for film production

#### **Beatoven.ai**
- **Unique Feature:** "Fairly Trained License" certification - ethically sourced training data
- **Pricing:** Subscription-based, commercial-safe
- **Best For:** Background music, content creators

#### **ElevenLabs Eleven Music** (New - Aug 2025)
- **Unique Feature:** First AI music generator cleared for YouTube monetization
- **Licensing:** Partnerships with Merlin Network & Kobalt = no copyright concerns
- **Best For:** Commercial projects needing bulletproof licensing

### Music Strategy Recommendation

1. **Score/Underscore:** Use AIVA Pro (€49/mo) for cinematic background music
   - Full copyright ownership on Pro plan
   - Export MIDI for further refinement in DAW if needed

2. **Special Musical Moments:** Consider Beatoven.ai or ElevenLabs Eleven Music for songs that need clearer provenance

3. **Legal Safety:** Avoid Suno/Udio for final production due to uncertain copyright status

---

## 3. Sound Effects

### AI-Generated SFX Tools

#### **Adobe Firefly** ⭐ Recommended
- **Integration:** Part of Creative Cloud
- **Features:** Text-to-audio, audio-to-audio, audio inpainting
- **Licensing:** Royalty-free for commercial use
- **Controls:** Use voice/audio recordings to guide timing and loudness
- **Cost:** Included with Creative Cloud subscription (~$23/mo for single app)

#### **ElevenLabs SFX Generator**
- **Quality:** Hyper-realistic effects
- **Cost:** Included in ElevenLabs subscription
- **Best For:** Foley, ambient sounds, custom effects

#### **Stability AI (Stable Audio 2.5)**
- **Features:** Enterprise-grade, multi-modal workflows
- **Best For:** Large-scale production, brand audio

#### **Free Options:**
- **SFX Engine:** Free AI generator, commercial license included
- **Lami.ai:** Free, no credit card, runs online
- **MyEdit:** Free AI sound effect generator

### Traditional SFX Libraries

#### **Freesound** (Free)
- 685,000+ sounds
- Mixed licensing (CC0, CC-BY, CC-BY-NC)
- **Important:** Check license per sound - some require attribution, some non-commercial only

#### **Soundsnap** (Subscription)
- Professional quality
- Subscription model for unlimited downloads
- Clear commercial licensing

#### **BBC Sound Effects** (Free, Limited)
- 16,000+ recordings
- **Limitation:** NOT cleared for commercial use by professionals

#### **BOOM Library** (Premium)
- Industry standard for high-end cinematic sounds
- Pay-per-pack or subscription

### SFX Strategy Recommendation

1. **Primary:** Adobe Firefly for custom AI-generated effects (especially magical/fantasy sounds for Jetplane)
2. **Secondary:** Freesound (CC0/CC-BY only) for standard foley
3. **Premium:** Consider BOOM Library packs for cinematic impacts if budget allows
4. **Dinosaur Sounds:** Custom AI generation via ElevenLabs or Firefly for Jetplane's unique vocalizations

---

## 4. Lip Sync Integration with Blender

### Available Tools

#### **Rhubarb Lip Sync** ⭐ Recommended
- **Type:** Command-line tool + Blender addon
- **How It Works:** Analyzes audio → generates mouth-shape keyframes from pose library
- **Cost:** FREE (open source)
- **GitHub:** [scaredyfish/blender-rhubarb-lipsync](https://github.com/scaredyfish/blender-rhubarb-lipsync)
- **Pros:** Battle-tested, reliable, integrates cleanly with Blender

#### **Parrot Lipsync**
- **Features:** 2D and 3D animation support, multi-language
- **Technology:** Uses Allosaurus library for phoneme detection
- **Cost:** FREE (open source)
- **GitHub:** [blackears/parrotLipsync](https://github.com/blackears/parrotLipsync)

#### **Lip Sync (iocgpoly)**
- **Features:** 25+ languages, uses Vosk + eSpeak NG
- **Location:** Blender Extensions marketplace
- **Cost:** Available on Blender Extensions

#### **Blender Lip Sync v2.3.2**
- **Released:** July 2025
- **Features:** Automatic lip-syncing from audio

### Recommended Workflow

1. **Record dialogue** using ElevenLabs
2. **Export audio** as WAV files (per character, per line)
3. **Run Rhubarb Lip Sync** on audio files
4. **Import keyframes** into Blender using the addon
5. **Manual refinement:** Adjust timing, exaggerate key phrases, add expressions

**Pro Tip:** AI lip sync provides 80% of the work. Budget time for manual polish on emotional moments.

---

## 5. Recommended Workflow

### Pre-Production
1. Generate character voice samples with ElevenLabs
2. Get director approval on voice casting
3. Set up AIVA project for score development

### Production (Per Scene)
```
1. DIALOGUE
   ├── Export script lines per character
   ├── Generate audio via ElevenLabs API
   ├── Review and regenerate as needed
   └── Export final WAV files

2. LIP SYNC
   ├── Run Rhubarb on dialogue audio
   ├── Import phoneme data to Blender
   ├── Auto-generate keyframes
   └── Manual polish pass

3. MUSIC
   ├── Describe mood/scene to AIVA
   ├── Generate variations
   ├── Select and customize
   └── Export stems if needed

4. SFX
   ├── Identify needed effects per scene
   ├── Generate custom via Adobe Firefly
   ├── Pull from Freesound (CC0) as needed
   └── Layer and mix
```

### Post-Production
1. Final audio mix (consider: DaVinci Resolve, Audacity, or professional DAW)
2. Sync verification
3. Export final mix

---

## 6. Budget Summary

### Monthly Costs During Production

| Tool | Plan | Cost |
|------|------|------|
| ElevenLabs | Pro | $99/mo |
| AIVA | Pro | €49/mo (~$53) |
| Adobe Creative Cloud | Single App | ~$23/mo |
| Rhubarb Lip Sync | Open Source | Free |
| Freesound | Free tier | Free |

**Estimated Monthly Total:** ~$175/month

### One-Time Costs (Optional)
- BOOM Library sound packs: $50-200 per pack
- Professional mixing services: Variable

### Cost Optimization Options
- **Budget Tier:** Fish Audio ($10/mo) + AIVA Standard (€15/mo) + Free tools = ~$40/mo
- **Free Tier:** Chatterbox (self-hosted) + AIVA Free + Freesound = $0 (requires technical setup)

---

## 7. Legal & Licensing Considerations

### Voice Generation
- **ElevenLabs:** Commercial use allowed on paid plans; cannot clone real people without consent
- **Fish Audio:** Check terms for commercial use
- **Chatterbox:** MIT license = full commercial freedom

### Music
- **AIVA Pro:** Full copyright ownership - safest option
- **Suno/Udio:** Copyright status uncertain - avoid for final production
- **Beatoven.ai:** "Fairly Trained" certification provides ethical assurance

### Sound Effects
- **Freesound:** MUST check license per sound
  - CC0: No restrictions
  - CC-BY: Attribution required
  - CC-BY-NC: Non-commercial only (DO NOT USE for this film)
- **Adobe Firefly:** Royalty-free commercial use
- **ElevenLabs SFX:** Commercial use on paid plans

### Recommendations
1. Document all audio sources and licenses
2. Use CC0 or commercially-licensed content only
3. Keep receipts/records for all paid services
4. When in doubt, generate custom AI audio rather than using unclear-license sources

---

## 8. Next Steps

### Immediate Actions
1. [ ] Sign up for ElevenLabs Pro trial to test voice generation
2. [ ] Create voice samples for each main character
3. [ ] Test AIVA with sample scene descriptions
4. [ ] Install Rhubarb Lip Sync Blender addon
5. [ ] Test lip sync pipeline with sample dialogue

### Director Review Questions
1. Approve voice casting approach (AI-generated custom voices)?
2. Budget approval for recommended tool stack (~$175/mo)?
3. Priority: Start with a pilot scene to validate full pipeline?

---

## References

### Voice Generation
- [ElevenLabs Pricing](https://elevenlabs.io/pricing)
- [Fish Audio](https://fish.audio/)
- [Chatterbox on GitHub](https://github.com/resemble-ai/chatterbox)

### Music
- [AIVA](https://www.aiva.ai/)
- [Beatoven.ai](https://www.beatoven.ai/)
- [Suno/Udio Licensing Updates - Billboard](https://www.billboard.com/pro/what-suno-udio-licensing-deals-mean-future-ai-music/)

### Sound Effects
- [Adobe Firefly Audio](https://www.adobe.com/products/firefly/features/sound-effect-generator.html)
- [Freesound](https://freesound.org/)
- [ElevenLabs Sound Effects](https://elevenlabs.io/sound-effects)

### Lip Sync
- [Rhubarb Lip Sync for Blender](https://github.com/scaredyfish/blender-rhubarb-lipsync)
- [Parrot Lipsync](https://github.com/blackears/parrotLipsync)
- [Blender Lip Sync Extension](https://extensions.blender.org/add-ons/iocgpoly-lip-sync/)
