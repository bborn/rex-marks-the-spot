"""
Headless Render Engine Controller

Manages Blender execution in headless (background) mode for automated rendering.
This module runs OUTSIDE of Blender and calls Blender as a subprocess.
"""

import os
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


# Default Blender executable path
BLENDER_EXECUTABLE = os.environ.get("BLENDER_PATH", "blender")


@dataclass
class RenderResult:
    """Result of a render operation."""
    success: bool
    output_path: Optional[str] = None
    render_time: float = 0.0
    stdout: str = ""
    stderr: str = ""
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'success': self.success,
            'output_path': self.output_path,
            'render_time': self.render_time,
            'error_message': self.error_message,
            'metadata': self.metadata,
        }


@dataclass
class RenderConfig:
    """Configuration for a render job."""
    output_path: str
    resolution: tuple = (1920, 1080)
    samples: int = 128
    engine: str = 'CYCLES'
    format: str = 'PNG'
    use_gpu: bool = True
    frame: Optional[int] = None
    animation: bool = False
    frame_start: Optional[int] = None
    frame_end: Optional[int] = None
    blend_file: Optional[str] = None
    timeout: int = 600  # 10 minutes default

    def to_args(self) -> List[str]:
        """Convert config to Blender command line arguments."""
        args = []

        if self.engine:
            args.extend(['-E', self.engine])

        if self.frame is not None:
            args.extend(['-f', str(self.frame)])
        elif self.animation:
            if self.frame_start is not None:
                args.extend(['-s', str(self.frame_start)])
            if self.frame_end is not None:
                args.extend(['-e', str(self.frame_end)])
            args.append('-a')

        args.extend(['-o', self.output_path])

        return args


def check_blender() -> tuple:
    """
    Check if Blender is available and get version.

    Returns:
        Tuple of (available: bool, version: str or error message)
    """
    try:
        result = subprocess.run(
            [BLENDER_EXECUTABLE, '--version'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            return True, version
        else:
            return False, result.stderr
    except FileNotFoundError:
        return False, f"Blender not found at '{BLENDER_EXECUTABLE}'"
    except subprocess.TimeoutExpired:
        return False, "Blender check timed out"


def render_blend_file(
    blend_file: str,
    output_path: str,
    config: Optional[RenderConfig] = None,
    verbose: bool = True
) -> RenderResult:
    """
    Render a .blend file directly.

    Args:
        blend_file: Path to the .blend file
        output_path: Output path for the render
        config: Optional render configuration
        verbose: Print progress

    Returns:
        RenderResult with outcome
    """
    if config is None:
        config = RenderConfig(output_path=output_path)
    else:
        config.output_path = output_path

    config.blend_file = blend_file

    cmd = [BLENDER_EXECUTABLE, '-b', blend_file]
    cmd.extend(config.to_args())

    if verbose:
        print(f"Rendering: {blend_file}")
        print(f"Command: {' '.join(cmd)}")

    start_time = datetime.now()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.timeout
        )

        render_time = (datetime.now() - start_time).total_seconds()

        if result.returncode == 0:
            return RenderResult(
                success=True,
                output_path=output_path,
                render_time=render_time,
                stdout=result.stdout,
                stderr=result.stderr,
                metadata={'blend_file': blend_file}
            )
        else:
            return RenderResult(
                success=False,
                render_time=render_time,
                stdout=result.stdout,
                stderr=result.stderr,
                error_message=f"Blender exited with code {result.returncode}"
            )

    except subprocess.TimeoutExpired:
        return RenderResult(
            success=False,
            error_message=f"Render timed out after {config.timeout} seconds"
        )
    except Exception as e:
        return RenderResult(
            success=False,
            error_message=str(e)
        )


def render_script(
    script_path: str,
    output_path: str,
    script_args: Optional[Dict[str, Any]] = None,
    config: Optional[RenderConfig] = None,
    verbose: bool = True
) -> RenderResult:
    """
    Execute a Python script in Blender and render.

    Args:
        script_path: Path to the Python script
        output_path: Output path for the render
        script_args: Arguments to pass to the script
        config: Optional render configuration
        verbose: Print progress

    Returns:
        RenderResult with outcome
    """
    if config is None:
        config = RenderConfig(output_path=output_path)
    else:
        config.output_path = output_path

    cmd = [BLENDER_EXECUTABLE, '-b', '-P', script_path]

    # Add script arguments after '--'
    if script_args:
        cmd.append('--')
        cmd.extend(['--output', output_path])
        cmd.extend(['--samples', str(config.samples)])

        for key, value in script_args.items():
            if key not in ('output', 'samples'):
                cmd.extend([f'--{key}', str(value)])

    if verbose:
        print(f"Executing script: {script_path}")
        print(f"Command: {' '.join(cmd)}")

    start_time = datetime.now()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.timeout
        )

        render_time = (datetime.now() - start_time).total_seconds()

        # Check if output file was created
        output_exists = Path(output_path).exists()

        if result.returncode == 0 and output_exists:
            return RenderResult(
                success=True,
                output_path=output_path,
                render_time=render_time,
                stdout=result.stdout,
                stderr=result.stderr,
                metadata={'script': script_path}
            )
        elif result.returncode == 0 and not output_exists:
            return RenderResult(
                success=False,
                render_time=render_time,
                stdout=result.stdout,
                stderr=result.stderr,
                error_message="Script completed but output file not found"
            )
        else:
            return RenderResult(
                success=False,
                render_time=render_time,
                stdout=result.stdout,
                stderr=result.stderr,
                error_message=f"Script failed with code {result.returncode}"
            )

    except subprocess.TimeoutExpired:
        return RenderResult(
            success=False,
            error_message=f"Script timed out after {config.timeout} seconds"
        )
    except Exception as e:
        return RenderResult(
            success=False,
            error_message=str(e)
        )


