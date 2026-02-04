#!/usr/bin/env python3
"""
Create Act 3 Animatic - Fairy Dinosaur Date Night

Combines storyboard panels from Act 3 with timing and music to create
an animatic video. Uses FFmpeg for video generation.

Usage:
    python3 scripts/create_act3_animatic.py

Options:
    --output PATH     Output file path (default: animatics/act3_animatic.mp4)
    --music PATH      Background music file
    --fps N           Frames per second (default: 24)
    --preview         Create lower resolution preview
    --no-music        Skip background music
"""

import os
import sys
import subprocess
import glob
import argparse
import tempfile
import shutil
from pathlib import Path


# Scene timing from animatic-notes.md (in seconds)
# Format: scene_number -> total_duration
SCENE_TIMINGS = {
    26: 180,  # 3:00 - Swamp Arrival
    27: 120,  # 2:00 - Colored Farts
    28: 90,   # 1:30 - Parents See Plumes
    29: 45,   # 0:45 - Parents Follow
    30: 30,   # 0:30 - Canyon Edge (Kids)
    31: 30,   # 0:30 - Canyon Edge (Parents)
    32: 180,  # 3:00 - Canyon Crossing
    33: 240,  # 4:00 - T-Rex Climax
    34: 45,   # 0:45 - Return
    35: 30,   # 0:30 - Standoff (split)
    36: 150,  # 2:30 - Standoff (main)
    37: 90,   # 1:30 - Epilogue
}


def get_panels_for_scene(panels_dir: str, scene_num: int) -> list:
    """Get all panel files for a specific scene, sorted by panel number."""
    pattern = os.path.join(panels_dir, f"scene-{scene_num:02d}-panel-*.png")
    panels = sorted(glob.glob(pattern))
    return panels


def get_all_panels(panels_dir: str) -> dict:
    """Get all panels organized by scene."""
    scenes = {}
    for scene_num in SCENE_TIMINGS.keys():
        panels = get_panels_for_scene(panels_dir, scene_num)
        if panels:
            scenes[scene_num] = panels
    return scenes


def calculate_panel_durations(scenes: dict) -> list:
    """
    Calculate duration for each panel based on scene timing and panel count.
    Returns list of (panel_path, duration_seconds) tuples.
    """
    panel_schedule = []

    for scene_num, panels in sorted(scenes.items()):
        scene_duration = SCENE_TIMINGS.get(scene_num, 60)  # Default 60s if missing
        panel_count = len(panels)

        if panel_count > 0:
            # Calculate base duration per panel
            base_duration = scene_duration / panel_count

            for panel_path in panels:
                panel_schedule.append((panel_path, base_duration))

    return panel_schedule


def create_concat_file(panel_schedule: list, output_path: str, fps: int) -> str:
    """
    Create an FFmpeg concat demuxer file with panel durations.
    Returns path to the concat file.
    """
    concat_path = os.path.join(output_path, "concat_list.txt")

    with open(concat_path, 'w') as f:
        for panel_path, duration in panel_schedule:
            # FFmpeg concat format: file 'path' and duration
            abs_path = os.path.abspath(panel_path)
            f.write(f"file '{abs_path}'\n")
            f.write(f"duration {duration}\n")

        # Need to repeat the last file for FFmpeg concat demuxer
        if panel_schedule:
            last_panel = os.path.abspath(panel_schedule[-1][0])
            f.write(f"file '{last_panel}'\n")

    return concat_path


def get_total_duration(panel_schedule: list) -> float:
    """Calculate total animatic duration in seconds."""
    return sum(duration for _, duration in panel_schedule)


def create_animatic_with_ffmpeg(
    concat_file: str,
    output_path: str,
    music_path: str = None,
    fps: int = 24,
    resolution: tuple = (1920, 1080),
    preview: bool = False,
    video_duration: float = None
):
    """
    Create animatic video using FFmpeg.
    """
    if preview:
        resolution = (960, 540)

    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
    ]

    # Add music if provided - use stream_loop to repeat music
    if music_path and os.path.exists(music_path):
        # Calculate how many times to loop the music
        # We use -stream_loop -1 for infinite loop, then cut with video length
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-stream_loop", "-1",  # Loop music infinitely
            "-i", music_path,
        ]

    # Video settings with scaling to consistent resolution
    cmd.extend([
        "-vf", f"scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264",
        "-preset", "medium" if not preview else "ultrafast",
        "-crf", "23" if not preview else "28",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
    ])

    # Audio settings
    if music_path and os.path.exists(music_path):
        cmd.extend([
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v",  # Use video from first input
            "-map", "1:a",  # Use audio from second input (looped)
        ])
        # Set duration to match video (not the looped audio)
        if video_duration:
            cmd.extend(["-t", str(video_duration)])
    else:
        cmd.extend(["-an"])  # No audio

    cmd.append(output_path)

    print(f"\nRunning FFmpeg command:")
    print(" ".join(cmd[:10]) + " ...")

    # Run FFmpeg
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr}")
        return False

    return True


