#!/usr/bin/env python3
"""
Create Act 2 Animatic for Fairy Dinosaur Date Night

Combines storyboard panels with timing from animatic-notes.md
and adds background music to create an MP4 animatic.

Usage:
    python scripts/create_act2_animatic.py
    python scripts/create_act2_animatic.py --output renders/act2_animatic.mp4
    python scripts/create_act2_animatic.py --no-music
"""

import os
import sys
import argparse
import subprocess
import tempfile
from pathlib import Path


# Panel timings from Act 2 animatic-notes.md (duration in seconds)
# Format: scene_number -> [panel_durations]
PANEL_TIMINGS = {
    11: [6, 5, 4],  # 15s total
    12: [20, 25, 15, 15],  # 75s total
    13: [20, 10, 25, 15, 15, 35, 30],  # 150s total
    14: [10, 10, 5, 20, 15],  # 60s total
    15: [6, 5, 4],  # 15s total
    16: [12, 10, 8],  # 30s total
    17: [8, 4, 4, 4],  # 20s total
    18: [15, 8, 7],  # 30s total
    19: [12, 12, 10, 8, 10, 8],  # 60s total
    20: [20, 15, 20, 10, 60, 15, 10, 30, 20, 25, 15],  # 240s (added panel 11)
    21: [15, 8, 20, 40, 25, 12, 20, 10],  # 150s total
    22: [20, 15, 15, 10, 10, 15, 20, 10, 15, 25, 15, 10, 20, 40],  # 240s (14 panels)
    23: [10, 8, 12, 20, 10, 30, 10, 20],  # 120s total
    24: [15, 15, 15],  # 45s total
    25: [15, 15, 30, 10, 15, 15, 20],  # 120s total
}


