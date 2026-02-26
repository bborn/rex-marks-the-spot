#!/usr/bin/env python3
"""
P-Video IMAGE-TO-VIDEO test with Scene 1 Panel 01 storyboard.
Generates 3 variants for comparison with Veo outputs.
"""

import os
import sys
import json
import time
import urllib.request
import subprocess

# Ensure REPLICATE_API_TOKEN is set in environment (e.g. via ~/.bashrc)
if not os.environ.get("REPLICATE_API_TOKEN"):
    print("ERROR: REPLICATE_API_TOKEN not set. Source ~/.bashrc or export it.")
    sys.exit(1)

import replicate

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
INPUT_IMAGE = os.path.join(OUTPUT_DIR, "scene-01-panel-01.png")
R2_PATH = "r2:rex-assets/animation-tests/pvideo-img2vid-test/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/pvideo-img2vid-test/"

MODEL = "prunaai/p-video"

ATMOSPHERIC_PROMPT = (
    "Pixar-style 3D animated establishing shot of a cozy living room on a stormy evening. "
    "Camera slowly pushes in. Warm lamplight flickers softly. Rain on window. "
    "TV casts blue glow. Cinematic lighting."
)

CINEMATIC_PROMPT = (
    "Beautifully lit 3D animated Pixar-quality interior scene. "
    "Slow smooth push-in. Warm golden light from table lamps. "
    "Thunderstorm outside with rain and lightning. Shallow depth of field."
)

VARIANTS = [
    {
        "name": "pvideo-draft-720p-5s-atmospheric",
        "filename": "pvideo-draft-720p-5s-atmospheric.mp4",
        "prompt": ATMOSPHERIC_PROMPT,
        "duration": 5,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "draft": True,
        "est_cost": 0.025,
    },
    {
        "name": "pvideo-std-720p-5s-atmospheric",
        "filename": "pvideo-std-720p-5s-atmospheric.mp4",
        "prompt": ATMOSPHERIC_PROMPT,
        "duration": 5,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "draft": False,
        "est_cost": 0.10,
    },
    {
        "name": "pvideo-std-1080p-5s-cinematic",
        "filename": "pvideo-std-1080p-5s-cinematic.mp4",
        "prompt": CINEMATIC_PROMPT,
        "duration": 5,
        "resolution": "1080p",
        "aspect_ratio": "16:9",
        "draft": False,
        "est_cost": 0.20,
    },
]


