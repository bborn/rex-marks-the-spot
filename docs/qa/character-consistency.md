# Character Consistency Audit Report

**Date**: 2026-02-04
**Auditor**: QA Agent
**Scope**: Review all character renders against screenplay and design documentation

---

## Executive Summary

This audit compared character designs across concept art, turnarounds, expression sheets, and storyboards against the screenplay (`screenplay/Fairy Dinosaur Date Night.md`) and design documentation (`assets/characters/`).

**Overall Finding**: Several significant inconsistencies were identified, ranging from minor documentation mismatches to major design direction conflicts (particularly for Jetplane).

### Quick Reference

| Character | Issues Found | Severity |
|-----------|--------------|----------|
| Leo | 3 | Medium |
| Mia | 1 | Low |
| Gabe | 2 | Medium |
| Nina | 2 | Medium |
| Ruben | 1 | Low |
| Jetplane | 3 | **Critical** |

---

## Detailed Findings

### 1. Leo Bornsztein (5-year-old boy)

#### Issue 1.1: Pajama Pattern Mismatch (Documentation vs Screenplay)
- **Severity**: Medium
- **Screenplay**: "Leo wears dinosaur pajamas" (line 16)
- **Design Documentation**: `leo/turnaround.md` specifies "Yellow PJs with rocket ship pattern"
- **Actual Renders**: `leo_v1.png`, `leo_v2.png`, `leo_v3.png`, `leo_v4.png` all correctly show GREEN DINOSAUR PAJAMAS
- **Storyboards**: `scene-01-panel-02.png` shows Leo in green dinosaur pajamas - CORRECT
- **Recommendation**: Update `leo/turnaround.md` to specify "Green dinosaur pajamas" for opening scene

#### Issue 1.2: Eye Color Inconsistency
- **Severity**: Medium
- **Design Documentation**: "Expressive brown eyes"
- **Actual Renders**:
  - `leo_v2.png`, `leo_v4.png`: Show BLUE eyes
  - `leo_turnaround.png`: Shows green/hazel eyes
  - `leo_expression_sheet.png`: Shows brown eyes
- **Recommendation**: Standardize eye color across all renders to brown as specified

#### Issue 1.3: Age Specification Discrepancy
- **Severity**: Low
- **Task briefing**: States "Leo 4-5"
- **Design Documentation**: States "Approximately 5 years old"
- **Screenplay**: Implies young child with sippy cup, suggests 4-5 range
- **Status**: Acceptable - design docs align with screenplay intent

---

### 2. Mia Bornsztein (8-year-old girl)

#### Issue 2.1: Age Specification Discrepancy
- **Severity**: Low
- **Task briefing**: States "Mia 9"
- **Screenplay**: "You need to remember she's only eight" (line 157)
- **Design Documentation**: States "Approximately 8 years old"
- **Actual Renders**: Character appears appropriately 8-9 years old
- **Note**: Task briefing is incorrect; screenplay and design docs correctly specify age 8
- **Recommendation**: No change to assets needed; task briefing contained error

#### Consistency Check - PASSED
- **Turnaround**: Purple star shirt, denim shorts, turquoise scrunchie - matches docs
- **Expression sheet**: Consistent design
- **Storyboard panels**: Character recognizable

---

### 3. Gabe Bornsztein (Father, late 30s)

