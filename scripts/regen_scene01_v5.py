#!/usr/bin/env python3
"""Regenerate Scene 1 storyboard panels on-model (v5).

Why v5 exists
-------------
v4 was already image-to-image from the locked turnarounds, and it still came out
off-model. The reason is in `scripts/regen_scene01_v4.py` itself: its
`CHAR_IDENTITY` blurbs contradict the locked identity sheet
(`scripts/validate/identity-sheets.json`) that the repaired validator grades
against. It told the model Gabe wears "black-framed glasses" (sheet:
`thin_wire_rectangular`), that Mia's hair is "worn DOWN (never a ... ponytail)"
(sheet: `ponytail`), that Mia has "light skin" (sheet: `tan`), and it never
named Jenny's `medium_brown` skin tone at all. The generator was being told to
draw the exact attributes the gate then failed.

v5 fixes that by deriving every identity line straight from
`identity-sheets.json`, in the validator's own vocabulary, so the generator and
the gate are working from one description.

Staging is preserved by attaching the corresponding v4 panel as a
composition-only reference: same camera, same room layout, same prop placement,
same lighting - only the people are replaced with on-model versions.

Usage:
  python3 scripts/regen_scene01_v5.py                    # all 9
  python3 scripts/regen_scene01_v5.py 1A 1E              # subset
  python3 scripts/regen_scene01_v5.py --attempt 2 1A     # retry suffix in log
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

MODEL = os.environ.get("REX_IMAGE_MODEL", "gemini-3-pro-image-preview")
FALLBACK_MODEL = "gemini-2.5-flash-image"
DELAY = 10  # seconds between calls (>=8 per CLAUDE.md)

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "asset-bible/manifests/scene-01.json"
CHAR_DIR = ROOT / "asset-bible/characters"
STAGING_DIR = ROOT / "work/v4"
OUT_DIR = ROOT / "work/v5"
SHEET = ROOT / "scripts/validate/identity-sheets.json"


# ---------------------------------------------------------------------------
# Identity: rendered from the locked sheet, in the validator's vocabulary.
# ---------------------------------------------------------------------------

# Plain-English rendering of each vocabulary value, so the image model reads a
# sentence and the validator reads the same enum. Do not editorialise: if a
# phrase here drifts from the sheet, the generator and the gate disagree again.
PHRASING = {
    "hair_colour": {
        "blonde": "blonde / golden hair",
        "light_brown": "light brown hair",
        "dark_brown": "DARK BROWN hair (definitely not blonde, not black)",
        "black": "black hair",
        "red_auburn": "AUBURN / COPPER-RED hair (definitely not blonde, not brown)",
        "grey_white": "grey / white hair",
    },
    "hair_length": {
        "cropped": "cropped very short",
        "short": "short (above the collar)",
        "chin": "chin-length",
        "shoulder": "SHOULDER-LENGTH - it ends at the shoulders, no longer",
        "mid_back": "long, reaching the middle of the back",
        "longer": "very long, past the waist",
    },
    "hair_texture": {
        "straight": "straight",
        "wavy": "wavy",
        "curly": "CURLY - defined springy curls, not straight and not merely wavy",
        "tightly_curled": "tightly curled / coiled",
    },
    "build": {
        "child": "small child's body proportions",
        "slim": "slim, slight build",
        "average": "an average, softly rounded adult build - noticeably fuller "
                   "than slim, not skinny or willowy",
        "heavy_set": "HEAVY-SET - a big soft body, wide through the chest and "
                     "belly, a visible paunch. He is NOT slim and NOT athletic",
        "stocky": "stocky and thickset",
    },
    "eyewear": {
        "none": "NO glasses at all",
        "thin_wire_round": "thin round wire-framed glasses",
        "thin_wire_rectangular": "THIN WIRE-FRAMED RECTANGULAR glasses. The rims "
                                 "are METAL WIRE - a fine dark-silver filament "
                                 "barely thicker than a drawn line, catching a "
                                 "small metallic highlight, with a thin wire "
                                 "bridge and thin wire temple arms. You can see "
                                 "the skin of his brow and cheek clearly through "
                                 "and around them. They are emphatically NOT "
                                 "thick, NOT chunky, NOT black plastic, NOT "
                                 "hipster frames, NOT heavy-rimmed",
        "heavy_dark_round": "heavy dark round frames",
        "heavy_dark_rectangular": "heavy dark rectangular frames",
        "other": "distinctive eyewear per the turnaround",
    },
    "facial_hair": {
        "clean_shaven": "clean-shaven",
        "stubble": "visible dark STUBBLE across the jaw, chin and upper lip - "
                   "he is never clean-shaven",
        "moustache": "a moustache",
        "full_beard": "a full beard",
    },
    "apparent_age": {
        "toddler": "a toddler",
        "child": "a young child",
        "teenager": "a teenager",
        "adult": "an adult",
        "older_adult": "an older adult",
    },
    "skin_tone": {
        "pale": "pale skin",
        "light": "light / fair skin",
        "tan": "warm TAN skin - noticeably warmer and deeper than pale, with freckles",
        "medium_brown": "MEDIUM BROWN skin - she is a brown-skinned girl, several "
                        "shades darker than every other person in the frame and "
                        "obviously darker than the pale-skinned parents. Warm brown, "
                        "not tan, not olive, not sun-kissed white. Keep her clearly "
                        "brown even in dim lamplight and even in the background",
        "deep_brown": "deep brown skin",
    },
    "hair_styling": {
        "worn_loose": "worn loose and down",
        "ponytail": "gathered up into a PONYTAIL",
        "bun_or_updo": "in a bun / updo",
        "braid": "in a braid",
        "tied_back": "tied back",
        "not_visible": "styling not visible",
    },
    "face_shape": {
        "round": "a round, full face",
        "oval": "an oval face",
        "long_and_narrow": "a long, narrow face",
        "square": "a square face",
        "heart": "a heart-shaped face",
    },
}

# Free-text extras that are true of the turnaround but outside the ten graded
# attributes (eye colour, freckles). These do not affect the gate; they keep the
# character recognisable to a human.
EXTRAS = {
    "Mia": "big brown eyes, freckles across the nose, 8 years old",
    "Leo": "bright blue eyes, rosy cheeks, 5 years old",
    "Jenny": "dark brown eyes, 15 years old, faintly bored expression",
    "Nina": "green eyes, warm freckled cheeks",
    "Gabe": "brown eyes, thick dark eyebrows, tired around the eyes",
}

# Attributes this cast measurably loses first, restated at the very end of the
# prompt where the generator weights them most heavily. Every entry here is a
# real, repeated failure recorded by the validator during this regeneration -
# not a guess. See docs/research/scene01-v5-panels.md.
HIGH_RISK = {
    "Gabe": ("Gabe's glasses must be THIN DARK-SILVER METAL WIRE rectangles, "
             "not thick black plastic, and he must have visible dark STUBBLE "
             "on his jaw and chin - these two details fail more often than "
             "anything else in this scene, so draw them deliberately even when "
             "he is small in frame."),
    "Jenny": ("Jenny's skin must stay clearly MEDIUM BROWN - the darkest skin "
              "tone in the frame - even under warm lamplight and even in the "
              "background."),
    "Mia": ("Mia's hair must be gathered in a HIGH CURLY PONYTAIL and she must "
            "read as an 8-year-old CHILD, not a teenager."),
}

ORDER = [
    "apparent_age", "build", "skin_tone", "face_shape",
    "hair_colour", "hair_length", "hair_texture", "hair_styling",
    "eyewear", "facial_hair",
]


def _identity_line(name: str, row: dict) -> str:
    bits = []
    for attr in ORDER:
        if attr not in row:
            continue
        # "clean-shaven" is the default for children and women; saying it out
        # loud in an image prompt is noise. Only state facial hair when there
        # is some.
        if attr == "facial_hair" and row[attr] == "clean_shaven":
            continue
        bits.append(PHRASING[attr][row[attr]])
    extra = EXTRAS.get(name)
    if extra:
        bits.append(extra)
    return f"{name}: " + "; ".join(bits) + "."


def load_identity_lines() -> dict[str, str]:
    with open(SHEET) as f:
        sheet = json.load(f)
    return {n: _identity_line(n, row) for n, row in sheet["characters"].items()}


# ---------------------------------------------------------------------------
# Wardrobe: manifest is authoritative. These fill in garment detail the manifest
# leaves open, and never contradict it. Jenny's hoodie is a standing
# "do not invent" rule - she is hoodie + phone.
# ---------------------------------------------------------------------------

WARDROBE_DETAIL = {
    "Mia": "concretely: a MAGENTA / hot-pink short-sleeved tee with small white "
           "star print + blue denim jeans (cuffed) + red sneakers. Not pajamas.",
    "Leo": "concretely: a GREEN dinosaur-print pajama top and matching pajama "
           "bottoms. Not shorts, not a plain tee.",
    "Jenny": "concretely: a CORAL / salmon zip-up HOODIE over a light tee, with "
             "dark charcoal-grey leggings and white sneakers, phone in hand. "
             "The coral hoodie is a locked, do-not-invent detail: never a grey "
             "top, never a bare tee, never a blue hoodie.",
    "Nina": "concretely: a long elegant BLACK formal evening dress.",
    "Gabe": "concretely: a BLACK TUXEDO with white dress shirt and black bow tie, "
            "worn slightly rumpled. He keeps his thin wire glasses on.",
}

# What the rejected v4 staging frames get WRONG about each character. Naming the
# error explicitly turns "match the turnaround" (which the model reads as
# "the picture in front of me is already fine") into a concrete edit
# instruction. Sourced from reports/audit-v4/scene-01-audit-v2.md.
STAGING_ERRORS = {
    "Gabe": "In the staging frame the man in the tuxedo is drawn SLIM and "
            "narrow-faced, CLEAN-SHAVEN, in THICK BLACK RECTANGULAR glasses. "
            "All three are wrong and must be redrawn: make him HEAVY-SET with "
            "a big belly and a round full face, give him dark STUBBLE across "
            "the jaw, and REPLACE the heavy black frames with hairline-thin "
            "metal WIRE rectangular frames - the single most-failed detail on "
            "this character, so draw the rims as thin as you can and still "
            "have them read as glasses.",
    "Nina": "In the staging frame the woman in the black dress is drawn SLENDER "
            "with LONG glamorous waves down her back. Both are wrong and must "
            "be redrawn: make her build fuller and softer, and cut her hair to "
            "an AUBURN SHOULDER-LENGTH wavy bob that ends at the shoulder.",
    "Mia": "In the staging frame the older girl wears her hair LOOSE and DOWN "
           "and her skin reads PALE. Both are wrong and must be redrawn: gather "
           "her curls into a HIGH CURLY PONYTAIL and warm her skin to TAN.",
    "Jenny": "In the staging frame the teenage babysitter is drawn PALE-SKINNED "
             "with SLEEK STRAIGHT hair in a grey/blue top. All wrong and must "
             "be redrawn: unmistakably MEDIUM BROWN skin - the darkest-skinned "
             "person in the frame by a clear margin, and still visibly brown "
             "under warm lamplight - DARK BROWN CURLY hair (springy defined "
             "curls) in a ponytail, and a CORAL zip hoodie.",
    "Leo": "Leo is close to correct in the staging frame; keep him blonde, "
           "tousled, blue-eyed, in green dino pajamas.",
}

STYLE = (
    "Render as a single 16:9 widescreen storyboard frame in a premium 3D-animated "
    "feature-film look (Pixar / DreamWorks style) - the SAME stylized 3D-character "
    "art style as the attached turnarounds (slightly cartoonish proportions, "
    "expressive features, NOT photorealistic humans). Cinematic lighting, soft "
    "volumetric atmosphere. 16:9 fills the entire image - do NOT add letterbox "
    "bars. Produce ONE in-world cinematic frame: no turnaround sheets, no split "
    "panels, no captions, no UI, no text of any kind."
)


def _shot_caption(shot_id: str) -> str:
    """Per-shot composition note. Identity claims here are kept consistent with
    identity-sheets.json - v4's captions contradicted it (e.g. Mia's hair)."""
    captions = {
        "1A": (
            "Wide establishing shot of the family living room in the evening. "
            "TV on the far LEFT of frame showing a colourful cartoon; couch "
            "center-left with the two kids on it - Mia screen-left with her legs "
            "tucked under her, Leo to her right holding his plush green T-Rex; "
            "large windows behind the couch showing a dark stormy sky with a "
            "lightning flash OUTSIDE the glass; kitchen visible background-right; "
            "Nina and Gabe in the mid-background on the right in date-night "
            "formalwear, getting ready to leave; armchair at the FAR RIGHT of "
            "frame with Jenny curled into it, absorbed in her phone. Dinosaur "
            "toys (plush T-Rex, plastic Triceratops, pterodactyl, small "
            "stegosaurus) scattered on the rug and couch. Warm amber lamplight "
            "inside against the cold storm outside. STATIC camera. EXACTLY five "
            "people in frame - two children, one teenager, two adults."
        ),
        "1B": (
            "Medium shot on Leo, slight push-in. Leo center frame, sitting "
            "cross-legged on the couch, hugging his plush green T-Rex. Plastic "
            "dinosaur toys scattered around him on the couch and floor. Soft warm "
            "TV glow on his face from camera-left. Mia only partially visible at "
            "the extreme screen-left frame edge - a slice of shoulder and her "
            "curly ponytail, not her full face. Cozy living-room background."
        ),
        "1C": (
            "Medium tracking shot following Nina, camera tracking left-to-right. "
            "Nina center frame, mid-stride moving from the living room toward the "
            "front door, fastening an earring as she walks. Gabe in the "
            "background, also in his tuxedo. Jenny in the background on the "
            "armchair, absorbed in her phone. Earrings catching the lamplight. "
            "Frantic but graceful motion. Warm interior, stormy sky through the "
            "windows. EXACTLY three people in frame."
        ),
        "1D": (
            "Two-shot of Gabe and Nina, medium shot from the waist up, STATIC. "
            "They share the foreground in date-night formalwear; Gabe is checking "
            "his wristwatch, impatient; Nina is beside him. In the soft-focus "
            "background: the two kids on the couch (Mia and Leo) and Jenny in the "
            "armchair on her phone, oblivious. Warm living-room light, stormy sky "
            "through the windows. EXACTLY five people in frame."
        ),
        "1E": (
            "Close-up insert on Jenny alone. Jenny center frame, head tilted DOWN "
            "toward her glowing phone, the screen lighting her face cool-blue from "
            "below while warm lamplight rims her from behind. Shallow depth of "
            "field, living-room background thrown out of focus. She is completely "
            "absorbed in texting. Her coral hoodie is clearly visible. Only one "
            "person in frame."
        ),
        "1F": (
            "Close-up insert of the TV screen filling most of the frame. A "
            "colourful cartoon image breaking up under static interference, with "
            "horizontal scan lines rolling through it. A brief blue time-warp "
            "flash inside the picture. A lightning flash faintly reflected in the "
            "screen glass. STATIC camera. NO people at all in this frame - it is "
            "a pure prop insert."
        ),
        "1G": (
            "Over-the-shoulder shot from BEHIND the two kids on the couch, looking "
            "past them at the TV. The glowing TV is the focal point. The kids are "
            "seen from behind, near-silhouetted against the TV glow: Mia "
            "screen-left (back of her head - a high CURLY DARK BROWN PONYTAIL) and "
            "Leo screen-right (back of his head - short tousled BLONDE hair, green "
            "dino-print pajama top). Past the couch, in the background, EXACTLY "
            "two adults: NINA with auburn shoulder-length wavy hair and light "
            "skin in the long black dress, and GABE - heavy-set, light-skinned, "
            "dark wavy hair, thin wire glasses, stubble - in the black tuxedo. "
            "EXACTLY four people total: two kids in front, two parents behind. Add "
            "nobody else."
        ),
        "1H": (
            "Close-up on Mia, slow push-in. Mia center frame, looking UP at her "
            "parents off-screen above the frame. Big brown expressive eyes, "
            "vulnerable and earnest. The TV flicker reflects faintly in her eyes. "
            "A lightning flash OUTSIDE a window briefly rims her face from "
            "camera-right - never draw a lightning bolt inside the room. Warm but "
            "tense. She must be unmistakably Mia: dark brown CURLY hair gathered "
            "in a HIGH PONYTAIL, warm tan freckled skin, magenta star tee. Only "
            "one person in frame."
        ),
        "1I": (
            "Front entryway / foyer of the same family home, beside the front "
            "door. Framing starts close on Gabe's face and pulls back into a "
            "two-shot as Nina enters from screen-left. Gabe in his black tuxedo, "
            "conflicted, caught mid-hesitation; Nina in the elegant black dress "
            "giving him a sharp don't-you-dare glare. Coat rack with hanging coats, "
            "console table with a vase or lamp, stormy window beyond. Warm lamp "
            "light. EXACTLY two people in frame."
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


def _build_prompt(shot: dict, identity_lines: dict[str, str], notes: str = "") -> str:
    chars = shot.get("characters", []) or []
    wardrobe = shot.get("wardrobe", {}) or {}
    props = shot.get("key_props", []) or []
    camera = shot.get("camera", "")
    composition = _shot_caption(shot["shot_id"])

    L: list[str] = []
    L.append(
        f"Generate a single cinematic storyboard frame for shot {shot['shot_id']} "
        "of an animated feature film."
    )
    L.append("")
    L.append(
        "TWO KINDS OF REFERENCE ARE ATTACHED, AND THEY ARE USED DIFFERENTLY."
    )
    L.append("")
    L.append(
        "  1. The STAGING REFERENCE (attached first) is an EARLIER, REJECTED "
        "version of this very shot. Its STAGING is approved and must be kept "
        "exactly: same camera angle and lens, same room layout, same furniture "
        "and prop placement, same person standing in the same spot in the same "
        "pose, same lighting and colour. It was rejected because THE PEOPLE IN "
        "IT ARE DRAWN AS THE WRONG PEOPLE - a different cast wearing the right "
        "clothes. Every human figure in it must be REDRAWN FROM SCRATCH as the "
        "correct character. Keep the blocking, replace the people."
    )
    L.append("")
    L.append(
        "  2. The CHARACTER TURNAROUNDS (attached after it) ARE the locked "
        "character designs and they WIN over the staging reference on every "
        "question of who a person is - face, hair, skin tone, build, age, "
        "glasses, facial hair. Where a turnaround and the staging frame "
        "disagree about a person's appearance, the TURNAROUND IS RIGHT and the "
        "staging frame is the error you are fixing."
    )
    L.append("")
    fixes = [STAGING_ERRORS[n] for n in chars if n in STAGING_ERRORS]
    if fixes:
        L.append(
            "SPECIFIC ERRORS IN THE STAGING REFERENCE THAT THIS REGENERATION "
            "EXISTS TO FIX - work through them one by one:"
        )
        for f in fixes:
            L.append(f"  - {f}")
        L.append("")
    if chars:
        L.append(
            "CHARACTER IDENTITY - MANDATORY, non-negotiable. Every clause below "
            "is a locked design fact checked by an automated gate. A single "
            "wrong item (wrong glasses, missing stubble, wrong skin tone, hair "
            "down instead of up) fails the panel:"
        )
        for name in chars:
            line = identity_lines.get(name)
            if line:
                L.append(f"  - {line}")
        L.append("")
    if wardrobe:
        L.append(
            "WARDROBE for THIS shot - MANDATORY. This OVERRIDES whatever the "
            "character wears in their turnaround; a turnaround is an identity "
            "card, not a dress code. It does NOT override anything in the "
            "identity block above. Read each line literally and do not blend "
            "outfits between characters:"
        )
        for name, desc in wardrobe.items():
            extra = WARDROBE_DETAIL.get(name, "")
            L.append(f"  - {name}: {desc}" + (f" ({extra})" if extra else ""))
        L.append("")
    if props:
        L.append("KEY PROPS - all of these must be visible:")
        for p in props:
            L.append(f"  - {p}")
        L.append("")
    L.append(f"CAMERA / FRAMING: {camera}")
    L.append("")
    L.append(f"COMPOSITION (must match the staging reference): {composition}")
    L.append("")
    L.append(
        "STAGING FIDELITY TEST: if your frame were laid side by side with the "
        "staging reference, the ONLY visible differences should be the people. "
        "Camera position, focal length, distance to subject, wall and window "
        "positions, furniture, background rooms, prop placement, lamp positions "
        "and the colour of the light must all read as the same frame. Do not "
        "push in, do not widen, do not swap the background."
    )
    L.append("")
    L.append(
        "SETTING: the family living room in the evening - warm interior lamp "
        "light, large windows onto a dark stormy night. Any lightning is visible "
        "OUTSIDE through a window only; never draw a bolt over interior walls, "
        "furniture or a person."
    )
    L.append("")
    L.append(STYLE)
    risks = [HIGH_RISK[n] for n in chars if n in HIGH_RISK]
    if risks:
        L.append("")
        L.append("FINAL CHECK before you render - the details this scene loses most often:")
        for r in risks:
            L.append(f"  - {r}")
    if notes:
        L.append("")
        L.append(f"CORRECTIONS FROM THE PREVIOUS ATTEMPT - fix these: {notes}")
    return "\n".join(L)


# The staging frame is attached at deliberately low resolution. At full size
# its faces dominate the generation and the character corrections stop landing
# (measured: identical off-model scores across three attempts). Downscaled, the
# layout, blocking, furniture and lighting all survive - a storyboard's staging
# is low-frequency information - while the off-model faces do not survive well
# enough to be copied.
STAGING_MAX_EDGE = 640


def generate_panel(client, shot: dict, out_path: Path, identity_lines,
                   model: str, notes: str = "",
                   staging_max_edge: int = STAGING_MAX_EDGE) -> bool:
    parts: list = []
    staging = STAGING_DIR / f"scene-01-{shot['shot_id']}-start.png"
    if staging.exists():
        parts.append(types.Part.from_text(
            text=("STAGING REFERENCE (rejected earlier version of this shot), "
                  "attached at deliberately LOW RESOLUTION. Use it for "
                  "composition, camera, blocking, prop placement and lighting "
                  "ONLY. Its PEOPLE are drawn as the WRONG PEOPLE and its "
                  "softness is an artifact of the downscale - render your own "
                  "frame at full crisp detail, and redraw every human figure "
                  "from the turnarounds below:")))
        parts.append(_img_to_part(staging, max_edge=staging_max_edge))
    else:
        print(f"  WARNING: no staging reference at {staging}", flush=True)

    # Turnarounds come last so they are the most recent thing in context: the
    # locked identity, not the rejected frame, is what the model should be
    # holding when it starts drawing faces.
    for name in shot.get("characters", []) or []:
        ref_path = _resolve_char_ref(name)
        parts.append(types.Part.from_text(
            text=(f"CHARACTER TURNAROUND - this is the REAL {name}. This is the "
                  f"locked design. It overrides the staging frame on every "
                  f"question of what {name} looks like:")))
        parts.append(_img_to_part(ref_path))

    parts.append(types.Part.from_text(text=_build_prompt(shot, identity_lines, notes)))

    print(f"[{shot['shot_id']}] generating with {model} "
          f"({len(shot.get('characters', []) or [])} char refs)...", flush=True)
    try:
        resp = client.models.generate_content(
            model=model,
            contents=parts,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )
    except Exception as e:
        print(f"  ERROR: {e}", flush=True)
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cand0 = (getattr(resp, "candidates", None) or [None])[0]
    if cand0 is not None:
        fr = getattr(cand0, "finish_reason", None)
        content = getattr(cand0, "content", None)
        parts_out = getattr(content, "parts", None) if content is not None else None
        if not parts_out:
            # An empty candidate means the model returned no image - usually a
            # safety/recitation stop. Say which, instead of raising TypeError.
            print(f"  FAILED: empty response (finish_reason={fr})", flush=True)
            return False
        for part in parts_out:
            if getattr(part, "inline_data", None) is not None:
                data = part.inline_data.data
                out_path.write_bytes(data)
                print(f"  saved {out_path.name} ({len(data)/1024:.0f} KB)", flush=True)
                return True
            elif getattr(part, "text", None):
                print(f"  text: {part.text[:200]}", flush=True)
    print("  FAILED: no image in response", flush=True)
    return False


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*", help="shot ids, default all")
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--suffix", default="", help="filename suffix, e.g. -a2")
    ap.add_argument("--notes", default="", help="corrections to feed the retry")
    args = ap.parse_args(argv)

    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set", file=sys.stderr)
        return 2
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    identity_lines = load_identity_lines()

    manifest = _load_manifest()
    wanted = set(args.shots) if args.shots else None
    shots = [s for s in manifest if (wanted is None or s["shot_id"] in wanted)]
    if not shots:
        print(f"No shots match {args.shots}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ok, bad = [], []
    for i, shot in enumerate(shots):
        out = out_dir / f"scene-01-{shot['shot_id']}-start{args.suffix}.png"
        if generate_panel(client, shot, out, identity_lines, args.model, args.notes):
            ok.append(shot["shot_id"])
        else:
            bad.append(shot["shot_id"])
        if i < len(shots) - 1:
            time.sleep(DELAY)
    print(f"\nDone. ok={ok} failed={bad}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
