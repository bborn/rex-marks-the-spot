# AI Image Generation Models for Storyboard Production

**Research Date:** February 2026
**Project:** Fairy Dinosaur Date Night
**Status:** Ready for Director Review

---

## Executive Summary

This document provides comprehensive research on AI image generation models for creating storyboard frames for "Fairy Dinosaur Date Night." The focus is on style consistency, character fidelity, API accessibility, and cost-effectiveness for producing hundreds of storyboard panels across three acts.

### Key Recommendations

| Use Case | Recommended Model | Why |
|----------|------------------|-----|
| **Primary Storyboards** | Gemini 2.0 Flash (Imagen 3) | Best style consistency, native conversation context, free tier generous |
| **High-Detail Hero Frames** | Midjourney v6.1 | Superior composition and cinematic quality |
| **Rapid Iteration** | Flux Schnell | Fastest generation, good for exploring variations |
| **Backup/Alternative** | DALL-E 3 | Excellent prompt adherence, good text rendering |
| **Sketch Style Boards** | Flux Dev + LoRA | Best for rough pencil/sketch aesthetic |

**Estimated Image Budget:** $0-50/month using Gemini free tier + selective Midjourney for hero frames

---

## 1. Model Comparison Matrix

### Overall Ratings for Storyboard Production

| Model | Style Consistency | Character Fidelity | Speed | API Access | Cost | Overall |
|-------|------------------|-------------------|-------|------------|------|---------|
| **Gemini 2.0 Flash** | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★★★ | ★★★★★ | **Best Overall** |
| **Imagen 3** | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★★☆ | ★★★★☆ | Excellent |
| **Midjourney v6.1** | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★☆☆☆ | ★★★☆☆ | Best Quality |
| **DALL-E 3** | ★★★★☆ | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★☆☆ | Most Accessible |
| **Flux Pro 1.1** | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ★★★★★ | ★★★☆☆ | Best Open Weights |
| **Flux Schnell** | ★★★☆☆ | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★★ | Fastest |

---

## 2. Detailed Model Analysis

### Gemini 2.0 Flash (with Imagen 3)

Google's multimodal model with native image generation capabilities.

| Feature | Details |
|---------|---------|
| **Strengths** | Conversational context retention, style consistency across sessions, understands complex scene descriptions |
| **Image Quality** | High - photorealistic to stylized, excellent lighting |
| **Character Consistency** | Very good with detailed character descriptions in system prompt |
| **Speed** | Fast - typically 3-8 seconds per image |
| **API Access** | Google AI Studio, Vertex AI |
| **Pricing** | Free tier: 60 requests/minute; Pay-as-you-go: $0.0025 per image |

**Why Best for Storyboards:**
- Maintains conversation context - can reference "the same character from panel 3"
- Understands cinematographic language (shot types, camera angles, lighting)
- Can iterate on frames: "make Mia look more scared" without re-describing everything
- Native text understanding reduces prompt engineering overhead

**Optimal Prompting Strategy:**
```
System: You are generating storyboard frames for "Fairy Dinosaur Date Night,"
a Pixar-style animated family adventure film.

Character Reference:
- Mia: 10-year-old girl, curly red hair, freckles, green eyes, adventurous
- Leo: 7-year-old boy, straight brown hair, blue eyes, curious
- Jetplane: Baby T-Rex with iridescent scales, oversized eyes, stubby arms
- Ruben: Small fairy godfather, butterfly wings, purple suit, silver hair

Style: Warm, expressive Pixar-style animation. Rich colors, dynamic poses,
cinematic composition. Sketch/storyboard aesthetic with visible linework.
```

---

### Imagen 3 (Standalone)

Google's dedicated image generation model, accessible via Vertex AI.

| Feature | Details |
|---------|---------|
| **Strengths** | Highest photorealism, excellent prompt adherence, superior text rendering |
| **Image Quality** | Industry-leading - often indistinguishable from photography |
| **Character Consistency** | Excellent with reference images or detailed descriptions |
| **Speed** | Medium - 5-15 seconds depending on complexity |
| **API Access** | Vertex AI, Google AI Studio |
| **Pricing** | $0.02-0.04 per image depending on resolution |

**Best For:**
- Final presentation storyboards requiring polish
- Marketing materials and pitch decks
- Scenes requiring photorealistic elements (environments, props)

**Limitations:**
- Standalone mode lacks conversational context
- Higher cost for large-scale production
- May be overkill for rough storyboard sketches

---

### Midjourney v6.1

The industry standard for artistic quality and composition.

