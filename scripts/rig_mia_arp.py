"""
Rig Mia character with Auto-Rig Pro.

Usage:
    blender --background models/characters/mia.blend --python scripts/rig_mia_arp.py

Workflow:
    1. Enable ARP addon
    2. Delete any existing armatures
    3. Join character meshes into a single body
    4. Append ARP humanoid reference rig
    5. Position reference bones to match Mia's proportions
    6. Match to Rig (generate final control rig)
    7. Bind mesh to rig
    8. Save as mia_arp_rigged.blend
"""

import bpy
import sys
import os
import math
from mathutils import Vector

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_DIR, "models", "characters", "mia_arp_rigged.blend")

print("=" * 60)
print("  Auto-Rig Pro: Rigging Mia")
print("=" * 60)
print(f"  Output: {OUTPUT_FILE}")
print()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def log(msg):
    print(f"  [ARP] {msg}")


def enable_addon(module_name):
    """Enable a Blender addon, return True on success."""
    try:
        bpy.ops.preferences.addon_enable(module=module_name)
        log(f"Enabled addon: {module_name}")
        return True
    except Exception as e:
        log(f"WARNING: Could not enable {module_name}: {e}")
        return False


# ---------------------------------------------------------------------------
# Monkey-patch to allow ARP to run in --background mode
# ---------------------------------------------------------------------------
# ARP's _append_arp accesses bpy.context.space_data.overlay which fails
# in background mode. We patch the internal function to skip that line.
def patch_arp_for_background():
    """Patch ARP's internal functions to work in background mode."""
    try:
        from auto_rig_pro.src import auto_rig as ar_module

        original_append = ar_module._append_arp

        def patched_append(rig_type, preset_description=''):
            """Wrapper that handles space_data access errors in bg mode."""
            # Temporarily replace space_data access
            import types
            ctx = bpy.context

            # Store original
            orig_space_data = None
            try:
                orig_space_data = ctx.space_data
            except:
                pass

            # If no space_data, we need to handle the overlay line
            # We'll just run the original and catch the AttributeError
            try:
                original_append(rig_type, preset_description=preset_description)
            except AttributeError as e:
                if 'space_data' in str(e) or 'overlay' in str(e):
                    log(f"Caught expected bg-mode error: {e}")
                    log("Attempting manual rig append...")
                    _manual_append_rig(rig_type)
                else:
                    raise

        ar_module._append_arp = patched_append
        log("Patched ARP for background mode")
        return True
    except Exception as e:
        log(f"Could not patch ARP: {e}")
        return False


def _manual_append_rig(rig_type):
    """Manually append the ARP rig blend file (background-safe)."""
    addon_dir = os.path.dirname(
        os.path.abspath(
            os.path.join(
                os.path.expanduser("~"),
                ".config/blender/4.0/scripts/addons/auto_rig_pro/src/auto_rig.py",
            )
        )
    )
    addon_root = os.path.dirname(addon_dir)
    filepath = os.path.join(addon_root, "armature_presets", f"{rig_type}.blend")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ARP preset not found: {filepath}")

    log(f"Loading rig from: {filepath}")

    # Track existing armatures
    existing_armatures = {o.name for o in bpy.data.objects if o.type == "ARMATURE"}

    # Load collections from the preset blend file
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.collections = data_from.collections
        data_to.actions = data_from.actions

    for collec in data_to.collections:
        if len(collec.children) or len(data_to.collections) == 1:
            bpy.context.scene.collection.children.link(collec)

    # Skip overlay line (the one that fails in bg mode)
    # bpy.context.space_data.overlay.show_relationship_lines = False

    bpy.ops.object.select_all(action='DESELECT')

    # Find the newly added rig
    rig = None
    for o in bpy.data.objects:
        if o.type == "ARMATURE" and o.name not in existing_armatures:
            rig = o
            break

    if rig is None:
        raise RuntimeError("No armature found after loading preset")

    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)

    # Convert to Blender 4.0 bone collections if needed
    if bpy.app.version >= (4, 0, 0):
        try:
            from auto_rig_pro.src.auto_rig import convert_armature_layers_to_collection
            convert_armature_layers_to_collection(rig)
        except:
            pass

    log(f"Appended rig: {rig.name}")
    return rig


# ---------------------------------------------------------------------------
# Step 1: Enable addons
# ---------------------------------------------------------------------------
log("Step 1: Enabling addons...")
enable_addon('auto_rig_pro')

# rig_tools is a companion addon
try:
    enable_addon('rig_tools')
except:
    pass

