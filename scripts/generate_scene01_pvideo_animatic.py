#!/usr/bin/env python3
"""
Generate Scene 1 full animatic using P-Video (prunaai/p-video) on Replicate.

Generates 9 standard-quality video clips (one per panel) from the existing
storyboard images, then stitches them into an animatic with ffmpeg.

Usage:
    export REPLICATE_API_TOKEN=...
    python3 scripts/generate_scene01_pvideo_animatic.py

Panel images are downloaded from R2. Generated clips and final animatic
are uploaded back to R2.
"""

import os
import sys
import json
import time
import urllib.request
import subprocess
from pathlib import Path
from datetime import datetime

# Ensure token is set
if not os.environ.get("REPLICATE_API_TOKEN"):
    print("ERROR: REPLICATE_API_TOKEN not set")
    sys.exit(1)

import replicate

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "scene01-pvideo-animatic"
PANELS_DIR = OUTPUT_DIR / "panels"
CLIPS_DIR = OUTPUT_DIR / "clips"

R2_PANEL_BASE = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/scene-01"
R2_UPLOAD_PREFIX = "animation-tests/scene01-pvideo-animatic"
R2_PUBLIC_BASE = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{R2_UPLOAD_PREFIX}"

MODEL = "prunaai/p-video"

# Per-panel prompts matching storyboard descriptions
PANEL_CONFIGS = [
    {
        "panel": "01",
        "name": "Wide Establishing Shot",
        "duration": 5,
        "prompt": (
            "Pixar-style 3D animated establishing shot of a cozy family living room "
            "on a stormy evening. Camera slowly pushes in. Warm lamplight flickers softly. "
            "Rain on window. TV casts blue glow across the room. Toy dinosaurs scattered "
            "on the floor. Rich warm color palette. Cinematic lighting, high quality animation."
        ),
    },
    {
        "panel": "02",
        "name": "Medium Shot - Leo",
        "duration": 5,
        "prompt": (
            "Pixar-style 3D animated medium shot of a young boy in dinosaur pajamas sitting "
            "on a couch hugging a plush T-Rex toy. Warm TV glow on his face. He watches "
            "contentedly and gives a quick smile. Soft warm interior lighting. "
            "Cinematic animation quality."
        ),
    },
    {
        "panel": "03",
        "name": "Tracking Shot - Nina",
        "duration": 5,
        "prompt": (
            "Pixar-style 3D animated tracking shot following an elegant woman in a black dress "
            "moving through her home putting on earrings. She multitasks gracefully - "
            "checking her purse, looking around. Warm golden interior lighting. "
            "Smooth camera movement. Cinematic quality."
        ),
    },
    {
        "panel": "04",
        "name": "Two-Shot - Gabe and Nina",
        "duration": 5,
        "prompt": (
            "Pixar-style 3D animated two-shot of a couple in formal black-tie attire. "
            "The man checks his watch impatiently while the woman adjusts her outfit. "
            "Warm interior lighting. Living room background with couch visible. "
            "Expressive character animation. Cinematic quality."
        ),
    },
    {
        "panel": "05",
        "name": "Close-up - Jenny",
        "duration": 5,
        "prompt": (
            "Pixar-style 3D animated close-up of a teenage girl with blonde ponytail "
            "looking down at her phone. Phone glow illuminates her face. She's absorbed "
            "in texting, cheerful but disconnected expression. Shallow depth of field. "
            "Cinematic lighting and animation quality."
        ),
    },
    {
        "panel": "06",
        "name": "Close-up - TV Flickering",
        "duration": 5,
        "prompt": (
            "Pixar-style 3D animated close-up of a TV screen showing a colorful cartoon "
            "that flickers with static. Horizontal scan lines roll through the image. "
            "Brief flash of blue light. Lightning flash reflected in the screen. "
            "Atmospheric and eerie. Cinematic quality."
        ),
    },
    {
        "panel": "07",
        "name": "Over-the-Shoulder - Kids Watching",
        "duration": 5,
        "prompt": (
            "Pixar-style 3D animated over-the-shoulder shot from behind two children "
            "on a couch looking at a TV. Parents visible preparing to leave in the "
            "background. Warm amber interior lighting contrasts with TV glow. "
            "Calm foreground, busy background. Cinematic quality."
        ),
    },
    {
        "panel": "08",
        "name": "Close-up - Mia",
        "duration": 5,
        "prompt": (
            "Pixar-style 3D animated close-up of an 8-year-old girl's face with big "
            "expressive eyes looking up with concern and vulnerability. Warm lighting. "
            "Camera slowly pushes in. Slight worry in her expression. Emotional and "
            "earnest. TV flicker reflects in her eyes. Cinematic quality."
        ),
    },
    {
        "panel": "09",
        "name": "Close-up - Gabe Hesitates",
        "duration": 5,
        "prompt": (
            "Pixar-style 3D animated close-up of a father's face showing inner conflict "
            "and hesitation. He's in a tuxedo. Warm interior lighting. His expression "
            "shifts from discomfort to resolution. Emotional moment. "
            "Cinematic quality, subtle animation."
        ),
    },
]


