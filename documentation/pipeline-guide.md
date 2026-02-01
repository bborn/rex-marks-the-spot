# Blender Automation Pipeline Guide

This document describes the LLM-controlled Blender automation pipeline for the "Fairy Dinosaur Date Night" animated movie project.

## Overview

The pipeline enables Claude to:
- Create and modify 3D objects in Blender
- Set up scenes with lighting, cameras, and materials
- Render frames headlessly (no GUI required)
- Validate rendered output using Claude Vision
- Iterate based on feedback to refine scenes

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PIPELINE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────────┐   │
│  │    Claude    │───▶│   Pipeline  │───▶│  Blender (CLI)   │   │
│  │   (Opus)     │    │  Orchestrator│    │  (headless)      │   │
│  └──────────────┘    └──────┬──────┘    └────────┬─────────┘   │
│         ▲                    │                    │              │
│         │                    ▼                    ▼              │
│         │           ┌─────────────┐      ┌─────────────┐        │
│         └───────────│  Validator  │◀─────│  Rendered   │        │
│                     │  (Vision)   │      │   Image     │        │
│                     └─────────────┘      └─────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
scripts/
├── blender/           # Blender Python modules (run inside Blender)
│   ├── __init__.py
│   ├── scene.py       # Scene setup and management
│   ├── objects.py     # Object creation and manipulation
│   ├── materials.py   # Material and shader utilities
│   ├── lighting.py    # Lighting setup helpers
│   ├── camera.py      # Camera positioning and animation
│   └── render.py      # Render configuration
│
├── render/            # Render pipeline (run outside Blender)
│   ├── __init__.py
│   ├── engine.py      # Headless render engine controller
│   └── batch.py       # Batch rendering support
│
├── validate/          # Vision validation (run outside Blender)
│   ├── __init__.py
│   └── vision.py      # Claude Vision integration
│
├── pipeline.py        # Main orchestration script
├── poc_create_scene.py    # Proof of concept: scene creation
└── poc_validation_loop.py # Proof of concept: validation loop
```

## Installation

### Prerequisites

1. **Blender 3.0+** - Install from [blender.org](https://www.blender.org/download/)
   ```bash
   # Verify installation
   blender --version
   ```

2. **Python 3.10+** with required packages:
   ```bash
   pip install anthropic
   ```

3. **Environment Variables**:
   ```bash
   # Required for vision validation
   export ANTHROPIC_API_KEY="your-api-key"

   # Optional: custom Blender path
   export BLENDER_PATH="/path/to/blender"
   ```

### Linux Dependencies (Headless Rendering)

```bash
# Debian/Ubuntu
sudo apt install libxrender1 libxxf86vm1 libxfixes3 libxi6 libsm6 libgl1 libxkbcommon0 libegl1 mesa-utils

# RHEL/Fedora
sudo dnf install libXrender libXxf86vm libXfixes libXi libSM libGL libxkbcommon libEGL mesa-dri-drivers
```

## Quick Start

### 1. Check Pipeline Status

```bash
python scripts/pipeline.py --check
```

### 2. Simple Scene Render

```bash
python scripts/pipeline.py \
  --scene "A forest scene with trees and an orange character" \
  --output-dir ./renders \
  --samples 64
```

### 3. Render with Validation

```bash
python scripts/pipeline.py \
  --scene "A character standing on green grass with blue sky" \
  --validate
```

### 4. Iterative Improvement Loop

```bash
python scripts/pipeline.py \
  --scene "A detailed forest environment" \
  --iterate \
  --max-iterations 3
```

## Module Reference

### Blender Modules (`scripts/blender/`)

These modules run **inside Blender** and provide the Python API for scene manipulation.

#### scene.py

```python
from blender import scene

# Clear all objects
scene.clear()

# Set up gradient sky
scene.setup_sky_gradient(
    horizon_color=(0.5, 0.7, 1.0, 1.0),
    zenith_color=(0.1, 0.3, 0.8, 1.0)
)

# Create collection for organization
scene.create_collection("Characters")

# Get scene info
info = scene.get_scene_info()
```

#### objects.py

```python
from blender import objects

# Primitives
cube = objects.create_cube("MyCube", size=2.0, location=(0, 0, 1))
sphere = objects.create_sphere("MySphere", radius=1.0)

# Compound objects
ground = objects.create_ground(size=20, color=(0.2, 0.5, 0.2, 1.0))
character = objects.create_character_placeholder("Hero", height=2.0)
tree = objects.create_simple_tree("Tree1", height=3.0, location=(5, 3, 0))

# Transforms
objects.transform(cube, location=(1, 2, 3), rotation=(0, 0, 45))

# Modifiers
objects.add_subdivision(cube, levels=2)
objects.add_bevel(cube, width=0.05)
```

#### materials.py

```python
from blender import materials

# Create materials
mat = materials.create_principled(
    "CharacterMat",
    color=(0.8, 0.4, 0.2, 1.0),
    roughness=0.5,
    metallic=0.0
)

