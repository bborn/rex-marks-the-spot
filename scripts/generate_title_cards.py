#!/usr/bin/env python3
"""Generate title cards featuring the main characters using Gemini API.

CRITICAL: Title cards must feature OUR actual characters:
- The Bornsztein family (Gabe, Nina, Mia, Leo)
- Jetplane (cute teal dinosaur - NOT generic dinos)
- Ruben (fairy godfather with iridescent wings)
- The magic minivan

NOT generic Jurassic Park dinosaurs. This is a FAMILY movie with SPECIFIC characters.
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
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "branding" / "title-cards"

# Character descriptions for consistency
CHARACTERS = """
MAIN CHARACTERS (must be included):

MIA: 8-year-old girl with warm brown hair in ponytail with turquoise scrunchie,
large expressive brown eyes, wearing purple t-shirt with star graphic,
determined kind expression, Pixar-style

LEO: 5-year-old boy with messy tousled brown hair and cowlick, big innocent brown eyes,
round face with freckles, gap-toothed smile, wearing bright green dinosaur t-shirt,
curious brave expression, adorable younger sibling, Pixar-style

GABE (Dad): Late 30s, short dark brown hair with gray at temples, rectangular glasses,
slight five-o'clock shadow, wearing white dress shirt (sleeves rolled up) with loosened blue tie,
loving protective father, Pixar-style

NINA (Mom): Late 30s, shoulder-length dark brown wavy hair, beautiful hazel-green eyes,
heart-shaped face, wearing elegant burgundy cocktail dress with gold jewelry,
graceful but strong, Pixar-style

RUBEN (Fairy Godfather): Appears 50s, wild unkempt silvery-gray hair, tired blue-gray eyes,
lanky build, GLOWING IRIDESCENT PURPLE-BLUE FAIRY WINGS on his back,
wearing faded purple vest over wrinkled white shirt, carrying slightly dented magic wand,
once-glamorous now washed-up fairy, Pixar-style

JETPLANE (Dinosaur): CUTE adorable dinosaur companion (NOT a realistic dinosaur),
soft TEAL BLUE-GREEN scales, cream-colored belly, orange fluffy neck ruff and tail tuft,
HUGE amber puppy-like eyes, coral-pink floppy ear-frills, round huggable body shape,
short stubby legs with pink toe beans, expressive tail, like a chicken-puppy-lizard hybrid,
designed to be merchandise-ready and iconic, family-friendly creature, Pixar-style

MAGIC MINIVAN: Purple/teal family minivan with magical sparkle trail, can fly,
whimsical design with glowing accents
"""

# Style prefix for Pixar-quality renders
PIXAR_STYLE = """Pixar-quality 3D animated movie poster style, vibrant colors,
professional lighting, warm family-friendly aesthetic, high quality render,
cinematic composition, magical atmosphere with sparkles and glow effects,
movie poster quality, polished final render, NOT a sketch"""

# Title card prompts featuring ALL main characters
TITLE_CARDS = [
    {
        "filename": "title-card-family-adventure-16x9.png",
        "prompt": f"""{PIXAR_STYLE},

Movie poster composition showing ALL these characters together:
{CHARACTERS}

SCENE: The whole BORNSZTEIN FAMILY (Gabe, Nina, Mia, Leo) standing in front of their
purple/teal MAGIC FLYING MINIVAN which hovers behind them with sparkle trail.
JETPLANE the cute teal dinosaur companion stands next to the kids, looking happy.
RUBEN the fairy godfather with his glowing iridescent wings floats above them,
wand in hand casting magical sparkles.

Behind them: a lush prehistoric jungle with magical elements - glowing plants,
colorful butterflies, mystical fog.

The family looks excited and adventurous. Warm golden lighting, magical atmosphere.
Title text space at top: "FAIRY DINOSAUR DATE NIGHT"

16:9 horizontal movie poster aspect ratio, vibrant colors, magical family adventure feel."""
    },
    {
        "filename": "title-card-family-adventure-1x1.png",
        "prompt": f"""{PIXAR_STYLE},

Square movie poster showing ALL these characters together:
{CHARACTERS}

COMPOSITION: The BORNSZTEIN FAMILY (Gabe, Nina, Mia, Leo) grouped together in center.
JETPLANE the cute teal dinosaur is in front, looking up happily at the camera.
RUBEN the fairy godfather with glowing rainbow wings hovers above the family.
The MAGIC MINIVAN flies in the background with sparkle trail.

Magical prehistoric jungle setting with colorful plants and mystical glow.
Family looks excited and united. Warm golden-hour lighting.
Space at top for title "FAIRY DINOSAUR DATE NIGHT"

1:1 square aspect ratio for social media, vibrant colors, magical family adventure."""
    },
    {
        "filename": "title-card-characters-hero-16x9.png",
        "prompt": f"""{PIXAR_STYLE},

Dynamic hero shot movie poster featuring ALL main characters:
{CHARACTERS}

