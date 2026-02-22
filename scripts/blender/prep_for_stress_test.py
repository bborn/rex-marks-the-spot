"""
Prepare the rigged blend file for stress testing.
- Removes/hides the metarig
- Ensures the generated rig is visible and active
- The stress_test_poses.py will find the correct armature

Usage:
    blender model_rigged.blend --background --python scripts/blender/prep_for_stress_test.py
"""

import bpy


def main():
    # Find and remove or hide the metarig
    metarig = bpy.data.objects.get("Mia_Metarig")
    if metarig:
        # Delete it entirely so the stress test finds the right armature
        bpy.data.objects.remove(metarig, do_unlink=True)
        print("Removed metarig")

    # Ensure the generated rig is visible
    rig = bpy.data.objects.get("Mia_Rig")
    if rig:
        rig.hide_viewport = False
        rig.hide_render = False
        rig.hide_set(False)
        print(f"Rig visible: {rig.name} with {len(rig.data.bones)} bones")
    else:
        print("ERROR: Mia_Rig not found!")
        # List all armatures
        for obj in bpy.context.scene.objects:
            if obj.type == 'ARMATURE':
                print(f"  Found armature: {obj.name}")

    # Save
    bpy.ops.wm.save_mainfile()
    print("Saved")


main()
