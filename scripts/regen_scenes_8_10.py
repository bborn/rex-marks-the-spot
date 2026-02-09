#!/usr/bin/env python3
"""Regenerate off-model storyboard panels for Scenes 8-10.

Uses approved character turnarounds as image references with Gemini
to ensure character consistency across all panels.
"""

import os
import sys
import time
from pathlib import Path
from PIL import Image

from google import genai
from google.genai import types

# Configuration
MODEL = "gemini-2.0-flash-exp-image-generation"
OUTPUT_DIR = Path(__file__).parent.parent / "tmp" / "regen"
TURNAROUND_DIR = Path(__file__).parent.parent / "tmp" / "turnarounds"

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Character descriptions matching approved turnarounds
GABE_DESC = (
    "Gabe: Pixar/Disney 3D animated style man, late 30s, dark brown wavy hair, "
    "rectangular dark-framed glasses (MUST have glasses), five o'clock shadow stubble, "
    "warm brown eyes, stocky/slightly soft build (NOT muscular), "
    "wearing a torn/disheveled white dress shirt with loosened dark blue tie "
    "(formal date night outfit now damaged from running through jungle)"
)

NINA_DESC = (
    "Nina: Pixar/Disney 3D animated style woman, late 30s, shoulder-length auburn/reddish-brown "
    "wavy hair, green eyes, freckles, heart-shaped face, "
    "wearing a torn/disheveled burgundy knee-length cocktail dress "
    "(formal date night outfit now damaged from running through jungle), "
    "strappy gold heels (or barefoot if lost them)"
)

STYLE_PREFIX = (
    "Pixar/Disney 3D animated movie still, high quality CG rendering, "
    "cinematic lighting, 16:9 aspect ratio widescreen, movie screenshot look. "
    "Characters must match the provided reference turnaround sheets EXACTLY "
    "for face shape, hair, and proportions. "
)

JETPLANE_DESC = (
    "A cute chicken-dog-lizard hybrid creature, cat-sized, with teal-green scales, "
    "an orange feathered ruff/crest on its head, large amber eyes, curious expression. "
    "Pixar/Disney 3D animated style."
)

