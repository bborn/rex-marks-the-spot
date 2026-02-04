#!/usr/bin/env python3
"""
Prehistoric Jungle Background Generation Script

Generates wide establishing shots of the prehistoric jungle for
"Fairy Dinosaur Date Night" using Google's Gemini API with Imagen.

Usage:
    python scripts/generate_jungle_backgrounds.py
    python scripts/generate_jungle_backgrounds.py --dry-run
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


# Prehistoric jungle establishing shots - Pixar-style wide backgrounds
JUNGLE_BACKGROUNDS = {
    "dense_fern_forest": """Pixar 3D animation style wide establishing shot,
dense prehistoric fern forest, towering ancient tree ferns reaching 50 feet tall,
multiple layers of lush green fronds creating cathedral-like canopy,
shafts of golden-green dappled sunlight filtering through dense foliage,
thick carpet of smaller ferns and prehistoric plants on forest floor,
humid misty atmosphere with visible moisture in air,
sense of overwhelming ancient botanical abundance,
warm inviting color palette with deep greens and golden light,
cinematic wide shot composition, professional animation production quality,
family-friendly magical prehistoric forest establishing shot""",

    "misty_swamp": """Pixar 3D animation style wide establishing shot,
atmospheric prehistoric swamp shrouded in ethereal morning mist,
still dark water reflecting ancient trees and sky,
gnarled cypress-like trees with hanging moss and vines,
mist rolling across water surface creating layers of depth,
soft diffused lighting with hints of warm amber sunrise,
lily pads and prehistoric aquatic plants on water,
mysterious but beautiful and inviting atmosphere,
giant dragonflies hovering in misty air,
cinematic wide shot composition, professional animation production quality,
family-friendly magical swamp establishing shot""",

    "ancient_tree_canopy": """Pixar 3D animation style wide establishing shot,
looking up into massive prehistoric tree canopy from below,
enormous ancient tree trunks rising like natural cathedral columns,
intricate pattern of branches and leaves against amber sky,
hanging vines and epiphytic plants decorating every branch,
pterodactyls gliding between the massive trees,
warm golden hour light filtering through leaf gaps,
sense of awe-inspiring vertical scale and ancient majesty,
small colorful prehistoric birds and insects in the canopy,
cinematic wide shot composition looking upward, professional animation production quality,
family-friendly magical forest canopy establishing shot""",

    "clearing_dinosaurs_distance": """Pixar 3D animation style wide establishing shot,
sunlit jungle clearing with gentle herbivore dinosaurs grazing in distance,
open meadow of prehistoric ferns and flowering plants,
friendly brachiosaurus family visible eating from tall trees,
smaller dinosaurs peacefully roaming the clearing,
jungle wall framing the peaceful scene on three sides,
warm golden afternoon sunlight bathing the clearing,
butterflies and dragonflies adding life and movement,
sense of peaceful prehistoric paradise,
cinematic wide establishing shot composition, professional animation production quality,
family-friendly dinosaur scene, gentle and welcoming atmosphere""",

    "river_stepping_stones": """Pixar 3D animation style wide establishing shot,
crystal clear prehistoric river winding through jungle,
natural stepping stones of rounded boulders crossing the water,
colorful fish and aquatic life visible in clear shallows,
lush jungle vegetation on both riverbanks,
small waterfall in background adding movement and sound,
warm sunlight sparkling on water surface,
moss-covered rocks and ferns along the banks,
inviting adventure crossing point for characters,
cinematic wide shot composition, professional animation production quality,
family-friendly river scene perfect for adventure sequence""",

    "volcano_horizon": """Pixar 3D animation style wide establishing shot,
dramatic prehistoric landscape with smoking volcano on distant horizon,
layered jungle valleys leading toward the volcanic mountain,
gentle smoke plume rising from volcano crater,
warm amber sunset sky with dramatic cloud formations,
silhouettes of pterodactyls flying against volcanic backdrop,
foreground jungle framing the epic vista,
sense of prehistoric world scale and grandeur,
beautiful not threatening volcano appearance,
cinematic wide establishing shot composition, professional animation production quality,
family-friendly epic landscape shot""",

    "primordial_dawn": """Pixar 3D animation style wide establishing shot,
prehistoric jungle at magical dawn moment,
soft pink and gold light spreading across misty landscape,
silhouettes of tall fern trees against colorful sunrise sky,
ground mist glowing with warm dawn light,
early morning dew sparkling on every leaf and frond,
peaceful awakening atmosphere with first birds stirring,
long shadows creating depth across the scene,
sense of new day beginning in ancient world,
cinematic wide establishing shot composition, professional animation production quality,
family-friendly magical dawn scene""",

    "bioluminescent_night": """Pixar 3D animation style wide establishing shot,
prehistoric jungle at night with magical bioluminescence,
glowing mushrooms and plants creating soft blue-green light,
fireflies and luminescent insects drifting through darkness,
starry prehistoric sky visible through canopy gaps,
mysterious but beautiful and enchanting atmosphere,
reflections of bioluminescent glow on water and leaves,
sense of wonder and magic in the nighttime jungle,
cool blue and warm amber accent lighting,
cinematic wide establishing shot composition, professional animation production quality,
family-friendly magical night scene, wondrous not scary""",
}


class JungleBackgroundGenerator:
    """Generates prehistoric jungle backgrounds using Google Gemini API."""

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
                    aspect_ratio="16:9",  # Wide establishing shot
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

    def generate_all(self, dry_run: bool = False) -> dict:
        """Generate all prehistoric jungle backgrounds."""
        results = {}

        print("\n" + "=" * 60)
        print("GENERATING PREHISTORIC JUNGLE BACKGROUNDS")
        print("=" * 60)

        for bg_name, prompt in JUNGLE_BACKGROUNDS.items():
            output_path = self.output_dir / f"{bg_name}.png"

            print(f"\n[{bg_name}]")
            if dry_run:
                print(f"  Prompt: {prompt[:100]}...")
                print(f"  Would save to: {output_path}")
                results[bg_name] = True
            else:
                results[bg_name] = self.generate_image(prompt.strip(), output_path)
                # Rate limiting - 8 second delay as per project guidelines
                time.sleep(8)

        return results


def print_summary(results: dict, output_dir: Path) -> None:
    """Print a summary of generation results."""
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)

    success = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for name, result in results.items():
        status = "SUCCESS" if result else "FAILED"
        print(f"  {name}: {status}")

    print("-" * 60)
    print(f"  TOTAL: {success} succeeded, {failed} failed")
    print(f"  Images saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate prehistoric jungle backgrounds using Gemini AI"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without generating")
    parser.add_argument("--list", action="store_true",
                        help="List all backgrounds to be generated")

    args = parser.parse_args()

    if args.list:
        print("\nPrehistoric Jungle Backgrounds:")
        print("=" * 60)
        for name in JUNGLE_BACKGROUNDS.keys():
            print(f"  - {name}")
        print(f"\nTotal: {len(JUNGLE_BACKGROUNDS)} backgrounds")
        sys.exit(0)

    output_dir = Path(__file__).parent.parent / "assets" / "environments" / "jungle"

    try:
        generator = JungleBackgroundGenerator(output_dir)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    results = generator.generate_all(dry_run=args.dry_run)
    print_summary(results, output_dir)

    total_failed = sum(1 for v in results.values() if not v)
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
