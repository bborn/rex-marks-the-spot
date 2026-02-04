#!/usr/bin/env python3
"""
Fix family action poses based on PR #90 review feedback:
1. Regenerate gabe_protective_stance as a SINGLE pose (not multi-angle sheet)
2. Fix Nina to wear torn BLACK COCKTAIL DRESS (not primitive clothing)
3. Make Leo look younger (4-5 years old, not 6-7)
4. Add a family group shot with all 4 members together
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
suitable for animated film promotional art.

IMPORTANT: Generate ONE single image with ONE view/angle only.
Do NOT create a reference sheet or multiple angles.
Just ONE cohesive scene."""

# Character reference for consistency
CHARACTER_REFS = {
    "gabe": """Gabe (Father, late 30s): Athletic dad-bod build, 6 feet tall, dark brown hair with gray at temples,
short stubble beard, rectangular glasses with thin dark frames, warm brown eyes.
Wearing BLACK TUXEDO with white dress shirt - now torn and disheveled from adventure.""",

    "nina": """Nina (Mother, late 30s): Elegant and warm, 5'7", shoulder-length wavy dark brown hair (was in updo, now loose and wild),
striking hazel-green eyes, fit athletic build.
CRITICALLY IMPORTANT: Wearing an elegant knee-length BLACK COCKTAIL DRESS that is now torn at the hem and dirty.
She is BAREFOOT (kicked off her heels). The dress is BLACK, sophisticated, like evening wear - NOT primitive or cave-woman style.""",

    "mia": """Mia (8-year-old daughter): Brown hair in ponytail with turquoise scrunchie,
big expressive hazel eyes, determined expression, wearing purple star t-shirt and denim shorts.
She is 8 years old, reaches about waist-height on adults.""",

    "leo": """Leo (4-5 year old son): VERY YOUNG CHILD - toddler proportions with large head relative to body.
Messy light brown/blonde hair with cowlick, big round innocent brown eyes, round cherubic face with full cheeks,
freckles across nose, gap-toothed smile (missing front tooth).
Wearing green dinosaur pajamas. He is SMALL - only reaches adult's knee height.
He should look like a PRESCHOOLER, not a school-age child. Chubby toddler cheeks, short stubby limbs.""",
}