# Panels to regenerate with detailed prompts
PANELS = [
    {
        "id": "scene-08-panel-01",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "WIDE ESTABLISHING SHOT from high angle craning down. "
            "Lush prehistoric Jurassic swamp environment with massive ferns, cycads, misty atmosphere. "
            f"{GABE_DESC} {NINA_DESC} "
            "Both stepping out of a crashed sedan in the center of frame. Nina exits passenger side looking awestruck. "
            "Gabe struggles from driver side mid-sentence. Car has steam/smoke from hood. "
            "The prehistoric plants dwarf them. Dark jungle green palette with golden sunlight. "
            "Cinematic, sense of scale and wonder."
        ),
    },
    {
        "id": "scene-08-panel-03",
        "refs": ["jetplane"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "MEDIUM SHOT, static camera. "
            "A nearly-closed TIME WARP portal (small backpack-sized, blue swirling energy, fading/crackling) floating center-left of frame. "
            f"{JETPLANE_DESC} The creature is center-right, sniffing curiously at the portal. "
            "In the background, slightly blurred, two human figures (man and woman in formal wear) visible but haven't noticed the creature. "
            "Lush Jurassic swamp vegetation. Misty atmosphere."
        ),
    },
    {
        "id": "scene-08-panel-05",
        "refs": ["jetplane"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "MEDIUM SHOT, static camera. "
            f"{JETPLANE_DESC} The creature is center frame, FROZEN in fear - eyes wide, body tense. "
            "It's about to scuttle away rapidly. The fading time warp portal (tiny, nearly invisible blue glow) visible behind it. "
            "Dark, ominous forest background. Sense of something dangerous approaching. "
            "The creature senses the T-Rex before anyone else."
        ),
    },
    {
        "id": "scene-08-panel-06",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "WIDE HERO SHOT - THE T-REX REVEAL. A massive 40-foot T-Rex emerges through parting trees on the right side. "
            "Earth-tone coloring (browns/grays), realistic predatory eyes, terrifying but not cartoonish. "
            "Dramatic backlighting with sun behind creating silhouette effect, steam/mist. "
            f"{GABE_DESC} {NINA_DESC} "
            "Both characters small in frame on the left, backs partially to camera, frozen in terror. "
            "Their crashed car visible between them and the T-Rex. "
            "Dramatic lighting, dark jungle green with golden highlights."
        ),
    },
    {
        "id": "scene-08-panel-09",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "MEDIUM TRACKING SHOT, steadicam following characters. "
            f"{NINA_DESC} Nina is slightly ahead, running desperately, her burgundy dress torn and muddy. "
            f"{GABE_DESC} Gabe is right behind her, tie flapping, shirt ripped. "
            "Both crashing through dense prehistoric ferns and vegetation. "
            "Sweat and fear on their faces. T-Rex visible in background demolishing trees as it pursues. "
            "Dramatic jungle chase, green vegetation, motion blur on background."
        ),
    },
    {
        "id": "scene-09-panel-01",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "STEADICAM CHASE SHOT from behind the characters. "
            f"{NINA_DESC} Nina running screen right, slightly ahead. "
            f"{GABE_DESC} Gabe running screen left, just behind. "
            "Both crashing through massive prehistoric ferns (human height+). "
            "T-Rex visible behind them gaining ground. "
            "Dense jungle, ground uneven with puddles splashing. Torn formal wear, pure terror. "
            "Motion and urgency in every element."
        ),
    },
    {
        "id": "scene-09-panel-04",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "MEDIUM SHOT, static camera. SHOCK moment. "
            "A SECOND DINOSAUR (Carnotaurus-type, smaller than T-Rex but still terrifying, "
            "warm red/orange coloring, head lowered aggressively) blocks the escape path. "
            f"{GABE_DESC} Gabe skidding to a stop in center frame. "
            f"{NINA_DESC} Nina colliding into him from behind. "
            "Both facing the new dinosaur threat. A hollow tree visible behind the dinosaur (was their goal). "
            "Dense jungle clearing. Shock and horror on their faces."
        ),
    },
    {
        "id": "scene-09-panel-05",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "MEDIUM TWO-SHOT, tracking alongside at running pace. "
            f"{NINA_DESC} Nina screen left, profile view, running and yelling at Gabe while fleeing. "
            f"{GABE_DESC} Gabe screen right, profile view, running and arguing back. "
            "Both in profile, running side by side. Formal wear in tatters, exhausted but still arguing. "
            "Comedy beat - married couple dynamics under extreme stress. "
            "Jungle blurring past. Dinosaur sounds implied."
        ),
    },
    {
        "id": "scene-09-panel-06",
        "refs": ["nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "POV SHOT from Nina's perspective. Quick pan to the right revealing a CAVE ENTRANCE "
            "in a rocky hillside. The cave opening is dark, just big enough for humans, "
            "hopefully too small for a T-Rex. "
            "Nina's hand visible at edge of frame reaching toward it. "
            "Rocky terrain, prehistoric vegetation. Desperate hope. Light focused on cave entrance."
        ),
    },
    {
        "id": "scene-09-panel-07",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "TRACKING SHOT following into cave entrance. "
            f"{NINA_DESC} Nina is grabbing Gabe by his suit collar, yanking him toward the cave. "
            f"{GABE_DESC} Gabe being pulled, stumbling. Physical comedy of the pull. "
            "They're diving/sliding into the dark cave entrance. "
            "Behind them, the T-Rex is arriving at the entrance, frustrated. "
            "Dramatic contrast between bright jungle light and dark cave. Action moment."
        ),
    },
    {
        "id": "scene-10-panel-01",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "WIDE ESTABLISHING SHOT of cave interior. Momentary safety. "
            "Light streams from the entrance creating dramatic god-rays, dust particles visible. "
            "Cave walls rough and dark, extending deeper into darkness. "
            f"{NINA_DESC} Nina on the ground center-left, catching her breath. "
            f"{GABE_DESC} Gabe on the ground center-right, looking toward the entrance. "
            "T-Rex silhouette visible at the cave entrance, too large to enter. "
            "Cave gray palette with amber light from entrance."
        ),
    },
    {
        "id": "scene-10-panel-03",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "MEDIUM TWO-SHOT with slow push-in framing. "
            f"{NINA_DESC} Nina screen left, clutching Gabe, face showing fear but also connection. "
            "Her auburn wavy hair is disheveled, dirt and scratches on her face. "
            f"{GABE_DESC} Gabe screen right, arm protectively around Nina, glasses slightly askew. "
            "Stubble, sweat, and dirt on his face. "
            "Both pressed against the cave wall, huddled together. "
            "Dramatic cave lighting - amber from entrance on one side, dark shadows on other. "
            "Terror but also love and connection between them. Torn formal wear."
        ),
    },
    {
        "id": "scene-10-panel-04",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "WIDE SHOT inside cave, static camera. "
            f"{NINA_DESC} and {GABE_DESC} "
            "Both sitting against cave wall, looking toward the entrance with wide eyes. "
            "Light at the entrance is flickering - large shadows moving across it (dinosaurs fighting outside). "
            "Dust falling from cave ceiling from impacts. "
            "The characters are reacting to TERRIFYING SOUNDS of a dinosaur battle outside. "
            "Dark cave interior, dramatic shadow play. Fear and tension."
        ),
    },
    {
        "id": "scene-10-panel-05",
        "refs": ["nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "CLOSE-UP of Nina's face filling the frame. "
            f"{NINA_DESC} "
            "Her face shows DETERMINATION replacing fear. Auburn wavy hair disheveled. "
            "Dirt, scratches, sweat on her face. Freckles visible. Green eyes sharp and focused. "
            "Jaw set with strength. She knows what they need to do. "
            "Dramatic cave lighting - warm amber on one side of face, cool shadows on other. "
            "Powerful emotional moment. She's transitioning from victim to protector."
        ),
    },
    {
        "id": "scene-10-panel-06",
        "refs": ["gabe", "nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "CLOSE TWO-SHOT - EMOTIONAL CLIMAX of Act 1. "
            f"{NINA_DESC} Nina screen left. {GABE_DESC} Gabe screen right. "
            "Both faces visible in intimate close-up. "
            "Their expressions transform from fear to a DIFFERENT kind of horror - "
            "they've just remembered their KIDS are home alone. "
            "Parental anguish and realization. Eyes meeting. "
            "Nina: auburn wavy hair, green eyes, freckles. Gabe: glasses, stubble. "
            "Cave lighting, emotional devastation on their faces. This is the gut-punch moment."
        ),
    },
    {
        "id": "scene-10-panel-07",
        "refs": ["nina"],
        "prompt": (
            f"{STYLE_PREFIX} "
            "CLOSE-UP INSERT of a smartphone held in a woman's dirty hand. "
            "Nina's hand (with wedding ring visible, gold band) gripping the phone tightly. "
            "Phone screen shows a glitchy/static display with faint blue glow (matching portal color). "
            "The phone is their HOPE - their connection back through the portal. "
            "In the blurred background, both Nina and Gabe's faces visible looking at the phone. "
            "Cave setting, dramatic lighting on the phone screen. "
            "The blue phone glow matches the portal blue, creating visual connection between worlds."
        ),
    },
]


