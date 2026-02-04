#!/usr/bin/env python3
"""
Scene Assembly Script for Fairy Dinosaur Date Night
====================================================

This script provides the workflow for assembling production scenes in Blender.
It can be used both interactively via BlenderMCP and in headless batch mode.

WORKFLOW OVERVIEW:
1. Clear scene and set up basic environment
2. Import character models (or create placeholders)
3. Position characters according to storyboard
4. Set up three-point lighting
5. Configure camera for the shot
6. Import environment reference image (optional)
7. Configure render settings
8. Render preview or production frames

Usage:
    Interactive (BlenderMCP):
        - Import this script in Blender and call functions as needed

    Headless batch render:
        blender -b -P scripts/scene_assembly.py -- [options]

Options:
    --scene NAME        Scene name (default: test)
    --preview           Low quality preview render
    --output DIR        Output directory (default: renders/)
    --characters LIST   Comma-separated character names to include
"""

import bpy
import bmesh
import sys
import os
import math
from pathlib import Path

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_scene():
    """Remove all objects from the scene to start fresh."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clean orphan data blocks
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)

    print("[Scene Assembly] Scene cleared")


def create_material(name, color, roughness=0.5, metallic=0.0, emission=0.0):
    """
    Create a Principled BSDF material.

    Args:
        name: Material name
        color: RGBA tuple (0-1 range)
        roughness: Surface roughness (0=smooth, 1=rough)
        metallic: Metallic value (0=dielectric, 1=metallic)
        emission: Emission strength

    Returns:
        bpy.types.Material
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission > 0:
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = emission
    return mat


# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

def create_ground_plane(size=10, color=(0.3, 0.5, 0.25, 1.0)):
    """Create a ground plane with material."""
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.data.materials.append(create_material("Ground_Mat", color, roughness=0.8))
    return ground


def setup_world_sky(sun_elevation=30, sun_rotation=45, strength=1.0):
    """
    Set up a procedural sky background.

    Args:
        sun_elevation: Sun angle above horizon in degrees
        sun_rotation: Sun rotation around vertical axis in degrees
        strength: Background strength
    """
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    # Nishita sky model
    sky_tex = nodes.new('ShaderNodeTexSky')
    sky_tex.sky_type = 'NISHITA'
    sky_tex.sun_elevation = math.radians(sun_elevation)
    sky_tex.sun_rotation = math.radians(sun_rotation)

    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = strength

    output = nodes.new('ShaderNodeOutputWorld')

    links.new(sky_tex.outputs['Color'], bg.inputs['Color'])
    links.new(bg.outputs['Background'], output.inputs['Surface'])

    print(f"[Scene Assembly] World sky configured (sun elevation: {sun_elevation}deg)")


