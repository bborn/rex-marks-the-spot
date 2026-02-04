#!/usr/bin/env python3
"""
Generate CORRECTED family action poses for Gabe and Nina.

CRITICAL: These must show NORMAL TIRED PARENTS, not fitness models.

Gabe: Normal dad body, slightly soft around the middle, desk worker build
Nina: Normal mom body, warm and approachable, relatable working mom
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "family" / "action-poses"

# Base style for all images
STYLE_BASE = """Pixar-style 3D animated character design, professional concept art,
warm appealing design, expressive faces, suitable for family animation,
high quality render, character design for animated film,
REALISTIC body proportions for adults in their early 40s - NOT athletic, NOT muscular,
normal everyday people body types"""

# CORRECTED character descriptions per director feedback
GABE_DESCRIPTION = """GABE - Father character, early 40s suburban dad

CRITICAL PHYSICAL DETAILS (must follow exactly):
- Age: Early 40s
- Build: NORMAL DAD BODY - slightly soft around the middle, NOT muscular or ripped at all
- Has a bit of a belly/paunch from sitting at desk all day
- NOT athletic, NOT fit, NOT a gym-goer
- Think: finance guy who sits at a computer 10 hours a day
- Face: Tired, stressed expression, visible fatigue
- Wears rectangular GLASSES
- Hair: Thinning or receding hairline, short brown hair with gray at temples
- Facial hair: Short beard/stubble, unkempt
- Style: Distracted workaholic dad
- NEVER show him as muscular, ripped, or athletic
- Should look like he hasn't exercised in years
- Average height, soft body, desk worker physique

Tonight's outfit: Black tuxedo (for gala date night) - but doesn't fit perfectly
because he's gained weight since buying it"""

NINA_DESCRIPTION = """NINA - Mother character, late 30s to early 40s mom

CRITICAL PHYSICAL DETAILS (must follow exactly):
- Age: Late 30s to early 40s
- Build: NORMAL MOM BODY - warm, approachable, NOT a model or fitness influencer
- Average build, not slim, not curvy in a glamorous way
- Realistic proportions for a working mom
- NOT sexy, NOT glamorous, NOT hourglass figure
- Think: Real working mom who handles everything, slightly frazzled
- Face: Patient but tired, warm genuine smile, laugh lines
- Hair: Dark brown, simple practical style (shoulder length)
- Eyes: Warm hazel-green, kind but exhausted
- Style: The household manager, practical, relatable
- Should look like she's been managing kids all day
- Comfortable in her own skin but clearly tired
- NOT a magazine model, NOT a fitness influencer

Tonight's outfit: Burgundy/wine colored cocktail dress (for gala) - elegant but modest,
practical mom style, not revealing"""

