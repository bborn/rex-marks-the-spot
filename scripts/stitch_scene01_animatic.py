#!/usr/bin/env python3
"""
Stitch Scene 1 panel clips into a rough animatic.

Produces two versions:
- Simple cut: hard cuts between panels
- Crossfade: 0.5s fade transitions between panels

Expects panel clips in output/scene01-panels/ and output/scene01-panel01-mvp/.
Outputs to output/scene01-animatic/ and uploads to R2.

Usage:
    python3 scripts/stitch_scene01_animatic.py
"""

import subprocess
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "scene01-animatic"
R2_PREFIX = "animation-tests/scene01-animatic"

# Panel clips in order (best version of each)
PANEL_SOURCES = {
    "01": "output/scene01-panel01-mvp/scene01-panel01-veo3-v1.mp4",
    "02": "output/scene01-panels/scene01-panel02-veo3.mp4",
    "03": "output/scene01-panels/scene01-panel03-veo3.mp4",
    "04": "output/scene01-panels/scene01-panel04-veo3.mp4",
    "05": "output/scene01-panels/scene01-panel05-veo3.mp4",
    "06": "output/scene01-panels/scene01-panel06-veo2.mp4",
    "07": "output/scene01-panels/scene01-panel07-veo3fast.mp4",
    "08": "output/scene01-panels/scene01-panel08-veo3fast.mp4",
    "09": "output/scene01-panels/scene01-panel09-veo2.mp4",
}

FADE_DURATION = 0.5


def get_duration(path):
    """Get video duration in seconds."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True,
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def has_audio(path):
    """Check if video has an audio stream."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    streams = json.loads(r.stdout).get("streams", [])
    return any(s["codec_type"] == "audio" for s in streams)


def normalize_panels():
    """Ensure all panels have audio tracks (add silence to Veo 2 clips)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    normalized = []

    for panel_id in sorted(PANEL_SOURCES.keys()):
        src = PROJECT_ROOT / PANEL_SOURCES[panel_id]
        dst = OUTPUT_DIR / f"panel{panel_id}.mp4"

        if not src.exists():
            print(f"  WARNING: Missing {src}")
            continue

        if has_audio(src):
            subprocess.run(["cp", str(src), str(dst)], check=True)
        else:
            # Add silent audio track
            subprocess.run([
                "ffmpeg", "-y", "-i", str(src),
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-c:v", "copy", "-c:a", "aac", "-shortest", str(dst),
            ], capture_output=True, check=True)
            print(f"  Added silent audio to panel {panel_id}")

        normalized.append(dst)

    return normalized


def stitch_simple(panels):
    """Create simple hard-cut animatic."""
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for p in panels:
            f.write(f"file '{p.name}'\n")

    output = OUTPUT_DIR / "scene01-animatic-simple.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output),
    ], capture_output=True, check=True)

    return output


def stitch_crossfade(panels):
    """Create animatic with crossfade transitions."""
    durations = [get_duration(p) for p in panels]
    n = len(panels)

    inputs = []
    for p in panels:
        inputs.extend(["-i", str(p)])

    # Build xfade filter chain
    filters = []
    for i in range(n - 1):
        offset = sum(durations[:i + 1]) - FADE_DURATION * (i + 1)

        v_in = f"[0:v][1:v]" if i == 0 else f"[vfade{i}][{i + 1}:v]"
        a_in = f"[0:a][1:a]" if i == 0 else f"[afade{i}][{i + 1}:a]"
        v_out = f"[vout]" if i == n - 2 else f"[vfade{i + 1}]"
        a_out = f"[aout]" if i == n - 2 else f"[afade{i + 1}]"

        filters.append(f"{v_in}xfade=transition=fade:duration={FADE_DURATION}:offset={offset:.3f}{v_out}")
        filters.append(f"{a_in}acrossfade=d={FADE_DURATION}:c1=tri:c2=tri{a_out}")

    output = OUTPUT_DIR / "scene01-animatic-crossfade.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output),
    ], capture_output=True, check=True)

    return output


def upload_to_r2(filepath):
    """Upload file to R2."""
    r2_path = f"{R2_PREFIX}/{filepath.name}"
    subprocess.run(
        ["rclone", "copy", str(filepath), f"r2:rex-assets/{R2_PREFIX}/"],
        check=True,
    )
    url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{r2_path}"
    print(f"  Uploaded: {url}")
    return url


def main():
    print("Normalizing panels (adding audio where missing)...")
    panels = normalize_panels()
    print(f"  {len(panels)} panels ready\n")

    print("Creating simple cut animatic...")
    simple = stitch_simple(panels)
    dur = get_duration(simple)
    size = simple.stat().st_size / (1024 * 1024)
    print(f"  {simple.name}: {dur:.1f}s, {size:.1f} MB\n")

    print("Creating crossfade animatic...")
    crossfade = stitch_crossfade(panels)
    dur = get_duration(crossfade)
    size = crossfade.stat().st_size / (1024 * 1024)
    print(f"  {crossfade.name}: {dur:.1f}s, {size:.1f} MB\n")

    print("Uploading to R2...")
    simple_url = upload_to_r2(simple)
    crossfade_url = upload_to_r2(crossfade)

    print(f"\nDone!")
    print(f"  Simple:    {simple_url}")
    print(f"  Crossfade: {crossfade_url}")


if __name__ == "__main__":
    main()
