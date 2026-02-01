"""
Scene Setup and Management

Utilities for Blender scene initialization, cleanup, and configuration.
"""

import bpy
from typing import Optional, List


def clear(keep_camera: bool = False, keep_lights: bool = False) -> None:
    """
    Clear all objects from the scene.

    Args:
        keep_camera: If True, preserve existing cameras
        keep_lights: If True, preserve existing lights
    """
    # Deselect all first
    bpy.ops.object.select_all(action='DESELECT')

    for obj in bpy.data.objects:
        if keep_camera and obj.type == 'CAMERA':
            continue
        if keep_lights and obj.type == 'LIGHT':
            continue
        obj.select_set(True)

    bpy.ops.object.delete()

    # Clean up orphaned data blocks
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def new(name: str = "Scene") -> bpy.types.Scene:
    """
    Create a new scene.

    Args:
        name: Name for the new scene

    Returns:
        The newly created scene
    """
    new_scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = new_scene
    return new_scene


def set_units(
    system: str = 'METRIC',
    length_unit: str = 'METERS',
    scale_length: float = 1.0
) -> None:
    """
    Configure scene units.

    Args:
        system: 'METRIC', 'IMPERIAL', or 'NONE'
        length_unit: 'KILOMETERS', 'METERS', 'CENTIMETERS', etc.
        scale_length: Scale factor for the scene
    """
    scene = bpy.context.scene
    scene.unit_settings.system = system
    scene.unit_settings.length_unit = length_unit
    scene.unit_settings.scale_length = scale_length


def set_frame_range(start: int, end: int, fps: int = 24) -> None:
    """
    Set the animation frame range and framerate.

    Args:
        start: Starting frame number
        end: Ending frame number
        fps: Frames per second
    """
    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end
    scene.render.fps = fps


def set_current_frame(frame: int) -> None:
    """
    Jump to a specific frame.

    Args:
        frame: Frame number to set
    """
    bpy.context.scene.frame_set(frame)


def create_collection(name: str, parent: Optional[str] = None) -> bpy.types.Collection:
    """
    Create a new collection for organizing objects.

    Args:
        name: Name for the collection
        parent: Name of parent collection (None for scene collection)

    Returns:
        The newly created collection
    """
    collection = bpy.data.collections.new(name)

    if parent:
        parent_collection = bpy.data.collections.get(parent)
        if parent_collection:
            parent_collection.children.link(collection)
        else:
            bpy.context.scene.collection.children.link(collection)
    else:
        bpy.context.scene.collection.children.link(collection)

    return collection


def link_to_collection(obj: bpy.types.Object, collection_name: str) -> bool:
    """
    Link an object to a specific collection.

    Args:
        obj: The object to link
        collection_name: Name of the target collection

    Returns:
        True if successful, False if collection not found
    """
    collection = bpy.data.collections.get(collection_name)
    if collection:
        # Unlink from all current collections
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        # Link to target collection
        collection.objects.link(obj)
        return True
    return False


def setup_world_background(
    color: tuple = (0.05, 0.05, 0.05, 1.0),
    strength: float = 1.0
) -> bpy.types.World:
    """
    Set up a simple world background color.

    Args:
        color: RGBA color tuple (0-1 range)
        strength: Background strength/brightness

    Returns:
        The configured world
    """
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # Create nodes
    node_background = nodes.new(type='ShaderNodeBackground')
    node_output = nodes.new(type='ShaderNodeOutputWorld')

    node_background.inputs["Color"].default_value = color
    node_background.inputs["Strength"].default_value = strength

    links.new(node_background.outputs["Background"], node_output.inputs["Surface"])

    return world


def setup_sky_gradient(
    horizon_color: tuple = (0.5, 0.7, 1.0, 1.0),
    zenith_color: tuple = (0.1, 0.3, 0.8, 1.0),
    strength: float = 1.0
) -> bpy.types.World:
    """
    Set up a gradient sky background.

    Args:
        horizon_color: RGBA color at the horizon
        zenith_color: RGBA color at the zenith (top)
        strength: Background strength/brightness

    Returns:
        The configured world
    """
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    nodes.clear()

    # Create gradient sky nodes
    node_background = nodes.new(type='ShaderNodeBackground')
    node_output = nodes.new(type='ShaderNodeOutputWorld')
    node_gradient = nodes.new(type='ShaderNodeTexGradient')
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_coord = nodes.new(type='ShaderNodeTexCoord')
    node_colorramp = nodes.new(type='ShaderNodeValToRGB')

    # Configure color ramp
    node_colorramp.color_ramp.elements[0].color = horizon_color
    node_colorramp.color_ramp.elements[1].color = zenith_color

    node_background.inputs["Strength"].default_value = strength

    # Link nodes
    links.new(node_coord.outputs["Generated"], node_mapping.inputs["Vector"])
    links.new(node_mapping.outputs["Vector"], node_gradient.inputs["Vector"])
    links.new(node_gradient.outputs["Fac"], node_colorramp.inputs["Fac"])
    links.new(node_colorramp.outputs["Color"], node_background.inputs["Color"])
    links.new(node_background.outputs["Background"], node_output.inputs["Surface"])

    return world


def setup_hdri(filepath: str, strength: float = 1.0, rotation: float = 0.0) -> bpy.types.World:
    """
    Set up an HDRI environment map for lighting.

    Args:
        filepath: Path to the HDR/EXR file
        strength: Environment strength
        rotation: Z-axis rotation in degrees

    Returns:
        The configured world
    """
    import math

    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    nodes.clear()

    # Create nodes
    node_coord = nodes.new(type='ShaderNodeTexCoord')
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_env = nodes.new(type='ShaderNodeTexEnvironment')
    node_background = nodes.new(type='ShaderNodeBackground')
    node_output = nodes.new(type='ShaderNodeOutputWorld')

    # Load the image
    node_env.image = bpy.data.images.load(filepath)

    # Set rotation
    node_mapping.inputs["Rotation"].default_value[2] = math.radians(rotation)

    node_background.inputs["Strength"].default_value = strength

    # Link nodes
    links.new(node_coord.outputs["Generated"], node_mapping.inputs["Vector"])
    links.new(node_mapping.outputs["Vector"], node_env.inputs["Vector"])
    links.new(node_env.outputs["Color"], node_background.inputs["Color"])
    links.new(node_background.outputs["Background"], node_output.inputs["Surface"])

    return world


def get_scene_info() -> dict:
    """
    Get current scene information for logging/debugging.

    Returns:
        Dictionary containing scene metadata
    """
    scene = bpy.context.scene

    objects_by_type = {}
    for obj in scene.objects:
        obj_type = obj.type
        if obj_type not in objects_by_type:
            objects_by_type[obj_type] = []
        objects_by_type[obj_type].append(obj.name)

    return {
        "name": scene.name,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "frame_current": scene.frame_current,
        "fps": scene.render.fps,
        "resolution": (scene.render.resolution_x, scene.render.resolution_y),
        "render_engine": scene.render.engine,
        "object_count": len(scene.objects),
        "objects_by_type": objects_by_type,
        "collections": [c.name for c in bpy.data.collections],
    }