def run_variant(variant):
    """Run a single P-Video variant and return results."""
    print(f"\n{'='*60}")
    print(f"Running: {variant['name']}")
    print(f"  Prompt: {variant['prompt'][:80]}...")
    print(f"  Resolution: {variant['resolution']}, Draft: {variant['draft']}")
    print(f"  Est. cost: ${variant['est_cost']:.3f}")
    print(f"{'='*60}")

    output_path = os.path.join(OUTPUT_DIR, variant["filename"])

    input_params = {
        "prompt": variant["prompt"],
        "image": open(INPUT_IMAGE, "rb"),
        "duration": variant["duration"],
        "resolution": variant["resolution"],
        "aspect_ratio": variant["aspect_ratio"],
        "draft": variant["draft"],
    }

    start_time = time.time()
    try:
        output = replicate.run(MODEL, input=input_params)
        elapsed = time.time() - start_time
        print(f"  Generation completed in {elapsed:.1f}s")

        # Output could be a FileOutput, URL string, or iterator
        # Handle different return types
        if hasattr(output, "read"):
            # It's a file-like object
            with open(output_path, "wb") as f:
                f.write(output.read())
        elif isinstance(output, str):
            # It's a URL - download it
            print(f"  Downloading from URL: {output[:100]}...")
            urllib.request.urlretrieve(output, output_path)
        elif hasattr(output, "url"):
            # FileOutput with url attribute
            print(f"  Downloading from: {output.url[:100]}...")
            urllib.request.urlretrieve(output.url, output_path)
        elif isinstance(output, list) and len(output) > 0:
            # List of outputs - take the first
            item = output[0]
            if isinstance(item, str):
                urllib.request.urlretrieve(item, output_path)
            elif hasattr(item, "url"):
                urllib.request.urlretrieve(item.url, output_path)
            elif hasattr(item, "read"):
                with open(output_path, "wb") as f:
                    f.write(item.read())
            else:
                print(f"  WARNING: Unknown list item type: {type(item)}")
                print(f"  Value: {item}")
                # Try to write it directly
                with open(output_path, "wb") as f:
                    f.write(bytes(item) if not isinstance(item, bytes) else item)
        else:
            print(f"  Output type: {type(output)}")
            print(f"  Output value: {output}")
            # Try to iterate (generator)
            try:
                with open(output_path, "wb") as f:
                    for chunk in output:
                        if isinstance(chunk, bytes):
                            f.write(chunk)
                        elif hasattr(chunk, "read"):
                            f.write(chunk.read())
                        else:
                            f.write(bytes(chunk))
            except TypeError:
                # Last resort - try direct write
                with open(output_path, "wb") as f:
                    f.write(bytes(output) if not isinstance(output, bytes) else output)

        file_size = os.path.getsize(output_path)
        print(f"  Saved: {output_path} ({file_size / 1024 / 1024:.2f} MB)")

        return {
            "name": variant["name"],
            "filename": variant["filename"],
            "success": True,
            "generation_time_s": round(elapsed, 1),
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "est_cost": variant["est_cost"],
            "resolution": variant["resolution"],
            "draft": variant["draft"],
            "prompt_type": "atmospheric" if "atmospheric" in variant["name"] else "cinematic",
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ERROR after {elapsed:.1f}s: {e}")
        return {
            "name": variant["name"],
            "filename": variant["filename"],
            "success": False,
            "error": str(e),
            "generation_time_s": round(elapsed, 1),
            "est_cost": variant["est_cost"],
            "resolution": variant["resolution"],
            "draft": variant["draft"],
        }


def upload_to_r2(local_path, r2_dest):
    """Upload a file to R2 using rclone."""
    print(f"  Uploading {os.path.basename(local_path)} to R2...")
    result = subprocess.run(
        ["rclone", "copy", local_path, r2_dest],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  Upload successful")
        return True
    else:
        print(f"  Upload failed: {result.stderr}")
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(INPUT_IMAGE):
        print(f"ERROR: Input image not found: {INPUT_IMAGE}")
        sys.exit(1)

    print(f"Input image: {INPUT_IMAGE}")
    print(f"Model: {MODEL}")
    print(f"Variants to generate: {len(VARIANTS)}")
    print(f"Total est. cost: ${sum(v['est_cost'] for v in VARIANTS):.3f}")

    results = []
    for variant in VARIANTS:
        result = run_variant(variant)
        results.append(result)

    # Upload successful outputs to R2
    print(f"\n{'='*60}")
    print("Uploading to R2...")
    print(f"{'='*60}")
    for result in results:
        if result["success"]:
            local_path = os.path.join(OUTPUT_DIR, result["filename"])
            uploaded = upload_to_r2(local_path, R2_PATH)
            result["r2_url"] = R2_PUBLIC + result["filename"] if uploaded else None
            result["uploaded"] = uploaded

    # Also upload the input image for reference
    upload_to_r2(INPUT_IMAGE, R2_PATH)

    # Save report
    report = {
        "test": "P-Video IMAGE-TO-VIDEO test",
        "model": MODEL,
        "input_image": "scene-01-panel-01.png",
        "input_image_url": "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/panels/scene-01-panel-01.png",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": results,
        "total_est_cost": sum(r["est_cost"] for r in results),
        "total_generation_time_s": sum(r["generation_time_s"] for r in results),
        "comparison_veo_urls": {
            "veo2": "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-panel01-mvp/scene01-panel01-veo2-v1.mp4",
            "veo3": "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-panel01-mvp/scene01-panel01-veo3-v1.mp4",
            "veo31": "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/animation-tests/scene01-panel01-mvp/scene01-panel01-veo31-v1.mp4",
        },
    }

    report_path = os.path.join(OUTPUT_DIR, "pvideo_img2vid_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved: {report_path}")

    # Upload report to R2
    upload_to_r2(report_path, R2_PATH)

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "OK" if r["success"] else f"FAILED: {r.get('error', 'unknown')}"
        if r["success"]:
            print(f"  {r['name']}: {status}")
            print(f"    Size: {r['file_size_mb']} MB, Time: {r['generation_time_s']}s")
            print(f"    URL: {r.get('r2_url', 'N/A')}")
        else:
            print(f"  {r['name']}: {status}")

    successful = sum(1 for r in results if r["success"])
    print(f"\n  {successful}/{len(results)} variants generated successfully")
    print(f"  Total est. cost: ${report['total_est_cost']:.3f}")
    print(f"  Total generation time: {report['total_generation_time_s']:.1f}s")

    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
