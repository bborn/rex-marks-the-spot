#!/usr/bin/env python3
"""Compare video generation across multiple models.

Generates the same prompt with each model, collects timing and cost data,
and optionally uploads results to R2.

Usage:
    # From the scripts/ directory:
    python -m video.compare "A fairy dinosaur dancing in a jungle" --models veo-3.1 p-video-draft

    # With image input:
    python -m video.compare "Camera orbits around a 3D character" --image char.png --models veo-3.1 p-video

    # Upload results to R2:
    python -m video.compare "Test prompt" --models p-video-draft --upload
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from video.base import create_generator, VideoResult


def run_comparison(
    prompt: str,
    models: list[str],
    output_dir: str = "./video_compare",
    image_path: Optional[str] = None,
    duration_seconds: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "16:9",
    upload: bool = False,
) -> dict:
    """Generate videos with multiple models and compare results.

    Returns a summary dict with per-model results and cost totals.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results: list[dict] = []
    total_cost = 0.0

    print("=" * 60)
    print("Video Generation Comparison")
    print("=" * 60)
    print(f"Prompt:     {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"Models:     {', '.join(models)}")
    print(f"Resolution: {resolution}")
    print(f"Duration:   {duration_seconds}s")
    if image_path:
        print(f"Image:      {image_path}")
    print("=" * 60)
    print()

    for model_name in models:
        print(f"--- {model_name} ---")

        # Cost estimate before running
        try:
            gen = create_generator(model_name)
        except (ValueError, EnvironmentError) as e:
            print(f"  SKIP: {e}")
            results.append({
                "model": model_name,
                "status": "skipped",
                "error": str(e),
            })
            print()
            continue

        est_cost = gen.estimate_cost(duration_seconds, resolution)
        print(f"  Estimated cost: ${est_cost:.4f}")

        safe_name = model_name.replace(".", "_").replace(" ", "_")
        filename = f"{safe_name}_{timestamp}.mp4"
        out_path = str(output_dir / filename)

        try:
            result: VideoResult = gen.generate(
                prompt=prompt,
                output_path=out_path,
                duration_seconds=duration_seconds,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                image_path=image_path,
            )

            total_cost += result.estimated_cost
            entry = {
                "model": model_name,
                "status": "success",
                "file": result.file_path,
                "filename": filename,
                "duration_seconds": result.duration_seconds,
                "estimated_cost": result.estimated_cost,
                "generation_time_seconds": result.generation_time_seconds,
                "model_used": result.model_used,
                "metadata": result.metadata,
            }
            results.append(entry)

            print(f"  Duration:  {result.duration_seconds}s")
            print(f"  Cost:      ${result.estimated_cost:.4f}")
            print(f"  Gen time:  {result.generation_time_seconds:.1f}s")
            print(f"  Saved:     {result.file_path}")

        except Exception as e:
            results.append({
                "model": model_name,
                "status": "error",
                "error": str(e),
            })
            print(f"  ERROR: {e}")

        print()

    # Build summary
    summary = {
        "timestamp": timestamp,
        "prompt": prompt,
        "image_path": image_path,
        "resolution": resolution,
        "duration_seconds": duration_seconds,
        "aspect_ratio": aspect_ratio,
        "total_estimated_cost": round(total_cost, 4),
        "results": results,
    }

    # Save summary JSON
    summary_path = output_dir / f"comparison_{timestamp}.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to {summary_path}")

    # Upload to R2 if requested
    if upload:
        _upload_results(output_dir, timestamp, results)

    # Print final table
    print()
    print("=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"{'Model':<20} {'Status':<10} {'Cost':>8} {'Gen Time':>10} {'Duration':>10}")
    print("-" * 60)
    for r in results:
        status = r["status"]
        cost = f"${r.get('estimated_cost', 0):.4f}" if status == "success" else "—"
        gen_time = f"{r.get('generation_time_seconds', 0):.1f}s" if status == "success" else "—"
        duration = f"{r.get('duration_seconds', 0)}s" if status == "success" else "—"
        print(f"{r['model']:<20} {status:<10} {cost:>8} {gen_time:>10} {duration:>10}")
    print("-" * 60)
    print(f"{'TOTAL':<20} {'':10} ${total_cost:>7.4f}")
    print()

    return summary


def _upload_results(output_dir: Path, timestamp: str, results: list[dict]):
    """Upload generated videos and summary to R2."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from r2_upload import upload_file

        r2_prefix = f"video-compare/{timestamp}"

        for r in results:
            if r["status"] == "success":
                local = r["file"]
                r2_path = f"{r2_prefix}/{r['filename']}"
                try:
                    url = upload_file(local, r2_path)
                    r["r2_url"] = url
                    print(f"  Uploaded {r['filename']} -> {url}")
                except Exception as e:
                    print(f"  Upload failed for {r['filename']}: {e}")

        # Upload summary
        summary_file = output_dir / f"comparison_{timestamp}.json"
        if summary_file.exists():
            upload_file(str(summary_file), f"{r2_prefix}/comparison.json")

    except ImportError:
        print("  WARNING: r2_upload not found, skipping upload")


def main():
    parser = argparse.ArgumentParser(
        description="Compare video generation across models"
    )
    parser.add_argument("prompt", help="Text prompt for video generation")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["veo-3.1", "p-video-draft"],
        help="Models to compare (default: veo-3.1 p-video-draft)",
    )
    parser.add_argument("--image", help="Optional image path for image-to-video")
    parser.add_argument(
        "--duration", type=int, default=5, help="Video duration in seconds (default: 5)"
    )
    parser.add_argument("--resolution", default="720p", help="Resolution (default: 720p)")
    parser.add_argument("--aspect-ratio", default="16:9", help="Aspect ratio (default: 16:9)")
    parser.add_argument("--output-dir", default="./video_compare", help="Output directory")
    parser.add_argument("--upload", action="store_true", help="Upload results to R2")

    args = parser.parse_args()

    run_comparison(
        prompt=args.prompt,
        models=args.models,
        output_dir=args.output_dir,
        image_path=args.image,
        duration_seconds=args.duration,
        resolution=args.resolution,
        aspect_ratio=args.aspect_ratio,
        upload=args.upload,
    )


if __name__ == "__main__":
    main()
