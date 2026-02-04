#!/usr/bin/env python3
"""Generate title card and logo designs for Fairy Dinosaur Date Night.

Creates multiple styles (whimsical, adventure, family-friendly) in both
horizontal (16:9) and square (1:1) formats using Gemini image generation.
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
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "branding"

# Base visual style consistent with storyboards
BASE_STYLE = """Pixar-style 3D animated movie title card, professional film poster quality,
vibrant colors, polished and cinematic, family movie aesthetic"""

# Title card prompts - different styles
TITLE_CARDS = {
    # Whimsical Style - magical, sparkly, fairy-tale feel
    "whimsical": {
        "horizontal": {
            "filename": "title-card-whimsical-horizontal.png",
            "prompt": f"""{BASE_STYLE}, 16:9 horizontal movie title card,
"FAIRY DINOSAUR DATE NIGHT" as magical glowing text in the center,
enchanted forest background with fairy sparkles and magic dust particles,
cute teal dinosaur silhouette and fairy wings integrated into the design,
soft pink and purple magical glow, starry sky above,
whimsical hand-lettered style font with sparkle effects,
dreamy and magical atmosphere, like a Disney fairy tale movie poster"""
        },
        "square": {
            "filename": "title-card-whimsical-square.png",
            "prompt": f"""{BASE_STYLE}, square 1:1 aspect ratio logo design,
"FAIRY DINOSAUR DATE NIGHT" in playful magical lettering,
centered composition for social media,
fairy sparkles and magic swirls around the text,
cute dinosaur and fairy wing motifs integrated,
soft gradient background pink to purple to teal,
enchanting storybook logo feel"""
        }
    },

    # Adventure Style - dynamic, exciting, action-packed
    "adventure": {
        "horizontal": {
            "filename": "title-card-adventure-horizontal.png",
            "prompt": f"""{BASE_STYLE}, 16:9 horizontal movie title card,
"FAIRY DINOSAUR DATE NIGHT" in bold dynamic 3D text,
prehistoric jungle background with lush vegetation,
dramatic lighting with golden sunset rays breaking through,
silhouettes of dinosaurs and a magic minivan,
adventure movie poster style, exciting and epic,
text has metallic gold and emerald green highlights,
sense of wonder and exploration"""
        },
        "square": {
            "filename": "title-card-adventure-square.png",
            "prompt": f"""{BASE_STYLE}, square 1:1 aspect ratio logo design,
"FAIRY DINOSAUR DATE NIGHT" bold adventure-style lettering,
dinosaur footprint and fairy wing combined icon behind text,
jungle green and sunset orange color palette,
dynamic swoosh effects suggesting motion,
adventure badge logo style, exciting and bold"""
        }
    },

    # Family-Friendly Style - warm, inviting, heartwarming
    "family": {
        "horizontal": {
            "filename": "title-card-family-horizontal.png",
            "prompt": f"""{BASE_STYLE}, 16:9 horizontal movie title card,
"FAIRY DINOSAUR DATE NIGHT" in warm friendly rounded font,
cozy living room transforming into magical prehistoric world,
two kids and a cute teal dinosaur creature in foreground,
warm golden lighting suggesting family and home,
hearts and stars subtly integrated into design,
welcoming and heartwarming family movie poster,
like Pixar Coco or Inside Out movie poster warmth"""
        },
        "square": {
            "filename": "title-card-family-square.png",
            "prompt": f"""{BASE_STYLE}, square 1:1 aspect ratio logo design,
"FAIRY DINOSAUR DATE NIGHT" in friendly rounded bubble letters,
cute teal dinosaur mascot hugging the text,
warm sunset gradient background,
family-friendly and inviting design,
soft rounded edges, playful but polished,
perfect for app icon or social media profile"""
        }
    }
}

# Logo-only designs (icon style without full title)
LOGOS = {
    "icon-dinosaur": {
        "filename": "logo-dinosaur-icon.png",
        "prompt": f"""Pixar-style 3D animated character icon, square composition,
cute teal dinosaur creature with big amber puppy eyes,
coral-pink ear frills, orange fluffy neck ruff,
simple clean background for icon use,
adorable mascot character, toyetic design,
high quality render suitable for app icon,
simple and recognizable silhouette"""
    },
    "icon-fairy-dino": {
        "filename": "logo-fairy-dino-combo.png",
        "prompt": f"""Pixar-style logo icon design, square composition,
cute teal dinosaur with small iridescent fairy wings,
magical sparkles around it, simple gradient background,
combination of dinosaur and fairy magic themes,
adorable mascot suitable for branding,
clean memorable icon design"""
    },
    "icon-minivan": {
        "filename": "logo-minivan-icon.png",
        "prompt": f"""Pixar-style 3D animated icon, square composition,
magical glowing minivan with sparkle trail,
flying through starry sky, fairy dust particles,
adventure and magic transportation theme,
simple clean design suitable for icon use,
blue and purple magical color palette"""
    },
    "wordmark-simple": {
        "filename": "logo-wordmark-simple.png",
        "prompt": f"""Clean typographic logo design, horizontal composition,
"FAIRY DINOSAUR DATE NIGHT" text only,
playful but professional animated movie font,
subtle gradient from teal to purple to pink,
tiny fairy wing and dinosaur tail integrated into letters,
white or transparent background,
simple wordmark suitable for various uses"""
    }
}


def generate_image(prompt: str, output_path: Path) -> bool:
    """Generate a single image using Gemini 2.0 Flash."""
    print(f"Generating: {output_path.name}")
    print(f"  Prompt: {prompt[:100]}...")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=f"Generate an image: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract and save the image
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"  ✓ Saved to {output_path}")
                return True

        print(f"  ✗ No image in response")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Generate all title card and logo designs."""
    print("=" * 60)
    print("Generating Title Cards and Logos")
    print("Fairy Dinosaur Date Night")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "title-cards").mkdir(exist_ok=True)
    (OUTPUT_DIR / "logos").mkdir(exist_ok=True)

    success_count = 0
    total = 0

    # Generate title cards
    print("\n--- TITLE CARDS ---")
    for style_name, formats in TITLE_CARDS.items():
        print(f"\n[Style: {style_name.upper()}]")
        for format_name, config in formats.items():
            total += 1
            output_path = OUTPUT_DIR / "title-cards" / config["filename"]
            if generate_image(config["prompt"], output_path):
                success_count += 1
            # Rate limiting - Gemini needs ~8 sec between requests
            time.sleep(8)

    # Generate logos
    print("\n--- LOGOS ---")
    for logo_name, config in LOGOS.items():
        total += 1
        print(f"\n[Logo: {logo_name}]")
        output_path = OUTPUT_DIR / "logos" / config["filename"]
        if generate_image(config["prompt"], output_path):
            success_count += 1
        time.sleep(8)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{total} images generated")
    print("=" * 60)

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
