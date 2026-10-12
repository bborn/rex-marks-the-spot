#!/usr/bin/env python3
"""Restage the Scene 2 (EXT. HOUSE - NIGHT) still so the minivan has a
reachable door.

Why this exists
---------------
The Omni take ``omni-s2-t2.mp4`` had Gabe grabbing the van's *tail light* to
open it.  That is not a prompt bug, it is a staging bug: in the plate
``s2-restage-t2.png`` the van presents its rear quarter to the characters'
approach, so the only feature on the surface they run at is a tail light.  The
model reached for the only affordance available.

This script produces two restaged plates, image-to-image off the existing
plate, changing ONLY the van's position and angle:

* ``broadside`` - van parallel to the house, sliding-door flank facing the
  front door.
* ``nosein``    - van angled nose-in, front passenger door AND sliding door
  both presented to the approach.

Everything else is held: locked house, teal family minivan, night storm, the
two characters and their wardrobe, Pixar-style 3D look.

Stills only.  This script never touches Runway/Omni.

Usage
-----
    .venv/bin/python scripts/factory/restage_s2_van_door.py            # dry run
    .venv/bin/python scripts/factory/restage_s2_van_door.py --fire
    .venv/bin/python scripts/factory/restage_s2_van_door.py --fire \
        --option broadside --attempt 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Reference snapshot handed over by the factory (see
# ~/factory-plan/claude-handoff-2026-08-31.md).
FACTORY_PLAN = Path(os.environ.get("FACTORY_PLAN", Path.home() / "factory-plan"))
PLATE = FACTORY_PLAN / "omni" / "s2" / "s2-restage-t2.png"
VAN_REF = FACTORY_PLAN / "lockups" / "family_car_exterior.png"

OUT_DIR = REPO_ROOT / "renders" / "factory" / "s2" / "restage-v3"

PREFERRED_MODEL = "gemini-3-pro-image-preview"
FALLBACK_MODEL = "gemini-2.5-flash-image"
ASPECT_RATIO = "3:2"  # matches the 1536x1024 plate

# Hard cost governor for this task.  gemini-3-pro-image-preview bills 1120
# output tokens for a 1K/2K image at $120/1M tokens.
COST_PER_IMAGE = {
    PREFERRED_MODEL: 0.134,
    FALLBACK_MODEL: 0.039,
}
HARD_CAP_USD = 1.00
REQUEST_DELAY_S = 8.0

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

# EXT. HOUSE - NIGHT, from the screenplay.  Quoted so the staging serves the
# actual beat and not a shot-list verb.
SCREENPLAY = (
    "EXT. HOUSE - NIGHT\n\n"
    "Rain starts to fall. We hear thunder and see flashes of lightning. "
    "Gabe and Nina burst out the door and rush to the car."
)

HOLD = """\
HOLD EXACTLY AS IN IMAGE 1 - do not redesign, restyle or re-light any of this:
- The house. Same grey shingle two-storey, same trim, same window pattern and
  their warm interior glow, same open front door with the warm hallway light
  and staircase inside, same wall lantern, same white garage door at frame
  right, same purple hydrangeas at the left, same porch steps. The house is
  LOCKED. Do not reopen its design, do not move the camera off it.
- The night storm: heavy rain streaks, dark blue-grey storm sky, lightning bolt
  in the upper right, wet reflective flagstone driveway throwing back the warm
  doorway light. Same colour grade, same key light.
- The two characters, and only these two people. Gabe: same face as image 1 -
  early-40s dad, wavy dark brown hair, black rectangular glasses, stubble, soft
  around the middle, black tuxedo with bow tie and white dress shirt, mid-run,
  leaning forward. Nina: same face as image 1 - auburn wavy shoulder-length
  hair, freckles, green eyes, sleeveless black midi dress, small black clutch in
  her hand, black strappy heels, mid-run. Same expressions, same urgency, same
  wet-in-the-rain look.
- The vehicle is the same teal-blue family minivan. Not a sedan, not an SUV, not
  a different car. Same teal paint, same silver multi-spoke alloy wheels, same
  proportions, rain-beaded and wet.
- Stylised Pixar-style 3D animation render. Do NOT drift toward photoreal, do
  not turn this into a photograph.

FORBIDDEN: no third person, no children, no dinosaurs on the lawn, no daylight,
no roof rack or luggage, no snack clutter, no text or watermark."""

OPTIONS: dict[str, str] = {}

OPTIONS["broadside"] = f"""\
IMAGE 1 is the locked Scene 2 plate. Re-render it with ONE change: where the
minivan sits and which way it faces. IMAGE 2 is the family van, for shape and
colour only - ignore its daylight, its roof luggage and its background.