def load_turnaround(character: str) -> Image.Image:
    """Load an approved character turnaround sheet."""
    path = TURNAROUND_DIR / f"{character}_turnaround_APPROVED.png"
    if not path.exists():
        print(f"WARNING: Turnaround not found for {character} at {path}")
        return None
    img = Image.open(path)
    print(f"  Loaded {character} turnaround: {img.size}")
    return img


def generate_panel(panel: dict, turnarounds: dict) -> bool:
    """Generate a single panel using turnarounds as references."""
    panel_id = panel["id"]
    output_path = OUTPUT_DIR / f"{panel_id}.png"

    print(f"\n{'='*60}")
    print(f"Generating: {panel_id}")
    print(f"  Refs: {panel['refs']}")

    # Build content parts with reference images
    parts = []
    for ref in panel["refs"]:
        if ref in turnarounds and turnarounds[ref] is not None:
            img = turnarounds[ref]
            parts.append(img)
            parts.append(f"Above is the approved character turnaround for {ref.title()}. "
                        f"The character in the generated image MUST match this reference exactly "
                        f"for face shape, hair style/color, body proportions, and overall design.")

    parts.append(f"Now generate this storyboard panel: {panel['prompt']}")

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=parts,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img_bytes = part.inline_data.data
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                size_kb = len(img_bytes) / 1024
                print(f"  SUCCESS: {output_path.name} ({size_kb:.0f} KB)")
                return True

        # Check for text response
        for part in response.candidates[0].content.parts:
            if part.text:
                print(f"  Text response: {part.text[:200]}")

        print(f"  FAILED: No image in response")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Scenes 8-10 Character-Locked Panel Regeneration")
    print(f"Model: {MODEL}")
    print(f"Panels to regenerate: {len(PANELS)}")
    print("=" * 60)

    # Load turnarounds
    print("\nLoading approved turnarounds...")
    turnarounds = {
        "gabe": load_turnaround("gabe"),
        "nina": load_turnaround("nina"),
    }
    # Jetplane doesn't have a turnaround yet, will use text description only
    turnarounds["jetplane"] = None

    # Filter to specific panels if args provided
    panels_to_gen = PANELS
    if len(sys.argv) > 1:
        ids = sys.argv[1:]
        panels_to_gen = [p for p in PANELS if p["id"] in ids]
        print(f"\nFiltered to {len(panels_to_gen)} panels: {[p['id'] for p in panels_to_gen]}")

    success = 0
    failed = []
    total = len(panels_to_gen)

    for i, panel in enumerate(panels_to_gen, 1):
        print(f"\n[{i}/{total}]", end="")
        if generate_panel(panel, turnarounds):
            success += 1
        else:
            failed.append(panel["id"])

        # Rate limiting - 10 second delay between requests
        if i < total:
            print("  Waiting 10s for rate limit...")
            time.sleep(10)

    print("\n" + "=" * 60)
    print(f"Complete: {success}/{total} panels generated")
    if failed:
        print(f"Failed: {failed}")
    print("=" * 60)

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
