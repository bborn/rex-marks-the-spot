# Image Quality Assurance System

## Purpose

This document defines the quality assurance system for all visual assets in "Fairy Dinosaur Date Night." The QA system ensures consistency, quality, and brand coherence across all AI-generated images.

---

## QA Reviewer Role

### Role Definition

The **QA Reviewer** is an AI agent persona assigned to review all pull requests containing visual assets before they are merged into main.

### Responsibilities

1. **Review all PRs** containing images in these directories:
   - `assets/characters/*/concept-art/`
   - `docs/storyboards/*/panels/`
   - `assets/environments/`
   - `assets/props/`
   - `renders/`

2. **Apply quality standards** specific to each asset type

3. **Flag issues** with clear, actionable feedback

4. **Approve or request changes** based on defined criteria

5. **Track consistency** across the entire production

### When QA Review is Required

| Change Type | QA Required |
|-------------|-------------|
| New storyboard panels | Yes |
| New character concept art | Yes |
| Environment/background art | Yes |
| 3D model renders | Yes |
| Prop designs | Yes |
| Documentation updates only | No |
| Script/code changes | No |

---

## Visual Style Bible

### Target Aesthetic

**Reference Films:**
- Pixar: *Coco*, *Inside Out*, *Luca*
- DreamWorks: *How to Train Your Dragon*, *The Croods*
- Sony: *Spider-Verse* (for stylized options)

**Core Style Attributes:**
- 3D CGI animation look (NOT 2D, NOT photorealistic)
- Warm, saturated colors
- Soft lighting with defined shadows
- Expressive, exaggerated features
- Clean, readable compositions
- Family-friendly tone in all imagery

### Style Consistency Scale

Rate each image 1-5 on style adherence:

| Score | Description |
|-------|-------------|
| 5 | Perfect match to target Pixar/DreamWorks aesthetic |
| 4 | Minor deviations, easily correctable |
| 3 | Noticeable style drift, needs regeneration |
| 2 | Wrong aesthetic entirely (too realistic, 2D, etc.) |
| 1 | Completely off-brand, reject immediately |

**Minimum passing score: 4**

---

## Asset Type Standards

### 1. Storyboard Panels

**Purpose:** Communicate story beats, camera angles, and composition

**Requirements:**

| Criterion | Standard | Pass/Fail |
|-----------|----------|-----------|
| Style | Pixar/DreamWorks 3D animated look | Must pass |
| Aspect Ratio | 16:9 (cinematic) | Must pass |
| Resolution | Minimum 1024px wide | Must pass |
| Composition | Clear focal point, readable at 50% scale | Must pass |
| Characters | Recognizable as defined characters | Must pass |
| Lighting | Matches scene description (day/night, mood) | Must pass |
| Continuity | Consistent with adjacent panels | Must pass |

**Character Consistency Checks:**

| Character | Must Verify |
|-----------|-------------|
| Mia | Brown hair with turquoise scrunchie, purple star shirt |
| Leo | Messy brown hair, freckles, green dinosaur shirt |
| Gabe | Dark hair with gray temples, rectangular glasses |
| Nina | Wavy dark brown hair, hazel-green eyes, elegant |
| Ruben | Gray wild hair, droopy iridescent wings, worn fairy clothes |
| Jetplane | Teal scales, orange ruff, huge amber eyes, pink ear-frills |

**Common Rejection Reasons:**
- Photorealistic style instead of animated
- Characters unrecognizable from reference designs
- Wrong costume for scene (e.g., pajamas in daytime adventure)
- Lighting doesn't match story context
- Composition too cluttered or unclear

---

### 2. Character Concept Art

**Purpose:** Define canonical character appearance for all production

**Requirements:**

| Criterion | Standard | Pass/Fail |
|-----------|----------|-----------|
| Style | Pixar-quality 3D character design | Must pass |
| Background | Clean white or neutral (for extraction) | Must pass |
| Proportions | Consistent with turnaround documentation | Must pass |
| Colors | Exact match to color palette hex codes | Must pass |
| Expression | Readable, exaggerated for animation | Must pass |
| Silhouette | Distinctive, recognizable in shadow | Must pass |
| Age-appropriate | Family-friendly, no inappropriate elements | Must pass |

