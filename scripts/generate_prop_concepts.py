#!/usr/bin/env python3
"""
Generate prop concept art variations for "Fairy Dinosaur Date Night".
Uses Gemini for high-quality Pixar-style prop renders.
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "props" / "concepts"

# Base style for all props
STYLE_BASE = """Pixar-style 3D animated prop design, professional concept art,
product design reference sheet style, clean white/light gray background,
appealing design suitable for family animation,
high quality render, prop design for animated film"""

# Prop definitions
PROPS = {
    "magic_minivan": {
        "name": "Magic Minivan",
        "description": """The Bornsztein family's minivan that travels through time-warps.
A regular-looking family minivan (think Honda Odyssey or Toyota Sienna style).
Interior is messy with typical family chaos - toys, snacks, papers.
When magical: glowing blue energy patterns on exterior, slightly ethereal glow.
Key details: child seats in back, dinosaur toy on dashboard, water bottle holders,
crumpled papers, random toys scattered around.
The car gets damaged/crushed during the story by dinosaurs.""",
        "variations": [
            "normal family minivan, parked, slightly messy interior visible through windows, warm evening lighting",
            "minivan with magical blue time-warp energy swirling around it, glowing wheels and headlights",
            "damaged/crashed minivan in jurassic swamp, dented hood, pterodactyl nest on top",
            "interior view showing messy backseat with toys, snacks, child seats, family warmth",
        ]
    },
    "mop_wand": {
        "name": "Ruben's Mop-Wand",
        "description": """Ruben the fairy godfather's magic wand - which is actually a janitor's mop.
A well-worn cleaning mop that has been converted into a magic wand.
The mop handle has old tape wrapped around it (repairs from past mishaps).
The mop head has a magical glow when casting spells (iridescent purple/blue shimmer).
Looks shabby and pathetic, but holds real magic.
Worn wooden handle with dents and scratches, faded color.
Small magical symbols barely visible carved into the handle.""",
        "variations": [
            "dormant mop-wand, worn and shabby, tape-wrapped handle, faded mop head, leaning against wall",
            "mop-wand casting spell, mop head glowing bright iridescent purple-blue, magical sparkles",
            "close-up detail sheet showing handle with magical runes, tape repairs, worn grip",
            "mop-wand floating horizontally with soft magical aura, ready for casting",
        ]
    },
    "stuffed_dino": {
        "name": "Leo's Stuffed Dinosaur",
        "description": """Leo's beloved stuffed dinosaur toy that he carries everywhere.
A well-loved plush brontosaurus/long-neck dinosaur.
Soft green fabric, slightly faded from years of hugging.
One button eye is slightly loose/crooked (adds character).
Patches where it's been repaired by mom.
Small size - about 12 inches long, perfect for a 5-year-old to carry.
Soft, squishy, clearly been through a lot but still huggable.
Think classic Pixar design - simple but emotionally resonant.""",
        "variations": [
            "full view of stuffed dino, well-loved and slightly worn, cute friendly face, soft green plush",
            "close-up showing wear details - loose button eye, repair patches, faded spots",
            "stuffed dino posed as if sleeping, peaceful expression, curled up position",
            "stuffed dino in action pose as if being played with, dynamic cute angle",
        ]
    },
    "family_photo": {
        "name": "Bornsztein Family Photo",
        "description": """A framed family portrait of the Bornsztein family.
Shows all four family members: Gabe (dad), Nina (mom), Mia (9-year-old), Leo (5-year-old).
Warm, loving family photograph, slightly posed but genuine.
In a simple wooden frame suitable for a living room.
The photo represents what the family is fighting to get back to.
Background suggests a professional photo studio (neutral gradient).
Everyone is smiling, dressed nicely but not formal.
Should evoke warmth, love, and what family means.""",
        "variations": [
            "traditional family portrait in wooden frame, warm lighting, genuine smiles, studio background",
            "candid-style family photo in frame, more natural pose, outdoor park setting",
            "close-up of framed photo sitting on fireplace mantle, warm home atmosphere",
            "the same photo but damaged/cracked from adventure, emotionally significant",
        ]
    },
    "fairy_dust_jars": {
        "name": "Fairy Dust Jars",
        "description": """Magical containers holding fairy dust for spells.
Glass jars of various sizes (like old-fashioned apothecary jars).
The fairy dust inside glows softly with different colors (gold, silver, iridescent).
Cork stoppers or crystal lids, some jars have magical seal wax.
Labels with faded magical writing (indecipherable runes).
Some jars are half-empty, some full, some nearly depleted.
Should feel both magical and somewhat mundane/practical.
Think fairy godmother storage meets old laboratory.""",
        "variations": [
            "collection of three fairy dust jars, different sizes, glowing gold and silver dust, cork stoppers",
            "single ornate fairy dust jar, crystal stopper, swirling iridescent dust inside, magical glow",
            "row of fairy dust jars on shelf, some full, some nearly empty, old labels, cozy magical storage",
            "close-up of fairy dust spilling from open jar, sparkles and magical particles floating",
        ]
    },
}


def generate_prop_variation(prop_key: str, variation_idx: int) -> bool:
    """Generate a single prop variation."""
    prop = PROPS[prop_key]
    variation = prop["variations"][variation_idx]

    filename = f"{prop_key}_v{variation_idx + 1}.png"
    output_path = OUTPUT_DIR / prop_key / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"  Skipping {filename} (exists)")
        return True

    prompt = f"""{STYLE_BASE}

PROP: {prop['name']}
{prop['description']}

THIS VARIATION: {variation}

Generate a prop design showing this specific view/state.
Clean background, professional animation concept art quality.
Pixar-style rendering, appealing and suitable for family film."""

    print(f"Generating: {filename}")
    print(f"  Variation: {variation[:50]}...")

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
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate prop concept art")
    parser.add_argument("--prop", "-p", choices=list(PROPS.keys()),
                        help="Generate for specific prop only")
    parser.add_argument("--variation", "-v", type=int,
                        help="Generate specific variation (1-4)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all props and variations")
    args = parser.parse_args()

    if args.list:
        print("\nProps and Variations:")
        print("=" * 60)
        for key, prop in PROPS.items():
            print(f"\n{prop['name']} ({key}):")
            for i, var in enumerate(prop["variations"], 1):
                print(f"  {i}. {var}")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    props = [args.prop] if args.prop else list(PROPS.keys())

    total = 0
    success = 0

    for prop_key in props:
        prop = PROPS[prop_key]
        print(f"\n{'=' * 60}")
        print(f"Prop: {prop['name']}")
        print(f"{'=' * 60}")

        if args.variation:
            variations = [args.variation - 1]
        else:
            variations = range(len(prop["variations"]))

        for var_idx in variations:
            total += 1
            if generate_prop_variation(prop_key, var_idx):
                success += 1
            time.sleep(8)  # Rate limit protection

    print(f"\n{'=' * 60}")
    print(f"Complete: {success}/{total} images generated")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