glass = materials.create_glass("GlassMat", roughness=0.1)
metal = materials.create_metal("MetalMat", color=(0.9, 0.9, 0.9, 1.0))
glow = materials.create_emission("GlowMat", strength=5.0)

# Assign to objects
materials.assign(my_object, mat)

# Add textures
materials.add_texture_node(mat, "/path/to/texture.png", "Base Color")
materials.add_normal_map(mat, "/path/to/normal.png", strength=1.0)
```

#### lighting.py

```python
from blender import lighting

# Standard setups
key, fill, rim = lighting.three_point_setup(target=(0, 0, 1))
key, left, right = lighting.studio_setup()
sun, world = lighting.outdoor_daylight(time_of_day="morning")

# Custom lights
point = lighting.create_point_light("Point", location=(0, 0, 5), energy=1000)
spot = lighting.create_spot_light("Spot", location=(5, -5, 5), target=(0, 0, 0))
area = lighting.create_area_light("Area", size=3.0, energy=500)
```

#### camera.py

```python
from blender import camera

# Set up main camera
cam = camera.setup_main(
    location=(7, -7, 5),
    target=(0, 0, 1),
    focal_length=50
)

# Camera animations
camera.add_keyframe(cam, frame=1, location=(10, -10, 5))
camera.add_keyframe(cam, frame=120, location=(0, -10, 5))

# Orbit animation
camera.create_orbit_animation(
    cam,
    center=(0, 0, 1),
    radius=10,
    start_frame=1,
    end_frame=240
)

# Depth of field
camera.set_dof(cam, focus_object="Character", fstop=2.8)
```

#### render.py

```python
from blender import render

# Configure render settings
settings = render.configure(
    output_path="//render.png",
    resolution=(1920, 1080),
    samples=256,
    engine='CYCLES',
    use_gpu=True
)

# Quick preview
render.configure_for_preview(output_path="//preview.png")

# High quality
render.configure_for_production(output_path="//final.png")

# Execute render
render.execute()

# Render specific frame
render.render_frame(frame=42, output_path="//frame_042.png")
```

### Render Pipeline (`scripts/render/`)

These modules run **outside Blender** and manage the rendering subprocess.

#### engine.py

```python
from render.engine import RenderEngine, render_script

# Check Blender availability
engine = RenderEngine()
print(f"Blender available: {engine.is_available()}")
print(f"Version: {engine.version}")

# Render a script
result = engine.render(
    "scripts/my_scene.py",
    "renders/output.png",
    samples=128
)

if result.success:
    print(f"Rendered in {result.render_time:.1f}s")
else:
    print(f"Error: {result.error_message}")

# Render inline Python code
code = '''
from blender import scene, objects, render
scene.clear()
objects.create_cube("Cube", location=(0, 0, 1))
render.configure_for_preview("//output.png")
render.execute()
'''
result = engine.render_code(code, "renders/output.png")
```

#### batch.py

```python
from render.batch import BatchRenderer, render_scenes, render_jobs

# Simple batch rendering
scenes = [
    {'script': 'scene1.py', 'output': 'scene1.png', 'samples': 64},
    {'script': 'scene2.py', 'output': 'scene2.png', 'samples': 128},
]
result = render_scenes(scenes, output_dir='./renders')

# Using BatchRenderer class
batch = BatchRenderer(output_dir='./renders')
batch.add_job("intro", "scripts/intro.py", samples=256)
batch.add_job("scene1", "scripts/scene1.py", samples=128)
result = batch.run(parallel=2)

# Animation frames
from render.batch import render_animation_frames
result = render_animation_frames(
    source="scene.py",
    output_pattern="frames/frame_{frame:04d}.png",
    start_frame=1,
    end_frame=120,
    parallel=4
)
```

### Vision Validation (`scripts/validate/`)

These modules run **outside Blender** and use Claude Vision for analysis.

#### vision.py

```python
from validate.vision import (
    validate_render,
    analyze_render,
    compare_renders,
    generate_scene_suggestions,
    RenderValidator
)

# Validate a render against description
result = validate_render(
    "render.png",
    "A forest scene with 4 trees and an orange character"
)

print(f"Matches: {result.matches_description}")
print(f"Confidence: {result.confidence:.0%}")
print(f"Missing: {result.elements_missing}")
print(f"Suggestions: {result.suggestions}")

# Ask specific questions
answer = analyze_render("render.png", "Is the lighting too dark?")

# Compare two renders
comparison = compare_renders("render_v1.png", "render_v2.png")
print(f"Preferred: Image {comparison.preferred_image}")
print(f"Differences: {comparison.differences}")

# Get scene setup suggestions
suggestions = generate_scene_suggestions(
    "A cozy cabin interior at night with warm lighting",
    style_reference="Pixar style"
)

# Using RenderValidator class
validator = RenderValidator()
for iteration in range(3):
    # ... render scene ...
    result = validator.validate("render.png", description)
    if result.matches_description:
        break
    print(validator.get_improvement_prompt(result))
```

## Example Workflows

### 1. Creating a Scene from Scratch

```python
#!/usr/bin/env python3
"""Example: Create a complete scene in Blender."""

