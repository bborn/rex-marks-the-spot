# Character Design Documentation

## Fairy Dinosaur Date Night - Character Concepts

This directory contains complete character design documentation for all six main characters in "Fairy Dinosaur Date Night."

## Characters Overview

| Character | Role | Key Visual Elements |
|-----------|------|---------------------|
| **Mia** | Kid protagonist (8yo girl) | Turquoise scrunchie, purple star shirt, determined expression |
| **Leo** | Kid protagonist (5yo boy) | Messy hair, freckles, gap-tooth, green dino shirt |
| **Gabe** | Dad | Rectangular glasses, gray temples, costume deterioration arc |
| **Nina** | Mom | Hazel-green eyes, burgundy dress, "The Look" |
| **Ruben** | Fairy godfather | Droopy wings (changing with emotion), wild gray hair, worn fairy clothes |
| **Jetplane** | Dinosaur companion | Teal scales, big amber eyes, ear-frills, rainbow farts |

## Quick Start: Generate Concept Art

### Automated Generation (Recommended)

```bash
# Set your API key
export OPENAI_API_KEY="your-key-here"

# Generate all character concept art
python scripts/generate_concept_art.py --all

# Generate for a specific character
python scripts/generate_concept_art.py --character jetplane

# Preview prompts without generating
python scripts/generate_concept_art.py --all --dry-run
```

See **[GENERATION-WORKFLOW.md](GENERATION-WORKFLOW.md)** for detailed instructions.

Track progress in **[IMAGE-MANIFEST.md](IMAGE-MANIFEST.md)** (75 images total).

---

## Directory Structure

```
assets/characters/
├── README.md                    # This file
├── AI-IMAGE-GENERATION-GUIDE.md # Master guide for AI image generation
├── GENERATION-WORKFLOW.md       # Step-by-step generation workflow
├── IMAGE-MANIFEST.md            # Deliverables checklist (75 images)
│
├── mia/
│   ├── turnaround.md           # 3D modeling reference
│   ├── expressions.md          # Key expressions needed
│   ├── color-palette.md        # Official colors with hex codes
│   └── concept-art/
│       └── PROMPTS.md          # AI generation prompts
│
├── leo/
│   ├── turnaround.md
│   ├── expressions.md
│   ├── color-palette.md
│   └── concept-art/
│       └── PROMPTS.md
│
├── gabe/
│   ├── turnaround.md
│   ├── expressions.md
│   ├── color-palette.md
│   └── concept-art/
│       └── PROMPTS.md
│
├── nina/
│   ├── turnaround.md
│   ├── expressions.md
│   ├── color-palette.md
│   └── concept-art/
│       └── PROMPTS.md
│
├── ruben/
│   ├── turnaround.md
│   ├── expressions.md
│   ├── color-palette.md
│   └── concept-art/
│       └── PROMPTS.md
│
└── jetplane/
    ├── turnaround.md
    ├── expressions.md
    ├── color-palette.md
    └── concept-art/
        └── PROMPTS.md
```

## Documentation Contents

### turnaround.md
- Physical description (height, build, proportions)
- Facial features
- Hair/wings/special features
- Costume design
- Key views for 3D modeling (front, side, back, 3/4)
- Rigging notes
- Scale references
- Animation guidelines

### expressions.md
- Primary expressions (6-8 key emotions)
- Secondary expressions
- Expression transitions
- Special character elements (wings for Ruben, ear-frills for Jetplane)
- Mouth shapes for dialogue
- Animation notes

### color-palette.md
- Hair/skin/eye colors with hex codes and RGB values
- Costume colors
- Accessory colors
- Emotional color variations
- Color harmony notes
- Technical rendering notes

### concept-art/PROMPTS.md
- Ready-to-use prompts for AI image generation
- Hero portraits
- Full body turnarounds
- Expression sheets
- Costume variations
- Action poses
- Merchandise-ready designs

## How to Generate Concept Art

1. **Read the AI-IMAGE-GENERATION-GUIDE.md** for general tips and tool recommendations

2. **Choose your tool**:
   - Midjourney V6+ (best for Pixar style)
   - DALL-E 3 (consistent, family-friendly)
   - Stable Diffusion XL (most control)

3. **Use the PROMPTS.md files** in each character's concept-art folder

4. **Save generated images** using naming convention:
   ```
   {character}_{type}_{variation}_v{version}.png
   ```

5. **Cross-reference** with turnaround.md and color-palette.md for accuracy

## Style Guide Summary

### Visual Style
- Pixar/Dreamworks animated film aesthetic
- Family-friendly (ages 6+)
- Expressive, readable emotions
- Distinctive silhouettes
- Warm, approachable color palettes

### Design Priorities
1. **Readability**: Emotions clear at any size
2. **Silhouette**: Recognizable in shadow
3. **Consistency**: Colors and features match documentation
4. **Appeal**: Characters feel likable and approachable
5. **Merchandise**: Especially Jetplane - must be toyetic

## Character Relationships (Visual)

### The Bornsztein Family
- **Hair color**: All four have brown hair (family connection)
- **Eyes**: All have warm brown/hazel eyes
- **Skin tone**: Consistent warm family palette
- **Kids vs Parents**: Kids have brighter, more saturated costumes

### Visual Pairings
- **Mia + Leo**: Purple and green complement each other
- **Gabe + Nina**: Formal wear pairs them as couple
- **Leo + Jetplane**: Green shirt echoes Jetplane's teal
- **Ruben + Kids**: His muted palette contrasts their brightness

## Notes for Director Review

### Priority Characters
1. **Jetplane** - Merchandise potential makes this crucial
2. **Mia & Leo** - Protagonists need to be instantly likable
3. **Ruben** - Unique design with wing expressions
4. **Parents** - Support characters but need costume arc

### Iteration Expectations
- First pass: Overall design and appeal
- Second pass: Expression range and readability
- Third pass: Color refinement
- Fourth pass: Final polish and consistency

### Questions for Review
- Is Jetplane cute/toyetic enough?
- Does "The Look" work for Nina?
- Are Ruben's wing states distinct enough?
- Do the kids read as siblings?
- Is the family connection visible?

---

*Documentation created for AI-assisted animation production pipeline*