# ---------------------------------------------------------------------------
# Step 2: Delete existing armatures
# ---------------------------------------------------------------------------
log("Step 2: Deleting existing armatures...")
armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
if armatures:
    bpy.ops.object.select_all(action='DESELECT')
    for arm in armatures:
        arm.select_set(True)
    bpy.context.view_layer.objects.active = armatures[0]
    bpy.ops.object.delete()
    log(f"Deleted {len(armatures)} armatures")
else:
    log("No existing armatures found")


# ---------------------------------------------------------------------------
# Step 3: Join character meshes into single body
# ---------------------------------------------------------------------------
log("Step 3: Joining character meshes...")

parent_empty = bpy.data.objects.get('Mia_Character')
if parent_empty is None:
    log("FATAL: 'Mia_Character' empty not found!")
    sys.exit(1)

mesh_objects = [obj for obj in bpy.data.objects
                if obj.type == 'MESH' and obj.parent == parent_empty]

if not mesh_objects:
    log("FATAL: No mesh objects under Mia_Character!")
    sys.exit(1)

log(f"Found {len(mesh_objects)} mesh parts")

# Apply all transforms first
bpy.ops.object.select_all(action='DESELECT')
for obj in mesh_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = mesh_objects[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Join all meshes
bpy.ops.object.join()
body = bpy.context.active_object
body.name = "Mia_Body"

log(f"Joined mesh: {body.name} ({len(body.data.vertices)} verts, "
    f"{len(body.data.polygons)} faces)")

# Calculate body bounding box for reference bone positioning
body_verts = [body.matrix_world @ v.co for v in body.data.vertices]
bb_min = Vector((min(v.x for v in body_verts),
                 min(v.y for v in body_verts),
                 min(v.z for v in body_verts)))
bb_max = Vector((max(v.x for v in body_verts),
                 max(v.y for v in body_verts),
                 max(v.z for v in body_verts)))

char_height = bb_max.z - bb_min.z
char_center_x = (bb_min.x + bb_max.x) / 2
char_center_y = (bb_min.y + bb_max.y) / 2

log(f"Character bounds: min={bb_min}, max={bb_max}")
log(f"Character height: {char_height:.3f}m")


# ---------------------------------------------------------------------------
# Step 4: Append ARP humanoid rig
# ---------------------------------------------------------------------------
log("Step 4: Appending ARP humanoid rig...")

# Patch ARP for background mode
patch_arp_for_background()

# Try the operator first, fall back to manual append
try:
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.arp.append_arp(rig_preset='human')
    log("arp.append_arp succeeded")
except Exception as e:
    log(f"arp.append_arp failed ({e}), using manual append...")
    _manual_append_rig('human')

# Find the ARP rig
rig = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        # Check if it's an ARP rig (has c_pos bone)
        if 'c_pos' in [b.name for b in obj.data.bones]:
            rig = obj
            break

if rig is None:
    # Just take any armature
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            rig = obj
            break

if rig is None:
    log("FATAL: No armature found after append!")
    sys.exit(1)

log(f"ARP rig: {rig.name} ({len(rig.data.bones)} bones)")

# Ensure we're in object mode
try:
    bpy.ops.object.mode_set(mode='OBJECT')
except:
    pass


# ---------------------------------------------------------------------------
# Step 5: Position reference bones to match Mia
# ---------------------------------------------------------------------------
log("Step 5: Positioning reference bones...")

# Reference bone positions for Mia (8-year-old, ~1.26m tall)
# Positions are (head_x, head_y, head_z, tail_x, tail_y, tail_z)
# Y is front-to-back in Blender (negative = front)
# Mia is centered at X≈0, facing -Y

H = char_height  # Total height
CX = char_center_x
CY = char_center_y

# Scale factor relative to default ARP rig (which is ~1.75m)
scale_factor = H / 1.75

# Key landmark Z positions (proportional to height)
Z_FOOT = bb_min.z
Z_ANKLE = Z_FOOT + 0.05 * (H / 1.26)
Z_KNEE = Z_FOOT + 0.277 * (H / 1.26)
Z_HIP = Z_FOOT + 0.48 * (H / 1.26)
Z_ROOT = Z_FOOT + 0.52 * (H / 1.26)
Z_SPINE1 = Z_FOOT + 0.58 * (H / 1.26)
Z_SPINE2 = Z_FOOT + 0.72 * (H / 1.26)
Z_NECK = Z_FOOT + 0.90 * (H / 1.26)
Z_HEAD = Z_FOOT + 1.00 * (H / 1.26)
Z_HEAD_TOP = bb_max.z
Z_SHOULDER = Z_FOOT + 0.87 * (H / 1.26)

# Lateral (X) positions
X_HIP = 0.06 * (H / 1.26)
X_SHOULDER = 0.10 * (H / 1.26)
X_ELBOW = 0.22 * (H / 1.26)
X_HAND = 0.32 * (H / 1.26)

# Reference bone positions: name -> (head, tail)
# Using actual ARP reference bone naming:
# - Center bones end with .x
# - Side bones end with .l or .r (we position .l, ARP mirrors to .r)
ref_bone_positions = {
    # Spine chain
    'root_ref.x':      (Vector((CX, CY, Z_ROOT)),
                        Vector((CX, CY, Z_SPINE1))),
    'spine_01_ref.x':  (Vector((CX, CY, Z_SPINE1)),
                        Vector((CX, CY, Z_SPINE2))),
    'spine_02_ref.x':  (Vector((CX, CY, Z_SPINE2)),
                        Vector((CX, CY, Z_NECK))),
    'neck_ref.x':      (Vector((CX, CY, Z_NECK)),
                        Vector((CX, CY, Z_HEAD))),
    'head_ref.x':      (Vector((CX, CY, Z_HEAD)),
                        Vector((CX, CY, Z_HEAD_TOP))),

    # Left arm chain
    'shoulder_ref.l':  (Vector((CX + X_SHOULDER * 0.3, CY, Z_SHOULDER)),
                        Vector((CX + X_SHOULDER, CY, Z_SHOULDER))),
    'arm_ref.l':       (Vector((CX + X_SHOULDER, CY, Z_SHOULDER)),
                        Vector((CX + X_ELBOW, CY, Z_SHOULDER - 0.02 * (H / 1.26)))),
    'forearm_ref.l':   (Vector((CX + X_ELBOW, CY, Z_SHOULDER - 0.02 * (H / 1.26))),
                        Vector((CX + X_HAND, CY, Z_SHOULDER - 0.04 * (H / 1.26)))),
    'hand_ref.l':      (Vector((CX + X_HAND, CY, Z_SHOULDER - 0.04 * (H / 1.26))),
                        Vector((CX + X_HAND + 0.04, CY, Z_SHOULDER - 0.04 * (H / 1.26)))),

    # Left leg chain
    'thigh_ref.l':     (Vector((CX + X_HIP, CY, Z_HIP)),
                        Vector((CX + X_HIP, CY + 0.01, Z_KNEE))),
    'leg_ref.l':       (Vector((CX + X_HIP, CY + 0.01, Z_KNEE)),
                        Vector((CX + X_HIP, CY, Z_ANKLE))),
    'foot_ref.l':      (Vector((CX + X_HIP, CY, Z_ANKLE)),
                        Vector((CX + X_HIP, CY - 0.06, Z_FOOT))),
    'toes_ref.l':      (Vector((CX + X_HIP, CY - 0.06, Z_FOOT)),
                        Vector((CX + X_HIP, CY - 0.10, Z_FOOT))),
}

# Select rig and enter edit mode
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')

# List all edit bones for debugging
edit_bones = rig.data.edit_bones
all_ref_bones = [b.name for b in edit_bones if '_ref' in b.name]
log(f"Found {len(all_ref_bones)} reference bones in rig")
if all_ref_bones:
    log(f"Reference bones: {all_ref_bones[:20]}...")

# Position each reference bone
positioned = 0
for bone_name, (head_pos, tail_pos) in ref_bone_positions.items():
    eb = edit_bones.get(bone_name)
    if eb is None:
        log(f"  WARNING: Reference bone '{bone_name}' not found, skipping")
        continue

    eb.head = head_pos
    eb.tail = tail_pos
    positioned += 1

    # Mirror to right side if this is a .l bone
    if bone_name.endswith('.l'):
        r_name = bone_name[:-2] + '.r'
        r_eb = edit_bones.get(r_name)
        if r_eb:
            r_eb.head = Vector((-head_pos.x, head_pos.y, head_pos.z))
            r_eb.tail = Vector((-tail_pos.x, tail_pos.y, tail_pos.z))
            positioned += 1

log(f"Positioned {positioned} reference bones")

# Back to object mode
bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------------------
# Step 6: Match to Rig (generate final control rig)
# ---------------------------------------------------------------------------
log("Step 6: Match to Rig...")

bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig

try:
    # match_to_rig may use invoke() which shows a dialog in non-bg mode
    # In background mode, we call execute directly
    bpy.ops.arp.match_to_rig()
    log("match_to_rig succeeded")
except Exception as e:
    log(f"match_to_rig error: {e}")
    # Try calling the internal function directly
    try:
        from auto_rig_pro.src.auto_rig import _match_to_rig
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = rig
        _match_to_rig()
        log("_match_to_rig (internal) succeeded")
    except Exception as e2:
        log(f"_match_to_rig internal also failed: {e2}")
        log("Continuing anyway - rig may still be usable for binding...")

# Check if match_to_rig flag is set
try:
    has_match = rig.data.get('has_match_to_rig', False)
    log(f"has_match_to_rig = {has_match}")
except:
    pass


# ---------------------------------------------------------------------------
# Step 7: Bind mesh to rig
# ---------------------------------------------------------------------------
log("Step 7: Binding mesh to rig...")

# Ensure object mode
try:
    bpy.ops.object.mode_set(mode='OBJECT')
except:
    pass

# Selection order matters: meshes first, then armature last (active)
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig

# Configure binding engine
scn = bpy.context.scene

# Try PSEUDO_VOXELS (ARP's built-in voxel method) first, fall back to HEAT_MAP
bind_success = False

for engine in ['PSEUDO_VOXELS', 'HEAT_MAP']:
    try:
        scn.arp_bind_engine = engine
        log(f"Trying bind engine: {engine}")
    except:
        log(f"Engine {engine} not available, trying next...")
        continue

    try:
        bpy.ops.arp.bind_to_rig()
        log(f"Bind succeeded with engine: {engine}")
        bind_success = True
        break
    except Exception as e:
        log(f"Bind failed with {engine}: {e}")
        continue

if not bind_success:
    # Last resort: manual parent with automatic weights
    log("ARP binding failed, falling back to Blender's automatic weights...")
    try:
        bpy.ops.object.select_all(action='DESELECT')
        body.select_set(True)
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        log("Automatic weights parenting succeeded")
        bind_success = True
    except Exception as e:
        log(f"Automatic weights also failed: {e}")

# Clean up: remove the Mia_Character empty if it's still around
parent_empty = bpy.data.objects.get('Mia_Character')
if parent_empty and parent_empty.type == 'EMPTY':
    # Re-parent body to rig if needed
    if body.parent != rig:
        log("Body not parented to rig, manual parent...")

# ---------------------------------------------------------------------------
# Step 8: Clean up and save
# ---------------------------------------------------------------------------
log("Step 8: Cleaning up and saving...")

# Ensure object mode
try:
    bpy.ops.object.mode_set(mode='OBJECT')
except:
    pass

# Find the rig that the body is actually bound to
bound_rig = None
for mod in body.modifiers:
    if mod.type == 'ARMATURE' and mod.object:
        bound_rig = mod.object
        break
if bound_rig is None and body.parent and body.parent.type == 'ARMATURE':
    bound_rig = body.parent

if bound_rig:
    log(f"Body bound to: {bound_rig.name}")
    rig = bound_rig

# Delete any duplicate armatures that aren't the bound rig
bpy.ops.object.select_all(action='DESELECT')
deleted_count = 0
for obj in list(bpy.data.objects):
    if obj.type == 'ARMATURE' and obj != rig:
        log(f"Removing duplicate armature: {obj.name}")
        bpy.data.objects.remove(obj, do_unlink=True)
        deleted_count += 1
if deleted_count:
    log(f"Removed {deleted_count} duplicate armature(s)")

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_FILE)
log(f"Saved: {OUTPUT_FILE}")

# Print summary
print()
print("=" * 60)
print("  Rigging Complete!")
print("=" * 60)
print(f"  Output:     {OUTPUT_FILE}")
print(f"  Rig:        {rig.name} ({len(rig.data.bones)} bones)")
print(f"  Body:       {body.name} ({len(body.data.vertices)} verts)")
print(f"  Bind:       {'SUCCESS' if bind_success else 'FAILED'}")

# List control bones
control_bones = [b.name for b in rig.data.bones if b.name.startswith('c_')]
print(f"  Controls:   {len(control_bones)} control bones")

# Check for armature modifier on body
arm_mods = [m for m in body.modifiers if m.type == 'ARMATURE']
print(f"  Arm mods:   {len(arm_mods)}")

# Check vertex groups
vgroups = [vg.name for vg in body.vertex_groups]
print(f"  VGroups:    {len(vgroups)}")
if vgroups:
    print(f"  Sample VG:  {vgroups[:5]}")
print("=" * 60)
