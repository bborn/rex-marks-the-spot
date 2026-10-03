"""
Build Scene 01 Living Room Layout Mockup in Blender.

Creates a simple 3D living room with furniture, props, character stand-ins,
8 named cameras, and renders all angles. This is a layout mockup for
storyboard reference — not final art.

Usage:
    xvfb-run -a blender --background --python build_scene01_layout.py
"""

import bpy
import math
import os
import mathutils

# ── Configuration ──────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.expanduser(
    "~/rex-marks-the-spot/assets/storyboards/v3/scene-01-layout"
)
BLEND_FILE = os.path.join(OUTPUT_DIR, "scene01_layout.blend")
RENDER_W = 1376
RENDER_H = 768

# Room dimensions
ROOM_W = 5.0   # X axis
ROOM_D = 4.0   # Y axis
ROOM_H = 2.7   # Z axis

# Room center is at origin. Floor at Z=0.
# Walls: X from -2.5 to 2.5, Y from -2.0 to 2.0
# "Front" camera looks from +Y toward -Y (toward TV wall at Y=-2.0)
# Window wall (behind couch) is at Y=+2.0
# TV wall is at Y=-2.0
# Left wall (from front camera) is at X=-2.5
# Right wall (from front camera) is at X=+2.5

WALL_THICKNESS = 0.1


# ── Helpers ────────────────────────────────────────────────────────────────

def clear_scene():
    """Remove all default objects."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Remove all collections' objects
    for col in bpy.data.collections:
        for obj in col.objects:
            bpy.data.objects.remove(obj, do_unlink=True)


def make_material(name, color):
    """Create a simple diffuse material. color is (R, G, B, A)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.8
    return mat


def add_cube(name, location, scale, material=None):
    """Add a cube (box) with given center location and half-extents scale."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (scale[0] * 2, scale[1] * 2, scale[2] * 2)
    bpy.ops.object.transform_apply(scale=True)
    if material:
        obj.data.materials.append(material)
    return obj


def add_cylinder(name, location, radius, depth, material=None):
    """Add a cylinder at location. depth = total height."""
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=depth, location=location, vertices=16
    )
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj


def add_plane(name, location, size_x, size_y, material=None):
    """Add a flat plane at location."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size_x, size_y, 1)
    bpy.ops.object.transform_apply(scale=True)
    if material:
        obj.data.materials.append(material)
    return obj


def add_camera(name, location, rotation_euler_deg):
    """Add a camera and return it."""
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    cam.name = name
    cam.data.name = name
    cam.rotation_euler = (
        math.radians(rotation_euler_deg[0]),
        math.radians(rotation_euler_deg[1]),
        math.radians(rotation_euler_deg[2]),
    )
    cam.data.clip_end = 50
    return cam


def point_camera_at(cam_obj, target_point):
    """Point a camera at a specific world point."""
    direction = mathutils.Vector(target_point) - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()


# ── Materials ──────────────────────────────────────────────────────────────

