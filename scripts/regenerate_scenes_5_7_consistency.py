#!/usr/bin/env python3
"""
Act 1 Scenes 5-7 Consistency Audit - Panel Regeneration

Regenerates off-model panels using approved character turnaround images as
references to enforce character lock. Uses Gemini image generation with
multimodal input (turnaround image + enhanced prompt).

Panels to regenerate:
1. Scene 05 Panel 02 - Gabe & Nina terror reaction (both off-model)
2. Scene 06 Panel 01 - Wide TV explodes (wrong figure count, 4 instead of 3)
3. Scene 06 Panel 02 - Reaction shot (all 3 characters off-model)
4. Scene 06 Panel 03 - Low light atmosphere (wrong count/silhouettes)
5. Scene 07 Panel 01 - Nina wakes close-up (completely off-model)
6. Scene 07 Panel 04 - Nina rouses Gabe (both off-model)

Usage:
    GEMINI_API_KEY=... python scripts/regenerate_scenes_5_7_consistency.py
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional
from io import BytesIO
from urllib.request import urlopen

import google.generativeai as genai
from PIL import Image

# Configuration
MODEL = "gemini-2.0-flash-exp-image-generation"
R2_BASE = "r2:rex-assets/storyboards/act1/panels/"
R2_PUBLIC_URL = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"
OUTPUT_DIR = Path(__file__).parent / "output" / "consistency_regen"
DELAY_BETWEEN_REQUESTS = 8  # seconds

# Approved turnaround URLs
TURNAROUND_URLS = {
    "gabe": f"{R2_PUBLIC_URL}/characters/gabe/gabe_turnaround_APPROVED.png",
    "nina": f"{R2_PUBLIC_URL}/characters/nina/nina_turnaround_APPROVED.png",
    "mia": f"{R2_PUBLIC_URL}/characters/mia/mia_turnaround_APPROVED.png",
    "leo": f"{R2_PUBLIC_URL}/characters/leo/leo_turnaround_APPROVED.png",
    "jenny": f"{R2_PUBLIC_URL}/characters/jenny/jenny_turnaround_APPROVED.png",
}

# Character description blocks matching approved turnarounds
CHAR_GABE = """GABE (the father, early 40s): Pixar-style 3D animated character.
- Dark brown wavy hair, slightly receding at temples
- Rectangular modern glasses (thin frames) - MUST have glasses
- Light stubble/five o'clock shadow
- Soft dad bod, NOT muscular - average build, slightly soft around middle
- In this scene: wearing a BLACK TUXEDO (formal date night attire)
- Warm brown eyes, slightly tired expression"""

CHAR_NINA = """NINA (the mother, late 30s): Pixar-style 3D animated character.
- Auburn/reddish-brown wavy shoulder-length hair (NOT black, NOT straight)
- Hazel-green eyes, freckles on cheeks
- Natural mom body, warm features
- In this scene: wearing an ELEGANT BLACK COCKTAIL DRESS (formal date night attire)
- White sneakers or heels depending on scene"""

CHAR_NINA_DISHEVELED = """NINA (the mother, late 30s): Pixar-style 3D animated character.
- Auburn/reddish-brown wavy shoulder-length hair, NOW DISHEVELED with debris
- Hazel-green eyes, freckles on cheeks
- Natural mom body, warm features
- Formal black cocktail dress now dirty and mussed from crash
- Dirt smudges on face, hair messy"""

CHAR_GABE_DISHEVELED = """GABE (the father, early 40s): Pixar-style 3D animated character.
- Dark brown wavy hair, now messy from crash
- Rectangular modern glasses (thin frames) - MUST have glasses, possibly askew
- Light stubble, small cut or bruise on forehead
- Soft dad bod, average build
- Black tuxedo now dirty and wrinkled from crash"""

CHAR_MIA = """MIA (daughter, 8 years old): Pixar-style 3D animated character.
- Dark brown curly hair with pink scrunchie/ponytail
- Light tan/olive complexion
- Big expressive brown eyes
- Wearing PINK polka-dot t-shirt and blue jeans with red sneakers
- Small, concerned expression"""

CHAR_LEO = """LEO (son, 5 years old): Pixar-style 3D animated character.
- Sandy BLONDE curly hair (NOT dark hair - he's the only blonde child)
- Fair skin, blue eyes, gap-toothed smile
- Round cherub face, small and cute
- Wearing GREEN dinosaur t-shirt, cargo shorts, red sneakers
- Clutching a small GREEN plush/plastic T-Rex toy"""

CHAR_JENNY = """JENNY (teenage babysitter, 15 years old): Pixar-style 3D animated character.
- Dark brown curly hair in a loose ponytail
- Darker skin tone, brown eyes
- Wearing CORAL/SALMON zip-up hoodie with dark gray leggings
- White sneakers
- Always has her phone in hand, slightly taller than the kids
- Bored/distracted teenage expression"""

# Panels to regenerate with enhanced prompts
PANELS_TO_REGEN = [
    {
        "filename": "scene-05-panel-02.png",
        "characters": ["gabe", "nina"],
        "prompt": f"""Generate a Pixar-style 3D animated storyboard panel, 16:9 cinematic widescreen composition.

SCENE: Interior of car at night during time warp event. Medium two-shot from dashboard perspective.

{CHAR_GABE}
{CHAR_NINA}

COMPOSITION:
- Gabe is on the LEFT (driver's seat), gripping the steering wheel, bracing for impact, mouth open screaming in terror
- Nina is on the RIGHT (passenger seat), hands up defensively, phone falling from her hand, screaming
- Bright blue time warp light (#0096FF) flooding through the windshield, washing over both of them
- Dashboard lights flickering wildly
- Camera shake energy suggesting violent impact
- Blue light casting dramatic shadows on their terrified faces
- Both in formal date night attire (tuxedo and black dress)

The characters MUST match the reference turnaround sheets provided - same face shapes, hair colors, and features.
Pixar animation style, dramatic lighting, cinematic composition.""",
    },
    {
        "filename": "scene-06-panel-01.png",
        "characters": ["jenny", "mia", "leo"],
        "prompt": f"""Generate a Pixar-style 3D animated storyboard panel, 16:9 cinematic widescreen composition.

SCENE: Cozy living room at night. Wide shot showing the TV and couch area. Supernatural moment.

{CHAR_JENNY}
{CHAR_MIA}
{CHAR_LEO}

COMPOSITION:
- Wide living room shot from behind/side angle
- EXACTLY THREE people on/near the couch - NO MORE, NO LESS:
  1. Jenny (tallest, teen) sitting on one end
  2. Mia (medium, 8yo girl) in the middle area
  3. Leo (smallest, 5yo boy) on the other side
- TV is in front of them, fizzling with blue electrical static (#0096FF)
- Small poof of smoke and blue sparks from the TV screen going black
- Blue electrical crackle matching time warp color
- Warm amber living room lighting interrupted by blue TV static
- Cozy domestic scene disrupted by supernatural event
- Storm visible through windows in background

CRITICAL: Only 3 figures visible - Jenny, Mia, and Leo. No other people.
The characters MUST match the reference turnaround sheets provided.
Pixar animation style, cinematic composition.""",
    },
    {
        "filename": "scene-06-panel-02.png",
        "characters": ["mia", "leo", "jenny"],
        "prompt": f"""Generate a Pixar-style 3D animated storyboard panel, 16:9 cinematic widescreen composition.

SCENE: Living room reaction shot after TV goes out. Medium group shot of three startled faces.

{CHAR_MIA}
{CHAR_LEO}
{CHAR_JENNY}

COMPOSITION:
- Medium close-up group shot showing EXACTLY three faces reacting in fear/shock:
- SCREEN LEFT: Mia (8yo girl) - dark brown curly hair with pink scrunchie, olive skin, big scared brown eyes, wearing pink polka-dot shirt
- CENTER: Leo (5yo boy) - sandy BLONDE curly hair, fair skin, blue eyes, clutching his GREEN dinosaur toy tightly, wearing green dino shirt
- SCREEN RIGHT: Jenny (15yo teen) - dark brown hair in ponytail, darker skin, coral hoodie, finally looking UP from her phone which illuminates her face, phone still in hand
- All three faces showing fear, confusion, sudden shock
- Eerie blue-ish ambient light from the now-dead TV
- Dark living room background

CRITICAL: Leo has BLONDE hair (he's the only blonde). Jenny has DARK BROWN hair and coral hoodie. Mia has dark brown curly hair with pink scrunchie.
The characters MUST match the reference turnaround sheets provided exactly.
Pixar animation style, dramatic lighting, cinematic composition.""",
    },
    {
        "filename": "scene-06-panel-03.png",
        "characters": ["jenny", "mia", "leo"],
        "prompt": f"""Generate a Pixar-style 3D animated storyboard panel, 16:9 cinematic widescreen composition.

SCENE: Living room plunged into darkness. Wide shot, eerie atmosphere.

{CHAR_JENNY}
{CHAR_MIA}
{CHAR_LEO}

COMPOSITION:
- Wide shot of the living room now dark, lit only by cool blue moonlight through windows
- EXACTLY THREE silhouettes/figures visible on the couch:
  1. Jenny (tallest figure, on one side) - lit slightly by her phone's glow
  2. Mia (medium-sized, 8yo) - silhouetted
  3. Leo (smallest, 5yo) - silhouetted, huddled close
- Dead TV is a dark void in the center of the room
- Cool blue moonlight streaming through windows creating long shadows
- Deep unsettling shadows throughout the room
- Storm still visible outside through windows
- Atmosphere has completely shifted from cozy to eerie
- Phone glow is the only warm light source, illuminating Jenny slightly

CRITICAL: Exactly 3 figures, not 4 or more. The tallest is Jenny, medium is Mia, smallest is Leo.
Pixar animation style, moody atmospheric lighting, cinematic composition.""",
    },
    {
        "filename": "scene-07-panel-01.png",
        "characters": ["nina"],
        "prompt": f"""Generate a Pixar-style 3D animated storyboard panel, 16:9 cinematic widescreen composition.

SCENE: Close-up of Nina waking up in the crashed car. Morning/day light.

{CHAR_NINA_DISHEVELED}

COMPOSITION:
- Extreme close-up of Nina's face, filling most of the frame
- Her eyes are fluttering open, adjusting to bright warm daylight (NOT storm light)
- Auburn/reddish-brown wavy hair is disheveled, messy from the crash
- Freckles visible on her cheeks
- Small bits of dirt and debris on her face
- Hazel-green eyes showing confusion, disorientation
- Soft warm golden light hitting her face from the side
- Slightly blurred background suggesting car interior
- Phone barely visible in her hand at bottom of frame
- Expression: slowly waking, confused, dazed

CRITICAL: This is NINA - she has auburn/reddish-brown WAVY hair (not black, not straight), hazel-green eyes, and freckles. She must match the reference turnaround provided.
Pixar animation style, intimate close-up, cinematic composition.""",
    },
    {
        "filename": "scene-07-panel-04.png",
        "characters": ["nina", "gabe"],
        "prompt": f"""Generate a Pixar-style 3D animated storyboard panel, 16:9 cinematic widescreen composition.

SCENE: Two-shot inside the crashed car. Nina reaches to wake Gabe. Bright daylight.

{CHAR_NINA_DISHEVELED}
{CHAR_GABE_DISHEVELED}

COMPOSITION:
- Medium two-shot inside the wrecked car interior
- GABE on the LEFT (driver's side): slumped against the steering wheel, semi-conscious, dark brown wavy hair messy, rectangular GLASSES still on but slightly askew, small cut on forehead, black tuxedo dirty and wrinkled
- NINA on the RIGHT (passenger side): leaning toward Gabe with concern, reaching out to touch his shoulder/shake him awake, auburn wavy hair disheveled, black cocktail dress dirty
- Bright warm daylight streaming through cracked/shattered windshield behind them
- Car interior shows crash damage - cracked glass, debris, items scattered
- Nina's expression: worried, concerned, trying to wake him
- Gabe's expression: groggy, barely responding

CRITICAL: Gabe MUST have rectangular glasses. Nina has auburn/reddish-brown wavy hair and freckles. Both must match the reference turnarounds provided.
Pixar animation style, dramatic two-shot, cinematic composition.""",
    },
]


def load_turnaround(char_name: str) -> Image.Image:
    """Load a turnaround image from local cache or download via rclone."""
    local_cache = Path("/tmp/audit/turnarounds")
    local_path = local_cache / f"{char_name}_turnaround_APPROVED.png"

    if local_path.exists():
        print(f"  Loading turnaround (cached): {local_path.name}")
        img = Image.open(local_path)
    else:
        # Download via rclone
        r2_path = f"r2:rex-assets/characters/{char_name}/{char_name}_turnaround_APPROVED.png"
        print(f"  Downloading turnaround: {r2_path}")
        local_cache.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["rclone", "copy", r2_path, str(local_cache)],
            capture_output=True, text=True, timeout=30,
        )
        if not local_path.exists():
            raise FileNotFoundError(f"Failed to download {r2_path}")
        img = Image.open(local_path)

    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def generate_panel(model_instance, panel: dict, turnaround_images: dict) -> Optional[Path]:
    """Generate a single panel with character turnaround references."""
    filename = panel["filename"]
    output_path = OUTPUT_DIR / filename

    print(f"\nGenerating: {filename}")

    # Build multimodal content: turnaround images + prompt
    content_parts = []

    # Add character reference images
    chars = panel["characters"]
    ref_text = "CHARACTER REFERENCE SHEETS (the generated characters MUST match these designs):\n"
    for i, char_name in enumerate(chars, 1):
        ref_text += f"\nReference {i} - {char_name.upper()} turnaround sheet:"
        content_parts.append(ref_text)
        content_parts.append(turnaround_images[char_name])
        ref_text = ""

    # Add the main prompt
    content_parts.append("\n\nNow generate the following storyboard panel:\n\n" + panel["prompt"])

    try:
        response = model_instance.generate_content(
            content_parts,
            generation_config={
                "response_modalities": ["IMAGE", "TEXT"],
            },
        )

        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    img_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    size_kb = len(img_bytes) / 1024
                    print(f"  SUCCESS: Saved {filename} ({size_kb:.0f} KB)")
                    return output_path

        # Check for text-only response (sometimes includes safety feedback)
        if hasattr(response, "candidates") and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    print(f"  Model response text: {part.text[:200]}")

        print(f"  FAILED: No image data in response")
        return None

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def upload_to_r2(local_path: Path, filename: str) -> Optional[str]:
    """Upload generated panel to R2."""
    dest = R2_BASE
    print(f"  Uploading {filename} to R2...")
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), dest],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            url = f"{R2_PUBLIC_URL}/storyboards/act1/panels/{filename}"
            print(f"  Uploaded: {url}")
            return url
        else:
            print(f"  Upload failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"  Upload error: {e}")
        return None


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    print("=" * 70)
    print("Act 1 Scenes 5-7 Consistency Audit - Panel Regeneration")
    print(f"Model: {MODEL}")
    print(f"Panels to regenerate: {len(PANELS_TO_REGEN)}")
    print(f"Delay between requests: {DELAY_BETWEEN_REQUESTS}s")
    print("=" * 70)

    # Configure Gemini
    genai.configure(api_key=api_key)
    model_instance = genai.GenerativeModel(MODEL)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Pre-load all needed turnaround images
    print("\nLoading approved character turnarounds...")
    needed_chars = set()
    for panel in PANELS_TO_REGEN:
        needed_chars.update(panel["characters"])

    turnaround_images = {}
    for char_name in needed_chars:
        turnaround_images[char_name] = load_turnaround(char_name)
    print(f"Loaded {len(turnaround_images)} turnaround sheets\n")

    # Generate each panel
    results = []
    for i, panel in enumerate(PANELS_TO_REGEN):
        result = generate_panel(model_instance, panel, turnaround_images)
        results.append((panel["filename"], result))

        if i < len(PANELS_TO_REGEN) - 1:
            print(f"  Waiting {DELAY_BETWEEN_REQUESTS}s before next request...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Upload successful generations to R2
    print("\n" + "=" * 70)
    print("Uploading to R2...")
    print("=" * 70)

    uploaded = []
    for filename, local_path in results:
        if local_path:
            url = upload_to_r2(local_path, filename)
            if url:
                uploaded.append((filename, url))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    success_count = sum(1 for _, path in results if path is not None)
    print(f"Generated: {success_count}/{len(PANELS_TO_REGEN)}")
    print(f"Uploaded:  {len(uploaded)}/{success_count}")

    if uploaded:
        print("\nRegenerated panels:")
        for filename, url in uploaded:
            print(f"  {filename}: {url}")

    failed = [(fn, p) for fn, p in results if p is None]
    if failed:
        print("\nFailed panels:")
        for filename, _ in failed:
            print(f"  {filename}")

    return 0 if success_count == len(PANELS_TO_REGEN) else 1


if __name__ == "__main__":
    sys.exit(main())
