#!/usr/bin/env python3
"""
Create Act 1 Animatic from storyboard panels with timing.

This script:
1. Reads panel timing from animatic-notes.md
2. Converts SVG placeholders to PNG where needed
3. Creates a video with proper panel durations
4. Adds background music track
5. Exports as MP4

Usage:
    python3 scripts/create_act1_animatic.py
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

# Try to import cairosvg for SVG conversion
try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False
    print("Warning: cairosvg not available. SVG files will be skipped.")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
PANELS_DIR = PROJECT_ROOT / "storyboards" / "act1" / "panels"
OUTPUT_DIR = PROJECT_ROOT / "output" / "animatics"
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio" / "music"

# Panel timing from animatic-notes.md (scene, panel, duration_seconds)
PANEL_TIMING = [
    # Scene 1: INT. HOME - EVENING (3:30 total)
    ("scene-01", "panel-01", 8),   # 1A - Wide establishing
    ("scene-01", "panel-02", 6),   # 1B - Medium - Leo
    ("scene-01", "panel-03", 15),  # 1C - Tracking - Nina
    ("scene-01", "panel-04", 45),  # 1D - Two-shot - Gabe/Nina
    ("scene-01", "panel-05", 5),   # 1E - Insert - Jenny
    ("scene-01", "panel-06", 4),   # 1F - Close-up - TV
    ("scene-01", "panel-07", 30),  # 1G - OTS - Kids watching
    ("scene-01", "panel-08", 20),  # 1H - Close-up - Mia
    ("scene-01", "panel-09", 77),  # 1I - Close-up - Gabe hesitates

    # Scene 2: EXT. HOUSE - NIGHT (0:15 total)
    ("scene-02", "panel-01", 6),   # 2A - Wide - house exterior
    ("scene-02", "panel-02", 5),   # 2B - Tracking - parents rush
    ("scene-02", "panel-03", 4),   # 2C - Low angle - lightning

    # Scene 3: INT. CAR - NIGHT (0:45 total)
    ("scene-03", "panel-01", 15),  # 3A - Two-shot - driving
    ("scene-03", "panel-02", 4),   # 3B - Insert - phone calling
    ("scene-03", "panel-03", 8),   # 3C - POV - windshield
    ("scene-03", "panel-04", 18),  # 3D - Close-up - Nina

    # Scene 4: INT. HOUSE - NIGHT MONTAGE (0:45 total)
    ("scene-04", "panel-01", 20),  # 4A - Wide - living room
    ("scene-04", "panel-02", 10),  # 4B - Insert - Jenny texting
    ("scene-04", "panel-03", 15),  # 4C - Insert - hidden phone

    # Scene 5: EXT. ROAD - NIGHT (0:20 total) - TIME WARP
    ("scene-05", "panel-01", 5),   # 5A - POV - road ahead
    ("scene-05", "panel-02", 4),   # 5B - Interior - reaction
    ("scene-05", "panel-03", 6),   # 5C - Wide - car swerves
    ("scene-05", "panel-04", 5),   # 5D - Close-up - vortex

    # Scene 6: INT. HOUSE - SIMULTANEOUSLY (0:20 total)
    ("scene-06", "panel-01", 5),   # 6A - Wide - TV explodes
    ("scene-06", "panel-02", 5),   # 6B - Reaction - all three
    ("scene-06", "panel-03", 5),   # 6C - Low light - atmosphere
    ("scene-06", "panel-04", 5),   # 6D - Insert - Nina's phone

    # Scene 7: INT. GABE'S CAR - DAY (1:30 total)
    ("scene-07", "panel-01", 15),  # 7A - Close-up - Nina wakes
    ("scene-07", "panel-02", 10),  # 7B - POV - car interior
    ("scene-07", "panel-03", 4),   # 7C - Insert - toy dinosaur
    ("scene-07", "panel-04", 20),  # 7D - Two-shot - rouse Gabe
    ("scene-07", "panel-05", 12),  # 7E - POV - Nina looking out
    ("scene-07", "panel-06", 29),  # 7F - Wide - swamp exterior

    # Scene 8: EXT. JURASSIC SWAMP - DAY (2:00 total)
    ("scene-08", "panel-01", 15),  # 8A - Wide - parents emerge
    ("scene-08", "panel-02", 10),  # 8B - POV - exotic plants
    ("scene-08", "panel-03", 15),  # 8C - Medium - time warp/creature
    ("scene-08", "panel-04", 5),   # 8D - Close-up - ground rumble
    ("scene-08", "panel-05", 5),   # 8E - Reaction - creature flees
    ("scene-08", "panel-06", 20),  # 8F - Wide - T-Rex appears
    ("scene-08", "panel-07", 15),  # 8G - Close-up - T-Rex head
    ("scene-08", "panel-08", 10),  # 8H - Low angle - car smash
    ("scene-08", "panel-09", 25),  # 8I - Tracking - parents flee

    # Scene 9: EXT. JURASSIC DENSE BRUSH - DAY (1:00 total)
    ("scene-09", "panel-01", 15),  # 9A - Steadicam - chase
    ("scene-09", "panel-02", 8),   # 9B - POV - looking back
    ("scene-09", "panel-03", 10),  # 9C - Wide - T-Rex crashes
    ("scene-09", "panel-04", 6),   # 9D - Medium - second dino
    ("scene-09", "panel-05", 12),  # 9E - Two-shot - running argue
    ("scene-09", "panel-06", 4),   # 9F - POV - cave spotted
    ("scene-09", "panel-07", 5),   # 9G - Tracking - slide into cave

    # Scene 10: INT. JURASSIC CAVE - DAY (1:30 total)
    ("scene-10", "panel-01", 15),  # 10A - Wide - cave interior
    ("scene-10", "panel-02", 10),  # 10B - Insert - T-Rex claws
    ("scene-10", "panel-03", 20),  # 10C - Two-shot - huddle
    ("scene-10", "panel-04", 10),  # 10D - Sound design shot
    ("scene-10", "panel-05", 15),  # 10E - Close-up - Nina
    ("scene-10", "panel-06", 15),  # 10F - Close-up - both realize
    ("scene-10", "panel-07", 5),   # 10G - Insert - phone (END)
]


def get_panel_path(scene: str, panel: str) -> Path:
    """Get the path to a panel file (PNG preferred, SVG fallback)."""
    png_path = PANELS_DIR / f"{scene}-{panel}.png"
    svg_path = PANELS_DIR / f"{scene}-{panel}.svg"

    if png_path.exists():
        return png_path
    elif svg_path.exists():
        return svg_path
    else:
        return None


def convert_svg_to_png(svg_path: Path, output_path: Path, width: int = 1920, height: int = 1080) -> bool:
    """Convert an SVG file to PNG."""
    if not HAS_CAIROSVG:
        return False

    try:
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(output_path),
            output_width=width,
            output_height=height
        )
        return True
    except Exception as e:
        print(f"Error converting {svg_path}: {e}")
        return False


def prepare_panels(temp_dir: Path) -> list:
    """
    Prepare all panels, converting SVGs to PNGs as needed.
    Returns list of (panel_path, duration) tuples.
    """
    prepared = []

    for i, (scene, panel, duration) in enumerate(PANEL_TIMING):
        panel_path = get_panel_path(scene, panel)

        if panel_path is None:
            print(f"Warning: Panel {scene}-{panel} not found, skipping")
            continue

        if panel_path.suffix == '.svg':
            # Convert SVG to PNG
            png_path = temp_dir / f"panel_{i:03d}.png"
            if convert_svg_to_png(panel_path, png_path):
                prepared.append((png_path, duration, f"{scene}-{panel}"))
                print(f"Converted: {scene}-{panel}.svg -> PNG")
            else:
                print(f"Warning: Could not convert {scene}-{panel}.svg")
        else:
            # Copy PNG to temp dir with sequential naming
            png_path = temp_dir / f"panel_{i:03d}.png"
            shutil.copy(panel_path, png_path)
            prepared.append((png_path, duration, f"{scene}-{panel}"))
            print(f"Using: {scene}-{panel}.png")

    return prepared


def create_concat_file(panels: list, temp_dir: Path) -> Path:
    """Create ffmpeg concat demuxer file with panel durations."""
    concat_file = temp_dir / "concat.txt"

    with open(concat_file, 'w') as f:
        for panel_path, duration, name in panels:
            # ffmpeg concat demuxer format
            f.write(f"file '{panel_path}'\n")
            f.write(f"duration {duration}\n")

        # Add last frame again to avoid truncation
        if panels:
            f.write(f"file '{panels[-1][0]}'\n")

    return concat_file


def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds."""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except:
        return 0


