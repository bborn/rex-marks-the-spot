#!/usr/bin/env python3
"""
Fix minivan style mismatch - regenerate interior shots and add orthographic view.

Addresses PR #96 review feedback:
1. Interior shots are photorealistic, need to be Pixar-style
2. Night storm shot has different grille design
3. Need orthographic side view for 3D reference
"""

import os
import sys
import argparse
import time
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai package not installed. Run: pip install google-genai")
    sys.exit(1)


# Reference prompt structure from the good exterior_normal shot:
# Strong emphasis on "Pixar 3D animation style" and "stylized" to avoid photorealism

FIXED_PROMPTS = {
    # Interior front - emphasize stylized/cartoon aesthetic, NOT realistic
    "interior_front": """Pixar 3D animation style environment concept art,
stylized cartoon family minivan interior front seats view,
simplified rounded shapes with soft diffuse lighting,
cute oversized fuzzy dice hanging from mirror with big cartoon eyes pattern,
chunky stylized dashboard with rounded buttons and knobs,
GPS screen with simple cartoon map graphics,
cloth seats with exaggerated puffy cushions,
coffee cup with fun cartoon steam swirls,
family photos as cute polaroid style drawings,
everything rendered in same stylized 3D look as Pixar's Cars movie,
soft ambient occlusion, no photorealistic textures,
warm cozy interior glow, professional Pixar animation quality,
simple clean shapes, cartoon proportions""",

    # Interior back kids - enhance stylization to match character art
    "interior_back_kids": """Pixar 3D animation style environment concept art,
stylized cartoon minivan back seat area for kids,
two oversized cute car seats - one bright purple one bright teal,
chunky simplified shapes like Pixar's Cars movie interiors,
scattered colorful cartoon dinosaur plush toys with big googly eyes,
spilled orange goldfish crackers rendered as cute simple shapes,
juice box with fun cartoon fruit character on it,
kid drawings taped to seats shown as cute crayon doodles,
backpack with cartoon animal patches,
window shade with adorable cartoon dinosaur pattern,
everything has rounded soft edges and stylized proportions,
warm friendly lighting, clean 3D render style,
matches Pixar movie aesthetic, no photorealistic textures""",

    # Night storm - match the grille/headlight design of exterior_normal
    "exterior_night_storm": """Pixar 3D animation style environment concept art,
stylized cartoon family minivan driving in storm at night,
dark teal-blue minivan with same rounded friendly design as Pixar Cars,
rounded oval headlights with warm yellow glow cutting through rain,
simple curved grille design with friendly face-like appearance,
chunky stylized windshield wipers in mid-sweep,
cartoon-style raindrops as simple teardrop shapes on windshield,
dramatic lightning bolt in stylized zigzag pattern,
wet road rendered with simple reflections not photorealistic,
silhouettes of parents visible through glowing windows,
stormy purple sky with swirling stylized clouds,
same vehicle design as the normal driveway exterior shot,
professional Pixar animation production quality""",

    # NEW: Orthographic side view for 3D modeling reference
    "exterior_side_ortho": """Pixar 3D animation style technical reference art,
family minivan clean orthographic side view profile,
dark teal-blue stylized minivan on pure white background,
perfectly flat side-on view with no perspective distortion,
friendly rounded body design matching Pixar Cars aesthetic,
chunky simplified wheel wells and wheels,
sliding door visible with simple line details,
roof rack with small luggage carrier,
fun bumper sticker shapes visible,
clean technical illustration for 3D modeling reference,
simple soft lighting from front,
no dramatic angles or effects,
pure profile silhouette view,
professional animation production model sheet style""",
}


class MinivanStyleFixer:
    """Regenerates minivan shots with consistent stylization."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=api_key)

    def generate_image(self, prompt: str, output_path: Path) -> bool:
        """Generate a single image using Gemini Imagen."""
        try:
            print(f"  Generating image...")

            # Try gemini-2.0-flash-exp for image generation
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )

            # Extract image from gemini response
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        image_data = part.inline_data.data

                        with open(output_path, "wb") as f:
                            f.write(image_data)

                        print(f"  Saved: {output_path}")
                        return True

            print(f"  ERROR: No images generated")
            return False

        except Exception as e:
            print(f"  ERROR: {e}")
            return False

    def fix_view(self, view_name: str, dry_run: bool = False) -> bool:
        """Regenerate a specific view with fixed stylization."""
        if view_name not in FIXED_PROMPTS:
            print(f"ERROR: Unknown view: {view_name}")
            return False

        prompt = FIXED_PROMPTS[view_name]
        output_path = self.output_dir / f"minivan_{view_name}.png"

        print(f"\n[{view_name}]")
        if dry_run:
            print(f"  Prompt preview: {prompt[:150]}...")
            print(f"  Would save to: {output_path}")
            return True
        else:
            return self.generate_image(prompt.strip(), output_path)

    def fix_all(self, dry_run: bool = False) -> dict:
        """Fix all problematic views."""
        results = {}

        print(f"\n{'='*60}")
        print("FIXING: MINIVAN STYLE MISMATCH")
        print(f"{'='*60}")

        for view_name in FIXED_PROMPTS.keys():
            results[view_name] = self.fix_view(view_name, dry_run=dry_run)
            if not dry_run:
                # Rate limiting - Gemini has quota limits
                print("  Waiting for rate limit (10s)...")
                time.sleep(10)

        return results


def print_summary(results: dict) -> None:
    """Print a summary of generation results."""
    print("\n" + "="*60)
    print("FIX SUMMARY")
    print("="*60)

    success = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)

    for view_name, result in results.items():
        status = "SUCCESS" if result else "FAILED"
        print(f"  {view_name}: {status}")

    print("-"*60)
    print(f"  TOTAL: {success} succeeded, {failed} failed")
    print(f"  Images saved to: assets/props/minivan/")


def main():
    parser = argparse.ArgumentParser(
        description="Fix minivan style mismatch - regenerate with Pixar-style"
    )
    parser.add_argument("--all", action="store_true", help="Fix all problematic views")
    parser.add_argument("--view", "-v", type=str,
                        choices=list(FIXED_PROMPTS.keys()),
                        help="Fix specific view")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without generating")
    parser.add_argument("--list", action="store_true",
                        help="List views that need fixing")

    args = parser.parse_args()

    if args.list:
        print("\nViews to fix:")
        print("="*60)
        for view in FIXED_PROMPTS.keys():
            print(f"  - {view}")
        sys.exit(0)

    if not args.all and not args.view:
        parser.error("Either --all or --view is required")

    output_dir = Path(__file__).parent.parent / "assets" / "props" / "minivan"

    try:
        fixer = MinivanStyleFixer(output_dir)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.all:
        results = fixer.fix_all(dry_run=args.dry_run)
    else:
        results = {args.view: fixer.fix_view(args.view, dry_run=args.dry_run)}

    print_summary(results)

    total_failed = sum(1 for v in results.values() if not v)
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()