def create_materials():
    mats = {}
    mats['wall'] = make_material("Wall_Beige", (0.85, 0.78, 0.65, 1.0))
    mats['floor'] = make_material("Floor_Wood", (0.45, 0.30, 0.18, 1.0))
    mats['ceiling'] = make_material("Ceiling_White", (0.95, 0.95, 0.93, 1.0))
    mats['couch'] = make_material("Couch_Brown", (0.40, 0.25, 0.12, 1.0))
    mats['coffee_table'] = make_material("CoffeeTable_Wood", (0.55, 0.38, 0.22, 1.0))
    mats['armchair'] = make_material("Armchair_Gray", (0.50, 0.50, 0.50, 1.0))
    mats['tv'] = make_material("TV_Black", (0.05, 0.05, 0.05, 1.0))
    mats['media_console'] = make_material("MediaConsole_Wood", (0.50, 0.35, 0.20, 1.0))
    mats['side_table'] = make_material("SideTable_Wood", (0.50, 0.35, 0.20, 1.0))
    mats['lamp_shade'] = make_material("Lamp_Cream", (0.95, 0.90, 0.75, 1.0))
    mats['lamp_base'] = make_material("Lamp_Metal", (0.3, 0.3, 0.3, 1.0))
    mats['rug'] = make_material("Rug_Warm", (0.65, 0.45, 0.30, 1.0))
    mats['window_frame'] = make_material("Window_White", (0.9, 0.9, 0.9, 1.0))
    mats['sky'] = make_material("Sky_Storm", (0.15, 0.18, 0.30, 1.0))
    mats['door'] = make_material("Door_Dark", (0.25, 0.18, 0.12, 1.0))
    mats['dino_toy_green'] = make_material("DinoToy_Green", (0.2, 0.55, 0.2, 1.0))
    mats['dino_toy_brown'] = make_material("DinoToy_Brown", (0.45, 0.30, 0.15, 1.0))
    mats['photo_frame'] = make_material("PhotoFrame_Brown", (0.35, 0.22, 0.12, 1.0))
    mats['photo'] = make_material("Photo_Light", (0.75, 0.70, 0.65, 1.0))
    mats['plush'] = make_material("Plush_Green", (0.25, 0.60, 0.20, 1.0))
    mats['mug'] = make_material("Mug_White", (0.9, 0.88, 0.85, 1.0))
    mats['leo'] = make_material("Leo_Green", (0.15, 0.65, 0.15, 1.0))
    mats['mia'] = make_material("Mia_Pink", (0.90, 0.45, 0.60, 1.0))
    mats['jenny'] = make_material("Jenny_Coral", (0.90, 0.50, 0.40, 1.0))
    mats['ceiling_light'] = make_material("CeilingLight_Warm", (1.0, 0.95, 0.85, 1.0))
    return mats


# ── Build Scene ────────────────────────────────────────────────────────────

