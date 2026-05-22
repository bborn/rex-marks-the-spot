"""Probe jetplane.blend: list contents to see if it has a usable mesh."""
import bpy
import sys

print("=== JETPLANE BLEND PROBE ===")
print(f"Scenes: {[s.name for s in bpy.data.scenes]}")
print(f"Objects: {len(bpy.data.objects)}")
for obj in bpy.data.objects:
    print(f"  - {obj.name} ({obj.type}) verts={len(obj.data.vertices) if obj.type == 'MESH' else 'n/a'}")
print(f"Meshes: {[m.name for m in bpy.data.meshes]}")
print(f"Materials: {[m.name for m in bpy.data.materials]}")
print(f"Cameras: {[c.name for c in bpy.data.cameras]}")
print(f"Lights: {[l.name for l in bpy.data.lights]}")
sys.stdout.flush()
