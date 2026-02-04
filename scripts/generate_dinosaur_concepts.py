#!/usr/bin/env python3
"""
Dinosaur Species Concept Art Generator

Generates concept art for additional dinosaur species in "Fairy Dinosaur Date Night"
using Google Gemini image generation.

Species to generate:
1. Friendly herbivore herd (2-3 variations)
2. Comical pterodactyls (2-3 variations)
3. Imposing but family-friendly T-Rex (2-3 variations)
4. Bioluminescent creatures (2-3 variations)

Usage:
    python scripts/generate_dinosaur_concepts.py

Requires GEMINI_API_KEY environment variable.
"""

import os
import sys
import base64
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# Dinosaur concept prompts - Pixar style, family-friendly
DINOSAUR_PROMPTS = {
    "herbivore_herd": {
        "description": "Friendly herbivore dinosaur herd",
        "variations": [
            {
                "name": "gentle_brachiosaurus_family",
                "prompt": """Pixar 3D animation style creature design, friendly family of Brachiosaurus dinosaurs,
                gentle giants with warm brown eyes and expressive faces, long graceful necks,
                soft sage green scales with cream-colored underbellies, small smile expressions,
                a parent pair with two baby Brachiosaurus, family-friendly appearance,
                lush prehistoric jungle background, warm golden sunlight filtering through trees,
                cute proportions, round features, appealing to children ages 6+,
                professional animation studio quality, Dreamworks/Pixar aesthetic"""
            },
            {
                "name": "playful_triceratops_group",
                "prompt": """Pixar 3D animation style creature design, group of playful Triceratops dinosaurs,
                friendly expressions with big kind eyes, rounded horn shapes (not sharp),
                warm terracotta orange and cream color scheme, spotted patterns,
                one adult showing patience, two juveniles playing together, one baby following mom,
                prehistoric meadow with giant ferns, soft diffused lighting,
                adorable proportions, huggable appearance, family-friendly design,
                professional character concept art, toyetic and merchandise-ready"""
            },
            {
                "name": "peaceful_parasaurolophus_herd",
                "prompt": """Pixar 3D animation style creature design, peaceful herd of Parasaurolophus dinosaurs,
                distinctive head crests glowing softly with bioluminescent patterns,
                elegant blue-purple gradient coloring with iridescent highlights,
                gentle doe-like eyes, graceful movements, musical appearance,
                herd of 5 dinosaurs of varying sizes, family grouping,
                misty prehistoric lakeside setting, magical twilight atmosphere,
                appealing stylized design, friendly and approachable,
                professional animation quality, suitable for family film"""
            }
        ]
    },

    "pterodactyls": {
        "description": "Comical pterodactyls",
        "variations": [
            {
                "name": "overprotective_pterodactyl_parents",
                "prompt": """Pixar 3D animation style creature design, comically overprotective Pterodactyl parents,
                exaggerated worried expressions, one parent squawking dramatically,
                other parent puffing up protectively over a large speckled egg,
                bright orange and teal feathered wings with comedic proportions,
                oversized beaky faces with googly anxious eyes,
                huge wingspan but stubby awkward bodies,
                nesting on top of a crushed car roof (comedic juxtaposition),
                very expressive, slapstick potential, family-friendly humor,
                professional animation character design, Dreamworks comedy style"""
            },
            {
                "name": "clumsy_pterodactyl_duo",
                "prompt": """Pixar 3D animation style creature design, pair of clumsy Pterodactyls,
                one tall and skinny, one short and round (classic comedy duo),
                silly expressions with crossed eyes and dopey grins,
                purple and yellow coloring with mismatched patterns,
                tangled together mid-flight in a comedic pose,
                exaggerated cartoon features, rubber-hose style flexibility,
                big expressive eyes, small useless-looking teeth,
                prehistoric sky background with fluffy clouds,
                maximum comedic appeal, slapstick animation potential,
                professional character concept art"""
            },
            {
                "name": "dramatic_pterodactyl_screamer",
                "prompt": """Pixar 3D animation style creature design, dramatically screaming Pterodactyl,
                mouth wide open in an over-the-top theatrical screech,
                eyes bulging comedically, wings spread in exaggerated shock,
                vibrant red and gold plumage like an opera singer,
                small fancy crest that looks like a toupee,
                pose suggesting it's reacting to something mundane,
                theatrical dramatic lighting for comedic effect,
                expressive cartoony features, meme-worthy expression,
                professional animation quality, designed for comedic moments"""
            }
        ]
    },

    "t_rex": {
        "description": "Imposing but family-friendly T-Rex",
        "variations": [
            {
                "name": "stern_but_fair_t_rex",
                "prompt": """Pixar 3D animation style creature design, imposing but family-friendly Tyrannosaurus Rex,
                massive and powerful but with readable, intelligent eyes,
                deep forest green scales with darker stripe patterns,
                stern expression like a strict teacher, not malicious,
                tiny arms held in an almost dignified pose,
                impressive size and presence but approachable design,
                strong jaw with teeth visible but not gruesome,
                standing tall in dramatic prehistoric landscape,
                powerful but not terrifying, respected antagonist design,
                professional animation character, suitable for ages 6+"""
            },
            {
                "name": "frustrated_hungry_t_rex",
                "prompt": """Pixar 3D animation style creature design, frustrated hungry T-Rex,
                comically frustrated expression, eyebrows furrowed,
                rumbling stomach suggested by expression, hangry but not scary,
                dark charcoal gray and burgundy coloring,
                small arms reaching futilely toward something just out of reach,
                sympathetic villain design - you almost feel bad for it,
                massive but with relatable body language,
                dramatic jungle background with crushed vegetation,
                imposing scale but with comedic undertones,
                professional family film antagonist design"""
            },
            {
                "name": "territorial_mama_t_rex",
                "prompt": """Pixar 3D animation style creature design, territorial mother T-Rex,
                protective fierce expression but with maternal warmth in eyes,
                earthy brown and amber coloring with subtle feathering details,
                powerful stance guarding her territory,
                visible strength but also visible care,
                one small T-Rex baby peeking from behind her leg,
                adds sympathy to the antagonist - she's protecting family too,
                dramatic prehistoric swamp setting,
                imposing but understandable motivations visible in design,
                professional animation quality, nuanced villain design"""
            }
        ]
    },

    "bioluminescent": {
        "description": "Bioluminescent prehistoric creatures",
        "variations": [
            {
                "name": "glowing_night_raptors",
                "prompt": """Pixar 3D animation style creature design, pack of small bioluminescent raptors,
                sleek bodies with glowing teal and purple patterns,
                stripe patterns that pulse and glow in the dark,
                curious cat-like behavior, tilted heads, alert ears,
                large reflective eyes that glow gold in the dark,
                feathered bodies with luminescent tips,
                pack of 4-5 creatures in nighttime prehistoric forest,
                magical and mysterious but not scary,
                firefly-like quality, enchanting rather than threatening,
                professional fantasy creature design, family-friendly"""
            },
            {
                "name": "luminous_aquatic_plesiosaur",
                "prompt": """Pixar 3D animation style creature design, friendly bioluminescent Plesiosaur,
                graceful long neck with swirling glow patterns,
                soft blue and seafoam green coloring with white light spots,
                gentle giant appearance with kind curious eyes,
                flippers that trail glowing particles in water,
                peaceful expression, almost mystical presence,
                emerging from prehistoric lake at twilight,
                reflection showing beautiful light patterns,
                magical and serene, like an underwater aurora,
                professional animation creature design, wonder-inspiring"""
            },
            {
                "name": "glowing_jellyfish_pterosaur",
                "prompt": """Pixar 3D animation style creature design, small flying creatures resembling
                a mix of pterosaur and jellyfish, translucent glowing wings,
                soft pink and purple bioluminescence throughout body,
                trailing tendrils that glow and sparkle,
                school of 6-8 creatures flying together like lanterns,
                cute small faces with tiny beaks, oversized curious eyes,
                nighttime prehistoric sky with stars visible,
                magical floating feeling, ethereal and beautiful,
                whimsical fantasy design, children would love these,
                professional concept art for animated film"""
            }
        ]
    }
}


