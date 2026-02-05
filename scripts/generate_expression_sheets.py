#!/usr/bin/env python3
"""Generate character expression sheets using Gemini API.

Creates expression sheets for all main characters showing emotions:
happy, sad, angry, surprised, scared, determined.
One sheet per character, output to assets/characters/expressions/
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "expressions"

# Common style prefix for Pixar-style character expression sheets
EXPRESSION_STYLE = """Professional character expression sheet, Pixar/Dreamworks 3D animation style,
showing 6 different emotions arranged in a 2x3 or 3x2 grid layout,
each emotion clearly labeled, consistent character design across all expressions,
clean white background, high quality animation concept art,
expressions: HAPPY (big genuine smile), SAD (downcast eyes, droopy),
ANGRY (furrowed brows, intense), SURPRISED (wide eyes, open mouth),
SCARED (fearful, trembling), DETERMINED (focused, jaw set),
professional animation studio quality, character model sheet style"""

# Character definitions with their unique visual descriptions
CHARACTERS = {
    "mia": {
        "name": "Mia",
        "filename": "mia_expression_sheet.png",
        "description": """8-year-old girl protagonist,
warm chestnut brown hair in ponytail with turquoise scrunchie,
large expressive brown eyes, oval face with soft features,
wearing purple t-shirt with star graphic,
determined but kind personality, emotional anchor character"""
    },
    "leo": {
        "name": "Leo",
        "filename": "leo_expression_sheet.png",
        "description": """5-year-old boy,
messy tousled brown hair with cowlick, very large innocent brown eyes,
round face with freckles, gap-toothed smile,
wearing bright green dinosaur t-shirt,
curious and brave little sibling, emotions change fast"""
    },
    "gabe": {
        "name": "Gabe",
        "filename": "gabe_expression_sheet.png",
        "description": """Father character late 30s,
short dark brown hair with gray at temples, rectangular glasses,
warm brown eyes, slight five o'clock shadow, average build,
wearing white dress shirt with sleeves rolled up, loosened blue tie,
workaholic dad learning to be present"""
    },
    "nina": {
        "name": "Nina",
        "filename": "nina_expression_sheet.png",
        "description": """Mother character late 30s,
shoulder-length dark brown hair in elegant waves, beautiful hazel-green eyes,
heart-shaped face with defined cheekbones, warm complexion,
wearing elegant burgundy cocktail dress,
patient and supportive but fierce when needed"""
    },
    "ruben": {
        "name": "Ruben",
        "filename": "ruben_expression_sheet.png",
        "description": """Depressed fairy godfather appears 50s,
silvery gray wild unkempt hair, tired blue-gray eyes with bags underneath,
lanky build with slight hunch,
fairy wings that change with emotion (droopy when sad, extended when heroic),
iridescent purple-blue wings, wearing faded purple vest over wrinkled shirt,
carrying dented magic wand, once-glamorous now washed-up aesthetic"""
    },
    "jetplane": {
        "name": "Jetplane",
        "filename": "jetplane_expression_sheet.png",
        "description": """Adorable dinosaur creature companion,
chicken-puppy-lizard hybrid, soft teal scales, cream-colored belly,
warm orange fluffy neck ruff and tail tuft, HUGE amber puppy eyes,
coral-pink floppy ear-frills that move with emotion,
round huggable body shape, short stubby legs with pink toe beans,
expressive tail, designed to be cute and merchandise-ready"""
    }
}


def generate_expression_sheet(character_key: str, character_info: dict) -> bool:
    """Generate an expression sheet for a single character."""
    output_path = OUTPUT_DIR / character_info["filename"]

    prompt = f"""{EXPRESSION_STYLE},

CHARACTER: {character_info['name']}
{character_info['description']}

Create a 2x3 grid showing this exact character with 6 emotions:
Top row: HAPPY (labeled), SAD (labeled), ANGRY (labeled)
Bottom row: SURPRISED (labeled), SCARED (labeled), DETERMINED (labeled)

Each expression must show the SAME character with consistent features,
only the facial expression and body language changes.
Labels should be clear and readable below each expression.
Professional animation reference quality."""

    print(f"\nGenerating expression sheet for: {character_info['name']}")
    print(f"  Output: {output_path}")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=f"Generate an image: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract and save the image from the response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"  ✓ Saved successfully")
                return True

        print(f"  ✗ No image in response")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Generate expression sheets for all main characters."""
    print("=" * 60)
    print("Generating Character Expression Sheets")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Characters: {', '.join(c['name'] for c in CHARACTERS.values())}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(CHARACTERS)

    for i, (key, info) in enumerate(CHARACTERS.items(), 1):
        print(f"\n[{i}/{total}]", end="")
        if generate_expression_sheet(key, info):
            success_count += 1

        # Delay between requests to avoid rate limiting
        if i < total:
            print("  Waiting before next request...")
            time.sleep(3)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{total} expression sheets generated")
    print("=" * 60)

    if success_count == total:
        print("\nAll expression sheets generated successfully!")
        print(f"Output location: {OUTPUT_DIR}")
    else:
        print(f"\nWarning: {total - success_count} sheets failed to generate")

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
