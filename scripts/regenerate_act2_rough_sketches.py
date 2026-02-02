#!/usr/bin/env python3
"""Regenerate Act 2 storyboard images in ROUGH SKETCH style using Gemini API.

This replaces the detailed Pixar-style renders with simple, loose sketches
like professional animation thumbnails - focusing on composition, camera angles,
and action flow rather than final render quality.
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
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "storyboards" / "act2" / "panels"

# ROUGH SKETCH style prefix - simple black and white thumbnails
STYLE_PREFIX = """Rough storyboard sketch, simple black and white pencil drawing,
loose gestural lines, basic shapes for characters, professional animation thumbnail style,
focus on composition and camera angle, NOT detailed or polished,
quick sketch like Pixar story artist thumbnails, grayscale only,
stick figures or simple silhouettes acceptable, 16:9 aspect ratio"""

# Simplified character descriptions for sketch style
CHARACTERS = {
    "gabe": "father figure in torn suit (simple shapes)",
    "nina": "mother figure in dress (simple shapes)",
    "mia": "older child girl (simple stick figure)",
    "leo": "younger child boy in dino pajamas (simple stick figure)",
    "ruben": "old man janitor with mop, droopy wings (basic shapes)",
    "mcnattin": "detective in suit (simple figure)",
    "jenny": "teenage girl (simple figure)"
}

# All Act 2 panels with ROUGH SKETCH prompts
ACT2_PANELS = [
    # Scene 11: House Morning (3 panels)
    {
        "filename": "scene-11-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide establishing shot,
suburban house exterior, multiple police cars in driveway,
yellow tape, morning light, investigation scene,
quick sketch showing layout and police activity"""
    },
    {
        "filename": "scene-11-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
detective figure on phone, notepad in hand,
police activity in background, simple gesture drawing"""
    },
    {
        "filename": "scene-11-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
nosy neighbor in bathrobe, holding coffee,
staring at police activity, small dog at feet,
comedy moment, simple sketch"""
    },

    # Scene 12: Jenny Interview (4 panels)
    {
        "filename": "scene-12-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
detective and teenage girl at table, interview scene,
morning light through window, simple composition sketch"""
    },
    {
        "filename": "scene-12-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
teenage girl face, nervous expression, remembering,
simple facial expression sketch"""
    },
    {
        "filename": "scene-12-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
detective face, interest piqued, listening intently,
simple facial expression sketch"""
    },
    {
        "filename": "scene-12-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
detective notepad with messy handwriting,
pen underlining key phrases, simple sketch"""
    },

    # Scene 13: Kids Breakfast (7 panels)
    {
        "filename": "scene-13-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
kitchen table with two children and social worker,
messy cereal, domestic scene, simple layout sketch"""
    },
    {
        "filename": "scene-13-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, close-up insert,
young boy eating cereal messily, milk on face,
happy expression, simple sketch"""
    },
    {
        "filename": "scene-13-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
older girl face, serious and worried expression,
trying to be grown up, simple facial sketch"""
    },
    {
        "filename": "scene-13-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
young boy doing explosion gesture with arms,
knocking over cereal bowl, action sketch"""
    },
    {
        "filename": "scene-13-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
overwhelmed social worker watching cereal spill,
reaching for napkins, simple reaction sketch"""
    },
    {
        "filename": "scene-13-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
two siblings at breakfast table telling story,
cleaning up while talking, teamwork, simple sketch"""
    },
    {
        "filename": "scene-13-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
detective taking phone as evidence,
kids watching concerned, evidence bag visible, simple sketch"""
    },

    # Scene 14: Cave Connection (5 panels)
    {
        "filename": "scene-14-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
Jurassic cave interior, two parent figures huddled,
T-Rex shadow at entrance, rough cave walls sketch"""
    },
    {
        "filename": "scene-14-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
smartphone screen with static and glitch,
faint glow at edges, hands holding phone, simple sketch"""
    },
    {
        "filename": "scene-14-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, extreme close-up,
phone battery showing 65 percent, time display,
important detail sketch"""
    },
    {
        "filename": "scene-14-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
mother holding phone thinking in cave,
disheveled appearance, husband in background, simple sketch"""
    },
    {
        "filename": "scene-14-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
mother face calling into phone desperately,
emotional expression, tears forming, simple sketch"""
    },

    # Scene 15: Police Car Kids (3 panels)
    {
        "filename": "scene-15-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide interior shot,
two children in police car back seat behind barrier,
phone on passenger seat, isolated feeling, layout sketch"""
    },
    {
        "filename": "scene-15-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
phone on car seat crackling with faint glow,
barrier visible at frame edge, simple sketch"""
    },
    {
        "filename": "scene-15-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot close-up,
two children faces recognizing voice,
hope dawning, leaning toward barrier, expression sketch"""
    },

    # Scene 16: Cave Intercut (3 panels)
    {
        "filename": "scene-16-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
mother kneeling calling into phone desperately,
hunched over phone, tears visible, emotional sketch"""
    },
    {
        "filename": "scene-16-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
father in cave finding tunnel exit,
light visible ahead, hope on face, simple sketch"""
    },
    {
        "filename": "scene-16-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
both parents making quick decision in cave,
phone between them, tunnel visible behind, composition sketch"""
    },

    # Scene 17: Car Frustration (4 panels)
    {
        "filename": "scene-17-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
two children pressing against car barrier screaming,
hands on barrier, tears forming, emotional sketch"""
    },
    {
        "filename": "scene-17-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
small child hands pressed against plexiglass barrier,
phone visible beyond, separation metaphor, simple sketch"""
    },
    {
        "filename": "scene-17-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
detective getting into driver seat,
unaware of kids' distress, keys in hand, simple sketch"""
    },
    {
        "filename": "scene-17-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, wide interior shot,
police car interior, detective driving front,
kids defeated in back, phone glow fading, layout sketch"""
    },

    # Scene 18: Cave Tunnel (3 panels)
    {
        "filename": "scene-18-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, tracking medium shot,
two parents moving through narrow cave tunnel,
mother leading with phone as light, single file, sketch"""
    },
    {
        "filename": "scene-18-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
phone screen showing signal bars dropping,
static increasing, battery lower, simple sketch"""
    },
    {
        "filename": "scene-18-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
parents paused in tunnel looking at phone,
golden light at tunnel exit behind, transitional sketch"""
    },

    # Scene 19: Montage (6 panels)
    {
        "filename": "scene-19-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
parents exiting cave into bright Jurassic jungle,
squinting in light, checking phone, simple sketch"""
    },
    {
        "filename": "scene-19-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
two children in institutional setting,
plastic chairs, fluorescent light, holding hands, simple sketch"""
    },
    {
        "filename": "scene-19-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, epic wide shot,
tiny parent figures in massive Jurassic landscape,
giant ferns, dinosaur silhouette distant, scale sketch"""
    },
    {
        "filename": "scene-19-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
child backpack open showing snacks inside,
dinosaur backpack design, simple detail sketch"""
    },
    {
        "filename": "scene-19-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
epic Jurassic sunset with parent silhouettes on ridge,
prehistoric landscape, beautiful sky, simple sketch"""
    },
    {
        "filename": "scene-19-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
police station at night, kids being settled,
janitor with mop visible in shadows, layout sketch"""
    },

    # Scene 20: Police Station Ruben Reveal (11 panels)
    {
        "filename": "scene-20-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide establishing shot,
police station conference room with sleeping bags,
older girl sitting alert, younger boy lying down, simple sketch"""
    },
    {
        "filename": "scene-20-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, medium tracking shot,
detective leading children into conference room,
awkward kindness, nighttime interior, simple sketch"""
    },
    {
        "filename": "scene-20-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
mysterious janitor in doorway with mop,
wild gray hair, something shimmering at back (wings),
kids looking up curious, character intro sketch"""
    },
    {
        "filename": "scene-20-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
old man face giving knowing wink,
tired but sparkling eyes, slight smile, expression sketch"""
    },
    {
        "filename": "scene-20-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
fairy godfather crouching to kid level explaining,
kids listening, mop held like wand, composition sketch"""
    },
    {
        "filename": "scene-20-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
droopy iridescent fairy wings revealed,
glowing faintly from janitor coveralls, reveal sketch"""
    },
    {
        "filename": "scene-20-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
two children faces with pure wonder,
boy covering mouth excited, girl amazed, expression sketch"""
    },
    {
        "filename": "scene-20-panel-08.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
fairy godfather demonstrating weak magic with mop,
dim sparkles, pencil barely levitating, action sketch"""
    },
    {
        "filename": "scene-20-panel-09.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
mop propping door open, visual metaphor,
fairy explaining portal concept, simple sketch"""
    },
    {
        "filename": "scene-20-panel-10.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
detective returning, fairy hiding wings quickly,
kids overselling innocence in sleeping bags, comedy sketch"""
    },
    {
        "filename": "scene-20-panel-11.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
two children in sleeping bags eyes open planning,
determined expressions, fairy waving at door edge, sketch"""
    },

    # Scene 21: Jurassic Tree Emotional (8 panels)
    {
        "filename": "scene-21-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide crane up shot,
massive prehistoric tree with two small figures on branch,
night sky with stars through canopy, scale sketch"""
    },
    {
        "filename": "scene-21-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
ruined heels being removed from blistered feet,
shoes dropping into darkness, simple detail sketch"""
    },
    {
        "filename": "scene-21-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
exhausted parents settling on tree branch for night,
intimate positioning, night sky through canopy, sketch"""
    },
    {
        "filename": "scene-21-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
mother face emotional confession beginning,
vulnerable expression, moonlight on face, sketch"""
    },
    {
        "filename": "scene-21-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
mother crying releasing held back fear,
tears streaming, hand to mouth, emotional sketch"""
    },
    {
        "filename": "scene-21-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
beautiful Jurassic night sky through ancient trees,
moon full, bioluminescence below, atmosphere sketch"""
    },
    {
        "filename": "scene-21-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
husband holding wife on tree branch,
head on shoulder, wedding rings catching moonlight, sketch"""
    },
    {
        "filename": "scene-21-panel-08.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
phone battery indicator showing 50 percent,
screen frozen glitchy, urgency reminder, simple sketch"""
    },

    # Scene 22: Station Escape Comedy (14 panels)
    {
        "filename": "scene-22-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, tracking medium shot,
fairy godfather pushing squeaky mop bucket down hall,
wincing at squeaks, comedic stealth, action sketch"""
    },
    {
        "filename": "scene-22-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
mop wand aimed at wheel, magic misfire,
wheel disappearing, bucket tilting, comedy sketch"""
    },
    {
        "filename": "scene-22-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
fairy trying to magically move office chair,
weak sparkles, chair barely moving, comedy sketch"""
    },
    {
        "filename": "scene-22-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
magic blast accidentally hitting ceiling,
ceiling tile exploding, debris falling, action sketch"""
    },
    {
        "filename": "scene-22-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, POV shot,
view through window at kids pretending to sleep,
locked door handle visible, simple sketch"""
    },
    {
        "filename": "scene-22-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
two children waking up hearing commotion,
sitting up alert, shadows through door, sketch"""
    },
    {
        "filename": "scene-22-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
kids using rolling chair as battering ram on door,
pushing together, kid ingenuity, action sketch"""
    },
    {
        "filename": "scene-22-panel-08.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
detective sleeping at desk head on arms,
completely oblivious, empty coffee cup, simple sketch"""
    },
    {
        "filename": "scene-22-panel-09.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
evidence cabinet with phone visible inside locked,
phone glowing through mesh, keys on desk, sketch"""
    },
    {
        "filename": "scene-22-panel-10.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
fairy magic misfiring toward sleeping detective,
magic beam curving wrong, kids horrified, action sketch"""
    },
    {
        "filename": "scene-22-panel-11.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
detective frozen mid-yawn by freeze spell,
frost shimmer effect, hand raised, simple sketch"""
    },
    {
        "filename": "scene-22-panel-12.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
child finger poking frozen detective face curious,
testing if really frozen, comedy sketch"""
    },
    {
        "filename": "scene-22-panel-13.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
retrieving phone from evidence cabinet triumph,
keys from frozen detective, phone glowing, sketch"""
    },
    {
        "filename": "scene-22-panel-14.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
group rushing to elevator escape achieved,
all three piling in, relief on faces, action sketch"""
    },

    # Scene 23: Car Chase (8 panels)
    {
        "filename": "scene-23-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide tracking shot,
group bursting out of police station into parking lot,
kids leading, fairy wings visible, night scene sketch"""
    },
    {
        "filename": "scene-23-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
girl checking phone like compass navigation,
signal direction indicator, determined grip, sketch"""
    },
    {
        "filename": "scene-23-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
group piling into police car kids in driver area,
absurd setup beginning, night parking lot, sketch"""
    },
    {
        "filename": "scene-23-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, interior medium shot,
girl driving barely seeing over wheel,
boy on her lap helping steer, fairy passenger horrified, sketch"""
    },
    {
        "filename": "scene-23-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
mop wand touching car ignition magical glow,
sparks at ignition, dashboard lighting up, sketch"""
    },
    {
        "filename": "scene-23-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, wide tracking shot,
police car racing through night streets,
pursuing cars behind, kids steering badly visible, chase sketch"""
    },
    {
        "filename": "scene-23-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
phone signal bars increasing getting closer,
screen less glitchy, navigation success, sketch"""
    },
    {
        "filename": "scene-23-panel-08.png",
        "prompt": f"""{STYLE_PREFIX}, medium interior shot,
car interior everyone listening to parents voices,
girl emotional while driving, phone glowing brighter, sketch"""
    },

    # Scene 24: Tree Wake (3 panels)
    {
        "filename": "scene-24-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
father face waking in tree at dawn,
eyes opening, recognition of sound, simple sketch"""
    },
    {
        "filename": "scene-24-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
phone crackling to life with kids voices,
screen active, hands gripping tight, battery 40 percent, sketch"""
    },
    {
        "filename": "scene-24-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
both parents clutching phone tears of joy,
dawn breaking behind through trees, emotional sketch"""
    },

    # Scene 25: Portal Jump Climax (7 panels)
    {
        "filename": "scene-25-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
police car crashed into curb steam from engine,
pursuing cars approaching behind, night scene sketch"""
    },
    {
        "filename": "scene-25-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, medium tracking shot,
kids and fairy running from car phone guiding,
fairy wings visible, police lights behind, action sketch"""
    },
    {
        "filename": "scene-25-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
girl running phone to ear talking to parents,
tears and wind, portal glow in eyes, emotional sketch"""
    },
    {
        "filename": "scene-25-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
excited boy grabbing phone proud announcement,
inappropriate smile, sister reaching for phone, sketch"""
    },
    {
        "filename": "scene-25-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, POV wide shot,
TIME WARP PORTAL visible ahead,
bright swirling vortex, electrical discharge at edges,
smaller than before and closing, night glow, sketch"""
    },
    {
        "filename": "scene-25-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
girl hiding phone in bushes near portal,
phone still glowing, reluctant hands, critical moment sketch"""
    },
    {
        "filename": "scene-25-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, wide hero shot,
THE JUMP into portal climax, three figures leaping,
girl leading, boy hand in hers, fairy wings spread,
portal swirling, police lights arriving behind,
iconic Act 2 climax action sketch"""
    },
]


