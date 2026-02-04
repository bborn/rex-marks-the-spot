#!/usr/bin/env python3
"""
Generate cartoon-style minivan images for the family vehicle.
Uses Gemini for Pixar-style renders of an ordinary family minivan.

Requirements:
- Plain cartoon minivan, NO face, NO magic effects, NO glowing
- Toyota Sienna/Honda Odyssey style shape
- Pixar-like animation style rendering
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "props" / "minivan"

# Base style for the minivan - emphasizing it's a NORMAL vehicle in CARTOON style
STYLE_BASE = """DIGITAL ILLUSTRATION style cartoon minivan, hand-painted look.
Render style: Dreamworks/Pixar concept art, NOT a 3D render.
Think digital painting with visible brushstrokes, soft edges, warm saturated colors.
EXAGGERATED PROPORTIONS: chunkier, rounder, friendlier than real cars.
Simplified details - no fine textures, no reflections, no photorealism.
Flat-ish shading with soft gradients, like production design artwork.
Color palette: warm teal/turquoise with cream/beige accents.
This is CONCEPT ART for an animated film, not a car advertisement.
Plain ordinary family minivan - NO face, NO anthropomorphic features,
NO magic effects, NO glowing, NO sparkles. Just a cartoon family car."""

# Minivan views to generate
MINIVAN_VIEWS = {
    "exterior_front_3quarter": {
        "description": """Front 3/4 view of a chunky cartoon minivan.
STYLE: Digital painting concept art, hand-painted look with soft brushstrokes.
Teal/turquoise color, rounded bubble-like proportions, simplified geometry.
NO brand logos, NO realistic details, NO reflections.
Warm cream-colored background, like animation production art.
Cute friendly vehicle design with exaggerated round shapes.""",
    },
    "exterior_side": {
        "description": """Side profile view of a chunky cartoon minivan.
STYLE: Digital painting concept art, hand-painted illustration look.
Teal/turquoise color, rounded bubble-like body, simplified shapes.
Sliding door visible, small roof rails, cute simplified wheels.
NO brand logos, NO realistic details, painterly soft shading.
Warm cream background, animation production design style.""",
    },
    "exterior_rear_3quarter": {
        "description": """Rear 3/4 view of a chunky cartoon minivan.
STYLE: Digital painting concept art, hand-painted illustration.
Teal/turquoise color, rounded cute rear end, simple taillights.
Small luggage on roof rack, cute bumper stickers (stick family).
Soft painterly shading, warm cream background.
Friendly cartoon vehicle design, NO photorealism.""",
    },
    "interior_front": {
        "description": """Cartoon minivan interior, looking forward from back seat.
STYLE: Digital painting, warm cozy illustration style.
Simple cartoon dashboard, chunky steering wheel, soft beige interior.
Kids' crayon drawings on seat backs, colorful sippy cups in holders.
Cheerful scattered snacks and toys, lived-in family car feel.
Warm golden lighting, soft painterly shading, cozy atmosphere.""",
    },
    "interior_back": {
        "description": """Cartoon minivan interior, looking back from front seats.
STYLE: Digital painting, warm cozy illustration style.
Two colorful booster seats (teal and purple), soft rounded shapes.
Kids' drawings taped to seat backs, scattered toys and sippy cups.
Warm afternoon light coming through windows, soft shadows.
Cozy family car interior, cartoon style, inviting and cheerful.""",
    },
    "exterior_driveway": {
        "description": """Cartoon minivan parked in a cozy suburban driveway.
STYLE: Digital painting illustration, warm evening scene.
Teal/turquoise chunky cartoon minivan with luggage on roof.
Stylized cartoon house in background with rounded architecture.
Golden sunset lighting, warm orange sky, soft purple shadows.
Everything has that friendly cartoon look - rounded shapes,
soft edges, painterly textures. A scene from an animated film.""",
    },
}


def generate_minivan_view(view_key: str) -> bool:
    """Generate a single minivan view."""
    view = MINIVAN_VIEWS[view_key]

    filename = f"minivan_{view_key}.png"
    output_path = OUTPUT_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Don't overwrite existing files unless --force is used
    if output_path.exists() and "--force" not in sys.argv:
        print(f"  Skipping {filename} (exists, use --force to regenerate)")
        return True

    prompt = f"""{STYLE_BASE}

VIEW: {view_key.replace('_', ' ').title()}
{view['description']}

Generate a single high-quality image of this ordinary family minivan.
Style should match modern Pixar/Disney animated films.
The vehicle is completely normal - magical things happen INSIDE it during the story,
but the van itself looks like any regular family car."""

    print(f"Generating: {filename}")
    print(f"  View: {view_key}")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=f"Generate an image: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  ✓ Saved: {output_path}")
                return True

        print(f"  ✗ No image in response")
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    print(f"  Response text: {part.text[:200]}")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate cartoon minivan images")
    parser.add_argument("--view", "-v", choices=list(MINIVAN_VIEWS.keys()),
                        help="Generate specific view only")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Regenerate even if files exist")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all available views")
    args = parser.parse_args()

    if args.list:
        print("\nMinivan Views:")
        print("=" * 60)
        for key in MINIVAN_VIEWS.keys():
            print(f"  - {key}")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    views = [args.view] if args.view else list(MINIVAN_VIEWS.keys())

    total = 0
    success = 0

    print(f"\n{'=' * 60}")
    print("Generating Cartoon-Style Minivan Images")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")

    for view_key in views:
        total += 1
        if generate_minivan_view(view_key):
            success += 1
        time.sleep(8)  # Rate limit protection

    print(f"\n{'=' * 60}")
    print(f"Complete: {success}/{total} images generated")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"{'=' * 60}")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