# Family action poses to generate
FAMILY_POSES = [
    {
        "filename": "gabe_nina_getting_ready_gala",
        "description": """Gabe and Nina getting ready for their gala date night.

        SCENE: Bedroom/bathroom doorway moment

        GABE: Standing in ill-fitting tuxedo (jacket tight around belly), fumbling with cufflinks,
        looking tired and stressed, glasses slightly askew, wants to just stay home.
        His soft dad-body clearly visible - NOT athletic at all.

        NINA: In modest burgundy dress, putting on simple earrings, giving Gabe an encouraging
        but tired smile. Normal mom body, not glamorous. She's patient but exhausted.

        Both look like real suburban parents who just want one night without the kids."""
    },
    {
        "filename": "gabe_protective_stance",
        "description": """Gabe in protective father stance.

        SCENE: Gabe shielding his family from danger (during dinosaur adventure)

        GABE: Arms spread protectively, stepping forward, determined expression despite fear.
        His tuxedo is disheveled/torn. His soft dad-body shows - he's NOT a hero physique,
        just a scared dad trying to protect his family. Glasses crooked, sweating.
        Average build, slightly overweight, clearly NOT someone who works out.

        Show him being brave despite his obvious physical unsuitability for adventure."""
    },
    {
        "filename": "nina_protective_stance",
        "description": """Nina in fierce mama-bear protective stance.

        SCENE: Nina protecting the kids during danger

        NINA: Arms out protectively, fierce determined expression, dress torn/dirty.
        Her normal mom body in action - NOT athletic or superhero-like.
        She's scared but determined. Practical mom shoes (kicked off heels long ago).

        Show a real mom being brave - not glamorous, just fiercely protective.
        Relatable exhausted mom energy mixed with fierce love."""
    },
    {
        "filename": "gabe_nina_running",
        "description": """Gabe and Nina running together from danger.

        SCENE: Both parents running through jungle/swamp

        GABE: Running awkwardly in dress shoes, out of breath, tuxedo flapping,
        soft belly bouncing, clearly not athletic. Face red from exertion.
        His desk-worker body struggling with physical activity.

        NINA: Running with more grace but still clearly exhausted, barefoot
        (abandoned heels), dress hiked up for running. Normal mom running,
        not graceful model running. Hair messy, face sweaty.

        Both looking back in fear. Comedy in their physical struggle."""
    },
    {
        "filename": "gabe_nina_exhausted_relief",
        "description": """Gabe and Nina exhausted but relieved, holding hands.

        SCENE: Moment of safety, catching breath

        GABE: Bent over, hands on knees, panting, glasses fogged up.
        Tuxedo completely ruined. His soft body showing through torn shirt.
        Relief washing over tired face.

        NINA: Leaning against him for support, equally exhausted.
        Dress torn and dirty. Hair completely disheveled.
        Sharing a tired but loving look with Gabe.

        Real couple moment - tired, messy, but in love."""
    },
    {
        "filename": "gabe_nina_tender_moment",
        "description": """Gabe and Nina having a quiet tender moment together.

        SCENE: Intimate couple moment, thinking about their kids

        GABE: Holding Nina's hand, looking at her with tired but loving eyes.
        Glasses reflecting light. His soft features showing gentleness.
        Just a tired dad who loves his wife.

        NINA: Squeezing his hand back, warm tired smile.
        Her normal features showing genuine love.
        Just a tired mom grateful for her husband.

        No glamour, just real love between exhausted parents."""
    },
    {
        "filename": "family_group_pose",
        "description": """The whole Bornsztein family together.

        SCENE: Family portrait moment - Gabe, Nina, Mia (9yo girl), Leo (5yo boy)

        GABE: Standing proud but tired, arm around Nina. Soft dad body in tuxedo.
        Glasses, thinning hair, gentle tired smile.

        NINA: Arm around Gabe, other hand on Mia's shoulder. Normal mom body
        in burgundy dress. Warm exhausted smile.

        MIA: 9-year-old girl, brown ponytail, standing responsible and proud.

        LEO: 5-year-old boy, messy blonde hair, being held or standing in front.

        A real, relatable suburban family - not picture perfect, just loving."""
    },
    {
        "filename": "gabe_nina_arguing_stressed",
        "description": """Gabe and Nina in a stressed argument moment.

        SCENE: Tension between tired parents during crisis

        GABE: Frustrated gesture, running hand through thinning hair.
        Stress visible on face. Glasses pushed up. Dad body language of defeat.

        NINA: Arms crossed, giving 'The Look' - one eyebrow raised, patient but
        frustrated. Normal mom stance. Dark hair falling out of place.

        Real couple having a real stressed moment - relatable parent conflict."""
    },
]


def generate_pose(pose: dict) -> bool:
    """Generate a single family pose."""
    filename = f"{pose['filename']}.png"
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        print(f"  Skipping {filename} (exists)")
        return True

    prompt = f"""{STYLE_BASE}

=== CRITICAL CHARACTER REQUIREMENTS ===

{GABE_DESCRIPTION}

{NINA_DESCRIPTION}

=== THIS SPECIFIC SCENE ===

{pose['description']}

=== IMPORTANT REMINDERS ===
- Gabe must have a SOFT DAD BODY - slightly overweight, NOT muscular
- Nina must have a NORMAL MOM BODY - NOT a model, NOT glamorous
- Both should look TIRED and like REAL SUBURBAN PARENTS
- Pixar style but REALISTIC proportions for adults
- Clean background, professional animation concept art quality
- These are NORMAL PEOPLE not fitness models or action heroes"""

    print(f"\nGenerating: {filename}")
    print(f"  Scene: {pose['filename'].replace('_', ' ').title()}")

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
    parser = argparse.ArgumentParser(description="Generate family action poses")
    parser.add_argument("--pose", "-p", type=int,
                        help="Generate specific pose (1-8)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all poses")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Regenerate even if files exist")
    args = parser.parse_args()

    if args.list:
        print("\nFamily Action Poses:")
        print("=" * 60)
        for i, pose in enumerate(FAMILY_POSES, 1):
            print(f"\n{i}. {pose['filename']}")
            print(f"   {pose['description'][:80]}...")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.force:
        # Remove existing files if force regenerating
        for f in OUTPUT_DIR.glob("*.png"):
            print(f"Removing: {f}")
            f.unlink()

    poses_to_generate = [FAMILY_POSES[args.pose - 1]] if args.pose else FAMILY_POSES

    total = 0
    success = 0

    print("\n" + "=" * 60)
    print("GENERATING CORRECTED FAMILY ACTION POSES")
    print("These show NORMAL TIRED PARENTS - not fitness models!")
    print("=" * 60)

    for pose in poses_to_generate:
        total += 1
        if generate_pose(pose):
            success += 1
        time.sleep(8)  # Rate limit protection

    print(f"\n{'=' * 60}")
    print(f"Complete: {success}/{total} images generated")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
