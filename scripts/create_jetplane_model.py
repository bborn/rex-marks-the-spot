#!/usr/bin/env python3
"""Create a stylized Jetplane dinosaur model using Blender Python.

This creates a cartoon-style dinosaur matching the approved turnaround design:
- Teal-green body with chunky proportions
- Orange crest on head
- Big expressive eyes
- Small/lovable build

Run: blender --background --python scripts/create_jetplane_model.py
"""

import bpy
import bmesh
import math
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "output", "3d-models", "jetplane")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clear_scene():
    """Remove all default objects."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    # Remove default collections' objects
    for c in bpy.data.collections:
        for obj in c.objects:
            bpy.data.objects.remove(obj, do_unlink=True)


def create_material(name, color, roughness=0.6, metallic=0.0):
    """Create a PBR material."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_metaball_element(mball, x, y, z, radius, type='BALL'):
    """Add a metaball element."""
    elem = mball.elements.new()
    elem.co = (x, y, z)
    elem.radius = radius
    elem.type = type
    return elem


def create_dinosaur_body():
    """Create the main body using metaballs, then convert to mesh."""
    # Create metaball for smooth organic shape
    mball = bpy.data.metaballs.new("DinoBody")
    mball.resolution = 0.06
    mball.render_resolution = 0.04

    obj = bpy.data.objects.new("DinoBody", mball)
    bpy.context.collection.objects.link(obj)

    # Main body - chunky barrel shape
    add_metaball_element(mball, 0, 0, 0.5, 0.45)  # Main torso
    add_metaball_element(mball, 0, 0.15, 0.55, 0.35)  # Upper torso
    add_metaball_element(mball, 0, -0.1, 0.4, 0.38)  # Lower torso/belly

    # Head - big round head
    add_metaball_element(mball, 0, 0.35, 0.85, 0.32)  # Head
    add_metaball_element(mball, 0, 0.45, 0.82, 0.2)  # Snout

    # Neck
    add_metaball_element(mball, 0, 0.25, 0.7, 0.22)  # Neck

    # Tail
    add_metaball_element(mball, 0, -0.3, 0.35, 0.25)  # Tail base
    add_metaball_element(mball, 0, -0.5, 0.3, 0.18)  # Tail mid
    add_metaball_element(mball, 0, -0.65, 0.28, 0.12)  # Tail tip

    # Arms/front legs - small T-rex style
    add_metaball_element(mball, 0.2, 0.15, 0.55, 0.1)  # Right arm
    add_metaball_element(mball, -0.2, 0.15, 0.55, 0.1)  # Left arm
    add_metaball_element(mball, 0.25, 0.2, 0.5, 0.07)  # Right hand
    add_metaball_element(mball, -0.25, 0.2, 0.5, 0.07)  # Left hand

    # Legs - chunky
    add_metaball_element(mball, 0.18, -0.05, 0.25, 0.15)  # Right thigh
    add_metaball_element(mball, -0.18, -0.05, 0.25, 0.15)  # Left thigh
    add_metaball_element(mball, 0.18, 0.0, 0.1, 0.12)  # Right shin
    add_metaball_element(mball, -0.18, 0.0, 0.1, 0.12)  # Left shin
    add_metaball_element(mball, 0.18, 0.05, 0.0, 0.1)  # Right foot
    add_metaball_element(mball, -0.18, 0.05, 0.0, 0.1)  # Left foot

    # Convert to mesh
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target='MESH')

    # After conversion, the original ref may be invalid - get active object
    body = bpy.context.active_object
    body.name = "DinoBody"
    body.select_set(False)
    return body


def create_crest():
    """Create the orange crest on top of the head."""
    # Create a series of crest spikes
    crest_obj = None

    for i in range(5):
        t = i / 4.0
        x = 0
        y = 0.3 - t * 0.5  # From head to back
        z = 0.95 + math.sin(t * math.pi) * 0.1  # Arc over head

        bpy.ops.mesh.primitive_cone_add(
            vertices=8,
            radius1=0.04,
            radius2=0.01,
            depth=0.12 + (1 - abs(t - 0.3) * 2) * 0.08,
            location=(x, y, z)
        )
        spike = bpy.context.active_object
        spike.rotation_euler = (math.radians(-20 + t * 30), 0, 0)

        if crest_obj is None:
            crest_obj = spike
            crest_obj.name = "Crest"
        else:
            spike.select_set(True)
            crest_obj.select_set(True)
            bpy.context.view_layer.objects.active = crest_obj
            bpy.ops.object.join()

    return crest_obj


def create_eyes():
    """Create big expressive cartoon eyes."""
    eyes = []
    for side in [-1, 1]:
        # Eyeball (white)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.08,
            segments=16,
            ring_count=12,
            location=(side * 0.12, 0.48, 0.9)
        )
        eyeball = bpy.context.active_object
        eyeball.name = f"Eye_{'R' if side > 0 else 'L'}"

        # Pupil (black)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.045,
            segments=12,
            ring_count=8,
            location=(side * 0.12, 0.54, 0.91)
        )
        pupil = bpy.context.active_object
        pupil.name = f"Pupil_{'R' if side > 0 else 'L'}"

        # Highlight (white dot)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.015,
            segments=8,
            ring_count=6,
            location=(side * 0.1, 0.555, 0.925)
        )
        highlight = bpy.context.active_object
        highlight.name = f"Highlight_{'R' if side > 0 else 'L'}"

        eyes.extend([eyeball, pupil, highlight])

    return eyes