def download_panel_image(panel_id: str) -> Path:
    """Download a panel image from R2 if not already cached."""
    filename = f"scene-01-panel-{panel_id}.png"
    local_path = PANELS_DIR / filename
    if local_path.exists():
        return local_path

    print(f"  Downloading panel {panel_id} from R2 via rclone...")
    subprocess.run(
        ["rclone", "copy", f"r2:rex-assets/storyboards/act1/scene-01/{filename}", str(PANELS_DIR)],
        check=True,
    )
    return local_path


def generate_clip(config: dict) -> dict:
    """Generate a P-Video standard clip for one panel."""
    panel_id = config["panel"]
    image_path = download_panel_image(panel_id)
    output_path = CLIPS_DIR / f"scene01-panel{panel_id}-pvideo-std.mp4"

    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  Panel {panel_id} already exists ({size_mb:.1f} MB), skipping")
        return {
            "panel": panel_id,
            "name": config["name"],
            "success": True,
            "skipped": True,
            "filename": output_path.name,
            "file_size_mb": round(size_mb, 2),
        }

    print(f"\n{'='*60}")
    print(f"Panel {panel_id}: {config['name']}")
    print(f"  Prompt: {config['prompt'][:80]}...")
    print(f"{'='*60}")

    start_time = time.time()
    try:
        output = replicate.run(
            MODEL,
            input={
                "prompt": config["prompt"],
                "image": open(str(image_path), "rb"),
                "duration": config["duration"],
                "resolution": "720p",
                "aspect_ratio": "16:9",
                "draft": False,
            },
        )
        elapsed = time.time() - start_time
        print(f"  Generated in {elapsed:.1f}s")

        # Handle different output types from Replicate
        if hasattr(output, "read"):
            with open(output_path, "wb") as f:
                f.write(output.read())
        elif isinstance(output, str):
            urllib.request.urlretrieve(output, str(output_path))
        elif hasattr(output, "url"):
            urllib.request.urlretrieve(output.url, str(output_path))
        elif isinstance(output, list) and len(output) > 0:
            item = output[0]
            if isinstance(item, str):
                urllib.request.urlretrieve(item, str(output_path))
            elif hasattr(item, "url"):
                urllib.request.urlretrieve(item.url, str(output_path))
            elif hasattr(item, "read"):
                with open(output_path, "wb") as f:
                    f.write(item.read())
        else:
            # Try iterator
            with open(output_path, "wb") as f:
                for chunk in output:
                    if isinstance(chunk, bytes):
                        f.write(chunk)
                    elif hasattr(chunk, "read"):
                        f.write(chunk.read())

        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  Saved: {output_path.name} ({size_mb:.1f} MB)")

        return {
            "panel": panel_id,
            "name": config["name"],
            "success": True,
            "skipped": False,
            "filename": output_path.name,
            "file_size_mb": round(size_mb, 2),
            "generation_time_s": round(elapsed, 1),
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ERROR after {elapsed:.1f}s: {e}")
        return {
            "panel": panel_id,
            "name": config["name"],
            "success": False,
            "error": str(e),
            "generation_time_s": round(elapsed, 1),
        }


def get_duration(path: Path) -> float:
    """Get video duration in seconds."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True,
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def has_audio(path: Path) -> bool:
    """Check if video has an audio stream."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    streams = json.loads(r.stdout).get("streams", [])
    return any(s["codec_type"] == "audio" for s in streams)


def normalize_clip(src: Path, dst: Path):
    """Normalize a clip: re-encode to consistent format, add silent audio if missing."""
    if has_audio(src):
        # Re-encode to consistent format
        subprocess.run([
            "ffmpeg", "-y", "-i", str(src),
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart",
            str(dst),
        ], capture_output=True, check=True)
    else:
        # Add silent audio track + re-encode
        subprocess.run([
            "ffmpeg", "-y", "-i", str(src),
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            "-movflags", "+faststart",
            str(dst),
        ], capture_output=True, check=True)


def stitch_animatic(clips: list[Path]) -> tuple[Path, Path]:
    """Create two versions of the animatic: simple cuts and crossfade."""
    norm_dir = OUTPUT_DIR / "normalized"
    norm_dir.mkdir(exist_ok=True)

    # Normalize all clips
    normalized = []
    for clip in clips:
        norm = norm_dir / clip.name
        print(f"  Normalizing {clip.name}...")
        normalize_clip(clip, norm)
        normalized.append(norm)

    # Simple cut version
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for n in normalized:
            f.write(f"file '{n}'\n")

    simple_out = OUTPUT_DIR / "scene01-pvideo-animatic-simple.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(simple_out),
    ], capture_output=True, check=True)

    # Crossfade version
    durations = [get_duration(n) for n in normalized]
    fade_dur = 0.5
    n_clips = len(normalized)

    inputs = []
    for n in normalized:
        inputs.extend(["-i", str(n)])

    filters = []
    for i in range(n_clips - 1):
        offset = sum(durations[:i + 1]) - fade_dur * (i + 1)
        v_in = f"[0:v][1:v]" if i == 0 else f"[vfade{i}][{i + 1}:v]"
        a_in = f"[0:a][1:a]" if i == 0 else f"[afade{i}][{i + 1}:a]"
        v_out = "[vout]" if i == n_clips - 2 else f"[vfade{i + 1}]"
        a_out = "[aout]" if i == n_clips - 2 else f"[afade{i + 1}]"
        filters.append(f"{v_in}xfade=transition=fade:duration={fade_dur}:offset={offset:.3f}{v_out}")
        filters.append(f"{a_in}acrossfade=d={fade_dur}:c1=tri:c2=tri{a_out}")

    crossfade_out = OUTPUT_DIR / "scene01-pvideo-animatic-crossfade.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(crossfade_out),
    ], capture_output=True, check=True)

    return simple_out, crossfade_out


