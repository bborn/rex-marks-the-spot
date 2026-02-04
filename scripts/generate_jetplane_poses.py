#!/usr/bin/env python3
"""Generate Jetplane character poses using Gemini API.

Creates individual pose images for Jetplane the dinosaur character.
Output to assets/characters/jetplane/poses/

Fixes from PR #94 review:
- Changed eye color from amber to YELLOW per script
- Added small wings that must be visible in all poses
- Standardized pink/coral accents
- Added side profile and back view poses for 3D reference
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
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "jetplane" / "poses"

# Base character description for consistency
# FIXED: Yellow eyes (per script), small wings visible, standardized pink accents
JETPLANE_BASE = """Pixar-style 3D animated character, adorable dinosaur creature named Jetplane,
soft teal-turquoise scaly body (#4DB6AC), cream-colored belly (#FFF8E1),
warm orange fluffy neck ruff and tail tuft,
HUGE expressive BRIGHT YELLOW puppy eyes with sparkle catchlights,
coral-pink floppy ear-frills that express emotion,
SMALL DECORATIVE WINGS on back (too small to fly, just cute nubs),
round huggable body shape, short stubby legs with pink toe beans,
pink accents on ear-frills and toe beans (consistent coral-pink #FFAB91),
expressive wagging tail,
cute plush toy aesthetic, high quality animation studio render,
clean simple background, professional character art,
IMPORTANT: small wings must be visible on the back"""

# Pose definitions - includes side profile and back view for 3D reference
POSES = {
    "happy": {
        "filename": "jetplane_happy.png",
        "emotion": "PURE JOY",
        "description": """Jetplane showing PURE JOY and happiness,
eyes huge and sparkling with multiple catchlights - BRIGHT YELLOW eyes,
big open smile with tongue slightly out,
ear-frills perked UP and forward excitedly,
tail wagging rapidly creating blur effect,
SMALL WINGS visible on back, slightly raised with excitement,
whole body vibrating with excitement,
bouncing in place, radiating happiness,
the happiest little dinosaur ever,
three-quarter front view showing wings"""
    },
    "scared": {
        "filename": "jetplane_scared.png",
        "emotion": "TERRIFIED",
        "description": """Jetplane looking TERRIFIED and scared,
BRIGHT YELLOW eyes MASSIVE with dilated pupils, lots of white showing,
mouth pulled back in fearful grimace,
ear-frills pressed flat against head,
tail tucked between legs,
SMALL WINGS pressed tight against body in fear,
body low and crouched, trembling visibly,
classic scared prey animal pose,
shaking with fear but still adorable,
angle shows wings clearly"""
    },
    "farting_rainbow": {
        "filename": "jetplane_farting_rainbow.png",
        "emotion": "RAINBOW FART",
        "description": """Jetplane doing his SIGNATURE RAINBOW FART move,
crouched position with rear end slightly raised,
tail lifted high,
BRIGHT YELLOW eyes squeezed shut in concentration,
cheeks puffed out,
SMALL WINGS spread out slightly,
BEAUTIFUL COLORFUL RAINBOW CLOUD emerging from behind,
rainbow colors: red, orange, yellow, green, blue, purple,
magical sparkles and glitter particles in the rainbow cloud,
the fart is MAGICAL and BEAUTIFUL not gross,
proud concentration face,
three-quarter rear view showing wings and rainbow"""
    },
    "curious": {
        "filename": "jetplane_curious.png",
        "emotion": "CURIOUS",
        "description": """Jetplane looking CURIOUS and investigating,
head tilted to one side adorably,
one ear-frill up and one ear-frill down asymmetrically,
BRIGHT YELLOW eyes wide and bright with wonder,
nose slightly forward, sniffing,
SMALL WINGS slightly raised with curiosity,
tail held level with gentle wave,
cautious lean forward posture,
the universal "what's that?" expression,
wings visible from angle"""
    },
    "protective": {
        "filename": "jetplane_protective.png",
        "emotion": "PROTECTIVE",
        "description": """Jetplane in PROTECTIVE stance,
standing wide and planted firmly,
determined brave expression despite visible fear in BRIGHT YELLOW eyes,
ear-frills back but alert and raised,
tail raised high and rattling,
SMALL WINGS spread wide (protective gesture),
showing small teeth in defensive display,
body positioned as if shielding something behind him,
brave little guardian pose,
the "I will protect you" stance,
wings clearly visible spread out"""
    },
    "sleeping": {
        "filename": "jetplane_sleeping.png",
        "emotion": "SLEEPING",
        "description": """Jetplane PEACEFULLY SLEEPING,
curled up in cozy ball position,
tail wrapped around body,
BRIGHT YELLOW eyes gently closed with peaceful expression,
soft gentle smile,
ear-frills relaxed and drooped softly,
SMALL WINGS folded neatly against back,
soft breathing pose, totally content,
adorable sleeping baby dinosaur,
so peaceful and huggable,
wings visible folded on back"""
    },
    "excited_playful": {
        "filename": "jetplane_excited_playful.png",
        "emotion": "EXCITED PLAYFUL",
        "description": """Jetplane in PLAYFUL EXCITED pose,
classic play bow position - butt high in air, front end down,
tail wagging so fast it's a blur,
mouth open in happy pant,
BRIGHT YELLOW eyes sparkling with excitement,
ear-frills perked up and forward,
SMALL WINGS fluttering with excitement,
the universal "let's play!" body language,
bouncy and energetic,
wings visible and animated"""
    },
    "brave": {
        "filename": "jetplane_brave.png",
        "emotion": "BRAVE HERO",
        "description": """Jetplane looking BRAVE and heroic,
standing tall with puffed chest,
BRIGHT YELLOW eyes showing determination with hint of fear underneath,
jaw set firmly (for a dinosaur),
ear-frills back but alert,
SMALL WINGS spread heroically (even though they can't fly),
wide planted stance,
tail raised confidently,
the "I'm scared but I'll do it anyway" hero pose,
courageous little dinosaur,
heroic angle showing wings spread"""
    },
    "eating_candy": {
        "filename": "jetplane_eating_candy.png",
        "emotion": "CANDY BLISS",
        "description": """Jetplane experiencing PURE BLISS eating candy,
BRIGHT YELLOW eyes closed or half-lidded in ecstasy,
absolute bliss face,
colorful candy pieces or wrapper visible,
tongue out savoring the taste,
ear-frills relaxed in contentment,
SMALL WINGS relaxed and slightly drooped with contentment,
whole body showing relaxed happiness,
the face of experiencing something delicious,
candy paradise,
wings visible but relaxed"""
    },
    "proud_post_fart": {
        "filename": "jetplane_proud.png",
        "emotion": "PROUD",
        "description": """Jetplane looking PROUD and smug,
looking back over shoulder at his own work,
chin up slightly, BRIGHT YELLOW eyes half-closed smugly,
slight satisfied smile,
chest puffed out,
SMALL WINGS perked up with pride,
fading rainbow cloud visible behind him,
the post-successful fart pose,
very pleased with himself,
"I did that" energy,
wings visible from this rear three-quarter angle"""
    },
    "side_profile": {
        "filename": "jetplane_side_profile.png",
        "emotion": "NEUTRAL SIDE VIEW",
        "description": """Jetplane in PERFECT SIDE PROFILE view for 3D reference,
standing in neutral relaxed pose,
PURE SIDE VIEW - 90 degree profile,
BRIGHT YELLOW eye visible from side,
ear-frill silhouette clear,
SMALL WINGS clearly visible in profile on back,
full body shape clearly shown from side,
cream belly visible,
orange neck ruff profile visible,
tail extended naturally,
pink toe beans on visible feet,
this is a CHARACTER REFERENCE SHEET pose,
clean neutral expression,
professional model sheet quality"""
    },
    "back_view": {
        "filename": "jetplane_back_view.png",
        "emotion": "BACK VIEW",
        "description": """Jetplane seen from DIRECTLY BEHIND for 3D reference,
BACK VIEW - looking at rear of character,
SMALL WINGS very clearly visible and prominent from this angle,
teal body color on back,
orange tail tuft visible,
back of ear-frills visible,
round body shape from behind,
short stubby back legs with pink toe beans visible,
head turned slightly so we can see a bit of profile,
BRIGHT YELLOW eye partially visible,
cream belly visible on sides,
this is a CHARACTER REFERENCE SHEET pose,
professional model sheet quality,
clean background,
showing wing placement and body proportions from behind"""
    }
}


def generate_pose(pose_key: str, pose_info: dict) -> bool:
    """Generate a single pose image."""
    output_path = OUTPUT_DIR / pose_info["filename"]

    prompt = f"""{JETPLANE_BASE}

POSE: {pose_info['emotion']}
{pose_info['description']}

Single character, full body visible, clean background with subtle gradient,
professional animation concept art quality, appealing and cute,
YELLOW eyes (not amber or orange), small wings visible."""

    print(f"\nGenerating pose: {pose_info['emotion']}")
    print(f"  Output: {output_path}")

    try:
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
                print(f"  ✓ Saved successfully")
                return True

        print(f"  ✗ No image in response")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Generate all Jetplane poses."""
    print("=" * 60)
    print("Generating Jetplane Character Poses (Fixed)")
    print("=" * 60)
    print("Fixes applied:")
    print("  - YELLOW eyes (not amber/orange)")
    print("  - Small wings visible in ALL poses")
    print("  - Consistent pink/coral accents")
    print("  - Added side profile and back view")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Poses to generate: {len(POSES)}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(POSES)

    for i, (key, info) in enumerate(POSES.items(), 1):
        print(f"\n[{i}/{total}]", end="")
        if generate_pose(key, info):
            success_count += 1

        # Delay between requests to avoid rate limiting (8 sec as per CLAUDE.md)
        if i < total:
            print("  Waiting 8 seconds before next request...")
            time.sleep(8)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{total} poses generated")
    print("=" * 60)

    if success_count == total:
        print("\nAll Jetplane poses generated successfully!")
        print(f"Output location: {OUTPUT_DIR}")
    else:
        print(f"\nWarning: {total - success_count} poses failed to generate")

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