| Feature | Details |
|---------|---------|
| **Strengths** | Unmatched artistic composition, cinematic lighting, emotional depth |
| **Image Quality** | Best-in-class for stylized/artistic output |
| **Character Consistency** | Good with character reference feature (--cref) |
| **Speed** | Slow - 30-90 seconds per image |
| **API Access** | Discord only (no official API), third-party wrappers exist |
| **Pricing** | $10/mo (Basic), $30/mo (Standard), $60/mo (Pro) |

**Why Consider Despite Limitations:**
- "Hero frame" quality unmatched - perfect for key emotional beats
- --sref (style reference) maintains visual consistency across panels
- --cref (character reference) helps with character continuity
- Community and ecosystem for animation/film styles

**Workflow Integration:**
```
/imagine prompt: Storyboard frame, Pixar animation style.
Mia (10yo, curly red hair, freckles) looks up in wonder at towering
dinosaurs in misty jungle. Golden hour lighting, wide shot,
cinematic composition --ar 16:9 --style raw --sref [style_reference_url]
```

**Limitations:**
- No official API - requires Discord automation or third-party services
- Slower iteration cycle
- Monthly subscription regardless of usage
- Less precise prompt adherence than DALL-E 3 or Imagen 3

---

### DALL-E 3 (via OpenAI)

OpenAI's latest image model, known for prompt fidelity and text rendering.

| Feature | Details |
|---------|---------|
| **Strengths** | Exceptional prompt adherence, best text-in-image, safety guardrails |
| **Image Quality** | High - clean, polished output |
| **Character Consistency** | Good with detailed descriptions, can struggle with complex poses |
| **Speed** | Fast - 5-10 seconds |
| **API Access** | OpenAI API, ChatGPT Plus |
| **Pricing** | $0.04-0.08 per image (1024x1024 to 1792x1024) |

**Best For:**
- Panels requiring text elements (signs, notes, speech bubbles)
- Precise scene composition matching written descriptions
- Integration with existing OpenAI workflows

**Prompting Notes:**
- DALL-E 3 rewrites prompts internally - be explicit about what NOT to change
- Include "exact prompt adherence" for literal interpretation
- Works well with ChatGPT for iterative refinement

**Sample Prompt:**
```
Create a storyboard frame in Pixar animation style showing:
Scene: Interior of a glowing minivan cockpit at night
Characters: Leo (7yo boy, brown hair) gripping the dashboard nervously
Mood: Tension mixed with wonder, blue and purple magical lighting
Composition: Medium close-up, slight low angle
Style: Clean animation cel-shading, visible but subtle outlines
```

---

### Flux (Black Forest Labs)

Open-weights model family with excellent quality and flexibility.

| Feature | Details |
|---------|---------|
| **Models** | Flux Pro 1.1, Flux Dev, Flux Schnell |
| **Strengths** | Open weights, LoRA support, fast iteration, good anatomy |
| **Image Quality** | Very good - approaching Midjourney for stylized content |
| **Character Consistency** | Good base, excellent with custom LoRAs |
| **Speed** | Schnell: 1-2 sec, Dev: 5-10 sec, Pro: 10-20 sec |
| **API Access** | Replicate, fal.ai, Together AI, self-hosted |
| **Pricing** | Schnell: ~$0.003/image, Dev: ~$0.025/image, Pro: ~$0.055/image |

**Why Flux for Storyboards:**
- **Schnell** for rapid exploration (nearly free, instant)
- **Dev** for production frames (best quality/cost ratio)
- **LoRA training** possible for character consistency
- Self-hosting option for unlimited generation

**Recommended Workflow:**
1. Use Schnell for quick concept exploration (10-20 variations)
2. Use Dev for selected frames requiring quality
3. Train character LoRAs for main cast consistency
4. Use Pro only for final hero frames if needed

**LoRA Training for Characters:**
Custom LoRAs can be trained on character concept art to ensure:
- Consistent character appearance across all frames
- Specific style adherence (sketch, animation, etc.)
- Reduced prompt complexity

---

## 3. Style Consistency Strategies

### The Core Challenge

Storyboards require visual consistency across hundreds of frames:
- Characters must look the same in every panel
- Art style must remain cohesive
- Lighting and mood should match scene requirements

### Strategy 1: Detailed System Prompts (Gemini/GPT)

Create a comprehensive character and style bible in the system prompt:

