#!/usr/bin/env python3
"""Generate Scene 1 v2 storyboard panels using Gemini img2img with character refs.

Uses approved character turnaround sheets as visual references for consistency.
Generates START and END frames for each of 9 panels (18 images total).
"""

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
    "high quality finished look, NOT a sketch, NOT black-and-white, full color"
)

# Environment description for consistency
ENV_DESC = (
    "Cozy family living room, evening. Warm amber table lamps and overhead light. "
    "Large window showing dark stormy sky outside. TV mounted on wall. "
    "Comfortable brown couch with colorful throw pillows. Dinosaur toys scattered on floor. "
    "Wooden coffee table. Family photos on walls. Warm hardwood floors with area rug."
)

# Panel definitions
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
            "Medium shot of Leo, a 5-year-old boy in dinosaur pajamas, sitting on a brown couch "
            "hugging a plush T-Rex toy. He looks content and happy watching TV. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Medium shot of Leo, a 5-year-old boy in dinosaur pajamas, sitting on a brown couch "
            "with a plush T-Rex toy. He glances down at his toy dinosaurs on the couch beside him "
            "with a slight warm smile. "
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
            "She wears an elegant black dress, getting ready for a fancy date night."
        ),
        "start_prompt": (
            "Medium tracking shot of Nina, an elegant woman in a black dress, walking through "
            "the living room putting on earrings. She moves gracefully. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Medium shot of Nina, an elegant woman in a black dress, near the front door area, "
            "checking her purse with frantic but graceful movement. Slight urgency in her posture. "
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
            "soft around the middle, NOT muscular. He wears a tuxedo. "
            "The woman is Nina, the mother - match EXACTLY from her turnaround. Elegant black dress. "
        ),
        "start_prompt": (
            "Two-shot of Gabe and Nina. Gabe in a tuxedo checking his watch impatiently, slightly frustrated. "
            "Nina still putting finishing touches on her outfit. Two kids visible on couch in background. "
            "Comedy staging - the contrast between his impatience and her composure. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Two-shot of Gabe and Nina. Gabe gesturing urgently with both hands, comically exasperated. "
            "Nina calm and composed, giving him a look. Classic comedy couple staging. "
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
            "The teenager is Jenny, the babysitter, age 15. Match EXACTLY from her turnaround sheet: "
            "blonde ponytail, casual teen clothing. She is glued to her phone."
        ),
        "start_prompt": (
            "Close-up insert shot of Jenny, a 15-year-old babysitter with blonde ponytail, "
            "looking down at her phone with an oblivious expression, texting. Phone screen glow on her face. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Close-up insert shot of Jenny, a 15-year-old babysitter with blonde ponytail, "
            "giving a brief distracted nod without looking up from her phone. Phone glow illuminating her face. "
            "Totally absorbed in texting. "
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
            "Match their hair and clothing from the turnaround sheets. We see the backs of their heads."
        ),
        "start_prompt": (
            "Over-the-shoulder shot from behind two children sitting on a couch watching TV. "
            "Girl (8, wavy hair) and boy (5, dinosaur pajamas) seen from behind. "
            "Parents blurred in the background rushing around getting ready. TV visible ahead. "
            f"Living room setting: {ENV_DESC} "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Over-the-shoulder shot from behind two children on couch. "
            "The girl (Mia, 8) turns her head slightly to look back at parents with concern on her face. "
            "Boy (Leo, 5, dinosaur pajamas) still watching TV. Parents blurred in background. "
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
            "saying 'Promise?' with an earnest, emotional expression. TV light reflected in her eyes. "
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
            "soft/round face, warm expression. The woman behind him is Nina - match from her turnaround."
        ),
        "start_prompt": (
            "Cinematic close-up of Gabe, a father in his early 40s with glasses and slight stubble, "
            "showing conflict and hesitation on his face. He's torn about leaving his kids. "
            "Warm lighting, shallow depth of field. Emotional weight. "
            f"{STYLE}"
        ),
        "end_prompt": (
            "Cinematic close-up of Gabe with glasses and stubble, saying 'Promise' with a mix of "
            "relief and lingering guilt. Behind him, slightly out of focus, Nina gives him a stern glare. "
            "Comedy meets emotion. Warm lighting. "
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
        # Print any text response for debugging
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                print(f"    API text: {part.text[:200]}")
        return None

    except Exception as e:
        print(f"    Error: {e}")
        return None


def save_image(data: bytes, filename: str) -> Path:
    """Save image data to output directory."""
    path = OUTPUT_DIR / filename
    with open(path, "wb") as f:
        f.write(data)
    return path


def main():
    print("=" * 70)
    print("Scene 1 v2 Storyboard Generator - Gemini img2img with Character Refs")
    print("=" * 70)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput: {OUTPUT_DIR}")

    # Load character references
    print("\nLoading character references...")
    load_character_refs()
    if not CHAR_REFS:
        print("ERROR: No character references loaded!")
        return 1

    # Phase 1: Generate hero establishing shot for environment locking
    print("\n" + "=" * 70)
    print("PHASE 1: Generating hero establishing shot for environment reference")
    print("=" * 70)

    env_ref_image = None
    panel_01 = PANELS[0]
    print(f"\n  Generating Panel 01 START (environment hero)...")
    env_data = generate_image(panel_01["start_prompt"], [], "")
    if env_data:
        save_image(env_data, "scene-01-panel-01-start.png")
        # Load as PIL Image for use as reference
        import io
        env_ref_image = Image.open(io.BytesIO(env_data))
        print("    ✓ Environment hero shot saved and loaded as reference")
    else:
        print("    ✗ Failed to generate environment hero shot")
        print("    Continuing without environment reference...")

    time.sleep(10)

    # Now generate Panel 01 END
    print(f"\n  Generating Panel 01 END...")
    end_data = generate_image(panel_01["end_prompt"], [], "", env_ref_image)
    if end_data:
        save_image(end_data, "scene-01-panel-01-end.png")
        print("    ✓ Panel 01 END saved")
    else:
        print("    ✗ Failed")

    time.sleep(10)

    # Phase 2: Generate all remaining panels
    print("\n" + "=" * 70)
    print("PHASE 2: Generating panels 02-09 with character refs + environment ref")
    print("=" * 70)

    results = {"01-start": env_data is not None, "01-end": end_data is not None}

    for panel in PANELS[1:]:  # Skip panel 01, already done
        pid = panel["id"]
        chars = panel["chars"]
        char_inst = panel.get("char_instruction", "")

        for frame in ["start", "end"]:
            key = f"{pid}-{frame}"
            prompt = panel[f"{frame}_prompt"]

            char_list = ", ".join(chars) if chars else "none"
            print(f"\n  [{key}] Panel {pid} {frame.upper()} (chars: {char_list})")

            data = generate_image(prompt, chars, char_inst, env_ref_image)
            if data:
                filename = f"scene-01-panel-{pid}-{frame}.png"
                save_image(data, filename)
                print(f"    ✓ Saved {filename}")
                results[key] = True
            else:
                print(f"    ✗ Failed")
                results[key] = False

            time.sleep(10)

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

    # Cost estimate: Gemini 2.0 Flash is ~$0.04/image for img2img
    est_cost = total * 0.04
    print(f"  Estimated API cost: ~${est_cost:.2f} ({total} calls × $0.04)")

    # List generated files
    print(f"\n  Output directory: {OUTPUT_DIR}")
    generated = sorted(OUTPUT_DIR.glob("scene-01-panel-*.png"))
    print(f"  Files on disk: {len(generated)}")

    if success < total:
        print(f"\n  WARNING: {total - success} panels failed. Re-run to retry.")

    return 0 if success == total else 1


if __name__ == "__main__":
    sys.exit(main())
