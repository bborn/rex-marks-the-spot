#!/usr/bin/env python3
"""Scene 2 (EXT. HOUSE - NIGHT) restage v4: each adult at their OWN front door.

Why this exists
---------------
Two takes died on the same root cause - the still never said which door each
person uses, so the video model guessed, and guessed wrong.

* ``t2`` - the van's rear faced the run.  No door on that surface at all, so
  Gabe grabbed the tail light.
* ``t3`` (off ``s2-restage-broadside.png``) - the van is broadside, but the
  sliding-door handle and the front-passenger-door handle sit inches apart at
  the B-pillar, and Nina's hand in the plate lands between them.  She pulled one
  handle and the other door opened; then Gabe climbed in behind her through the
  same sliding door.

v4 fixes the ambiguity in the staging rather than in the prompt wording.  The
door assignment is fixed and identical across all three variations:

    Nina  -> FRONT PASSENGER door.  She rides shotgun.
    Gabe  -> DRIVER's door, reached by rounding the NOSE of the van.

The sliding door is the kids' door.  It plays no part in this shot: in every
variation it is either far behind Nina down the flank, or out of frame entirely.
There is never a second handle within reach of her hand.

The three variations differ ONLY in van angle and camera position.  Everything
else - house, storm, wardrobe, faces, the teal minivan, the Pixar look - is held
from the plate ``s2-restage-t2.png`` (the Omni house, which is the locked one).

Stills only.  This script never touches Runway/Omni.

Usage
-----
    .venv/bin/python scripts/factory/restage_s2_own_doors.py              # dry run
    .venv/bin/python scripts/factory/restage_s2_own_doors.py --fire
    .venv/bin/python scripts/factory/restage_s2_own_doors.py --fire \
        --variation noseleft --attempt 2 --spent 0.402
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

# The Omni house is the locked one.  Deliberately NOT front-house-set-lockup.jpg
# (photoreal - it is what caused the original restyle) and NOT
# bornsztein_home_exterior.png (dinosaurs on the lawn).
PLATE = FACTORY_PLAN / "omni" / "s2" / "s2-restage-t2.png"
GABE_REF = FACTORY_PLAN / "lockups" / "gabe_turnaround_APPROVED.png"
NINA_REF = FACTORY_PLAN / "lockups" / "nina_dress_turnaround.png"

OUT_DIR = REPO_ROOT / "renders" / "factory" / "s2" / "restage-v4"

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
MAX_ATTEMPTS = 3

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

SCREENPLAY = (
    "EXT. HOUSE - NIGHT\n\n"
    "Rain starts to fall. We hear thunder and see flashes of lightning. "
    "Gabe and Nina burst out the door and rush to the car."
)

# The one thing this whole task exists to nail down.  Identical in all three
# variations - only the camera moves.
DOOR_ASSIGNMENT = """\
THE DOOR ASSIGNMENT - THIS IS THE POINT OF THE IMAGE. A viewer must be able to
say who is getting in where, at a glance, without being told:

- NINA is going to the FRONT PASSENGER DOOR. She rides shotgun. She is standing
  at that door, her near hand closed on THAT door's handle - the handle just
  behind the wing mirror, forward of the B-pillar, on the front door with the
  big front side window. Her hand is on the FRONT door handle and nothing else
  is within reach of it.
- GABE is going to the DRIVER'S DOOR, on the far side of the van. He is NOT
  following Nina and he is NOT going to her door. He is rounding the NOSE of the
  van - crossing in front of the grille and headlights - on his way around to
  his own door. He is past her, ahead of her, turned away from her, his body and
  his gaze aimed around the front of the van and off toward the driver's side.
  There is clear open ground between him and Nina.
- They are heading to two DIFFERENT doors. Their paths diverge: hers stops at
  the near front door, his continues around the nose and out of the frame's
  reach.

THE SLIDING DOOR IS OUT OF THIS SHOT. It is the kids' door and it plays no part
in this beat. Do NOT put a sliding-door handle, a sliding-door track, or a
second door handle anywhere near Nina's hand. If any part of the sliding door is
visible at all it must be far down the flank behind her, small, deep in
perspective, and unmistakably a separate door - never within an arm's length of
her hand, never at the same pillar, never a pair of handles side by side.