def render_python_code(
    code: str,
    output_path: str,
    config: Optional[RenderConfig] = None,
    verbose: bool = True
) -> RenderResult:
    """
    Execute Python code directly in Blender.

    Args:
        code: Python code to execute
        output_path: Output path for the render
        config: Optional render configuration
        verbose: Print progress

    Returns:
        RenderResult with outcome
    """
    # Write code to temporary file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False
    ) as f:
        f.write(code)
        temp_script = f.name

    try:
        result = render_script(
            script_path=temp_script,
            output_path=output_path,
            config=config,
            verbose=verbose
        )
        result.metadata['source'] = 'inline_code'
        return result
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_script)
        except:
            pass


def generate_render_script(
    scene_description: dict,
    output_path: str
) -> str:
    """
    Generate a Blender Python script from a scene description.

    Args:
        scene_description: Dictionary describing the scene
        output_path: Where to save the generated script

    Returns:
        Path to the generated script
    """
    lines = [
        '#!/usr/bin/env python3',
        '"""Auto-generated Blender scene script."""',
        '',
        'import sys',
        'import os',
        '',
        '# Add scripts directory to path',
        'script_dir = os.path.dirname(os.path.abspath(__file__))',
        'parent_dir = os.path.dirname(script_dir)',
        'sys.path.insert(0, parent_dir)',
        '',
        'from blender import scene, objects, materials, lighting, camera, render',
        '',
        '',
        'def setup_scene():',
        '    """Set up the scene based on description."""',
        '    # Clear existing scene',
        '    scene.clear()',
        '',
    ]

    # Generate code based on scene description
    if 'ground' in scene_description:
        g = scene_description['ground']
        lines.append(f"    objects.create_ground(size={g.get('size', 20)})")
        lines.append('')

    if 'objects' in scene_description:
        for obj in scene_description['objects']:
            obj_type = obj.get('type', 'cube')
            name = obj.get('name', 'Object')
            location = obj.get('location', (0, 0, 0))

            if obj_type == 'cube':
                lines.append(f"    objects.create_cube('{name}', location={location})")
            elif obj_type == 'sphere':
                lines.append(f"    objects.create_sphere('{name}', location={location})")
            elif obj_type == 'character':
                lines.append(f"    objects.create_character_placeholder('{name}', location={location})")
            elif obj_type == 'tree':
                lines.append(f"    objects.create_simple_tree('{name}', location={location})")

        lines.append('')

    if 'lighting' in scene_description:
        light_type = scene_description['lighting'].get('type', 'three_point')
        if light_type == 'three_point':
            lines.append('    lighting.three_point_setup()')
        elif light_type == 'outdoor':
            time = scene_description['lighting'].get('time', 'midday')
            lines.append(f"    lighting.outdoor_daylight(time_of_day='{time}')")
        lines.append('')

    if 'sky' in scene_description:
        sky = scene_description['sky']
        if 'gradient' in sky:
            lines.append(f"    scene.setup_sky_gradient()")
        lines.append('')

    # Camera setup
    cam_loc = scene_description.get('camera', {}).get('location', (7, -7, 5))
    cam_target = scene_description.get('camera', {}).get('target', (0, 0, 1))
    lines.append(f"    camera.setup_main(location={cam_loc}, target={cam_target})")
    lines.append('')

    # Render configuration
    res = scene_description.get('resolution', (1920, 1080))
    samples = scene_description.get('samples', 64)
    lines.extend([
        '',
        'def main():',
        '    """Main entry point."""',
        '    import sys',
        '    ',
        '    # Parse arguments',
        '    output = "render.png"',
        f'    samples = {samples}',
        '    ',
        '    if "--" in sys.argv:',
        '        args = sys.argv[sys.argv.index("--") + 1:]',
        '        for i, arg in enumerate(args):',
        '            if arg == "--output" and i + 1 < len(args):',
        '                output = args[i + 1]',
        '            elif arg == "--samples" and i + 1 < len(args):',
        '                samples = int(args[i + 1])',
        '    ',
        '    setup_scene()',
        '    ',
        f'    render.configure(',
        f'        output_path=output,',
        f'        resolution={res},',
        '        samples=samples',
        '    )',
        '    render.execute()',
        '    ',
        '    print(f"Render complete: {{output}}")',
        '',
        '',
        'if __name__ == "__main__":',
        '    main()',
    ])

    # Write script
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    return output_path