# Fixed action poses
FIXED_POSES = [
    {
        "filename": "gabe_protective_stance.png",
        "title": "Gabe Protective Stance (FIXED - Single Pose)",
        "prompt": f"""SINGLE CHARACTER, SINGLE POSE, ONE VIEW ONLY.

{CHARACTER_REFS['gabe']}

Scene: Gabe standing alone in a protective father stance.
His arms are spread wide as if shielding his family behind him (family not visible, just him).
His black tuxedo is visibly torn - jacket ripped at the shoulder, white shirt untucked with dirt marks, bow tie loose and hanging.
Expression: fierce determination mixed with fear, jaw set, eyebrows furrowed protectively.
Dynamic pose: weight forward on balls of feet, knees slightly bent, ready to defend.
Background: simple dark gradient suggesting danger, dramatic front lighting on his face.
His rectangular glasses are slightly askew but staying on his face.

THIS IS A SINGLE CHARACTER PORTRAIT - just Gabe, one pose, one angle. NOT a reference sheet."""
    },
    {
        "filename": "nina_fierce_mamabear.png",
        "title": "Nina Fierce Mama-Bear (FIXED - Black Dress)",
        "prompt": f"""SINGLE CHARACTER, SINGLE POSE, ONE VIEW ONLY.

{CHARACTER_REFS['nina']}

Scene: Nina alone in a fierce protective mama-bear stance, her body coiled and ready to strike.
She is wearing an ELEGANT BLACK COCKTAIL DRESS - sophisticated evening wear that is now torn at the hem and dirty from adventure.
The dress is BLACK (not brown, not primitive, not cave-woman style) - it's a classy knee-length cocktail dress, the kind you'd wear to a fancy gala.
She has kicked off her heels and is BAREFOOT.
Her dark hair was in an elegant updo but is now wild and loose around her shoulders.
Expression: intense protective fury, hazel-green eyes blazing with maternal fire.
One hand raised in a "stop" gesture, other arm pulled back ready to strike.
Dynamic pose: low athletic crouch, like a tiger ready to pounce.
Background: simple gradient, dramatic side lighting emphasizing her fierce silhouette.
Shows both elegance and primal protective power - a mom who will destroy anything threatening her kids.

THIS IS A SINGLE CHARACTER PORTRAIT - just Nina, one pose, one angle."""
    },
    {
        "filename": "mia_leo_running_together.png",
        "title": "Mia and Leo Running Together (FIXED - Leo Younger)",
        "prompt": f"""TWO CHARACTERS running together, SINGLE SCENE, ONE VIEW.

{CHARACTER_REFS['mia']}

{CHARACTER_REFS['leo']}

Scene: Big sister Mia (8 years old) holding the hand of her VERY YOUNG little brother Leo (4-5 years old).
Mia is pulling Leo along as they run to safety together.

IMPORTANT: Leo must look like a PRESCHOOLER/TODDLER - only 4-5 years old:
- Large head relative to small body (toddler proportions)
- Chubby round cheeks
- Short stubby arms and legs
- Much smaller than Mia - his head only reaches her shoulder
- Baby face with big innocent eyes
- His green dinosaur pajamas are slightly oversized, making running harder

Leo clutches a small stuffed dinosaur toy in his free hand, looking scared but trusting his big sister.
Mia looks back over her shoulder protectively while leading the way forward, determined expression.
Dynamic running poses: Mia confident and leading, Leo's much shorter toddler legs working hard to keep up.
Her ponytail flying behind her.
Background: motion blur suggesting speed, warm lighting.
Shows the protective sibling bond - brave big sister helping her baby brother.

ONE SCENE, ONE ANGLE - not a reference sheet."""
    },
    {
        "filename": "family_group_action.png",
        "title": "Family Group Action Shot (NEW)",
        "prompt": f"""FOUR CHARACTERS in ONE cohesive action scene.

{CHARACTER_REFS['gabe']}
{CHARACTER_REFS['nina']}
{CHARACTER_REFS['mia']}
{CHARACTER_REFS['leo']}

Scene: The entire Bornsztein family of four in a dynamic action pose together.
They are running/moving together as a unit through danger.

Composition (left to right or grouped):
- Gabe on one side in his torn black tuxedo, one arm protectively around the family
- Nina on the other side in her torn black cocktail dress (barefoot), also protective
- Mia (8yo) in the middle-front, holding Leo's hand
- Leo (4-5yo toddler) being protected by everyone, clutching his stuffed dinosaur

All four are in motion - running or moving urgently together.
Parents creating a protective shell around the two kids.
Everyone's clothes show battle damage from their adventure.
Expressions: determined, scared but united, protecting each other.

IMPORTANT: Leo (the youngest) must look like a 4-5 year old TODDLER - much smaller than his 8-year-old sister,
with chubby cheeks and toddler proportions.

Background: Simple gradient suggesting jungle/danger behind them, dramatic lighting.
This shows the family unit - four people who will protect each other no matter what.

SINGLE SCENE showing all four family members together in action."""
    },
]


def generate_fixed_pose(pose: dict, force: bool = False) -> bool:
    """Generate a single fixed action pose image."""
    output_path = OUTPUT_DIR / pose["filename"]

    if output_path.exists() and not force:
        print(f"  Skipping {pose['filename']} (exists, use --force to regenerate)")
        return True

    full_prompt = f"""{STYLE_BASE}

{pose['prompt']}

Generate this as a SINGLE cohesive image. Professional Pixar-quality 3D animation style.
Do NOT create multiple views or a reference sheet - just ONE scene, ONE angle."""

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
    parser = argparse.ArgumentParser(description="Fix family action poses per PR #90 feedback")
    parser.add_argument("--pose", "-p", type=int, choices=range(1, 5),
                        help="Generate specific pose (1=Gabe, 2=Nina, 3=Mia+Leo, 4=Family Group)")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Force regenerate even if file exists")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all poses to fix")
    args = parser.parse_args()

    if args.list:
        print("\nFixed Family Action Poses (PR #90 feedback):")
        print("=" * 60)
        for i, pose in enumerate(FIXED_POSES, 1):
            print(f"  {i}. {pose['title']}")
            print(f"     -> {pose['filename']}")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.pose:
        poses = [FIXED_POSES[args.pose - 1]]
    else:
        poses = FIXED_POSES

    total = len(poses)
    success = 0

    print(f"\n{'=' * 60}")
    print("Fixing Family Action Poses (PR #90 Review Feedback)")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}\n")

    for pose in poses:
        if generate_fixed_pose(pose, force=args.force):
            success += 1
        if pose != poses[-1]:  # Don't wait after last image
            print("  Waiting 10 seconds for rate limit...")
            time.sleep(10)

    print(f"\n{'=' * 60}")
    print(f"Complete: {success}/{total} images generated")
    print(f"{'=' * 60}")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
