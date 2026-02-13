"""
Render validation poses for Mia rig v2 with correct camera positioning.
The character is at armature scale 0.01, so effective height ~0.012 in world space.
Run with: xvfb-run blender --background --python scripts/render_mia_v2_poses.py
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
    print(f"[RENDER] {msg}")


def setup_scene():
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

    # Get actual mesh bounding box in world space
    bbox_corners = [mesh.matrix_world @ mathutils.Vector(c) for c in mesh.bound_box]
    min_co = mathutils.Vector((
        min(c.x for c in bbox_corners),
        min(c.y for c in bbox_corners),
        min(c.z for c in bbox_corners)
    ))
    max_co = mathutils.Vector((
        max(c.x for c in bbox_corners),
        max(c.y for c in bbox_corners),
        max(c.z for c in bbox_corners)
    ))
    center = (min_co + max_co) / 2
    size = max_co - min_co

    log(f"  Mesh center: [{center.x:.4f}, {center.y:.4f}, {center.z:.4f}]")
    log(f"  Mesh size: [{size.x:.4f}, {size.y:.4f}, {size.z:.4f}]")

    # Camera distance based on character size
    cam_dist = max(size.x, size.y, size.z) * 2.5

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

    fill_data = bpy.data.lights.new("FillLight", 'SUN')
    fill_data.energy = 1.5
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.rotation_euler = (math.radians(60), 0, math.radians(-60))
    bpy.context.scene.collection.objects.link(fill_obj)

    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.film_transparent = True

    world = bpy.data.worlds.new("ValidWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.12, 0.12, 0.18, 1.0)
    bg.inputs[1].default_value = 0.5
    scene.world = world

    return armature, mesh, cam_obj, center, cam_dist


def set_camera(cam_obj, position, target):
    cam_obj.location = position
    direction = mathutils.Vector(target) - mathutils.Vector(position)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()


def clear_pose(armature):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.scale_clear()
    bpy.ops.object.mode_set(mode='OBJECT')


def render(name):
    filepath = os.path.join(OUTPUT_DIR, f"{name}.png")
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    log(f"  Rendered: {name}.png")


def main():
    log("=" * 60)
    log("RENDERING MIA RIG V2 VALIDATION POSES")
    log("=" * 60)

    armature, mesh, cam_obj, center, cam_dist = setup_scene()

    # --- REST POSE ---
    log("Rendering rest pose...")
    clear_pose(armature)

    # Front view
    set_camera(cam_obj,
        (center.x, center.y - cam_dist, center.z),
        center)
    render("v2_rest_front")

    # Side view
    set_camera(cam_obj,
        (center.x + cam_dist, center.y, center.z),
        center)
    render("v2_rest_side")

    # Back view
    set_camera(cam_obj,
        (center.x, center.y + cam_dist, center.z),
        center)
    render("v2_rest_back")

    # --- ARM BACKSWING POSE ---
    log("Rendering arm backswing pose...")
    clear_pose(armature)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    # Simulate walk mid-stride: left arm back, right arm forward
    left_arm = armature.pose.bones.get("LeftArm")
    right_arm = armature.pose.bones.get("RightArm")
    left_forearm = armature.pose.bones.get("LeftForeArm")
    right_forearm = armature.pose.bones.get("RightForeArm")

    if left_arm:
        left_arm.rotation_mode = 'XYZ'
        left_arm.rotation_euler = (math.radians(-70), 0, 0)  # Strong backward swing
    if right_arm:
        right_arm.rotation_mode = 'XYZ'
        right_arm.rotation_euler = (math.radians(50), 0, 0)  # Forward swing
    if left_forearm:
        left_forearm.rotation_mode = 'XYZ'
        left_forearm.rotation_euler = (math.radians(20), 0, 0)
    if right_forearm:
        right_forearm.rotation_mode = 'XYZ'
        right_forearm.rotation_euler = (math.radians(40), 0, 0)

    # Also add slight leg swing for walking context
    left_upleg = armature.pose.bones.get("LeftUpLeg")
    right_upleg = armature.pose.bones.get("RightUpLeg")
    if left_upleg:
        left_upleg.rotation_mode = 'XYZ'
        left_upleg.rotation_euler = (math.radians(30), 0, 0)  # Forward
    if right_upleg:
        right_upleg.rotation_mode = 'XYZ'
        right_upleg.rotation_euler = (math.radians(-20), 0, 0)  # Back

    bpy.context.view_layer.update()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Side view (critical for arm-leg clipping check)
    set_camera(cam_obj,
        (center.x + cam_dist, center.y, center.z),
        center)
    render("v2_arm_backswing_side")

    # Front view
    set_camera(cam_obj,
        (center.x, center.y - cam_dist, center.z),
        center)
    render("v2_arm_backswing_front")

    # 3/4 view
    set_camera(cam_obj,
        (center.x + cam_dist * 0.7, center.y - cam_dist * 0.7, center.z),
        center)
    render("v2_arm_backswing_3q")

    # --- SPINE COUNTER-ROTATION POSE ---
    log("Rendering spine twist pose...")
    clear_pose(armature)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    hips = armature.pose.bones.get("Hips")
    if hips:
        hips.rotation_mode = 'XYZ'
        hips.rotation_euler = (0, math.radians(20), math.radians(15))

    bpy.context.view_layer.update()

    # Check spine counter-rotation effect
    spine = armature.pose.bones.get("Spine")
    if spine:
        # The constraint should have applied counter-rotation
        mat = spine.matrix
        euler = mat.to_euler()
        log(f"  Spine evaluated rotation: X={math.degrees(euler.x):.1f} Y={math.degrees(euler.y):.1f} Z={math.degrees(euler.z):.1f}")

    bpy.ops.object.mode_set(mode='OBJECT')

    set_camera(cam_obj,
        (center.x, center.y - cam_dist, center.z),
        center)
    render("v2_spine_twist_front")

    # Top view
    set_camera(cam_obj,
        (center.x, center.y, center.z + cam_dist),
        center)
    render("v2_spine_twist_top")

    # --- PONYTAIL TEST ---
    log("Rendering ponytail head-turn pose...")
    clear_pose(armature)

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    head = armature.pose.bones.get("Head")
    if head:
        head.rotation_mode = 'XYZ'
        head.rotation_euler = (0, 0, math.radians(25))  # Turn head right

    bpy.context.view_layer.update()

    # Check ponytail response
    for i in range(1, 5):
        pbone = armature.pose.bones.get(f"Ponytail_{i:02d}")
        if pbone:
            mat = pbone.matrix
            euler = mat.to_euler()
            log(f"  Ponytail_{i:02d} rotation: X={math.degrees(euler.x):.1f} Y={math.degrees(euler.y):.1f} Z={math.degrees(euler.z):.1f}")

    bpy.ops.object.mode_set(mode='OBJECT')

    # Back view (shows ponytail best)
    set_camera(cam_obj,
        (center.x, center.y + cam_dist, center.z + cam_dist * 0.3),
        (center.x, center.y, center.z + center.z * 0.3))
    render("v2_ponytail_back")

    # 3/4 back view
    set_camera(cam_obj,
        (center.x + cam_dist * 0.5, center.y + cam_dist * 0.7, center.z + cam_dist * 0.2),
        (center.x, center.y, center.z + center.z * 0.3))
    render("v2_ponytail_3q_back")

    log("")
    log("=" * 60)
    log("ALL VALIDATION RENDERS COMPLETE")
    log("=" * 60)


if __name__ == "__main__":
    main()