```markdown
# Storyboard Generation System Prompt

## Visual Style
- Pixar/Dreamworks animation aesthetic
- Warm color palette: ambers, teals, soft purples
- Expressive character poses and faces
- Visible linework suggesting hand-drawn origins
- 16:9 aspect ratio for all frames

## Character Specifications

### Mia (Protagonist)
- Age: 10 years old
- Hair: Curly, vibrant red, shoulder-length
- Eyes: Large, green, highly expressive
- Skin: Fair with freckles across nose and cheeks
- Build: Athletic, confident posture
- Clothing: Purple t-shirt, denim shorts, red sneakers
- Personality in poses: Brave, protective, determined

### Leo (Mia's Brother)
- Age: 7 years old
- Hair: Straight, brown, slightly messy
- Eyes: Large, blue, often wide with wonder
- Skin: Fair, rosy cheeks
- Build: Smaller, often looking up at things
- Clothing: Yellow striped shirt, khaki shorts
- Personality in poses: Curious, sometimes scared, imaginative

[Continue for all characters...]
```

### Strategy 2: Reference Images (Midjourney/Flux)

Use --cref (character reference) and --sref (style reference) in Midjourney:

```
/imagine [scene description] --cref [character_sheet_url] --sref [style_reference_url] --sw 100
```

For Flux, use IP-Adapter or LoRA-based character conditioning.

### Strategy 3: Seed Locking

Most models support seed values for reproducibility:

```python
# Example: Consistent character with seed
response = model.generate(
    prompt="Mia looking determined, medium shot",
    seed=42,  # Lock randomness
    style_preset="animation"
)
```

### Strategy 4: Multi-Stage Pipeline

1. **Generate character sheets** first (turnaround, expressions)
2. **Train LoRA** on character sheets (Flux)
3. **Use LoRA** for all storyboard generation
4. **Post-process** for style unification if needed

---

## 4. Storyboard-Specific Considerations

### Shot Types and Composition

AI models understand cinematographic terminology:

| Shot Type | Prompt Language |
|-----------|-----------------|
| Establishing | "wide establishing shot," "extreme wide angle" |
| Full Shot | "full body shot," "character visible head to toe" |
| Medium Shot | "medium shot," "waist-up framing" |
| Close-Up | "close-up," "face filling frame" |
| Extreme Close-Up | "extreme close-up on eyes," "macro detail shot" |
| Over-the-Shoulder | "OTS shot," "over shoulder composition" |
| POV | "first-person view," "POV shot through character's eyes" |

### Camera Angles

| Angle | Prompt Language |
|-------|-----------------|
| Eye Level | "eye-level angle," "neutral camera height" |
| Low Angle | "low angle," "looking up at subject," "hero shot" |
| High Angle | "high angle," "bird's eye," "looking down" |
| Dutch Angle | "Dutch angle," "tilted frame," "canted shot" |

### Panel Notation

Include standard storyboard annotations:

```
Frame 47 - Act 2, Scene 3
Shot: Medium close-up, slight low angle
Action: Mia reaches toward the glowing portal
Camera: Push in slowly
Audio: [Magical humming intensifies]
Dialogue: "Leo, stay behind me."
```

---

## 5. Cost Analysis and Optimization

### Estimated Production Volume

| Act | Scenes | Panels per Scene | Total Panels |
|-----|--------|------------------|--------------|
| Act 1 | 12 | 8-15 | ~140 |
| Act 2 | 18 | 10-20 | ~270 |
| Act 3 | 10 | 8-15 | ~115 |
| **Total** | 40 | - | **~525 panels** |

Including iterations (3x average): **~1,575 generations**

### Cost Comparison

| Model | Cost per Image | Total Cost (1,575 images) |
|-------|---------------|---------------------------|
| Gemini 2.0 Flash (free tier) | $0 | **$0** (within limits) |
| Gemini 2.0 Flash (paid) | $0.0025 | **$3.94** |
| Flux Schnell | $0.003 | **$4.73** |
| Flux Dev | $0.025 | **$39.38** |
| DALL-E 3 | $0.04 | **$63.00** |
| Flux Pro | $0.055 | **$86.63** |
| Imagen 3 | $0.03 | **$47.25** |
| Midjourney (Standard) | $30/mo flat | **$30/month** |

### Recommended Budget Strategy

**Tier 1: Zero Budget**
- Use Gemini 2.0 Flash free tier for all storyboards
- 60 requests/minute is more than sufficient
- Total cost: **$0**

**Tier 2: Quality Focus ($30-50/month)**
- Gemini for rapid iteration and 80% of frames
- Midjourney Standard for hero frames and key emotional beats
- Total cost: **~$35/month**

**Tier 3: Maximum Flexibility ($50-100/month)**
- Gemini for exploration
- Flux Dev for production frames
- Midjourney for final presentation boards
- Total cost: **~$75/month**

---

## 6. API Integration Recommendations

### Primary: Gemini API (Google AI Studio)

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Generate storyboard frame
response = model.generate_content([
    "Generate a storyboard frame: Mia and Leo discover Jetplane "
    "hiding in the cave. Warm torchlight, medium shot, "
    "expressions of wonder and delight. Pixar animation style."
])

