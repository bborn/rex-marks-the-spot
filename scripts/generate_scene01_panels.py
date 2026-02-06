#!/usr/bin/env python3
"""
Generate all 9 storyboard panels for Act 1, Scene 1.
Uses Gemini image generation with character reference images.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from google import genai
from google.genai import types

# Configuration
MODEL = "gemini-2.0-flash-exp-image-generation"
OUTPUT_DIR = Path(__file__).parent / "storyboards"
REFS_DIR = Path(__file__).parent / "refs"
R2_DEST = "r2:rex-assets/storyboards/act1/scene-01/"
R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/storyboards/act1/scene-01"

# Local character reference files (downloaded from R2)
CHAR_REFS = {
    "mia": REFS_DIR / "mia_turnaround_APPROVED.png",
    "leo": REFS_DIR / "leo_turnaround_APPROVED.png",
    "nina": REFS_DIR / "nina_turnaround_v5.png",
    "gabe": REFS_DIR / "gabe_turnaround_v4.png",
}

# Style prefix for all panels
STYLE_PREFIX = (
    "Professional animation storyboard panel in black and white pencil sketch style. "
    "Pixar-like cartoon aesthetic with clean expressive lines. Cinematic composition. "
    "Slight gray shading for depth. Looks like a real animation studio storyboard drawing. "
)

# Panel definitions
PANELS = [
    {
        "id": "01",
        "name": "Panel 1A - Wide Establishing Shot",
        "chars_needed": ["mia", "leo"],
        "prompt": (
            "Wide establishing shot of a cozy family living room at evening. "
            "A large TV is on the left side showing a colorful cartoon. "
            "Two kids sit on a couch center-left: an 8-year-old girl (Mia) with her legs tucked under her, "
            "and a 5-year-old boy (Leo) in dinosaur pajamas clutching a plush T-Rex. "
            "A teenage girl (Jenny) sits in an armchair far right, head down looking at her phone. "
            "Through the windows, a dark stormy sky with lightning. Dinosaur toys scattered on floor. "
            "Warm interior lighting contrasts with cool storm light outside. Slightly cluttered family home. "
            "The parents are visible as blurry figures moving in the background near the kitchen."
        ),
    },
    {
        "id": "02",
        "name": "Panel 1B - Medium Shot Leo",
        "chars_needed": ["leo"],
        "prompt": (
            "Medium shot of Leo, a cute 5-year-old boy sitting cross-legged on a couch. "
            "He wears green dinosaur pajamas with cartoon dino patterns. He's hugging a plush T-Rex toy lovingly. "
            "Several plastic dinosaur toys are scattered around him on the couch - a T-Rex, Triceratops, pterodactyl. "
            "His face is lit by soft TV glow. He looks content and happy watching TV. "
            "Mia (his older sister) is partially visible at the edge of the frame. "
            "The mood is warm and cozy."
        ),
    },
    {
        "id": "03",
        "name": "Panel 1C - Tracking Shot Nina",
        "chars_needed": ["nina"],
        "prompt": (
            "Medium shot tracking Nina, a stylish mom in her 30s wearing an elegant black dress. "
            "She's putting on earrings while walking through the house, multitasking frantically. "
            "Her earrings catch the light. She moves with frantic but graceful energy. "
            "The background shows the domestic space - living room transitioning toward front door. "
            "Motion lines suggest movement from left to right. "
            "Her husband Gabe appears briefly as a blurred figure in the background. "
            "The mood is rushed but elegant."
        ),
    },
    {
        "id": "04",
        "name": "Panel 1D - Two-Shot Gabe and Nina",
        "chars_needed": ["gabe", "nina"],
        "prompt": (
            "Two-shot medium frame from waist up. Gabe (dad, 30s) stands screen right in a slightly rumpled tuxedo, "
            "checking his watch impatiently with rushed body language. "
            "Nina (mom, 30s) stands screen left in her elegant black dress, still putting together her look. "
            "They're having rapid-fire overlapping dialogue - speech bubbles or dialogue lines suggested. "
            "In the background, the kids are visible on the couch and Jenny the babysitter is oblivious on her phone. "
            "Gabe looks frustrated, Nina looks composed despite the chaos. "
            "Comedy timing and domestic energy."
        ),
    },
    {
        "id": "05",
        "name": "Panel 1E - Close-up Jenny",
        "chars_needed": [],
        "prompt": (
            "Close-up shot of Jenny, a 15-year-old teenage babysitter with a blonde ponytail. "
            "She's looking down at her phone, completely absorbed in texting. Oblivious to everything around her. "
            "Phone screen glow illuminates her face. She has a cheerful but disconnected expression. "
            "The background is blurred (shallow depth of field effect in sketch style). "
            "She's the picture of a typical distracted teen babysitter. "
            "Comic irony - she's supposed to be watching the kids but is totally absorbed in her phone."
        ),
    },
    {
        "id": "06",
        "name": "Panel 1F - TV Flickering Close-up",
        "chars_needed": [],
        "prompt": (
            "Close-up shot of a TV screen filling most of the frame. "
            "A colorful cartoon is playing but the image is distorted with static. "
            "Horizontal scan lines roll through the picture. The TV jitters and flickers. "
            "A brief flash of eerie blue light emanates from the screen - foreshadowing a time warp. "
            "Lightning is reflected in the TV screen surface. "
            "The feeling is ominous and mysterious - something is wrong with the TV. "
            "The sketch shows the static lines and distortion clearly with cross-hatching."
        ),
    },
    {
        "id": "07",
        "name": "Panel 1G - Over-Shoulder Kids Watching",
        "chars_needed": ["mia", "leo"],
        "prompt": (
            "Over-the-shoulder shot from behind the two kids on the couch. "
            "We see the backs of their heads: Mia (8yo girl, left) and Leo (5yo boy in dinosaur pajamas, right). "
            "They're looking toward the TV which is visible ahead of them. "
            "In the background beyond the TV, the parents (Gabe in tuxedo, Nina in black dress) are visible still rushing around. "
            "The kids are silhouetted against the TV glow. "
            "There's a contrast between the children's calm and the parents' chaos in the background. "
            "Mia looks slightly more concerned, glancing back at parents."
        ),
    },
    {
        "id": "08",
        "name": "Panel 1H - Close-up Mia",
        "chars_needed": ["mia"],
        "prompt": (
            "Close-up shot of Mia's face. She's an 8-year-old girl with big expressive eyes. "
            "She looks up at her parents (off-screen above) with an emotional, earnest expression. "
            "There's worry and need for reassurance in her face. She's asking 'Promise?' "
            "A slight TV flicker is reflected in her eyes. "
            "A brief lightning flash illuminates her face from the side. "
            "This is the emotional anchor of the scene - a child needing comfort before parents leave. "
            "The mood is warm but vulnerable. Very close framing on her face."
        ),
    },
    {
        "id": "09",
        "name": "Panel 1I - Close-up Gabe Hesitating",
        "chars_needed": ["gabe", "nina"],
        "prompt": (
            "Split composition: left side shows a close-up of Gabe's face showing conflict and hesitation. "
            "He's a dad in his 30s in a tuxedo, uncomfortable and torn. "
            "Right side pulls back to a two-shot revealing Nina next to him, giving him a sharp 'don't you dare' glare. "
            "The tension is palpable - he needs to promise his daughter he'll be back for bedtime "
            "but doesn't want to make a promise he can't keep. Nina's expression forces his hand. "
            "He finally relents. The mood shifts from tension to reluctant resolution."
        ),
    },
]


def load_image_bytes(path: Path) -> tuple:
    """Load image file as bytes and mime type."""
    data = path.read_bytes()
    return data, "image/png"


def generate_panel(client, panel: dict, char_ref_bytes: dict) -> bool:
    """Generate a single storyboard panel."""
    panel_id = panel["id"]
    panel_name = panel["name"]
    output_path = OUTPUT_DIR / f"scene-01-panel-{panel_id}.png"

    print(f"\n{'='*60}")
    print(f"Generating {panel_name}")
    print(f"Output: {output_path}")

    full_prompt = STYLE_PREFIX + panel["prompt"]

    # Build content parts with character references
    content_parts = []
    for char_name in panel["chars_needed"]:
        if char_name in char_ref_bytes:
            img_data, mime = char_ref_bytes[char_name]
            content_parts.append(types.Part.from_bytes(data=img_data, mime_type=mime))
            content_parts.append(types.Part.from_text(
                text=f"Above: approved character design for {char_name.title()}. Match this design exactly in the storyboard panel."
            ))

    content_parts.append(types.Part.from_text(
        text=f"Now generate this storyboard panel: {full_prompt}"
    ))

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=content_parts,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    img_bytes = part.inline_data.data
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    print(f"  SUCCESS: {len(img_bytes):,} bytes saved")
                    return True
                elif part.text:
                    print(f"  Text: {part.text[:200]}")

        print(f"  FAILED: No image in response")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def upload_to_r2(panel_id: str) -> str:
    """Upload a panel to R2."""
    local_path = OUTPUT_DIR / f"scene-01-panel-{panel_id}.png"
    print(f"  Uploading panel {panel_id} to R2...")
    try:
        result = subprocess.run(
            ["rclone", "copy", str(local_path), R2_DEST],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            url = f"{R2_PUBLIC}/scene-01-panel-{panel_id}.png"
            print(f"  Uploaded: {url}")
            return url
        else:
            print(f"  Upload error: {result.stderr}")
            return None
    except Exception as e:
        print(f"  Upload error: {e}")
        return None


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Act 1 Scene 1 - Storyboard Panel Generator")
    print(f"Model: {MODEL}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)

    # Configure client
    client = genai.Client(api_key=api_key)

    # Load character references
    print("\nLoading character references...")
    char_ref_bytes = {}
    for name, path in CHAR_REFS.items():
        if path.exists():
            char_ref_bytes[name] = load_image_bytes(path)
            print(f"  {name}: OK ({len(char_ref_bytes[name][0]):,} bytes)")
        else:
            print(f"  {name}: NOT FOUND at {path}")

    # Generate all panels
    results = {}
    for i, panel in enumerate(PANELS):
        success = generate_panel(client, panel, char_ref_bytes)
        results[panel["id"]] = success

        # Rate limiting between requests
        if i < len(PANELS) - 1:
            print("  Waiting 10s for rate limit...")
            time.sleep(10)

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)
    succeeded = [pid for pid, ok in results.items() if ok]
    failed = [pid for pid, ok in results.items() if not ok]
    print(f"Succeeded: {len(succeeded)}/{len(results)}")
    if failed:
        print(f"Failed: panels {', '.join(failed)}")

    # Upload successful panels to R2
    urls = {}
    if succeeded:
        print("\nUploading to R2...")
        for panel_id in succeeded:
            url = upload_to_r2(panel_id)
            if url:
                urls[panel_id] = url

    # Retry failed panels once
    if failed:
        print(f"\nRetrying {len(failed)} failed panels...")
        for panel_id in list(failed):
            panel = next(p for p in PANELS if p["id"] == panel_id)
            time.sleep(12)
            success = generate_panel(client, panel, char_ref_bytes)
            if success:
                url = upload_to_r2(panel_id)
                if url:
                    urls[panel_id] = url
                    succeeded.append(panel_id)
                    failed.remove(panel_id)

    # Final report
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(f"Generated: {len(succeeded)}/{len(results)} panels")
    if urls:
        print("\nR2 URLs:")
        for pid, url in sorted(urls.items()):
            print(f"  Panel {pid}: {url}")
    if failed:
        print(f"\nStill failed: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\nAll panels generated and uploaded successfully!")


if __name__ == "__main__":
    main()
