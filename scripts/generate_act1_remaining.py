#!/usr/bin/env python3
"""Generate remaining Act 1 storyboard images (Scenes 2-10) using Gemini API."""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "storyboards" / "act1" / "panels"

# All remaining Act 1 panels (Scenes 2-10) from PROMPTS.md
ACT1_REMAINING_PANELS = [
    # Scene 2: EXT. HOUSE - NIGHT (3 panels)
    {
        "filename": "scene-02-panel-01.png",
        "prompt": """Storyboard panel, wide establishing exterior, suburban house at night,
Pixar animation style, heavy rain falling, storm in full force,
warm light spilling from windows, car in driveway,
dark stormy sky dominates upper frame, lightning illuminates scene,
trees bending in wind, puddles forming, ominous atmosphere,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-02-panel-02.png",
        "prompt": """Storyboard panel, medium tracking shot, formal couple rushing through rain,
Pixar animation style, husband running to driver side jacket over head,
wife following with clutch held over head,
door just slammed behind them, heavy rain soaking formal attire,
heels splashing through puddles, car lights flickering on,
handheld energy, urgency, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-02-panel-03.png",
        "prompt": """Storyboard panel, low angle wide shot looking up at sky,
Pixar animation style, house roofline at bottom of frame,
massive lightning bolt cracking across churning dark clouds,
rain falling toward camera, dramatic ominous atmosphere,
silhouette of trees and house at bottom, foreboding,
16:9 cinematic composition"""
    },

    # Scene 3: INT. CAR - NIGHT (4 panels)
    {
        "filename": "scene-03-panel-01.png",
        "prompt": """Storyboard panel, two-shot car interior from dashboard,
Pixar animation style, husband driving left wife passenger right,
rain streaking across windshield, wipers beating rhythmically,
wife searching purse then car console, dashboard glow on faces,
occasional lightning flash illuminates interior, tense body language,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-03-panel-02.png",
        "prompt": """Storyboard panel, close-up insert, smartphone screen in dark car,
Pixar animation style, screen showing "Calling Nina Cell",
phone bright in dark interior, woman's fingers holding phone,
ringing indicator visible, tension building,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-03-panel-03.png",
        "prompt": """Storyboard panel, POV through windshield, driver's view of road,
Pixar animation style, heavy rain obscuring vision,
road barely visible through rain, wipers struggling,
lightning reveals empty road ahead, ominous darkness,
headlight beams catching rain, something could appear any moment,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-03-panel-04.png",
        "prompt": """Storyboard panel, close-up, elegant wife in profile or three-quarter view,
Pixar animation style, concerned expression, dashboard glow warm on features,
rain shadows moving across face, lightning briefly illuminates,
emotional character moment, dark brown wavy hair,
phone partially visible in hand, 16:9 cinematic composition"""
    },

    # Scene 4: INT. HOUSE - NIGHT MONTAGE (3 panels)
    {
        "filename": "scene-04-panel-01.png",
        "prompt": """Storyboard panel, wide shot, peaceful living room same as scene 1,
Pixar animation style, children comfortable on couch with toys,
TV on showing cartoons, warm amber lighting,
babysitter in armchair absorbed in phone,
cozy blankets, storm muted through windows, calm contrast,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-04-panel-02.png",
        "prompt": """Storyboard panel, close-up insert, teenage babysitter hands and phone,
Pixar animation style, texting completely absorbed, slight smile,
phone screen visible showing text conversation,
oblivious to surroundings, comedic irony,
background blurred, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-04-panel-03.png",
        "prompt": """Storyboard panel, close-up insert, smartphone partially hidden under cushion,
Pixar animation style, phone vibrating with "Gabe Calling" on screen,
no one noticing, dramatic irony, cozy fabric texture around phone,
screen lighting up repeatedly, children's feet visible in soft background,
slow push composition, 16:9 cinematic composition"""
    },

    # Scene 5: EXT. ROAD - NIGHT - TIME WARP (4 panels) - MAJOR VFX
    {
        "filename": "scene-05-panel-01.png",
        "prompt": """Storyboard panel, POV through windshield, MAJOR VFX moment,
Pixar animation style, rain-obscured road then sudden bright FLASH,
massive TIME WARP materializes directly in path,
bright blue spinning vortex (#0096FF), clockwise swirling,
electrical discharge around edges crackling white-blue,
center fading to deep space void, vortex growing rapidly filling view,
rain frozen near vortex, road illuminated blue,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-05-panel-02.png",
        "prompt": """Storyboard panel, medium two-shot interior car, MAJOR VFX,
Pixar animation style, husband and wife screaming in terror,
bright blue time warp light flooding through windshield,
husband gripping wheel bracing, wife hands up defensively,
phone falling from wife's hand, dashboard lights flickering,
camera shake from impact, terror on faces,
blue light washing over them, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-05-panel-03.png",
        "prompt": """Storyboard panel, wide exterior shot, spectacular VFX moment,
Pixar animation style, car entering massive blue TIME WARP,
swirling blue vortex dominating center-right of frame,
car swerving trying to avoid, then consumed by vortex,
car stretching/distorting as it enters portal,
tires screeching visible smoke, electrical discharge,
vortex pulling car in gravitationally, brightest blue at entry point,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-05-panel-04.png",
        "prompt": """Storyboard panel, close-up on vortex edge, VFX detail,
Pixar animation style, car hood being consumed by swirling blue energy,
reality bending at the edge, car metal distorting,
headlights stretching into light trails, electrical arcs,
swirling blue dominates frame, car passing through barrier,
then empty road, rain, darkness remains,
16:9 cinematic composition"""
    },

    # Scene 6: INT. HOUSE - SIMULTANEOUSLY (4 panels)
    {
        "filename": "scene-06-panel-01.png",
        "prompt": """Storyboard panel, wide living room shot, supernatural moment,
Pixar animation style, TV suddenly fizzles with static,
small "poof" of smoke and sparks from TV, not violent explosion,
children and babysitter on couch watching, screen goes black,
blue electrical crackle matching time warp color,
normal domestic scene interrupted by supernatural event,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-06-panel-02.png",
        "prompt": """Storyboard panel, medium group shot, three startled faces,
Pixar animation style, 8-year-old girl alert and scared screen left,
5-year-old boy clutching dinosaur toy center,
teenage babysitter finally looking up from phone screen right,
fear and confusion on all faces, phone light illuminating babysitter,
sudden shock reaction, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-06-panel-03.png",
        "prompt": """Storyboard panel, wide low light, eerie atmosphere,
Pixar animation style, living room now dark lit only by moonlight,
children as silhouettes on couch, babysitter lit by phone glow,
dead TV as dark void in room, cool blue moonlight through windows,
deep unsettling shadows, storm still visible outside,
atmosphere completely changed, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-06-panel-04.png",
        "prompt": """Storyboard panel, close-up insert, supernatural phone glow,
Pixar animation style, smartphone partially hidden under cushion,
GLOWING with bright blue unnatural light matching time warp color,
pulsing light emanating from entire phone not just screen,
child's hand reaching toward it at frame edge,
mysterious supernatural quality, link between worlds established,
16:9 cinematic composition"""
    },

    # Scene 7: INT. GABE'S CAR - DAY (6 panels)
    {
        "filename": "scene-07-panel-01.png",
        "prompt": """Storyboard panel, close-up, woman's face eyes closed then opening,
Pixar animation style, soft warm light not storm light,
dirt and debris on cheek, hair disheveled,
eyes adjusting to light, confusion in expression,
phone visible in her hand, slow awakening,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-07-panel-02.png",
        "prompt": """Storyboard panel, POV from passenger position scanning car,
Pixar animation style, chaos inside crashed car,
debris scattered everywhere, daylight streaming through cracked windshield,
husband slumped against window unconscious visible,
water dripping down glass, smoke wisping from hood,
random items scattered papers toys sunglasses,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-07-panel-03.png",
        "prompt": """Storyboard panel, close-up insert, plastic T-Rex toy on dashboard,
Pixar animation style, dramatically lit by sunlight,
symbolic and ominous in context, foreshadowing,
dashboard debris around it, almost watching the scene,
thematic echo of what's outside, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-07-panel-04.png",
        "prompt": """Storyboard panel, medium two-shot, wife reaching to wake husband,
Pixar animation style, wife screen right leaning toward husband,
husband screen left slumped against steering wheel,
both disheveled from crash, husband has small cut or bruise,
wife's concern visible, bright daylight through windows,
formal wear dirty and mussed, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-07-panel-05.png",
        "prompt": """Storyboard panel, POV from car looking through window,
Pixar animation style, LUSH tropical prehistoric vegetation visible,
through dirty cracked window, massive fern leaves,
strange flowers, humid atmosphere visible,
definitely NOT suburban America, wonder building,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-07-panel-06.png",
        "prompt": """Storyboard panel, wide landscape shot through car window,
Pixar animation style, full reveal of JURASSIC SWAMP,
lush prehistoric vegetation, giant ferns twice car height,
exotic unknown flowers, humid steam rising,
water visible between plants, cycads and tree ferns,
warm golden-green light, primordial beauty,
no sign of civilization, prehistoric world reveal,
16:9 cinematic composition"""
    },

    # Scene 8: EXT. JURASSIC SWAMP - DAY (9 panels) - MAJOR VFX
    {
        "filename": "scene-08-panel-01.png",
        "prompt": """Storyboard panel, wide establishing shot, crane down composition,
Pixar animation style, formal couple stepping out of crashed car into swamp,
man in rumpled tuxedo woman in disheveled black dress,
car center clearly damaged, steam from hood,
prehistoric plants dwarf them, overwhelming scale,
small time warp and weird creature visible unnoticed in background,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-08-panel-02.png",
        "prompt": """Storyboard panel, POV handheld exploring, sense of wonder,
Pixar animation style, looking around at prehistoric plants,
giant fern fronds, unusual flowering plants,
large dragonflies, steam and mist in air,
beautiful but alien environment, humid atmosphere,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-08-panel-03.png",
        "prompt": """Storyboard panel, medium shot, nearly-closed TIME WARP,
Pixar animation style, small backpack-sized blue swirling vortex,
WEIRD CREATURE investigating it curiously (chicken-dog-lizard hybrid),
cute colorful creature cat-sized sniffing at fading portal,
parents visible in background not noticing,
first glimpse of future Jetplane character,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-08-panel-04.png",
        "prompt": """Storyboard panel, close-up ground level, Jurassic Park homage,
Pixar animation style, puddle of water with ripples forming,
small stones vibrating, leaves trembling,
muddy ground with debris vibrating, something big approaching,
classic dinosaur approach signal, ominous,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-08-panel-05.png",
        "prompt": """Storyboard panel, medium shot, cute creature FREEZING in fear,
Pixar animation style, chicken-dog-lizard hybrid eyes widening,
looking toward source of rumbling, then scuttling away rapidly,
time warp nearly invisible now fading, animal panic behavior,
the creature knows what's coming, ominous stillness,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-08-panel-06.png",
        "prompt": """Storyboard panel, wide HERO SHOT, T-REX REVEAL, MAJOR VFX,
Pixar animation style, massive T-Rex emerging through trees,
realistic coloring earth tones browns grays, NOT cartoonish,
40+ feet tall, predatory intelligent eyes,
formal couple small in frame left backs to us,
car between them and T-Rex, trees parting,
dramatic backlighting sun behind T-Rex creating silhouette,
terrifying scale contrast humans tiny vs dinosaur massive,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-08-panel-07.png",
        "prompt": """Storyboard panel, close-up, T-Rex head filling frame,
Pixar animation style, textured skin detail, terrifying,
eye with predatory intelligence, nostrils flaring sniffing,
teeth visible, head tilting investigating,
prehistoric beauty and terror combined,
humans possibly reflected in eye, slight sway movement,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-08-panel-08.png",
        "prompt": """Storyboard panel, low angle, T-Rex destroying car,
Pixar animation style, massive dinosaur foot/tail crushing car,
car crumpling like tin can, glass shattering,
debris flying, T-Rex dominating frame from above,
scale comparison foot bigger than car roof,
destruction spectacle, car alarm dying mid-crush,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-08-panel-09.png",
        "prompt": """Storyboard panel, medium tracking shot, couple running for lives,
Pixar animation style, wife slightly ahead husband right behind,
formal attire being destroyed by jungle, torn and muddy,
wife's heels problematic, both crashing through vegetation,
T-Rex visible pursuing behind demolishing everything,
sweat and fear on faces, pure terror and survival,
16:9 cinematic composition"""
    },

    # Scene 9: EXT. JURASSIC DENSE BRUSH - DAY (7 panels) - ACTION
    {
        "filename": "scene-09-panel-01.png",
        "prompt": """Storyboard panel, steadicam chase shot from behind,
Pixar animation style, formal couple crashing through giant ferns,
T-Rex visible in background gaining, crashing through,
wife's dress torn, husband's jacket abandoned/torn,
human-height ferns being pushed aside, ground uneven puddles splashing,
dust and debris flying, full sprint survival,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-09-panel-02.png",
        "prompt": """Storyboard panel, POV over shoulder looking back while running,
Pixar animation style, T-Rex MUCH closer than expected,
massive scale, mouth open roaring, trees falling like dominoes,
ground trembling camera shake, terrifyingly close,
swath of destruction behind, handheld energy,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-09-panel-03.png",
        "prompt": """Storyboard panel, wide shot, T-Rex CRASHING through jungle,
Pixar animation style, trees snapping like twigs,
ferns exploding outward, debris flying all directions,
birds and creatures fleeing, dust cloud rising,
T-Rex barely slowed, raw destructive power,
formal couple as small figures running at frame edge,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-09-panel-04.png",
        "prompt": """Storyboard panel, medium shot shock cut, NEW THREAT,
Pixar animation style, SECOND DINOSAUR blocking escape route,
Carnotaurus or similar carnivore, different coloring from T-Rex,
head lowered ready to charge, aggressive posture,
formal couple skidding to stop in front of it,
hollow tree visible behind dinosaur was their goal,
surrounded trapped feeling, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-09-panel-05.png",
        "prompt": """Storyboard panel, medium tracking alongside, comedy in chaos,
Pixar animation style, husband and wife running in profile,
both arguing while fleeing for lives, married couple dynamics,
exertion on faces, clothes in tatters,
occasional glance back, comedic despite mortal danger,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-09-panel-06.png",
        "prompt": """Storyboard panel, POV quick pan locking onto salvation,
Pixar animation style, desperate scan then CAVE ENTRANCE spotted,
dark cave opening in rocky hillside,
just big enough for humans, too small for T-Rex,
vegetation around entrance, hope amid terror,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-09-panel-07.png",
        "prompt": """Storyboard panel, tracking into cave entrance,
Pixar animation style, wife grabbing husband's suit collar,
yanking him toward cave, physical comedy of the pull,
both diving/sliding into cave darkness,
T-Rex massive foot/head arriving just as they get in,
barely made it, T-Rex frustrated at entrance,
16:9 cinematic composition"""
    },

    # Scene 10: INT. JURASSIC CAVE - DAY (7 panels) - EMOTIONAL CLIMAX
    {
        "filename": "scene-10-panel-01.png",
        "prompt": """Storyboard panel, wide cave interior establishing,
Pixar animation style, light streaming from entrance,
formal couple just tumbled in on ground catching breath,
T-Rex head visible at entrance too big to fit,
cave walls rough and dark, dust particles in light cone,
momentary safety, disheveled dirty exhausted,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-10-panel-02.png",
        "prompt": """Storyboard panel, close-up insert, T-Rex claws at cave entrance,
Pixar animation style, massive claws scraping rock,
trying to reach in, light blocked when claw fills entrance,
rock scraping creating sparks, detailed claw texture,
just barely out of reach, primal terror,
frustrated ROAR implied, 16:9 cinematic composition"""
    },
    {
        "filename": "scene-10-panel-03.png",
        "prompt": """Storyboard panel, medium two-shot, intimate framing,
Pixar animation style, husband and wife huddled together,
inching back from entrance pressed against cave wall,
wife clutching husband, husband arm around wife,
formal wear destroyed, dirt sweat cuts visible,
terror but also connection, holding each other,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-10-panel-04.png",
        "prompt": """Storyboard panel, wide interior reacting to sounds,
Pixar animation style, couple looking toward entrance,
light at entrance flickering shadows moving,
dust falling from ceiling from impacts,
dinosaur battle happening outside heard not seen,
faces reacting to sounds of massive combat,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-10-panel-05.png",
        "prompt": """Storyboard panel, close-up, wife's face transformation,
Pixar animation style, fear transforming to determination,
dirt on face, hair disheveled, eyes sharp and focused,
jaw set, strength emerging, cave lighting dramatic,
mama bear energy, resolve forming,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-10-panel-06.png",
        "prompt": """Storyboard panel, tight two-shot, EMOTIONAL GUT-PUNCH,
Pixar animation style, husband and wife faces close,
the moment they remember THE KIDS, horror dawning,
fear transforms to different kind of horror, parental anguish,
eyes meeting, realization hitting, everything else forgotten,
most emotional beat of Act 1,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-10-panel-07.png",
        "prompt": """Storyboard panel, close-up insert, HOPE OBJECT,
Pixar animation style, wife's dirty hand holding phone,
phone possibly showing static or glitch on screen,
wedding ring visible on finger, symbolic,
the device that links both worlds,
phone equals hope, end of Act 1 image,
couple's faces visible at top of frame looking down,
16:9 cinematic composition"""
    },
]


def generate_image(prompt: str, filename: str, retry_count: int = 3) -> bool:
    """Generate a single image using Gemini 2.0 Flash."""
    output_path = OUTPUT_DIR / filename

    # Skip if already exists
    if output_path.exists():
        print(f"  ⊘ Skipping (exists): {filename}")
        return True

    print(f"Generating: {filename}")
    print(f"  Prompt: {prompt[:100]}...")

    for attempt in range(retry_count):
        try:
            # Use Gemini 2.0 Flash with native image generation
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
                    print(f"  ✓ Saved to {output_path}")
                    return True

            print(f"  ✗ No image in response (attempt {attempt + 1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(5)

        except Exception as e:
            print(f"  ✗ Error (attempt {attempt + 1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(5)

    return False


def main():
    """Generate remaining Act 1 storyboard panels (Scenes 2-10)."""
    print("=" * 60)
    print("Generating Act 1 Storyboard Panels (Scenes 2-10)")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Total panels: {len(ACT1_REMAINING_PANELS)}")
    print()

    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set")
        return 1

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(ACT1_REMAINING_PANELS)

    # Optional: specify start/end index via command line args
    start_idx = 0
    end_idx = total
    if len(sys.argv) > 1:
        start_idx = int(sys.argv[1])
    if len(sys.argv) > 2:
        end_idx = int(sys.argv[2])

    panels_to_generate = ACT1_REMAINING_PANELS[start_idx:end_idx]

    for i, panel in enumerate(panels_to_generate, start_idx + 1):
        print(f"\n[{i}/{total}] ", end="")
        if generate_image(panel["prompt"], panel["filename"]):
            success_count += 1

        # Delay between requests to avoid rate limiting
        if i < end_idx:
            time.sleep(3)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{len(panels_to_generate)} images generated")
    print("=" * 60)

    return 0 if success_count == len(panels_to_generate) else 1


if __name__ == "__main__":
    sys.exit(main())
