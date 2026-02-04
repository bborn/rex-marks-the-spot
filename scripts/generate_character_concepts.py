#!/usr/bin/env python3
"""
Generate character concept art variations for director review.
Uses Gemini for high-quality Pixar-style character renders.
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "concepts"

# Base style for all characters
STYLE_BASE = """Pixar-style 3D animated character design, professional concept art,
full body character turnaround reference sheet style, clean white/light gray background,
warm appealing design, expressive face, suitable for family animation,
high quality render, character design for animated film"""

# Character definitions with CORRECT ages per director
CHARACTERS = {
    "mia": {
        "name": "Mia Bornsztein",
        "description": """9-year-old girl, the responsible older sister.
Brown hair usually in a ponytail, big expressive hazel eyes.
Determined and brave but still clearly a kid.
Wears cozy pajamas at home (maybe with subtle star pattern).
Athletic build for her age, slightly tall.
Carries herself with confidence but shows vulnerability.
Key traits: brave, caring, sometimes bossy, fiercely protective of Leo.""",
        "variations": [
            "confident pose, hands on hips, slight smile",
            "worried expression, looking off to the side, biting lip",
            "determined action pose, running forward",
            "tender moment, kneeling down to comfort someone",
        ]
    },
    "leo": {
        "name": "Leo Bornsztein",
        "description": """4-5 year old boy, Mia's little brother.
Blonde/light brown messy hair, big round innocent blue eyes.
Round cherubic face, small for his age.
ALWAYS in dinosaur pajamas (green with dino prints).
Often carries a stuffed dinosaur or snacks.
Imaginative, sweet, sometimes scared but tries to be brave.
Key traits: innocent, imaginative, loves dinosaurs, easily distracted by wonder.""",
        "variations": [
            "excited pose, arms up, huge smile, holding stuffed dino",
            "scared, hiding behind something, peeking out",
            "wonder and awe, mouth open, looking up at something amazing",
            "sleepy, rubbing eyes, dragging stuffed dinosaur",
        ]
    },
    "gabe": {
        "name": "Gabe Bornsztein",
        "description": """Late 30s/early 40s father, athletic dad-bod build.
Dark brown hair with hints of gray at temples, short beard/stubble.
Rectangular glasses, warm brown eyes.
Starts in a black tuxedo (date night) that gets progressively destroyed.
Protective, sometimes impatient, deeply loves his family.
Key traits: protective, practical, dry humor, secretly scared but hides it.""",
        "variations": [
            "formal tuxedo, adjusting cufflinks, slight nervous smile",
            "disheveled, torn tuxedo, protective stance",
            "tender dad moment, crouching down, arms open",
            "determined/serious, rolling up sleeves, ready for action",
        ]
    },
    "nina": {
        "name": "Nina Bornsztein",
        "description": """Late 30s mother, warm and elegant.
Shoulder-length wavy dark brown hair, striking hazel-green eyes.
Starts in elegant black cocktail dress (date night), progressively damaged.
Athletic and capable, not a damsel.
The emotional heart of the family, but also fierce when protecting her kids.
Key traits: warm, brave, resourceful, fierce mama-bear when needed.""",
        "variations": [
            "elegant dress, putting on earring, soft smile",
            "action pose, hiking up dress to run, determined",
            "emotional, hand over heart, tears in eyes",
            "protective stance, arms out, shielding someone",
        ]
    },
    "ruben": {
        "name": "Ruben the Fairy Godfather",
        "description": """Washed-up fairy godfather, looks like a magical janitor.
Wild gray Einstein-like hair, tired baggy eyes with dark circles.
Wears faded blue janitor coveralls with magic symbols barely visible.
Droopy, slightly tattered iridescent wings (like a moth's).
Uses a mop as his magic wand (the mop head glows when casting).
Grumpy exterior but heart of gold. Hasn't had a successful wish in decades.
Key traits: grumpy, sarcastic, secretly caring, comedic, redeems himself.""",
        "variations": [
            "grumpy, leaning on mop, unimpressed expression",
            "surprised, wings perking up, mop glowing",
            "defeated slump, wings drooping, looking at failed spell",
            "triumphant moment, mop raised, wings spread, genuine smile",
        ]
    },
    "jetplane": {
        "name": "Jetplane the Dinosaur",
        "description": """Small friendly dinosaur, about the size of a large dog.
Bright teal/turquoise body with purple and pink accents.
Big expressive yellow eyes, always looks happy and curious.
Short stubby legs, long neck, small wings (can't really fly).
Special ability: farts rainbow-colored clouds when scared or excited.
Think Stitch meets a baby brontosaurus, irresistibly cute.
Key traits: loyal, playful, accidentally causes chaos, pure comic relief.""",
        "variations": [
            "happy bouncing pose, tongue out, tail wagging",
            "scared, rainbow cloud behind, embarrassed expression",
            "curious, head tilted, sniffing something",
            "protective, small but fierce, standing guard",
        ]
    },
}


def generate_character_variation(character_key: str, variation_idx: int) -> bool:
    """Generate a single character variation."""
    char = CHARACTERS[character_key]
    variation = char["variations"][variation_idx]

    filename = f"{character_key}_v{variation_idx + 1}.png"
    output_path = OUTPUT_DIR / character_key / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"  Skipping {filename} (exists)")
        return True

    prompt = f"""{STYLE_BASE}

CHARACTER: {char['name']}
{char['description']}

THIS VARIATION: {variation}

Generate a full-body character design showing this specific pose/expression.
Clean background, professional animation concept art quality."""

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
    parser = argparse.ArgumentParser(description="Generate character concept art")
    parser.add_argument("--character", "-c", choices=list(CHARACTERS.keys()),
                        help="Generate for specific character only")
    parser.add_argument("--variation", "-v", type=int,
                        help="Generate specific variation (1-4)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all characters and variations")
    args = parser.parse_args()

    if args.list:
        print("\nCharacters and Variations:")
        print("=" * 60)
        for key, char in CHARACTERS.items():
            print(f"\n{char['name']} ({key}):")
            for i, var in enumerate(char["variations"], 1):
                print(f"  {i}. {var}")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    characters = [args.character] if args.character else list(CHARACTERS.keys())

    total = 0
    success = 0

    for char_key in characters:
        char = CHARACTERS[char_key]
        print(f"\n{'=' * 60}")
        print(f"Character: {char['name']}")
        print(f"{'=' * 60}")

        if args.variation:
            variations = [args.variation - 1]
        else:
            variations = range(len(char["variations"]))

        for var_idx in variations:
            total += 1
            if generate_character_variation(char_key, var_idx):
                success += 1
            time.sleep(8)  # Rate limit protection

    print(f"\n{'=' * 60}")
    print(f"Complete: {success}/{total} images generated")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