def create_nostrils():
    """Add small nostrils on the snout."""
    nostrils = []
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.02,
            segments=8,
            ring_count=6,
            location=(side * 0.05, 0.58, 0.8)
        )
        nostril = bpy.context.active_object
        nostril.name = f"Nostril_{'R' if side > 0 else 'L'}"
        nostrils.append(nostril)
    return nostrils


def setup_materials(body, crest, eyes):
    """Apply materials to all parts."""
    # Teal-green body
    teal = create_material("TealGreen", (0.15, 0.55, 0.45, 1.0), roughness=0.7)

    # Orange crest
    orange = create_material("OrangeCrest", (0.9, 0.45, 0.1, 1.0), roughness=0.5)

    # Eye white
    eye_white = create_material("EyeWhite", (0.95, 0.95, 0.95, 1.0), roughness=0.3)

    # Pupil black
    pupil_black = create_material("PupilBlack", (0.05, 0.05, 0.05, 1.0), roughness=0.2)

    # Highlight
    highlight = create_material("Highlight", (1.0, 1.0, 1.0, 1.0), roughness=0.1)

    # Belly lighter color
    belly = create_material("Belly", (0.6, 0.8, 0.7, 1.0), roughness=0.7)

    # Nostril dark
    nostril_mat = create_material("Nostril", (0.1, 0.3, 0.25, 1.0), roughness=0.8)

    # Apply body material
    body.data.materials.append(teal)

    # Apply crest material
    if crest:
        crest.data.materials.append(orange)

    # Apply eye materials
    for eye_obj in eyes:
        name = eye_obj.name
        if "Pupil" in name:
            eye_obj.data.materials.append(pupil_black)
        elif "Highlight" in name:
            eye_obj.data.materials.append(highlight)
        elif "Nostril" in name:
            eye_obj.data.materials.append(nostril_mat)
        else:
            eye_obj.data.materials.append(eye_white)


def smooth_object(obj):
    """Apply smooth shading and subdivision."""
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()

    # Add subdivision modifier for smoothness
    subsurf = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2
    bpy.ops.object.modifier_apply(modifier="Subdivision")
    obj.select_set(False)


def export_model():
    """Export the complete model as GLB."""
    # Select all objects
    bpy.ops.object.select_all(action='SELECT')

    # Export GLB
    glb_path = os.path.join(OUTPUT_DIR, "jetplane.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
    )

    size_mb = os.path.getsize(glb_path) / (1024 * 1024)
    print(f"Exported: {glb_path} ({size_mb:.2f} MB)")

    # Count mesh stats
    total_verts = 0
    total_faces = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            total_verts += len(obj.data.vertices)
            total_faces += len(obj.data.polygons)
    print(f"Total: {total_verts} vertices, {total_faces} faces")

    return glb_path


def render_preview():
    """Render a preview image."""
    # Add camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    cam_obj.location = (1.2, -1.2, 0.8)

    # Point camera at model center
    empty = bpy.data.objects.new("CamTarget", None)
    bpy.context.scene.collection.objects.link(empty)
    empty.location = (0, 0, 0.5)
    constraint = cam_obj.constraints.new(type='TRACK_TO')
    constraint.target = empty
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

    # Add lights
    light1 = bpy.data.lights.new("Key", type='SUN')
    light1.energy = 3.0
    light1_obj = bpy.data.objects.new("Key", light1)
    bpy.context.scene.collection.objects.link(light1_obj)
    light1_obj.rotation_euler = (math.radians(50), math.radians(30), 0)

    light2 = bpy.data.lights.new("Fill", type='SUN')
    light2.energy = 1.5
    light2_obj = bpy.data.objects.new("Fill", light2)
    bpy.context.scene.collection.objects.link(light2_obj)
    light2_obj.rotation_euler = (math.radians(60), math.radians(-45), 0)

    # Background
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.color = (0.15, 0.15, 0.2)

    # Render settings
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024

    preview_path = os.path.join(OUTPUT_DIR, "preview_jetplane.png")
    bpy.context.scene.render.filepath = preview_path
    bpy.context.scene.render.image_settings.file_format = 'PNG'

    bpy.ops.render.render(write_still=True)
    print(f"Preview: {preview_path}")
    return preview_path


def main():
    print("Creating Jetplane dinosaur model...")
    clear_scene()

    # Create body
    print("  Creating body...")
    body = create_dinosaur_body()

    # Create crest
    print("  Creating crest...")
    crest = create_crest()

    # Create eyes
    print("  Creating eyes...")
    eyes = create_eyes()

    # Create nostrils
    print("  Creating nostrils...")
    nostrils = create_nostrils()

    # Apply materials
    print("  Applying materials...")
    all_eye_parts = eyes + nostrils
    setup_materials(body, crest, all_eye_parts)

    # Smooth the body
    print("  Smoothing...")
    smooth_object(body)

    # Export
    print("  Exporting...")
    glb_path = export_model()

    # Render preview
    print("  Rendering preview...")
    render_preview()

    print("\nJetplane model complete!")
    return glb_path


if __name__ == "__main__":
    main()
