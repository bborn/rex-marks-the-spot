#!/usr/bin/env python3
"""Regenerate Scene 1 storyboard panels on-model against the locked turnarounds.

Reads asset-bible/manifests/scene-01.json. For each shot, feeds the locked
turnaround of every manifest character to gemini-3-pro-image-preview as
image-to-image references, with a prompt that locks identity to the
turnarounds and pulls wardrobe + composition + key_props from the manifest.

Outputs to storyboards/v4/scene-01/scene-01-{shot_id}-start.png.

Usage:
  python3 scripts/regen_scene01_v4.py                  # all 9
  python3 scripts/regen_scene01_v4.py 1A 1E 1H         # subset
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

MODEL = "gemini-3-pro-image-preview"
DELAY = 10  # seconds between calls (>=8 per CLAUDE.md)

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "asset-bible/manifests/scene-01.json"
CHAR_DIR = ROOT / "asset-bible/characters"
OUT_DIR = ROOT / "storyboards/v4/scene-01"

# Per-character identity blurb: what the model MUST honor from the turnaround.
# These are short, factual descriptions of each turnaround so the model can
# resolve which reference image maps to which character in the prompt.
CHAR_IDENTITY = {
    "Mia": (
        "girl, ~7-9 years old, light skin, voluminous dark brown curly hair "
        "worn DOWN (never a bun or tight ponytail), big brown eyes, slim child build"
    ),
    "Leo": (
        "boy, ~4-5 years old, light skin, short blond/golden tousled hair, "
        "round friendly face, blue eyes, small child build"
    ),
    "Jenny": (
        "teenage girl, ~15 years old, mid-brown skin tone, dark brown wavy hair "
        "(typically in a low/mid ponytail), thin teen build"
    ),
    "Nina": (
        "adult woman, mom, fair skin, auburn / red-brown wavy shoulder-length hair, "
        "green eyes, slightly curvy build"
    ),
    "Gabe": (
        "adult man, dad, fair skin, dark brown hair, ALWAYS wearing his "
        "black-framed glasses (signature feature - never remove them), "
        "light dark-brown stubble/scruff on jaw and chin, soft build (a bit "
        "chubby around the middle)"
    ),
    "Ruben": (
        "fairy godfather character per turnaround"
    ),
    "Jetplane": (
        "color-farting dinosaur character per turnaround"
    ),
}

STYLE = (
    "Render as a single 16:9 widescreen storyboard frame in a premium 3D-animated "
    "feature-film look (Pixar / DreamWorks style) - SAME stylized 3D-character art "
    "style as the reference turnarounds (slightly cartoonish proportions, "
    "exaggerated expressive features, NOT photorealistic humans). Cinematic "
    "lighting, soft volumetric atmosphere. Aspect ratio: 16:9 fills the entire "
    "image (do NOT add letterbox black bars). DO NOT draw multiple poses, "
    "turnaround sheets, model sheets, or any UI/text - produce a single "
    "in-world cinematic frame."
)


def _shot_caption(shot_id: str) -> str:
    """Per-shot composition note, derived from storyboards/act1/scene-01-home-evening.md."""
    captions = {
        "1A": (
            "Wide establishing shot of the family living room at evening. "
            "Frame composition: TV on the left side of frame; couch center-left with the "
            "two kids on it (Mia screen-left with legs tucked under, Leo screen-right "
            "clutching his plush T-Rex); armchair far right with Jenny absorbed in her phone; "
            "kitchen visible in the background-right; Nina and Gabe seen in the background, "
            "in date-night formalwear, moving through the space getting ready to leave. "
            "Dinosaur toys (plush T-Rex, plastic Triceratops, pterodactyl) scattered on "
            "floor and couch. Warm amber interior lamps, contrasting with a dark stormy "
            "sky and a lightning flash visible THROUGH the windows (lightning OUTSIDE only, "
            "never inside the room). Cozy but slightly cluttered. STATIC camera."
        ),
        "1B": (
            "Medium shot on Leo, slight push-in. Leo center frame, sitting cross-legged on "
            "the couch, hugging a plush T-Rex toy. Plastic dinosaur toys (T-Rex, Triceratops, "
            "pterodactyl) scattered around him on the couch and floor. Soft warm TV glow on "
            "his face from camera-left. Mia partially visible at the frame edge (screen-left) "
            "as a small slice - back/shoulder, not full face. Cozy living room background."
        ),
        "1C": (
            "Medium tracking shot following Nina, camera tracks left-to-right. "
            "Nina center frame, mid-stride moving from living room toward the front door "
            "area, putting on an earring as she walks. Gabe appears briefly in the "
            "background (also in tuxedo); Jenny passed by in the background on the armchair "
            "absorbed in her phone. Earrings catching the lamp light. Frantic but graceful "
            "motion. Warm interior, stormy sky through windows."
        ),
        "1D": (
            "Two-shot of Gabe and Nina together, medium shot from the waist up, STATIC. "
            "They share the frame in date-night formalwear. Gabe is checking his "
            "wristwatch (impatient). Nina alongside him. In the soft-focus background, "
            "the kids are seen on the couch (Mia and Leo) and Jenny in the armchair "
            "absorbed in her phone (oblivious). Warm living room lighting; stormy sky "
            "through the windows."
        ),
        "1E": (
            "Close-up insert on Jenny only. Jenny center frame, head tilted DOWN at her "
            "glowing phone (screen lighting her face cool-blue from below). Shallow depth "
            "of field, the living-room background blurred. Phone is the key prop. STATIC. "
            "She is completely absorbed in texting - oblivious to the family. "
            "No other characters in focus."
        ),
        "1F": (
            "Close-up insert of just the TV screen filling most of the frame. "
            "A colorful cartoon image distorted by static interference, with horizontal "
            "scan lines rolling through. A brief blue time-warp flash in the picture "
            "(foreshadowing). A lightning flash is faintly reflected in the screen glass. "
            "STATIC camera. No characters visible (insert shot)."
        ),
        "1G": (
            "Over-the-shoulder shot from BEHIND the two kids on the couch, looking past "
            "them toward the TV. The TV (with cartoon glow) is the focal point past the "
            "kids. We see the kids from behind/silhouette: Mia screen-left (back of head "
            "visible - voluminous dark curly hair worn down) and Leo screen-right (back "
            "of head, in green dino-print pajama top). In the background past the couch, "
            "ONLY TWO adults visible: NINA, who has AUBURN / COPPER-RED wavy hair and "
            "fair (pale white) skin, wearing the long black formal dress; and GABE, who "
            "has FAIR (PALE WHITE) SKIN (definitely NOT dark-skinned, NOT brown-skinned), "
            "dark brown hair, and black-framed glasses, wearing the black tuxedo. Their "
            "skin tones and hair colors must match the attached turnarounds even at "
            "background distance. EXACTLY 4 people total in the frame: 2 kids in front "
            "+ 2 parents in back. Do not add any other adults or kids."
        ),
        "1H": (
            "Close-up on Mia, slow push-in. Mia center frame, looking UP at her parents "
            "off-screen (above frame). Big expressive eyes, vulnerable / earnest emotion. "
            "The TV flicker reflects faintly in her eyes. A lightning flash (visible "
            "OUTSIDE only, e.g. through a window, never as a bolt drawn inside the room) "
            "briefly illuminates her face from camera-right. Warm but tense atmosphere. "
            "This is the emotional anchor of the scene - so she must be unmistakably "
            "Mia: voluminous dark CURLY hair worn DOWN (NOT a ponytail, NOT a bun), "
            "wearing casual home wear (NOT pajamas). No other characters in focus."
        ),
        "1I": (
            "Starts as a close-up on Gabe's face, then PULLs back to a two-shot with "
            "Nina entering frame from screen-left. Gabe wears a black tuxedo, conflicted "
            "expression. Nina wears the elegant black formal dress, giving him a sharp "
            "'don't-you-dare' glare. Front-door area of the living room. Warm lamp light, "
            "stormy night beyond the windows. Just these two characters in focus."
        ),
    }
    return captions.get(shot_id, "")


def _load_manifest() -> list[dict]:
    with open(MANIFEST) as f:
        return json.load(f)


def _resolve_char_ref(name: str) -> Path:
    p = CHAR_DIR / f"{name.lower()}_turnaround_APPROVED.png"
    if not p.exists():
        raise FileNotFoundError(f"Turnaround not found: {p}")
    return p


def _img_to_part(path: Path, max_edge: int = 1600) -> types.Part:
    img = Image.open(path)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_edge:
        s = max_edge / float(max(w, h))
        img = img.resize((int(w * s), int(h * s)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png")


def _build_prompt(shot: dict) -> str:
    chars = shot.get("characters", []) or []
    wardrobe = shot.get("wardrobe", {}) or {}
    props = shot.get("key_props", []) or []
    camera = shot.get("camera", "")
    composition = _shot_caption(shot["shot_id"])

    lines: list[str] = []
    lines.append(
        "Generate a single cinematic storyboard frame for shot "
        f"{shot['shot_id']} of an animated feature film. The character "
        "reference images attached above ARE the locked character designs - "
        "match each character's identity (face, hair, skin tone, age and "
        "body proportions) EXACTLY against their turnaround. Do not age them "
        "up or down. Do not change hair color, hair length, hairstyle, or "
        "skin tone from the turnaround."
    )
    lines.append("")
    lines.append("REFERENCE IMAGES (in attached order):")
    for name in chars:
        lines.append(f"  - {name}: {CHAR_IDENTITY.get(name, '(see turnaround)')}")
    lines.append("")
    if wardrobe:
        lines.append(
            "WARDROBE for THIS shot - MANDATORY (overrides whatever each "
            "character was wearing in their turnaround - turnarounds define "
            "identity only, not outfit). Read each line literally: if a "
            "character's wardrobe says 'casual home wear', they MUST NOT be "
            "in pajamas. If it says 'pajamas', they MUST be in pajamas. If it "
            "says 'tuxedo' or 'formal dress', that exact garment. Do not blend "
            "outfits across characters."
        )
        for name, desc in wardrobe.items():
            extra = ""
            if name == "Mia" and "casual home wear" in desc.lower():
                extra = (
                    " (concretely: a magenta / hot-pink casual top with small "
                    "dotted pattern + blue denim jeans, matching what Mia is "
                    "wearing in her turnaround. NOT pajamas, NOT a nightgown.)"
                )
            elif name == "Leo" and "dinosaur" in desc.lower():
                extra = " (green dino-print pajama top + matching bottoms.)"
            lines.append(f"  - {name}: {desc}{extra}")
        lines.append("")
    if props:
        lines.append("KEY PROPS to include:")
        for p in props:
            lines.append(f"  - {p}")
        lines.append("")
    lines.append(f"CAMERA / FRAMING: {camera}")
    lines.append("")
    lines.append(f"COMPOSITION: {composition}")
    lines.append("")
    lines.append(
        "Setting is the family living room at evening - warm interior lamp "
        "light, large windows showing a dark stormy night sky. Any lightning "
        "must be visible OUTSIDE through a window only; never draw a "
        "lightning bolt overlapping interior walls, furniture, or a "
        "character's body."
    )
    lines.append("")
    lines.append(STYLE)
    return "\n".join(lines)


def generate_panel(client: genai.Client, shot: dict, out_path: Path) -> bool:
    parts: list = []
    # Attach a labeled reference image for each character, in the manifest's order
    # so the prompt's "(in attached order)" matches the actual sequence.
    for name in shot.get("characters", []) or []:
        ref_path = _resolve_char_ref(name)
        parts.append(types.Part.from_text(text=f"REFERENCE - {name} turnaround:"))
        parts.append(_img_to_part(ref_path))

    prompt = _build_prompt(shot)
    parts.append(types.Part.from_text(text=prompt))

    print(f"[{shot['shot_id']}] generating ({len(shot.get('characters', []))} refs)...", flush=True)
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=parts,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(resp, "candidates") and resp.candidates:
        for part in resp.candidates[0].content.parts:
            if getattr(part, "inline_data", None) is not None:
                data = part.inline_data.data
                with open(out_path, "wb") as f:
                    f.write(data)
                kb = len(data) / 1024
                print(f"  saved {out_path.name} ({kb:.0f} KB)", flush=True)
                return True
            elif getattr(part, "text", None):
                print(f"  text: {part.text[:200]}", flush=True)
    print("  FAILED: no image in response", flush=True)
    return False


def main(argv: list[str]) -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set", file=sys.stderr)
        return 2
    client = genai.Client(api_key=api_key)

    manifest = _load_manifest()
    wanted = set(argv) if argv else None
    shots = [s for s in manifest if (wanted is None or s["shot_id"] in wanted)]
    if not shots:
        print(f"No shots match {argv}", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    successes: list[str] = []
    failures: list[str] = []
    for i, shot in enumerate(shots):
        out = OUT_DIR / f"scene-01-{shot['shot_id']}-start.png"
        ok = generate_panel(client, shot, out)
        if ok:
            successes.append(shot["shot_id"])
        else:
            failures.append(shot["shot_id"])
        if i < len(shots) - 1:
            time.sleep(DELAY)

    print()
    print(f"OK: {successes}")
    print(f"FAIL: {failures}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
