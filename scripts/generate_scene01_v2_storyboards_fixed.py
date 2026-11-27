#!/usr/bin/env python3
"""Generate Scene 1 v2 storyboard panels (FIXED) - Gemini img2img with character refs.

Fixes from v2 original:
- 16:9 aspect ratio crop on all images
- Panel 02: Leo sitting on couch, medium shot
- Panel 03: Nina in black dress (not burgundy)
- Panel 05: Jenny blonde ponytail emphasis
- Panel 07: Both kids sitting on couch
- Panel 08 end: No dialogue text in image
- Panel 09: Gabe in tuxedo, Nina dark brown hair, no dialogue text

Usage:
    # Regenerate only specific panels:
    python generate_scene01_v2_storyboards_fixed.py --panels 02 03 05 07 08-end 09

    # Crop all existing images to 16:9 without regenerating:
    python generate_scene01_v2_storyboards_fixed.py --crop-only

    # Regenerate all panels:
    python generate_scene01_v2_storyboards_fixed.py
"""

import argparse
import io
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Directories
CHAR_REF_DIR = Path("/tmp/char-refs")
OUTPUT_DIR = Path.home() / "rex-marks-the-spot" / "assets" / "storyboards" / "v2" / "scene-01"

# Character reference images (loaded once)
CHAR_REFS = {}

# Style prefix for all prompts
STYLE = (
    "Pixar-style 3D animated film rendering, cinematic lighting, "
    "warm domestic evening lighting, 16:9 widescreen composition, "
    "high quality finished look, NOT a sketch, NOT black-and-white, full color. "
    "Do NOT render any text, words, letters, dialogue, or captions in the image."
)

# Environment description for consistency
ENV_DESC = (
    "Cozy family living room, evening. Warm amber table lamps and overhead light. "
    "Large window showing dark stormy sky outside. TV mounted on wall. "
    "Comfortable brown couch with colorful throw pillows. Dinosaur toys scattered on floor. "
    "Wooden coffee table. Family photos on walls. Warm hardwood floors with area rug."
)