def import_environment_reference(image_path, location=(0, 10, 2), scale=8):
    """
    Import an image as a reference plane in the background.

    Args:
        image_path: Path to the image file
        location: 3D location for the plane
        scale: Size of the reference plane

    Returns:
        Reference plane object or None if failed
    """
    if not os.path.exists(image_path):
        print(f"[Scene Assembly] Warning: Image not found: {image_path}")
        return None

    # Load image
    img = bpy.data.images.load(image_path)

    # Create plane with image aspect ratio
    aspect = img.size[0] / img.size[1] if img.size[1] > 0 else 1.0

    bpy.ops.mesh.primitive_plane_add(size=scale, location=location)
    plane = bpy.context.active_object
    plane.name = "Environment_Reference"
    plane.scale.x = aspect
    plane.rotation_euler = (math.radians(90), 0, 0)

    # Create material with image texture
    mat = bpy.data.materials.new(name="EnvRef_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = nodes.get("Principled BSDF")

    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = img

    links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 1.0

    plane.data.materials.append(mat)

    print(f"[Scene Assembly] Environment reference loaded: {os.path.basename(image_path)}")
    return plane


# ============================================================================
# CHARACTER FUNCTIONS
# ============================================================================

# Character color palette (matches storyboard designs)
CHARACTER_COLORS = {
    'Mia': (0.3, 0.5, 0.9, 1.0),      # Blue (8yo protagonist)
    'Leo': (0.4, 0.8, 0.4, 1.0),      # Green (5yo protagonist)
    'Gabe': (0.15, 0.15, 0.2, 1.0),   # Dark gray (Dad)
    'Nina': (0.6, 0.15, 0.15, 1.0),   # Maroon (Mom)
    'Ruben': (0.6, 0.3, 0.7, 1.0),    # Purple (Fairy godfather)
    'Jetplane': (0.9, 0.5, 0.2, 1.0), # Orange (Dinosaur)
}

CHARACTER_HEIGHTS = {
    'Mia': 1.2,
    'Leo': 1.0,
    'Gabe': 1.85,
    'Nina': 1.7,
    'Ruben': 0.6,   # Small fairy
    'Jetplane': 2.0, # Large dinosaur
}


def create_placeholder_character(name, location=(0, 0, 0), pose='standing'):
    """
    Create a simple mannequin placeholder for character positioning.

    This is used during scene blocking before actual character models are imported.

    Args:
        name: Character name (Mia, Leo, Gabe, Nina, Ruben, Jetplane)
        location: World location tuple (x, y, z)
        pose: 'standing' or 'sitting'

    Returns:
        Root empty object for the character
    """
    color = CHARACTER_COLORS.get(name, (0.5, 0.5, 0.5, 1.0))
    height = CHARACTER_HEIGHTS.get(name, 1.7)

    # Create root empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
    root = bpy.context.active_object
    root.name = f"{name}_Root"
    root.empty_display_size = 0.3

    # Create material
    mat = create_material(f"{name}_Mat", color, roughness=0.7)

    # Body proportions
    body_height = height * 0.5
    body_radius = height * 0.12
    head_radius = height * 0.1

    # Adjust for pose
    body_z = body_height / 2 + 0.1
    if pose == 'sitting':
        body_z = 0.5

    # Body (cylinder)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=body_radius,
        depth=body_height,
        location=(location[0], location[1], body_z)
    )
    body = bpy.context.active_object
    body.name = f"{name}_Body"
    body.parent = root
    body.data.materials.append(mat)

    # Head (sphere)
    head_z = body_z + body_height/2 + head_radius + 0.05
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=head_radius,
        location=(location[0], location[1], head_z)
    )
    head = bpy.context.active_object
    head.name = f"{name}_Head"
    head.parent = root
    head.data.materials.append(mat)

    # Arms (horizontal cylinder)
    arm_z = body_z + body_height * 0.3
    bpy.ops.mesh.primitive_cylinder_add(
        radius=height * 0.04,
        depth=height * 0.4,
        rotation=(0, math.radians(90), 0),
        location=(location[0], location[1], arm_z)
    )
    arms = bpy.context.active_object
    arms.name = f"{name}_Arms"
    arms.parent = root
    arms.data.materials.append(mat)

    # Legs (only if standing)
    if pose == 'standing':
        for side, offset in [('L', -0.1), ('R', 0.1)]:
            bpy.ops.mesh.primitive_cylinder_add(
                radius=height * 0.05,
                depth=height * 0.35,
                location=(location[0] + offset, location[1], height * 0.175)
            )
            leg = bpy.context.active_object
            leg.name = f"{name}_Leg_{side}"
            leg.parent = root
            leg.data.materials.append(mat)

    print(f"[Scene Assembly] Created placeholder: {name} at {location}")
    return root


def import_character_model(name, blend_path, location=(0, 0, 0)):
    """
    Import a character from a .blend file.

    Args:
        name: Character name for the imported objects
        blend_path: Path to the .blend file
        location: Where to place the character

    Returns:
        List of imported objects
    """
    if not os.path.exists(blend_path):
        print(f"[Scene Assembly] Character file not found: {blend_path}")
        return create_placeholder_character(name, location)

    # Link/append all objects from the blend file
    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects

    imported = []
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            obj.location = location
            imported.append(obj)

    print(f"[Scene Assembly] Imported character: {name} ({len(imported)} objects)")
    return imported