ONLY ONE DOOR HANDLE is legible in the area around Nina's hand: the front
passenger door handle she is holding."""

HOLD = """\
HOLD EXACTLY AS IN IMAGE 1 - do not redesign, restyle or re-light any of this:
- The house. Same grey clapboard/shingle two-storey, same trim, same window
  pattern and their warm interior glow, same open front door with the warm
  hallway light and the staircase visible inside, same wall lantern, same white
  garage door, same purple hydrangeas, same porch steps. The house is LOCKED.
- The night storm: heavy rain streaks, dark blue-grey storm sky, lightning in
  the upper sky, wet reflective flagstone driveway throwing back the warm
  doorway light. Same colour grade, same key light.
- The vehicle is the same teal-blue family minivan. Not a sedan, not an SUV, not
  a different car. Same teal paint, same silver multi-spoke alloy wheels, same
  proportions, rain-beaded and wet.
- Stylised Pixar-style 3D animation render, same as image 1. Do NOT drift toward
  photoreal, do not turn this into a photograph, do not change the render style.

THE TWO PEOPLE - and only these two people:
- GABE (face from image 2): early-40s dad, wavy dark brown hair, BLACK
  RECTANGULAR GLASSES, stubble, soft around the middle. Black tuxedo, black bow
  tie, white dress shirt. Mid-stride, leaning forward, wet in the rain.
- NINA (wardrobe and face from image 3): auburn wavy shoulder-length hair,
  freckles, green eyes. Sleeveless black midi dress, small black clutch, black
  strappy heels. Wet in the rain.

FORBIDDEN: no third person, no children, no babysitter, no dinosaurs, no
daylight, no roof rack or luggage, no text or watermark, no second car."""

VARIATIONS: dict[str, str] = {}

VARIATIONS["noseleft"] = f"""\
IMAGE 1 is the locked Scene 2 plate - take its house, its weather, its light and
its render style. IMAGE 2 is Gabe's approved turnaround (face and glasses only).
IMAGE 3 is Nina's dress turnaround (face, hair and wardrobe only). Ignore the
turnarounds' plain backgrounds and their lighting.

RESTAGE THE VAN AND THE TWO PEOPLE. Change nothing else.

VARIATION A - NOSE ANGLED CAMERA-LEFT, PASSENGER SIDE TO THE HOUSE:
Park the teal minivan on the driveway in the right half of frame in a FRONT
THREE-QUARTER view, rotated about 40 degrees: its NOSE - grille, headlights,
windscreen, wing mirror - is nearest the camera and angled toward frame LEFT
(toward the house), and its passenger flank rakes away from us back toward frame
right and into the depth of the shot. Because the van is angled, the FRONT
PASSENGER DOOR is the big, near, clearly readable door in the middle of frame
right; anything behind the B-pillar falls away small and dark into perspective.
No red tail light, no rear hatch, no tailgate, no licence plate in frame.

THE BEAT (same beat as image 1):
{SCREENPLAY}

Camera at standing eye level, medium-wide, the lit front doorway of the house
still visible at frame left across the driveway.

{DOOR_ASSIGNMENT}

Nina is at the front passenger door, side-on to camera, one hand on that door's
handle just behind the wing mirror, her clutch in the other hand, glancing back
toward the house. Gabe is at the van's NOSE, closer to frame right, crossing in
front of the grille in mid-stride, his body already turned away toward the far
side of the van - the driver's side - with a clear gap of wet driveway between
him and Nina.

{HOLD}"""

VARIATIONS["overthenose"] = f"""\
IMAGE 1 is the locked Scene 2 plate - take its house, its weather, its light and
its render style. IMAGE 2 is Gabe's approved turnaround (face and glasses only).
IMAGE 3 is Nina's dress turnaround (face, hair and wardrobe only). Ignore the
turnarounds' plain backgrounds and their lighting.

RESTAGE THE VAN AND THE TWO PEOPLE. Change nothing else.

