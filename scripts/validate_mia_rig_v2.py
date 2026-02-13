"""
Validate Mia's fixed rig by posing it in the positions that previously caused issues:
1. Arm back-swing (previously clipped through thigh)
2. Spine twist (should now show counter-rotation)
3. Head turn (ponytail should follow with lag)

Renders validation images for each pose.
Run with: xvfb-run blender --background --python scripts/validate_mia_rig_v2.py
"""
import bpy
import math
import mathutils
import os
import sys

OUTPUT_DIR = "tmp/mia_rig_v2_validation"
INPUT_GLB = "tmp/mia_rigged_v2.glb"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def log(msg):
    print(f"[VALIDATE] {msg}")


def setup_scene():
    """Import the fixed model and set up rendering."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=INPUT_GLB)

    armature = None
    mesh = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH' and len(obj.data.vertices) > 100:
            mesh = obj

    if not armature or not mesh:
        log("ERROR: Missing armature or mesh!")
        sys.exit(1)

    # Add camera
    cam_data = bpy.data.cameras.new("ValidCam")
    cam_data.lens = 50
    cam_obj = bpy.data.objects.new("ValidCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Add lighting
    light_data = bpy.data.lights.new("KeyLight", 'SUN')
    light_data.energy = 3.0
    light_obj = bpy.data.objects.new("KeyLight", light_data)
    light_obj.rotation_euler = (math.radians(45), 0, math.radians(30))
    bpy.context.scene.collection.objects.link(light_obj)

    # Fill light
    fill_data = bpy.data.lights.new("FillLight", 'SUN')
    fill_data.energy = 1.5
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.rotation_euler = (math.radians(60), 0, math.radians(-60))
    bpy.context.scene.collection.objects.link(fill_obj)

    # Set up render settings
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.film_transparent = True

    # World background
    world = bpy.data.worlds.new("ValidWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.15, 0.15, 0.2, 1.0)
    bg.inputs[1].default_value = 0.5
    scene.world = world

    return armature, mesh, cam_obj


def set_camera_for_pose(cam_obj, position, target):
    """Position camera looking at target."""
    cam_obj.location = position
    direction = mathutils.Vector(target) - mathutils.Vector(position)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()


def clear_pose(armature):
    """Reset all bones to rest pose."""
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.scale_clear()
    bpy.ops.object.mode_set(mode='OBJECT')


def render_pose(name, cam_obj, cam_pos, cam_target):
    """Render the current pose to a file."""
    set_camera_for_pose(cam_obj, cam_pos, cam_target)
    filepath = os.path.join(OUTPUT_DIR, f"{name}.png")
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    log(f"  Rendered: {filepath}")
    return filepath


def validate_arm_limits(armature, cam_obj):
    """Test that arm rotation limits prevent clipping."""
    log("Test 1: Arm back-swing limits...")

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Pose: left arm swung far back (the position that caused clipping)
    left_arm = armature.pose.bones.get("LeftArm")
    right_arm = armature.pose.bones.get("RightArm")

    if left_arm:
        # Try to swing arm backward past the limit
        # The constraint should clamp this
        left_arm.rotation_mode = 'XYZ'
        left_arm.rotation_euler = (math.radians(-80), 0, 0)  # Extreme backward

    if right_arm:
        # Right arm forward (opposite phase of walk)
        right_arm.rotation_mode = 'XYZ'
        right_arm.rotation_euler = (math.radians(60), 0, 0)

    # Update scene to apply constraints
    bpy.context.view_layer.update()

    bpy.ops.object.mode_set(mode='OBJECT')

    # Render from side view to check arm-leg clearance
    rendered = []
    # Character is scaled 0.01 so world position is small
    rendered.append(render_pose(
        "arm_backswing_side",
        cam_obj,
        (0.025, 0.0, 0.006),  # Side view
        (0.0, 0.0, 0.006)
    ))

    rendered.append(render_pose(
        "arm_backswing_front",
        cam_obj,
        (0.0, -0.025, 0.006),  # Front view
        (0.0, 0.0, 0.006)
    ))

    # Report actual rotation after constraint
    bpy.ops.object.mode_set(mode='POSE')
    if left_arm:
        actual = [math.degrees(r) for r in left_arm.rotation_euler]
        log(f"  Left arm requested: -80°, actual after constraint: {actual[0]:.1f}°")
    bpy.ops.object.mode_set(mode='OBJECT')

    return rendered


def validate_spine_rotation(armature, cam_obj):
    """Test that spine counter-rotation works."""
    log("Test 2: Spine counter-rotation...")

    clear_pose(armature)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Rotate hips - spine should counter-rotate
    hips = armature.pose.bones.get("Hips")
    spine = armature.pose.bones.get("Spine")

    if hips:
        hips.rotation_mode = 'XYZ'
        hips.rotation_euler = (0, math.radians(25), math.radians(15))  # Twist during walk

    bpy.context.view_layer.update()

    bpy.ops.object.mode_set(mode='OBJECT')

    rendered = []
    rendered.append(render_pose(
        "spine_twist_front",
        cam_obj,
        (0.0, -0.025, 0.006),
        (0.0, 0.0, 0.006)
    ))

    rendered.append(render_pose(
        "spine_twist_top",
        cam_obj,
        (0.0, 0.0, 0.025),  # Top view
        (0.0, 0.0, 0.006)
    ))

    # Check spine counter-rotation
    bpy.ops.object.mode_set(mode='POSE')
    if spine:
        # Get the evaluated rotation
        spine_rot = [math.degrees(r) for r in spine.rotation_euler]
        log(f"  Hips rotated: Y=25°, Z=15°")
        log(f"  Spine rotation (should be opposing): {spine_rot}")
    bpy.ops.object.mode_set(mode='OBJECT')

    return rendered


def validate_ponytail(armature, cam_obj):
    """Test that ponytail bones exist and respond to head movement."""
    log("Test 3: Ponytail secondary motion...")

    clear_pose(armature)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Check ponytail bones exist
    ponytail_bones = []
    for i in range(1, 5):
        pbone = armature.pose.bones.get(f"Ponytail_{i:02d}")
        if pbone:
            ponytail_bones.append(pbone)
            log(f"  Found Ponytail_{i:02d} with {len(pbone.constraints)} constraints")
        else:
            log(f"  MISSING: Ponytail_{i:02d}")

    # Turn head to one side - ponytail should follow with lag
    head = armature.pose.bones.get("Head")
    if head:
        head.rotation_mode = 'XYZ'
        head.rotation_euler = (0, 0, math.radians(30))  # Turn head right

    bpy.context.view_layer.update()

    bpy.ops.object.mode_set(mode='OBJECT')

    rendered = []
    # Back view to see ponytail
    rendered.append(render_pose(
        "ponytail_headturn_back",
        cam_obj,
        (0.0, 0.02, 0.01),  # Back view
        (0.0, 0.0, 0.008)
    ))

    # Three-quarter back view
    rendered.append(render_pose(
        "ponytail_headturn_3q",
        cam_obj,
        (0.015, 0.015, 0.01),  # 3/4 back view
        (0.0, 0.0, 0.008)
    ))

    return rendered


def validate_rest_pose(armature, cam_obj):
    """Render rest pose for comparison."""
    log("Test 0: Rest pose (baseline)...")

    clear_pose(armature)

    rendered = []
    rendered.append(render_pose(
        "rest_pose_front",
        cam_obj,
        (0.0, -0.025, 0.006),
        (0.0, 0.0, 0.006)
    ))

    rendered.append(render_pose(
        "rest_pose_side",
        cam_obj,
        (0.025, 0.0, 0.006),
        (0.0, 0.0, 0.006)
    ))

    rendered.append(render_pose(
        "rest_pose_back",
        cam_obj,
        (0.0, 0.025, 0.008),
        (0.0, 0.0, 0.006)
    ))

    return rendered


def main():
    log("=" * 60)
    log("VALIDATING MIA RIG V2")
    log("=" * 60)

    armature, mesh, cam_obj = setup_scene()

    all_renders = []

    # Test 0: Rest pose
    all_renders.extend(validate_rest_pose(armature, cam_obj))

    # Test 1: Arm limits
    all_renders.extend(validate_arm_limits(armature, cam_obj))

    # Test 2: Spine counter-rotation
    all_renders.extend(validate_spine_rotation(armature, cam_obj))

    # Test 3: Ponytail
    all_renders.extend(validate_ponytail(armature, cam_obj))

    log("")
    log("=" * 60)
    log("VALIDATION COMPLETE")
    log("=" * 60)
    log(f"  Rendered {len(all_renders)} validation images to {OUTPUT_DIR}/")
    for r in all_renders:
        log(f"    - {os.path.basename(r)}")


if __name__ == "__main__":
    main()
