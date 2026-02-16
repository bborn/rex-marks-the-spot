#!/usr/bin/env python3
"""
Generate Mia character turnaround V3 with SCULPTED CHUNKY HAIR.

KEY CHANGE FROM V2:
Hair must be SOLID SCULPTED VOLUMES like Pixar's Mirabel (Encanto) or Moana.
NO individual curly strands - they create terrible mesh artifacts in Meshy 3D.
Curl texture comes from PAINTED SURFACE, not silhouette edge.
Hair silhouette must be SMOOTH and CHUNKY.

Also updated:
- Brown/dark skin tone
- Pink headband (not scrunchie)
- Pink t-shirt with polka dots
- Blue jeans (not shorts)
- Red sneakers
- A-Pose for 3D modeling

Usage:
    python scripts/generate_mia_turnaround_v3.py
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "mia_turnaround_v3"
R2_DEST = "r2:rex-assets/characters/mia/turnaround-v2/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/characters/mia/turnaround-v2"

# Core character description - SCULPTED CHUNKY HAIR is the critical change
BASE_PROMPT = """Character turnaround model sheet for 3D animation production.
Pixar-quality stylized 3D animated character design.

CHARACTER: Mia, an 8-year-old girl.

SKIN: Brown/dark skin tone, warm and rich. NOT light or pale.

FACE: Big expressive brown eyes, Pixar-style proportions with large head and big eyes relative to body.
Small nose, cheerful expression, light freckles optional.

HAIR - THIS IS THE MOST CRITICAL ELEMENT:
Dark brown/black curly hair styled as SCULPTED CHUNKY VOLUMES.
Think Pixar's Mirabel from Encanto or Moana - the curls read as SOLID CARVED SHAPES, like clay or sculpted foam.
The hair has a SMOOTH OUTER SILHOUETTE with NO wispy strands, NO thin curly pieces, NO flyaway hairs.
Curl texture comes from the PAINTED SURFACE DETAIL on the hair mass, NOT from the edge silhouette.
The hair silhouette is ROUND, SMOOTH, and CHUNKY - like a solid helmet of sculpted curls.
Hair is shoulder-length, full and voluminous, with a PINK HEADBAND pushing it back from the forehead.
The headband is bright pink and clearly visible from front and side views.
NO ponytail - the hair is DOWN, held back by the headband, falling in chunky sculpted curl volumes.

