#!/usr/bin/env python3
"""
Environment Concept Art Generation Script

Generates environment concept art for "Fairy Dinosaur Date Night" using
Google's Gemini API with Imagen 3 image generation.

Usage:
    python scripts/generate_environment_art.py --all
    python scripts/generate_environment_art.py --location "bornsztein_home"
    python scripts/generate_environment_art.py --dry-run
"""

import os
import sys
import base64
import argparse
import time
from pathlib import Path
from datetime import datetime

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai package not installed. Run: pip install google-genai")
    sys.exit(1)


# Environment prompts - Pixar-style concept art for each key location
ENVIRONMENT_PROMPTS = {
    "bornsztein_home": {
        "exterior": """Pixar 3D animation style environment concept art,
cozy two-story suburban family home exterior at evening,
warm welcoming appearance with soft amber lights glowing from windows,
storm clouds gathering overhead with lightning in distance,
well-kept front yard with scattered dinosaur toys on the lawn,
family minivan parked in driveway,
autumn leaves on the ground, warm color palette,
professional animation production quality,
establishing shot composition, cinematic lighting""",

        "living_room": """Pixar 3D animation style environment concept art,
cozy family living room interior at evening,
comfortable oversized sofa with colorful throw pillows,
warm amber lamplight creating soft shadows,
TV screen flickering with storm warning,
dinosaur toys scattered across the carpet,
family photos on walls and shelves,
kids' drawings on refrigerator visible in background kitchen,
warm wood floors, lived-in family atmosphere,
storm visible through large windows,
professional animation production quality""",

        "kids_bedroom": """Pixar 3D animation style environment concept art,
shared children's bedroom, two small beds,
dinosaur posters and star decorations on walls,
glowing star nightlight casting soft blue glow,
toy dinosaurs on shelves and scattered on floor,
cozy blankets and stuffed animals,
window showing storm outside,
warm protective atmosphere despite storm,
professional animation production quality""",
    },

    "family_car": {
        "exterior": """Pixar 3D animation style environment concept art,
family minivan exterior, friendly rounded design,
dark teal/blue metallic paint,
slightly worn but well-loved appearance,
parked in suburban driveway at evening,
roof rack with luggage,
bumper stickers visible,
warm interior glow from windows,
professional animation production quality""",

        "interior": """Pixar 3D animation style environment concept art,
family minivan interior view from backseat perspective,
car seats with scattered toys and snack crumbs,
kids' drawings and stickers on seat backs,
GPS mounted on dashboard,
warm family atmosphere,
rain beginning on windshield,
parents silhouettes in front seats,
professional animation production quality""",

        "damaged_jurassic": """Pixar 3D animation style environment concept art,
family minivan crashed in prehistoric jungle,
vehicle covered in mud and vine tangles,
cracked windshield with fern fronds poking through,
wheels stuck in muddy swamp water,
giant prehistoric plants surrounding the wreck,
misty atmosphere with golden-green jungle lighting,
dramatic contrast of modern vehicle in ancient world,
professional animation production quality""",
    },

    "highway_portal": {
        "approach": """Pixar 3D animation style environment concept art,
suburban road at night during intense storm,
car headlights illuminating rain-slicked pavement,
ominous swirling clouds overhead,
lightning strikes in background,
strange blue glow appearing on horizon ahead,
trees bending in wind,
dramatic stormy atmosphere,
professional animation production quality""",

        "portal_opening": """Pixar 3D animation style environment concept art,
magical time portal opening on rainy road,
swirling vortex of brilliant blue and purple energy,
clockwork gears and cosmic symbols visible in the swirl,
lightning converging on the portal center,
family car approaching the phenomenon,
sparks and magical particles flying outward,
dramatic supernatural atmosphere,
professional animation production quality""",
    },

    "time_warp_effect": {
        "tunnel": """Pixar 3D animation style VFX concept art,
time travel tunnel interior,
swirling spiral of blue, purple, and gold energy,
floating clock faces and calendar pages,
streaking starlight and cosmic dust,
family silhouette tumbling through the vortex,
prehistoric creatures visible in temporal echoes,
kaleidoscopic magical atmosphere,
professional animation VFX reference""",

        "small_portal": """Pixar 3D animation style VFX concept art,
small backpack-sized time portal hovering in jungle,
brilliant blue swirling energy contained in small sphere,
clockwork gears visible inside the vortex,
gentle glow illuminating surrounding ferns,
magical sparkles drifting from edges,
mysterious but not threatening appearance,
professional animation production quality""",

        "closing_portal": """Pixar 3D animation style VFX concept art,
time portal collapsing and closing,
blue energy spiraling inward,
fragments of prehistoric and modern imagery mixing,
desperate urgency in the visual,
bright flash at the center,
family silhouettes reaching toward the shrinking opening,
dramatic emotional moment,
professional animation VFX reference""",
    },

    "jurassic_landscape": {
        "swamp_wide": """Pixar 3D animation style environment concept art,
expansive Jurassic period swamp landscape,
towering tree ferns and massive cycads,
humid misty atmosphere with golden-green lighting,
shallow water with prehistoric lily pads,
distant volcano with smoke on horizon,
pterodactyls silhouettes in amber sky,
giant dragonflies hovering over water,
lush overwhelming prehistoric beauty,
professional animation production quality""",

        "dense_jungle": """Pixar 3D animation style environment concept art,
dense Jurassic jungle interior,
massive fern fronds creating dark canopy,
thick vine-covered tree trunks,
shafts of golden light piercing through foliage,
mysterious shadows suggesting hidden creatures,
colorful prehistoric flowers and plants,
humid misty atmosphere,
both beautiful and slightly dangerous feeling,
professional animation production quality""",

        "river_crossing": """Pixar 3D animation style environment concept art,
prehistoric river winding through jungle,
clear water showing fish and aquatic life,
fallen massive log forming natural bridge,
rocky banks with interesting geological formations,
giant dragonflies and prehistoric insects,
golden hour lighting reflecting on water,
peaceful but wild prehistoric beauty,
professional animation production quality""",

        "canyon_vista": """Pixar 3D animation style environment concept art,
dramatic Jurassic canyon overlook,
vast prehistoric landscape visible below,
layered rock formations in warm earth tones,
distant herds of herbivore dinosaurs grazing,
smoking volcano on far horizon,
pterodactyl flock flying across amber sunset,
epic cinematic scale and grandeur,
professional animation production quality""",
    },

    "dinosaur_nesting_area": {
        "nest_clearing": """Pixar 3D animation style environment concept art,
hidden dinosaur nesting ground in jungle clearing,
large bowl-shaped nests made of branches and ferns,
massive spotted eggs nestled in soft vegetation,
protective parent dinosaur silhouette nearby,
dappled sunlight through jungle canopy,
peaceful sacred atmosphere,
baby dinosaur tracks in soft earth,
professional animation production quality""",

        "hatchery": """Pixar 3D animation style environment concept art,
dinosaur eggs hatching scene environment,
cracked shells revealing tiny baby dinosaurs,
warm nest surrounded by fern walls,
mother dinosaur watching protectively,
soft golden lighting creating warm atmosphere,
scattered eggshell fragments,
heartwarming nurturing scene,
professional animation production quality""",

        "family_moment": """Pixar 3D animation style environment concept art,
dinosaur family gathering area,
adult and baby dinosaurs of various sizes,
gentle interaction between species,
Jetplane-type creature fitting in with dinosaur families,
soft evening light filtering through trees,
peaceful coexistence atmosphere,
warm emotional family-friendly scene,
professional animation production quality""",
    },

    "fairy_godfather_realm": {
        "entrance": """Pixar 3D animation style environment concept art,
magical portal to fairy realm appearing in forest,
shimmering iridescent doorway between two ancient trees,
fairy dust and sparkles drifting through the air,
glimpse of magical world beyond,
soft purple and blue magical glow,
contrast between prehistoric jungle and magical realm,
mysterious and inviting atmosphere,
professional animation production quality""",

        "fairy_glade": """Pixar 3D animation style environment concept art,
whimsical fairy godfather's home environment,
run-down magical cottage in enchanted glade,
oversized mushrooms and glowing flowers,
broken wishing well with magical residue,
scattered magical items and failed experiments,
beautiful but sadly neglected fairy aesthetic,
iridescent butterfly-like creatures,
magical but melancholy atmosphere,
professional animation production quality""",

        "magic_workshop": """Pixar 3D animation style environment concept art,
fairy godfather's cluttered magic workshop interior,
shelves of dusty potion bottles and spell books,
dented wands and broken magical items,
cobwebs on enchanted objects,
once-beautiful stained glass windows,
single shaft of light illuminating dust motes,
magical potential hidden under neglect,
professional animation production quality""",

        "restored_realm": """Pixar 3D animation style environment concept art,
fairy realm restored to magical glory,
brilliant iridescent colors and floating lights,
healthy glowing flowers and magical creatures,
crystalline structures reflecting rainbow light,
fairy godfather's cottage now warm and welcoming,
magical waterfall with sparkling water,
joyful restored magical atmosphere,
professional animation production quality""",
    },
}


