#!/usr/bin/env python3
"""
Minivan Concept Art Generation Script

Generates NORMAL family minivan concept art for "Fairy Dinosaur Date Night".
The magic minivan is a REGULAR vehicle - NOT a Cars-movie style vehicle with a face.

CRITICAL: The minivan must NOT have:
- Eyes for headlights
- A mouth-like grille
- Any anthropomorphic features
- Any sentient car characteristics

The magic comes from what the minivan DOES (time travel), not what it looks like.

Usage:
    python scripts/generate_minivan_concept_art.py --all
    python scripts/generate_minivan_concept_art.py --view exterior_front
    python scripts/generate_minivan_concept_art.py --dry-run
"""

import os
import sys
import argparse
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai package not installed. Run: pip install google-genai")
    sys.exit(1)


# Base style description that EXPLICITLY excludes anthropomorphic features
BASE_STYLE = """
Pixar 3D animation style, high quality render, professional animation production quality.
IMPORTANT: This is a NORMAL REALISTIC VEHICLE design.
DO NOT include any anthropomorphic features like:
- Eyes (the headlights are just headlights, not eyes)
- Mouths or expressions on the grille
- Any face-like features
- Any sentient or living vehicle characteristics
This is NOT a Cars movie style vehicle. It is a standard modern family minivan.
"""

# Minivan-specific prompts - emphasizing normal vehicle design
MINIVAN_PROMPTS = {
    "exterior_front": f"""
{BASE_STYLE}
Exterior front three-quarter view of a modern silver metallic family minivan,
Toyota Sienna or Honda Odyssey style design,
NORMAL round headlights (not eyes), standard chrome grille (not a mouth),
parked in suburban driveway at golden hour,
clean modern vehicle design, realistic automotive proportions,
slightly worn but well-maintained family vehicle appearance,
subtle dust and fingerprints showing it's a real family car,
warm golden sunset lighting, cinematic composition
""",

    "exterior_side": f"""
{BASE_STYLE}
Side profile view of a modern silver metallic family minivan,
standard minivan silhouette like Toyota Sienna or Honda Odyssey,
sliding rear doors visible, roof rack with cargo box,
normal headlights and taillights (no faces or expressions),
parked on residential street,
family bumper stickers on rear,
late afternoon suburban lighting,
realistic automotive design, not anthropomorphic
""",

    "exterior_rear": f"""
{BASE_STYLE}
Rear three-quarter view of a silver metallic family minivan,
modern minivan design with large rear window and hatchback,
standard taillights (no expressions), normal license plate area,
rear bumper with family vacation stickers,
kids' handprints visible on dusty rear window,
parked in suburban setting,
evening light, warm tones,
realistic vehicle proportions, no face features
""",

    "exterior_night_storm": f"""
{BASE_STYLE}
Exterior view of a silver metallic family minivan driving through a storm at night,
headlights cutting through heavy rain (normal headlights, not eyes),
windshield wipers working, rain streaking across the vehicle,
standard minivan shape visible through the rain and darkness,
lightning illuminating the scene,
dramatic stormy atmosphere,
realistic vehicle design, no anthropomorphic features,
tension and urgency in the scene
""",

    "exterior_magical": f"""
{BASE_STYLE}
Silver metallic family minivan surrounded by magical blue time-warp energy,
the vehicle is a NORMAL minivan (not anthropomorphic, no face),
swirling blue and purple magical vortex surrounding the car,
sparks and energy crackling around the vehicle,
the magic effect is EXTERNAL to the car - the car itself is just a normal vehicle,
contrast between mundane family minivan and extraordinary magical phenomenon,
dramatic lighting from the magical energy,
exciting but the vehicle remains a normal inanimate object
""",

    "exterior_jurassic": f"""
{BASE_STYLE}
Silver metallic family minivan crashed and stuck in prehistoric jungle swamp,
vehicle covered in mud, vines growing over hood,
cracked windshield, wheels stuck in muddy water,
normal minivan design visible despite damage (no face, no expressions),
surrounded by giant ferns, cycads, and prehistoric vegetation,
misty humid atmosphere with golden-green jungle lighting,
modern technology stranded in ancient world,
the car is an inanimate object, not a character
""",

    "interior_front": f"""
{BASE_STYLE}
Interior view of family minivan from passenger perspective looking at dashboard,
standard minivan interior with modern infotainment screen,
normal steering wheel, regular dashboard gauges,
family clutter: coffee cups, sunglasses, charging cables,
child car seats visible in rearview mirror,
GPS mounted on windshield,
warm natural light streaming through windows,
lived-in family vehicle feeling,
realistic modern minivan interior
""",

    "interior_rear": f"""
{BASE_STYLE}
Interior view of family minivan from rear seats looking forward,
captain's chairs and bench seat visible,
scattered toys, snack crumbs, juice boxes,
kids' drawings and stickers on seat backs,
tablet mounted on headrest for entertainment,
family chaos aesthetic,
warm golden hour light through windows,
realistic minivan interior design
""",
}


