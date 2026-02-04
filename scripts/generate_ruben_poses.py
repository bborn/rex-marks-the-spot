#!/usr/bin/env python3
"""
Generate Ruben fairy godfather poses for animation reference.
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

OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "ruben" / "poses"

# Base style for Ruben
STYLE_BASE = """Pixar-style 3D animated character design, professional concept art,
full body character pose, clean white/light gray background,
warm appealing design, expressive face, suitable for family animation,
high quality render, character design for animated film"""

# Ruben character description
RUBEN_DESCRIPTION = """Washed-up fairy godfather named Ruben, appears in his 50s but centuries old.
Wild unkempt silvery gray Einstein-like hair going everywhere.
Tired blue-gray eyes with heavy dark bags underneath, long drawn face that was once handsome.
Prominent slightly bulbous nose, perpetual 3-day stubble, world-weary cynical expression.
Wears faded purple moth-eaten vest over wrinkled cream button-down shirt (half-untucked).
Worn baggy blue-gray trousers, scuffed pointed curled-toe fairy shoes.
Has translucent iridescent fairy wings (purple-blue) that droop sadly, slightly tattered edges.
Uses an old MOP as his magic wand - the mop head glows when casting spells.
Key traits: grumpy, sarcastic, secretly caring, comedic, redeems himself.
Think Haymitch Abernathy meets a worn-out fairy tale character."""

# Poses to generate
POSES = [
    {
        "name": "grumpy_with_mop",
        "description": "Standing grumpily, leaning heavily on his mop like a cane, unimpressed and cynical expression, wings drooping down sadly, looking at viewer with tired disdain, classic 'I don't want to be here' body language",
    },
    {
        "name": "casting_spell",
        "description": "Active magic casting pose, holding mop aloft, the mop head GLOWING with bright blue-purple magical energy, swirling magic particles and sparkles around it, eyes focused with concentration, wings slightly perked up, dynamic action pose",
    },
    {
        "name": "surprised_success",
        "description": "Expression of complete surprise and disbelief, eyes wide, eyebrows raised, mouth forming an 'O', looking at his own mop in shock that the magic actually worked, wings popping up involuntarily, 'wait that worked?' moment",
    },
    {
        "name": "defeated_slump",
        "description": "Completely dejected pose, shoulders slumped forward, looking down at ground, wings drooping extra low almost dragging, mop hanging limply at his side, the picture of magical depression and failure",
    },
    {
        "name": "triumphant_heroic",
        "description": "Full heroic transformation moment! Standing tall and proud, mop raised high above head with brilliant magical glow, wings FULLY EXTENDED and glowing with inner light, genuine smile on face, years seem to fall away, the fairy godfather he was meant to be",
    },
    {
        "name": "flying_tattered_wings",
        "description": "Flying pose with tattered but functional wings spread wide, arms out for balance, slightly wobbly uncertain flight, hair and clothes billowing, wings showing wear and tear but still working, comedic 'I can't believe I'm flying' expression",
    },
    {
        "name": "embarrassed_failure",
        "description": "Magic misfire pose, wincing with one eye closed and one peeking open, grimacing, mop sputtering weak sparks and gray smoke instead of real magic, wings trying to fold in and hide, shoulders hunched in embarrassment",
    },
    {
        "name": "reluctant_caring",
        "description": "Fighting his affection, trying to maintain grumpy expression but eyes are softening, slight suppressed smile, standing near but pretending not to care, wings betraying his true emotion by perking up slightly, gruff exterior cracking",
    },
    {
        "name": "protective_stance",
        "description": "Protective pose, wings spread forward like a shield, mop held defensively, eyes wide with genuine fear and determination, jaw tight, standing between danger and those he protects, the reluctant hero awakening",
    },
    {
        "name": "magic_concentration",
        "description": "Intense spell concentration pose, eyes narrowed, one eyebrow raised, tongue slightly sticking out, mop pointed forward with tip beginning to glow, wings twitching with the effort, whole body focused on getting this spell right",
    },
]


def generate_pose(pose: dict) -> bool:
    """Generate a single Ruben pose."""
    filename = f"ruben_{pose['name']}.png"
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        print(f"  Skipping {filename} (exists)")
        return True

    prompt = f"""{STYLE_BASE}

CHARACTER: Ruben the Fairy Godfather
{RUBEN_DESCRIPTION}

THIS POSE: {pose['description']}

Generate a full-body character pose showing this specific action/expression.
The mop is his magic wand. Wings always reflect his emotional state.
Clean background, professional animation concept art quality.
Make it appealing and expressive for an animated family film."""

    print(f"Generating: {filename}")
    print(f"  Pose: {pose['description'][:60]}...")

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
    parser = argparse.ArgumentParser(description="Generate Ruben fairy godfather poses")
    parser.add_argument("--pose", "-p", choices=[p["name"] for p in POSES],
                        help="Generate specific pose only")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all poses")
    parser.add_argument("--delay", "-d", type=int, default=8,
                        help="Delay between generations in seconds (default: 8)")
    args = parser.parse_args()

    if args.list:
        print("\nRuben Poses:")
        print("=" * 60)
        for i, pose in enumerate(POSES, 1):
            print(f"\n{i}. {pose['name']}:")
            print(f"   {pose['description'][:80]}...")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.pose:
        poses_to_generate = [p for p in POSES if p["name"] == args.pose]
    else:
        poses_to_generate = POSES

    total = 0
    success = 0

    print(f"\n{'=' * 60}")
    print(f"Generating {len(poses_to_generate)} Ruben poses")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")

    for pose in poses_to_generate:
        total += 1
        if generate_pose(pose):
            success += 1
        if total < len(poses_to_generate):
            print(f"  Waiting {args.delay}s for rate limit...")
            time.sleep(args.delay)

    print(f"\n{'=' * 60}")
    print(f"Complete: {success}/{total} images generated")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"{'=' * 60}")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
