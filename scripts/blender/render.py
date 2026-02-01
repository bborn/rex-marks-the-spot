"""
Render Configuration and Execution

Configure render settings and execute renders.
"""

import bpy
import os
from typing import Optional, Tuple


def configure(
    output_path: str = "//render.png",
    resolution: Tuple[int, int] = (1920, 1080),
    samples: int = 128,
    engine: str = 'CYCLES',
    format: str = 'PNG',
    color_depth: str = '8',
    use_gpu: bool = True,
    use_denoising: bool = True,
    denoiser: str = 'OPENIMAGEDENOISE'
) -> dict:
    """
    Configure render settings.

    Args:
        output_path: Output file path (// prefix = relative to blend file)
        resolution: (width, height) in pixels
        samples: Render samples (for Cycles)
        engine: 'CYCLES', 'BLENDER_EEVEE', or 'BLENDER_WORKBENCH'
        format: 'PNG', 'JPEG', 'OPEN_EXR', 'TIFF', etc.
        color_depth: '8', '16', or '32' bits
        use_gpu: Try to use GPU rendering
        use_denoising: Enable denoising
        denoiser: 'OPENIMAGEDENOISE' or 'OPTIX'

    Returns:
        Dictionary of applied settings
    """
    scene = bpy.context.scene
    render = scene.render

    # Basic settings
    render.filepath = output_path
    render.resolution_x = resolution[0]
    render.resolution_y = resolution[1]
    render.resolution_percentage = 100

    # File format
    render.image_settings.file_format = format
    if format in ('PNG', 'TIFF', 'OPEN_EXR'):
        render.image_settings.color_depth = color_depth

    # Engine selection
    render.engine = engine

    applied = {
        'output_path': output_path,
        'resolution': resolution,
        'engine': engine,
        'format': format,
    }

    if engine == 'CYCLES':
        scene.cycles.samples = samples
        applied['samples'] = samples

        # Denoising
        scene.cycles.use_denoising = use_denoising
        if use_denoising:
            try:
                scene.cycles.denoiser = denoiser
                applied['denoiser'] = denoiser
            except:
                pass

        # GPU setup
        if use_gpu:
            device = _setup_gpu()
            applied['device'] = device
        else:
            scene.cycles.device = 'CPU'
            applied['device'] = 'CPU'

    elif engine == 'BLENDER_EEVEE':
        scene.eevee.taa_render_samples = samples
        applied['samples'] = samples

    return applied


def _setup_gpu() -> str:
    """
    Configure GPU rendering.

    Returns:
        Device type used ('CUDA', 'OPTIX', 'HIP', 'METAL', 'CPU')
    """
    scene = bpy.context.scene

    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences

        # Try device types in order of preference
        for device_type in ['OPTIX', 'CUDA', 'HIP', 'METAL', 'NONE']:
            try:
                prefs.compute_device_type = device_type
                prefs.get_devices()

                if prefs.devices:
                    # Enable all available devices
                    for device in prefs.devices:
                        device.use = True

                    if device_type != 'NONE':
                        scene.cycles.device = 'GPU'
                        print(f"GPU rendering enabled: {device_type}")
                        return device_type

            except Exception:
                continue

        # Fallback to CPU
        scene.cycles.device = 'CPU'
        return 'CPU'

    except Exception as e:
        print(f"GPU setup failed: {e}")
        scene.cycles.device = 'CPU'
        return 'CPU'


def configure_for_preview(
    output_path: str = "//preview.png",
    resolution: Tuple[int, int] = (960, 540),
    samples: int = 16
) -> dict:
    """
    Configure quick preview render settings.

    Args:
        output_path: Output file path
        resolution: Lower resolution for speed
        samples: Fewer samples for speed

    Returns:
        Applied settings dictionary
    """
    return configure(
        output_path=output_path,
        resolution=resolution,
        samples=samples,
        engine='CYCLES',
        use_denoising=False
    )


def configure_for_production(
    output_path: str = "//render.png",
    resolution: Tuple[int, int] = (1920, 1080),
    samples: int = 256
) -> dict:
    """
    Configure high-quality production render settings.

    Args:
        output_path: Output file path
        resolution: Full resolution
        samples: High sample count

    Returns:
        Applied settings dictionary
    """
    return configure(
        output_path=output_path,
        resolution=resolution,
        samples=samples,
        engine='CYCLES',
        format='PNG',
        color_depth='16',
        use_denoising=True,
        denoiser='OPENIMAGEDENOISE'
    )


