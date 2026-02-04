#!/usr/bin/env python3
"""Generate movie trailer storyboard images using Gemini API.

Creates a 60-90 second teaser trailer with dramatic pacing.
Selects the best moments from all 3 acts for maximum impact.

STYLE: Cinematic storyboard panels with warm Pixar-style aesthetic.
"""

import base64
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "storyboards" / "trailer" / "panels"

# Cinematic style prefix - for trailer impact
TRAILER_STYLE = """Pixar-style animated film storyboard panel, warm cinematic lighting,
professional composition, high contrast for dramatic effect,
clean stylized characters with expressive faces,
16:9 widescreen aspect ratio, movie trailer quality,
rich color palette, emotional staging"""

# Character consistency notes
CHARACTERS = {
    "MIA": "8-year-old girl, brown hair ponytail, big expressive eyes, pajamas",
    "LEO": "5-year-old boy, light brown hair, round face, dinosaur pajamas, innocent",
    "GABE": "40s father, dark hair, stubble, black tuxedo (later torn/dirty)",
    "NINA": "late 30s mother, brown hair, elegant black dress (later ruined)",
    "RUBEN": "old man, wild gray hair, janitor coveralls, tired eyes, mop as wand",
    "JETPLANE": "small cute creature, chicken-lizard hybrid, bright eyes, friendly"
}

# ========================================
# TRAILER PANELS - 26 panels for ~75 seconds
# ========================================