def get_project_root():
    """Get the project root directory."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def find_panels(panels_dir: Path) -> list:
    """Find all Act 2 storyboard panels and return them in scene/panel order."""
    panels = []

    for scene in range(11, 26):  # Scenes 11-25
        scene_panels = sorted(
            panels_dir.glob(f"scene-{scene:02d}-panel-*.png"),
            key=lambda p: int(p.stem.split("-")[-1])
        )
        for panel in scene_panels:
            panels.append((scene, panel))

    return panels


def get_panel_duration(scene: int, panel_index: int, timings: dict) -> float:
    """Get duration for a specific panel based on scene and panel index."""
    if scene not in timings:
        return 5.0  # Default duration

    scene_timings = timings[scene]
    if panel_index < len(scene_timings):
        return scene_timings[panel_index]
    else:
        # Extra panels get average duration of the scene
        return sum(scene_timings) / len(scene_timings)


def create_concat_file(panels: list, timings: dict, output_path: Path) -> Path:
    """Create ffmpeg concat file with durations."""
    concat_file = output_path / "concat_list.txt"

    current_scene = None
    panel_in_scene = 0

    with open(concat_file, "w") as f:
        for scene, panel_path in panels:
            if scene != current_scene:
                current_scene = scene
                panel_in_scene = 0

            duration = get_panel_duration(scene, panel_in_scene, timings)
            # Use absolute path for ffmpeg
            f.write(f"file '{panel_path.resolve()}'\n")
            f.write(f"duration {duration}\n")

            panel_in_scene += 1

        # Add last frame again to ensure final frame displays correctly
        if panels:
            f.write(f"file '{panels[-1][1].resolve()}'\n")

    return concat_file


def get_total_duration(panels: list, timings: dict) -> float:
    """Calculate total video duration."""
    total = 0.0
    current_scene = None
    panel_in_scene = 0

    for scene, _ in panels:
        if scene != current_scene:
            current_scene = scene
            panel_in_scene = 0

        total += get_panel_duration(scene, panel_in_scene, timings)
        panel_in_scene += 1

    return total


def create_animatic(
    panels_dir: Path,
    output_file: Path,
    music_file: Path = None,
    resolution: tuple = (1920, 1080),
    fps: int = 24,
) -> bool:
    """Create the animatic video."""

    # Find panels
    panels = find_panels(panels_dir)
    if not panels:
        print(f"Error: No panels found in {panels_dir}")
        return False

    print(f"Found {len(panels)} panels")

    # Calculate total duration
    total_duration = get_total_duration(panels, PANEL_TIMINGS)
    print(f"Total duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")

    # Create temp directory for intermediate files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create concat file
        concat_file = create_concat_file(panels, PANEL_TIMINGS, tmpdir)
        print(f"Created concat file: {concat_file}")

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Build ffmpeg command
        # Use concat demuxer with scale filter to ensure consistent resolution
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
        ]

        # Add music if provided
        if music_file and music_file.exists():
            cmd.extend(["-i", str(music_file)])
            # Loop music if needed to cover the video duration
            cmd.extend(["-stream_loop", "-1"])
            # Re-add after the second input
            cmd_with_audio = cmd[:5] + [
                "-stream_loop", "-1",
                "-i", str(music_file),
            ] + cmd[5:]
            cmd = cmd_with_audio[:5] + cmd[5:]  # Fix command order

        # Rebuild command properly for music
        if music_file and music_file.exists():
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-stream_loop", "-1",
                "-i", str(music_file),
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
            ]

        # Video filters: scale to target resolution, maintain aspect ratio with padding
        vf = f"scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2:color=black"

        cmd.extend([
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
        ])

        # Audio settings
        if music_file and music_file.exists():
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(total_duration),  # Limit to video duration
            ])

        cmd.extend([
            "-movflags", "+faststart",
            str(output_file),
        ])

        print("Running ffmpeg...")
        print(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            print("ffmpeg completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg error: {e.stderr}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Create Act 2 animatic from storyboard panels"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="renders/act2_animatic.mp4",
        help="Output video file path (default: renders/act2_animatic.mp4)",
    )
    parser.add_argument(
        "--music", "-m",
        type=str,
        default=None,
        help="Background music file (default: adventure_music.wav)",
    )
    parser.add_argument(
        "--no-music",
        action="store_true",
        help="Create animatic without music",
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default="1920x1080",
        help="Output resolution WxH (default: 1920x1080)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Frames per second (default: 24)",
    )

    args = parser.parse_args()

    # Get project paths
    project_root = get_project_root()
    panels_dir = project_root / "docs" / "storyboards" / "act2" / "panels"

    # Parse resolution
    try:
        width, height = map(int, args.resolution.split("x"))
        resolution = (width, height)
    except ValueError:
        print(f"Invalid resolution format: {args.resolution}")
        sys.exit(1)

    # Determine music file
    music_file = None
    if not args.no_music:
        if args.music:
            music_file = Path(args.music)
        else:
            # Default to adventure_music
            music_file = project_root / "assets" / "audio" / "music" / "adventure_music.wav"
            if not music_file.exists():
                music_file = project_root / "docs" / "media" / "audio" / "music" / "adventure_music.mp3"

    if music_file and not music_file.exists():
        print(f"Warning: Music file not found: {music_file}")
        print("Creating animatic without music...")
        music_file = None

    # Determine output path
    output_file = Path(args.output)
    if not output_file.is_absolute():
        output_file = project_root / output_file

    print("=" * 60)
    print("ACT 2 ANIMATIC GENERATOR")
    print("Fairy Dinosaur Date Night")
    print("=" * 60)
    print(f"Panels directory: {panels_dir}")
    print(f"Output file: {output_file}")
    print(f"Resolution: {resolution[0]}x{resolution[1]}")
    print(f"FPS: {args.fps}")
    if music_file:
        print(f"Music: {music_file}")
    else:
        print("Music: None")
    print("=" * 60)

    # Create the animatic
    success = create_animatic(
        panels_dir=panels_dir,
        output_file=output_file,
        music_file=music_file,
        resolution=resolution,
        fps=args.fps,
    )

    if success:
        print("=" * 60)
        print(f"Animatic created successfully: {output_file}")

        # Get file info
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"File size: {size_mb:.1f} MB")

        print("=" * 60)
    else:
        print("Failed to create animatic")
        sys.exit(1)


if __name__ == "__main__":
    main()