class EnvironmentArtGenerator:
    """Generates environment concept art using Google Gemini API."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)

    def generate_image(self, prompt: str, output_path: Path) -> bool:
        """Generate a single image using Gemini Imagen 3."""
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

    def generate_location(self, location: str, dry_run: bool = False) -> dict:
        """Generate all concept art for a specific location."""
        if location not in ENVIRONMENT_PROMPTS:
            print(f"ERROR: Unknown location: {location}")
            return {}

        prompts = ENVIRONMENT_PROMPTS[location]
        results = {}
        location_dir = self.output_dir / location

        print(f"\n{'='*60}")
        print(f"Generating: {location.upper().replace('_', ' ')}")
        print(f"{'='*60}")

        for view_name, prompt in prompts.items():
            output_path = location_dir / f"{location}_{view_name}.png"

            print(f"\n[{view_name}]")
            if dry_run:
                print(f"  Prompt: {prompt[:80]}...")
                print(f"  Would save to: {output_path}")
                results[view_name] = True
            else:
                results[view_name] = self.generate_image(prompt.strip(), output_path)
                # Rate limiting - Gemini has quota limits
                time.sleep(3)

        return results

    def generate_all(self, dry_run: bool = False) -> dict:
        """Generate concept art for all locations."""
        all_results = {}

        for location in ENVIRONMENT_PROMPTS.keys():
            all_results[location] = self.generate_location(location, dry_run=dry_run)

        return all_results


def print_summary(results: dict) -> None:
    """Print a summary of generation results."""
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    total_success = 0
    total_failed = 0

    for location, view_results in results.items():
        success = sum(1 for v in view_results.values() if v)
        failed = sum(1 for v in view_results.values() if not v)
        total_success += success
        total_failed += failed

        status = "SUCCESS" if failed == 0 else "PARTIAL" if success > 0 else "FAILED"
        print(f"  {location}: {status} ({success}/{len(view_results)})")

    print("-"*60)
    print(f"  TOTAL: {total_success} succeeded, {total_failed} failed")
    print(f"  Images saved to: assets/environments/")


def main():
    parser = argparse.ArgumentParser(
        description="Generate environment concept art using Gemini AI"
    )
    parser.add_argument("--all", action="store_true", help="Generate all environments")
    parser.add_argument("--location", "-l", type=str,
                        choices=list(ENVIRONMENT_PROMPTS.keys()),
                        help="Generate specific location")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without generating")
    parser.add_argument("--list", action="store_true",
                        help="List all available locations")

    args = parser.parse_args()

    if args.list:
        print("\nAvailable Locations:")
        print("="*60)
        for loc, views in ENVIRONMENT_PROMPTS.items():
            print(f"\n{loc.upper().replace('_', ' ')}:")
            for view in views.keys():
                print(f"  - {view}")
        sys.exit(0)

    if not args.all and not args.location:
        parser.error("Either --all or --location is required")

    output_dir = Path(__file__).parent.parent / "assets" / "environments"

    try:
        generator = EnvironmentArtGenerator(output_dir)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.all:
        results = generator.generate_all(dry_run=args.dry_run)
    else:
        results = {args.location: generator.generate_location(args.location, dry_run=args.dry_run)}

    print_summary(results)

    total_failed = sum(sum(1 for v in r.values() if not v) for r in results.values())
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