# Panel definitions (FIXED)
PANELS = [
    {
        "id": "01",
        "name": "Wide Establishing",
        "chars": [],
        "start_prompt": (
            f"Wide establishing shot of {ENV_DESC} "
            "TV is on showing a colorful cartoon. Storm clouds visible through window. "
            "Calm, peaceful atmosphere. Two children visible on couch from distance. "
            f"{STYLE}"
        ),
        "end_prompt": (
            f"Wide establishing shot of {ENV_DESC} "
            "Dramatic lightning flash illuminates the room through the window, casting sharp shadows. "
            "TV flickers with static interference. Same room, dramatic shift in mood. "
            f"{STYLE}"
        ),
    },
    {
        "id": "02",
        "name": "Medium Shot Leo",
        "chars": ["leo"],
        "char_instruction": (
            "The boy in this scene is Leo, age 5. Match this character EXACTLY in face shape, "
            "proportions, hair color and style, and clothing from the reference turnaround sheet. "
            "He wears dinosaur pajamas and hugs a plush T-Rex toy."
        ),
        "start_prompt": (
            "MEDIUM SHOT framed from waist up. Leo, a 5-year-old boy in dinosaur pajamas, "
            "is SITTING on the brown couch, NOT standing. He hugs a plush T-Rex toy and "
            "looks content and happy watching TV. He is seated comfortably on the couch cushions. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "MEDIUM SHOT framed from waist up. Leo, a 5-year-old boy in dinosaur pajamas, "
            "is SITTING on the brown couch, NOT standing. He has a plush T-Rex toy and "
            "glances down at his toy dinosaurs on the couch beside him with a slight warm smile. "
            "He is seated on the couch. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
    },
    {
        "id": "03",
        "name": "Tracking Shot Nina",
        "chars": ["nina"],
        "char_instruction": (
            "The woman in this scene is Nina, the mother. Match this character EXACTLY in face, "
            "proportions, hair, and body type from the reference turnaround sheet. "
            "She wears an ELEGANT BLACK COCKTAIL DRESS. The dress is BLACK, not any other color. "
            "NOT burgundy, NOT maroon, NOT red. A BLACK dress. Getting ready for a fancy date night."
        ),
        "start_prompt": (
            "Medium tracking shot of Nina, an elegant woman in a BLACK cocktail dress, walking through "
            "the living room putting on earrings. She moves gracefully. "
            "Nina wears an ELEGANT BLACK COCKTAIL DRESS. The dress is BLACK, not any other color. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Medium shot of Nina, an elegant woman in a BLACK cocktail dress, near the front door area, "
            "checking her purse with frantic but graceful movement. Slight urgency in her posture. "
            "Nina wears an ELEGANT BLACK COCKTAIL DRESS. The dress is BLACK, not any other color. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
    },
    {
        "id": "04",
        "name": "Two-Shot Gabe and Nina",
        "chars": ["gabe", "nina"],
        "char_instruction": (
            "The man is Gabe, the father - match EXACTLY from his turnaround: glasses, slight stubble, "
            "soft around the middle, NOT muscular. He wears a BLACK TUXEDO with white shirt and bow tie. "
            "The woman is Nina, the mother - match EXACTLY from her turnaround. "
            "Nina has DARK BROWN wavy hair and wears an ELEGANT BLACK cocktail dress."
        ),
        "start_prompt": (
            "Two-shot of Gabe and Nina. Gabe in a BLACK TUXEDO checking his watch impatiently, slightly frustrated. "
            "Nina still putting finishing touches on her outfit. Two kids visible on couch in background. "
            "Comedy staging - the contrast between his impatience and her composure. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Two-shot of Gabe and Nina. Gabe in a BLACK TUXEDO gesturing urgently with both hands, comically exasperated. "
            "Nina calm and composed in a BLACK dress, giving him a look. Classic comedy couple staging. "
            "Kids on couch in background. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
    },
    {
        "id": "05",
        "name": "Insert Jenny",
        "chars": ["jenny"],
        "char_instruction": (
            "The teenager is Jenny, the babysitter, age 15. "
            "This character is a BLONDE teenager with a BLONDE PONYTAIL. She has BLONDE HAIR. "
            "Match the BLONDE hair color and ponytail hairstyle from the reference image EXACTLY. "
            "Her hair is BLONDE, not dark, not brown, not black. BLONDE PONYTAIL. "
            "She wears casual teen clothes and is glued to her phone."
        ),
        "start_prompt": (
            "Close-up insert shot of Jenny, a 15-year-old babysitter with BLONDE PONYTAIL hair. "
            "She has BLONDE hair tied in a ponytail. Her hair color is BLONDE. "
            "She is looking down at her phone with an oblivious expression, texting. "
            "Phone screen glow on her face. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Close-up insert shot of Jenny, a 15-year-old babysitter with BLONDE PONYTAIL hair. "
            "She has BLONDE hair tied in a ponytail. Her hair color is BLONDE. "
            "She gives a brief distracted nod without looking up from her phone. "
            "Phone glow illuminating her face. Totally absorbed in texting. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
    },
    {
        "id": "06",
        "name": "Close-up TV Flickering",
        "chars": [],
        "start_prompt": (
            "Extreme close-up of a TV screen showing a colorful cartoon with bright happy colors. "
            "The TV is mounted on a living room wall. Normal, clear picture. "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Extreme close-up of a TV screen glitching with static lines, blue electrical flicker, "
            "scan lines rolling through the image. The cartoon is breaking up. "
            "Eerie blue-white interference pattern. TV mounted on living room wall. "
            f"{STYLE}"
        ),
    },
    {
        "id": "07",
        "name": "Over-the-Shoulder Kids",
        "chars": ["mia", "leo"],
        "char_instruction": (
            "The two children seen FROM BEHIND are Mia (8, curly/wavy hair) and Leo (5, dinosaur pajamas). "
            "Match their hair and clothing from the turnaround sheets. We see the backs of their heads. "
            "Both children are SITTING on the couch side by side. Neither is standing."
        ),
        "start_prompt": (
            "Over-the-shoulder shot from behind two children SITTING on a couch watching TV. "
            "Both children are SITTING on the couch side by side, seen from behind. Neither is standing. "
            "Girl (8, wavy hair) and boy (5, dinosaur pajamas) both SEATED on the couch. "
            "Parents blurred in the background rushing around getting ready. TV visible ahead. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Over-the-shoulder shot from behind two children SITTING on couch side by side. "
            "Both children are SITTING. Neither is standing. "
            "The girl (Mia, 8) turns her head slightly to look back at parents with concern on her face. "
            "Boy (Leo, 5, dinosaur pajamas) still watching TV. Both are SEATED. Parents blurred in background. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
    },
    {
        "id": "08",
        "name": "Close-up Mia",
        "chars": ["mia"],
        "char_instruction": (
            "This is Mia, age 8. Match this character EXACTLY from the reference turnaround sheet: "
            "face shape, eye color, wavy hair, skin tone, proportions. She has big expressive eyes."
        ),
        "start_prompt": (
            "Cinematic close-up of Mia, an 8-year-old girl with wavy hair and big expressive eyes, "
            "looking up with slight worry. Warm ambient lighting from table lamps. "
            "Shallow depth of field. Emotional, vulnerable expression. "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Cinematic close-up of Mia, an 8-year-old girl with wavy hair and big expressive eyes, "
            "with an earnest pleading expression, lips slightly parted as if asking a question. "
            "TV light reflected in her eyes. "
            "Lightning flash from window casts dramatic light. Deeply emotional moment. "
            f"{STYLE}"
        ),
    },
    {
        "id": "09",
        "name": "Close-up Gabe Hesitates",
        "chars": ["gabe", "nina"],
        "char_instruction": (
            "The man in close-up is Gabe - match EXACTLY from turnaround: glasses, stubble, "
            "soft/round face, warm expression. Gabe wears a BLACK TUXEDO with white shirt and bow tie. "
            "NOT casual clothes. NOT a flannel. He is dressed formally for a gala. "
            "The woman behind him is Nina - match from her turnaround. "
            "Nina has DARK BROWN wavy hair (NOT red, NOT auburn) and wears a BLACK cocktail dress."
        ),
        "start_prompt": (
            "Cinematic close-up of Gabe, a father in his early 40s with glasses and slight stubble, "
            "wearing a BLACK TUXEDO with white shirt and bow tie. NOT casual clothes, NOT a flannel. "
            "He is dressed formally. He shows conflict and hesitation on his face. "
            "He's torn about leaving his kids. Warm lighting, shallow depth of field. Emotional weight. "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Cinematic close-up of Gabe with glasses and stubble, wearing a BLACK TUXEDO. "
            "He has a resigned but loving expression, nodding slightly. "
            "Behind him, slightly out of focus, Nina with DARK BROWN wavy hair gives him a stern glare. "
            "Nina wears a BLACK dress. Comedy meets emotion. Warm lighting. "
            f"{STYLE}"
        ),
    },
]

# Character ref file mapping
CHAR_FILES = {
    "mia": "mia_turnaround_APPROVED_ALT.png",
    "leo": "leo_turnaround_APPROVED.png",
    "gabe": "gabe_turnaround_APPROVED.png",
    "nina": "nina_turnaround_APPROVED.png",
    "jenny": "jenny_turnaround_APPROVED.png",
}


def crop_to_16_9(img: Image.Image) -> Image.Image:
    """Center-crop an image to 16:9 aspect ratio."""
    w, h = img.size
    target_ratio = 16 / 9
    current_ratio = w / h

    if abs(current_ratio - target_ratio) < 0.01:
        return img  # Already 16:9

    if current_ratio < target_ratio:
        # Too tall — crop top and bottom
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    else:
        # Too wide — crop left and right
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))

    return img


def load_character_refs():
    """Load all character reference images."""
    for name, filename in CHAR_FILES.items():
        path = CHAR_REF_DIR / filename
        if path.exists():
            CHAR_REFS[name] = Image.open(path)
            print(f"  Loaded {name}: {path}")
        else:
            print(f"  WARNING: Missing {name} ref: {path}")


def generate_image(prompt: str, char_names: list, char_instruction: str = "",
                   env_ref: Image.Image = None) -> bytes | None:
    """Generate a single image using Gemini with character references."""
    contents = []

    # Add character reference images
    for name in char_names:
        if name in CHAR_REFS:
            contents.append(CHAR_REFS[name])

    # Add environment reference if available
    if env_ref is not None:
        contents.append(env_ref)

    # Build the text prompt
    full_prompt = ""
    if char_instruction:
        full_prompt += f"CHARACTER REFERENCE: {char_instruction}\n\n"
    if env_ref is not None:
        full_prompt += (
            "ENVIRONMENT REFERENCE: Use the provided environment image as reference "
            "for the living room setting. Match the same room layout, furniture, "
            "colors, and lighting.\n\n"
        )
    full_prompt += f"GENERATE THIS IMAGE: {prompt}"

    contents.append(full_prompt)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["Text", "Image"]
            ),
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return part.inline_data.data

        print("    No image in response")
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                print(f"    API text: {part.text[:200]}")
        return None

    except Exception as e:
        print(f"    Error: {e}")
        return None


def save_image(data: bytes, filename: str) -> Path:
    """Save image data to output directory, cropped to 16:9."""
    img = Image.open(io.BytesIO(data))
    img = crop_to_16_9(img)
    path = OUTPUT_DIR / filename
    img.save(path)
    print(f"    Saved {filename} ({img.size[0]}x{img.size[1]}, 16:9)")
    return path


def crop_existing_images(exclude_filenames: set):
    """Crop all existing storyboard images to 16:9 (that weren't just regenerated)."""
    print("\n" + "=" * 70)
    print("Cropping existing images to 16:9")
    print("=" * 70)

    for path in sorted(OUTPUT_DIR.glob("scene-01-panel-*.png")):
        if path.name in exclude_filenames:
            continue
        img = Image.open(path)
        w, h = img.size
        cropped = crop_to_16_9(img)
        if cropped.size != (w, h):
            cropped.save(path)
            print(f"  Cropped {path.name}: {w}x{h} -> {cropped.size[0]}x{cropped.size[1]}")
        else:
            print(f"  Already 16:9: {path.name} ({w}x{h})")


def parse_panel_spec(specs: list[str]) -> set[str]:
    """Parse panel specs like '02', '03', '08-end' into set of 'ID-frame' keys.

    If just a panel number is given (e.g. '02'), both start and end are included.
    If a specific frame is given (e.g. '08-end'), only that frame is included.
    """
    keys = set()
    for spec in specs:
        if "-" in spec:
            # Specific frame like '08-end'
            keys.add(spec)
        else:
            # Both frames
            keys.add(f"{spec}-start")
            keys.add(f"{spec}-end")
    return keys


def main():
    parser = argparse.ArgumentParser(description="Scene 1 v2 storyboard generator (fixed)")
    parser.add_argument("--panels", nargs="+",
                        help="Specific panels to regenerate (e.g. 02 03 05 08-end 09)")
    parser.add_argument("--crop-only", action="store_true",
                        help="Only crop existing images to 16:9, no regeneration")
    args = parser.parse_args()

    print("=" * 70)
    print("Scene 1 v2 Storyboard Generator (FIXED)")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput: {OUTPUT_DIR}")

    if args.crop_only:
        crop_existing_images(set())
        return 0

    # Determine which panels to generate
    if args.panels:
        target_keys = parse_panel_spec(args.panels)
        print(f"\nRegenerating specific panels: {sorted(target_keys)}")
    else:
        target_keys = None  # All panels

    # Load character references
    print("\nLoading character references...")
    load_character_refs()
    if not CHAR_REFS:
        print("ERROR: No character references loaded!")
        return 1

    # Load environment reference from existing panel 01
    env_ref_path = OUTPUT_DIR / "scene-01-panel-01-start.png"
    env_ref_image = None
    if env_ref_path.exists():
        env_ref_image = Image.open(env_ref_path)
        print(f"\nLoaded environment reference: {env_ref_path}")
    else:
        print("\nWARNING: No environment reference image found")

    # Generate panels
    results = {}
    regenerated_files = set()

    for panel in PANELS:
        pid = panel["id"]
        chars = panel["chars"]
        char_inst = panel.get("char_instruction", "")

        for frame in ["start", "end"]:
            key = f"{pid}-{frame}"
            filename = f"scene-01-panel-{pid}-{frame}.png"

            # Skip if not in target list
            if target_keys and key not in target_keys:
                continue

            prompt = panel[f"{frame}_prompt"]
            char_list = ", ".join(chars) if chars else "none"
            print(f"\n  [{key}] Panel {pid} {frame.upper()} (chars: {char_list})")

            data = generate_image(prompt, chars, char_inst, env_ref_image)
            if data:
                save_image(data, filename)
                regenerated_files.add(filename)
                results[key] = True
            else:
                print(f"    ✗ Failed")
                results[key] = False

            time.sleep(10)

    # Crop remaining existing images to 16:9
    crop_existing_images(regenerated_files)

    # Summary
    print("\n" + "=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)

    success = sum(1 for v in results.values() if v)
    total = len(results)

    for key, ok in sorted(results.items()):
        status = "✓" if ok else "✗"
        print(f"  {status} scene-01-panel-{key}.png")

    print(f"\n  {success}/{total} images generated successfully")
    print(f"  Estimated API cost: ~${total * 0.04:.2f}")

    # Verify all 18 images are 16:9
    print("\n  Verifying 16:9 aspect ratio on all images...")
    all_ok = True
    for path in sorted(OUTPUT_DIR.glob("scene-01-panel-*.png")):
        img = Image.open(path)
        w, h = img.size
        ratio = w / h
        status = "✓" if abs(ratio - 16/9) < 0.02 else "✗"
        if status == "✗":
            all_ok = False
        print(f"    {status} {path.name}: {w}x{h} (ratio: {ratio:.3f})")

    if not all_ok:
        print("\n  WARNING: Some images are not 16:9!")

    generated = sorted(OUTPUT_DIR.glob("scene-01-panel-*.png"))
    print(f"\n  Total files on disk: {len(generated)}")

    if success < total:
        print(f"\n  WARNING: {total - success} panels failed. Re-run to retry.")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
