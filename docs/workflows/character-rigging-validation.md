# Character Rigging & Validation Workflow

Repeatable process for rigging AI-generated characters to production quality.
Used for: Mia, Leo, Gabe, Nina, Ruben, Jetplane.

## Overview

```
Turnaround Sheet → Mesh Cleanup → Auto-Rig → Stress Test → Human Review → Fix → Repeat
                                                              ↑                    |
                                                              └────────────────────┘
```

The key insight: **automated QA cannot catch rigging problems**. A human must visually review stress test renders. This workflow uses the Rigging Review App as the quality gate.

---

## Prerequisites

- Blender 3.6+ installed
- Auto-Rig Pro ($40, Blender Market) - OR - AccuRIG 2 (free, Windows/Mac)
- Rigging Review App running: `cd scripts/rigging-review-app && ./start.sh`
- Character mesh (FBX/GLB from Tripo/Meshy/Rodin)

---

## Step 1: Mesh Preparation

Before rigging, clean up the AI-generated mesh. This is the most important step.

### In Blender:

1. **Import mesh** (File > Import > FBX/glTF)

2. **Check for issues:**
   - Select mesh > Edit Mode > Select All (A)
   - Mesh > Clean Up > Make Manifold
   - Mesh > Normals > Recalculate Outside
   - Check for floating parts: Select mesh > Edit Mode > L (select linked) - if parts highlight separately, they're disconnected

3. **Separate loose parts:**
   - Hair, hats, accessories should be separate objects
   - Select floating geometry > P (Separate) > Selection
   - Name them clearly: `Mia_Hair`, `Mia_Body`, etc.

4. **Reduce poly count for rigging:**
   - Target: 20k-30k tris for body mesh
   - Modifier > Decimate > Ratio (adjust until ~25k)
   - Apply modifier
   - Keep original as backup (duplicate before decimating)

5. **Fix topology at joints (if needed):**
   - If deformation is bad after rigging, consider Remesh:
   - Modifier > Remesh > Voxel > Size ~0.01 > Apply
   - WARNING: This destroys UVs - retexture needed after

### Script helper:
```bash
blender character.blend --background --python scripts/blender/mesh_cleanup.py
```

---

## Step 2: Rigging

### Decision Tree

```
Is the character humanoid?
├── YES
│   ├── Do you have Blender + Auto-Rig Pro?
│   │   ├── YES → Use Auto-Rig Pro (Step 2A)
│   │   └── NO → Use AccuRIG 2 (Step 2B) or Mixamo (Step 2C)
│   └── Is the mesh very messy (high tri, no edge loops)?
│       └── YES → Use Auto-Rig Pro Voxelize mode
└── NO (Jetplane, etc.)
    └── Use Rigify custom template (Step 2D)
```

### Step 2A: Auto-Rig Pro (Recommended for humanoids)

1. Open character in Blender
2. `3D View > Sidebar > ARP > Smart`
3. Click reference points: neck, chin, wrists, ankles, hips
4. For problematic AI meshes: enable **"Voxelize"** in Smart options
5. Click **"OK"** to generate rig
6. Adjust if needed: move bones that aren't centered in limbs
7. Click **"Match to Rig"** to bind mesh to skeleton
8. Test basic poses in Pose Mode

### Step 2B: AccuRIG 2 (Free alternative, Windows/Mac only)

1. Open AccuRIG 2
2. Import FBX mesh
3. Place guide markers (5-7 points)
4. Generate rig
5. Adjust weights if needed
6. Export as FBX
7. Import FBX into Blender

### Step 2C: Mixamo (Quick but limited)

1. Go to mixamo.com
2. Upload FBX (must be < 100k tris)
3. Place guide markers
4. Download rigged FBX
5. Import into Blender
6. NOTE: No facial rig, poor with non-standard proportions

### Step 2D: Rigify (Non-humanoid characters)

1. Add metarig: Add > Armature > (choose template)
2. Scale/position bones to fit mesh
3. Add custom bones for unique parts (tail, wings)
4. Generate rig
5. Weight paint manually (most work-intensive)

---

## Step 3: Attach Accessories

For hair, hats, and other accessories that should NOT deform with the body:

1. Select the accessory object
2. Select the armature (Shift+click)
3. Ctrl+P > Bone (pick the parent bone, e.g. "Head" for hair)
4. The accessory will now follow the bone rigidly, no weight painting

For accessories that need SOME deformation (scarves, capes):
- Parent to armature with automatic weights
- Weight paint to limit influence to nearby bones

---

## Step 4: Stress Test Renders

### Run the automated stress test:

```bash
blender character.blend --background --python scripts/rigging-review-app/stress_test_poses.py -- \
    --output ./stress_renders/ \
    --character "Mia" \
    --tool "Auto-Rig Pro" \
    --notes "v1 - initial rig, no weight adjustments" \
    --upload http://rex:3090
```

This renders 8 stress poses from 2 angles (16 images) and uploads them to the review app.

### If Blender is not available headlessly:

1. Open the .blend file
2. Run the script from Blender's text editor
3. Or manually pose and render each stress pose

### The 8 Stress Test Poses