# This script runs INSIDE Blender
# Execute with: blender -b -P this_script.py

from blender import scene, objects, materials, lighting, camera, render

# Clear and set up
scene.clear()
scene.setup_sky_gradient()

# Create ground
ground = objects.create_ground(size=30, color=(0.15, 0.4, 0.15, 1.0))

# Create character
character = objects.create_character_placeholder(
    "MainCharacter",
    height=2.0,
    color=(0.8, 0.4, 0.2, 1.0),
    location=(0, 0, 0)
)

# Create trees
tree_positions = [(-5, 5, 0), (6, 3, 0), (-3, -6, 0), (5, -4, 0)]
for i, pos in enumerate(tree_positions):
    objects.create_simple_tree(f"Tree_{i}", height=4.0, location=pos)

# Setup lighting
lighting.three_point_setup(target=(0, 0, 1))

# Setup camera
camera.setup_main(location=(10, -10, 6), target=(0, 0, 1))

# Configure and render
render.configure_for_production(output_path="//scene.png")
render.execute()
```

### 2. Full Pipeline with Validation

```python
#!/usr/bin/env python3
"""Example: Complete pipeline with validation."""

# This script runs OUTSIDE Blender
from render.engine import RenderEngine
from validate.vision import validate_render

# Define what we want
scene_description = """
A simple outdoor scene with:
- Green grassy ground
- An orange character (pill/capsule shape) in the center
- Four trees around the character
- Blue sky with gradient
- Three-point lighting setup
"""

# Render
engine = RenderEngine()
result = engine.render(
    "scripts/poc_create_scene.py",
    "renders/scene.png",
    samples=64
)

if result.success:
    print(f"Rendered in {result.render_time:.1f}s")

    # Validate
    validation = validate_render("renders/scene.png", scene_description)

    print(f"\nValidation Results:")
    print(f"  Matches: {validation.matches_description}")
    print(f"  Confidence: {validation.confidence:.0%}")

    if validation.elements_found:
        print(f"  Found: {', '.join(validation.elements_found)}")

    if validation.elements_missing:
        print(f"  Missing: {', '.join(validation.elements_missing)}")

    if validation.suggestions:
        print(f"\n  Suggestions:")
        for s in validation.suggestions:
            print(f"    - {s}")
```

### 3. Batch Animation Rendering

```python
#!/usr/bin/env python3
"""Example: Batch render animation frames."""

from render.batch import render_animation_frames

# Render 120 frames with 4 parallel workers
result = render_animation_frames(
    source="scripts/animated_scene.py",
    output_pattern="renders/frames/frame_{frame:04d}.png",
    start_frame=1,
    end_frame=120,
    samples=64,
    parallel=4
)

print(f"\nBatch Complete:")
print(f"  Total frames: {result.total_jobs}")
print(f"  Completed: {result.completed}")
print(f"  Failed: {result.failed}")
print(f"  Total time: {result.total_time:.1f}s")
print(f"  Avg time/frame: {result.total_time / result.total_jobs:.1f}s")
```

## Configuration Files

### Scene Configuration (JSON)

```json
{
    "scene_description": "A forest clearing at sunset",
    "output_dir": "./renders",
    "output_name": "forest_sunset",
    "resolution": [1920, 1080],
    "samples": 256,
    "validate": true,
    "iterate": true,
    "max_iterations": 3,
    "style_reference": "Studio Ghibli style"
}
```

### Batch Configuration (JSON)

```json
{
    "jobs": [
        {
            "name": "scene_01",
            "source": "scripts/scenes/scene_01.py",
            "output": "renders/scene_01.png",
            "samples": 256,
            "resolution": [1920, 1080],
            "priority": 1
        },
        {
            "name": "scene_02",
            "source": "scripts/scenes/scene_02.py",
            "output": "renders/scene_02.png",
            "samples": 256,
            "dependencies": ["scene_01"]
        }
    ]
}
```

## Troubleshooting

### Blender Not Found

```bash
# Check if Blender is in PATH
which blender

# Set custom path
export BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"
```

### GPU Rendering Issues

```python
# Force CPU rendering
render.configure(use_gpu=False)
```

### Vision API Not Working

```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test API
python -c "from validate.vision import check_api_available; print(check_api_available())"
```

### Eevee Headless Rendering

Eevee requires a display. Use virtual framebuffer:

```bash
# Install Xvfb
sudo apt install xvfb

# Run with virtual display
Xvfb :1 -screen 0 1920x1080x24 &
DISPLAY=:1 blender -b scene.blend -E BLENDER_EEVEE -f 1
```

## Best Practices

1. **Start with low samples** (32-64) for iteration, increase for final renders
2. **Use preview resolution** (960x540) during development
3. **Organize scenes in collections** for complex setups
4. **Save .blend files** periodically for manual inspection
5. **Use the validation loop** to catch issues early
6. **Batch render overnight** for animation sequences

## Next Steps

- [ ] Add character rigging automation
- [ ] Implement procedural environment generators
- [ ] Add BlenderMCP integration for interactive development
- [ ] Create scene templates for common setups
- [ ] Build asset library management