def build_room(mats):
    """Create floor, walls, ceiling."""
    # Floor
    add_plane("Floor", (0, 0, 0), ROOM_W / 2, ROOM_D / 2, mats['floor'])

    # Ceiling
    add_plane("Ceiling", (0, 0, ROOM_H), ROOM_W / 2, ROOM_D / 2, mats['ceiling'])

    # Back wall (behind couch, Y=+2.0) - has window cutout, we'll just make the wall
    # Left portion
    add_cube("Wall_Back_Left", (-1.7, ROOM_D/2, ROOM_H/2),
             (0.4, WALL_THICKNESS/2, ROOM_H/2), mats['wall'])
    # Right portion
    add_cube("Wall_Back_Right", (1.7, ROOM_D/2, ROOM_H/2),
             (0.4, WALL_THICKNESS/2, ROOM_H/2), mats['wall'])
    # Above window
    add_cube("Wall_Back_Top", (0, ROOM_D/2, ROOM_H - 0.25),
             (ROOM_W/2, WALL_THICKNESS/2, 0.25), mats['wall'])
    # Below window
    add_cube("Wall_Back_Bottom", (0, ROOM_D/2, 0.4),
             (ROOM_W/2, WALL_THICKNESS/2, 0.4), mats['wall'])
    # Window sill area (between left/right portions, above bottom, below top)
    # Window opening: center, 1.8m wide, 1.2m tall, bottom at 0.8m
    # Left of window
    add_cube("Wall_Back_WinL", (-1.25, ROOM_D/2, 1.4),
             (0.175, WALL_THICKNESS/2, 0.6), mats['wall'])
    # Right of window
    add_cube("Wall_Back_WinR", (1.25, ROOM_D/2, 1.4),
             (0.175, WALL_THICKNESS/2, 0.6), mats['wall'])

    # Front wall (TV wall, Y=-2.0) - omitted so front cameras can see into the room
    # The TV and media console visually anchor this wall instead.

    # Left wall (X=-2.5) - solid
    add_cube("Wall_Left", (-ROOM_W/2, 0, ROOM_H/2),
             (WALL_THICKNESS/2, ROOM_D/2, ROOM_H/2), mats['wall'])

    # Right wall (X=+2.5) - has door opening toward back
    # Door: ~0.9m wide, ~2.1m tall, centered at about X=2.5, Y=1.2
    # Below door top
    add_cube("Wall_Right_Front", (ROOM_W/2, -0.8, ROOM_H/2),
             (WALL_THICKNESS/2, 1.2, ROOM_H/2), mats['wall'])
    # Above door
    add_cube("Wall_Right_AboveDoor", (ROOM_W/2, 1.2, 2.4),
             (WALL_THICKNESS/2, 0.45, 0.3), mats['wall'])
    # Behind door
    add_cube("Wall_Right_Back", (ROOM_W/2, 1.85, ROOM_H/2),
             (WALL_THICKNESS/2, 0.15, ROOM_H/2), mats['wall'])

    # Window: blue plane behind it (stormy sky)
    add_plane("Sky_Plane", (0, ROOM_D/2 + 0.15, 1.4), 0.9, 0.6, mats['sky'])

    # Window frame (thin border)
    add_cube("Window_Frame_Top", (0, ROOM_D/2 - 0.02, 2.0),
             (0.95, 0.02, 0.03), mats['window_frame'])
    add_cube("Window_Frame_Bottom", (0, ROOM_D/2 - 0.02, 0.8),
             (0.95, 0.02, 0.03), mats['window_frame'])
    add_cube("Window_Frame_Left", (-0.9, ROOM_D/2 - 0.02, 1.4),
             (0.03, 0.02, 0.6), mats['window_frame'])
    add_cube("Window_Frame_Right", (0.9, ROOM_D/2 - 0.02, 1.4),
             (0.03, 0.02, 0.6), mats['window_frame'])

    # Door frame
    add_cube("Door_Frame", (ROOM_W/2 - 0.02, 1.2, 1.05),
             (0.04, 0.45, 1.05), mats['door'])