def generate_image(prompt: str, filename: str, force: bool = False) -> bool:
    """Generate a single image using Gemini 2.0 Flash."""
    output_path = OUTPUT_DIR / filename

    # Only skip if exists AND not forcing regeneration
    if output_path.exists() and not force:
        print(f"  ⊘ Skipping (exists): {filename}")
        return True

    print(f"Generating: {filename}")
    print(f"  Prompt: {prompt[:80]}...")

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
    """Regenerate Act 2 storyboard panels in ROUGH SKETCH style."""
    print("=" * 60)
    print("REGENERATING Act 2 Storyboard Panels - ROUGH SKETCH STYLE")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Total panels: {len(ACT2_PANELS)}")
    print()
    print("Style: Black and white pencil sketches, loose gestural lines,")
    print("       basic shapes, animation thumbnail style")
    print()

    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set")
        return 1

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Parse command line arguments
    force_regen = "--force" in sys.argv or "-f" in sys.argv

    # Optional: specify scene range via command line args
    start_idx = 0
    end_idx = len(ACT2_PANELS)

    for arg in sys.argv[1:]:
        if arg.startswith("--start="):
            start_idx = int(arg.split("=")[1])
        elif arg.startswith("--end="):
            end_idx = int(arg.split("=")[1])
        elif arg.isdigit():
            if start_idx == 0:
                start_idx = int(arg)
            else:
                end_idx = int(arg)

    if force_regen:
        print("*** FORCE MODE: Will regenerate ALL panels, replacing existing ***")
        print()

    panels_to_generate = ACT2_PANELS[start_idx:end_idx]
    total = len(ACT2_PANELS)

    success_count = 0

    for i, panel in enumerate(panels_to_generate, start_idx + 1):
        print(f"\n[{i}/{total}] ", end="")
        if generate_image(panel["prompt"], panel["filename"], force=force_regen):
            success_count += 1

        # Small delay between requests to avoid rate limiting
        if i < end_idx:
            time.sleep(2)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{len(panels_to_generate)} images generated")
    print("=" * 60)

    return 0 if success_count == len(panels_to_generate) else 1


if __name__ == "__main__":
    sys.exit(main())
