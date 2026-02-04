#!/usr/bin/env python3
"""
Environment Concept Variation Generator

Generates multiple style variations of key environments for director review.
Creates 3 style variations for each environment:
- Warm/Cozy style
- Dramatic/Cinematic style
- Stylized/Whimsical style

Usage:
    python scripts/generate_environment_variations.py --all
    python scripts/generate_environment_variations.py --env family_home
    python scripts/generate_environment_variations.py --dry-run
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


# Style modifiers for variations
STYLE_VARIATIONS = {
    "warm_cozy": {
        "name": "Warm & Cozy",
        "suffix": "warm_cozy",
        "modifiers": """soft golden hour lighting, warm amber tones,
inviting comfortable atmosphere, gentle shadows, homey feeling,
Pixar 3D animation style, professional animation production quality"""
    },
    "dramatic_cinematic": {
        "name": "Dramatic Cinematic",
        "suffix": "dramatic",
        "modifiers": """dramatic cinematic lighting, high contrast shadows,
epic scale and grandeur, moody atmospheric fog, rim lighting,
Pixar 3D animation style, professional animation production quality"""
    },
    "stylized_whimsical": {
        "name": "Stylized Whimsical",
        "suffix": "whimsical",
        "modifiers": """highly stylized cartoon aesthetic, exaggerated proportions,
playful bright colors, whimsical dreamlike quality, soft rounded shapes,
Pixar 3D animation style with extra stylization, professional animation quality"""
    }
}


# Base environment descriptions (without style modifiers)
ENVIRONMENT_BASES = {
    "family_home": {
        "description": "Family Home Interior",
        "base_prompt": """Family living room interior, cozy suburban home,
comfortable oversized sofa with colorful throw pillows,
family photos on walls, kids' toys scattered on carpet,
dinosaur figurines on shelves, TV in corner,
open floor plan showing glimpse of kitchen,
evening time with warm interior lights on,
storm visible through large windows,
lived-in family atmosphere with personal touches"""
    },
    "magic_minivan": {
        "description": "Magic Minivan Interior",
        "base_prompt": """Family minivan interior from backseat perspective,
kid-friendly chaos with toys and snacks,
children's drawings taped to seat backs,
GPS on dashboard showing strange route,
colorful car seats with sippy cups in holders,
mysterious magical glow beginning to appear,
faint sparkles and fairy dust particles floating,
family vehicle becoming portal to adventure"""
    },
    "jurassic_swamp": {
        "description": "Jurassic Swamp",
        "base_prompt": """Vast Jurassic period swamp landscape,
towering tree ferns and massive cycads,
shallow murky water with prehistoric lily pads,
thick humid mist hanging in the air,
distant smoking volcano on horizon,
pterodactyl silhouettes flying overhead,
giant dragonflies and prehistoric insects,
lush overwhelming prehistoric wilderness,
dangerous but beautiful ancient world"""
    },
    "cave_hideout": {
        "description": "Cave Hideout",
        "base_prompt": """Hidden cave interior serving as secret hideout,
natural rocky walls with interesting formations,
makeshift camp setup with gathered supplies,
small campfire casting flickering warm light,
cave entrance showing glimpse of jungle outside,
cozy shelter contrasting with dangerous world,
kids' belongings arranged as temporary home,
bioluminescent fungi providing subtle glow,
safe refuge feeling despite prehistoric setting"""
    }
}


class VariationGenerator:
    """Generates environment concept variations using Gemini API."""

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

    def generate_variation(
        self,
        env_key: str,
        style_key: str,
        dry_run: bool = False
    ) -> bool:
        """Generate a single environment variation."""
        env = ENVIRONMENT_BASES[env_key]
        style = STYLE_VARIATIONS[style_key]

        # Combine base prompt with style modifiers
        full_prompt = f"{env['base_prompt'].strip()}, {style['modifiers'].strip()}"

        output_path = self.output_dir / env_key / f"{env_key}_{style['suffix']}.png"

        print(f"\n  Style: {style['name']}")

        if dry_run:
            print(f"  Prompt preview: {full_prompt[:100]}...")
            print(f"  Would save to: {output_path}")
            return True
        else:
            return self.generate_image(full_prompt, output_path)

    def generate_environment(self, env_key: str, dry_run: bool = False) -> dict:
        """Generate all style variations for an environment."""
        if env_key not in ENVIRONMENT_BASES:
            print(f"ERROR: Unknown environment: {env_key}")
            return {}

        env = ENVIRONMENT_BASES[env_key]
        results = {}

        print(f"\n{'='*60}")
        print(f"Generating variations: {env['description'].upper()}")
        print(f"{'='*60}")

        for style_key in STYLE_VARIATIONS.keys():
            results[style_key] = self.generate_variation(env_key, style_key, dry_run)
            if not dry_run:
                # Rate limiting for Gemini API
                time.sleep(3)

        return results

    def generate_all(self, dry_run: bool = False) -> dict:
        """Generate all variations for all environments."""
        all_results = {}

        for env_key in ENVIRONMENT_BASES.keys():
            all_results[env_key] = self.generate_environment(env_key, dry_run)

        return all_results


def print_summary(results: dict) -> None:
    """Print generation summary."""
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    total_success = 0
    total_failed = 0

    for env_key, style_results in results.items():
        env_name = ENVIRONMENT_BASES[env_key]["description"]
        success = sum(1 for v in style_results.values() if v)
        failed = sum(1 for v in style_results.values() if not v)
        total_success += success
        total_failed += failed

        status = "SUCCESS" if failed == 0 else "PARTIAL" if success > 0 else "FAILED"
        print(f"  {env_name}: {status} ({success}/{len(style_results)} variations)")

    print("-"*60)
    print(f"  TOTAL: {total_success} succeeded, {total_failed} failed")
    print(f"  Images saved to: assets/environments/concepts/")


def main():
    parser = argparse.ArgumentParser(
        description="Generate environment concept variations for director review"
    )
    parser.add_argument("--all", action="store_true",
                        help="Generate all environment variations")
    parser.add_argument("--env", "-e", type=str,
                        choices=list(ENVIRONMENT_BASES.keys()),
                        help="Generate variations for specific environment")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without generating")
    parser.add_argument("--list", action="store_true",
                        help="List environments and styles")

    args = parser.parse_args()

    if args.list:
        print("\nEnvironments:")
        print("="*60)
        for key, env in ENVIRONMENT_BASES.items():
            print(f"  {key}: {env['description']}")

        print("\nStyle Variations:")
        print("="*60)
        for key, style in STYLE_VARIATIONS.items():
            print(f"  {key}: {style['name']}")
        sys.exit(0)

    if not args.all and not args.env:
        parser.error("Either --all or --env is required")

    output_dir = Path(__file__).parent.parent / "assets" / "environments" / "concepts"

    try:
        generator = VariationGenerator(output_dir)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.all:
        results = generator.generate_all(dry_run=args.dry_run)
    else:
        results = {args.env: generator.generate_environment(args.env, dry_run=args.dry_run)}

    print_summary(results)

    total_failed = sum(sum(1 for v in r.values() if not v) for r in results.values())
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