def configure_animation(
    output_path: str = "//frames/frame_",
    resolution: Tuple[int, int] = (1920, 1080),
    samples: int = 128,
    start_frame: Optional[int] = None,
    end_frame: Optional[int] = None,
    fps: int = 24
) -> dict:
    """
    Configure settings for animation rendering.

    Args:
        output_path: Output path with frame placeholder
        resolution: Frame resolution
        samples: Samples per frame
        start_frame: Animation start (None = use scene setting)
        end_frame: Animation end (None = use scene setting)
        fps: Frames per second

    Returns:
        Applied settings dictionary
    """
    scene = bpy.context.scene

    if start_frame is not None:
        scene.frame_start = start_frame
    if end_frame is not None:
        scene.frame_end = end_frame

    scene.render.fps = fps

    settings = configure(
        output_path=output_path,
        resolution=resolution,
        samples=samples,
        format='PNG'
    )

    settings.update({
        'frame_start': scene.frame_start,
        'frame_end': scene.frame_end,
        'fps': fps,
        'total_frames': scene.frame_end - scene.frame_start + 1
    })

    return settings


def execute(
    animation: bool = False,
    write_still: bool = True
) -> str:
    """
    Execute the render.

    Args:
        animation: If True, render animation; if False, render single frame
        write_still: Write result to file

    Returns:
        Output file path
    """
    if animation:
        bpy.ops.render.render(animation=True)
    else:
        bpy.ops.render.render(write_still=write_still)

    return bpy.context.scene.render.filepath


def render_frame(
    frame: int,
    output_path: Optional[str] = None
) -> str:
    """
    Render a specific frame.

    Args:
        frame: Frame number to render
        output_path: Optional override for output path

    Returns:
        Output file path
    """
    scene = bpy.context.scene

    # Set frame
    scene.frame_set(frame)

    # Override path if provided
    if output_path:
        original_path = scene.render.filepath
        scene.render.filepath = output_path
        execute(animation=False, write_still=True)
        scene.render.filepath = original_path
        return output_path
    else:
        return execute(animation=False, write_still=True)


def render_viewport(
    output_path: str,
    resolution: Tuple[int, int] = (1920, 1080)
) -> str:
    """
    Render the viewport (OpenGL render).

    Args:
        output_path: Output file path
        resolution: Image resolution

    Returns:
        Output file path
    """
    scene = bpy.context.scene
    render = scene.render

    render.filepath = output_path
    render.resolution_x = resolution[0]
    render.resolution_y = resolution[1]

    bpy.ops.render.opengl(write_still=True)

    return output_path


def get_render_info() -> dict:
    """
    Get current render settings info.

    Returns:
        Dictionary of current render settings
    """
    scene = bpy.context.scene
    render = scene.render

    info = {
        'filepath': render.filepath,
        'resolution': (render.resolution_x, render.resolution_y),
        'resolution_percentage': render.resolution_percentage,
        'engine': render.engine,
        'format': render.image_settings.file_format,
        'camera': scene.camera.name if scene.camera else None,
        'frame_current': scene.frame_current,
        'frame_start': scene.frame_start,
        'frame_end': scene.frame_end,
        'fps': render.fps,
    }

    if render.engine == 'CYCLES':
        info['samples'] = scene.cycles.samples
        info['device'] = scene.cycles.device
        info['denoising'] = scene.cycles.use_denoising

    elif render.engine == 'BLENDER_EEVEE':
        info['samples'] = scene.eevee.taa_render_samples

    return info


def set_output_format(
    format: str = 'PNG',
    color_mode: str = 'RGBA',
    color_depth: str = '8',
    compression: int = 15,
    quality: int = 90
) -> None:
    """
    Configure output file format.

    Args:
        format: 'PNG', 'JPEG', 'OPEN_EXR', 'TIFF', etc.
        color_mode: 'BW', 'RGB', 'RGBA'
        color_depth: '8', '16', '32' (format dependent)
        compression: PNG compression (0-100)
        quality: JPEG quality (0-100)
    """
    render = bpy.context.scene.render
    img_settings = render.image_settings

    img_settings.file_format = format
    img_settings.color_mode = color_mode

    if format in ('PNG', 'TIFF', 'OPEN_EXR'):
        img_settings.color_depth = color_depth

    if format == 'PNG':
        img_settings.compression = compression

    if format == 'JPEG':
        img_settings.quality = quality


def set_film_settings(
    transparent: bool = False,
    exposure: float = 0.0,
    gamma: float = 1.0
) -> None:
    """
    Configure film/output settings.

    Args:
        transparent: Render with transparent background
        exposure: Exposure adjustment
        gamma: Gamma correction
    """
    scene = bpy.context.scene

    scene.render.film_transparent = transparent

    if scene.render.engine == 'CYCLES':
        scene.cycles.film_exposure = exposure

    scene.view_settings.gamma = gamma
