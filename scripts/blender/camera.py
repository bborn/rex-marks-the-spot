"""
Camera Utilities

Create, position, and configure cameras for rendering.
"""

import bpy
import math
from typing import Optional, Tuple, Union


# Type aliases
Vector3 = Tuple[float, float, float]


def create(
    name: str = "Camera",
    location: Vector3 = (7, -7, 5),
    rotation: Optional[Vector3] = None,
    focal_length: float = 50.0,
    sensor_width: float = 36.0
) -> bpy.types.Object:
    """
    Create a new camera.

    Args:
        name: Camera name
        location: Position (x, y, z)
        rotation: Rotation in degrees (x, y, z), None for default
        focal_length: Focal length in mm
        sensor_width: Sensor width in mm

    Returns:
        The camera object
    """
    bpy.ops.object.camera_add(location=location)
    camera_obj = bpy.context.active_object
    camera_obj.name = name

    camera = camera_obj.data
    camera.lens = focal_length
    camera.sensor_width = sensor_width

    if rotation:
        camera_obj.rotation_euler = tuple(math.radians(r) for r in rotation)

    return camera_obj


def setup_main(
    location: Vector3 = (7, -7, 5),
    target: Optional[Union[Vector3, bpy.types.Object, str]] = None,
    focal_length: float = 50.0,
    name: str = "MainCamera"
) -> bpy.types.Object:
    """
    Set up the main render camera.

    Args:
        location: Camera position
        target: Look-at target (position, object, or object name)
        focal_length: Focal length in mm
        name: Camera name

    Returns:
        The camera object
    """
    camera_obj = create(name=name, location=location, focal_length=focal_length)

    if target is not None:
        look_at(camera_obj, target)

    # Set as active camera
    bpy.context.scene.camera = camera_obj

    return camera_obj


def look_at(
    camera: Union[bpy.types.Object, str],
    target: Union[Vector3, bpy.types.Object, str]
) -> None:
    """
    Point a camera at a target.

    Args:
        camera: Camera object or name
        target: Look-at target (position, object, or object name)
    """
    if isinstance(camera, str):
        camera = bpy.data.objects.get(camera)

    # Handle target types
    target_obj = None
    if isinstance(target, str):
        target_obj = bpy.data.objects.get(target)
    elif isinstance(target, bpy.types.Object):
        target_obj = target
    elif isinstance(target, (tuple, list)):
        # Create a temporary empty for the position
        bpy.ops.object.empty_add(location=target)
        target_obj = bpy.context.active_object
        target_obj.name = f"{camera.name}_Target"

    if target_obj is None:
        return

    # Remove existing Track To constraints
    for constraint in list(camera.constraints):
        if constraint.type == 'TRACK_TO':
            camera.constraints.remove(constraint)

    # Add Track To constraint
    constraint = camera.constraints.new(type='TRACK_TO')
    constraint.target = target_obj
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'


def set_active(camera: Union[bpy.types.Object, str]) -> bpy.types.Object:
    """
    Set a camera as the active render camera.

    Args:
        camera: Camera object or name

    Returns:
        The active camera object
    """
    if isinstance(camera, str):
        camera = bpy.data.objects.get(camera)

    bpy.context.scene.camera = camera
    return camera


def get_active() -> Optional[bpy.types.Object]:
    """
    Get the currently active camera.

    Returns:
        The active camera or None
    """
    return bpy.context.scene.camera


def set_dof(
    camera: Union[bpy.types.Object, str],
    focus_distance: Optional[float] = None,
    focus_object: Optional[Union[bpy.types.Object, str]] = None,
    fstop: float = 2.8,
    enabled: bool = True
) -> None:
    """
    Configure depth of field settings.

    Args:
        camera: Camera object or name
        focus_distance: Focus distance in meters (ignored if focus_object set)
        focus_object: Object to focus on
        fstop: Aperture f-stop value
        enabled: Enable/disable DOF
    """
    if isinstance(camera, str):
        camera = bpy.data.objects.get(camera)

    cam_data = camera.data
    cam_data.dof.use_dof = enabled
    cam_data.dof.aperture_fstop = fstop

    if focus_object:
        if isinstance(focus_object, str):
            focus_object = bpy.data.objects.get(focus_object)
        cam_data.dof.focus_object = focus_object
    elif focus_distance:
        cam_data.dof.focus_distance = focus_distance