VARIATION B - LOW CAMERA ACROSS THE VAN'S NOSE:
Drop the camera to about waist height and move it around so we are looking
ACROSS the front of the teal minivan. The van's nose - grille, headlights, wet
bonnet - is the near foreground at frame right, cut off by the right edge of
frame. The van runs away from us to frame left in a steep front three-quarter,
so that on the near flank we see the front wheel, the wing mirror and the FRONT
PASSENGER DOOR, and then the van is cropped: the B-pillar, the sliding door and
the whole rear of the van are OUT OF FRAME. There is exactly one door and one
door handle visible on the van in this entire image. No red tail light, no rear
hatch, no sliding door, no second handle.

THE BEAT (same beat as image 1):
{SCREENPLAY}

Low, slightly heroic angle, rain falling through the frame, the lit front
doorway of the house glowing behind and above at frame left.

{DOOR_ASSIGNMENT}

Nina is at that one front passenger door, mid-frame, hand on its handle, clutch
tucked under her other arm, one heel lifting as she steps up to get in. Gabe is
in the near foreground at frame right, rounding the van's nose - we catch him
from behind and side, mid-stride past the headlight, hand skimming the wet
bonnet as he swings around it toward the driver's side. He is moving AWAY from
Nina, around the front of the van, not toward her door.

{HOLD}"""

VARIATIONS["highwide"] = f"""\
IMAGE 1 is the locked Scene 2 plate - take its house, its weather, its light and
its render style. IMAGE 2 is Gabe's approved turnaround (face and glasses only).
IMAGE 3 is Nina's dress turnaround (face, hair and wardrobe only). Ignore the
turnarounds' plain backgrounds and their lighting.

RESTAGE THE VAN AND THE TWO PEOPLE. Change nothing else.

VARIATION C - RAISED WIDE, VAN NOSE-OUT TOWARD CAMERA-LEFT:
Raise the camera a little above head height and pull back to a wide shot that
takes in the lit front door of the house at frame left, the wet driveway across
the middle, and the teal minivan at frame right. Park the van nose-out and
angled about 30 degrees, its grille and headlights toward frame left and the
camera, its passenger flank toward the house so the FRONT PASSENGER DOOR faces
the camera squarely and is fully lit by the doorway glow. From this height and
angle the rear half of the van foreshortens hard away to frame right - the
sliding door is a distant, dark, plainly separate panel far down the flank, and
its handle is not readable. No red tail light, no rear hatch in frame.

THE BEAT (same beat as image 1):
{SCREENPLAY}

Slight high angle, wide, so the geometry of the whole run reads: door of the
house, wet driveway, van, and two people on two diverging paths.

{DOOR_ASSIGNMENT}

The wide framing must make the split legible from across the room: Nina stopped
at the front passenger door with her hand on that handle, and Gabe several
strides further on, out at the van's nose, curving around the grille toward the
driver's side. Draw a clear diagonal of empty wet driveway between them so the
two paths visibly fork.

{HOLD}"""


# Corrections fed back in on later attempts, from looking at what came out.
ATTEMPT_NOTES: dict[tuple[str, int], str] = {
    ("noseleft", 2): """

CORRECTIONS - attempt 1 got Nina right and Gabe wrong. Keep Nina exactly as she
was; move Gabe.
- KEEP: the van's nose, grille and headlights at frame RIGHT with the flank
  raking away to frame left (attempt 1 put it there and it reads well - do not
  flip it back). Keep Nina standing at the front passenger door just behind the
  wing mirror with her hand closed on that one handle and her clutch in the
  other hand. Keep the single visible door handle.
- FIX GABE: in attempt 1 he was running toward frame LEFT, back at the house.
  That reads as him running AWAY from the van. He must be going the other way.
  Put Gabe at the FRONT of the van, at frame right, crossing in front of the
  grille and headlights - closer to camera than the van's nose, lit from below
  by the headlight wash, mid-stride moving RIGHT and away, his back and shoulder
  toward us, head turned around the corner of the van toward the driver's side.
  He is beyond Nina, on the far side of her, with the whole nose of the van
  between them.
- The read must be: Nina stops here at the front door; Gabe keeps going around
  the front of the van to his own door.""",
    ("overthenose", 2): """

