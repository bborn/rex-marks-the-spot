#!/usr/bin/env python3
"""
Generate family action poses for the Bornsztein family.
Creates 5 dynamic action scenes showing the family in various situations.
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "family" / "action"

# Base style for all images - consistent with project aesthetic
STYLE_BASE = """Pixar-style 3D animated character art, professional animation quality,
family-friendly, warm appealing design, expressive characters,
high quality render, dynamic action pose, cinematic lighting,
suitable for animated film promotional art"""

# Character reference for consistency
CHARACTER_REFS = {
    "gabe": """Gabe (Father, late 30s): Dad-bod build, dark brown hair with hints of gray,
short stubble beard, rectangular glasses, warm brown eyes. Wearing black tuxedo (now torn and disheveled).
NOT a fitness model - normal relatable dad body.""",

    "nina": """Nina (Mother, late 30s/early 40s): Warm, relatable mom with shoulder-length wavy dark brown hair,
striking hazel-green eyes, NORMAL average mom body type (NOT athletic or fit, just normal healthy woman),
soft and approachable appearance, late 30s mom who looks like a real person.
Wearing elegant burgundy/wine cocktail dress (now torn/dirty).""",

    "mia": """Mia (8-year-old daughter, OLDER sister): Brown hair in ponytail with turquoise scrunchie,
big expressive hazel eyes, determined expression, wearing purple star t-shirt and denim shorts.
She is the OLDER of the two kids.""",

    "leo": """Leo (5-year-old son, YOUNGER brother): Messy blonde/light brown hair, big round innocent blue eyes,
round cherubic face, wearing green dinosaur pajamas, small for his age.
He is the YOUNGER of the two kids.""",
}

# CRITICAL: The family has exactly 4 members - NO MORE, NO LESS
FAMILY_COUNT_REMINDER = """CRITICAL: This family has EXACTLY 4 members:
1. Gabe (dad)
2. Nina (mom)
3. Mia (8-year-old daughter - OLDER child)
4. Leo (5-year-old son - YOUNGER child)
DO NOT add any extra people. There are only TWO children, not three."""

# The 5 action poses to generate
ACTION_POSES = [
    {
        "filename": "gabe_protective_stance.png",
        "title": "Gabe Protective Stance",
        "prompt": f"""Full body action pose. {CHARACTER_REFS['gabe']}

Scene: Gabe standing in a protective father stance, arms spread wide shielding his family behind him.
His tuxedo is visibly torn - jacket ripped at the shoulder, shirt untucked with dirt marks, bow tie loose.
Expression: fierce determination mixed with fear, jaw set, eyebrows furrowed.
Dynamic pose: weight forward on balls of feet, ready to defend.
Background: simple gradient suggesting danger approaching, dramatic lighting from front.
Show his glasses slightly askew but staying on."""
    },
    {
        "filename": "nina_fierce_mamabear.png",
        "title": "Nina Fierce Mama-Bear",
        "prompt": f"""Full body action pose. {CHARACTER_REFS['nina']}

Scene: Nina in fierce protective mama-bear stance, standing defensively.
Her burgundy cocktail dress is torn at the hem, heels kicked off (barefoot), hair wild and loose.
Expression: intense protective fury, eyes blazing with maternal fire.
Arms out to sides in protective stance.
Body type: NORMAL average mom body, NOT athletic or slim - warm, soft, relatable appearance.
She is late 30s/early 40s with a normal healthy woman's body, not a fitness model.
Background: simple gradient, dramatic lighting.
Shows maternal strength through fierce expression, not through athletic physique."""
    },
    {
        "filename": "mia_leo_running_together.png",
        "title": "Mia and Leo Running Together",
        "prompt": f"""Two characters running together. {CHARACTER_REFS['mia']} {CHARACTER_REFS['leo']}

