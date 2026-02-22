# QA Review: Mia Walking Animation Test

**Reviewer:** QA Agent (Task #255)
**Date:** 2026-02-12
**Asset:** `mia_walking_test.mp4`
**URL:** https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/3d-models/characters/mia/animation-tests/mia_walking_test.mp4

---

## Overall Grade: B-

Solid first test. The model holds up well during movement with no catastrophic rigging failures, and the Pixar-like stylized aesthetic comes through. However, the walk cycle feels stiff in the upper body and secondary motion (hair, clothing) is underdeveloped. Needs targeted fixes before production use.

---

## Technical Specs Verified

| Spec | Expected | Actual | Status |
|------|----------|--------|--------|
| Resolution | 1920x1080 | **1280x720** | MISMATCH |
| Frame Rate | 24fps | 24fps | OK |
| Duration | 5 seconds | 5 seconds | OK |
| Total Frames | 120 | 120 | OK |
| Codec | - | H.264 (libx264) | OK |
| File Size | - | 493 KB | OK |

---

## What Works Well

1. **Clean mesh deformation** - No mesh explosion, vertex tearing, or catastrophic joint collapse at any point during the walk. The auto-rigging from Meshy held up well across 120 frames.

2. **Consistent ground contact** - The drop shadow tracks the character correctly throughout the animation. Feet generally maintain contact with the ground plane, and the character reads as "grounded" rather than floating.

3. **Forward locomotion** - The character translates through space correctly (walking from screen-right toward screen-left with slight depth change). This isn't a walk-in-place cycle - it's a proper traveling walk, which is harder to get right.

4. **Arm counter-swing present** - Arms do swing in opposition to legs, which is the fundamental requirement for a natural walk. The phasing is correct (right arm forward when left leg is forward).

5. **Texture stability** - PBR textures on the shirt, jeans, hair, and skin remain clean throughout all frames. No UV swimming, texture stretching, or seam popping visible during movement.

6. **Recognizable silhouette** - Mia's character reads clearly in every frame. The proportions (large head, slim build, ponytail) are maintained and the character is instantly identifiable.

---

## Issues Found

### Critical

None - no show-stopping issues that would require starting over.

### Major

**M1. Stiff upper body / no hip-shoulder counter-rotation**
The torso moves as a rigid block. In a natural walk, the hips and shoulders rotate in opposition (when right leg is forward, right hip is forward and right shoulder is back). This counter-rotation is barely visible in any frame. The result is a mechanical, robotic feel to the walk.
- **Frames affected:** All
- **Fix:** Add spine twist keyframes with ~5-8 degrees of counter-rotation synced to the stride cycle

**M2. Hair/ponytail is mostly static**
The curly ponytail shows minimal secondary motion. Per the character turnaround spec, the ponytail should have "secondary motion, bounce during movement." Currently it moves slightly with the head but doesn't bounce, sway, or delay behind the body's movement.
- **Frames affected:** All
- **Fix:** Add hair physics simulation or manual secondary animation on the ponytail bone chain with 2-3 frame delay behind head motion

**M3. Resolution rendered at 720p, not 1080p**
The video is 1280x720 instead of the stated 1920x1080. For production-quality validation we need the correct target resolution to evaluate texture detail and any aliasing issues.
- **Fix:** Re-render at 1920x1080 for final evaluation

### Minor

**m1. Static facial expression**
The face shows zero variation throughout the 5-second walk. While subtle, even a basic walk should have slight brow movement, blink cycles, or micro-expressions. Currently Mia looks like a mannequin from the neck up.
- **Fix:** Add a blink cycle (every 2-3 seconds) and very subtle brow/mouth variation

**m2. Limited arm swing amplitude**
While the arm counter-swing is correctly phased, the range of motion is small. For an 8-year-old walking with purpose, the arms should swing more freely. Current amplitude is about 15-20 degrees; should be closer to 30-40 degrees.
- **Fix:** Increase arm swing keyframe values by ~50-80%

**m3. No vertical head bob**
The head stays at a constant height through the cycle. A natural walk has ~1-2cm of vertical oscillation where the body rises at mid-stance and dips at heel strike. There's minimal bob visible.
- **Fix:** Add subtle vertical translation to the hip/root bone (~0.01-0.02 Blender units) synced to stride

**m4. Costume color discrepancy from character spec**
The turnaround spec defines Mia wearing a **purple** t-shirt with a **turquoise** scrunchie and **denim shorts**. The animation shows a **pink/magenta** t-shirt, **pink** scrunchie, and **full-length jeans/leggings**. This could be intentional (different outfit for this scene) but should be confirmed.
- **Fix:** Verify with Director whether this outfit variant is approved or if textures need updating

**m5. Clothing deformation is minimal**
The shirt and jeans show very little fabric deformation during movement. They look painted-on rather than like actual clothing. Some subtle wrinkling at the elbows, knees, and waist during extreme poses would add realism.
- **Fix:** Low priority - could add cloth simulation pass or hand-animated wrinkle morphs in a later polish pass

---

## Recommended Fixes (Priority Order)

| Priority | Fix | Effort | Impact |
|----------|-----|--------|--------|
| 1 | Add hip-shoulder counter-rotation (M1) | Medium | High - single biggest improvement to walk naturalism |
| 2 | Add ponytail secondary motion (M2) | Medium | High - the hair is a key character feature |
| 3 | Increase arm swing amplitude (m2) | Low | Medium - quick keyframe adjustment |
| 4 | Add vertical head/body bob (m3) | Low | Medium - quick keyframe adjustment |
| 5 | Re-render at 1080p (M3) | Low | Medium - needed for production validation |
| 6 | Add blink cycle (m1) | Low | Low-Medium - adds life to the character |
| 7 | Verify costume colors (m4) | Low | Low - creative direction question |
| 8 | Cloth deformation (m5) | High | Low - polish pass item |

---

## Production Ready?

**No** - needs one more iteration addressing M1 (hip-shoulder rotation) and M2 (hair physics) at minimum.

### Reasoning

The current animation demonstrates that the Meshy auto-rig works and the model can be animated without breaking. That's a significant milestone. However, the walk is too stiff for a hero character in a Pixar-style production. Mia appears in nearly every scene - her walk needs to convey personality (determined, purposeful, slightly worried). Right now it conveys "generic humanoid locomotion test."

The good news is that the fixes are additive (layering more animation on top of what exists) rather than requiring a redo. The base walk cycle timing and foot placement are solid - it just needs the secondary motion layers that bring it to life.

### Suggested Next Steps

1. Fix M1 + M2 + m2 + m3 (the motion issues) - these are all keyframe adjustments in Blender
2. Re-render at 1080p
3. Submit for second QA pass
4. If approved, use this walk cycle as the template for other character animations

---

## Frame Reference

Key frames analyzed (sampled every 10 frames from 120 total):
- Frame 0: Start pose, arms at sides
- Frame 10: Walk initiation, first stride beginning
- Frame 20: Mid-stride, left leg forward
- Frame 30: Passing position
- Frame 40: Right leg extension
- Frame 50: Contact position
- Frame 60: Second cycle beginning
- Frame 70-90: Continued walking, consistent stride
- Frame 100-119: Walk continues, character has translated significantly across frame

Additionally analyzed frames 24-48 in detail for one complete stride cycle.