HERO COMPOSITION:
- Center foreground: MIA and LEO (the kids) looking brave and determined
- Behind kids: JETPLANE the cute teal dinosaur, protectively close to them
- Left side: GABE and NINA (parents) looking protective but amazed
- Right side: RUBEN the fairy godfather, wings glowing, wand raised casting magic
- Background: MAGIC MINIVAN flying through a prehistoric sky at sunset

The pose suggests adventure - characters ready for action but warm family connection.
Magical sparkles and glowing effects throughout.
Dramatic but family-friendly lighting.

16:9 horizontal cinematic poster, title space at top for "FAIRY DINOSAUR DATE NIGHT"."""
    },
    {
        "filename": "title-card-characters-hero-1x1.png",
        "prompt": f"""{PIXAR_STYLE},

Square format dynamic hero shot featuring ALL main characters:
{CHARACTERS}

COMPOSITION arranged in circle/group:
- Center: JETPLANE the cute teal dinosaur with huge amber eyes, looking playful
- Around Jetplane: The four BORNSZTEIN family members (Gabe, Nina, Mia, Leo)
- Above: RUBEN flying with his glowing fairy wings spread wide
- Background hint: MAGIC MINIVAN in sky with sparkle trail

Warm magical lighting, prehistoric jungle elements in background.
Everyone looks happy and connected - this is about family and friendship.

1:1 square social media format, magical family movie aesthetic.
Space for title "FAIRY DINOSAUR DATE NIGHT" at top."""
    },
    {
        "filename": "title-card-magical-moment-16x9.png",
        "prompt": f"""{PIXAR_STYLE},

Emotional magical moment movie poster:
{CHARACTERS}

SCENE: Night scene with magical bioluminescent prehistoric jungle.
The BORNSZTEIN FAMILY sits around a glowing campfire.
JETPLANE the cute teal dinosaur is curled up with the kids (Mia and Leo).
RUBEN stands nearby, his fairy wings casting a soft protective glow.
The MAGIC MINIVAN is parked behind them, its headlights creating warm light.

The moment captures family warmth and wonder - they're having an adventure but they're together.
Fireflies and magical sparkles in the air. Stars visible above through jungle canopy.

16:9 widescreen cinematic composition, warm and magical, family movie poster quality.
Title space: "FAIRY DINOSAUR DATE NIGHT"."""
    },
    {
        "filename": "title-card-magical-moment-1x1.png",
        "prompt": f"""{PIXAR_STYLE},

Square format magical night scene:
{CHARACTERS}

INTIMATE MOMENT: Close framing on the family and their magical friends.
MIA and LEO in center, hugging JETPLANE the cute teal dinosaur.
GABE and NINA on either side, looking lovingly at their kids.
RUBEN above/behind, his iridescent wings glowing softly.
Magical fireflies and sparkles fill the frame.

Night lighting with warm bioluminescent glow from plants.
MAGIC MINIVAN suggested in background with its headlights on.

Cozy, warm, family-focused composition. This is a movie about love and adventure.
1:1 square format, magical family movie aesthetic.
Title: "FAIRY DINOSAUR DATE NIGHT"."""
    },
]


def generate_image(prompt: str, filename: str) -> bool:
    """Generate a single image using Gemini 2.0 Flash."""
    output_path = OUTPUT_DIR / filename

    print(f"Generating: {filename}")
    print(f"  Prompt (first 100 chars): {prompt[:100].replace(chr(10), ' ')}...")

    try:
        # Use Gemini 2.0 Flash with native image generation
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
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
                print(f"  ✓ Saved to {output_path}")
                return True

        print(f"  ✗ No image in response")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Generate all title cards featuring main characters."""
    print("=" * 70)
    print("Generating Title Cards - Featuring Main Characters")
    print("=" * 70)
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    print("Characters to include:")
    print("  - Bornsztein Family: Gabe, Nina, Mia, Leo")
    print("  - Jetplane (cute teal dinosaur)")
    print("  - Ruben (fairy godfather)")
    print("  - Magic Minivan")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(TITLE_CARDS)

    for i, card in enumerate(TITLE_CARDS, 1):
        print(f"\n[{i}/{total}] ", end="")
        if generate_image(card["prompt"], card["filename"]):
            success_count += 1

        # Delay between requests to avoid rate limiting (8 seconds as per CLAUDE.md)
        if i < total:
            print("  Waiting 8 seconds before next request...")
            time.sleep(8)

    print("\n" + "=" * 70)
    print(f"Complete: {success_count}/{total} title cards generated")
    print("=" * 70)

    if success_count > 0:
        print(f"\nGenerated images saved to: {OUTPUT_DIR}")
        print("\nCharacters featured in all title cards:")
        print("  ✓ Bornsztein Family (Gabe, Nina, Mia, Leo)")
        print("  ✓ Jetplane (our cute teal dinosaur, NOT generic dinos)")
        print("  ✓ Ruben (fairy godfather with wings)")
        print("  ✓ Magic Minivan")

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
