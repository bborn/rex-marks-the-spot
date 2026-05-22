#!/usr/bin/env python3
"""Generate P-Video motion clips from start frames using Replicate."""

import os
import time
import replicate
from pathlib import Path
import urllib.request

# REPLICATE_API_TOKEN must be set in environment (e.g. via ~/.bashrc)

OUTDIR = Path(__file__).parent

CLIPS = [
    {
        "name": "1A",
        "input_image": OUTDIR / "panel-1A-start.png",
        "prompt": "Camera stays still. Lightning flash illuminates the room through the windows. TV screen flickers with brief static. Children glance toward the window. Subtle movement only.",
        "output": OUTDIR / "panel-1A-clip.mp4",
    },
    {
        "name": "1B",
        "input_image": OUTDIR / "panel-1B-start.png",
        "prompt": "Camera slowly pushes in slightly. Boy looks down at his dinosaur toys and smiles contentedly. He squeezes the plush T-Rex. Gentle subtle movement.",
        "output": OUTDIR / "panel-1B-clip.mp4",
    },
    {
        "name": "1G",
        "input_image": OUTDIR / "panel-1G-start.png",
        "prompt": "Camera stays still. The girl on the left turns her head to look back over her shoulder with a concerned expression. The boy stays facing the TV. Parents move in background.",
        "output": OUTDIR / "panel-1G-clip.mp4",
    },
]

def generate_clip(clip_info):
    """Generate a P-Video clip from a start frame."""
    print(f"\nGenerating clip {clip_info['name']}...")
    print(f"  Input: {clip_info['input_image']}")
    print(f"  Prompt: {clip_info['prompt'][:80]}...")

    with open(clip_info["input_image"], "rb") as f:
        input_image = f.read()

    output = replicate.run(
        "prunaai/p-video",
        input={
            "image": open(clip_info["input_image"], "rb"),
            "prompt": clip_info["prompt"],
            "duration": 5,
            "resolution": "720p",
        },
    )

    # Output could be a URL or file-like object
    print(f"  Output type: {type(output)}")

    if isinstance(output, str):
        # It's a URL
        print(f"  Downloading from URL: {output[:100]}...")
        urllib.request.urlretrieve(output, str(clip_info["output"]))
    elif hasattr(output, 'read'):
        # File-like
        with open(clip_info["output"], "wb") as f:
            f.write(output.read())
    elif isinstance(output, list) and len(output) > 0:
        # List of URLs
        url = str(output[0])
        print(f"  Downloading from URL: {url[:100]}...")
        urllib.request.urlretrieve(url, str(clip_info["output"]))
    else:
        # Try to iterate
        print(f"  Output value: {output}")
        raise RuntimeError(f"Unexpected output type: {type(output)}")

    size = os.path.getsize(clip_info["output"])
    print(f"  Saved: {clip_info['output']} ({size} bytes)")
    return True

for i, clip in enumerate(CLIPS):
    generate_clip(clip)
    if i < len(CLIPS) - 1:
        print("Waiting 5s between clips...")
        time.sleep(5)

print("\n" + "=" * 60)
print("All clips generated successfully!")
print("=" * 60)
