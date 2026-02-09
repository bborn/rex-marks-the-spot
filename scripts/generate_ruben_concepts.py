#!/usr/bin/env python3
"""
Generate 4 Ruben concept variations for director review.
Director feedback: Too Nordic/fit in V1, still not right V2.
Want: balding, jovial but droopy, big hands, Eastern European working man.
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "characters" / "ruben" / "concepts"

STYLE_BASE = """Pixar-style 3D animated character design, professional concept art,
full body standing character on clean white background,
warm appealing design suitable for family animation,
high quality render, character design for animated film.
The character has small translucent purple-blue fairy wings on his back that droop downward sadly.
He has oversized working-man hands. Eastern European descent features."""

CONCEPTS = {
    "ruben_concept_A": {
        "label": "A) BALD SUPERINTENDENT",
        "prompt": f"""{STYLE_BASE}

CHARACTER: Ruben - Fairy Godfather (Bald Superintendent variant)
A washed-up fairy godfather who looks like a building superintendent.
Completely bald on top with a horseshoe pattern of gray hair around the sides.
Round soft face, stocky barrel-chested build with a big gut/belly.
Tired droopy eyes with dark circles, warm but exhausted expression.
Simple dark blue work uniform (custodian/super style), regular black work shoes.
Small translucent purple fairy wings drooping sadly behind him.
Big thick working hands, meaty fingers.
About 5'8", hunched posture, looks like he hasn't slept well in years.
Eastern European working man features - broad nose, heavy brow.

Label at bottom: "A) BALD SUPERINTENDENT"
Full body view, front-facing, clean white background."""
    },
    "ruben_concept_B": {
        "label": "B) BALDING HANDYMAN",
        "prompt": f"""{STYLE_BASE}

CHARACTER: Ruben - Fairy Godfather (Balding Handyman variant)
A washed-up fairy godfather who looks like a neighborhood handyman.
Receding hairline with thinning gray-brown hair, visible scalp on top.
Soft round face with perpetual stubble, friendly tired smile.
Bigger build with a gut, broad shoulders, barrel body.
Red-and-black flannel shirt, brown tool vest with pockets, beat-up gray sneakers.
Small translucent purple fairy wings drooping behind him.
Prominent large hands, thick fingers that look like they fix things.
About 5'9", slightly slouched posture.
Eastern European features - wide face, heavy-lidded tired eyes with dark circles.

Label at bottom: "B) BALDING HANDYMAN"
Full body view, front-facing, clean white background."""
    },
    "ruben_concept_C": {
        "label": "C) OLDER WORKING MAN",
        "prompt": f"""{STYLE_BASE}

CHARACTER: Ruben - Fairy Godfather (Older Working Man variant)
A washed-up fairy godfather who looks like a retired Eastern European laborer.
Nearly bald with just a ring of short gray hair around the sides, shiny dome.
Heavier set, softer body, round belly, thick limbs.
Wrinkled tired face but with jovial laugh lines, bushy gray eyebrows.
Simple light blue button-down shirt (slightly rumpled), brown work pants, brown slip-on shoes.
Very droopy small translucent purple fairy wings behind him, almost touching the ground.
Eastern European working man features - wide face, prominent nose, jowly cheeks.
Big weathered hands with thick knuckles.
About 5'7", stooped posture, looks jovial but bone-tired.

Label at bottom: "C) OLDER WORKING MAN"
Full body view, front-facing, clean white background."""
    },
    "ruben_concept_D": {
        "label": "D) PORTLY MAINTENANCE",
        "prompt": f"""{STYLE_BASE}

CHARACTER: Ruben - Fairy Godfather (Portly Maintenance variant)
A washed-up fairy godfather who looks like a building maintenance worker.
Balding with gray hair on the sides, thin wispy strands on top.
Rounder fuller figure, prominent belly, soft all over.
Tired but kind face, gentle eyes with heavy bags, slight warm smile.
Gray-green maintenance uniform with name patch, comfortable black shoes.
Small droopy translucent purple fairy wings behind him, barely visible.
Big meaty hands, pudgy fingers.
About 5'8", world-weary but warm presence.
Eastern European descent - broad face, thick neck, heavy features softened by kindness.

Label at bottom: "D) PORTLY MAINTENANCE"
Full body view, front-facing, clean white background."""
    },
}


def generate_concept(key: str, info: dict) -> bool:
    """Generate a single concept image."""
    filename = f"{key}.png"
    output_path = OUTPUT_DIR / filename

    if output_path.exists():
        print(f"  Skipping {filename} (exists)")
        return True

    print(f"Generating: {info['label']}")

    try:
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=f"Generate an image: {info['prompt']}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"  Saved: {output_path}")
                return True

        print(f"  No image in response")
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.text:
                    print(f"  Text response: {part.text[:200]}")
        return False

    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    success = 0

    for key, info in CONCEPTS.items():
        total += 1
        if generate_concept(key, info):
            success += 1
        if total < len(CONCEPTS):
            print("  Waiting 10s for rate limit...")
            time.sleep(10)

    print(f"\nComplete: {success}/{total} images generated")
    print(f"Output: {OUTPUT_DIR}")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