# ============================================================================
# LIGHTING SETUP
# ============================================================================

def setup_three_point_lighting(key_energy=500, fill_energy=200, rim_energy=300):
    """
    Set up standard three-point lighting for character/scene rendering.

    Args:
        key_energy: Key light intensity
        fill_energy: Fill light intensity
        rim_energy: Rim/back light intensity

    Returns:
        Dict of light objects
    """
    lights = {}

    # Key Light (main light, front-right, warm)
    bpy.ops.object.light_add(type='AREA', location=(3, -2, 4))
    key = bpy.context.active_object
    key.name = "Key_Light"
    key.data.energy = key_energy
    key.data.size = 3.0
    key.data.color = (1.0, 0.95, 0.9)
    key.rotation_euler = (math.radians(45), 0, math.radians(30))
    lights['key'] = key

    # Fill Light (softer, front-left, slightly cool)
    bpy.ops.object.light_add(type='AREA', location=(-3, -1, 3))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = fill_energy
    fill.data.size = 4.0
    fill.data.color = (0.9, 0.95, 1.0)
    fill.rotation_euler = (math.radians(45), 0, math.radians(-30))
    lights['fill'] = fill

    # Rim Light (edge definition, behind, warm)
    bpy.ops.object.light_add(type='AREA', location=(0, 3, 3))
    rim = bpy.context.active_object
    rim.name = "Rim_Light"
    rim.data.energy = rim_energy
    rim.data.size = 2.0
    rim.data.color = (1.0, 0.9, 0.7)
    rim.rotation_euler = (math.radians(110), 0, 0)
    lights['rim'] = rim

    # Ambient sun for overall fill
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.name = "Sun_Ambient"
    sun.data.energy = 1.0
    sun.rotation_euler = (math.radians(45), 0, math.radians(30))
    lights['sun'] = sun

    print(f"[Scene Assembly] Three-point lighting configured")
    return lights


def setup_interior_lighting(warmth=0.9):
    """
    Set up warm interior lighting suitable for home scenes.

    Args:
        warmth: Color temperature warmth (0=cool, 1=warm)
    """
    lights = {}

    # Ceiling light (main)
    bpy.ops.object.light_add(type='AREA', location=(0, 1, 3.5))
    main = bpy.context.active_object
    main.name = "Ceiling_Light"
    main.data.energy = 300
    main.data.size = 2.0
    main.data.color = (1.0, 0.9 * warmth + 0.1, 0.75 * warmth + 0.25)
    lights['ceiling'] = main

    # Window light (if present)
    bpy.ops.object.light_add(type='AREA', location=(-3.5, 1, 1.5))
    window = bpy.context.active_object
    window.name = "Window_Light"
    window.data.energy = 150
    window.data.size = 1.5
    window.data.color = (1.0, 0.7, 0.4)  # Sunset orange
    window.rotation_euler = (0, math.radians(-90), 0)
    lights['window'] = window

    print(f"[Scene Assembly] Interior lighting configured (warmth: {warmth})")
    return lights


# ============================================================================
# CAMERA SETUP
# ============================================================================

def setup_camera(location=(5, -5, 3), target=(0, 0, 1), lens=35):
    """
    Set up a camera pointed at a target location.

    Args:
        location: Camera position
        target: Point the camera looks at
        lens: Focal length in mm

    Returns:
        Camera object
    """
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.active_object
    camera.name = "Scene_Camera"
    camera.data.lens = lens
    camera.data.clip_end = 1000

    # Point at target
    from mathutils import Vector
    direction = Vector(target) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()

    # Set as active
    bpy.context.scene.camera = camera

    print(f"[Scene Assembly] Camera at {location}, lens {lens}mm")
    return camera


