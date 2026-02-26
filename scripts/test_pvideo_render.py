#!/usr/bin/env python3
"""Test P-Video render using Scene 1 Panel 01 storyboard and compare with Veo output.

Generates a test video clip via Replicate P-Video (prunaai/p-video),
compares metadata/quality against existing Veo-generated scene01 video,
uploads results to R2, and prints a quality/cost comparison report.

Usage:
    cd scripts/
    python test_pvideo_render.py
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure scripts/ is on the path so `from video import ...` works
sys.path.insert(0, str(Path(__file__).resolve().parent))

from video.base import create_generator

# ---------- Configuration ----------

STORYBOARD_IMAGE = str(
    Path(__file__).resolve().parent.parent
    / "storyboards"
    / "sketches"
    / "scene-01-panel-01-sketch.png"
)

VEO_REFERENCE_VIDEO = str(
    Path(__file__).resolve().parent.parent
    / "docs"
    / "media"
    / "video"
    / "scene01_home_evening.mp4"
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "pvideo-test"

PROMPT = (
    "Slow camera pan across a cozy family living room in the evening. "
    "Warm golden lighting from a table lamp illuminates the scene. "
    "A family sits on a comfortable sofa — parents and two young children. "
    "Pixar-style 3D animation with soft shadows and rich colors. "
    "Gentle ambient movement, breathing, subtle hair sway."
)

R2_UPLOAD_PREFIX = "animation-tests/pvideo-test"


# ---------- Helpers ----------

def get_video_metadata(path: str) -> dict:
    """Extract video metadata using ffprobe."""
    if not os.path.exists(path):
        return {"error": f"File not found: {path}"}

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                path,
            ],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        streams = data.get("streams", [])

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        return {
            "file": path,
            "file_size_bytes": int(fmt.get("size", 0)),
            "file_size_mb": round(int(fmt.get("size", 0)) / (1024 * 1024), 2),
            "duration_seconds": round(float(fmt.get("duration", 0)), 2),
            "format": fmt.get("format_name", "unknown"),
            "video_codec": video_stream.get("codec_name", "unknown"),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "fps": video_stream.get("avg_frame_rate", "unknown"),
            "has_audio": audio_stream is not None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        }
    except Exception as e:
        return {"error": str(e)}


def upload_to_r2(local_path: str, r2_key: str) -> str:
    """Upload a file to R2 and return the public URL."""
    r2_dest = f"r2:rex-assets/{r2_key}"
    print(f"  Uploading {os.path.basename(local_path)} -> {r2_dest}")
    result = subprocess.run(
        ["rclone", "copy", local_path, f"r2:rex-assets/{os.path.dirname(r2_key)}/"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  WARNING: rclone upload failed: {result.stderr}")
        return ""
    url = f"https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/{r2_key}"
    print(f"  -> {url}")
    return url


def run_pvideo_test():
    """Run P-Video generation test and comparison."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("P-VIDEO TEST RENDER - Scene 1 Panel 01")
    print("=" * 70)
    print()

    # Validate inputs
    if not os.path.exists(STORYBOARD_IMAGE):
        print(f"ERROR: Storyboard image not found: {STORYBOARD_IMAGE}")
        sys.exit(1)
    print(f"Input image:  {STORYBOARD_IMAGE}")
    print(f"  Size: {os.path.getsize(STORYBOARD_IMAGE) / 1024:.0f} KB")

    veo_exists = os.path.exists(VEO_REFERENCE_VIDEO)
    if veo_exists:
        print(f"Veo reference: {VEO_REFERENCE_VIDEO}")
    else:
        print("Veo reference: NOT FOUND (will skip comparison)")
    print()

    # ---------- Run P-Video (draft mode for cost savings) ----------
    print("-" * 70)
    print("STEP 1: Generate with P-Video (draft mode, 720p)")
    print("-" * 70)

    pvideo_draft_path = str(OUTPUT_DIR / f"pvideo_draft_{timestamp}.mp4")

    try:
        gen_draft = create_generator("p-video-draft")
        est = gen_draft.estimate_cost(5, "720p")
        print(f"Estimated cost (draft, 5s, 720p): ${est:.4f}")
        print()
        print("Generating...")

        result_draft = gen_draft.generate(
            prompt=PROMPT,
            output_path=pvideo_draft_path,
            duration_seconds=5,
            aspect_ratio="16:9",
            resolution="720p",
            image_path=STORYBOARD_IMAGE,
        )

        print(f"  Duration:  {result_draft.duration_seconds}s")
        print(f"  Cost:      ${result_draft.estimated_cost:.4f}")
        print(f"  Gen time:  {result_draft.generation_time_seconds:.1f}s")
        print(f"  Saved:     {result_draft.file_path}")
        print()
    except Exception as e:
        print(f"  ERROR generating draft: {e}")
        result_draft = None

    # ---------- Run P-Video (standard mode) ----------
    print("-" * 70)
    print("STEP 2: Generate with P-Video (standard mode, 720p)")
    print("-" * 70)

    pvideo_std_path = str(OUTPUT_DIR / f"pvideo_standard_{timestamp}.mp4")

    try:
        gen_std = create_generator("p-video")
        est = gen_std.estimate_cost(5, "720p")
        print(f"Estimated cost (standard, 5s, 720p): ${est:.4f}")
        print()
        print("Generating...")

        result_std = gen_std.generate(
            prompt=PROMPT,
            output_path=pvideo_std_path,
            duration_seconds=5,
            aspect_ratio="16:9",
            resolution="720p",
            image_path=STORYBOARD_IMAGE,
        )

        print(f"  Duration:  {result_std.duration_seconds}s")
        print(f"  Cost:      ${result_std.estimated_cost:.4f}")
        print(f"  Gen time:  {result_std.generation_time_seconds:.1f}s")
        print(f"  Saved:     {result_std.file_path}")
        print()
    except Exception as e:
        print(f"  ERROR generating standard: {e}")
        result_std = None

    # ---------- Gather metadata ----------
    print("-" * 70)
    print("STEP 3: Video Metadata Comparison")
    print("-" * 70)

    all_videos = {}

    if veo_exists:
        all_videos["veo_scene01"] = get_video_metadata(VEO_REFERENCE_VIDEO)
    if result_draft and os.path.exists(pvideo_draft_path):
        all_videos["pvideo_draft"] = get_video_metadata(pvideo_draft_path)
    if result_std and os.path.exists(pvideo_std_path):
        all_videos["pvideo_standard"] = get_video_metadata(pvideo_std_path)

    for label, meta in all_videos.items():
        print(f"\n  [{label}]")
        if "error" in meta:
            print(f"    Error: {meta['error']}")
        else:
            print(f"    Resolution: {meta['width']}x{meta['height']}")
            print(f"    Duration:   {meta['duration_seconds']}s")
            print(f"    FPS:        {meta['fps']}")
            print(f"    Codec:      {meta['video_codec']}")
            print(f"    File size:  {meta['file_size_mb']} MB")
            print(f"    Audio:      {'Yes (' + meta['audio_codec'] + ')' if meta['has_audio'] else 'No'}")

    # ---------- Cost Comparison ----------
    print()
    print("-" * 70)
    print("STEP 4: Cost Comparison")
    print("-" * 70)

    cost_data = []

    if result_draft:
        cost_data.append({
            "model": "P-Video (draft)",
            "duration": f"{result_draft.duration_seconds}s",
            "resolution": "720p",
            "cost": result_draft.estimated_cost,
            "gen_time": result_draft.generation_time_seconds,
        })

    if result_std:
        cost_data.append({
            "model": "P-Video (standard)",
            "duration": f"{result_std.duration_seconds}s",
            "resolution": "720p",
            "cost": result_std.estimated_cost,
            "gen_time": result_std.generation_time_seconds,
        })

    # Add Veo estimates for comparison (no actual generation)
    veo_estimates = [
        ("Veo 2 (est)", 8, "720p", 0.02 * 8),
        ("Veo 3 (est)", 8, "720p", 0.03 * 8),
        ("Veo 3.1 (est)", 8, "720p", 0.035 * 8),
    ]
    for name, dur, res, cost in veo_estimates:
        cost_data.append({
            "model": name,
            "duration": f"{dur}s",
            "resolution": res,
            "cost": cost,
            "gen_time": "N/A (estimated)",
        })

    print()
    print(f"{'Model':<22} {'Duration':>10} {'Resolution':>12} {'Cost':>10} {'Gen Time':>12}")
    print("-" * 70)
    for row in cost_data:
        gt = f"{row['gen_time']:.1f}s" if isinstance(row["gen_time"], float) else row["gen_time"]
        print(f"{row['model']:<22} {row['duration']:>10} {row['resolution']:>12} ${row['cost']:>8.4f} {gt:>12}")

    # ---------- Upload to R2 ----------
    print()
    print("-" * 70)
    print("STEP 5: Upload to R2")
    print("-" * 70)

    uploaded_urls = {}

    if result_draft and os.path.exists(pvideo_draft_path):
        fname = os.path.basename(pvideo_draft_path)
        url = upload_to_r2(pvideo_draft_path, f"{R2_UPLOAD_PREFIX}/{fname}")
        if url:
            uploaded_urls["pvideo_draft"] = url

    if result_std and os.path.exists(pvideo_std_path):
        fname = os.path.basename(pvideo_std_path)
        url = upload_to_r2(pvideo_std_path, f"{R2_UPLOAD_PREFIX}/{fname}")
        if url:
            uploaded_urls["pvideo_standard"] = url

    # ---------- Build and save report ----------
    report = {
        "test_name": "P-Video Test Render - Scene 1 Panel 01",
        "timestamp": timestamp,
        "prompt": PROMPT,
        "input_image": STORYBOARD_IMAGE,
        "results": {},
        "cost_comparison": cost_data,
        "uploaded_urls": uploaded_urls,
    }

    if result_draft:
        report["results"]["pvideo_draft"] = {
            "status": "success",
            "duration_seconds": result_draft.duration_seconds,
            "estimated_cost": result_draft.estimated_cost,
            "generation_time_seconds": result_draft.generation_time_seconds,
            "metadata": result_draft.metadata,
            "video_info": all_videos.get("pvideo_draft", {}),
        }
    if result_std:
        report["results"]["pvideo_standard"] = {
            "status": "success",
            "duration_seconds": result_std.duration_seconds,
            "estimated_cost": result_std.estimated_cost,
            "generation_time_seconds": result_std.generation_time_seconds,
            "metadata": result_std.metadata,
            "video_info": all_videos.get("pvideo_standard", {}),
        }
    if veo_exists:
        report["results"]["veo_reference"] = {
            "status": "reference",
            "video_info": all_videos.get("veo_scene01", {}),
        }

    report_path = str(OUTPUT_DIR / f"pvideo_test_report_{timestamp}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport saved: {report_path}")

    # Upload report
    report_url = upload_to_r2(report_path, f"{R2_UPLOAD_PREFIX}/pvideo_test_report_{timestamp}.json")
    if report_url:
        uploaded_urls["report"] = report_url

    # ---------- Final Summary ----------
    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    total_cost = 0
    for r in [result_draft, result_std]:
        if r:
            total_cost += r.estimated_cost

    print(f"  Total P-Video cost:  ${total_cost:.4f}")
    print(f"  Videos generated:    {sum(1 for r in [result_draft, result_std] if r)}")
    if uploaded_urls:
        print(f"  Uploaded to R2:")
        for label, url in uploaded_urls.items():
            print(f"    {label}: {url}")

    print()
    print("Quality Notes:")
    print("  - P-Video draft: Faster, cheaper, lower quality (good for iteration)")
    print("  - P-Video standard: Slower, higher quality (good for final renders)")
    print("  - Veo 3.1: Premium quality but ~3-4x more expensive for same duration")
    print()

    return report


if __name__ == "__main__":
    run_pvideo_test()
