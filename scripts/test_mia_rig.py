#!/usr/bin/env python3
"""
Test Mia's rigged 3D model in Blender.
Downloads the rigged GLB, verifies the rig, creates test poses, and renders previews.
Run with: blender --background --python scripts/test_mia_rig.py
"""

import bpy
import math
import os
import json
import mathutils

OUTPUT_DIR = "/tmp/mia_rig_tests"
GLB_PATH = "/tmp/mia_rigged.glb"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def clear_scene():
    """Clear all objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    # Clean up orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.armatures:
        if block.users == 0:
            bpy.data.armatures.remove(block)


def import_model():
    """Import the GLB model."""
    print("\n=== IMPORTING MODEL ===")
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=GLB_PATH)

    # Remove any stray objects (like Icosphere)
    for obj in list(bpy.data.objects):
        if obj.type not in ('ARMATURE', 'MESH', 'CAMERA', 'LIGHT'):
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type == 'MESH' and obj.name != 'char1':
            # Remove stray meshes like Icosphere
            if len(obj.data.vertices) < 100:
                print(f"  Removing stray mesh: {obj.name} ({len(obj.data.vertices)} verts)")
                bpy.data.objects.remove(obj, do_unlink=True)

    print("Import complete!")
    for obj in bpy.data.objects:
        print(f"  {obj.name} (type: {obj.type})")

    return True


def verify_rig():
    """Verify the rig structure and report findings."""
    print("\n=== VERIFYING RIG ===")
    report = {
        "armature_found": False,
        "bone_count": 0,
        "bone_names": [],
        "humanoid_standard": False,
        "mesh_linked": False,
        "vertex_groups": 0,
        "vertex_count": 0,
        "face_count": 0,
        "character_height": 0,
        "issues": [],
        "initial_pose": "unknown"
    }

    armature = None
    mesh = None

    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH' and obj.name == 'char1':
            mesh = obj

    if not armature:
        report["issues"].append("No armature found!")
        return report

    report["armature_found"] = True
    report["bone_count"] = len(armature.data.bones)

    # Check bone names
    bone_names = [b.name for b in armature.data.bones]
    report["bone_names"] = bone_names
    print(f"  Armature: {armature.name}")
    print(f"  Bones ({len(bone_names)}):")
    for name in bone_names:
        parent = armature.data.bones[name].parent
        print(f"    {name} -> parent: {parent.name if parent else 'ROOT'}")

    # Check if humanoid standard (Mixamo-like naming)
    required_bones = ['Hips', 'Spine', 'Head', 'LeftArm', 'RightArm', 'LeftLeg', 'RightLeg']
    missing = [b for b in required_bones if b not in bone_names]
    report["humanoid_standard"] = len(missing) == 0
    if missing:
        report["issues"].append(f"Missing standard bones: {missing}")
    else:
        print("  Humanoid standard bones: ALL PRESENT")

    # Check mesh
    if mesh:
        report["vertex_count"] = len(mesh.data.vertices)
        report["face_count"] = len(mesh.data.polygons)
        report["vertex_groups"] = len(mesh.vertex_groups)
        print(f"  Mesh: {mesh.name}")
        print(f"    Vertices: {report['vertex_count']:,}")
        print(f"    Faces: {report['face_count']:,}")
        print(f"    Vertex Groups: {report['vertex_groups']}")

        # Check armature modifier
        has_armature_mod = any(m.type == 'ARMATURE' for m in mesh.modifiers)
        report["mesh_linked"] = has_armature_mod
        if not has_armature_mod:
            report["issues"].append("Mesh has no Armature modifier")
        else:
            print("    Armature modifier: PRESENT")

        # Get character height
        dims = mesh.dimensions
        report["character_height"] = round(dims[2], 3)
        print(f"    Character height: {dims[2]:.3f}m")
        print(f"    Character width: {dims[0]:.3f}m")
        print(f"    Character depth: {dims[1]:.3f}m")

    # Check initial pose
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    # Check if arms are roughly horizontal (T-pose) or at sides (A-pose)
    if 'LeftArm' in armature.pose.bones:
        left_arm = armature.pose.bones['LeftArm']
        # In rest pose, check the bone's orientation
        rest_bone = armature.data.bones['LeftArm']
        vec = rest_bone.tail_local - rest_bone.head_local
        # If arm goes mostly sideways, it's T-pose
        if abs(vec[0]) > abs(vec[2]):
            report["initial_pose"] = "T-pose (approximate)"
        else:
            report["initial_pose"] = "A-pose or neutral"
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  Initial pose: {report['initial_pose']}")

    return report


def setup_scene():
    """Set up lighting, camera, and render settings."""
    print("\n=== SETTING UP SCENE ===")

    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'

    # White background
    world = bpy.data.worlds.get('World')
    if not world:
        world = bpy.data.worlds.new('World')
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (0.95, 0.95, 0.95, 1)
        bg.inputs[1].default_value = 1.5

    # Get character center and height for camera/light positioning
    mesh = bpy.data.objects.get('char1')
    if mesh:
        char_height = mesh.dimensions[2]
        char_center_z = char_height / 2
    else:
        char_height = 1.2
        char_center_z = 0.6

    # Remove existing cameras and lights
    for obj in list(bpy.data.objects):
        if obj.type in ('CAMERA', 'LIGHT'):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Create camera - front 3/4 view
    cam_data = bpy.data.cameras.new('RenderCam')
    cam_data.lens = 85  # Portrait lens
    cam_obj = bpy.data.objects.new('RenderCam', cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Position camera for 3/4 view
    cam_dist = char_height * 2.5
    cam_angle = math.radians(30)  # 30 degrees from front
    cam_x = cam_dist * math.sin(cam_angle)
    cam_y = -cam_dist * math.cos(cam_angle)
    cam_z = char_center_z + char_height * 0.1

    cam_obj.location = (cam_x, cam_y, cam_z)

    # Point camera at character center
    direction = mathutils.Vector((0, 0, char_center_z)) - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    # 3-point lighting setup
    # Key light (main, warm)
    key_data = bpy.data.lights.new('KeyLight', 'AREA')
    key_data.energy = 200
    key_data.color = (1.0, 0.95, 0.9)
    key_data.size = 2
    key_obj = bpy.data.objects.new('KeyLight', key_data)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (char_height * 1.5, -char_height * 2, char_height * 1.5)
    key_obj.rotation_euler = (math.radians(45), 0, math.radians(30))

    # Fill light (softer, cooler)
    fill_data = bpy.data.lights.new('FillLight', 'AREA')
    fill_data.energy = 80
    fill_data.color = (0.9, 0.95, 1.0)
    fill_data.size = 3
    fill_obj = bpy.data.objects.new('FillLight', fill_data)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (-char_height * 2, -char_height * 1.5, char_height)
    fill_obj.rotation_euler = (math.radians(30), 0, math.radians(-45))

    # Rim light (backlight)
    rim_data = bpy.data.lights.new('RimLight', 'AREA')
    rim_data.energy = 150
    rim_data.color = (1.0, 1.0, 1.0)
    rim_data.size = 1.5
    rim_obj = bpy.data.objects.new('RimLight', rim_data)
    bpy.context.collection.objects.link(rim_obj)
    rim_obj.location = (-char_height * 0.5, char_height * 2, char_height * 1.8)
    rim_obj.rotation_euler = (math.radians(-30), 0, math.radians(170))

    print("  Camera and 3-point lighting set up")
    print(f"  Camera at: ({cam_x:.2f}, {cam_y:.2f}, {cam_z:.2f})")
    return True


def reset_pose(armature):
    """Reset all bones to rest pose."""
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.scale_clear()
    bpy.ops.object.mode_set(mode='OBJECT')


def apply_pose(armature, pose_name, bone_rotations):
    """Apply a pose by rotating specified bones.

    bone_rotations: dict of bone_name -> (rx, ry, rz) in degrees
    """
    print(f"\n  Applying pose: {pose_name}")
    reset_pose(armature)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    for bone_name, (rx, ry, rz) in bone_rotations.items():
        if bone_name in armature.pose.bones:
            bone = armature.pose.bones[bone_name]
            bone.rotation_mode = 'XYZ'
            bone.rotation_euler = (
                math.radians(rx),
                math.radians(ry),
                math.radians(rz)
            )
            print(f"    {bone_name}: ({rx}, {ry}, {rz})")
        else:
            print(f"    WARNING: Bone '{bone_name}' not found!")

    bpy.ops.object.mode_set(mode='OBJECT')
    # Force update
    bpy.context.view_layer.update()


def render_pose(pose_name):
    """Render the current pose to a file."""
    output_path = os.path.join(OUTPUT_DIR, f"mia_pose_{pose_name}.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"  File size: {size/1024:.0f} KB")
    return output_path


def create_test_poses():
    """Create and render test poses."""
    print("\n=== CREATING TEST POSES ===")

    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break

    if not armature:
        print("ERROR: No armature found!")
        return []

    rendered_files = []

    # Pose 0: T-Pose (rest/default)
    print("\n--- Pose 0: T-Pose (Default) ---")
    reset_pose(armature)
    rendered_files.append(render_pose("tpose"))

    # Pose 1: Victory / Arms Raised
    print("\n--- Pose 1: Victory (Arms Raised) ---")
    apply_pose(armature, "victory", {
        'LeftArm': (0, 0, 60),       # Raise left arm up
        'LeftForeArm': (0, 0, 30),    # Slight bend
        'RightArm': (0, 0, -60),      # Raise right arm up
        'RightForeArm': (0, 0, -30),  # Slight bend
        'Head': (15, 0, 0),           # Slight tilt up
        'Spine': (5, 0, 0),           # Slight lean back
    })
    rendered_files.append(render_pose("victory"))

    # Pose 2: Waving
    print("\n--- Pose 2: Waving ---")
    apply_pose(armature, "waving", {
        'RightArm': (0, -30, -80),     # Right arm raised
        'RightForeArm': (-60, 0, 0),   # Elbow bent
        'RightHand': (0, 0, 20),       # Slight hand tilt
        'Head': (0, -10, 0),           # Look slightly right
        'Spine': (0, -5, 0),           # Slight turn
    })
    rendered_files.append(render_pose("waving"))

    # Pose 3: Running
    print("\n--- Pose 3: Running ---")
    apply_pose(armature, "running", {
        'Hips': (10, 0, 0),           # Lean forward
        'Spine02': (-5, 0, 0),         # Counter-lean
        'LeftUpLeg': (-40, 0, 0),      # Left leg forward
        'LeftLeg': (50, 0, 0),         # Left knee bent
        'RightUpLeg': (30, 0, 0),      # Right leg back
        'RightLeg': (20, 0, 0),        # Right knee slight bend
        'LeftArm': (30, 0, 20),        # Left arm back
        'LeftForeArm': (30, 0, 0),     # Bent
        'RightArm': (-30, 0, -20),     # Right arm forward
        'RightForeArm': (50, 0, 0),    # Bent
        'Head': (-5, 0, 0),            # Look forward
    })
    rendered_files.append(render_pose("running"))

    # Pose 4: Sitting
    print("\n--- Pose 4: Sitting ---")
    apply_pose(armature, "sitting", {
        'Hips': (0, 0, 0),
        'LeftUpLeg': (-90, 0, 5),      # Legs bent 90 at hip
        'LeftLeg': (90, 0, 0),         # Knees bent 90
        'RightUpLeg': (-90, 0, -5),    # Legs bent 90 at hip
        'RightLeg': (90, 0, 0),        # Knees bent 90
        'LeftArm': (20, 0, 40),        # Arms relaxed
        'LeftForeArm': (30, 0, 0),
        'RightArm': (20, 0, -40),
        'RightForeArm': (30, 0, 0),
        'Spine': (-10, 0, 0),          # Slight lean back
    })
    rendered_files.append(render_pose("sitting"))

    return rendered_files


def main():
    """Main entry point."""
    print("=" * 60)
    print("MIA RIGGED MODEL TEST")
    print("=" * 60)

    # Step 1: Import
    if not os.path.exists(GLB_PATH):
        print(f"ERROR: GLB file not found at {GLB_PATH}")
        print("Download it first with: wget -O /tmp/mia_rigged.glb <url>")
        return

    import_model()

    # Step 2: Verify rig
    report = verify_rig()

    # Step 3: Setup scene
    setup_scene()

    # Step 4: Create poses and render
    rendered_files = create_test_poses()

    # Step 5: Save report
    report["rendered_files"] = rendered_files
    report_path = os.path.join(OUTPUT_DIR, "rig_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved: {report_path}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Armature found: {report['armature_found']}")
    print(f"Bone count: {report['bone_count']}")
    print(f"Humanoid standard: {report['humanoid_standard']}")
    print(f"Mesh linked to armature: {report['mesh_linked']}")
    print(f"Vertex groups: {report['vertex_groups']}")
    print(f"Mesh complexity: {report['vertex_count']:,} verts / {report['face_count']:,} faces")
    print(f"Character height: {report['character_height']}m")
    print(f"Initial pose: {report['initial_pose']}")
    print(f"Issues: {report['issues'] if report['issues'] else 'None'}")
    print(f"Renders: {len(rendered_files)} files")
    for f in rendered_files:
        print(f"  {f}")
    print("=" * 60)


if __name__ == '__main__':
    main()