def set_clipping(
    camera: Union[bpy.types.Object, str],
    near: float = 0.1,
    far: float = 1000.0
) -> None:
    """
    Set camera clipping planes.

    Args:
        camera: Camera object or name
        near: Near clipping distance
        far: Far clipping distance
    """
    if isinstance(camera, str):
        camera = bpy.data.objects.get(camera)

    camera.data.clip_start = near
    camera.data.clip_end = far


def add_keyframe(
    camera: Union[bpy.types.Object, str],
    frame: int,
    location: Optional[Vector3] = None,
    rotation: Optional[Vector3] = None,
    focal_length: Optional[float] = None
) -> None:
    """
    Add animation keyframe for camera.

    Args:
        camera: Camera object or name
        frame: Frame number
        location: Position keyframe
        rotation: Rotation keyframe (degrees)
        focal_length: Focal length keyframe
    """
    if isinstance(camera, str):
        camera = bpy.data.objects.get(camera)

    bpy.context.scene.frame_set(frame)

    if location:
        camera.location = location
        camera.keyframe_insert(data_path="location", frame=frame)

    if rotation:
        camera.rotation_euler = tuple(math.radians(r) for r in rotation)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)

    if focal_length:
        camera.data.lens = focal_length
        camera.data.keyframe_insert(data_path="lens", frame=frame)


def create_orbit_animation(
    camera: Union[bpy.types.Object, str],
    center: Vector3 = (0, 0, 1),
    radius: float = 7.0,
    height: float = 3.0,
    start_frame: int = 1,
    end_frame: int = 120,
    start_angle: float = 0.0,
    end_angle: float = 360.0
) -> None:
    """
    Create an orbital camera animation around a point.

    Args:
        camera: Camera object or name
        center: Center point of orbit
        radius: Orbit radius
        height: Camera height above center
        start_frame: Animation start frame
        end_frame: Animation end frame
        start_angle: Starting angle in degrees
        end_angle: Ending angle in degrees
    """
    if isinstance(camera, str):
        camera = bpy.data.objects.get(camera)

    cx, cy, cz = center

    for frame in range(start_frame, end_frame + 1):
        progress = (frame - start_frame) / (end_frame - start_frame)
        angle = math.radians(start_angle + (end_angle - start_angle) * progress)

        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        z = cz + height

        add_keyframe(camera, frame, location=(x, y, z))

    # Make sure camera always looks at center
    look_at(camera, center)


def frame_object(
    camera: Union[bpy.types.Object, str],
    target: Union[bpy.types.Object, str],
    margin: float = 1.2
) -> None:
    """
    Position camera to frame an object nicely.

    Args:
        camera: Camera object or name
        target: Object to frame
        margin: Extra margin factor (1.0 = tight, 1.5 = loose)
    """
    if isinstance(camera, str):
        camera = bpy.data.objects.get(camera)
    if isinstance(target, str):
        target = bpy.data.objects.get(target)

    # Get object bounds
    bbox = [target.matrix_world @ bpy.mathutils.Vector(corner)
            for corner in target.bound_box]

    # Calculate center and size
    center = sum((bpy.mathutils.Vector(v) for v in bbox), bpy.mathutils.Vector()) / 8
    size = max(
        max(v[i] for v in bbox) - min(v[i] for v in bbox)
        for i in range(3)
    )

    # Calculate distance based on field of view
    fov = 2 * math.atan(camera.data.sensor_width / (2 * camera.data.lens))
    distance = (size * margin) / (2 * math.tan(fov / 2))

    # Position camera
    direction = camera.location - bpy.mathutils.Vector(center)
    if direction.length > 0:
        direction.normalize()
    else:
        direction = bpy.mathutils.Vector((1, -1, 0.5)).normalized()

    camera.location = bpy.mathutils.Vector(center) + direction * distance
    look_at(camera, (center.x, center.y, center.z))


def list_cameras() -> list:
    """
    List all cameras in the scene.

    Returns:
        List of camera names
    """
    return [obj.name for obj in bpy.data.objects if obj.type == 'CAMERA']
