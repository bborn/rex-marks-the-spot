"""
Object Creation and Manipulation

Utilities for creating, modifying, and transforming 3D objects in Blender.
"""

import bpy
import math
from typing import Optional, Tuple, List, Union


# Type aliases
Vector3 = Tuple[float, float, float]
Color4 = Tuple[float, float, float, float]


def get(name: str) -> Optional[bpy.types.Object]:
    """
    Get an object by name.

    Args:
        name: The object name

    Returns:
        The object or None if not found
    """
    return bpy.data.objects.get(name)


def select(obj: Union[bpy.types.Object, str], exclusive: bool = True) -> bpy.types.Object:
    """
    Select an object.

    Args:
        obj: Object or object name
        exclusive: If True, deselect all other objects first

    Returns:
        The selected object
    """
    if isinstance(obj, str):
        obj = bpy.data.objects.get(obj)

    if exclusive:
        bpy.ops.object.select_all(action='DESELECT')

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def delete(obj: Union[bpy.types.Object, str]) -> bool:
    """
    Delete an object.

    Args:
        obj: Object or object name

    Returns:
        True if deleted, False if not found
    """
    if isinstance(obj, str):
        obj = bpy.data.objects.get(obj)

    if obj is None:
        return False

    bpy.data.objects.remove(obj, do_unlink=True)
    return True


def transform(
    obj: Union[bpy.types.Object, str],
    location: Optional[Vector3] = None,
    rotation: Optional[Vector3] = None,
    scale: Optional[Vector3] = None
) -> bpy.types.Object:
    """
    Set object transformation.

    Args:
        obj: Object or object name
        location: (x, y, z) position
        rotation: (x, y, z) rotation in degrees
        scale: (x, y, z) scale factors

    Returns:
        The transformed object
    """
    if isinstance(obj, str):
        obj = bpy.data.objects.get(obj)

    if location:
        obj.location = location

    if rotation:
        obj.rotation_euler = tuple(math.radians(r) for r in rotation)

    if scale:
        obj.scale = scale

    return obj


def parent(child: Union[bpy.types.Object, str], parent_obj: Union[bpy.types.Object, str]) -> None:
    """
    Set parent-child relationship.

    Args:
        child: Child object or name
        parent_obj: Parent object or name
    """
    if isinstance(child, str):
        child = bpy.data.objects.get(child)
    if isinstance(parent_obj, str):
        parent_obj = bpy.data.objects.get(parent_obj)

    child.parent = parent_obj


def duplicate(
    obj: Union[bpy.types.Object, str],
    name: Optional[str] = None,
    linked: bool = False
) -> bpy.types.Object:
    """
    Duplicate an object.

    Args:
        obj: Object or object name to duplicate
        name: Name for the new object (None for auto)
        linked: If True, share mesh data

    Returns:
        The duplicated object
    """
    if isinstance(obj, str):
        obj = bpy.data.objects.get(obj)

    new_obj = obj.copy()
    if not linked:
        new_obj.data = obj.data.copy()

    if name:
        new_obj.name = name

    bpy.context.collection.objects.link(new_obj)
    return new_obj


# Primitive Creation Functions

