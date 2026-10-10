# Scene 2 restage v4 - each adult at their own front door

Three restaged plates for EXT. HOUSE - NIGHT, image-to-image off
`~/factory-plan/omni/s2/s2-restage-t2.png` (the Omni house, which is the locked
one). They differ only in van angle and camera position. The door assignment is
identical in all three.

**Compare sheet:**
<https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/factory/s2/restage-v4/s2-restage-v4-compare.png>

## The one line, per variation

| | one line |
|---|---|
| **v4-B over the nose** (recommended) | Nina is at the front passenger door with her hand closed on that handle; Gabe is in the near foreground rounding the van's nose on his way to the driver's door. |
| **v4-A nose camera-left** | Nina is at the front passenger door by the wing mirror, clutch in her other hand; Gabe is out at the van's nose on the far side, rounding the grille to the driver's door. |
| **v4-C raised wide** | Nina is at the front passenger door with her fingers wrapped on that handle; Gabe is at the van's nose, hand on the bonnet, swinging around it to the driver's door. |

## Files

All in `r2:rex-assets/factory/s2/restage-v4/`, served from
`https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev/factory/s2/restage-v4/`.

| file | what it is |
|---|---|
| `s2-restage-overthenose-a2.png` | **v4-B, the pick.** Low camera across the van's nose. |
| `s2-restage-noseleft-a2.png` | v4-A. Eye level, van nose to frame left, van's whole length between the two of them. |
| `s2-restage-highwide-a3.png` | v4-C. Raised camera, wide. |
| `s2-restage-v4-compare.png` | Four-up against the rejected v3 broadside. |
| `*-a1.png`, `highwide-a2.png` | Earlier attempts, kept for the record. |

## What was actually wrong, and what fixed it

Both dead takes have the same root cause: the still never said which door each
person uses, so the video model picked one.

- **t2** - the van's rear faced the run. No door on that surface at all, so Gabe
  grabbed the tail light.
- **t3** (off `s2-restage-broadside.png`) - the van is broadside, but the sliding
  door handle and the front passenger door handle sit inches apart at the
  B-pillar and Nina's hand in the plate lands between them. She pulled one and
  the other opened; Gabe then climbed in behind her through the same sliding
  door.

The fix is geometric, not verbal. **Turn the van so its nose is the end
presented to camera.** That does three things at once:

1. The front passenger door becomes the big, near, unambiguous door, and
   everything behind the B-pillar foreshortens away or leaves frame entirely.
   In v4-B there is exactly **one door handle on the van in the whole image**.
2. It puts the tail out of the shot, so the t2 failure cannot recur.
3. It gives Gabe somewhere to go that is visibly *not* Nina's door. Rounding the
   nose is a legible, one-second action that ends on the far flank - the
   driver's side - which the camera never sees. He cannot be read as following
   her through her door because his path leaves the frame in the other
   direction.

Nina rides shotgun, Gabe drives. The sliding door is the kids' door and plays no
part in this beat.

## Caveat on v4-C

v4-C is the weakest of the three and is marked amber on the sheet. Nina's grip
on the front passenger handle is correct and unambiguous, but the raised wide
framing keeps enough of the flank in shot that the **sliding door handle is still
visible about a hand's width behind her**, and a red tail light clips the right
edge. It is a long way better than the v3 control - she is forward of the
B-pillar and clearly gripping the front handle, not standing between two of them
- but if the sliding handle near her hand is the thing that killed t3, v4-C is
the one that could do it again. Three attempts were spent on this variation and
the budget cap closed before a fourth; v4-B and v4-A are clean.

## Cost

7 images on `gemini-3-pro-image-preview`, **$0.938 against the $1.00 cap**
(a1 x3, a2 x3, highwide a3). Stills only. No video was generated - Runway was
not fired from this machine.

## Reproducing

```bash
./scripts/setup_python_env.sh
.venv/bin/python scripts/factory/restage_s2_own_doors.py             # dry run
.venv/bin/python scripts/factory/restage_s2_own_doors.py --fire
.venv/bin/python scripts/factory/build_s2_restage_v4_sheet.py
```

The script carries a hard `$1.00` governor that refuses to fire when the next
image would cross it, so `--spent` must be passed honestly across runs.

## Worth keeping

- The v3 script fed `family_car_exterior.png` in as a van reference and it kept
  dragging the render back toward a rear three-quarter. v4 drops the van
  reference entirely and feeds the **character** lockups instead
  (`gabe_turnaround_APPROVED.png`, `nina_dress_turnaround.png`). The van reads
  fine from the plate alone, and the faces and wardrobe came back tighter.
- Naming the geometry beats naming the intent. "Her hand is on the front
  passenger door handle" produced two handles side by side. "Everything behind
  the B-pillar is out of frame; exactly one door handle is visible on the van"
  produced one handle.
- The model ignores left/right in "nose toward frame left" about half the time,
  and it does not matter - what matters is that the **nose**, not the tail, is
  the presented end. Let it pick the side.