THE PROBLEM WITH IMAGE 1: the van presents its rear quarter to the characters,
so there is no door on the surface they are running at - only a tail light.

THE ONE CHANGE - BROADSIDE STAGING:
Park the teal minivan parallel to the house, broadside to the camera, along the
driveway on the right half of frame, so that its full flank faces the house and
the camera. The side we see is the SLIDING-DOOR side. Present, clearly and
unambiguously: the front passenger door with its window and door handle, and
behind it the SLIDING REAR DOOR - its handle, its seam, and the sliding-door
track running along the body under the rear side window. The nose of the van
points toward frame left. We see the flank of the van, NOT its tail: no tail
light, no rear hatch, no licence plate, no bumper stickers anywhere in the
characters' path.

THE BEAT (same beat as image 1, mid-run):
{SCREENPLAY}

Gabe and Nina are mid-stride between the lit front door and the van, running
toward the camera-facing flank. The sliding door is directly ahead of them and
close - an arm's reach away at the end of their run, its handle plainly
readable. It must be obvious that the sliding door is the thing they are
heading for and the thing a hand would land on next.

{HOLD}"""

OPTIONS["nosein"] = f"""\
IMAGE 1 is the locked Scene 2 plate. Re-render it with ONE change: where the
minivan sits and which way it faces. IMAGE 2 is the family van, for shape and
colour only - ignore its daylight, its roof luggage and its background.

THE PROBLEM WITH IMAGE 1: the van presents its rear quarter to the characters,
so there is no door on the surface they are running at - only a tail light.

THE ONE CHANGE - NOSE-IN STAGING:
Turn the teal minivan around so it is angled nose-in toward the house, parked on
the driveway on the right half of frame in a three-quarter FRONT view. Its front
end - grille, headlights, windscreen - is toward the house and frame left, and
its passenger flank rakes away from us to frame right. Both openable doors on
that flank are presented to the approach: the FRONT PASSENGER DOOR (window,
mirror, door handle) and, behind it, the SLIDING REAR DOOR with its handle and
its sliding track under the rear side window. We see the front three-quarter of
the van, NOT its tail: no tail light, no rear hatch, no licence plate in the
characters' path.

THE BEAT (same beat as image 1, mid-run):
{SCREENPLAY}

Gabe and Nina are mid-stride between the lit front door and the van, running at
that presented flank. Gabe's run line ends at the sliding door, Nina's at the
front passenger door - both doors are close, reachable, and clearly the things
they are heading for, with their handles plainly readable.

{HOLD}"""


# Corrections fed back in on later attempts, from looking at what came out.
ATTEMPT_NOTES: dict[tuple[str, int], str] = {
    ("broadside", 2): """\

CORRECTIONS - a previous attempt got this wrong, do not repeat it:
- The van was still angled rear-quarter with a red tail light visible at frame
  right. There must be NO red tail light, NO rear hatch, NO tailgate anywhere in
  this image. If a tail light is visible, the staging has failed.
- Turn the van a full 180 degrees from that: its NOSE - grille, headlights,
  windscreen, wing mirror - is the end nearest frame right and nearest the
  camera; its flank recedes to frame left. The van is broadside, parallel to the
  driveway, its long side square to camera.
- Push the van slightly further back and right so its whole flank fits in the
  right third of frame: front passenger door AND sliding rear door both fully
  visible, both handles readable, the sliding-door track running along the body.
- The sliding door must be the closest part of the van to the running couple.""",
    ("broadside", 3): """

CORRECTIONS - two previous attempts got this wrong. Both drifted back to the
staging of image 1 and both put a red tail light at frame right. That is the
exact defect being fixed. Ignore image 1's van entirely; keep only its house,
its people, its weather and its light.

REDRAW THE VAN AS A SIDE ELEVATION. Reading the van left to right across the
right third of the frame, in this order:
  1. the rear wheel and the rear side window at the far LEFT end of the van,
  2. the SLIDING REAR DOOR - its handle, its vertical seams, and the sliding
     track running along the body under the window,
  3. the FRONT PASSENGER DOOR - its window, its handle, its wing mirror,
  4. the front wheel,
  5. the bonnet, windscreen and headlight, with the van's NOSE at the RIGHT
     edge of frame.
The van's tail is out of frame to the left, behind the couple. NO red tail
light, NO rear hatch, NO tailgate, NO licence plate anywhere in this image.
The van sits low and flat and parallel to the driveway - a clean broadside, not
an angled three-quarter.

Nina's run line ends at the sliding door handle. It is the nearest openable
thing to her, roughly at her shoulder height, and it must read instantly as the
door she is about to grab.""",
    ("nosein", 2): """\