OUTFIT:
- PINK T-SHIRT (bright bubblegum pink) with small white polka dots
- BLUE JEANS (full length, regular kid's denim jeans, NOT shorts)
- RED SNEAKERS with white soles and white laces

POSE: A-POSE for 3D modeling reference:
- Arms held slightly away from body at approximately 30-45 degrees
- Fingers relaxed, palms facing thighs
- Legs slightly apart, feet flat
- Standing straight, looking forward

LAYOUT: Character turnaround sheet showing THREE VIEWS arranged horizontally on a clean white background:
- LEFT: FRONT VIEW (largest, facing camera directly)
- CENTER: SIDE PROFILE VIEW (full 90-degree side view showing hair volume)
- RIGHT: BACK VIEW (facing away, showing back of hair and outfit)

All three views must show the EXACT SAME character with IDENTICAL design, proportions, and outfit.
Even, flat lighting with no dramatic shadows. Clean white or very light gray background.
Professional animation studio model sheet quality.
Stylized Pixar/Disney 3D animation aesthetic, NOT photorealistic."""


# Three variations with different emphasis on the chunky hair
VARIATIONS = [
    {
        "name": "v3a",
        "suffix": """The hair is like SCULPTED CLAY - imagine the curls were carved from a single block of dark brown clay.
Each curl is a THICK ROUNDED SHAPE, like fat tubes or thick ribbons wound together.
The overall hair shape is a SMOOTH DOME that frames her face, with the curl definition visible as
surface texture and slight bumps on the smooth overall volume. Think PlayDoh or claymation hair.
Headband is a simple bright pink band. Expression is curious and brave.""",
    },
    {
        "name": "v3b",
        "suffix": """The hair looks like CHUNKY CARVED WOOD or SOLID FOAM shapes.
The curls are BIG, BOLD, BLOCKY volumes - each curl section is at least 2-3 inches wide.
NO thin strands at all. The hair masses read as 5-6 large chunky curl sections clustered together.
From the side, the hair silhouette is ONE SMOOTH CURVED LINE with minimal bumps.
Pink headband is slightly wider. Expression is determined and confident.""",
    },
    {
        "name": "v3c",
        "suffix": """The hair has a SIMPLIFIED GEOMETRIC quality - like Moana's hair in Disney's movie.
Large flowing sections of hair that read as SOLID MASSES, not individual strands.
The curly texture is suggested through SUBTLE WAVE PATTERNS on the surface of thick hair chunks.
The entire head of hair could be described as 3-4 LARGE SCULPTED PIECES fitting together.
From any angle, the hair edge is CLEAN and SMOOTH, not fuzzy or stringy.
Pink headband sits neatly on top. Expression is warm and friendly.""",
    },
]


def generate_turnaround(prompt: str, name: str) -> bool:
    """Generate a single turnaround sheet."""
    output_path = OUTPUT_DIR / f"mia_{name}.png"

    print(f"\n{'='*50}")
    print(f"Generating: {name}")
    print(f"  Output: {output_path}")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=f"Generate an image: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract and save image
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_path, "wb") as f:
                    f.write(image_data)
                size_kb = len(image_data) / 1024
                print(f"  SAVED: {output_path.name} ({size_kb:.0f} KB)")
                return True

        # Check for text response (sometimes model refuses or gives text only)
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                print(f"  Text response: {part.text[:200]}")

        print(f"  FAILED: No image in response")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def upload_to_r2(local_dir: Path) -> list:
    """Upload all generated images to R2."""
    urls = []
    print(f"\nUploading to R2: {R2_DEST}")

    for png in sorted(local_dir.glob("*.png")):
        try:
            result = subprocess.run(
                ["rclone", "copy", str(png), R2_DEST],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                url = f"{R2_PUBLIC}/{png.name}"
                print(f"  Uploaded: {url}")
                urls.append(url)
            else:
                print(f"  FAILED to upload {png.name}: {result.stderr}")
        except Exception as e:
            print(f"  ERROR uploading {png.name}: {e}")

    return urls


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    print("=" * 60)
    print("Mia Character Turnaround V3 Generator")
    print("CRITICAL CHANGE: Sculpted chunky hair volumes")
    print("=" * 60)
    print()
    print("Key changes from V2:")
    print("  - SCULPTED CHUNKY hair (no individual strands)")
    print("  - Brown/dark skin tone")
    print("  - Pink headband (not scrunchie)")
    print("  - Pink t-shirt with white polka dots")
    print("  - Blue jeans (not shorts)")
    print("  - Red sneakers")
    print("  - A-Pose for 3D modeling")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

    # Generate each variation
    results = []
    for i, variation in enumerate(VARIATIONS):
        full_prompt = BASE_PROMPT + "\n\n" + variation["suffix"]
        success = generate_turnaround(full_prompt, variation["name"])
        results.append((variation["name"], success))

        # Rate limiting between requests (8+ seconds per CLAUDE.md)
        if i < len(VARIATIONS) - 1:
            print("\n  Waiting 10 seconds for rate limiting...")
            time.sleep(10)

    # Upload successful results to R2
    print()
    urls = upload_to_r2(OUTPUT_DIR)

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)

    for name, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"  mia_{name}.png: {status}")

    successful = sum(1 for _, s in results if s)
    print(f"\n  Total: {successful}/{len(results)} successful")

    if urls:
        print(f"\nR2 URLs:")
        for url in urls:
            print(f"  {url}")

    # List generated files
    if OUTPUT_DIR.exists():
        print("\nLocal files:")
        for f in sorted(OUTPUT_DIR.glob("*.png")):
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name} ({size_kb:.0f} KB)")

    return 0 if successful > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