def create_cube(
    name: str = "Cube",
    size: float = 2.0,
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """Create a cube."""
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def create_sphere(
    name: str = "Sphere",
    radius: float = 1.0,
    segments: int = 32,
    rings: int = 16,
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """Create a UV sphere."""
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius,
        segments=segments,
        ring_count=rings,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def create_cylinder(
    name: str = "Cylinder",
    radius: float = 1.0,
    depth: float = 2.0,
    vertices: int = 32,
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """Create a cylinder."""
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=depth,
        vertices=vertices,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def create_cone(
    name: str = "Cone",
    radius1: float = 1.0,
    radius2: float = 0.0,
    depth: float = 2.0,
    vertices: int = 32,
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """Create a cone."""
    bpy.ops.mesh.primitive_cone_add(
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        vertices=vertices,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def create_plane(
    name: str = "Plane",
    size: float = 2.0,
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """Create a plane."""
    bpy.ops.mesh.primitive_plane_add(size=size, location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def create_torus(
    name: str = "Torus",
    major_radius: float = 1.0,
    minor_radius: float = 0.25,
    major_segments: int = 48,
    minor_segments: int = 12,
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """Create a torus."""
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=major_segments,
        minor_segments=minor_segments,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def create_empty(
    name: str = "Empty",
    display_type: str = 'PLAIN_AXES',
    size: float = 1.0,
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """
    Create an empty object.

    Args:
        name: Object name
        display_type: 'PLAIN_AXES', 'ARROWS', 'CIRCLE', 'CUBE', 'SPHERE', etc.
        size: Display size
        location: Position
    """
    bpy.ops.object.empty_add(type=display_type, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.empty_display_size = size
    return obj


def create_text(
    name: str = "Text",
    text: str = "Text",
    size: float = 1.0,
    extrude: float = 0.0,
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """Create a 3D text object."""
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.body = text
    obj.data.size = size
    obj.data.extrude = extrude
    return obj


# Compound Object Creators

def create_ground(
    name: str = "Ground",
    size: float = 20.0,
    color: Color4 = (0.3, 0.3, 0.3, 1.0)
) -> bpy.types.Object:
    """
    Create a ground plane with a basic material.

    Args:
        name: Object name
        size: Plane size
        color: RGBA color for the material
    """
    from . import materials

    plane = create_plane(name=name, size=size, location=(0, 0, 0))
    mat = materials.create_principled(f"{name}_Material", color=color, roughness=0.8)
    materials.assign(plane, mat)
    return plane


def create_character_placeholder(
    name: str = "Character",
    height: float = 2.0,
    color: Color4 = (0.8, 0.4, 0.2, 1.0),
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """
    Create a simple character placeholder (capsule shape).

    Args:
        name: Base name for the character
        height: Total height
        color: RGBA color
        location: Base position
    """
    from . import materials

    body_height = height * 0.6
    head_radius = height * 0.15
    body_radius = height * 0.2

    x, y, z = location

    # Body
    body = create_cylinder(
        name=f"{name}_Body",
        radius=body_radius,
        depth=body_height,
        location=(x, y, z + body_height / 2)
    )

    # Head
    head = create_sphere(
        name=f"{name}_Head",
        radius=head_radius,
        location=(x, y, z + body_height + head_radius * 0.8)
    )

    # Create and apply material
    mat = materials.create_principled(f"{name}_Material", color=color, roughness=0.5)
    materials.assign(body, mat)
    materials.assign(head, mat)

    # Parent head to body
    head.parent = body

    return body


def create_simple_tree(
    name: str = "Tree",
    height: float = 3.0,
    trunk_color: Color4 = (0.4, 0.25, 0.1, 1.0),
    foliage_color: Color4 = (0.1, 0.6, 0.2, 1.0),
    location: Vector3 = (0, 0, 0)
) -> bpy.types.Object:
    """
    Create a simple tree (trunk + cone foliage).

    Args:
        name: Base name for the tree
        height: Total tree height
        trunk_color: RGBA color for trunk
        foliage_color: RGBA color for foliage
        location: Base position
    """
    from . import materials

    trunk_height = height * 0.33
    trunk_radius = height * 0.05
    foliage_height = height * 0.5
    foliage_radius = height * 0.27

    x, y, z = location

    # Trunk
    trunk = create_cylinder(
        name=f"{name}_Trunk",
        radius=trunk_radius,
        depth=trunk_height,
        location=(x, y, z + trunk_height / 2)
    )

    # Foliage
    foliage = create_cone(
        name=f"{name}_Foliage",
        radius1=foliage_radius,
        depth=foliage_height,
        location=(x, y, z + trunk_height + foliage_height / 2)
    )

    # Materials
    trunk_mat = materials.create_principled(f"{name}_Trunk_Mat", color=trunk_color, roughness=0.9)
    foliage_mat = materials.create_principled(f"{name}_Foliage_Mat", color=foliage_color, roughness=0.7)

    materials.assign(trunk, trunk_mat)
    materials.assign(foliage, foliage_mat)

    # Parent foliage to trunk
    foliage.parent = trunk

    return trunk


# Modifiers

def add_modifier(
    obj: Union[bpy.types.Object, str],
    modifier_type: str,
    name: Optional[str] = None,
    **settings
) -> bpy.types.Modifier:
    """
    Add a modifier to an object.

    Args:
        obj: Object or object name
        modifier_type: 'SUBSURF', 'BEVEL', 'ARRAY', 'MIRROR', etc.
        name: Custom modifier name
        **settings: Modifier-specific settings

    Returns:
        The created modifier
    """
    if isinstance(obj, str):
        obj = bpy.data.objects.get(obj)

    modifier = obj.modifiers.new(name=name or modifier_type, type=modifier_type)

    for key, value in settings.items():
        if hasattr(modifier, key):
            setattr(modifier, key, value)

    return modifier


def add_subdivision(
    obj: Union[bpy.types.Object, str],
    levels: int = 2,
    render_levels: int = 2
) -> bpy.types.Modifier:
    """Add subdivision surface modifier."""
    return add_modifier(obj, 'SUBSURF', levels=levels, render_levels=render_levels)


def add_bevel(
    obj: Union[bpy.types.Object, str],
    width: float = 0.02,
    segments: int = 2
) -> bpy.types.Modifier:
    """Add bevel modifier."""
    return add_modifier(obj, 'BEVEL', width=width, segments=segments)


def add_array(
    obj: Union[bpy.types.Object, str],
    count: int = 3,
    offset: Vector3 = (1, 0, 0)
) -> bpy.types.Modifier:
    """Add array modifier."""
    mod = add_modifier(obj, 'ARRAY', count=count)
    mod.use_relative_offset = True
    mod.relative_offset_displace = offset
    return mod


def apply_all_modifiers(obj: Union[bpy.types.Object, str]) -> None:
    """Apply all modifiers to an object."""
    if isinstance(obj, str):
        obj = bpy.data.objects.get(obj)

    select(obj, exclusive=True)

    for modifier in obj.modifiers:
        bpy.ops.object.modifier_apply(modifier=modifier.name)
