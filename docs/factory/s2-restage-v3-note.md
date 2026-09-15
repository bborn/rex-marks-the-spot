# Scene 2 restage v3 — giving the van a reachable door

**Date:** 2026-09-01 · **Scene:** 2, EXT. HOUSE — NIGHT · **Stills only, no video fired.**

Bruno picks one. The chosen still then goes to Grok to fire on Runway Omni — not from here.

---

## The defect

`omni-s2-t2.mp4` had Gabe grab the van's **tail light** to open it, then vanish,
while Nina climbed in a front door she never ran toward.

This was never a prompt bug. In the plate `s2-restage-t2.png` the minivan sits at
frame right with its **rear quarter** angled toward the house. The couple runs
left-to-right into the back end of the vehicle. The only feature on the surface
they are approaching is a tail light, so the model reached for it. Staging that
does not afford the action cannot be prompted around.

## What changed

Exactly one thing: **where the van sits and which way it faces.** Both options
were made image-to-image off `s2-restage-t2.png`, so the rest of the frame is
carried over rather than re-imagined.

| Option | Staging | The affordance |
|---|---|---|
| **A — Broadside** (`s2-restage-broadside.png`) | Van parallel to the driveway, full flank square to camera, nose at frame right. Sliding door, front passenger door, wing mirror, front wheel all present; tail out of frame. | Nina's hand is already closing on the **sliding door handle**. Unmistakable. |
| **B — Nose-in** (`s2-restage-nosein.png`) | Van angled, front three-quarter to the approach — grille, headlight, windscreen, mirror. | Two adjacent handles — front passenger door and sliding door — at the end of the run. Gabe's line ends at one, Nina's at the other. |

**No tail light, rear hatch or licence plate is in the characters' path in either.**

## What stayed locked

- **House** — same grey shingle two-storey, same window pattern and warm interior
  glow, same open front door with hallway light and staircase, same wall lantern,
  same white garage door, same purple hydrangeas, same porch steps. Not restyled,
  not reopened, camera not moved off it.
- **Storm** — same rain streaks, same storm sky, same lightning in the upper
  right, same wet flagstone driveway throwing back the warm doorway light, same
  colour grade.
- **Vehicle** — the same teal family minivan. Not a sedan, not a different van.
- **Characters** — two people only. Gabe: tuxedo, bow tie, black rectangular
  glasses, stubble, dad bod, face from `gabe_turnaround_APPROVED.png`. Nina:
  auburn wavy hair, freckles, green eyes, sleeveless black midi, clutch, heels.
  Same faces, same wardrobe, same mid-run beat as the current plate.
- **Look** — stylised Pixar-style 3D. No drift toward photoreal.

## What it cost

5 images on `gemini-3-pro-image-preview` at ~$0.134 each = **~$0.67** against the
$1.00 cap. No video. The Runway key was never touched.

## What we learned (worth keeping)

**Do not feed `family_car_exterior.png` into a restage that is trying to get the
van's tail out of the approach.** That reference is itself a rear three-quarter
of the van, complete with tail lights and bumper stickers. Attempts 1 and 2 of
the broadside kept snapping back to a rear-quarter with a red tail light at frame
right, and the written correction ("no tail light, nose at frame right") made it
*worse* — the note fought the picture and the picture won. Attempt 3 dropped the
van reference entirely and described the van's silhouette in words, front-to-back
in reading order, and landed it first try. The script now takes `--no-van-ref`
for this.

Corollary: on a restage, a correction note phrased against the base image pulls
the render *toward* the base image. When the base image is the defect, remove it
from the evidence rather than arguing with it.

## Files

R2: `r2:rex-assets/factory/s2/restage-v3/`
(`https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/factory/s2/restage-v3/<name>`)

| File | What |
|---|---|
| `s2-restage-broadside.png` | **Option A**, deliverable (= attempt 3) |
| `s2-restage-nosein.png` | **Option B**, deliverable (= attempt 1) |
| `s2-restage-v3-compare.png` | Side-by-side sheet: rejected plate, A, B |
| `s2-restage-broadside-a1..a3.png`, `s2-restage-nosein-a1..a2.png` | All attempts, kept as record |

Code: `scripts/factory/restage_s2_van_door.py`,
`scripts/factory/build_s2_restage_sheet.py`.

## Open note for whoever fires this

Option A shows the van's driver-side flank (nose at frame right). Scene 3 is
locked with Gabe driver-left and Nina passenger-right in the car interior. If
that matters to the cut, Option B is the safer join. Flagging it rather than
deciding it.