CORRECTIONS - a previous attempt got this wrong, do not repeat it:
- The van's nose pointed out toward frame right instead of in toward the house.
  Swing it so the grille and headlights angle toward the house at frame left,
  with the passenger flank raking back to frame right.
- Keep both door handles crisp and readable, and keep the whole van inside the
  frame - do not crop the nose off the right edge.
- No red tail light, no rear hatch anywhere in frame.""",
}


@dataclass
class Result:
    option: str
    attempt: int
    model: str
    path: Path | None
    text: str
    cost: float


def _client():
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is not set")
    return genai.Client(api_key=api_key)


def _prompt_for(option: str, attempt: int) -> str:
    return OPTIONS[option] + ATTEMPT_NOTES.get((option, attempt), "")


def _parts(prompt: str, van_ref: bool = True):
    from google.genai import types

    parts = [types.Part.from_bytes(data=PLATE.read_bytes(), mime_type="image/png")]
    # VAN_REF is itself a rear three-quarter of the van, complete with tail
    # lights.  On a restage whose whole point is to get the tail out of the
    # approach, it pulls the render straight back to the defect - so later
    # attempts drop it and describe the van's silhouette in words instead.
    if van_ref:
        parts.append(
            types.Part.from_bytes(data=VAN_REF.read_bytes(), mime_type="image/png")
        )
    parts.append(prompt)
    return parts


def generate(
    client,
    option: str,
    attempt: int,
    model: str,
    spent: float,
    van_ref: bool = True,
) -> Result:
    from genai_compat import generate_image

    cost = COST_PER_IMAGE.get(model, COST_PER_IMAGE[PREFERRED_MODEL])
    if spent + cost > HARD_CAP_USD:
        raise SystemExit(
            f"cost governor: ${spent:.3f} spent, next image ${cost:.3f}, "
            f"cap ${HARD_CAP_USD:.2f} - refusing to fire"
        )

    image_bytes, text = generate_image(
        client,
        _parts(_prompt_for(option, attempt), van_ref=van_ref),
        model=model,
        aspect_ratio=ASPECT_RATIO,
    )

    path = None
    if image_bytes:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / f"s2-restage-{option}-a{attempt}.png"
        path.write_bytes(image_bytes)
    return Result(option, attempt, model, path, text.strip(), cost)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fire", action="store_true", help="actually call the API")
    ap.add_argument(
        "--option",
        action="append",
        choices=sorted(OPTIONS),
        help="restage option (default: both)",
    )
    ap.add_argument("--attempt", type=int, default=1, help="attempt number (max 3)")
    ap.add_argument("--model", default=PREFERRED_MODEL)
    ap.add_argument(
        "--no-van-ref",
        action="store_true",
        help="omit family_car_exterior.png (its rear-quarter view reinforces the tail)",
    )
    ap.add_argument(
        "--spent", type=float, default=0.0, help="USD already spent on this task"
    )
    args = ap.parse_args()

    options = args.option or sorted(OPTIONS)
    if args.attempt > 3:
        raise SystemExit("max 3 attempts per option")

    for missing in (p for p in (PLATE, VAN_REF) if not p.exists()):
        raise SystemExit(f"missing reference: {missing}")

    if not args.fire:
        for option in options:
            print(f"===== {option} a{args.attempt} =====\n{_prompt_for(option, args.attempt)}\n")
        print("dry run - pass --fire to generate")
        return 0

    client = _client()
    spent = args.spent
    results: list[Result] = []
    for i, option in enumerate(options):
        if i:
            time.sleep(REQUEST_DELAY_S)
        model = args.model
        try:
            result = generate(
                client, option, args.attempt, model, spent, van_ref=not args.no_van_ref
            )
        except Exception as exc:  # noqa: BLE001 - fall back to the cheaper model
            print(f"{option}: {model} failed ({exc}); falling back")
            time.sleep(REQUEST_DELAY_S)
            result = generate(
                client,
                option,
                args.attempt,
                FALLBACK_MODEL,
                spent,
                van_ref=not args.no_van_ref,
            )
        spent += result.cost
        results.append(result)
        print(
            json.dumps(
                {
                    "option": result.option,
                    "attempt": result.attempt,
                    "model": result.model,
                    "path": str(result.path) if result.path else None,
                    "text": result.text[:400],
                    "spent_usd": round(spent, 3),
                },
                indent=2,
            )
        )

    print(f"\ntotal spend this run: ${spent - args.spent:.3f} (cap ${HARD_CAP_USD:.2f})")
    return 0 if all(r.path for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
