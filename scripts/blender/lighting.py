"""
Lighting Setup Utilities

Create and configure lighting for Blender scenes.
"""

import bpy
import math
from typing import Optional, Tuple, Union


# Type aliases
Vector3 = Tuple[float, float, float]
Color3 = Tuple[float, float, float]


def create_light(
    light_type: str,
    name: str,
    location: Vector3 = (0, 0, 5),
    rotation: Optional[Vector3] = None,
    energy: float = 1000.0,
    color: Color3 = (1.0, 1.0, 1.0),
    size: float = 1.0
) -> bpy.types.Object:
    """
    Create a light of any type.

    Args:
        light_type: 'POINT', 'SUN', 'SPOT', 'AREA'
        name: Light object name
        location: Position (x, y, z)
        rotation: Rotation in degrees (x, y, z), None for default
        energy: Light intensity (watts for point/spot/area, sun uses different scale)
        color: RGB color (0-1 range)
        size: Light size (radius for point, angle for spot, size for area)

    Returns:
        The light object
    """
    bpy.ops.object.light_add(type=light_type, location=location)
    light_obj = bpy.context.active_object
    light_obj.name = name
    light = light_obj.data

    light.energy = energy
    light.color = color

    if rotation:
        light_obj.rotation_euler = tuple(math.radians(r) for r in rotation)

    # Type-specific settings
    if light_type == 'POINT':
        light.shadow_soft_size = size
    elif light_type == 'SUN':
        light.angle = math.radians(size)  # Angular diameter in degrees
    elif light_type == 'SPOT':
        light.spot_size = math.radians(size * 10)  # Cone angle
        light.shadow_soft_size = size * 0.1
    elif light_type == 'AREA':
        light.size = size

    return light_obj


def create_point_light(
    name: str = "PointLight",
    location: Vector3 = (0, 0, 5),
    energy: float = 1000.0,
    color: Color3 = (1.0, 1.0, 1.0),
    radius: float = 0.25
) -> bpy.types.Object:
    """Create a point light."""
    return create_light('POINT', name, location, energy=energy, color=color, size=radius)


def create_sun(
    name: str = "Sun",
    rotation: Vector3 = (45, 0, 45),
    energy: float = 5.0,
    color: Color3 = (1.0, 0.95, 0.9),
    angle: float = 0.526
) -> bpy.types.Object:
    """
    Create a sun light.

    Args:
        name: Light name
        rotation: Direction (rotation in degrees)
        energy: Sun intensity
        color: Sun color
        angle: Angular diameter in degrees
    """
    light_obj = create_light('SUN', name, location=(0, 0, 10), energy=energy, color=color)
    light_obj.rotation_euler = tuple(math.radians(r) for r in rotation)
    light_obj.data.angle = math.radians(angle)
    return light_obj


def create_spot_light(
    name: str = "SpotLight",
    location: Vector3 = (0, 0, 5),
    target: Optional[Vector3] = None,
    energy: float = 1000.0,
    color: Color3 = (1.0, 1.0, 1.0),
    spot_size: float = 45.0,
    spot_blend: float = 0.15
) -> bpy.types.Object:
    """
    Create a spot light.

    Args:
        name: Light name
        location: Position
        target: Point to aim at (None to use default rotation)
        energy: Light intensity
        color: Light color
        spot_size: Cone angle in degrees
        spot_blend: Edge softness (0-1)
    """
    light_obj = create_light('SPOT', name, location, energy=energy, color=color)
    light = light_obj.data

    light.spot_size = math.radians(spot_size)
    light.spot_blend = spot_blend

    if target:
        # Point at target using Track To constraint
        bpy.ops.object.constraint_add(type='TRACK_TO')
        constraint = light_obj.constraints["Track To"]

        # Create empty as target
        bpy.ops.object.empty_add(location=target)
        target_empty = bpy.context.active_object
        target_empty.name = f"{name}_Target"

        constraint.target = target_empty
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        # Re-select the light
        light_obj.select_set(True)
        bpy.context.view_layer.objects.active = light_obj

    return light_obj


def create_area_light(
    name: str = "AreaLight",
    location: Vector3 = (0, 0, 5),
    rotation: Vector3 = (0, 0, 0),
    energy: float = 1000.0,
    color: Color3 = (1.0, 1.0, 1.0),
    size: float = 2.0,
    shape: str = 'RECTANGLE',
    size_y: Optional[float] = None
) -> bpy.types.Object:
    """
    Create an area light.

    Args:
        name: Light name
        location: Position
        rotation: Rotation in degrees
        energy: Light intensity
        color: Light color
        size: Light width
        shape: 'SQUARE', 'RECTANGLE', 'DISK', 'ELLIPSE'
        size_y: Height for rectangle/ellipse (None = same as size)
    """
    light_obj = create_light('AREA', name, location, rotation, energy, color, size)
    light = light_obj.data

    light.shape = shape
    if shape in ('RECTANGLE', 'ELLIPSE') and size_y:
        light.size_y = size_y

    return light_obj