def find_music_file() -> str:
    """Find a suitable music file from the project."""
    music_paths = [
        "assets/audio/music/adventure_music.wav",
        "docs/media/audio/music/adventure_music.mp3",
        "assets/audio/music/main_theme.wav",
        "docs/media/audio/music/main_theme.mp3",
    ]

    for path in music_paths:
        if os.path.exists(path):
            return path

    return None


def print_summary(panel_schedule: list, scenes: dict):
    """Print a summary of the animatic content."""
    print("\n" + "=" * 60)
    print("ACT 3 ANIMATIC SUMMARY")
    print("=" * 60)

    total_duration = get_total_duration(panel_schedule)
    total_panels = len(panel_schedule)

    print(f"\nTotal Duration: {int(total_duration // 60)}:{int(total_duration % 60):02d}")
    print(f"Total Panels: {total_panels}")
    print(f"Average Panel Duration: {total_duration / total_panels:.2f}s")

    print("\nScene Breakdown:")
    print("-" * 50)
    for scene_num in sorted(scenes.keys()):
        panel_count = len(scenes[scene_num])
        scene_duration = SCENE_TIMINGS.get(scene_num, 60)
        scene_names = {
            26: "Swamp Arrival",
            27: "Colored Farts",
            28: "Parents See Plumes",
            29: "Parents Follow",
            30: "Canyon Edge (Kids)",
            31: "Canyon Edge (Parents)",
            32: "Canyon Crossing",
            33: "T-Rex Climax",
            34: "Return",
            35: "Standoff (Part 1)",
            36: "Standoff (Part 2)",
            37: "Epilogue",
        }
        name = scene_names.get(scene_num, "Unknown")
        mins = scene_duration // 60
        secs = scene_duration % 60
        print(f"  Scene {scene_num}: {name}")
        print(f"           {panel_count} panels, {int(mins)}:{int(secs):02d}")
    print("-" * 50)


def main():
    parser = argparse.ArgumentParser(description="Create Act 3 Animatic")
    parser.add_argument("--output", "-o", default="animatics/act3_animatic.mp4",
                        help="Output file path")
    parser.add_argument("--music", "-m", help="Background music file path")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second")
    parser.add_argument("--preview", action="store_true",
                        help="Create lower resolution preview")
    parser.add_argument("--no-music", action="store_true",
                        help="Create animatic without music")
    parser.add_argument("--panels-dir", default="storyboards/act3/panels",
                        help="Directory containing panel images")

    args = parser.parse_args()

    print("=" * 60)
    print("FAIRY DINOSAUR DATE NIGHT - ACT 3 ANIMATIC GENERATOR")
    print("=" * 60)

    # Verify panels directory exists
    if not os.path.isdir(args.panels_dir):
        print(f"Error: Panels directory not found: {args.panels_dir}")
        sys.exit(1)

    # Get all panels
    print(f"\n[1/5] Scanning panels from {args.panels_dir}...")
    scenes = get_all_panels(args.panels_dir)

    if not scenes:
        print("Error: No panels found!")
        sys.exit(1)

    total_panels = sum(len(p) for p in scenes.values())
    print(f"      Found {total_panels} panels across {len(scenes)} scenes")

    # Calculate panel durations
    print("\n[2/5] Calculating panel timing...")
    panel_schedule = calculate_panel_durations(scenes)

    # Print summary
    print_summary(panel_schedule, scenes)

    # Find music
    music_path = None
    if not args.no_music:
        music_path = args.music or find_music_file()
        if music_path:
            print(f"\n[3/5] Using music: {music_path}")
        else:
            print("\n[3/5] No music file found - creating animatic without music")
    else:
        print("\n[3/5] Skipping music (--no-music flag)")

    # Create output directory
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Create temporary directory for concat file
    print("\n[4/5] Preparing FFmpeg input...")
    temp_dir = tempfile.mkdtemp(prefix="animatic_")

    try:
        concat_file = create_concat_file(panel_schedule, temp_dir, args.fps)

        # Create animatic
        print(f"\n[5/5] Creating animatic video...")
        print(f"      Output: {args.output}")
        print(f"      FPS: {args.fps}")
        print(f"      Preview mode: {args.preview}")

        total_duration = get_total_duration(panel_schedule)
        success = create_animatic_with_ffmpeg(
            concat_file=concat_file,
            output_path=args.output,
            music_path=music_path,
            fps=args.fps,
            preview=args.preview,
            video_duration=total_duration
        )

        if success:
            print("\n" + "=" * 60)
            print("SUCCESS! Animatic created!")
            print("=" * 60)
            print(f"\nOutput file: {os.path.abspath(args.output)}")

            # Get file size
            if os.path.exists(args.output):
                size_mb = os.path.getsize(args.output) / (1024 * 1024)
                print(f"File size: {size_mb:.1f} MB")

            total_duration = get_total_duration(panel_schedule)
            print(f"Duration: {int(total_duration // 60)}:{int(total_duration % 60):02d}")
        else:
            print("\nError: Failed to create animatic!")
            sys.exit(1)

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