CORRECTIONS - attempt 1 failed badly on four counts. Fix all four:
1. THE HOUSE WAS RESTYLED. Go back to the house in image 1 exactly: grey
   shingle two-storey with the gabled dormer, the white garage door, the deep
   open front doorway with the warm hallway light and the STAIRCASE visible
   inside, the single wall lantern, the purple hydrangeas, the flagstone steps.
   Do not invent a new porch, do not change the front door, do not add a second
   lantern, do not move to a ranch house.
2. NINA WAS WRONG. She must have long AUBURN WAVY shoulder-length hair - not a
   dark brown bob, not short hair. Sleeveless black midi dress with a round
   neck - not a short-sleeved V-neck. Small black clutch, black strappy heels.
   Freckles, green eyes.
3. NINA WAS NOT AT A DOOR. She was left standing on the path. She must be AT
   THE VAN, at the front passenger door, her hand closed on that door's handle.
   She is the one at the door.
4. GABE WAS AT NINA'S DOOR with his hand on the bonnet. Move him off it. He is
   further right, PAST the front passenger door, out at the nose, rounding the
   grille toward the driver's side, moving away from her.""",
    ("highwide", 2): """

CORRECTIONS - attempt 1 reproduced the exact defect this task exists to fix.
- TWO DOOR HANDLES ended up within reach of Nina's hands: the front passenger
  door handle under one hand and the SLIDING DOOR handle under the other. That
  is the failure. There must be exactly ONE door handle visible on the whole
  van, the front passenger one, and Nina's free hand holds her CLUTCH - it is
  nowhere near the bodywork.
- Crop or rotate so the sliding door is not in frame: swing the van further
  round to a steeper front three-quarter and push the rear half out past the
  right edge of frame. Everything behind the B-pillar is gone. No rear side
  window, no sliding door, no sliding-door track, no second handle.
- FIX GABE: in attempt 1 he was drifting toward frame left with nothing to walk
  to, which reads as leaving. Put him hard at the van's NOSE, in front of the
  grille and headlights at frame left, mid-stride and clearly curving AROUND the
  front corner of the van toward the driver's side on the far flank - one hand
  out to the wet bonnet as he swings round it, head turned that way.
- Keep the raised camera and the wide framing: the lit front doorway at frame
  left, the wet driveway across the middle, and a clear diagonal of empty
  driveway between Gabe at the nose and Nina at her door, so the two paths
  visibly fork.""",
    ("highwide", 3): """

CORRECTIONS - two attempts have failed. Attempt 1 put a second door handle under
Nina's free hand. Attempt 2 swung the van the wrong way: a RED TAIL LIGHT and
the rear quarter ended up at frame right, and Gabe ran off toward frame left
with nothing to walk to. Throw both away and build the frame in this order:

1. THE VAN. Raised camera, wide shot. Put the teal minivan across the right half
   of frame in a FRONT three-quarter, its NOSE - grille, headlights, wet bonnet,
   wing mirror - at frame RIGHT and nearest the camera, its passenger flank
   raking back toward frame left and into depth. There is NO red tail light, NO
   rear hatch, NO tailgate anywhere in this image. If a red light appears, the
   staging has failed.
2. ONE DOOR. Exactly ONE door handle is visible on the van in the whole image:
   the FRONT PASSENGER door handle, just behind the wing mirror. Push the rear
   of the van far back into perspective and out of the left edge of frame so
   there is no sliding door, no sliding-door track, no rear side window, and no
   second handle to be seen.
3. NINA. Standing at that one door, side-on, her near hand CLOSED AROUND that
   handle - fingers wrapped on it, not resting flat on the window or the sill.
   Her other hand holds her black clutch against her body, well away from the
   bodywork.
4. GABE. Out at frame right, at the van's NOSE, in front of the grille and
   headlights, mid-stride and clearly curving AROUND the front corner toward the
   driver's side on the far flank - one hand skimming the wet bonnet, head and
   shoulders turned that way, moving RIGHT and away from Nina. Not toward the
   house, not toward her door.
5. Between them, a clear diagonal of empty wet driveway, so the two paths fork.
   Keep the lit front doorway of the locked house at frame left.""",
}