class MinivanArtGenerator:
    """Generates minivan concept art using Google Gemini API."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)

    def generate_image(self, prompt: str, output_path: Path) -> bool:
        """Generate a single image using Gemini Flash image generation."""
        try:
            print(f"  Generating image...")

            # Use Gemini 2.0 Flash experimental image generation
            # This uses the generate_content method with image output
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )

            # Extract image from response
            if response.candidates and response.candidates[0].content.parts:
                output_path.parent.mkdir(parents=True, exist_ok=True)

                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        print(f"  Saved: {output_path}")
                        return True

                print(f"  ERROR: No image data in response")
                return False
            else:
                print(f"  ERROR: No images generated")
                return False

        except Exception as e:
            print(f"  ERROR: {e}")
            return False

    def generate_view(self, view_name: str, dry_run: bool = False) -> bool:
        """Generate a specific view of the minivan."""
        if view_name not in MINIVAN_PROMPTS:
            print(f"ERROR: Unknown view: {view_name}")
            return False

        prompt = MINIVAN_PROMPTS[view_name]
        output_path = self.output_dir / f"magic_minivan_{view_name}.png"

        print(f"\n[{view_name}]")
        if dry_run:
            print(f"  Prompt: {prompt.strip()[:100]}...")
            print(f"  Would save to: {output_path}")
            return True
        else:
            return self.generate_image(prompt.strip(), output_path)

    def generate_all(self, dry_run: bool = False) -> dict:
        """Generate all minivan concept art views."""
        results = {}

        print(f"\n{'='*60}")
        print("GENERATING MAGIC MINIVAN CONCEPT ART")
        print("(Normal minivan design - NO anthropomorphic features)")
        print(f"{'='*60}")

        for view_name in MINIVAN_PROMPTS.keys():
            results[view_name] = self.generate_view(view_name, dry_run=dry_run)
            if not dry_run:
                # Rate limiting - Gemini has quota limits
                print("  Waiting for rate limit...")
                time.sleep(8)  # 8 second delay as per CLAUDE.md

        return results


def print_summary(results: dict) -> None:
    """Print a summary of generation results."""
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    success = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for view_name, result in results.items():
        status = "OK" if result else "FAILED"
        print(f"  {view_name}: {status}")

    print("-"*60)
    print(f"  TOTAL: {success} succeeded, {failed} failed")
    print(f"  Images saved to: assets/props/minivan/")


def main():
    parser = argparse.ArgumentParser(
        description="Generate magic minivan concept art (NORMAL vehicle, not Cars-style)"
    )
    parser.add_argument("--all", action="store_true", help="Generate all views")
    parser.add_argument("--view", "-v", type=str,
                        choices=list(MINIVAN_PROMPTS.keys()),
                        help="Generate specific view")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without generating")
    parser.add_argument("--list", action="store_true",
                        help="List all available views")

    args = parser.parse_args()

    if args.list:
        print("\nAvailable Views:")
        print("="*60)
        for view in MINIVAN_PROMPTS.keys():
            print(f"  - {view}")
        sys.exit(0)

    if not args.all and not args.view:
        parser.error("Either --all or --view is required")

    # Output to assets/props/minivan/
    output_dir = Path(__file__).parent.parent / "assets" / "props" / "minivan"

    try:
        generator = MinivanArtGenerator(output_dir)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.all:
        results = generator.generate_all(dry_run=args.dry_run)
    else:
        results = {args.view: generator.generate_view(args.view, dry_run=args.dry_run)}

    print_summary(results)

    total_failed = sum(1 for v in results.values() if not v)
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