**Deliverable-Specific Standards:**

**Hero Portraits:**
- Full face visible, slight 3/4 angle preferred
- Neutral or signature expression
- Shoulders visible minimum

**Turnarounds:**
- Four views: front, side (left), back, 3/4
- Identical pose across all views
- Arms slightly away from body for clarity
- Feet visible in all views

**Expression Sheets:**
- Minimum 6 expressions per sheet
- Include: happy, sad, scared, angry, surprised, determined
- Character-specific expressions as defined in docs
- Consistent head size across expressions

**Action Poses:**
- Clear line of action
- Dynamic but readable
- Costume appropriate for scene context

---

### 3. Environment/Background Art

**Purpose:** Establish locations and atmosphere

**Requirements:**

| Criterion | Standard | Pass/Fail |
|-----------|----------|-----------|
| Style | Matches character art style (Pixar 3D) | Must pass |
| Mood | Appropriate for story beat | Must pass |
| Depth | Clear foreground/midground/background | Must pass |
| Character space | Appropriate areas for character placement | Must pass |
| Continuity | Consistent with established locations | Must pass |

**Location-Specific Standards:**

| Location | Key Elements |
|----------|-------------|
| Bornsztein Home | Warm lighting, cozy, modern suburban |
| Magic Minivan | Slightly beat-up exterior, roomy interior |
| Jurassic Swamp | Humid, misty, prehistoric plants, threatening |
| Cave | Dark with bioluminescent accents, safe feeling |
| Colorful Canyon | Rainbow-streaked rock formations, magical |

---

### 4. Prop Designs

**Purpose:** Define important story objects

**Requirements:**

| Criterion | Standard | Pass/Fail |
|-----------|----------|-----------|
| Style | Matches production aesthetic | Must pass |
| Scale | Shown with size reference | Recommended |
| Detail | Appropriate for screen prominence | Must pass |
| Function | Visual design suggests usage | Must pass |

**Key Props:**

| Prop | Critical Details |
|------|-----------------|
| Ruben's Wand | Dented, tape on handle, stars that sometimes sputter |
| Leo's Toy Dinosaur | Foreshadows Jetplane, well-loved appearance |
| Nina's Wedding Ring | Gold band, visible in key moments |
| Gabe's Glasses | Rectangular, present in all Gabe images |

---

## Review Process

### PR Submission Requirements

Before submitting a PR with visual assets:

1. **Self-check** against applicable standards above
2. **Include metadata** in PR description:
   - Asset type (storyboard, concept art, environment, prop)
   - Scene/character reference
   - Generation tool used
   - Prompt used (for reproducibility)
3. **Label PR** with `needs-qa-review`

### Review Workflow

```
[PR Created]
    ↓
[Auto-labeled: needs-qa-review]
    ↓
[QA Reviewer assigned]
    ↓
[Review against standards]
    ↓
    ├── [APPROVED] → Merge to main
    │
    └── [CHANGES REQUESTED] → Back to creator
                ↓
        [Creator addresses feedback]
                ↓
        [Re-review]
```

### Review Checklist Template

```markdown
## QA Review: [PR Title]

### Asset Summary
- Type: [Storyboard / Concept Art / Environment / Prop]
- Count: [N images]
- Scene/Character: [Reference]

### Style Consistency
- [ ] Matches Pixar/DreamWorks animated aesthetic
- [ ] Consistent with existing approved assets
- Score: [1-5]

### Technical Quality
- [ ] Resolution meets minimum requirements
- [ ] Aspect ratio correct for asset type
- [ ] No artifacts or obvious AI generation errors

### Character Consistency (if applicable)
- [ ] Characters match reference designs
- [ ] Costumes appropriate for scene
- [ ] Expressions readable

### Continuity
- [ ] Matches established visual canon
- [ ] Consistent with adjacent scenes/panels
- [ ] No contradictions with approved art

### Verdict
- [ ] **APPROVED** - Ready to merge
- [ ] **CHANGES REQUESTED** - See comments

### Comments
[Specific feedback here]
```

---

