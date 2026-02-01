#!/usr/bin/env python3
"""
Concept Art Generation Script

Generates character concept art for "Fairy Dinosaur Date Night" using
AI image generation APIs (OpenAI DALL-E 3, Stability AI, or Leonardo AI).

Usage:
    # Generate all characters (requires OPENAI_API_KEY environment variable)
    python scripts/generate_concept_art.py --all

    # Generate specific character
    python scripts/generate_concept_art.py --character jetplane

    # Generate specific type of art
    python scripts/generate_concept_art.py --character mia --type portrait

    # Use different API provider
    python scripts/generate_concept_art.py --all --provider stability

    # Dry run (show prompts without generating)
    python scripts/generate_concept_art.py --all --dry-run
"""

import os
import sys
import json
import argparse
import base64
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class GenerationConfig:
    """Configuration for image generation."""
    provider: str = "openai"  # openai, stability, leonardo
    model: str = "dall-e-3"  # Model to use
    size: str = "1024x1024"  # Image size
    quality: str = "hd"  # hd or standard
    style: str = "vivid"  # vivid or natural
    n: int = 1  # Number of images per prompt


# Character prompts extracted from PROMPTS.md files
CHARACTER_PROMPTS = {
    "mia": {
        "portrait": """Pixar 3D animation style character design, 8-year-old girl named Mia,
warm chestnut brown hair in high ponytail with bright turquoise scrunchie,
large expressive brown eyes, oval face with soft cheekbones,
small upturned nose, kind but determined expression,
wearing purple t-shirt with yellow star graphic,
professional character concept art, white background,
family-friendly animated film quality""",

        "turnaround": """Character model sheet, 360-degree turnaround, Pixar animation style,
8-year-old girl with brown ponytail and turquoise hair tie,
purple star t-shirt, denim shorts with cuffed hem,
pink and white velcro sneakers, front view, side view, back view,
three-quarter view, consistent proportions throughout,
professional animation studio quality, clean white background""",

        "expressions": """Character expression sheet, 6 expressions, Pixar 3D animation style,
8-year-old girl with brown ponytail and turquoise scrunchie,
showing: determined/brave, worried/concerned, loving big sister smile,
fear/startled, joy/relief with tears, frustrated eye roll,
consistent character design, professional animation reference,
clean presentation on white background""",

        "action": """Character action pose, Pixar 3D animation style,
8-year-old girl with brown ponytail taking charge,
standing confidently, one hand on hip, determined expression,
purple star shirt, denim shorts, dynamic hero pose,
professional character art""",
    },

    "leo": {
        "portrait": """Pixar 3D animation style character design, 5-year-old boy named Leo,
messy tousled chestnut brown hair with stubborn cowlick sticking up,
very large innocent brown eyes, round face with full cheeks,
light freckles across nose and cheeks, gap-toothed smile,
wearing bright green t-shirt with orange dinosaur graphic,
adorable curious expression, professional character concept art,
family-friendly animated film quality, white background""",

        "turnaround": """Character model sheet, 360-degree turnaround, Pixar animation style,
5-year-old boy with messy brown hair and freckles,
green dinosaur t-shirt, khaki cargo shorts with big pockets,
blue and orange velcro sneakers, front view, side view, back view,
three-quarter view, shorter and rounder proportions than typical,
professional animation studio quality, clean white background""",

        "expressions": """Character expression sheet, 6 expressions, Pixar 3D animation style,
5-year-old boy with messy brown hair and freckles, gap-toothed smile,
showing: pure wonder with jaw dropped, scared hiding behind hands,
brave despite fear with puffed chest, pure joy with full gap-tooth grin,
sad missing parents with watery eyes, curious head tilt,
big unfiltered child emotions, professional animation reference""",

        "action": """Character action pose, Pixar 3D animation style,
5-year-old boy looking up in complete amazement,
eyes huge, mouth open in awe, pointing upward,
messy brown hair, green dinosaur shirt, khaki shorts,
childlike wonder pose, professional character art""",
    },

    "gabe": {
        "portrait": """Pixar 3D animation style character design, father character age 38,
short dark brown hair with hints of gray at temples,
warm brown eyes behind rectangular dark-framed glasses,
oval face tending toward square jaw, five o'clock shadow stubble,
slightly tired but warm expression, white dress shirt,
loosened dark blue tie, professional but stressed appearance,
professional character concept art, white background""",

        "turnaround": """Character model sheet, 360-degree turnaround, Pixar animation style,
late 30s father with glasses and stubble, 6 feet tall,
white dress shirt with sleeves rolled up, charcoal dress pants,
loosened navy tie, brown dress shoes, average build slightly soft,
front view, side view, back view, three-quarter view,
professional animation studio quality, clean white background""",

        "expressions": """Character expression sheet, 6 expressions, Pixar 3D animation style,
late 30s father with rectangular glasses and stubble,
showing: distracted looking at invisible phone, stressed hand to temple,
terror with wide eyes behind glasses, protective determined father,
guilt and realization looking down, genuine joy and relief with tears,
glasses stay on throughout, professional animation reference""",

        "costume_progression": """Character progression sheet, Pixar 3D animation style,
same father character shown in three stages:
Stage 1 pristine formal wear white shirt and tie,
Stage 2 slightly disheveled and dusty,
Stage 3 torn and dirty survival mode but standing stronger,
white dress shirt getting progressively more damaged,
professional animation reference""",
    },

    "nina": {
        "portrait": """Pixar 3D animation style character design, mother character age 37,
shoulder-length dark brown hair with elegant soft waves,
beautiful hazel-green eyes with warm expression,
heart-shaped face with defined cheekbones, refined features,
wearing elegant burgundy wine-colored cocktail dress,
simple gold earrings, patient but strong presence,
professional character concept art, white background""",

        "turnaround": """Character model sheet, 360-degree turnaround, Pixar animation style,
late 30s elegant mother, 5'7" tall, graceful proportions,
burgundy knee-length cocktail dress, strappy gold heels,
gold bracelet and small earrings, hair in soft waves,
front view, side view, back view, three-quarter view,
professional animation studio quality, clean white background""",

        "expressions": """Character expression sheet, 6 expressions, Pixar 3D animation style,
elegant mother with dark wavy hair and hazel-green eyes,
showing: patient supportive smile that doesn't reach eyes,
THE LOOK (one eyebrow raised, direct stare, knowing disappointment),
terror but focused, fierce protective mama bear,
breaking point with tears and flushed face, relief and love,
professional animation reference, this is an important character""",

        "the_look": """Single character expression, extreme close-up, Pixar 3D animation style,
beautiful mother's face giving THE LOOK,
one eyebrow slightly raised, eyes locked forward,
lips pressed together, head perfectly still,
slight head tilt, disappointed but knowing expression,
this should be iconic and meme-worthy,
professional animation quality, detailed facial features""",
    },

    "ruben": {
        "portrait": """Pixar 3D animation style character design, depressed fairy godfather,
appears 50s years old, wild unkempt silvery gray hair going everywhere,
tired blue-gray eyes with heavy dark bags underneath,
long drawn face that was once handsome, prominent nose,
perpetual stubble, world-weary cynical expression,
iridescent fairy wings drooping sadly behind him,
faded purple vest over wrinkled cream shirt,
professional character concept art, white background""",

        "turnaround": """Character model sheet, 360-degree turnaround, Pixar animation style,
fairy godfather character, 5'9" but hunched posture,
silvery wild hair, sad droopy translucent fairy wings,
faded purple moth-eaten vest, wrinkled half-untucked shirt,
worn baggy trousers, scuffed pointed curled fairy shoes,
holding dented magic wand with tape-wrapped handle,
front view, side view, back view, three-quarter view,
professional animation studio quality""",

        "expressions": """Character expression sheet, 6 expressions, Pixar 3D animation style,
fairy godfather with wild gray hair and tired eyes,
showing: world-weary cynical default, embarrassed magic failure,
surprised when magic works, fighting affection for kids,
real fear for others, genuine warmth finally showing,
wings should reflect emotions in each pose,
professional animation reference""",

        "wing_states": """Character wing variations, Pixar 3D animation style, fairy godfather
with gray hair and sad expression, showing wing states:
droopy and dull (depressed), slightly perked (interested),
fully extended and glowing (heroic moment),
iridescent blue-purple fairy wings, same character throughout,
professional animation reference""",

        "transformation": """Character transformation sheet, Pixar 3D animation style,
fairy godfather showing progression: depressed hunched posture
with droopy wings (start), gradually standing straighter,
to final heroic pose with wings fully extended and glowing,
same worn clothes throughout, professional animation reference""",
    },

    "jetplane": {
        "portrait": """Pixar 3D animation style creature design, adorable dinosaur named Jetplane,
chicken-puppy-lizard hybrid creature, round huggable body shape,
soft teal-green scales, cream-colored belly, warm orange fluffy neck ruff,
HUGE amber puppy-like eyes with multiple catchlights,
soft coral-pink floppy ear-frills that express emotion,
small cute T-Rex style arms, stubby legs with pink toe beans,
expressive tail with orange fluffy tuft at end,
joyful friendly expression, designed to be iconic and toyetic,
professional character concept art, this is the merchandising star""",

        "turnaround": """Character model sheet, 360-degree turnaround, Pixar animation style,
adorable teal dinosaur creature, cat-sized (small form),
round body, big amber eyes, coral ear-frills, orange neck ruff,
cream belly, stubby legs, fluffy tail tuft,
front view, side view, back view, three-quarter view, top view,
bottom view showing pink toe beans,
professional animation studio quality, toyetic design""",

        "expressions": """Character expression sheet, 8 expressions, Pixar 3D animation style,
adorable teal dinosaur with big amber eyes and pink ear-frills,
showing: pure joy with wagging tail, terrified with flat ears,
brave despite fear with raised tail, curious head tilt,
sad droopy with watery eyes, loving nuzzle expression,
excited bouncing, proud after accomplishment,
ear-frills and tail reflect each emotion,
professional animation reference, maximum expressiveness""",

        "size_comparison": """Character size comparison sheet, Pixar 3D animation style,
cute teal dinosaur in TWO sizes side by side:
SMALL FORM: cat-sized (18 inches), can be hugged by child
LARGE FORM: rideable (4 feet tall), can carry two kids
exact same design proportions in both sizes,
same big eyes, ear-frills, colors, cuteness factor,
professional animation reference""",

        "rainbow_fart": """Character action sequence, Pixar 3D animation style,
cute teal dinosaur rainbow fart sequence in 4 panels:
1. Alert pose, ears perk up, realizing it's coming
2. Crouch position, eyes squeeze shut, concentration
3. Release moment with colorful rainbow cloud emerging
4. Proud/surprised aftermath looking back at rainbow
magical sparkly family-friendly rainbow effect,
comedic not gross, professional animation reference""",

        "merchandise": """Character pose sheet, Pixar 3D animation style,
adorable teal dinosaur mascot character, showing merchandise-ready poses:
standing proud, playful bow, hugging pose, action pose,
simple silhouette-friendly designs, plush toy appeal,
professional character art suitable for products""",
    },
}