# Save image
image = response.candidates[0].content.parts[0].inline_data
with open("frame_047.png", "wb") as f:
    f.write(image.data)
```

### Secondary: Flux via Replicate

```python
import replicate

output = replicate.run(
    "black-forest-labs/flux-dev",
    input={
        "prompt": "Storyboard frame, Pixar style: Jetplane the baby T-Rex "
                  "with iridescent scales sneezes a rainbow-colored cloud. "
                  "Cave interior, warm lighting, comedic pose",
        "aspect_ratio": "16:9",
        "output_format": "png"
    }
)
```

### Backup: OpenAI DALL-E 3

```python
from openai import OpenAI

client = OpenAI()

response = client.images.generate(
    model="dall-e-3",
    prompt="Storyboard panel in Pixar animation style: A magical "
           "purple minivan crashes through a swirling time portal. "
           "Dramatic angle, motion blur, energy effects",
    size="1792x1024",
    quality="hd",
    n=1
)

image_url = response.data[0].url
```

---

## 7. Production Workflow

### Recommended Pipeline

```
1. SCRIPT BREAKDOWN
   ├── Extract key scenes from screenplay
   ├── Identify shot requirements per scene
   ├── Note character appearances and emotions
   └── Create shot list with panel numbers

2. STYLE LOCK
   ├── Generate 10-20 test frames across different scenes
   ├── Select preferred style direction
   ├── Create style reference library
   └── Document prompt templates that work

3. BATCH GENERATION
   ├── Use Gemini for first-pass generation (all panels)
   ├── Review and flag panels needing improvement
   ├── Regenerate flagged panels with refined prompts
   └── Use Midjourney for hero frames if needed

4. CONSISTENCY PASS
   ├── Review all panels for character consistency
   ├── Flag inconsistencies
   ├── Regenerate or edit as needed
   └── Final approval

5. ASSEMBLY
   ├── Organize frames by act/scene/panel
   ├── Add panel annotations (shot type, action, dialogue)
   ├── Export for animatic creation
   └── Archive generation prompts for future reference
```

### Quality Checklist

For each frame, verify:
- [ ] Character appearance matches reference
- [ ] Shot type matches storyboard notes
- [ ] Composition supports the story beat
- [ ] Emotional tone is correct
- [ ] Lighting matches scene context
- [ ] No anatomical errors
- [ ] Aspect ratio is 16:9
- [ ] Resolution sufficient for presentation

---

## 8. Recommendations Summary

### For "Fairy Dinosaur Date Night" Production

**Primary Tool: Gemini 2.0 Flash**
- Use for 90%+ of storyboard generation
- Leverage conversation context for consistency
- Free tier sufficient for entire production

**Secondary Tool: Midjourney v6.1**
- Reserve for hero frames (5-10 per act)
- Use for pitch deck and marketing materials
- Use --sref for style consistency

**Exploration Tool: Flux Schnell**
- Rapid concept exploration
- Testing composition ideas
- Nearly free iteration

**Backup: DALL-E 3**
- Use when Gemini unavailable
- Best for panels with text elements
- Good prompt adherence

### Immediate Next Steps

- [ ] Set up Google AI Studio account and API key
- [ ] Create character style guide document with reference images
- [ ] Generate test frames for each main character
- [ ] Establish prompt templates for common shot types
- [ ] Generate Act 1, Scene 1 storyboard as proof of concept
- [ ] Document successful prompts in shared library

### Director Review Questions

1. Approve Gemini as primary storyboard generation tool?
2. Budget allocation for Midjourney hero frames ($30/mo)?
3. Preferred style direction: sketch/rough or polished animation?
4. Priority characters for initial style lock testing?
5. Acceptable iteration count per frame (recommend 3-5)?

---

## References & Sources

### Model Documentation
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Imagen 3 on Vertex AI](https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview)
- [Midjourney Documentation](https://docs.midjourney.com/)
- [OpenAI DALL-E 3 API](https://platform.openai.com/docs/guides/images)
- [Flux Model Card - Black Forest Labs](https://blackforestlabs.ai/)

### Benchmarks & Comparisons
- [Artificial Analysis Image Arena](https://artificialanalysis.ai/text-to-image)
- [AI Image Generator Comparison 2026](https://www.unite.ai/best-ai-image-generators/)

### Storyboard Best Practices
- [The Art of the Storyboard](https://www.studiobinder.com/blog/what-is-a-storyboard/)
- [Pixar Storyboard Techniques](https://www.khanacademy.org/computing/pixar/storytelling)
