# Blender Scene Assembly Workflow

This document describes the workflow for assembling production scenes in Blender for the "Fairy Dinosaur Date Night" animated movie.

## Overview

Scene assembly is the process of bringing together characters, environments, lighting, and camera to create a shot that matches the storyboard. This workflow can be executed:

1. **Interactively via BlenderMCP** - For real-time scene building and iteration
2. **Headless batch mode** - For automated rendering

## Quick Start

### Test the workflow

```bash
# Run the test render
blender -b -P scripts/render_scene_assembly_test.py
```

This creates a test render at `renders/test/scene_assembly_test.png` with placeholder characters.

### Use in BlenderMCP

```python
# Import the module
import scene_assembly as sa

# Assemble a test scene
sa.assemble_test_scene()

# Or build a custom scene
sa.assemble_scene_from_storyboard(
    scene_name="act1_scene1",
    character_positions={
        'Mia': (-1, 1.5, 0),
        'Leo': (0.5, 1.5, 0),
    },
    camera_settings={
        'location': (0, -5, 2),
        'rotation_deg': (75, 0, 0),
        'lens': 35
    },
    lighting_type='interior'
)
```

## Workflow Steps

### 1. Clear Scene

Always start with a clean scene to avoid conflicts with existing objects.

```python
sa.clear_scene()
```

### 2. Set Up Environment

Create the ground plane and world background:

```python
# Ground plane
sa.create_ground_plane(size=10, color=(0.3, 0.5, 0.25, 1.0))

# Sky background (for outdoor scenes)
sa.setup_world_sky(sun_elevation=30, sun_rotation=45)

# Or import an environment reference image
sa.import_environment_reference('assets/environments/jurassic_landscape/jurassic_landscape_swamp_wide.png')
```

### 3. Add Characters

Use placeholder characters for scene blocking, then replace with actual models:

```python
# Placeholders for blocking
mia = sa.create_placeholder_character('Mia', location=(-1, 0.5, 0))
leo = sa.create_placeholder_character('Leo', location=(1, 0.5, 0))

# Or import actual character models
# sa.import_character_model('Mia', 'models/characters/mia.blend', location=(-1, 0.5, 0))
```

**Available Characters:**
| Name | Color | Height | Description |
|------|-------|--------|-------------|
| Mia | Blue | 1.2m | 8-year-old protagonist |
| Leo | Green | 1.0m | 5-year-old protagonist |
| Gabe | Dark Gray | 1.85m | Dad |
| Nina | Maroon | 1.7m | Mom |
| Ruben | Purple | 0.6m | Fairy godfather |
| Jetplane | Orange | 2.0m | Dinosaur |

### 4. Set Up Lighting

Choose a lighting setup based on the scene type:

```python
# Three-point lighting (standard, good for most shots)
sa.setup_three_point_lighting(key_energy=500, fill_energy=200, rim_energy=300)

# Interior lighting (warm, for home scenes)
sa.setup_interior_lighting(warmth=0.9)
```

**Lighting Components:**
- **Key Light**: Main light source, warm white, front-right
- **Fill Light**: Softer fill, slightly cool, front-left
- **Rim Light**: Edge definition, golden, behind subjects
- **Sun Ambient**: Overall ambient fill

### 5. Configure Camera

Set up the camera to match the storyboard:

```python
# Using target point
sa.setup_camera(location=(5, -5, 3), target=(0, 0, 1), lens=35)

# Or explicit rotation
sa.setup_camera_simple(location=(5, -5, 3), rotation_deg=(70, 0, 45), lens=35)
```

**Common Focal Lengths:**
| Lens | Use Case |
|------|----------|
| 24mm | Wide establishing shots |
| 35mm | Standard medium shots |
| 50mm | Portrait/close-ups |
| 85mm | Tight close-ups |

### 6. Configure Render

Set up render settings:

```python
sa.configure_render(
    output_dir='renders/scene01',
    resolution=(1920, 1080),
    samples=64,
    preview=False,  # True for quick previews
    engine='CYCLES'  # or 'BLENDER_EEVEE'
)
```

### 7. Render

```python
# Single frame
bpy.ops.render.render(write_still=True)

# Animation
bpy.ops.render.render(animation=True)
```

## Production Scene Example

Here's a complete example for Scene 01 (family living room):

```python
import scene_assembly as sa

# Build the scene
sa.assemble_scene_from_storyboard(
    scene_name="scene01_living_room",
    character_positions={
        'Mia': (-0.5, 1.5, 0.45),    # Sitting on couch
        'Leo': (0.5, 1.5, 0.45),     # Sitting on couch
        'Gabe': (2.0, 2.0, 0),       # Standing
        'Nina': (1.5, 0.5, 0),       # Standing
    },
    camera_settings={
        'location': (0, -4, 1.5),
        'rotation_deg': (75, 0, 0),
        'lens': 35
    },
    lighting_type='interior',
    env_image='assets/environments/bornsztein_home/bornsztein_home_living_room.png'
)

# Render
import bpy
bpy.ops.render.render(write_still=True)
```

## File Structure

```
scripts/
├── scene_assembly.py          # Main assembly module
├── render_scene_assembly_test.py  # Test script
├── render_scene01_home_evening.py # Production scene example
scenes/
├── scene_assembly_test.blend  # Saved test scene
renders/
├── test/
│   └── scene_assembly_test.png
```

## BlenderMCP Integration

When using BlenderMCP interactively:

1. Ensure BlenderMCP server is running (see `scripts/start_blender_mcp.sh`)
2. Use MCP tools to execute scene_assembly functions
3. Use `get_viewport_screenshot` to preview without full render
4. Use `execute_blender_code` to run assembly functions

Example MCP workflow:
```
1. mcp__blender__execute_blender_code: "import scene_assembly as sa; sa.assemble_test_scene()"
2. mcp__blender__get_viewport_screenshot: Preview the result
3. mcp__blender__execute_blender_code: "bpy.ops.render.render(write_still=True)"
```

## Troubleshooting

### Render times out via MCP
Use headless batch rendering instead:
```bash
blender -b -P scripts/render_scene_assembly_test.py
```

### Characters not visible
- Check camera location and rotation
- Verify character locations are within camera view
- Ensure lighting is properly configured

### GPU not detected
The script automatically falls back to CPU rendering. To force GPU:
```python
bpy.context.scene.cycles.device = 'GPU'
```

## Next Steps

1. Replace placeholder characters with AI-generated models from Tripo/Meshy/Rodin
2. Add environment geometry (walls, furniture, props)
3. Set up camera animation for each shot
4. Add character animations