class ConceptArtGenerator:
    """
    Generates concept art using various AI image generation APIs.
    """

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.output_base = Path(__file__).parent.parent / "assets" / "characters"

    def generate_with_openai(self, prompt: str, output_path: Path) -> bool:
        """Generate image using OpenAI DALL-E API."""
        try:
            import openai
        except ImportError:
            print("ERROR: openai package not installed. Run: pip install openai")
            return False

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY environment variable not set")
            return False

        client = openai.OpenAI(api_key=api_key)

        try:
            print(f"  Generating with DALL-E 3...")
            response = client.images.generate(
                model=self.config.model,
                prompt=prompt,
                size=self.config.size,
                quality=self.config.quality,
                style=self.config.style,
                n=self.config.n,
                response_format="b64_json",
            )

            # Save the image
            output_path.parent.mkdir(parents=True, exist_ok=True)

            for i, image_data in enumerate(response.data):
                img_bytes = base64.b64decode(image_data.b64_json)

                if len(response.data) > 1:
                    save_path = output_path.with_stem(f"{output_path.stem}_{i+1}")
                else:
                    save_path = output_path

                with open(save_path, "wb") as f:
                    f.write(img_bytes)

                print(f"  Saved: {save_path}")

            return True

        except Exception as e:
            print(f"  ERROR: {e}")
            return False

    def generate_with_stability(self, prompt: str, output_path: Path) -> bool:
        """Generate image using Stability AI API."""
        try:
            import requests
        except ImportError:
            print("ERROR: requests package not installed. Run: pip install requests")
            return False

        api_key = os.environ.get("STABILITY_API_KEY")
        if not api_key:
            print("ERROR: STABILITY_API_KEY environment variable not set")
            return False

        try:
            print(f"  Generating with Stability AI...")
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "text_prompts": [
                        {"text": prompt, "weight": 1},
                        {"text": "ugly, deformed, blurry, low quality, realistic, anime", "weight": -1},
                    ],
                    "cfg_scale": 7,
                    "height": 1024,
                    "width": 1024,
                    "samples": 1,
                    "steps": 30,
                },
            )

            if response.status_code != 200:
                print(f"  ERROR: API returned {response.status_code}: {response.text}")
                return False

            data = response.json()

            output_path.parent.mkdir(parents=True, exist_ok=True)

            for i, artifact in enumerate(data.get("artifacts", [])):
                img_bytes = base64.b64decode(artifact["base64"])

                if len(data["artifacts"]) > 1:
                    save_path = output_path.with_stem(f"{output_path.stem}_{i+1}")
                else:
                    save_path = output_path

                with open(save_path, "wb") as f:
                    f.write(img_bytes)

                print(f"  Saved: {save_path}")

            return True

        except Exception as e:
            print(f"  ERROR: {e}")
            return False

    def generate(self, prompt: str, output_path: Path) -> bool:
        """Generate image using configured provider."""
        if self.config.provider == "openai":
            return self.generate_with_openai(prompt, output_path)
        elif self.config.provider == "stability":
            return self.generate_with_stability(prompt, output_path)
        else:
            print(f"ERROR: Unknown provider: {self.config.provider}")
            return False

    def generate_for_character(
        self,
        character: str,
        art_types: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> Dict[str, bool]:
        """Generate all concept art for a specific character."""
        if character not in CHARACTER_PROMPTS:
            print(f"ERROR: Unknown character: {character}")
            return {}

        prompts = CHARACTER_PROMPTS[character]
        if art_types:
            prompts = {k: v for k, v in prompts.items() if k in art_types}

        results = {}
        char_output_dir = self.output_base / character / "concept-art"

        print(f"\n{'='*60}")
        print(f"Generating concept art for: {character.upper()}")
        print(f"{'='*60}")

        for art_type, prompt in prompts.items():
            output_path = char_output_dir / f"{character}_{art_type}_v1.png"

            print(f"\n[{art_type}]")
            if dry_run:
                print(f"  Prompt: {prompt[:100]}...")
                print(f"  Would save to: {output_path}")
                results[art_type] = True
            else:
                results[art_type] = self.generate(prompt.strip(), output_path)
                # Rate limiting
                time.sleep(2)

        return results

    def generate_all(self, dry_run: bool = False) -> Dict[str, Dict[str, bool]]:
        """Generate concept art for all characters."""
        all_results = {}

        for character in CHARACTER_PROMPTS.keys():
            all_results[character] = self.generate_for_character(
                character,
                dry_run=dry_run
            )

        return all_results


def print_summary(results: Dict[str, Dict[str, bool]]) -> None:
    """Print a summary of generation results."""
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    total_success = 0
    total_failed = 0

    for character, art_results in results.items():
        success = sum(1 for v in art_results.values() if v)
        failed = sum(1 for v in art_results.values() if not v)
        total_success += success
        total_failed += failed

        status = "SUCCESS" if failed == 0 else "PARTIAL" if success > 0 else "FAILED"
        print(f"  {character}: {status} ({success}/{len(art_results)})")

    print("-"*60)
    print(f"  TOTAL: {total_success} succeeded, {total_failed} failed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate character concept art using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate art for all characters",
    )
    parser.add_argument(
        "--character", "-c",
        type=str,
        choices=list(CHARACTER_PROMPTS.keys()),
        help="Generate art for specific character",
    )
    parser.add_argument(
        "--type", "-t",
        type=str,
        help="Generate specific art type (portrait, turnaround, expressions, etc.)",
    )
    parser.add_argument(
        "--provider", "-p",
        type=str,
        default="openai",
        choices=["openai", "stability"],
        help="AI provider to use (default: openai)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show prompts without generating images",
    )
    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List all available prompts and exit",
    )
    parser.add_argument(
        "--size",
        type=str,
        default="1024x1024",
        help="Image size (default: 1024x1024)",
    )
    parser.add_argument(
        "--quality",
        type=str,
        default="hd",
        choices=["standard", "hd"],
        help="Image quality for DALL-E (default: hd)",
    )

    args = parser.parse_args()

    # List prompts mode
    if args.list_prompts:
        print("\nAvailable Prompts:")
        print("="*60)
        for char, prompts in CHARACTER_PROMPTS.items():
            print(f"\n{char.upper()}:")
            for art_type in prompts.keys():
                print(f"  - {art_type}")
        sys.exit(0)

    # Validate arguments
    if not args.all and not args.character:
        parser.error("Either --all or --character is required")

    # Create config
    config = GenerationConfig(
        provider=args.provider,
        size=args.size,
        quality=args.quality,
    )

    # Create generator
    generator = ConceptArtGenerator(config)

    # Generate
    if args.all:
        results = generator.generate_all(dry_run=args.dry_run)
    else:
        art_types = [args.type] if args.type else None
        results = {
            args.character: generator.generate_for_character(
                args.character,
                art_types=art_types,
                dry_run=args.dry_run,
            )
        }

    # Print summary
    print_summary(results)

    # Exit with appropriate code
    total_failed = sum(
        sum(1 for v in r.values() if not v)
        for r in results.values()
    )
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