TRAILER_PANELS = [
    # ===== OPENING HOOK (3 panels) =====
    {
        "filename": "trailer-001-family-home.png",
        "section": "opening",
        "duration": 3,
        "prompt": f"""{TRAILER_STYLE},
WIDE ESTABLISHING SHOT - warm suburban living room at evening,
TV glowing in corner, two kids on couch watching cartoons,
{CHARACTERS['MIA']} and {CHARACTERS['LEO']} cuddled together,
dinosaur toys scattered everywhere, cozy family atmosphere,
storm visible through window, warm golden interior lighting,
Pixar domestic scene feel, inviting and relatable"""
    },
    {
        "filename": "trailer-002-parents-leaving.png",
        "section": "opening",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
MEDIUM SHOT - parents in formal wear rushing to leave,
{CHARACTERS['GABE']} checking watch impatiently,
{CHARACTERS['NINA']} putting on earrings while walking,
kids visible in background on couch, teen babysitter on phone,
door open to stormy night outside, sense of urgency,
family comedy staging, warm interior vs dark exterior"""
    },
    {
        "filename": "trailer-003-promise.png",
        "section": "opening",
        "duration": 3,
        "prompt": f"""{TRAILER_STYLE},
CLOSE-UP EMOTIONAL SHOT - {CHARACTERS['MIA']} looking up,
big pleading eyes, hopeful but worried expression,
SPEECH BUBBLE or implied dialogue: "Promise?",
soft focus background showing father figure,
critical emotional beat, audience hook moment,
warm lighting on child's face, vulnerability"""
    },

    # ===== INCITING INCIDENT (3 panels) =====
    {
        "filename": "trailer-004-storm-drive.png",
        "section": "incident",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
DRAMATIC WIDE SHOT - car driving through intense storm,
rain lashing windshield, lightning illuminating sky,
headlights cutting through darkness, road barely visible,
ominous atmosphere, danger approaching,
cinematic weather effects, thriller tension building"""
    },
    {
        "filename": "trailer-005-timewarp.png",
        "section": "incident",
        "duration": 3,
        "prompt": f"""{TRAILER_STYLE},
VFX HERO SHOT - massive TIME WARP portal opening in road,
bright blue (#0096FF) swirling vortex of energy,
electrical discharge crackling at edges,
car approaching the impossible phenomenon,
mind-bending sci-fi moment, scale and awe,
dramatic low angle, car small against massive portal"""
    },
    {
        "filename": "trailer-006-crash-into-portal.png",
        "section": "incident",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
ACTION SHOT - car entering the time warp portal,
blue energy swirling around vehicle,
parents' terrified faces visible through windshield,
motion blur and energy effects,
point of no return moment, dramatic impact,
everything changes, visual shock and awe"""
    },

    # ===== MYSTERY/STAKES (3 panels) =====
    {
        "filename": "trailer-007-tv-explodes.png",
        "section": "stakes",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
DRAMATIC SHOT - TV screen exploding with sparks,
{CHARACTERS['MIA']} and {CHARACTERS['LEO']} ducking in fear,
lights flickering out, phone glowing mysteriously,
something supernatural just happened,
dark room lit only by phone glow and sparks,
horror movie tension in family film"""
    },
    {
        "filename": "trailer-008-parents-missing.png",
        "section": "stakes",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
EMOTIONAL MEDIUM SHOT - kids with social worker,
{CHARACTERS['MIA']} looking determined but scared,
{CHARACTERS['LEO']} eating cereal, confused,
police activity in background, serious atmosphere,
something is very wrong, family torn apart,
institutional fluorescent lighting, cold contrast"""
    },
    {
        "filename": "trailer-009-jurassic-wake.png",
        "section": "stakes",
        "duration": 3,
        "prompt": f"""{TRAILER_STYLE},
STUNNING REVEAL SHOT - parents waking in prehistoric jungle,
{CHARACTERS['GABE']} and {CHARACTERS['NINA']} in crashed car,
surrounded by massive ferns and ancient plants,
steamy mist, golden-green jungle lighting,
pure wonder and confusion on their faces,
they're not in Kansas anymore moment"""
    },

    # ===== T-REX REVEAL (2 panels) =====
    {
        "filename": "trailer-010-jurassic-beauty.png",
        "section": "trex",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
BREATHTAKING WIDE SHOT - lush Jurassic swamp landscape,
prehistoric plants reaching to the sky,
misty atmosphere with shafts of golden light,
small portal visible in background (blue glow),
sense of ancient world, dangerous beauty,
establishing the stakes of being trapped here"""
    },
    {
        "filename": "trailer-011-trex-reveal.png",
        "section": "trex",
        "duration": 3,
        "prompt": f"""{TRAILER_STYLE},
TERRIFYING LOW ANGLE - T-REX emerging from jungle,
massive dinosaur breaking through trees,
realistic proportions, earth tones, intelligent eyes,
parents tiny in foreground, running away,
pure primal terror, stakes couldn't be higher,
blockbuster movie money shot"""
    },

    # ===== RUBEN & RESCUE DECISION (3 panels) =====
    {
        "filename": "trailer-012-ruben-reveal.png",
        "section": "heroes",
        "duration": 3,
        "prompt": f"""{TRAILER_STYLE},
COMEDIC REVEAL SHOT - {CHARACTERS['RUBEN']} revealing himself,
old man in janitor clothes with magical sparkles around him,
mop held like a wizard's staff,
kids {CHARACTERS['MIA']} and {CHARACTERS['LEO']} staring in wonder,
"I'm your fairy godfather" moment,
comedy beat with magical undertones, subversive"""
    },
    {
        "filename": "trailer-013-kids-determined.png",
        "section": "heroes",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
HERO POSE - kids ready for adventure,
{CHARACTERS['MIA']} looking determined, protective of Leo,
{CHARACTERS['LEO']} with snack backpack, brave face,
decision to rescue their parents,
young heroes rising to the challenge,
warm lighting, empowerment moment"""
    },
    {
        "filename": "trailer-014-steal-police-car.png",
        "section": "heroes",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
COMEDIC ACTION SHOT - kids driving police car,
{CHARACTERS['MIA']} barely able to see over steering wheel,
{CHARACTERS['LEO']} sitting on her lap helping steer,
{CHARACTERS['RUBEN']} panicking in passenger seat,
police lights flashing, completely insane situation,
family film pushing boundaries, hilarious"""
    },

    # ===== ADVENTURE MONTAGE (5 panels) =====
    {
        "filename": "trailer-015-portal-jump.png",
        "section": "adventure",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
DYNAMIC ACTION - kids and Ruben jumping into portal,
blue time warp energy swirling around them,
determined/scared expressions,
leap of faith moment, no turning back,
heroic slow-motion feeling, dramatic lighting"""
    },
    {
        "filename": "trailer-016-meet-jetplane.png",
        "section": "adventure",
        "duration": 3,
        "prompt": f"""{TRAILER_STYLE},
CUTE CHARACTER INTRO - {CHARACTERS['JETPLANE']} meeting Leo,
adorable strange creature with chicken-lizard features,
{CHARACTERS['LEO']} reaching out to pet it,
love at first sight between boy and creature,
comedic sidekick introduction, merchandise moment,
bright jungle setting, heartwarming"""
    },
    {
        "filename": "trailer-017-colored-farts.png",
        "section": "adventure",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
COMEDIC VFX SHOT - Jetplane releasing colored fart plumes,
rainbow smoke rising into the sky (red, blue, green),
kids and Ruben reacting with disgust and amazement,
the ridiculous becomes useful,
visual gag that also serves the plot,
colorful and absurd, family comedy gold"""
    },
    {
        "filename": "trailer-018-parents-see-signal.png",
        "section": "adventure",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
HOPEFUL WIDE SHOT - parents on Jurassic bluff,
{CHARACTERS['GABE']} and {CHARACTERS['NINA']} dirty and exhausted,
pointing at distant colored plumes in the sky,
hope restored, their children are here,
emotional moment, rescue might be possible,
beautiful sunset lighting over prehistoric landscape"""
    },
    {
        "filename": "trailer-019-canyon-bridge.png",
        "section": "adventure",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
FANTASTICAL WIDE SHOT - crayon bridge spanning canyon,
colorful crayons magically forming bridge structure,
kids and Ruben carefully crossing,
impossible made possible through magic,
whimsical yet dangerous, creative problem solving,
vertiginous drop below, tension"""
    },

    # ===== CLIMAX TEASE (4 panels) =====
    {
        "filename": "trailer-020-leo-falls.png",
        "section": "climax",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
DRAMATIC ACTION - {CHARACTERS['LEO']} falling from bridge,
crayon snapping beneath him,
{CHARACTERS['MIA']} reaching out screaming,
heart-stopping moment of danger,
will they save him in time?,
extreme downward angle, vertigo"""
    },
    {
        "filename": "trailer-021-trex-blocks-path.png",
        "section": "climax",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
TENSE STANDOFF - T-Rex blocking the portal,
entire family huddled together,
massive dinosaur between them and escape,
time running out (phone battery dying),
impossible situation, how will they survive?,
dramatic scale contrast"""
    },
    {
        "filename": "trailer-022-ruben-magic.png",
        "section": "climax",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
MAGICAL ACTION - {CHARACTERS['RUBEN']} casting his biggest spell,
mop glowing with intense magical energy,
strain and determination on his face,
kids watching hopefully,
fairy godfather moment of redemption,
swirling magical effects"""
    },
    {
        "filename": "trailer-023-giant-jetplane.png",
        "section": "climax",
        "duration": 3,
        "prompt": f"""{TRAILER_STYLE},
EPIC VFX SHOT - Jetplane transformed to GIANT size,
now bigger than the T-Rex,
creature that was cute is now MASSIVE and terrifying,
T-Rex backing away in fear,
{CHARACTERS['LEO']} tiny below, commanding: "Attack!",
complete reversal of power, triumphant"""
    },

    # ===== RESOLUTION HOOK (2 panels) =====
    {
        "filename": "trailer-024-family-reunion.png",
        "section": "resolution",
        "duration": 3,
        "prompt": f"""{TRAILER_STYLE},
EMOTIONAL CLIMAX - family group hug reunion,
{CHARACTERS['GABE']}, {CHARACTERS['NINA']}, {CHARACTERS['MIA']}, {CHARACTERS['LEO']} embracing,
tears of joy, relief, love,
Jetplane (small again) nearby watching happily,
everything they went through was worth it,
warm golden lighting, happy ending promise"""
    },
    {
        "filename": "trailer-025-comedy-beat.png",
        "section": "resolution",
        "duration": 2,
        "prompt": f"""{TRAILER_STYLE},
COMEDY BUTTON - {CHARACTERS['LEO']} proudly presenting Jetplane,
dialogue implied: "He farts colors!",
family looking bemused/amused,
Jetplane looking proud of himself,
final laugh before title card,
breaking tension with humor"""
    },
]

# Title cards (text-based, simpler generation)
TITLE_CARDS = [
    {
        "filename": "trailer-title-01-this-summer.png",
        "position": "after trailer-003",
        "prompt": f"""Cinematic movie title card, dark background with subtle blue energy wisps,
bold white text centered: "THIS SUMMER",
professional movie trailer typography, clean minimalist design,
slight lens flare effect, premium feel, 16:9 aspect ratio"""
    },
    {
        "filename": "trailer-title-02-one-family.png",
        "position": "after trailer-011",
        "prompt": f"""Cinematic movie title card, dark background with prehistoric jungle silhouette,
bold white text centered: "ONE FAMILY",
professional movie trailer typography, atmospheric mist,
dramatic lighting, premium feel, 16:9 aspect ratio"""
    },
    {
        "filename": "trailer-title-03-anywhere.png",
        "position": "after trailer-019",
        "prompt": f"""Cinematic movie title card, dark background with swirling blue portal energy,
bold white text centered: "WILL GO ANYWHERE",
professional movie trailer typography, magical sparkles,
dramatic and hopeful, premium feel, 16:9 aspect ratio"""
    },
    {
        "filename": "trailer-title-04-logo.png",
        "position": "end",
        "prompt": f"""Movie logo title card, animated film style,
"FAIRY DINOSAUR DATE NIGHT" in playful but epic font,
small colorful dinosaur silhouette integrated into design,
magical sparkles and swirls around text,
dark background with warm color accents,
professional animated feature logo, 16:9 aspect ratio"""
    },
    {
        "filename": "trailer-title-05-coming-soon.png",
        "position": "end",
        "prompt": f"""Cinematic movie title card, dark background,
"COMING SOON" in clean white professional text,
subtle magical particles floating,
minimal elegant design, movie trailer standard,
16:9 aspect ratio"""
    },
]


def generate_image(prompt: str, filename: str) -> bool:
    """Generate a single image using Gemini 2.0 Flash."""
    output_path = OUTPUT_DIR / filename

    # Skip if already exists
    if output_path.exists():
        print(f"  ⏭  Skipping (exists): {filename}")
        return True

    print(f"Generating: {filename}")
    print(f"  Prompt: {prompt[:100]}...")

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
    """Generate all trailer storyboard panels."""
    print("=" * 60)
    print("Generating Movie Trailer Storyboard Panels")
    print("FAIRY DINOSAUR DATE NIGHT - 60-90 Second Teaser")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_panels = TRAILER_PANELS + TITLE_CARDS
    success_count = 0
    total = len(all_panels)

    for i, panel in enumerate(all_panels, 1):
        print(f"\n[{i}/{total}] ", end="")
        if generate_image(panel["prompt"], panel["filename"]):
            success_count += 1

        # Small delay between requests to avoid rate limiting
        if i < total:
            time.sleep(3)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{total} images generated")
    print("=" * 60)

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
