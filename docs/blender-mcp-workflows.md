# BlenderMCP Workflow Examples

This document provides example workflows for using BlenderMCP with Claude to create 3D scenes for "Fairy Dinosaur Date Night".

## Prerequisites

Before running these workflows:
1. Start the Blender MCP server (see [setup guide](./blender-mcp-setup.md))
2. Ensure Claude Code has MCP tools enabled (check `.mcp.json` is present)

## Workflow 1: Basic Scene Setup

### Goal
Create a simple scene with a ground plane, basic lighting, and camera.

### Claude Prompts

```
1. "Get the current Blender scene info"

2. "Create a ground plane at (0, 0, 0) with size 20"

3. "Create a sun light at position (5, -5, 10) with energy 3"

4. "Create a camera at position (6, -6, 4) looking at the origin"

5. "Take a screenshot of the current viewport"
```

### Expected Result
- A flat ground plane
- Directional lighting from the sun
- Camera positioned to view the scene

---

## Workflow 2: Character Placeholder

### Goal
Create a simple character placeholder for scene blocking.

### Claude Prompts

```
1. "Create a cylinder at (0, 0, 0.75) with radius 0.5 and depth 1.5 - this is the body"

2. "Create a sphere at (0, 0, 2) with radius 0.4 - this is the head"

3. "Set both objects to have an orange material"

4. "Group these objects into a collection called 'CharacterPlaceholder'"
```

### Expected Result
- Simple capsule-shaped character placeholder
- Orange colored for visibility
- Organized in a collection

---

## Workflow 3: Environment Building (Jurassic Forest)

### Goal
Create a prehistoric forest environment for the movie setting.

### Claude Prompts

```
1. "Create a large green ground plane (30x30) with some roughness"

2. "Execute Blender code to create 10 simple trees at random positions:
   - Tree = brown cylinder trunk + green cone foliage
   - Scatter within 10 units of center"

3. "Add some large rocks using primitive shapes (scaled spheres/cubes)"

4. "Browse Poly Haven for tropical/forest HDRIs"

5. "Download a prehistoric-looking environment HDRI and apply it"

6. "Take a screenshot to preview the environment"
```

### Expected Result
- Green terrain with multiple trees
- Rocky elements for Jurassic feel
- Environmental lighting from HDRI

---

## Workflow 4: Iterative Scene Development

### Goal
Demonstrate the iterative feedback loop for scene refinement.

### Process

1. **Initial Creation**
   ```
   "Create a basic scene with a dinosaur placeholder (large scaled sphere body,
   smaller sphere head, cone tail)"
   ```

2. **Review**
   ```
   "Take a screenshot of the current scene"
   ```

3. **Refine Based on Feedback**
   ```
   "The dinosaur looks too round. Make the body more elongated by scaling
   the body sphere to (2, 1, 1)"
   ```

4. **Review Again**
   ```
   "Take another screenshot to see the changes"
   ```

5. **Continue Iterating**
   ```
   "Add small spheres for eyes and position them on the head"
   ```

This workflow demonstrates how BlenderMCP enables rapid iteration.

---

## Workflow 5: Material and Lighting Setup

### Goal
Create appealing materials and lighting for a shot.

### Claude Prompts

```
1. "Get info about all objects in the scene"

2. "Create a principled material named 'Jetplane_Skin' with:
   - Base color: Purple (#8B5CF6)
   - Roughness: 0.4
   - Subsurface: 0.2 (for skin-like appearance)"

3. "Apply 'Jetplane_Skin' material to the dinosaur body"

4. "Create a three-point lighting setup:
   - Key light (sun) from front-left
   - Fill light (area) from right
   - Rim light (spot) from behind"

5. "Adjust the key light energy until the scene looks well-lit"

6. "Take a screenshot to evaluate the lighting"
```

---

## Workflow 6: Asset Integration (Poly Haven)

### Goal
Import high-quality assets from Poly Haven.

### Claude Prompts

```
1. "Search Poly Haven for 'rock' assets"

2. "Download the first suitable rock model"

3. "Position the rock at (-3, 2, 0) and scale it to 2x"

4. "Search Poly Haven for 'grass' textures"

5. "Download a grass texture and apply it to the ground plane"

6. "Search Poly Haven for 'forest' HDRIs"

7. "Download and set a forest HDRI as the world background"
```

---

## Workflow 7: Animation Preparation

### Goal
Set up a scene for animation by creating keyframe-ready objects.

### Claude Prompts

```
1. "Create a sphere at (0, 0, 1) named 'AnimatedBall'"

2. "Execute Blender code to:
   - Set current frame to 1
   - Position ball at (0, 0, 1)
   - Insert location keyframe
   - Set frame to 30
   - Position ball at (5, 0, 1)
   - Insert location keyframe
   - Set frame to 60
   - Position ball at (5, 0, 3)
   - Insert location keyframe"

3. "Set the scene frame range to 1-60"

4. "Play back the animation and describe what happens"
```

---

## Workflow 8: Custom Python Execution

### Goal
Execute complex operations using custom Python code.

### Example: Create a Spiral of Objects

```
"Execute the following Blender Python code to create a spiral of cubes:

import bpy
import math

for i in range(20):
    angle = i * 0.5
    radius = 1 + i * 0.2
    x = math.cos(angle) * radius
    y = math.sin(angle) * radius
    z = i * 0.1

    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(x, y, z))
    cube = bpy.context.active_object
    cube.name = f'SpiralCube_{i}'
"
```

---

## Tips for Effective MCP Usage

### Do
- Start with simple shapes, then add detail
- Take frequent screenshots to validate progress
- Use collections to organize objects
- Save your work frequently (via Python: `bpy.ops.wm.save_mainfile()`)

### Don't
- Create too many objects at once (performance)
- Forget to name objects meaningfully
- Skip the review step between major changes

### Performance
- Complex operations may take longer
- Large asset downloads may timeout
- If a command fails, simply retry

### Debugging
- Use `get_blender_scene_info` to understand current state
- Use `get_object_info` to debug specific objects
- Execute Python code to print debug information

---

## Integration with Scripts

After developing a scene with MCP, you can export the workflow to Python:

1. Use `get_blender_scene_info` to capture the final state
2. Ask Claude to "Generate a Python script that recreates this scene"
3. Save the script to `scripts/` for reproducible renders
4. Run headless: `blender -b -P scripts/my_scene.py`

This bridges interactive development (MCP) with production rendering (scripts).