def three_point_setup(
    target: Vector3 = (0, 0, 1),
    key_energy: float = 5.0,
    fill_energy: float = 100.0,
    rim_energy: float = 200.0,
    distance: float = 5.0
) -> Tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    """
    Create a classic three-point lighting setup.

    Args:
        target: Point the lights aim toward
        key_energy: Key light intensity
        fill_energy: Fill light intensity
        rim_energy: Rim/back light intensity
        distance: Base distance from target

    Returns:
        Tuple of (key_light, fill_light, rim_light)
    """
    tx, ty, tz = target

    # Key light - main light, typically sun or strong area light
    key_light = create_sun(
        name="Key_Light",
        rotation=(45, 15, 45),
        energy=key_energy,
        color=(1.0, 0.98, 0.95)
    )

    # Fill light - softer, fills shadows
    fill_light = create_area_light(
        name="Fill_Light",
        location=(tx - distance * 0.8, ty - distance * 0.6, tz + distance * 0.5),
        rotation=(60, 0, -30),
        energy=fill_energy,
        color=(0.9, 0.95, 1.0),
        size=3.0
    )

    # Rim/back light - creates edge definition
    rim_light = create_spot_light(
        name="Rim_Light",
        location=(tx, ty + distance, tz + distance * 0.8),
        target=target,
        energy=rim_energy,
        color=(1.0, 0.98, 0.95),
        spot_size=60,
        spot_blend=0.3
    )

    return key_light, fill_light, rim_light


def studio_setup(
    width: float = 10.0,
    height: float = 5.0,
    key_energy: float = 2000.0,
    fill_energy: float = 500.0
) -> Tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    """
    Create a studio lighting setup with area lights.

    Args:
        width: Studio width
        height: Light height
        key_energy: Key light intensity
        fill_energy: Fill/side light intensity

    Returns:
        Tuple of (key_light, left_fill, right_fill)
    """
    # Key light (front, above)
    key_light = create_area_light(
        name="Studio_Key",
        location=(0, -width * 0.4, height),
        rotation=(60, 0, 0),
        energy=key_energy,
        size=width * 0.6,
        shape='RECTANGLE',
        size_y=width * 0.4
    )

    # Left fill
    left_fill = create_area_light(
        name="Studio_Left",
        location=(-width * 0.5, 0, height * 0.6),
        rotation=(45, 0, 90),
        energy=fill_energy,
        size=width * 0.3,
        shape='SQUARE'
    )

    # Right fill
    right_fill = create_area_light(
        name="Studio_Right",
        location=(width * 0.5, 0, height * 0.6),
        rotation=(45, 0, -90),
        energy=fill_energy,
        size=width * 0.3,
        shape='SQUARE'
    )

    return key_light, left_fill, right_fill


def outdoor_daylight(
    time_of_day: str = "midday",
    cloud_factor: float = 0.0
) -> Tuple[bpy.types.Object, bpy.types.World]:
    """
    Create outdoor daylight lighting.

    Args:
        time_of_day: 'dawn', 'morning', 'midday', 'afternoon', 'dusk', 'night'
        cloud_factor: 0.0 (clear) to 1.0 (overcast)

    Returns:
        Tuple of (sun_light, world)
    """
    from . import scene

    # Time-based settings
    settings = {
        'dawn': {'rotation': (10, 0, 90), 'energy': 2.0, 'color': (1.0, 0.6, 0.4),
                 'horizon': (0.9, 0.6, 0.4, 1), 'zenith': (0.3, 0.4, 0.7, 1)},
        'morning': {'rotation': (30, 0, 60), 'energy': 4.0, 'color': (1.0, 0.9, 0.8),
                    'horizon': (0.7, 0.8, 1.0, 1), 'zenith': (0.3, 0.5, 0.9, 1)},
        'midday': {'rotation': (70, 0, 30), 'energy': 5.0, 'color': (1.0, 0.98, 0.95),
                   'horizon': (0.6, 0.8, 1.0, 1), 'zenith': (0.2, 0.4, 0.9, 1)},
        'afternoon': {'rotation': (45, 0, -30), 'energy': 4.0, 'color': (1.0, 0.9, 0.8),
                      'horizon': (0.7, 0.75, 0.9, 1), 'zenith': (0.25, 0.45, 0.85, 1)},
        'dusk': {'rotation': (10, 0, -90), 'energy': 2.0, 'color': (1.0, 0.5, 0.3),
                 'horizon': (0.95, 0.5, 0.3, 1), 'zenith': (0.2, 0.2, 0.5, 1)},
        'night': {'rotation': (30, 0, 45), 'energy': 0.1, 'color': (0.7, 0.8, 1.0),
                  'horizon': (0.05, 0.05, 0.1, 1), 'zenith': (0.01, 0.01, 0.03, 1)},
    }

    s = settings.get(time_of_day, settings['midday'])

    # Reduce energy based on clouds
    adjusted_energy = s['energy'] * (1.0 - cloud_factor * 0.7)

    sun = create_sun(
        name="Sun",
        rotation=s['rotation'],
        energy=adjusted_energy,
        color=s['color']
    )

    # Set up sky
    world = scene.setup_sky_gradient(
        horizon_color=s['horizon'],
        zenith_color=s['zenith'],
        strength=1.0 - cloud_factor * 0.5
    )

    return sun, world


def delete_all_lights() -> int:
    """
    Delete all lights in the scene.

    Returns:
        Number of lights deleted
    """
    count = 0
    for obj in list(bpy.data.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)
            count += 1
    return count