# Corrections that apply to any variation whose first attempt reverts to the
# ambiguous two-handles-at-the-pillar staging.  Appended by --note.
GENERIC_NOTES: dict[str, str] = {
    "twohandles": """

CORRECTIONS - a previous attempt got this wrong, do not repeat it:
- Two door handles ended up side by side near Nina's hand. That is the exact
  defect being fixed. Crop or rotate the van so the sliding door is not in the
  frame at all. Only ONE door handle may be visible on the van.
- Move Nina forward along the van, in front of the B-pillar, level with the wing
  mirror, so her hand is unmistakably on the FRONT door.""",
    "gabefollowing": """

CORRECTIONS - a previous attempt got this wrong, do not repeat it:
- Gabe was crowding Nina at the same door. Move him right out to the van's NOSE,
  in front of the grille, at least a full van's-width of open ground away from
  her, body turned away from her toward the far side of the van.
- His shoulders, hips and gaze all point around the front of the van, not at her
  door. He is leaving frame around the nose, not arriving at her handle.""",
    "tail": """

CORRECTIONS - a previous attempt got this wrong, do not repeat it:
- A red tail light / rear hatch appeared. Rotate the van so its NOSE, not its
  tail, is the end presented to camera. No red tail light anywhere in frame.""",
}


@dataclass
class Result:
    variation: str
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


def _prompt_for(variation: str, attempt: int, notes: list[str]) -> str:
    prompt = VARIATIONS[variation] + ATTEMPT_NOTES.get((variation, attempt), "")
    for note in notes:
        prompt += GENERIC_NOTES[note]
    return prompt


def _parts(prompt: str):
    from google.genai import types

    return [
        types.Part.from_bytes(data=PLATE.read_bytes(), mime_type="image/png"),
        types.Part.from_bytes(data=GABE_REF.read_bytes(), mime_type="image/png"),
        types.Part.from_bytes(data=NINA_REF.read_bytes(), mime_type="image/png"),
        prompt,
    ]


def generate(
    client,
    variation: str,
    attempt: int,
    model: str,
    spent: float,
    notes: list[str],
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
        _parts(_prompt_for(variation, attempt, notes)),
        model=model,
        aspect_ratio=ASPECT_RATIO,
    )

    path = None
    if image_bytes:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / f"s2-restage-{variation}-a{attempt}.png"
        path.write_bytes(image_bytes)
    return Result(variation, attempt, model, path, text.strip(), cost)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fire", action="store_true", help="actually call the API")
    ap.add_argument(
        "--variation",
        action="append",
        choices=sorted(VARIATIONS),
        help="restage variation (default: all three)",
    )
    ap.add_argument(
        "--attempt", type=int, default=1, help=f"attempt number (max {MAX_ATTEMPTS})"
    )
    ap.add_argument(
        "--note",
        action="append",
        choices=sorted(GENERIC_NOTES),
        default=[],
        help="append a correction note to the prompt (repeatable)",
    )
    ap.add_argument("--model", default=PREFERRED_MODEL)
    ap.add_argument(
        "--spent", type=float, default=0.0, help="USD already spent on this task"
    )
    args = ap.parse_args()

    variations = args.variation or sorted(VARIATIONS)
    if args.attempt > MAX_ATTEMPTS:
        raise SystemExit(f"max {MAX_ATTEMPTS} attempts per variation")

    for missing in (p for p in (PLATE, GABE_REF, NINA_REF) if not p.exists()):
        raise SystemExit(f"missing reference: {missing}")

    if not args.fire:
        for variation in variations:
            print(
                f"===== {variation} a{args.attempt} =====\n"
                f"{_prompt_for(variation, args.attempt, args.note)}\n"
            )
        print("dry run - pass --fire to generate")
        return 0

    client = _client()
    spent = args.spent
    results: list[Result] = []
    for i, variation in enumerate(variations):
        if i:
            time.sleep(REQUEST_DELAY_S)
        try:
            result = generate(
                client, variation, args.attempt, args.model, spent, args.note
            )
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001 - fall back to the cheaper model
            print(f"{variation}: {args.model} failed ({exc}); falling back")
            time.sleep(REQUEST_DELAY_S)
            result = generate(
                client, variation, args.attempt, FALLBACK_MODEL, spent, args.note
            )
        spent += result.cost
        results.append(result)
        print(
            json.dumps(
                {
                    "variation": result.variation,
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