## Handling Rejections

### Rejection Categories

| Category | Action Required |
|----------|----------------|
| Style mismatch | Regenerate with adjusted prompts |
| Character inconsistency | Use reference images in prompt |
| Technical issues | Adjust generation parameters |
| Continuity error | Review adjacent panels, align |
| Minor issues | Can be addressed in iteration |

### Feedback Format

When requesting changes, use this format:

```
**Issue:** [Specific problem]
**Location:** [Which image/element]
**Expected:** [What it should look like]
**Suggestion:** [How to fix - prompt adjustment, etc.]
```

### Appeal Process

If creator disagrees with rejection:
1. Add comment explaining creative rationale
2. Request Director (human) review
3. Director makes final call

---

## Consistency Tools

### Reference Image Sets

Maintain approved reference images for each character:

```
assets/characters/{name}/reference/
├── approved_portrait.png      # Canonical face
├── approved_turnaround.png    # Canonical body
├── approved_colors.png        # Color reference
└── REFERENCE_NOTES.md         # Usage guidelines
```

### Prompt Templates

Use standardized prompt components:

**Style Prefix (always include):**
```
Pixar-style 3D animated film, DreamWorks quality, family-friendly,
professional animation, high quality render,
```

**Style Suffix (always include):**
```
--no realistic, photorealistic, anime, 2D, cartoon, creepy, horror
```

### Color Palette Enforcement

Include hex codes in prompts for consistency:

| Character | Key Colors |
|-----------|-----------|
| Mia | Purple shirt #8B5CF6, Turquoise scrunchie #2DD4BF |
| Leo | Green dino shirt #22C55E, Khaki shorts #D4A574 |
| Gabe | White shirt #FFFFFF, Blue tie #3B82F6 |
| Nina | Burgundy dress #881337, Gold jewelry #FFD700 |
| Ruben | Faded purple vest #7C3AED, Iridescent wings |
| Jetplane | Teal scales #14B8A6, Orange ruff #FB923C, Amber eyes #F59E0B |

---

## Quality Metrics

### Production Health Dashboard

Track these metrics weekly:

| Metric | Target | Warning |
|--------|--------|---------|
| First-pass approval rate | >70% | <50% |
| Average review cycles | <2 | >3 |
| Style consistency score | >4.0 | <3.5 |
| Character recognition rate | 100% | <95% |

### Common Issues Log

Maintain a log of recurring issues for training:

```
production/quality-assurance/issues-log.md
```

Format:
```markdown
## [Date] - [Issue Type]
**Frequency:** [How often]
**Root cause:** [Why it happens]
**Solution:** [How to prevent]
**Prompt adjustment:** [If applicable]
```

---

## Integration with TaskYou

### QA Reviewer Persona Definition

Add to remote task queue configuration:

```yaml
persona: qa-reviewer
role: Quality Assurance Reviewer
responsibilities:
  - Review PRs labeled 'needs-qa-review'
  - Apply standards from QA-SYSTEM.md
  - Provide actionable feedback
  - Approve or request changes
triggers:
  - PR created with image files
  - PR labeled 'needs-qa-review'
autonomy: review-only  # Cannot merge, only approve/request changes
escalate_to: director  # Human review for disputes
```

### Automated Checks (Future)

Consider implementing:
- Aspect ratio validation
- Resolution verification
- Color palette extraction and comparison
- Style classifier (trained on approved assets)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-02-02 | Initial QA system definition |

---

## Quick Reference Card

### Before Submitting Images

1. Is it Pixar/DreamWorks style (not realistic, not 2D)?
2. Are characters recognizable with correct costumes?
3. Is the resolution sufficient (1024px minimum)?
4. Does it match the scene's lighting/mood?
5. Is it consistent with adjacent panels?

### Red Flags (Auto-Reject)

- Photorealistic rendering
- 2D/anime style
- Unrecognizable characters
- Wrong aspect ratio
- Inappropriate content
- Major continuity breaks

### Green Flags (Strong Approval Signals)

- Perfect style match to reference films
- Characters instantly recognizable
- Clear composition and readability
- Emotional tone matches script
- Consistent with production aesthetic