def build_furniture(mats):
    """Create couch, coffee table, armchair, TV, etc."""
    # ── Couch (centered, facing -Y toward TV wall) ──
    couch_y = 0.7  # toward back of room
    couch_z_seat = 0.45  # seat height

    # Seat cushion
    add_cube("Couch_Seat", (0, couch_y, couch_z_seat/2 + 0.05),
             (1.0, 0.425, couch_z_seat/2), mats['couch'])
    # Back rest
    add_cube("Couch_Back", (0, couch_y + 0.35, 0.55),
             (1.0, 0.075, 0.35), mats['couch'])
    # Left arm
    add_cube("Couch_ArmL", (-0.92, couch_y, 0.35),
             (0.1, 0.425, 0.35), mats['couch'])
    # Right arm
    add_cube("Couch_ArmR", (0.92, couch_y, 0.35),
             (0.1, 0.425, 0.35), mats['couch'])

    # ── Coffee table ──
    ct_y = couch_y - 0.85
    add_cube("CoffeeTable_Top", (0, ct_y, 0.43),
             (0.6, 0.3, 0.025), mats['coffee_table'])
    # Legs
    for dx, dy in [(-0.5, -0.22), (0.5, -0.22), (-0.5, 0.22), (0.5, 0.22)]:
        add_cube(f"CoffeeTable_Leg_{dx}_{dy}", (dx, ct_y + dy, 0.21),
                 (0.025, 0.025, 0.21), mats['coffee_table'])

    # ── Armchair (to the right of TV, from front camera = +X side, near TV wall) ──
    ac_x = 1.8
    ac_y = -1.2
    ac_z_seat = 0.45

    add_cube("Armchair_Seat", (ac_x, ac_y, ac_z_seat/2 + 0.05),
             (0.45, 0.425, ac_z_seat/2), mats['armchair'])
    add_cube("Armchair_Back", (ac_x, ac_y + 0.35, 0.55),
             (0.45, 0.075, 0.35), mats['armchair'])
    add_cube("Armchair_ArmL", (ac_x - 0.4, ac_y, 0.35),
             (0.06, 0.425, 0.35), mats['armchair'])
    add_cube("Armchair_ArmR", (ac_x + 0.4, ac_y, 0.35),
             (0.06, 0.425, 0.35), mats['armchair'])

    # ── Media console + TV (on front/TV wall, Y=-2.0) ──
    tv_y = -ROOM_D/2 + 0.3

    # Media console
    add_cube("MediaConsole", (0, tv_y, 0.25),
             (0.75, 0.2, 0.25), mats['media_console'])

    # TV (flat rectangle on top of console)
    add_cube("TV_Screen", (0, tv_y - 0.05, 0.85),
             (0.6, 0.02, 0.35), mats['tv'])
    # TV stand/neck
    add_cube("TV_Stand", (0, tv_y, 0.55),
             (0.1, 0.05, 0.05), mats['tv'])

    # ── Side tables with lamps (flanking couch) ──
    for side, sx in [("Left", -1.3), ("Right", 1.3)]:
        st_y = couch_y
        # Table
        add_cube(f"SideTable_{side}", (sx, st_y, 0.3),
                 (0.25, 0.25, 0.3), mats['side_table'])
        # Lamp base (cylinder)
        add_cylinder(f"Lamp_Base_{side}", (sx, st_y, 0.65), 0.05, 0.08, mats['lamp_base'])
        # Lamp shade (cylinder)
        add_cylinder(f"Lamp_Shade_{side}", (sx, st_y, 0.80), 0.12, 0.2, mats['lamp_shade'])

    # ── Area rug ──
    add_plane("AreaRug", (0, ct_y, 0.005), 1.25, 0.9, mats['rug'])

    # ── Ceiling light fixture (drum shape) ──
    add_cylinder("CeilingLight", (0, 0, ROOM_H - 0.08), 0.25, 0.15, mats['ceiling_light'])


def build_props(mats):
    """Dinosaur toys, wall photos, plush, mug."""
    couch_y = 0.7
    ct_y = couch_y - 0.85

    # Dinosaur toys on floor near couch
    toy_positions = [
        (-0.6, couch_y - 0.5, 0.04),
        (-0.4, couch_y - 0.55, 0.035),
        (0.3, couch_y - 0.45, 0.04),
        (0.5, couch_y - 0.6, 0.03),
        (-0.1, couch_y - 0.65, 0.035),
    ]
    for i, pos in enumerate(toy_positions):
        mat = mats['dino_toy_green'] if i % 2 == 0 else mats['dino_toy_brown']
        size = 0.03 + (i % 3) * 0.008
        add_cube(f"DinoToy_{i}", pos, (size, size, size), mat)

    # Wall photos on left wall (X=-2.5)
    photo_positions = [(-ROOM_W/2 + 0.06, -0.5, 1.5),
                       (-ROOM_W/2 + 0.06, 0.2, 1.6),
                       (-ROOM_W/2 + 0.06, 0.8, 1.45)]
    for i, pos in enumerate(photo_positions):
        # Frame
        add_cube(f"PhotoFrame_{i}", pos, (0.01, 0.18, 0.14), mats['photo_frame'])
        # Photo (slightly in front)
        add_cube(f"Photo_{i}", (pos[0] - 0.015, pos[1], pos[2]),
                 (0.005, 0.15, 0.11), mats['photo'])

    # Plush T-Rex on couch (small green lump)
    add_cube("Plush_TRex", (0.3, couch_y + 0.1, 0.55),
             (0.06, 0.06, 0.08), mats['plush'])

    # Mug on coffee table
    add_cylinder("Mug", (-0.2, ct_y, 0.48), 0.035, 0.08, mats['mug'])