| # | Pose | What It Tests |
|---|------|---------------|
| 1 | T-Pose | Baseline mesh quality |
| 2 | Deep Squat | Hip/thigh weights, knee deformation |
| 3 | Arms Overhead | Shoulder weights, armpit deformation |
| 4 | Arms Behind Back | Shoulder/chest clipping |
| 5 | Spine Twist 90deg | Torso deformation, waist |
| 6 | Extreme Head Turn | Neck weights, hair deformation |
| 7 | Walk Extreme | Overall locomotion deformation |
| 8 | Full Bend Forward | Spine chain, belly, back stretch |

---

## Step 5: Human Review

1. Open the review app: `http://rex:3090`
2. Click on the character
3. For each pose render:
   - **Approve** if deformation looks acceptable
   - **Reject** if there are visible issues
   - **Add feedback** describing the specific problem (e.g. "left shoulder clips through chest", "hair stretches when head turns")
4. After reviewing all poses, the agent can check feedback via API

### Agent reads feedback:

```bash
# Get latest iteration status
curl http://rex:3090/api/summary

# Get specific pose feedback
curl http://rex:3090/api/iterations/{iteration_id}/poses
```

---

## Step 6: Fix Issues

Based on review feedback, apply fixes:

### Common Issues and Fixes

| Feedback | Cause | Fix |
|----------|-------|-----|
| "Hair stretches/distorts" | Hair weighted to body bones | Separate hair object, parent to head bone (rigid) |
| "Shoulder clips through chest" | Upper arm weights too wide | Weight paint: reduce influence of upper_arm bone on chest verts |
| "Knee/elbow sharp crease" | No interpolation at joint | Add more edge loops at joint OR adjust weight gradient |
| "Waist collapses on twist" | Spine weights too abrupt | Smooth weight transition between spine bones |
| "Mesh pokes through itself" | Self-intersection | Move bones to better center of limb, or shrinkwrap modifier |
| "Fingers/toes deform badly" | Wrong bone assignments | Manually weight paint finger/toe vertices |
| "Accessories float away" | Parented to wrong bone | Re-parent to correct bone |
| "Arms don't reach full range" | IK limits too tight | Adjust IK constraints in armature |

### Weight Painting Tips

1. Select mesh, go to Weight Paint mode
2. Select a bone (Ctrl+click in weight paint mode)
3. Blue = no influence, Red = full influence
4. Paint with Subtract brush to remove unwanted influence
5. Paint with Add brush to add influence
6. Use Smooth brush to blend transitions
7. Check "Auto Normalize" to keep total weights = 1.0

---

## Step 7: Re-test

After fixing, run stress tests again:

```bash
blender character.blend --background --python scripts/rigging-review-app/stress_test_poses.py -- \
    --output ./stress_renders_v2/ \
    --character "Mia" \
    --tool "Auto-Rig Pro" \
    --notes "v2 - fixed hair (rigid parent), smoothed shoulder weights" \
    --upload http://rex:3090
```

The app tracks iterations, so the reviewer can compare v1 vs v2.

**Repeat Steps 5-7 until all poses are approved.**

---

## Step 8: Add Animations

Once the rig passes stress tests:

1. **From Mixamo:**
   - Download FBX animations from mixamo.com
   - In Blender: File > Import > FBX (animation only)
   - Use Auto-Rig Pro Remap to retarget onto your rig

2. **From library:**
   - Apply animation actions from .blend library files

3. **Custom:**
   - Keyframe in Blender's pose mode

---

## Quick Reference

### Start review app:
```bash
cd scripts/rigging-review-app && ./start.sh
```

### Run stress tests:
```bash
blender model.blend --background --python scripts/rigging-review-app/stress_test_poses.py -- \
    --output ./renders/ --character "Name" --tool "Tool" --upload http://rex:3090
```

### Upload manually via API:
```bash
curl -X POST http://rex:3090/api/bulk-upload \
    -F "character_name=Mia" \
    -F "rigging_tool=Auto-Rig Pro" \
    -F "notes=description of changes" \
    -F "pose_names=t_pose,deep_squat,arms_overhead" \
    -F "images=@t_pose.png" \
    -F "images=@deep_squat.png" \
    -F "images=@arms_overhead.png"
```

### Check review status:
```bash
curl http://rex:3090/api/summary
```

---

## Character Checklist

Use this for each character:

- [ ] Mesh imported and cleaned
- [ ] Loose parts separated (hair, accessories)
- [ ] Rigged (note tool used: _____________)
- [ ] Hair/accessories attached correctly
- [ ] Stress test v1 uploaded to review app
- [ ] Human review complete
- [ ] Issues fixed (list iterations)
- [ ] All stress poses approved
- [ ] Walking animation tested
- [ ] Character saved as production .blend
- [ ] .blend uploaded to R2

### Per-Character Status

| Character | Mesh | Rig | Stress Test | Approved | Animated |
|-----------|------|-----|-------------|----------|----------|
| Mia       | [ ]  | [ ] | [ ]         | [ ]      | [ ]      |
| Leo       | [ ]  | [ ] | [ ]         | [ ]      | [ ]      |
| Gabe      | [ ]  | [ ] | [ ]         | [ ]      | [ ]      |
| Nina      | [ ]  | [ ] | [ ]         | [ ]      | [ ]      |
| Ruben     | [ ]  | [ ] | [ ]         | [ ]      | [ ]      |
| Jetplane  | [ ]  | [ ] | [ ]         | [ ]      | [ ]      |