def generate_with_gemini_image(prompt: str, output_path: Path, api_key: str) -> bool:
    """Generate image using Gemini's image generation model."""
    try:
        import google.generativeai as genai
    except ImportError:
        print("ERROR: google-generativeai not installed")
        return False

    try:
        genai.configure(api_key=api_key)

        # Use the dedicated image generation model (nano-banana or gemini-2.5-flash-image)
        model_name = 'gemini-2.5-flash-image'

        print(f"  Generating with {model_name}...")

        model = genai.GenerativeModel(model_name)

        # Generate the image with proper config
        response = model.generate_content(
            f"Generate an image: {prompt}",
            generation_config={
                "response_modalities": ["IMAGE", "TEXT"],
            }
        )

        # Save the image
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    print(f"  Saved: {output_path}")
                    return True

        print(f"  No image data in response")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        # Try alternative model
        return generate_with_nano_banana(prompt, output_path, api_key)


def generate_with_nano_banana(prompt: str, output_path: Path, api_key: str) -> bool:
    """Generate image using nano-banana-pro-preview model."""
    try:
        import google.generativeai as genai
    except ImportError:
        return False

    try:
        genai.configure(api_key=api_key)

        print(f"  Trying nano-banana-pro-preview...")

        model = genai.GenerativeModel('nano-banana-pro-preview')

        response = model.generate_content(
            f"Generate an image: {prompt}",
            generation_config={
                "response_modalities": ["IMAGE", "TEXT"],
            }
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    print(f"  Saved: {output_path}")
                    return True

        print(f"  No image in nano-banana response")
        return False

    except Exception as e:
        print(f"  ERROR with nano-banana: {e}")
        return False


def generate_with_gemini_imagen(prompt: str, output_path: Path, api_key: str) -> bool:
    """Main image generation function - tries multiple methods."""
    # Try the primary image generation model first
    if generate_with_gemini_image(prompt, output_path, api_key):
        return True

    # Fallback to nano-banana
    return generate_with_nano_banana(prompt, output_path, api_key)


def generate_all_dinosaur_concepts(dry_run: bool = False) -> Dict[str, Dict[str, bool]]:
    """Generate all dinosaur concept art."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and not dry_run:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    output_base = Path(__file__).parent.parent / "assets" / "creatures" / "concepts"
    output_base.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for category, data in DINOSAUR_PROMPTS.items():
        print(f"\n{'='*60}")
        print(f"Generating: {data['description'].upper()}")
        print(f"{'='*60}")

        category_results = {}

        for variation in data["variations"]:
            name = variation["name"]
            prompt = variation["prompt"].strip()

            output_path = output_base / f"{name}_v1.png"

            print(f"\n[{name}]")

            if dry_run:
                print(f"  Prompt preview: {prompt[:150]}...")
                print(f"  Would save to: {output_path}")
                category_results[name] = True
            else:
                success = generate_with_gemini_imagen(prompt, output_path, api_key)
                category_results[name] = success
                # Rate limiting
                time.sleep(3)

        all_results[category] = category_results

    return all_results


def print_summary(results: Dict[str, Dict[str, bool]]) -> None:
    """Print summary of generation results."""
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    total_success = 0
    total_failed = 0

    for category, variations in results.items():
        success = sum(1 for v in variations.values() if v)
        failed = sum(1 for v in variations.values() if not v)
        total_success += success
        total_failed += failed

        status = "SUCCESS" if failed == 0 else "PARTIAL" if success > 0 else "FAILED"
        print(f"  {category}: {status} ({success}/{len(variations)})")

    print("-"*60)
    print(f"  TOTAL: {total_success} succeeded, {total_failed} failed")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate dinosaur species concept art")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    parser.add_argument("--list", action="store_true", help="List all prompts")

    args = parser.parse_args()

    if args.list:
        print("\nDinosaur Concept Art Prompts:")
        print("="*60)
        for category, data in DINOSAUR_PROMPTS.items():
            print(f"\n{category.upper()}: {data['description']}")
            for v in data["variations"]:
                print(f"  - {v['name']}")
        return

    results = generate_all_dinosaur_concepts(dry_run=args.dry_run)
    print_summary(results)

    # Return exit code based on results
    total_failed = sum(sum(1 for v in r.values() if not v) for r in results.values())
    sys.exit(1 if total_failed > 0 and not args.dry_run else 0)


if __name__ == "__main__":
    main()