#### Issue 3.1: Formal Attire Inconsistency
- **Severity**: Medium
- **Screenplay**: "GABE & NINA BORNSZTEIN, dressed in black-tie attire" (line 18)
- **Design Documentation**: Specifies "Gala Outfit" with white dress shirt and dark blue tie
- **Actual Renders**:
  - `gabe_v1.png`, `gabe_v2.png`: Show BLACK TUXEDO with bow tie (matches screenplay's "black-tie")
  - `gabe_turnaround.png`, `gabe_expression_sheet.png`: Show white shirt with regular tie (less formal)
- **Recommendation**: Clarify which is the "official" gala look; turnaround should match the tuxedo if that's the approved direction

#### Issue 3.2: Minor Age Appearance
- **Severity**: Low
- **Design Documentation**: "Age: Late 30s (38)"
- **Actual Renders**: Character appears appropriately late 30s with gray temples as specified
- **Status**: Acceptable

---

### 4. Nina Bornsztein (Mother, late 30s)

#### Issue 4.1: Dress Color Inconsistency
- **Severity**: Medium
- **Design Documentation**: "Elegant burgundy/wine cocktail dress"
- **Actual Renders**:
  - `nina_turnaround.png`: Shows BURGUNDY dress - CORRECT
  - `nina_v1.png`, `nina_v2.png`: Show BLACK dress - INCORRECT
- **Recommendation**: Regenerate concept art with correct burgundy/wine dress color

#### Issue 4.2: Dress Style Variation
- **Severity**: Low
- **Design Documentation**: "Cocktail dress, knee-length"
- **Actual Renders**:
  - `nina_turnaround.png`: Shows longer, more conservative dress
  - `nina_v1.png`: Shows more glamorous cocktail dress
- **Recommendation**: Decide on final dress style and ensure consistency

---

### 5. Ruben Romanovsky (Fairy Godfather)

#### Issue 5.1: Dual Appearance by Design
- **Severity**: Low (may be intentional)
- **Screenplay Context**: Ruben first appears "disguised" as a janitor, later reveals fairy nature
- **Actual Renders**:
  - `ruben_v1.png`: Shows janitor outfit with mop, fairy wings visible - CORRECT for initial disguise
  - `ruben_turnaround.png`: Shows formal fairy outfit - CORRECT for later scenes
- **Note**: Both designs may be appropriate for different story moments
- **Recommendation**: Confirm this dual-design approach is intentional; document which outfit for which scenes

#### Consistency Check - MOSTLY PASSED
- **Design Documentation**: Wild gray hair, tired blue-gray eyes, fairy wings, rumpled clothes
- **Actual Renders**: Match description well
- **Minor Note**: Ruben appears older than the screenplay's "forty-nine" - matches kids' perception ("80 or 75") which may be intentional for comedy

---

### 6. Jetplane (Dinosaur Companion)

#### Issue 6.1: CRITICAL - Fundamentally Different Design Directions
- **Severity**: CRITICAL
- **Design Documentation**: Describes "chicken-puppy-lizard hybrid" that is "round, soft, huggable"
- **Actual Renders Show THREE Completely Different Designs**:

**Design A - "Round Bird-Like" (turnaround)**
- File: `jetplane_turnaround.png`
- Appearance: Round owl-like body, teal scales, orange neck ruff, droopy ear flaps
- Matches: Design documentation's "huggable" description

**Design B - "Brontosaurus-Like" (concepts)**
- Files: `jetplane_v1.png`, `jetplane_v2.png`, `jetplane_v3.png`
- Appearance: Long-necked dinosaur, quadrupedal, teal with pink/purple spots and spines
- Does NOT match: "Round, soft" description; looks like a traditional dinosaur

**Design C - "Low-Poly 3D" (preview)**
- File: `jetplane_preview.png`
- Appearance: Blob-like, robotic, dark teal, completely different aesthetic
- Does NOT match: Either other design or documentation

- **Recommendation**: IMMEDIATE design direction decision required. Pick ONE Jetplane design and regenerate all assets consistently.

#### Issue 6.2: Size Proportions
- **Severity**: Medium
- **Design Documentation**: "Small Form: About the size of a large house cat (18" long, 12" tall)"
- **Actual Renders**: Scale difficult to assess without character comparison shots
- **Recommendation**: Create scale reference sheet showing Jetplane next to Leo/Mia

#### Issue 6.3: Missing Key Feature
- **Severity**: Low
- **Design Documentation**: Prominent "toe beans" mentioned as merchandise feature
- **Actual Renders**: Not clearly visible in any current renders
- **Recommendation**: Include underside/belly view showing toe beans

---

## Storyboard vs Character Asset Comparison

### Act 1 Storyboards Reviewed

| Panel | Characters | Consistency Status |
|-------|------------|-------------------|
| scene-01-panel-01 | Mia, Leo on couch | Leo in correct green dino PJs |
| scene-01-panel-02 | Leo close-up | Correct pajamas, holds dino toy |
| scene-01-panel-05 | Jenny (babysitter) | Blonde ponytail, ~15yo - matches screenplay |
| scene-01-panel-08 | Close-up (Mia eyes) | Brown eyes - matches docs |

**Storyboard Assessment**: Act 1 storyboards generally align with screenplay descriptions. Character styles appear consistent within storyboard art style.

---

## Costume Correctness Summary

| Character | Screenplay Description | Design Docs | Renders | Status |
|-----------|----------------------|-------------|---------|--------|
| Leo | "Dinosaur pajamas" | "Rocket ship pajamas" | Green dino PJs | **Renders correct, docs need update** |
| Mia | (Not specified) | "Purple star shirt, denim shorts" | Matches | OK |
| Gabe | "Black-tie attire" | "White shirt, dark tie" | Mixed (tux vs casual) | **Needs clarification** |
| Nina | "Black-tie attire" | "Burgundy cocktail dress" | Mixed (burgundy vs black) | **Needs standardization** |
| Ruben | "Janitor" disguise | Formal fairy outfit | Both exist | OK (if intentional) |
| Jetplane | "Chicken-puppy-lizard" | "Round, huggable" | 3 different designs | **CRITICAL - pick one** |

---

## Priority Action Items

### Critical (Block production)
1. **Jetplane design decision**: Choose ONE design direction and regenerate all assets

### High Priority
2. **Nina dress color**: Regenerate concepts with burgundy dress
3. **Gabe formal attire**: Decide if tuxedo or dress shirt is canonical; update turnaround
4. **Leo eye color**: Standardize to brown across all renders

### Medium Priority
5. **Update Leo design docs**: Change pajama description from "rocket ship" to "dinosaur"
6. **Nina dress style**: Finalize cocktail vs conservative dress length

### Low Priority
7. **Jetplane scale reference**: Create comparison sheet with kids
8. **Jetplane toe beans**: Add underside view for merchandise reference
9. **Document Ruben's dual outfits**: Clarify which scenes use janitor vs fairy look

---

## Appendix: Files Reviewed

### Character Assets
- `assets/characters/turnarounds/*.png` (6 files)
- `assets/characters/expressions/*.png` (6 files)
- `assets/characters/concepts/*/` (24 files across 6 characters)
- `assets/characters/jetplane_preview.png`

### Documentation
- `assets/characters/README.md`
- `assets/characters/{character}/turnaround.md` (6 files)

### Storyboards
- `storyboards/act1/panels/scene-01-panel-*.png` (9 files)

### Screenplay
- `screenplay/Fairy Dinosaur Date Night.md`

---

*Report generated as part of Task #133: QA Character Consistency Audit*