def setup_camera_simple(location=(5, -5, 3), rotation_deg=(70, 0, 45), lens=35):
    """
    Set up a camera with explicit rotation angles.

    Args:
        location: Camera position
        rotation_deg: Rotation in degrees (x, y, z)
        lens: Focal length
    """
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.active_object
    camera.name = "Scene_Camera"
    camera.data.lens = lens
    camera.data.clip_end = 1000

    camera.rotation_euler = (
        math.radians(rotation_deg[0]),
        math.radians(rotation_deg[1]),
        math.radians(rotation_deg[2])
    )

    bpy.context.scene.camera = camera
    print(f"[Scene Assembly] Camera configured")
    return camera


# ============================================================================
# RENDER CONFIGURATION
# ============================================================================

def configure_render(
    output_dir='renders',
    resolution=(1920, 1080),
    samples=64,
    preview=False,
    engine='CYCLES'
):
    """
    Configure render settings for the scene.

    Args:
        output_dir: Directory for output frames
        resolution: (width, height) tuple
        samples: Number of render samples
        preview: If True, use lower quality settings
        engine: 'CYCLES' or 'BLENDER_EEVEE_NEXT'
    """
    scene = bpy.context.scene
    render = scene.render

    # Output path
    os.makedirs(output_dir, exist_ok=True)
    render.filepath = os.path.join(os.path.abspath(output_dir), 'frame_')
    render.image_settings.file_format = 'PNG'

    # Resolution
    if preview:
        render.resolution_x = resolution[0] // 2
        render.resolution_y = resolution[1] // 2
        samples = max(16, samples // 4)
    else:
        render.resolution_x = resolution[0]
        render.resolution_y = resolution[1]

    render.resolution_percentage = 100

    # Engine (handle both EEVEE naming conventions across Blender versions)
    if engine.startswith('BLENDER_EEVEE'):
        try:
            scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Blender 4.2+
        except TypeError:
            scene.render.engine = 'BLENDER_EEVEE'  # Blender 4.0-4.1
        scene.eevee.taa_render_samples = samples
    else:
        scene.render.engine = engine

    if engine == 'CYCLES':
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True

        # Try GPU
        try:
            prefs = bpy.context.preferences.addons['cycles'].preferences
            for device_type in ['OPTIX', 'CUDA', 'HIP', 'METAL']:
                try:
                    prefs.compute_device_type = device_type
                    prefs.get_devices()
                    if prefs.devices:
                        for device in prefs.devices:
                            device.use = True
                        scene.cycles.device = 'GPU'
                        print(f"[Scene Assembly] Using GPU: {device_type}")
                        break
                except:
                    continue
            else:
                scene.cycles.device = 'CPU'
        except:
            scene.cycles.device = 'CPU'

    print(f"[Scene Assembly] Render: {render.resolution_x}x{render.resolution_y}, {samples} samples")
    return render


# ============================================================================
# COMPLETE SCENE ASSEMBLY FUNCTIONS
# ============================================================================

def assemble_test_scene():
    """
    Assemble a complete test scene with placeholder characters.
    This demonstrates the full workflow.
    """
    print("\n" + "=" * 60)
    print("SCENE ASSEMBLY TEST")
    print("=" * 60)

    # Step 1: Clear
    print("\n[1/6] Clearing scene...")
    clear_scene()

    # Step 2: Environment
    print("[2/6] Setting up environment...")
    create_ground_plane()
    setup_world_sky(sun_elevation=30, sun_rotation=45)

    # Step 3: Characters
    print("[3/6] Creating placeholder characters...")
    characters = {}
    characters['Mia'] = create_placeholder_character('Mia', location=(-1.0, 0.5, 0))
    characters['Leo'] = create_placeholder_character('Leo', location=(1.0, 0.5, 0))
    characters['Ruben'] = create_placeholder_character('Ruben', location=(0, 2.0, 0))
    characters['Jetplane'] = create_placeholder_character('Jetplane', location=(0, -1.5, 0))

    # Step 4: Lighting
    print("[4/6] Setting up lighting...")
    setup_three_point_lighting()

    # Step 5: Camera
    print("[5/6] Configuring camera...")
    setup_camera_simple(location=(5, -5, 3), rotation_deg=(70, 0, 45), lens=35)

    # Step 6: Render settings
    print("[6/6] Configuring render...")
    configure_render(output_dir='renders/test', preview=True)

    print("\n" + "=" * 60)
    print("SCENE ASSEMBLY COMPLETE")
    print("=" * 60)
    print("\nTo render, run: bpy.ops.render.render(write_still=True)")

    return characters


def assemble_scene_from_storyboard(
    scene_name,
    character_positions,
    camera_settings,
    lighting_type='three_point',
    env_image=None
):
    """
    Assemble a production scene based on storyboard specifications.

    Args:
        scene_name: Name for the scene
        character_positions: Dict of {name: (x, y, z)} positions
        camera_settings: Dict with location, rotation, lens
        lighting_type: 'three_point', 'interior', or 'outdoor'
        env_image: Optional environment reference image path

    Example:
        assemble_scene_from_storyboard(
            scene_name="act1_scene1",
            character_positions={
                'Mia': (-1, 1.5, 0),
                'Leo': (0.5, 1.5, 0),
                'Gabe': (2, 2, 0),
                'Nina': (1.5, 0.5, 0),
            },
            camera_settings={
                'location': (0, -5, 2),
                'rotation_deg': (75, 0, 0),
                'lens': 35
            },
            lighting_type='interior'
        )
    """
    print(f"\n[Scene Assembly] Building scene: {scene_name}")

    clear_scene()

    # Environment
    create_ground_plane()
    if lighting_type == 'outdoor':
        setup_world_sky()
    else:
        # Dark background for interior
        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world
        world.use_nodes = True
        nodes = world.node_tree.nodes
        nodes.clear()
        bg = nodes.new('ShaderNodeBackground')
        bg.inputs['Color'].default_value = (0.1, 0.08, 0.06, 1.0)
        output = nodes.new('ShaderNodeOutputWorld')
        world.node_tree.links.new(bg.outputs['Background'], output.inputs['Surface'])

    # Environment reference
    if env_image:
        import_environment_reference(env_image)

    # Characters
    characters = {}
    for name, pos in character_positions.items():
        characters[name] = create_placeholder_character(name, location=pos)

    # Lighting
    if lighting_type == 'three_point':
        setup_three_point_lighting()
    elif lighting_type == 'interior':
        setup_interior_lighting()
    else:
        setup_three_point_lighting()

    # Camera
    cam = camera_settings
    setup_camera_simple(
        location=cam.get('location', (5, -5, 3)),
        rotation_deg=cam.get('rotation_deg', (70, 0, 45)),
        lens=cam.get('lens', 35)
    )

    # Render config
    configure_render(
        output_dir=f'renders/{scene_name}',
        preview=True
    )

    print(f"[Scene Assembly] Scene '{scene_name}' ready")
    return characters


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def parse_args():
    """Parse command line arguments."""
    args = {
        'scene': 'test',
        'preview': False,
        'output': 'renders',
        'characters': ['Mia', 'Leo', 'Ruben', 'Jetplane'],
    }

    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
        i = 0
        while i < len(argv):
            if argv[i] == '--scene' and i + 1 < len(argv):
                args['scene'] = argv[i + 1]
                i += 2
            elif argv[i] == '--preview':
                args['preview'] = True
                i += 1
            elif argv[i] == '--output' and i + 1 < len(argv):
                args['output'] = argv[i + 1]
                i += 2
            elif argv[i] == '--characters' and i + 1 < len(argv):
                args['characters'] = argv[i + 1].split(',')
                i += 2
            else:
                i += 1

    return args


def main():
    """Main entry point for CLI usage."""
    args = parse_args()

    print("=" * 60)
    print(f"SCENE ASSEMBLY: {args['scene']}")
    print("=" * 60)

    # Run test assembly
    assemble_test_scene()

    # Render if not in interactive mode
    if bpy.app.background:
        print("\nRendering...")
        bpy.ops.render.render(write_still=True)
        print(f"\nOutput saved to: {bpy.context.scene.render.filepath}")


if __name__ == "__main__":
    main()