class RenderEngine:
    """
    High-level render engine interface.

    Manages render jobs and provides a consistent API for rendering.
    """

    def __init__(self, blender_path: Optional[str] = None):
        """
        Initialize the render engine.

        Args:
            blender_path: Path to Blender executable (None = use default)
        """
        global BLENDER_EXECUTABLE
        if blender_path:
            BLENDER_EXECUTABLE = blender_path

        self.blender_path = BLENDER_EXECUTABLE
        self.available, self.version = check_blender()

    def is_available(self) -> bool:
        """Check if Blender is available."""
        return self.available

    def render(
        self,
        script_or_blend: str,
        output_path: str,
        **kwargs
    ) -> RenderResult:
        """
        Render a script or blend file.

        Args:
            script_or_blend: Path to .py script or .blend file
            output_path: Output render path
            **kwargs: Additional configuration options

        Returns:
            RenderResult
        """
        if not self.available:
            return RenderResult(
                success=False,
                error_message=f"Blender not available: {self.version}"
            )

        config = RenderConfig(
            output_path=output_path,
            resolution=kwargs.get('resolution', (1920, 1080)),
            samples=kwargs.get('samples', 128),
            engine=kwargs.get('engine', 'CYCLES'),
            timeout=kwargs.get('timeout', 600)
        )

        if script_or_blend.endswith('.blend'):
            return render_blend_file(script_or_blend, output_path, config)
        else:
            return render_script(
                script_or_blend,
                output_path,
                script_args=kwargs.get('script_args'),
                config=config
            )

    def render_code(self, code: str, output_path: str, **kwargs) -> RenderResult:
        """
        Render inline Python code.

        Args:
            code: Python code to execute
            output_path: Output render path
            **kwargs: Additional configuration options

        Returns:
            RenderResult
        """
        config = RenderConfig(
            output_path=output_path,
            samples=kwargs.get('samples', 128),
            timeout=kwargs.get('timeout', 600)
        )
        return render_python_code(code, output_path, config)
