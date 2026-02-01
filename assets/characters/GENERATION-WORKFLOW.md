# Concept Art Generation Workflow

This document provides step-by-step instructions for generating concept art for all 6 characters in "Fairy Dinosaur Date Night".

## Quick Start

### Option 1: Automated Generation (Recommended)

```bash
# Set your API key
export OPENAI_API_KEY="your-key-here"

# Generate all character concept art
python scripts/generate_concept_art.py --all

# Generate for a specific character
python scripts/generate_concept_art.py --character jetplane

# Dry run to preview prompts
python scripts/generate_concept_art.py --all --dry-run
```

### Option 2: Manual Generation

Use the prompts in each character's `concept-art/PROMPTS.md` file with your preferred AI image generation tool.

---

## Recommended Tools

### Tier 1: Best Quality

| Tool | Best For | Cost | Link |
|------|----------|------|------|
| **DALL-E 3** | Consistent, family-friendly designs | ~$0.04-0.08/image | [OpenAI](https://platform.openai.com) |
| **Midjourney V6** | Stylized, Pixar-like aesthetic | $10-30/month | [Discord](https://midjourney.com) |
| **Stable Diffusion XL** | Maximum control, local generation | Free (local) | [Stability AI](https://stability.ai) |

### Tier 2: Alternatives

| Tool | Notes |
|------|-------|
| Leonardo AI | Good free tier, animation-friendly |
| Adobe Firefly | Safe for commercial use |
| Playground AI | Free tier available |

---

## Generation Priority Order

Generate characters in this order (merchandise potential + screen time):

1. **Jetplane** - Highest merchandise potential, must be iconic
2. **Mia** - Main protagonist, emotional anchor
3. **Leo** - Second protagonist, cuteness factor
4. **Ruben** - Unique design with wing expressions
5. **Nina** - "The Look" must be perfect
6. **Gabe** - Costume progression important

---

## What to Generate per Character

### Required (Minimum Viable)
1. **Hero Portrait** - Front-facing character portrait
2. **Full Body Turnaround** - Front, side, back, 3/4 views
3. **Expression Sheet** - 6-8 key emotions

### Recommended (Full Set)
4. **Action Poses** - Character-specific dynamic poses
5. **Costume Variations** - Different outfits/states
6. **Special Elements** - Character-specific features

### Character-Specific Priorities

| Character | Must-Have | Special Focus |
|-----------|-----------|---------------|
| Mia | Turquoise scrunchie visible | Protective sister poses |
| Leo | Gap-tooth smile, freckles | Wonder expressions |
| Gabe | Glasses always on | Costume deterioration arc |
| Nina | "The Look" close-up | Elegant to survival transition |
| Ruben | Wing states (3 versions) | Transformation arc |
| Jetplane | ALL poses | Size comparison, rainbow farts |

---

## Step-by-Step Generation Process

### Step 1: Set Up Your Environment

```bash
# Install required packages
pip install openai requests pillow

# Set API key (choose one)
export OPENAI_API_KEY="sk-..."
export STABILITY_API_KEY="sk-..."
```

### Step 2: Review Prompts

```bash
# List all available prompts
python scripts/generate_concept_art.py --list-prompts

# Preview what will be generated
python scripts/generate_concept_art.py --all --dry-run
```

### Step 3: Generate Iteratively

Start with one character to test quality:

```bash
# Test with Jetplane first (most important)
python scripts/generate_concept_art.py --character jetplane --type portrait

# If quality is good, generate all Jetplane art
python scripts/generate_concept_art.py --character jetplane

# Then proceed to other characters
python scripts/generate_concept_art.py --character mia
python scripts/generate_concept_art.py --character leo
# ... etc
```

### Step 4: Review and Iterate

After generation:
1. Check each image against the quality checklist
2. Regenerate any that don't meet standards
3. Version up (v1 → v2) as you iterate

### Step 5: Organize Output

Images are automatically saved to:
```
assets/characters/{character}/concept-art/
├── {character}_portrait_v1.png
├── {character}_turnaround_v1.png
├── {character}_expressions_v1.png
└── ...
```

---

## Quality Checklist

Before finalizing any concept art, verify:

- [ ] **Readable at small size** - Expression clear when shrunk
- [ ] **Distinctive silhouette** - Recognizable in shadow
- [ ] **Color consistency** - Matches palette documentation
- [ ] **Family-friendly** - Appropriate for ages 6+
- [ ] **Pixar/Dreamworks quality** - Professional animation aesthetic
- [ ] **Character appeal** - Feels likable and approachable
- [ ] **Documentation match** - Consistent with turnaround specs

### Character-Specific Checks

| Character | Must Verify |
|-----------|-------------|
| Mia | Turquoise scrunchie always visible |
| Leo | Freckles visible, gap in teeth |
| Gabe | Glasses on, gray at temples |
| Nina | Hazel-green eyes, wedding ring |
| Ruben | Wings match emotional state |
| Jetplane | Pink toe beans, ear-frill positions |

---

## Using Midjourney (Manual)

If using Midjourney via Discord:

### Basic Command Format
```
/imagine prompt: [copy prompt from PROMPTS.md] --ar 1:1 --s 250 --q 2
```

### Aspect Ratios
- `--ar 1:1` for portraits
- `--ar 16:9` for expression sheets
- `--ar 2:3` for full body

### Style Settings
- `--s 250` balanced stylization
- `--q 2` higher quality
- `--v 6` use version 6

### Consistency Tips
- Use `--seed [number]` to lock style across variations
- Generate one "hero" image first, then reference it
- Add `--no realistic, creepy, horror, anime` to negative

---

## Troubleshooting

### Common Issues

**Problem:** Images look too realistic
**Solution:** Add "Pixar style, 3D animated, cartoon" to start of prompt

**Problem:** Colors don't match documentation
**Solution:** Include hex codes in prompt: "purple shirt (#8B5CF6)"

**Problem:** Inconsistent character across images
**Solution:** Generate a hero image first, use as reference for variations

**Problem:** Expressions not readable
**Solution:** Request "extreme expression, exaggerated features, animation style"

### API Errors

**OpenAI rate limit:** Wait 60 seconds between batches
**Content policy:** Remove any potentially triggering words, emphasize "family-friendly"
**Size not supported:** Use 1024x1024 for DALL-E 3

---

## File Naming Convention

Follow this pattern:
```
{character}_{type}_{variation}_v{version}.png

Examples:
mia_portrait_hero_v1.png
mia_turnaround_front_v1.png
mia_expressions_core_v2.png
jetplane_rainbow_fart_sequence_v1.png
ruben_wing_states_heroic_v3.png
```

---

## Next Steps After Generation

1. **Review with stakeholders** - Get feedback on designs
2. **Iterate on feedback** - Version up as needed
3. **Create final selection** - Pick best versions
4. **Update character docs** - Add image references
5. **Prepare for 3D modeling** - Export clean references

---

## Resources

- Character PROMPTS: `assets/characters/{name}/concept-art/PROMPTS.md`
- Color palettes: `assets/characters/{name}/color-palette.md`
- Turnaround specs: `assets/characters/{name}/turnaround.md`
- Expression guides: `assets/characters/{name}/expressions.md`
- Master guide: `assets/characters/AI-IMAGE-GENERATION-GUIDE.md`
