# Character Rigging Production Guide

**Project:** Fairy Dinosaur Date Night
**Last Updated:** February 2026
**Purpose:** Definitive guide for producing animation-ready rigged characters

This guide covers everything needed to take an AI-generated 3D model and make it ready for production animation. It is the source of truth for all character rigging work on this project.

---

## Table of Contents

1. [Rigging Fundamentals](#section-1-rigging-fundamentals)
2. [Our Meshy Workflow](#section-2-our-meshy-workflow)
3. [Post-Meshy Cleanup in Blender](#section-3-post-meshy-cleanup-in-blender)
4. [Quality Checklist](#section-4-quality-checklist)
5. [Alternative Approaches](#section-5-alternative-approaches)
6. [Troubleshooting](#section-6-troubleshooting)
7. [Character-Specific Notes](#section-7-character-specific-notes)
8. [Quick Reference](#section-8-quick-reference)

---

## Section 1: Rigging Fundamentals

### What Is a Rig?

A **rig** is a skeletal structure embedded inside a 3D mesh that lets animators pose and move a character. Without a rig, every vertex of the mesh would need to be moved individually per frame.

In Blender, a rig is called an **armature**, made up of individual **bones**. Each bone represents a controllable joint. When an animator rotates or moves a bone, the surrounding mesh vertices follow.

### Bone Hierarchies

Bones are organized in a parent-child tree. Movement cascades from parent to child:

```
Hips (root)
  +-- Spine
  |     +-- Spine1
  |           +-- Spine2 (Chest)
  |                 +-- Neck
  |                 |     +-- Head
  |                 +-- LeftShoulder
  |                 |     +-- LeftUpperArm
  |                 |           +-- LeftForearm
  |                 |                 +-- LeftHand
  |                 |                       +-- Fingers...
  |                 +-- RightShoulder
  |                       +-- (mirrors left arm)
  +-- LeftUpperLeg
  |     +-- LeftLowerLeg
  |           +-- LeftFoot
  |                 +-- LeftToe
  +-- RightUpperLeg
        +-- (mirrors left leg)
```

**Root bone** (typically "Hips"): Moving the root moves the entire character. Every other bone descends from it.

**Parent-child inheritance**: Rotating a shoulder causes the upper arm, forearm, hand, and fingers to all follow. But each child can also rotate independently relative to its parent.

### Weight Painting

**Weight painting** controls how much influence each bone has over each vertex. Every vertex gets a weight from **0.0** (no influence) to **1.0** (full influence) per bone.

- Near joints, vertices are influenced by two adjacent bones (e.g., elbow area: part upper arm, part forearm), creating smooth bending.
- Weights for all bones influencing a single vertex must normalize to **1.0** total.
- In Blender, weight painting is done visually: **red** = 1.0 (full influence), **blue** = 0.0 (no influence).

Each bone automatically creates a corresponding **vertex group** with the same name. Weight painting edits these vertex groups.

### IK vs FK

**Forward Kinematics (FK):**
- Each bone is rotated individually, working down the chain (shoulder -> upper arm -> forearm -> hand).
- Best for: arm swings, flowing gestures, tail/hair/cape animation, artistic arcs.

**Inverse Kinematics (IK):**
- You position the end of the chain (hand or foot), and all intermediate joints calculate automatically.
- Best for: feet planted on ground, hands gripping objects, climbing, any fixed-endpoint motion.

| Scenario | FK | IK |
|----------|----|----|
| Arm swinging freely | Yes | |
| Hand gripping railing | | Yes |
| Walk cycle (legs) | | Yes |
| Flowing arm gesture | Yes | |
| Foot on ground | | Yes |
| Tail wagging | Yes | |

**Production rigs include FK/IK switching** so animators can change mid-animation (e.g., IK for grabbing a door handle, then FK for pulling away with a sweeping motion). Blender's Rigify generates this automatically.

### Bone Constraints

Constraints control and limit bone behavior:

| Constraint | Purpose | Common Use |
|-----------|---------|-----------|
| **Limit Rotation** | Prevents joints from bending unnaturally | Knees only bend backward (0-150 deg), elbows only one direction |
| **Copy Rotation** | One bone copies another's rotation (partially) | Twist bones in forearm copy fraction of hand twist |
| **Damped Track** | Points bone toward a target | Eye tracking a look-at target |
| **IK** | Inverse kinematics solver | Hand/foot placement |
| **Stretch To** | Stretches bone toward target | Cartoon squash-and-stretch |
| **Child Of** | Dynamic parent switching | Space switching (world/local/parent) |

### Pole Targets

Pole targets solve the ambiguity in IK: which direction should a joint bend? Without a pole target, a knee could bend forward, backward, or sideways.

- **Knees**: pole target placed in front, ensuring forward bending
- **Elbows**: pole target placed behind, ensuring backward bending

### Humanoid Rig Standards

**Bone counts by rig complexity:**

| Type | Bone Count | Use Case |
|------|-----------|----------|
| Minimum humanoid (Unity) | 15 | Bare minimum for retargeting |
| Mixamo standard | 65 | Full body with fingers |
| Rigify generated | ~333 | Production rig with FK/IK/mechanism bones |
| Game-ready typical | 30-75 | Depends on finger/face needs |
| Film production | 100-500+ | Includes face rig, correctives, twist bones |

**Standard naming conventions:**

- **Mixamo**: Prefixed `mixamorig:` (e.g., `mixamorig:Hips`, `mixamorig:LeftArm`)
- **Blender**: `.L`/`.R` suffixes (e.g., `Shoulder.L`, `UpperArm.L`)
- **Unity Humanoid**: Internal names (Hips, Spine, Chest, LeftUpperArm, etc.)

Consistent naming matters for animation retargeting, mirroring, and tool compatibility.

### Common Rigging Mistakes

1. **Weight bleed**: Upper arm vertices influenced by chest bone -> arm clips through torso
2. **No rotation limits**: Joints bend 360 degrees through the body
3. **Too few spine bones**: Single spine bone = rigid plank torso
4. **Missing twist bones**: Forearm twist causes candy-wrapper collapse
5. **Unweighted vertices**: Stray verts that fly off during animation
6. **Asymmetric weights**: Left/right sides behave differently

### Secondary Motion

**Hair rigging options:**

| Approach | Pros | Cons |
|----------|------|------|
| **Bone chains (FK)** | Full control, works everywhere | Manual animation work |
| **Physics sim** | Automatic, reactive | Unpredictable, harder to export |
| **Hybrid** (recommended) | Best of both, spring bones | Moderate setup |

For this project: bone chains with spring/jiggle physics for main characters' hair. Bake to keyframes for export.

**Cloth simulation**: Applied as physics modifier, pinned at attachment points (shoulders for cape, waist for skirt). Collision with character body prevents pass-through.

### Facial Animation

**Two approaches:**

| Method | Setup Time | Quality | File Size | Best For |
|--------|-----------|---------|-----------|----------|
| **Blend shapes/shape keys** | High (sculpt each) | Highest | Larger | Film production |
| **Bone-based** | Moderate | Good | Smaller | Games, stylized |
| **Hybrid** (industry standard) | Highest | Best | Moderate | Hero characters |

**For this project**: Bone-based jaw/eye controls + 15-25 shape keys for core expressions (smile, frown, surprise, anger, blink, lip shapes for dialogue). AI-generated models don't come with shape keys, so start with bone-only facial rigs and add shape keys later for hero characters.

---

## Section 2: Our Meshy Workflow

### What Meshy's Auto-Rig Provides

Meshy offers a marker-based auto-rigging system. You place markers on key joints (shoulder, ankle, waist), and Meshy generates the skeleton and applies automatic weight painting.

**What Meshy does well:**
- Fast automatic skeleton generation (seconds)
- Automatic weight painting
- 500+ preset animations (locomotion, daily activities, combat, acrobatics)
- FBX and GLB export with animation
- Integrated with model generation pipeline

**What Meshy does NOT provide:**
- No published bone hierarchy documentation (black-box system)
- No bone constraints (no IK/FK, no rotation limits)
- No finger bones (or very simplified)
- No facial rig / face bones
- No ability to customize the rig before export
- No bone editing or weight paint adjustment within the platform
- Weight painting has known issues at elbows and shoulders

### Meshy's Actual Limitations

Based on official docs, user reports, and independent reviews:

1. **API only supports textured humanoid (bipedal) models** -- must be UV-unwrapped with base color textures
2. **Quadruped rigging** is UI-only, not available via API
3. **No finger bones** -- Meshy's blog recommends Mixamo for finger rigging
4. **No face bones** -- facial animation is not possible with Meshy rigs
5. **Weight painting issues** at elbows and shoulders are common
6. **Preset animations only** -- no custom animation creation within Meshy
7. **Height parameter** (default 1.7m) and marker placement are the only customization

### Step-by-Step Meshy Pipeline

```
1. GENERATE/UPLOAD MODEL
   - Generate via Meshy text-to-3D or image-to-3D
   - Or upload existing GLB (must be UV-unwrapped with PNG textures)
   - Model should be in neutral stance (T-pose recommended)

2. AUTO-RIG
   - Place markers on key joints: shoulder, ankle, waist
   - Set height (default 1.7m, adjust for children/creatures)
   - Meshy generates skeleton + weights automatically

3. SELECT ANIMATION (optional)
   - Choose from 500+ preset animations
   - Walking and running auto-generated via API
   - Preview animation on the rigged model

4. EXPORT
   - Download FBX (recommended for animation data)
   - GLB also available
   - Default 24 FPS for animations

5. POST-PROCESSING (required for production)
   - Import into Blender
   - Fix weight painting at elbows/shoulders
   - Add IK constraints
   - Add rotation limits
   - Add facial rig separately
   - See Section 3 for full cleanup workflow
```

### Optimal Meshy Settings

| Setting | Value | Reason |
|---------|-------|--------|
| Export format | FBX | Best animation data preservation |
| Height | Character-specific (see Section 7) | Accurate proportions |
| Marker placement | Precise as possible | Directly affects rig quality |
| Model stance | T-pose or A-pose | Best for clean deformation |
| Textures | Must be UV-unwrapped PNG | API requirement |

### FBX vs GLB for Meshy Exports

| Format | Strengths | Weaknesses |
|--------|-----------|-----------|
| **FBX** | Better animation data, preferred for Blender/Unity/Unreal, complex armatures | Proprietary format |
| **GLB** | Single file, good for web/AR, bundles everything | Less reliable animation in some pipelines |

**Recommendation**: Always export FBX when animation is involved. Keep GLB as backup.

### Assessment: When Meshy Is Enough

| Use Case | Meshy Sufficient? |
|----------|------------------|
| Previs / blocking | Yes |
| Background characters | Yes (with basic cleanup) |
| Supporting characters | Maybe (needs cleanup) |
| Hero characters | No (needs re-rigging) |
| Facial animation | No |
| Custom animations | No (preset-only) |

---

## Section 3: Post-Meshy Cleanup in Blender

### Import Into Blender

```python
# File > Import > FBX (.fbx)
# Or from command line:
# blender --background --python scripts/rigging_pipeline.py -- --model character.fbx --character mia
```

After import, verify:
1. Armature is present (check Outliner for object with bone icon)
2. Mesh is parented to armature
3. Vertex groups exist on the mesh (Properties > Object Data > Vertex Groups)

### Required Weight Painting Fixes

The most common post-import fixes needed:

**1. Normalize all weights**
```
Select mesh > Weight Paint mode > Weights menu > Normalize All
```
This ensures all vertex weights sum to 1.0, preventing "floaty" vertices.

**2. Limit total influences to 4**
```
Select mesh > Weight Paint mode > Weights menu > Limit Total (limit=4)
```
Game engines typically support max 4 bone influences per vertex.

**3. Clean zero-weight groups**
```
Select mesh > Object mode > Object menu > Clean Vertex Group Weights (limit=0.01)
```

**4. Fix shoulder area**

Shoulders are the most problematic area for auto-rigs. Common issues:
- Upper arm vertices influenced by chest/spine bones
- Deltoid area doesn't deform smoothly when arm raises

Fix process:
1. Enter Weight Paint mode with the armature in Pose mode
2. Pose the arm straight up (180 degrees)
3. Select the "UpperArm" vertex group
4. Use the **Subtract** brush (hold Ctrl) to remove chest bone influence from the deltoid area
5. Use the **Draw** brush to add proper UpperArm influence
6. Use the **Blur** brush (Shift) to smooth transitions

**5. Fix hip/thigh area**

Similar to shoulders -- thigh vertices often bleed into the opposite leg or torso.

Fix process:
1. Pose the leg into a deep squat
2. Check the "Thigh" vertex group
3. Clean up any cross-body weight bleed
4. Smooth transitions between thigh and hips

### Adding IK Constraints

For characters that need foot/hand placement (all hero characters):

```python
# In Blender, select armature > Pose mode > Select hand/foot bone
# Bone Properties > Bone Constraints > Add > Inverse Kinematics

# Settings:
# Chain Length: 2 (2-bone chain for limbs)
# Target: Empty object placed at desired position (optional)
# Pole Target: Empty object controlling bend direction (optional)
```

Or use the automated script:
```bash
blender --background --python scripts/rigging_pipeline.py -- \
    --model character.fbx --character mia --output mia_rigged.fbx
```

The pipeline script (`scripts/rigging_pipeline.py`) auto-detects bone names across Mixamo, AccuRIG, and standard conventions.

### Adding Rotation Limits

Prevents impossible joint positions. Key limits:

| Joint | Axis | Min | Max | Notes |
|-------|------|-----|-----|-------|
| Elbow | X | -5 deg | 150 deg | Only bends one direction |
| Elbow | Y | -90 deg | 90 deg | Twist range |
| Elbow | Z | -10 deg | 10 deg | Minimal side-to-side |
| Knee | X | -5 deg | 150 deg | Only bends backward |
| Knee | Y,Z | -10 deg | 10 deg | Nearly locked |
| Head | X | -45 deg | 45 deg | Nod range |
| Head | Y | -80 deg | 80 deg | Turn range |
| Head | Z | -45 deg | 45 deg | Tilt range |
| Fingers | X | -10 deg | 100 deg | Curl range |

Applied in Blender: Select bone in Pose mode > Bone Constraints > Add > Limit Rotation.

### Hair/Clothing Setup

**Option A: Bone chains (recommended for this project)**

1. In Edit mode on the armature, add a chain of 4-6 bones following each major hair strand
2. Parent hair bones to the head bone
3. Weight paint the hair mesh to these bones
4. Apply spring/jiggle physics addon for automated secondary motion
5. Bake to keyframes for export

**Option B: Cloth simulation**

1. Separate hair/clothing as its own mesh object
2. Add Cloth physics modifier
3. Pin vertices at attachment points (using vertex group)
4. Add collision modifier to the body mesh
5. Bake simulation
6. For export: bake to shape keys or vertex animation

### Twist Bone Setup

Prevents the "candy wrapper" effect when forearms rotate:

1. In Edit mode, subdivide the forearm bone to create 2-4 segments
2. Each segment gets a Copy Rotation constraint pointing at the hand bone
3. Set influence to distribute the twist:
   - Segment 1 (near elbow): 25% influence
   - Segment 2: 50% influence
   - Segment 3: 75% influence
   - Hand: 100% (original rotation)

Or enable **Preserve Volume** on the Armature modifier (uses Dual Quaternion skinning).

---

## Section 4: Quality Checklist

Run the quality checker script to automate validation:
```bash
blender --background --python scripts/rig_quality_checker.py -- model.fbx
```

### Must Have (All Animated Characters)

- [ ] All vertices weighted (>99% coverage)
- [ ] No clipping in rest pose (T-pose or A-pose)
- [ ] Proper deformation at shoulders (test: arms forward + up)
- [ ] Proper deformation at hips (test: deep squat pose)
- [ ] Proper deformation at elbows/knees (test: full bend)
- [ ] No candy-wrapper twist at forearms
- [ ] Consistent bone naming convention (all .L/.R or all Left/Right)
- [ ] Single root bone (typically Hips)
- [ ] Clean FBX/GLB export with all data intact
- [ ] Walks/runs without foot sliding (if using locomotion)

### Should Have (Hero Characters: Mia, Leo, Ruben, Jetplane)

- [ ] IK/FK switching on arms and legs
- [ ] Foot roll controls (heel pivot, ball pivot, toe pivot)
- [ ] Finger controls (at least open/close per hand)
- [ ] Rotation limits on all joints
- [ ] Facial controls (jaw open, blink, brow raise at minimum)
- [ ] Symmetry (left/right bone counts match)
- [ ] Max 4 bone influences per vertex
- [ ] Animation-friendly control shapes (custom bone shapes)

### Nice to Have (Premium Quality)

- [ ] Corrective shape keys at problem joints (shoulder, hip)
- [ ] Secondary motion bones (hair, cloth, tail)
- [ ] Squash-and-stretch on spine/limbs
- [ ] Bendy bones for smooth cartoon curves
- [ ] Custom properties for animation sliders
- [ ] Proxy rig (simplified mesh for faster viewport)

### Stress Test Poses

Before signing off on a rig, test these specific poses:

1. **Arms straight up** - Tests shoulder deformation
2. **Arms straight forward** - Tests shoulder/chest blend
3. **Deep squat** - Tests hip/knee deformation
4. **Full arm twist (180 deg)** - Tests candy-wrapper
5. **Head turn (90 deg)** - Tests neck deformation
6. **Walk cycle** - Tests all joints in motion
7. **Run cycle** - Tests extreme ranges
8. **Sitting cross-legged** - Tests hip/leg clipping

---

## Section 5: Alternative Approaches

### When Meshy Isn't Enough

Meshy rigs are sufficient for previs and background characters. For hero characters and production animation, use one of these alternatives:

### Tool Comparison

| Tool | Cost | Time/Char | Quality | Stylized Support | Animation Library | Best For |
|------|------|-----------|---------|-----------------|-------------------|----------|
| **AccuRIG 2** | Free | ~10 min | Better | Good | 4,500+ | Our hero characters |
| **Mixamo** | Free | ~5 min | Good | Limited | 2,500+ | Quick + animations |
| **Rigify** | Free | 2-8 hrs | Best | Flexible | None | Full custom rigs |
| **Auto-Rig Pro** | $40 | 1-4 hrs | Best | Flexible | None | Blender power users |
| **Cascadeur** | Free (indie) | ~15 min | Good | Good | AI-generated | Physics animation |
| **CloudRig** | Free | 2-6 hrs | Best | Flexible | None | Blender Studio users |

### AccuRIG 2 (Recommended for Hero Characters)

**Why**: Free, handles big heads and exaggerated proportions well, 4,500+ motion library, better weight painting than Mixamo.

**Workflow:**
1. Download AccuRIG 2 from reallusion.com (free)
2. Import your 3D model
3. Place 5 joint markers (hip, shoulders, ankles)
4. AccuRIG auto-generates skeleton + weights
5. Apply animations from motion library
6. Export as FBX
7. Import to Blender for cleanup (Section 3)

**Handles our characters well because:**
- Mia/Leo (kids): AccuRIG handles child proportions
- Ruben (fairy wings): Can add extra bones after auto-rig
- Jetplane (quadruped): AccuRIG supports quadrupeds natively

### Mixamo (Best for Quick Prototyping)

**Why**: Free, instant results, massive animation library, industry-standard bone naming.

**Workflow:**
1. Go to mixamo.com
2. Upload OBJ/FBX model
3. Place markers on chin, wrists, elbows, knees, groin
4. Auto-rig generates in seconds
5. Browse 2,500+ animations, apply to character
6. Download FBX (with skin, 30 fps)
7. Import to Blender

**Limitations:**
- Stalled development (Adobe hasn't updated meaningfully)
- Humanoid-only (no quadrupeds)
- Limited stylized support (may struggle with exaggerated proportions)
- Shoulder/hip artifacts in extreme poses

### Rigify (Best for Custom Production Rigs)

**Why**: Free, built into Blender, generates full production rig with FK/IK switching, the most flexible option.

**Workflow:**
1. Add > Armature > Human (metarig)
2. In Edit mode, scale and position each metarig bone to match character
3. Armature Properties > Generate Rig
4. Parent mesh to generated rig (Ctrl+P > Armature Deform > Automatic Weights)
5. Fix weight painting in Weight Paint mode
6. Test with poses

**Time investment:** 2-8 hours per character, but produces the highest quality rig.

**When to use Rigify:**
- Character needs complex controls (Ruben with wings, Jetplane with tail)
- Auto-rigs consistently fail for a specific character
- Need custom FK/IK switching, space switching, or bendy bones
- Long-term investment (rig will be reused across many scenes)

### Auto-Rig Pro ($40 Blender Addon)

**Why**: Better UX than Rigify (9/10 vs 5/10), includes retargeting, game export presets, bendy bones.

**When to consider:** If Rigify's learning curve is too steep, or if you need game engine export features.

### Cascadeur (Physics-Based Animation)

**Why**: AI-powered posing, physics-based animation, supports quadrupeds (since 2025.3).

**When to consider:** For Jetplane (quadruped with physics-based movement), or when animation quality matters more than rig complexity.

### Hybrid Approach (Recommended for This Project)

```
Model Generation: Tripo AI or Meshy
         |
         v
Auto-Rigging: AccuRIG 2 (hero chars) or Mixamo (supporting chars)
         |
         v
Blender Import: FBX import
         |
         v
Cleanup: Fix weights, add IK, add rotation limits
         |
         v
Facial (hero only): Bone-based jaw/eye + key shape keys
         |
         v
Animation: Mixamo library + custom keyframes
         |
         v
Secondary Motion: Bone chains with spring physics (hair, cloth)
         |
         v
Export: FBX for production, GLB for web preview
```

### Time Estimates

| Approach | Time/Character | Quality Level | Best For |
|----------|---------------|--------------|----------|
| Auto-rig only | 5-15 min | 60-75% | Background extras, previs |
| Auto-rig + basic cleanup | 1-2 hrs | 80-90% | Supporting characters |
| Auto-rig + full polish | 4-8 hrs | 95%+ | Hero characters |
| Manual rig (Rigify) | 8-40 hrs | 100% custom | When auto-rig fails |

**Project total estimate (6 characters):**
- Hero chars (Mia, Leo, Ruben, Jetplane): 4-8 hrs each = 16-32 hrs
- Supporting chars (Gabe, Nina): 1-2 hrs each = 2-4 hrs
- **Total: 18-36 hours**

---

## Section 6: Troubleshooting

### Arm-Through-Leg/Torso Clipping

**Cause:** Weight painting bleeds across body parts. Upper arm vertices have influence from chest/spine bones, or thigh vertices bleed to opposite leg.

**Fix:**
1. Put rig in the problem pose (arm raised or leg bent)
2. Enter Weight Paint mode
3. Select the problematic bone's vertex group
4. Use Subtract brush (hold Ctrl) to remove influence from wrong areas
5. Use Blur brush (Shift) to smooth transitions
6. Test pose again

**Prevention:** Add Limit Rotation constraints to prevent joints from exceeding anatomical ranges. Test with extreme poses during rig QA.

### Stiff Torso / No Counter-Rotation

**Cause:** Too few spine bones (1-2) or spine bones don't distribute rotation.

**Fix:**
1. Ensure 3-4 spine bones minimum (Spine, Spine1, Spine2/Chest)
2. Add Copy Rotation constraint to upper spine that copies -30% of hip Y rotation (counter-rotation during walking)
3. For Rigify rigs: use the built-in torso FK/IK controls

### Static Hair

**Cause:** Hair mesh weighted entirely to head bone, no secondary motion.

**Fix (bone chain approach):**
1. Add bone chain following each major hair clump (4-6 bones per strand)
2. Parent to head bone
3. Weight paint hair mesh to chain bones
4. Add spring/jiggle constraint or addon for automated follow-through

**Fix (physics approach):**
1. Separate hair as its own mesh
2. Add Cloth physics with pin group at scalp
3. Add Collision to body mesh
4. Bake simulation before rendering

### Foot Sliding

**Cause:** Feet animated in FK without ground contact locking.

**Fix:**
1. Use IK on legs with foot target at fixed world-space position during contact
2. Implement reverse foot setup: heel pivot > ball pivot > toe pivot bone chain
3. Keyframe IK target to stay planted during contact phase

**Quick fix:** In Graph Editor, select foot bone Y position keyframes and flatten them to 0 during contact phase.

### Candy-Wrapper Effect at Forearms

**Cause:** Single bone twisted too far. Linear Blend Skinning can't preserve volume during twist.

**Fix options:**
1. **Twist bones** (best): Add 2-4 extra bones along forearm, each copying a fraction of hand twist
2. **Dual Quaternion skinning**: Enable "Preserve Volume" on Armature modifier (may cause bulging elsewhere)
3. **Corrective shape keys**: Sculpt corrections that activate at specific twist angles

### Joints Pinching or Folding

**Cause:** Too sharp a weight gradient between adjacent bones.

**Fix:**
1. Select the joint area in Weight Paint mode
2. Use Blur brush (Shift) extensively to smooth the transition
3. For stubborn areas, manually paint a broader gradient
4. Test at 50% and 100% bend angles

### Mesh Spikes/Flying Vertices

**Cause:** A few vertices assigned to the wrong bone, or unweighted vertices (weight = 0 for all bones).

**Fix:**
1. Pose the rig -- spikes will reveal problem vertices
2. In Weight Paint mode, identify which bone group they belong to
3. Use Subtract brush to remove wrong influence
4. Use Draw brush to assign correct bone influence
5. Verify: Weights menu > Normalize All

### Export Problems

**FBX import shows no animation:**
- Ensure "Bake Animation" is enabled during export
- Check that animations are on the correct armature (not on an action strip)
- Try unchecking "Add Leaf Bones" in FBX export

**GLB shows deformed mesh:**
- GLB doesn't support all Blender features (bendy bones, custom constraints)
- Bake all constraints to keyframes before GLB export
- Use "Apply Modifiers" option

**Bone names mangled on import:**
- Some tools rename bones on export (adding prefixes/suffixes)
- Use Blender's search-and-replace on bone names
- Or use the script: `scripts/rigging_pipeline.py` which handles common renames

**Scale issues:**
- Different tools use different scale units (Blender = 1m, some tools = 1cm)
- On FBX import: try "Automatic" or manual scale (0.01 for cm-based models)
- Apply scale after import: Ctrl+A > Scale

---

## Section 7: Character-Specific Notes

### Mia (8-year-old daughter)

| Setting | Value |
|---------|-------|
| Height | ~1.2m |
| Body type | Child proportions (large head relative to body) |
| Rig method | AccuRIG 2 (handles child proportions) |
| Target bones | ~120 |
| Special needs | Facial rig (expressions are key for storytelling) |
| Hair | Long -- needs bone chain (6-8 bones) |
| Priority | Hero character, full cleanup |

### Leo (5-year-old son)

| Setting | Value |
|---------|-------|
| Height | ~1.0m |
| Body type | Toddler proportions (very large head) |
| Rig method | AccuRIG 2 |
| Target bones | ~120 |
| Special needs | Dinosaur pajamas (cloth sim or baked), plush T-Rex toy (separate rig) |
| Hair | Short -- head bone only |
| Priority | Hero character, full cleanup |

### Ruben (fairy godfather)

| Setting | Value |
|---------|-------|
| Height | ~1.75m (but with wings extending further) |
| Body type | Adult with fairy wings |
| Rig method | AccuRIG 2 + manual wing bones |
| Target bones | ~150 (extra for wings) |
| Special needs | Wings need separate bone chains (8-12 bones per wing), magical effects |
| Hair/accessories | Possible hat/crown |
| Priority | Hero character, full cleanup + custom wing rig |

### Jetplane (color-farting dinosaur)

| Setting | Value |
|---------|-------|
| Height | ~1.5m at shoulder |
| Body type | Quadruped dinosaur |
| Rig method | AccuRIG 2 (quadruped mode) or Cascadeur |
| Target bones | ~100 |
| Special needs | Tail (5-7 FK bones), jaw for expressions, unique body proportions |
| Hair/accessories | None |
| Priority | Hero character, quadruped pipeline |

### Gabe (dad)

| Setting | Value |
|---------|-------|
| Height | ~1.8m |
| Body type | Adult male, stocky, soft around middle |
| Rig method | Mixamo (sufficient for supporting role) |
| Target bones | ~65 |
| Special needs | Glasses (separate object parented to head bone) |
| Hair | Short -- head bone only |
| Priority | Supporting, basic cleanup only |

### Nina (mom)

| Setting | Value |
|---------|-------|
| Height | ~1.7m |
| Body type | Adult female, elegant |
| Rig method | Mixamo |
| Target bones | ~65 |
| Special needs | Auburn wavy hair (needs bone chain, 4-6 bones), earrings |
| Hair | Wavy past shoulders -- needs bone chain |
| Priority | Supporting, basic cleanup + hair bones |

---

## Section 8: Quick Reference

### Blender Rigging Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+P | Parent mesh to armature |
| Ctrl+Tab | Toggle Weight Paint mode |
| Alt+R | Clear rotation (reset pose) |
| Alt+G | Clear location |
| Shift+I | Add IK constraint interactively |
| X | Enable mirror in Weight Paint |
| Ctrl (in Weight Paint) | Subtract brush |
| Shift (in Weight Paint) | Blur/smooth brush |

### Weight Painting Quick Fixes

```
Normalize All:      Mesh selected > Weight Paint > Weights > Normalize All
Limit Total:        Mesh selected > Weight Paint > Weights > Limit Total (4)
Auto Weights:       Select mesh + armature > Ctrl+P > Armature Deform > Auto Weights
Mirror Weights:     Weight Paint > Weights > Mirror
Clean Zero Groups:  Object mode > Clean Vertex Group Weights (limit=0.01)
```

### Pipeline Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/rig_quality_checker.py` | Validate rig quality | `blender --background --python scripts/rig_quality_checker.py -- model.fbx` |
| `scripts/rigging_pipeline.py` | Automated rigging pipeline | `blender --background --python scripts/rigging_pipeline.py -- --model char.glb --character mia` |

### Decision Flowchart

```
Is this a hero character? (Mia, Leo, Ruben, Jetplane)
  |
  YES --> Use AccuRIG 2 for auto-rig
  |         |
  |         v
  |       Import FBX to Blender
  |         |
  |         v
  |       Run rig_quality_checker.py
  |         |
  |         v
  |       Fix weights at shoulders/hips
  |         |
  |         v
  |       Add IK + rotation limits
  |         |
  |         v
  |       Add facial controls (bone-based)
  |         |
  |         v
  |       Add secondary motion (hair/cloth)
  |         |
  |         v
  |       Export production FBX
  |
  NO --> Is this a supporting character? (Gabe, Nina)
    |
    YES --> Use Mixamo for auto-rig
    |         |
    |         v
    |       Import FBX to Blender
    |         |
    |         v
    |       Basic weight fixes only
    |         |
    |         v
    |       Export FBX
    |
    NO --> Background character
      |
      v
    Meshy auto-rig is sufficient
      |
      v
    Quick weight check, export as-is
```

### Key File Locations

```
docs/guides/character-rigging-production-guide.md  -- This guide
docs/research/3d-model-generation.md               -- Tool comparison
scripts/rig_quality_checker.py                     -- Automated QA
scripts/rigging_pipeline.py                        -- Automated pipeline
scripts/meshy_retexture.py                         -- Meshy API integration
assets/characters/{name}/turnaround.md             -- Per-character design specs
```

---

## Sources

- Meshy API Documentation: docs.meshy.ai
- Meshy Animation Features: meshy.ai/features/ai-animation-generator
- Blender Rigging Manual: docs.blender.org/manual
- AccuRIG 2: reallusion.com/auto-rig/accurig
- Mixamo: mixamo.com
- Rigify Documentation: docs.blender.org/manual/en/latest/addons/rigging/rigify.html
- Pixar Rigging Pipeline: sciencebehindpixar.org/pipeline/rigging
- Pixar CurveNet: cghero.com/articles/new-pixar-rigging-system-curvenet
- Disney Animation Rigging: disneyanimation.com/process/rigging
- CloudRig: extensions.blender.org/add-ons/cloudrig
- Cascadeur: cascadeur.com
- Tripo AI Auto-Rigging: tripo3d.ai/features/ai-auto-rigging