def build_characters(mats):
    """Place character stand-in cylinders."""
    couch_y = 0.7
    couch_seat_z = 0.45

    # Leo - left side of couch from front camera = -X side
    # Seated, ~0.7m tall cylinder sitting on couch seat
    add_cylinder("Leo_Standin", (-0.45, couch_y, couch_seat_z + 0.35),
                 0.12, 0.7, mats['leo'])

    # Mia - right side of couch from front camera = +X side
    add_cylinder("Mia_Standin", (0.45, couch_y, couch_seat_z + 0.45),
                 0.12, 0.9, mats['mia'])

    # Jenny - in armchair
    ac_x = 1.8
    ac_y = -1.2
    add_cylinder("Jenny_Standin", (ac_x, ac_y, 0.45 + 0.5),
                 0.14, 1.0, mats['jenny'])


def build_cameras():
    """Set up all 8 named cameras."""
    couch_y = 0.7
    room_center = (0, 0, 1.2)
    couch_center = (0, couch_y, 0.8)

    cameras = {}

    # 1. cam_front_wide: Wide shot from front, looking at couch + window
    cam = add_camera("cam_front_wide", (0, -3.5, 1.5), (0, 0, 0))
    point_camera_at(cam, (0, couch_y, 1.0))
    cam.data.lens = 24
    cameras['cam_front_wide'] = cam

    # 2. cam_reverse_wide: Behind couch, looking toward TV (OTS)
    cam = add_camera("cam_reverse_wide", (0.5, 2.0, 1.6), (0, 0, 0))
    point_camera_at(cam, (0, -1.7, 0.8))
    cam.data.lens = 28
    cameras['cam_reverse_wide'] = cam

    # 3. cam_medium_couch: Medium shot of couch area
    cam = add_camera("cam_medium_couch", (0, -1.8, 1.3), (0, 0, 0))
    point_camera_at(cam, (0, couch_y, 0.7))
    cam.data.lens = 35
    cameras['cam_medium_couch'] = cam

    # 4. cam_closeup_left: Close-up near left side of couch (Mia)
    # Left from front camera = -X, but Mia is on the right (+X) from front camera
    # Actually task says "cam_closeup_left: Close-up position near the left side of the couch (for Mia close-ups)"
    # And Mia is on the right side from front camera (+X). Let me re-read...
    # "Mia (on couch, right side from front camera)" but "cam_closeup_left: for Mia close-ups"
    # This is confusing - I'll put the camera on the left side looking at the right side (at Mia)
    cam = add_camera("cam_closeup_left", (-1.2, 0.0, 1.2), (0, 0, 0))
    point_camera_at(cam, (0.45, couch_y, 0.8))
    cam.data.lens = 50
    cameras['cam_closeup_left'] = cam

    # 5. cam_closeup_right: Close-up on the right side
    cam = add_camera("cam_closeup_right", (1.5, 0.0, 1.2), (0, 0, 0))
    point_camera_at(cam, (-0.45, couch_y, 0.8))
    cam.data.lens = 50
    cameras['cam_closeup_right'] = cam

    # 6. cam_tv_closeup: Looking straight at the TV
    cam = add_camera("cam_tv_closeup", (0, 0.5, 1.0), (0, 0, 0))
    point_camera_at(cam, (0, -1.7, 0.85))
    cam.data.lens = 40
    cameras['cam_tv_closeup'] = cam

    # 7. cam_armchair: Medium shot of armchair area (Jenny)
    cam = add_camera("cam_armchair", (0.5, -0.5, 1.3), (0, 0, 0))
    point_camera_at(cam, (1.8, -1.2, 0.8))
    cam.data.lens = 40
    cameras['cam_armchair'] = cam

    # 8. cam_two_shot_center: Medium shot from center, two adults in front of couch
    cam = add_camera("cam_two_shot_center", (0, -1.5, 1.4), (0, 0, 0))
    point_camera_at(cam, (0, 0.2, 1.0))
    cam.data.lens = 35
    cameras['cam_two_shot_center'] = cam

    return cameras