def create_animatic(panels: list, output_path: Path, audio_path: Path = None):
    """Create the animatic video using ffmpeg."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Calculate total duration
        total_duration = sum(duration for _, duration, _ in panels)
        print(f"\nTotal animatic duration: {total_duration}s ({total_duration // 60}:{total_duration % 60:02d})")

        # Create concat file
        concat_file = create_concat_file(panels, temp_path)

        # Build ffmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
        ]

        # Add audio if available
        if audio_path and audio_path.exists():
            audio_duration = get_audio_duration(audio_path)
            print(f"Using audio: {audio_path.name} ({audio_duration:.1f}s)")

            # Loop audio if shorter than video
            if audio_duration < total_duration:
                cmd.extend(['-stream_loop', '-1'])

            cmd.extend(['-i', str(audio_path)])
            cmd.extend(['-shortest'])
            cmd.extend(['-map', '0:v', '-map', '1:a'])
            cmd.extend(['-c:a', 'aac', '-b:a', '192k'])

        # Video encoding settings
        cmd.extend([
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-r', '24',
            str(output_path)
        ])

        print(f"\nCreating animatic: {output_path}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr}")
            return False

        return True


def main():
    """Main entry point."""
    print("=" * 60)
    print("Act 1 Animatic Creator")
    print("Fairy Dinosaur Date Night")
    print("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create temp directory for prepared panels
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        print("\n[1/3] Preparing panels...")
        panels = prepare_panels(temp_path)

        if not panels:
            print("Error: No panels found!")
            return 1

        print(f"\nPrepared {len(panels)} panels")

        # Find audio track
        audio_path = AUDIO_DIR / "main_theme.wav"
        if not audio_path.exists():
            # Try other audio files
            for audio_file in AUDIO_DIR.glob("*.wav"):
                audio_path = audio_file
                break
            else:
                audio_path = None
                print("\nNo audio track found, creating silent animatic")

        print("\n[2/3] Creating animatic video...")
        output_path = OUTPUT_DIR / "act1_animatic.mp4"

        success = create_animatic(panels, output_path, audio_path)

        if success:
            # Get output file size
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"\n[3/3] Done!")
            print(f"\nOutput: {output_path}")
            print(f"Size: {size_mb:.1f} MB")

            # Create a manifest file
            manifest_path = OUTPUT_DIR / "act1_animatic_manifest.txt"
            with open(manifest_path, 'w') as f:
                f.write("Act 1 Animatic - Panel Manifest\n")
                f.write("=" * 40 + "\n\n")

                cumulative = 0
                for panel_path, duration, name in panels:
                    start_time = f"{cumulative // 60}:{cumulative % 60:02d}"
                    cumulative += duration
                    end_time = f"{cumulative // 60}:{cumulative % 60:02d}"
                    f.write(f"{start_time} - {end_time}: {name} ({duration}s)\n")

                f.write(f"\nTotal duration: {cumulative // 60}:{cumulative % 60:02d}\n")

            print(f"Manifest: {manifest_path}")
            return 0
        else:
            print("\nError creating animatic!")
            return 1


if __name__ == "__main__":
    exit(main())