def upload_to_r2(filepath: Path) -> str:
    """Upload file to R2 and return public URL."""
    subprocess.run(
        ["rclone", "copy", str(filepath), f"r2:rex-assets/{R2_UPLOAD_PREFIX}/"],
        check=True,
    )
    url = f"{R2_PUBLIC_BASE}/{filepath.name}"
    print(f"  Uploaded: {url}")
    return url


def main():
    # Create directories
    for d in [OUTPUT_DIR, PANELS_DIR, CLIPS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"Generating Scene 1 P-Video animatic")
    print(f"  Model: {MODEL}")
    print(f"  Panels: {len(PANEL_CONFIGS)}")
    print(f"  Quality: standard (720p)")
    print(f"  Duration: 5s per clip")
    print()

    # Generate all clips
    results = []
    for i, config in enumerate(PANEL_CONFIGS):
        result = generate_clip(config)
        results.append(result)

        # Brief pause between generations to avoid rate limits
        if result["success"] and not result.get("skipped") and i < len(PANEL_CONFIGS) - 1:
            print("  Waiting 5s...")
            time.sleep(5)

    # Check which clips succeeded
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\n{'='*60}")
    print(f"Generation complete: {len(successful)}/{len(results)} panels")
    print(f"{'='*60}")

    if failed:
        print("Failed panels:")
        for r in failed:
            print(f"  Panel {r['panel']}: {r.get('error', 'unknown')}")

    if len(successful) < len(PANEL_CONFIGS):
        print(f"\nWARNING: Only {len(successful)}/{len(PANEL_CONFIGS)} panels generated.")
        if len(successful) == 0:
            print("No clips to stitch. Exiting.")
            return

    # Collect clip paths in order
    clips = []
    for config in PANEL_CONFIGS:
        clip_path = CLIPS_DIR / f"scene01-panel{config['panel']}-pvideo-std.mp4"
        if clip_path.exists():
            clips.append(clip_path)

    # Stitch animatic
    print(f"\n{'='*60}")
    print(f"Stitching animatic from {len(clips)} clips...")
    print(f"{'='*60}")

    simple_out, crossfade_out = stitch_animatic(clips)

    simple_dur = get_duration(simple_out)
    simple_size = simple_out.stat().st_size / (1024 * 1024)
    crossfade_dur = get_duration(crossfade_out)
    crossfade_size = crossfade_out.stat().st_size / (1024 * 1024)

    print(f"\n  Simple cut:  {simple_dur:.1f}s, {simple_size:.1f} MB")
    print(f"  Crossfade:   {crossfade_dur:.1f}s, {crossfade_size:.1f} MB")

    # Upload everything to R2
    print(f"\n{'='*60}")
    print("Uploading to R2...")
    print(f"{'='*60}")

    uploaded = {}
    for clip in clips:
        url = upload_to_r2(clip)
        uploaded[clip.name] = url

    simple_url = upload_to_r2(simple_out)
    crossfade_url = upload_to_r2(crossfade_out)

    # Save report
    report = {
        "task": "Scene 1 Full P-Video Animatic",
        "generated_at": datetime.now().isoformat(),
        "model": MODEL,
        "quality": "standard",
        "resolution": "720p",
        "clips": results,
        "animatic_simple": {
            "filename": simple_out.name,
            "url": simple_url,
            "duration_s": round(simple_dur, 1),
            "size_mb": round(simple_size, 1),
        },
        "animatic_crossfade": {
            "filename": crossfade_out.name,
            "url": crossfade_url,
            "duration_s": round(crossfade_dur, 1),
            "size_mb": round(crossfade_size, 1),
        },
        "clip_urls": uploaded,
    }

    report_path = OUTPUT_DIR / "pvideo_animatic_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    upload_to_r2(report_path)

    # Final summary
    print(f"\n{'='*60}")
    print("DONE!")
    print(f"{'='*60}")
    print(f"  Clips generated: {len(successful)}/{len(PANEL_CONFIGS)}")
    print(f"  Simple animatic:    {simple_url}")
    print(f"  Crossfade animatic: {crossfade_url}")
    total_time = sum(r.get("generation_time_s", 0) for r in results)
    print(f"  Total generation time: {total_time:.0f}s")


if __name__ == "__main__":
    main()
