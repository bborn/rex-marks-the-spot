#!/usr/bin/env python3
"""
Cave Hideout Environment Art Generation Script

Generates 6-8 images of the cave hideout location for "Fairy Dinosaur Date Night".
Uses Google's Gemini API with Imagen image generation.

Required views:
1. Wide establishing shot
2. Cozy corner with makeshift beds
3. Entrance with jungle visible
4. Bioluminescent mushrooms lighting
5. Campfire area
6. Storage corner with supplies
7. Ancient cave paintings
8. Nighttime moonlit view
"""

import os
import sys
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai package not installed. Run: pip install google-genai")
    sys.exit(1)

# Base style elements for consistency
STYLE_BASE = """Pixar 3D animation style environment concept art,
prehistoric cave hideout, animated movie production quality,
warm inviting atmosphere, family-friendly adventure aesthetic,"""

# Individual views for the cave hideout
CAVE_VIEWS = {
    "establishing_wide": f"""{STYLE_BASE}
wide establishing shot of prehistoric cave hideout interior,
spacious natural cave with curved rock walls and stalactites,
warm campfire at center casting orange glow on rock formations,
bioluminescent cyan and purple mushrooms growing in clusters along walls,
makeshift camp setup with cloth tents and wooden crates,
large cave mouth opening to lush green Jurassic jungle outside,
layered lighting from fire glow and mushroom bioluminescence,
epic scale showing the full living space,
cinematic wide-angle composition""",

    "cozy_beds": f"""{STYLE_BASE}
cozy sleeping corner in prehistoric cave hideout,
makeshift beds made from large fern fronds and soft moss,
colorful woven blankets and cushions,
small glowing bioluminescent mushrooms as nightlights,
cloth canopy overhead for privacy and warmth,
scattered personal belongings - a teddy bear, drawings, small toys,
warm amber light from nearby campfire,
safe and protected feeling despite prehistoric setting,
intimate medium shot composition""",

    "entrance_jungle": f"""{STYLE_BASE}
view from inside cave hideout looking out toward entrance,
massive natural cave opening framing lush Jurassic jungle beyond,
hanging vines and ferns partially obscuring entrance,
golden-green sunlight streaming through foliage,
silhouettes of giant ferns and prehistoric plants visible,
pterodactyl silhouette flying past in distance,
contrast between dark safe cave and bright wild jungle,
sense of wonder and adventure awaiting outside,
dramatic backlit composition""",

    "bioluminescent_mushrooms": f"""{STYLE_BASE}
magical bioluminescent mushroom grove inside cave hideout,
clusters of glowing cyan teal and soft purple mushrooms,
variety of shapes - small fairy-like and large spotted caps,
mushrooms growing on fallen logs rocks and cave walls,
soft ethereal glow reflecting on wet cave surfaces,
tiny glowing spores floating in the air like fireflies,
mushroom light creating paths and patterns on cave floor,
enchanted fairy-tale atmosphere within prehistoric setting,
dreamy soft-focus detail shot""",

    "campfire_area": f"""{STYLE_BASE}
central campfire gathering area in cave hideout,
crackling fire with warm orange and yellow flames,
circle of smooth rocks around the firepit,
carved log benches for sitting together,
cooking setup with pot hanging over fire,
smoke wisping up toward natural chimney crack in ceiling,
warm light dancing on nearby faces of rock formations,
cozy family gathering spot feeling,
inviting warm medium shot""",

    "storage_corner": f"""{STYLE_BASE}
supply storage area in cave hideout corner,
stacked wooden crates and woven baskets,
salvaged items from crashed car - flashlight, first aid kit, snacks,
prehistoric finds - interesting rocks, dinosaur feathers, shells,
improvised shelving made from branches,
small clay water jugs and containers,
organized chaos of survival supplies mixed with treasured finds,
resourceful and inventive camp life,
detailed still-life composition""",

    "cave_paintings": f"""{STYLE_BASE}
ancient mysterious cave paintings on hideout wall,
childlike drawings mixed with genuine prehistoric art,
handprints in red ochre pigment,
drawings of dinosaurs - both cute and realistic styles,
simple family figures holding hands,
map-like markings showing journey paths,
warm firelight illuminating the painted wall,
sense of ancient mystery and modern hope together,
atmospheric detail shot with dramatic lighting""",

    "nighttime_moonlit": f"""{STYLE_BASE}
cave hideout at night with moonlight streaming through entrance,
silvery blue moonbeams mixing with warm ember glow,
sleeping figures in cozy beds visible in shadows,
bioluminescent mushrooms providing soft ambient light,
stars visible through cave mouth opening,
peaceful nocturnal atmosphere,
contrast of cool moonlight and warm remaining firelight,
safe sanctuary feeling during prehistoric night,
moody atmospheric wide shot""",
}


class CaveHideoutGenerator:
    """Generates cave hideout environment art using Google Gemini API."""

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

    def generate_all(self, dry_run: bool = False) -> dict:
        """Generate all cave hideout views."""
        results = {}

        print(f"\n{'='*60}")
        print(f"CAVE HIDEOUT ENVIRONMENT ART GENERATION")
        print(f"{'='*60}")
        print(f"Output directory: {self.output_dir}")
        print(f"Views to generate: {len(CAVE_VIEWS)}")

        for view_name, prompt in CAVE_VIEWS.items():
            output_path = self.output_dir / f"cave_{view_name}.png"

            print(f"\n[{view_name.replace('_', ' ').upper()}]")

            if dry_run:
                print(f"  Prompt preview: {prompt[:100].strip()}...")
                print(f"  Would save to: {output_path}")
                results[view_name] = True
            else:
                results[view_name] = self.generate_image(prompt.strip(), output_path)
                # Rate limiting - wait between requests
                if list(CAVE_VIEWS.keys()).index(view_name) < len(CAVE_VIEWS) - 1:
                    print("  Waiting 8 seconds for rate limit...")
                    time.sleep(8)

        return results


def print_summary(results: dict) -> None:
    """Print a summary of generation results."""
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    success = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for view_name, status in results.items():
        icon = "[OK]" if status else "[FAIL]"
        print(f"  {icon} cave_{view_name}.png")

    print("-"*60)
    print(f"  TOTAL: {success} succeeded, {failed} failed")
    print(f"  Images saved to: assets/environments/cave/")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate cave hideout environment art using Gemini AI"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without generating")

    args = parser.parse_args()

    output_dir = Path(__file__).parent.parent / "assets" / "environments" / "cave"

    try:
        generator = CaveHideoutGenerator(output_dir)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    results = generator.generate_all(dry_run=args.dry_run)
    print_summary(results)

    total_failed = sum(1 for v in results.values() if not v)
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