Scene: Mia holding Leo's hand, pulling him along as they run to safety.
Leo clutches a small stuffed dinosaur in his other hand, looking scared but trusting his sister.
Mia looks back over her shoulder protectively while leading the way forward.
Dynamic running poses: Mia confident and determined, Leo's shorter legs working hard to keep up.
Her ponytail flying behind her, his pajamas slightly oversized making running harder.
Background: motion blur suggesting speed, warm lighting.
Shows sibling bond and Mia's protective older sister nature."""
    },
    {
        "filename": "family_huddled_scared.png",
        "title": "Whole Family Huddled Scared",
        "prompt": f"""Family group pose with EXACTLY 4 people - no more, no less.
{FAMILY_COUNT_REMINDER}

{CHARACTER_REFS['gabe']} {CHARACTER_REFS['nina']} {CHARACTER_REFS['mia']} {CHARACTER_REFS['leo']}

Scene: EXACTLY four family members (dad Gabe, mom Nina, daughter Mia, son Leo) huddled together in fear.
Gabe and Nina (parents) on the outside creating a protective shell around their TWO children.
Only TWO kids: Mia (8, girl with ponytail, purple star shirt) and Leo (5, blonde boy in green dino pajamas).
Leo hiding his face in Mia's shoulder, Mia holding him tight.
Parents' hands interlinked behind the kids.
Nina should have a NORMAL mom body type - soft, warm, relatable - NOT athletic.
All looking in the same direction at something frightening.
Background: dark shadows, small light source on the family.
IMPORTANT: Only 4 people total - 2 adults and 2 children."""
    },
    {
        "filename": "family_celebrating_relieved.png",
        "title": "Family Celebrating and Relieved",
        "prompt": f"""Family group pose with EXACTLY 4 people - no more, no less.
{FAMILY_COUNT_REMINDER}

{CHARACTER_REFS['gabe']} {CHARACTER_REFS['nina']} {CHARACTER_REFS['mia']} {CHARACTER_REFS['leo']}

Scene: EXACTLY four family members celebrating joyfully after surviving their adventure.
The four people are: Gabe (dad with glasses, tuxedo), Nina (mom with dark hair, burgundy dress),
Mia (8-year-old girl, ponytail, purple star shirt), and Leo (5-year-old boy, blonde, green dino pajamas).
ONLY TWO CHILDREN - Mia and Leo. There is no third child.
Gabe lifting Leo up high, both laughing.
Nina embracing Mia, both with tears of relief and smiles.
Nina has a NORMAL average mom body - soft, warm, approachable - NOT athletic or slim.
All in battle-worn clothes but glowing with happiness.
Background: warm golden light.
CRITICAL: Count the people - there must be exactly 4: 2 parents + 2 kids."""
    },
]


def generate_action_pose(pose: dict) -> bool:
    """Generate a single action pose image."""
    output_path = OUTPUT_DIR / pose["filename"]

    if output_path.exists():
        print(f"  Skipping {pose['filename']} (exists)")
        return True

    full_prompt = f"""{STYLE_BASE}

{pose['prompt']}

Generate this scene as a single cohesive image with all described characters in the specified poses.
Professional Pixar-quality animation style, emotionally expressive, family-friendly."""

    print(f"Generating: {pose['filename']}")
    print(f"  Title: {pose['title']}")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=f"Generate an image: {full_prompt}",
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
    parser = argparse.ArgumentParser(description="Generate family action poses")
    parser.add_argument("--pose", "-p", type=int, choices=range(1, 6),
                        help="Generate specific pose (1-5)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all poses")
    args = parser.parse_args()

    if args.list:
        print("\nFamily Action Poses:")
        print("=" * 60)
        for i, pose in enumerate(ACTION_POSES, 1):
            print(f"  {i}. {pose['title']} -> {pose['filename']}")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.pose:
        poses = [ACTION_POSES[args.pose - 1]]
    else:
        poses = ACTION_POSES

    total = len(poses)
    success = 0

    print(f"\n{'=' * 60}")
    print("Generating Family Action Poses")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}\n")

    for pose in poses:
        if generate_action_pose(pose):
            success += 1
        if pose != poses[-1]:  # Don't wait after last image
            print("  Waiting 8 seconds for rate limit...")
            time.sleep(8)

    print(f"\n{'=' * 60}")
    print(f"Complete: {success}/{total} images generated")
    print(f"{'=' * 60}")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