def build_lighting():
    """Set up warm main lights + cool window light."""
    # Main warm key light (overhead, slightly front)
    bpy.ops.object.light_add(type='POINT', location=(0.5, -0.5, 2.5))
    key = bpy.context.active_object
    key.name = "Key_Light"
    key.data.energy = 800
    key.data.color = (1.0, 0.9, 0.7)  # warm
    key.data.shadow_soft_size = 2.0

    # Fill light (softer, from left)
    bpy.ops.object.light_add(type='POINT', location=(-2.0, 0, 2.0))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 400
    fill.data.color = (1.0, 0.92, 0.78)

    # Ceiling light (from the fixture position)
    bpy.ops.object.light_add(type='POINT', location=(0, 0, 2.55))
    ceiling = bpy.context.active_object
    ceiling.name = "Ceiling_Practical"
    ceiling.data.energy = 600
    ceiling.data.color = (1.0, 0.9, 0.75)

    # Cool window light (blue-ish, from behind couch)
    bpy.ops.object.light_add(type='AREA', location=(0, 2.3, 1.4))
    window_light = bpy.context.active_object
    window_light.name = "Window_Light"
    window_light.data.energy = 300
    window_light.data.color = (0.6, 0.7, 1.0)  # cool blue
    window_light.data.size = 1.8
    window_light.rotation_euler = (math.radians(90), 0, 0)

    # Lamp practicals (warm spots from the side table lamps)
    for side, sx in [("Left", -1.3), ("Right", 1.3)]:
        bpy.ops.object.light_add(type='POINT', location=(sx, 0.7, 0.85))
        lamp = bpy.context.active_object
        lamp.name = f"Lamp_Practical_{side}"
        lamp.data.energy = 150
        lamp.data.color = (1.0, 0.85, 0.6)

    # Extra fill from front (where the missing wall is) to brighten the scene
    bpy.ops.object.light_add(type='AREA', location=(0, -3.0, 1.5))
    front_fill = bpy.context.active_object
    front_fill.name = "Front_Fill"
    front_fill.data.energy = 200
    front_fill.data.color = (1.0, 0.95, 0.9)
    front_fill.data.size = 3.0
    front_fill.rotation_euler = (math.radians(90), 0, 0)


def setup_render():
    """Configure EEVEE render settings."""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = RENDER_W
    scene.render.resolution_y = RENDER_H
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'

    # EEVEE settings for Blender 4.0
    scene.eevee.taa_render_samples = 32

    # Set world background to dark (storm night)
    world = bpy.data.worlds.get("World")
    if not world:
        world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.05, 0.05, 0.08, 1.0)
        bg.inputs["Strength"].default_value = 0.5


def render_all_cameras(cameras):
    """Render from each camera and save to disk."""
    scene = bpy.context.scene
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for name, cam in cameras.items():
        scene.camera = cam
        filepath = os.path.join(OUTPUT_DIR, f"{name}.png")
        scene.render.filepath = filepath
        print(f"Rendering {name} ...")
        bpy.ops.render.render(write_still=True)
        print(f"  Saved: {filepath}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Building Scene 01 Living Room Layout Mockup")
    print("=" * 60)

    clear_scene()

    print("Creating materials...")
    mats = create_materials()

    print("Building room...")
    build_room(mats)

    print("Building furniture...")
    build_furniture(mats)

    print("Building props...")
    build_props(mats)

    print("Building character stand-ins...")
    build_characters(mats)

    print("Setting up lighting...")
    build_lighting()

    print("Setting up cameras...")
    cameras = build_cameras()

    print("Configuring render settings...")
    setup_render()

    print(f"Saving blend file: {BLEND_FILE}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE)

    print("Rendering all 8 camera angles...")
    render_all_cameras(cameras)

    print("=" * 60)
    print("Done! All renders saved to:", OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()
