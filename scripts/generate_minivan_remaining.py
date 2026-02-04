#!/usr/bin/env python3
"""
Magic Minivan Concept Art - Remaining Images

Generates the remaining concept art images using Gemini 2.0 Flash with image generation.
"""

import os
import sys
import base64
import argparse
import time
from pathlib import Path
from io import BytesIO

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai package not installed. Run: pip install google-genai")
    sys.exit(1)


# Remaining minivan prompts that need to be generated
REMAINING_PROMPTS = {
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

    "wrecked": """Pixar 3D animation style environment concept art,
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


class GeminiFlashImageGenerator:
    """Generates images using Gemini 2.0 Flash with image generation."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)

    def generate_image(self, prompt: str, output_path: Path) -> bool:
        """Generate an image using Gemini 2.0 Flash with image generation."""
        try:
            print(f"  Generating with gemini-2.0-flash-exp-image-generation...")

            # Use the experimental image generation model
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )

            # Extract the image from the response
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        image_bytes = part.inline_data.data

                        with open(output_path, "wb") as f:
                            f.write(image_bytes)

                        print(f"  Saved: {output_path}")
                        return True

            print(f"  ERROR: No image in response")
            return False

        except Exception as e:
            print(f"  ERROR: {e}")
            return False

    def generate_all(self, dry_run: bool = False) -> dict:
        """Generate all remaining minivan concept art views."""
        results = {}

        print(f"\n{'='*60}")
        print("Generating: REMAINING MINIVAN CONCEPT ART")
        print(f"{'='*60}")

        for view_name, prompt in REMAINING_PROMPTS.items():
            output_path = self.output_dir / f"minivan_{view_name}.png"

            print(f"\n[{view_name}]")
            if dry_run:
                print(f"  Prompt: {prompt[:100]}...")
                print(f"  Would save to: {output_path}")
                results[view_name] = True
            else:
                results[view_name] = self.generate_image(prompt.strip(), output_path)
                # Rate limiting - recommended 8+ seconds
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


def main():
    parser = argparse.ArgumentParser(
        description="Generate remaining minivan concept art using Gemini Flash"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without generating")
    parser.add_argument("--view", "-v", type=str,
                        choices=list(REMAINING_PROMPTS.keys()),
                        help="Generate specific view only")

    args = parser.parse_args()

    output_dir = Path(__file__).parent.parent / "assets" / "props" / "minivan"

    try:
        generator = GeminiFlashImageGenerator(output_dir)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.view:
        prompt = REMAINING_PROMPTS[args.view]
        output_path = output_dir / f"minivan_{args.view}.png"
        print(f"\n[{args.view}]")
        if args.dry_run:
            print(f"  Prompt: {prompt[:100]}...")
            results = {args.view: True}
        else:
            results = {args.view: generator.generate_image(prompt.strip(), output_path)}
    else:
        results = generator.generate_all(dry_run=args.dry_run)

    print_summary(results)

    total_failed = sum(1 for v in results.values() if not v)
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
