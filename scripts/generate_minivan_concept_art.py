#!/usr/bin/env python3
"""
Magic Minivan Concept Art Generation Script

Generates concept art for the magic minivan prop from "Fairy Dinosaur Date Night"
using Google's Gemini API with Imagen image generation.

Usage:
    python scripts/generate_minivan_concept_art.py --all
    python scripts/generate_minivan_concept_art.py --view exterior_normal
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


# Minivan concept art prompts - matching the Pixar-style aesthetic of the project
MINIVAN_PROMPTS = {
    "exterior_normal": """Pixar 3D animation style prop concept art,
family minivan exterior view, friendly rounded design,
dark teal-blue metallic paint color, slightly worn but well-loved appearance,
parked in suburban driveway at evening time,
roof rack with small luggage carrier,
fun bumper stickers visible on rear bumper,
child-friendly appearance with rounded edges,
warm amber light glowing from neighborhood,
family-friendly animated film aesthetic,
professional animation production quality, front three-quarter view""",

    "exterior_transformed": """Pixar 3D animation style VFX concept art,
magical family minivan with glowing transformation effect,
dark teal-blue minivan enveloped in swirling blue and purple magical energy,
fairy dust sparkles surrounding the vehicle,
magical runes and clockwork symbols floating around it,
ethereal glow emanating from headlights and windows,
mystical aura pulsing with time-travel magic,
dramatic supernatural atmosphere,
the vehicle appears to be charging up for time travel,
professional animation production quality, dramatic lighting""",

    "interior_front": """Pixar 3D animation style environment concept art,
family minivan interior front seats view from passenger perspective,
comfortable cloth seats in dark gray,
GPS navigation mounted on dashboard with glowing screen,
scattered receipts and coffee cup in cupholder,
fuzzy dice hanging from rearview mirror,
family photos clipped to sun visor,
rain beginning to fall on windshield with wipers visible,
warm interior lighting contrasting with dark stormy sky outside,
lived-in family vehicle atmosphere,
professional animation production quality""",

    "interior_back_kids": """Pixar 3D animation style environment concept art,
family minivan interior view from front looking back at kids' area,
colorful car seats in the middle row - one purple, one teal,
kids' drawings and stickers decorating seat backs,
scattered dinosaur toys on the seats and floor,
spilled goldfish crackers and juice boxes,
backpack with snacks visible,
sippy cups in cupholders,
window shade with cute animal patterns,
cozy messy kids' space in family vehicle,
professional animation production quality""",

    "flying_portal": """Pixar 3D animation style VFX concept art,
family minivan flying through magical time warp portal,
dark teal minivan tumbling through swirling vortex of blue purple and gold energy,
floating clock faces and calendar pages surrounding the vehicle,
streaking starlight and cosmic dust trails,
headlights cutting beams through the magical chaos,
glimpses of prehistoric world visible ahead,
dramatic sense of motion and supernatural travel,
intense bright magical lighting effects,
epic time travel sequence moment,
professional animation VFX quality""",

    "prehistoric_jungle": """Pixar 3D animation style environment concept art,
family minivan crashed in prehistoric jungle swamp,
dark teal minivan covered in mud splatter and tangled vines,
cracked windshield with giant fern fronds pressing against glass,
wheels half-submerged in murky swamp water,
massive prehistoric plants towering around the vehicle,
humid misty atmosphere with golden-green jungle lighting,
tropical Jurassic flora surrounding the modern vehicle,
dramatic contrast of family car in ancient world,
pterodactyl silhouette visible in distant sky,
vehicle damaged but recognizable,
professional animation production quality""",

    "exterior_night_storm": """Pixar 3D animation style environment concept art,
family minivan on dark suburban road during intense storm,
dark teal minivan with headlights cutting through heavy rain,
windshield wipers fighting against downpour,
lightning flash illuminating the wet road surface,
ominous storm clouds swirling overhead,
trees bending in strong winds beside the road,
interior glow showing parents silhouettes in front,
tense dramatic atmosphere before the time warp,
professional animation production quality, cinematic lighting""",

    "minivan_wrecked": """Pixar 3D animation style environment concept art,
family minivan severely damaged in prehistoric setting,
dark teal minivan crushed and mangled,
massive T-Rex footprint dent visible in the roof,
windows shattered, doors hanging off hinges,
nest of branches and sticks built on top by pterodactyls,
completely covered in mud and prehistoric vegetation,
wheels broken, sitting at odd angle in swamp,
golden-green jungle light filtering through giant ferns,
tells the story of what happened to the parents' car,
professional animation production quality""",
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
        """Generate a single image using Gemini Imagen."""
        try:
            print(f"  Generating image...")

            response = self.client.models.generate_images(
                model="imagen-4.0-generate-001",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                )
            )

            if response.generated_images:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image_data = response.generated_images[0].image.image_bytes

                with open(output_path, "wb") as f:
                    f.write(image_data)

                print(f"  Saved: {output_path}")
                return True
            else:
                print(f"  ERROR: No images generated")
                return False

        except Exception as e:
            print(f"  ERROR: {e}")
            return False

    def generate_view(self, view_name: str, dry_run: bool = False) -> bool:
        """Generate concept art for a specific view."""
        if view_name not in MINIVAN_PROMPTS:
            print(f"ERROR: Unknown view: {view_name}")
            return False

        prompt = MINIVAN_PROMPTS[view_name]
        output_path = self.output_dir / f"minivan_{view_name}.png"

        print(f"\n[{view_name}]")
        if dry_run:
            print(f"  Prompt: {prompt[:100]}...")
            print(f"  Would save to: {output_path}")
            return True
        else:
            return self.generate_image(prompt.strip(), output_path)

    def generate_all(self, dry_run: bool = False) -> dict:
        """Generate all minivan concept art views."""
        results = {}

        print(f"\n{'='*60}")
        print("Generating: MAGIC MINIVAN CONCEPT ART")
        print(f"{'='*60}")

        for view_name in MINIVAN_PROMPTS.keys():
            results[view_name] = self.generate_view(view_name, dry_run=dry_run)
            if not dry_run:
                # Rate limiting - Gemini has quota limits (8+ seconds recommended)
                print("  Waiting for rate limit...")
                time.sleep(10)

        return results


def print_summary(results: dict) -> None:
    """Print a summary of generation results."""
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    success = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for view_name, result in results.items():
        status = "SUCCESS" if result else "FAILED"
        print(f"  {view_name}: {status}")

    print("-"*60)
    print(f"  TOTAL: {success} succeeded, {failed} failed")
    print(f"  Images saved to: assets/props/minivan/")


def main():
    parser = argparse.ArgumentParser(
        description="Generate magic minivan concept art using Gemini AI"
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
        print("\nAvailable Minivan Views:")
        print("="*60)
        for view in MINIVAN_PROMPTS.keys():
            print(f"  - {view}")
        sys.exit(0)

    if not args.all and not args.view:
        parser.error("Either --all or --view is required")

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
        if not args.dry_run:
            time.sleep(3)

    print_summary(results)

    total_failed = sum(1 for v in results.values() if not v)
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
