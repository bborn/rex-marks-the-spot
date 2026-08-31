#!/usr/bin/env python3
"""Generate the v5 END panel for each Scene 1 shot, and gate it on identity.

Why this exists
---------------
`storyboards/v5/scene-01/` has only `-start` panels. MiniMax H3's
`end_image_url` needs a last frame per shot, and task #341 measured that
anchoring to an OFF-MODEL last frame is worse than not anchoring at all
(continuity 0.354 with a bad anchor vs 0.231 with none, and the clip ends as a
different person). So every end panel has to clear the same identity gate the
start panels cleared before it may be used.

An end panel is the SAME STAGING at the END of the shot's action. Same room,
same camera, same cast, same wardrobe, same light - only the moment differs.
The moment is taken from the beat verb in `asset-bible/manifests/scene-01.json`
(the camera note) and the Key Action line in
`docs/storyboards/act1/scene-01-home-evening.md`.

Two techniques carried over from task #345, which is the point of doing this
after #345 rather than before it:

1. **No image plate on a shot where a face is large in frame.** 1B, 1D, 1E, 1H
   and 1I are built from the locked turnarounds plus written staging
   (`END_STAGING`); the plate is only attached on the wides and the object
   insert (1A, 1C, 1F, 1G).
2. **Light the graded detail, don't only draw it.** `LIT_DETAIL` asks for
   Gabe's rims as brushed silver wire with a specular highlight and a gap of
   lit skin at the brow. #345 moved Gabe 0.40 -> 1.00 on pixels that were
   already correct by doing exactly this.

One difference from #345 worth stating, because it changes what the plate is
for. In #345 the plate was a v4 panel, i.e. a picture of the WRONG PEOPLE, and
its whole risk was that the model copied the faces. Here the plate is the v5
START panel of the same shot, which already passed the identity gate. So on the
plated shots the instruction is the opposite of #345's: keep the people exactly
as drawn, and change only the moment. The plate is still downscaled, because a
sharp plate makes the model reproduce the frame rather than advance it.

Usage:
  python3 scripts/gen_scene01_end_panels.py                       # all 9
  python3 scripts/gen_scene01_end_panels.py 1B 1E                 # subset
  python3 scripts/gen_scene01_end_panels.py --max-attempts 2 --budget 1.20
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location("regen_v5", ROOT / "scripts/regen_scene01_v5.py")
regen = importlib.util.module_from_spec(_spec)
sys.modules["regen_v5"] = regen
_spec.loader.exec_module(regen)

_vspec = importlib.util.spec_from_file_location(
    "shot_validator", ROOT / "scripts/validate/shot_validator.py")
sv = importlib.util.module_from_spec(_vspec)
sys.modules["shot_validator"] = sv
_vspec.loader.exec_module(sv)

from google.genai import types  # noqa: E402  (after sys.path setup)

MANIFEST = ROOT / "asset-bible/manifests/scene-01.json"
CHAR_DIR = ROOT / "asset-bible/characters"
LOC_DIR = ROOT / "work/locations"
START_DIR = ROOT / "work/v5"          # the validated v5 start panels
OUT_DIR = ROOT / "work/v5-end"
VAL_DIR = ROOT / "work/val-end"
SHEET = ROOT / "scripts/validate/identity-sheets.json"
LEDGER = ROOT / "reports/scene-01-v5-render/ledger.json"

IMAGE_COST = 0.04          # gemini-3-pro-image-preview, per generated image
IDENTITY_GATE = 0.60

# The plate is attached only where no face is large in frame.  Everything else
# is built plateless from the turnarounds + END_STAGING (technique 1, #345).
PLATED = {"1A", "1C", "1F", "1G"}
PLATE_MAX_EDGE = {1: 640, 2: 512, 3: 448}


# ---------------------------------------------------------------------------
# What has changed by the end of the shot.  One entry per shot, taken from the
# beat verb in the manifest's camera note and the Key Action in the scene
# breakdown.  Keep these MODEST: an end frame that is a different composition
# gives H3 licence to re-stage the shot rather than play it.
# ---------------------------------------------------------------------------

END_ACTION = {
    "1A": (
        "This is the LAST frame of an 8-second STATIC wide establishing shot. "
        "The camera has not moved at all - identical position, identical lens, "
        "identical framing. What has changed in eight seconds:\n"
        "  - The lightning outside the windows is at its BRIGHTEST: a forked "
        "blue-white bolt across the dark sky behind the glass, throwing a cold "
        "blue wash across the middle of the room and the back of the couch. "
        "The bolt stays OUTSIDE the window; never over an interior wall, over "
        "furniture or over a person.\n"
        "  - The TV at screen left has glitched: a band of grey static rolls "
        "through the cartoon picture, the colours have jumped.\n"
        "  - Leo has turned his head to his left, away from the TV, looking "
        "toward his parents across the room; he still hugs the plush dinosaur.\n"
        "  - Mia has turned her head toward the windows at the lightning, lips "
        "parted.\n"
        "  - Jenny has not moved at all - still head-down on her phone.\n"
        "Everyone stays exactly where they were. Nobody stands up, nobody "
        "leaves, nobody new enters, nothing moves position in the room."
    ),
    "1B": (
        "This is the LAST frame of a 6-second medium shot with a slight PUSH. "
        "What has changed in six seconds:\n"
        "  - The push has completed: Leo is about 10 percent LARGER in frame "
        "than at the start and very slightly lower, the couch back a little "
        "closer. It is the same camera on the same axis, only marginally "
        "nearer - not a new angle and not a close-up.\n"
        "  - Leo has tipped his head down toward the green plush dinosaur he "
        "is hugging, chin tucked, eyes on the toy, and broken into a quick "
        "delighted open-mouthed grin - a small private giggle at his own toy.\n"
        "Nothing else changes. He stays cross-legged in the same spot on the "
        "same cushion, the toys stay where they are, Mia stays at the extreme "
        "left edge of frame."
    ),
    "1C": (
        "This is the LAST frame of a 15-second medium TRACKING shot that "
        "follows Nina across the room toward the front door. By the FIRST "
        "frame the track has essentially ARRIVED - she is already at the front "
        "hall - so the camera barely moves in the last stretch. Treat this as "
        "a nearly LOCKED-OFF frame. What has changed:\n"
        "  - Nina has finished putting the earring in. BOTH hands are now DOWN "
        "- one settling the small black purse against her hip, the other "
        "loose at her side. Her arms are no longer raised to her ear and her "
        "elbows are no longer up.\n"
        "  - She has turned her head to look BACK over her shoulder into the "
        "living room at screen right, mouth open mid-sentence, brows up - "
        "still calling instructions to the babysitter, and looking for her "
        "phone.\n"
        "  - The camera has drifted a very small distance - no more than a "
        "hand's width of parallax. Nina stays in the SAME PLACE in the frame "
        "and at the SAME SIZE, the front door stays behind her at screen "
        "left, the armchair and the babysitter stay at screen right, the "
        "console table and lamp stay at the far left edge. Same lens, same "
        "height, same distance.\n"
        "  - Gabe stays exactly where he is beside the front door, waiting. "
        "He does not move closer to camera and he does not get larger.\n"
        "  - Jenny stays curled in the armchair on her phone.\n"
        "Nobody new enters and nothing is re-staged."
    ),
    "1D": (
        "This is the LAST frame of a 45-second STATIC two-shot with occasional "
        "reframes. The camera is in the same place at the same height on the "
        "same lens. What has changed:\n"
        "  - Gabe has DROPPED HIS WRIST. He is no longer looking at his watch. "
        "Both of his hands are now open, palms turned slightly up and lifted a "
        "little away from his sides in an exasperated 'can we PLEASE go' "
        "gesture. His head is UP and turned toward Nina, eyebrows raised, "
        "mouth open mid-word. Frustrated but not angry - comic exasperation.\n"
        "  - Nina has turned more square to him. One hand pats the side of her "
        "hip as if feeling for a pocket, the other is held palm-up. Her mouth "
        "is open - she is asking him where her phone is - and her expression "
        "has gone from wry sideways glance to open searching appeal.\n"
        "Both of them stay standing in exactly the same spots, the same "
        "distance apart, the same size in frame. The two children on the sofa "
        "behind them and the babysitter in the armchair behind them are "
        "UNCHANGED and still in frame."
    ),
    "1E": (
        "This is the LAST frame of a 5-second STATIC close-up insert. The "
        "camera has not moved at all. What has changed in five seconds:\n"
        "  - Jenny's thumb is mid-tap on the phone screen, having just typed.\n"
        "  - Her expression has warmed: a small, cheerful, closed-lip SMILE at "
        "whatever she is reading, one eyebrow a little up. The slight frown of "
        "the first frame is gone.\n"
        "  - She still has NOT looked up. Her chin is still down, her eyes are "
        "still on the phone. Her head has not turned.\n"
        "  - The phone's cool blue-white glow on her face and hands is a touch "
        "brighter.\n"
        "Nothing else changes: same framing, same pose, same defocused living "
        "room behind her."
    ),
    "1F": (
        "This is the LAST frame of a 4-second STATIC close-up insert on the "
        "television. There are no people in this frame at all. The camera has "
        "not moved. What has changed in four seconds:\n"
        "  - The interference has swelled. Grey static and horizontal scan "
        "lines now cover most of the picture; the cartoon shapes are still "
        "readable underneath but broken up and smeared.\n"
        "  - The BLUE TIME-WARP FLASH is at its peak: a bright blue-white bar "
        "of light blooming across the middle of the screen, brighter and wider "
        "than in the first frame, with a visible glow spilling out of the "
        "screen onto the wooden TV cabinet, the wall and the lampshade.\n"
        "  - The lightning visible through the window at screen right has "
        "faded to a dimmer afterglow.\n"
        "Same television, same angle, same room behind it, same furniture. No "
        "people enter the frame."
    ),
    "1G": (
        "This is the LAST frame of a 30-second STATIC over-the-shoulder shot "
        "from behind the two children. The camera has not moved.\n"
        "Read the beat carefully: the children glance back at their parents "
        "IN THE MIDDLE of this shot and have RETURNED THEIR ATTENTION TO THE "
        "CARTOON by the end of it. So in this last frame:\n"
        "  - BOTH CHILDREN ARE FACING THE TELEVISION AGAIN, backs to camera, "
        "exactly as in the first frame. NEITHER CHILD'S FACE IS VISIBLE. Do "
        "not turn a child toward camera; do not show a cheek, an eye or a "
        "profile. We see the back of the girl's head with her high curly "
        "ponytail at screen left and the back of the boy's blond head at "
        "screen right, and nothing more of either of them. Their heads have "
        "settled a fraction lower and closer together than in the first "
        "frame - they have just turned back - but they are otherwise "
        "identical.\n"
        "  - In the background, NINA has turned toward the children and "
        "lifted one hand in a small goodbye wave, smiling at them. GABE has "
        "half-turned toward the door and is glancing back over his shoulder "
        "at them.\n"
        "  - The cartoon on the TV is at a different moment - the same show, "
        "the same flat cartoon style, a different arrangement of the same "
        "cartoon figures.\n"
        "Nobody stands up, nobody leaves the room, the couch backs stay "
        "across the bottom of frame exactly as they are, and the room, "
        "furniture, windows and storm are unchanged."
    ),
    "1H": (
        "This is the LAST frame of a 20-second close-up with a very SLOW PUSH "
        "in. What has changed:\n"
        "  - The push has completed: Mia is about 12 percent LARGER in frame "
        "than at the start, and her head sits a little higher. Same camera "
        "axis, same lens character - marginally nearer, not a new angle.\n"
        "  - She has FINISHED speaking. Her mouth is now CLOSED, lips pressed "
        "gently together. Her eyebrows have lifted in the middle into a small "
        "hopeful plea. Her eyes are still turned up and off to screen right at "
        "her parents, and they are shining - a little glassy, catching the "
        "window light. She is waiting for an answer.\n"
        "  - The lightning outside the window has faded from its bright fork "
        "to a dimmer blue-white afterglow, so the cold rim light on her is "
        "softer and the warm lamp is doing more of the work.\n"
        "The out-of-focus foreground shapes at the extreme left and right "
        "edges of frame stay exactly where they are, still out of focus, still "
        "cropped at the frame edge."
    ),
    "1I": (
        "This is the LAST frame of the shot. Gabe has just given in and said "
        "'Promise.' Tension, then release. What has changed:\n"
        "  - GABE has lifted his chin and is now looking straight at Nina "
        "instead of down and away. His mouth is open mid-word and the guilty "
        "wince has resolved into a small, tired, conceding half-smile. One "
        "hand has come up a little from his side, palm turned out, in a small "
        "'all right, all right' gesture. He is no longer hesitating.\n"
        "  - NINA's glare has released. Her lowered brows have come up, her "
        "shoulders have dropped out of their squared-off set, and there is a "
        "small satisfied close-lipped smile at the corner of her mouth. Her "
        "fists have opened. Her body has begun to turn toward the front door "
        "and her near hand is starting to reach toward the brass doorknob.\n"
        "Both stay standing in the same spots at the same distance from "
        "camera, the same size in frame. The entryway, the lamp, the "
        "coat-tree, the console tables and the storm at the window are all "
        "unchanged. Still EXACTLY two people in frame and nobody else."
    ),
}


# ---------------------------------------------------------------------------
# Plateless staging for the shots where a face is large in frame (technique 1).
# Written by reading the validated v5 START panel: camera height and distance,
# figure scale, poses, the set left to right, the floor, and the direction and
# colour of the light.  Deliberately says nothing about what the characters
# LOOK like - that comes from the identity block, rendered from the locked
# sheet.  1I's is reused verbatim from regen_scene01_v5.PLATELESS_STAGING.
# ---------------------------------------------------------------------------

END_STAGING = {
    "1B": (
        "FRAMING AND CAMERA. Eye-level with a seated five-year-old, static, a "
        "medium shot across a living-room couch at night. The boy is centred "
        "slightly right of the middle of the frame and occupies roughly the "
        "middle third; his head is about one third of the frame's height. "
        "Normal lens, shallow-ish depth so the room behind him is soft but "
        "readable. Camera about six feet back.\n"
        "    BLOCKING. LEO sits cross-legged on the centre cushion of a "
        "large grey-taupe fabric couch, feet bare and tucked in, both arms "
        "wrapped around a bright green plush dinosaur held against his chest.\n"
        "    MIA is cropped hard at the EXTREME LEFT EDGE of frame - only the "
        "back and side of her head and one shoulder are in shot, out of focus, "
        "facing away from camera toward her brother. She is a foreground "
        "silhouette, not a subject.\n"
        "    SET, LEFT TO RIGHT. Far left behind Mia: a dark wooden bookcase "
        "with books and a stack of paper. Left of centre: a grey upholstered "
        "armchair with a cushion on it, and behind it a floor lamp with a warm "
        "cream drum shade, lit. Behind the couch, filling the top right two "
        "thirds: a large white-framed sash WINDOW in several panes, rain "
        "streaking the glass, wet dark foliage and a blue-white LIGHTNING BOLT "
        "in the clouds OUTSIDE the glass. On the windowsill behind the couch, "
        "screen right: a short stack of hardback books and a potted green "
        "plant. ON THE COUCH with him: a brown plastic toy T-Rex standing on "
        "the left cushion in front of a grey throw pillow, a brown plastic "
        "Triceratops on the cushion to his right, and a tan pterodactyl lying "
        "on the far right cushion beside a second grey pillow. Warm honey "
        "hardwood floor visible bottom left.\n"
        "    LIGHT. Warm amber key from the floor lamp at screen left and from "
        "the television off-frame left, filling his face; cool blue spill from "
        "the stormy window behind rims his hair and the top of the couch. "
        "Cosy, low-lit, night-time domestic."
    ),
    "1D": (
        "FRAMING AND CAMERA. Eye-level, static, a medium two-shot in a living "
        "room at night, both adults framed from about mid-thigh up. Normal "
        "lens, camera roughly eight feet back. Each head is about one fifth of "
        "the frame's height. Five people are in frame: two adults standing in "
        "the foreground and, well behind them and smaller, two children on a "
        "sofa at screen left and a teenage girl in an armchair at screen "
        "right.\n"
        "    BLOCKING. GABE stands just left of centre, his body squared to "
        "camera and turned very slightly screen-right, filling the centre of "
        "the frame. NINA stands to his right, close beside him, her body "
        "turned screen-left toward him, her arms down.\n"
        "    SET, LEFT TO RIGHT. Far left: a wooden side table with a "
        "cream-shaded table lamp, lit, and a stack of magazines under it. Left "
        "third: the arm and seat of a grey-taupe fabric SOFA seen side-on, "
        "with the two children sitting on it - the girl nearer camera with her "
        "legs crossed and an open picture book on her lap, the small boy "
        "beside her hugging a green plush dinosaur. Behind the sofa, filling "
        "the upper left third: a large white-framed multi-pane WINDOW with a "
        "beige curtain drawn back at its right edge, rain on the glass, and a "
        "blue-white LIGHTNING BOLT in the dark clouds OUTSIDE the glass. "
        "Centre and right: a plain warm-beige wall. Right third: a grey "
        "armchair, angled toward camera, with the teenage babysitter curled "
        "sideways in it looking down at a phone held in both hands, white "
        "sneakers up on the seat; behind her a floor lamp with a cream drum "
        "shade, lit, against the wall. A dark rug on honey hardwood at the "
        "bottom of frame.\n"
        "    LIGHT. Warm amber key from the two practical lamps, left and "
        "right; cool blue fill from the window behind the sofa, raking across "
        "the left side of the frame. Warm, lived-in, a little tense."
    ),
    "1E": (
        "FRAMING AND CAMERA. A close-up insert, static, slightly above her eye "
        "level, on a teenage girl sitting in a dim living room at night. She "
        "is in three-quarter profile facing SCREEN LEFT, placed centre-right "
        "of frame, cut off at about the waist by the bottom edge. Her head is "
        "about half the frame's height. Long lens, very SHALLOW DEPTH OF "
        "FIELD - the entire room behind her is soft, blurred bokeh, and only "
        "her face, hair and hands are sharp.\n"
        "    BLOCKING. She sits on the arm or edge of a couch, head bowed over "
        "a dark smartphone she holds in both hands low in the frame, below her "
        "chin at bottom centre-left. Her shoulders are rounded forward. She is "
        "looking down at the screen, not at the room.\n"
        "    SET, LEFT TO RIGHT, ALL DEFOCUSED. Far left: a floor lamp with a "
        "cream shade, lit, a bright warm blob; beside it a pale curtain. Left "
        "of centre and behind her: two tall white-framed WINDOWS with rain on "
        "the glass and pale blue-white LIGHTNING glowing OUTSIDE them, and "
        "below them the back of a grey couch with a cushion on it. Right of "
        "her head: a pale wall, a small framed picture, a leafy potted plant. "
        "Far right: a dark wooden bookshelf with books. A soft warm surface "
        "crosses the very bottom right corner.\n"
        "    LIGHT. The PHONE is the key: a cool blue-white glow from below, "
        "lighting her chin, the underside of her nose, her cheek and her "
        "hands, and leaving her brow in shadow. Warm amber ambience from the "
        "lamp at screen left on her hair and the edge of her hood. Cool blue "
        "window light behind her, separating her from the wall. Dim, intimate, "
        "night-time."
    ),
    "1H": (
        "FRAMING AND CAMERA. A close-up on a seated eight-year-old girl, at "
        "her eye level, looking very slightly up. She is centred, her head "
        "filling about half the frame's height, framed from the knees up with "
        "her knees drawn toward her chest at the bottom of frame. Her body is "
        "in three-quarter view turned SCREEN RIGHT and her chin is LIFTED - "
        "she is looking up and off screen right at adults who are not in "
        "focus. Longish lens; the background is soft but readable.\n"
        "    FOREGROUND. At the EXTREME LEFT EDGE and the EXTREME RIGHT EDGE "
        "of the frame, hard out of focus and cropped by the frame, are two "
        "over-the-shoulder foreground shapes - the near shoulder and side of "
        "the head of a dark-haired adult at the left, warm-lit, and at the "
        "right the dark clothed shoulder and the underside of a bearded jaw of "
        "a second adult. They are blurred foreground masses that frame her, "
        "not characters in the shot; neither face is legible.\n"
        "    SET. Behind her at screen left: the back and arm of a grey couch "
        "with a cushion, a cream-shaded table lamp lit on a table, and a small "
        "framed botanical picture on a warm beige wall, with a curtain edge "
        "above. Behind her at screen right: a large white-framed multi-pane "
        "WINDOW, rain on the glass, dark wet foliage beyond, and a bright "
        "forked blue-white LIGHTNING BOLT in the sky OUTSIDE the glass. Honey "
        "hardwood floor in the bottom right corner.\n"
        "    LIGHT. Warm amber key from the table lamp at screen left across "
        "her face; hard cool blue-white from the window at screen right rimming "
        "her right cheek, her shoulder and the edge of her hair. Her eyes catch "
        "both. Warm but vulnerable; this is the emotional anchor of the scene."
    ),
    "1I": regen.PLATELESS_STAGING["1I"],
}


# Per-shot corrections found by eyeballing the first pass of end panels against
# their start panels.  Each one is a real, observed failure of the matched pair,
# not a precaution: 1C grew sleeves on a sleeveless gown and re-staged the room,
# 1G invented a third child and put the parents on the television, 1H lost Mia's
# ponytail and ran the push BACKWARDS so she got smaller.
EXTRA_NOTE = {
    "1C": (
        "SPECIFIC CONTINUITY TRAPS IN THIS SHOT:\n"
        "  - NINA'S GOWN IS SLEEVELESS, with thin shoulder straps and a V "
        "neckline, and her arms are BARE from the shoulder down. She does NOT "
        "gain sleeves, a jacket, a wrap or a shrug between the two frames.\n"
        "  - Do not re-stage the room. The white panelled front door, the "
        "coat-tree, the console table with the lamp, the floor lamp, the "
        "armchair and the side table all stay exactly where the first frame "
        "puts them, at the same size.\n"
        "  - JENNY IS SMALL AND IN THE BACKGROUND HERE, and her hair is the "
        "attribute this shot loses. Draw her ponytail as a CLUMPED, LUMPY, "
        "RAGGED mass of separated CURLS with a bumpy outline and two or three "
        "loose corkscrew curls springing free at her temple and jaw - big, "
        "chunky curl shapes, drawn larger than looks natural so they survive "
        "at this size. A smooth ponytail silhouette is scored as straight "
        "hair and fails the panel."
    ),
    "1G": (
        "SPECIFIC CONTINUITY TRAPS IN THIS SHOT:\n"
        "  - THERE ARE EXACTLY TWO CHILDREN IN THIS FRAME. One girl at screen "
        "left with a high curly ponytail, one blond boy at screen right. Do "
        "not add a third child, a third head or a third silhouette.\n"
        "  - THE TELEVISION SHOWS A CHILDREN'S CARTOON - flat, brightly "
        "coloured cartoon characters. It never shows the parents, the living "
        "room, the children, or anything from this film.\n"
        "  - The parents stand in the ROOM in the background beside the "
        "bookcase, on the far side of the couch. They are not in a doorway "
        "and there is no open door behind them.\n"
        "  - The couch backs run across the bottom of the frame and the two "
        "children sit on the floor in front of them, seen from behind and "
        "slightly above."
    ),
    "1D": (
        "SPECIFIC CONTINUITY TRAPS IN THIS SHOT:\n"
        "  - NINA'S GOWN IS SLEEVELESS, with thin shoulder straps and a "
        "surplice V neckline, and her arms and shoulders are BARE. She does "
        "NOT gain sleeves, a jacket, a wrap or a shrug between the two "
        "frames.\n"
        "  - Gabe and Nina stay the same size in frame and the same distance "
        "apart. The camera does not push in, pull back or change angle."
    ),
    "1H": (
        "SPECIFIC CONTINUITY TRAPS IN THIS SHOT:\n"
        "  - A PUSH IN MAKES HER BIGGER. She must fill MORE of the frame than "
        "in the first frame, not less. HER HEAD ALONE - crown to chin - takes "
        "up ABOUT HALF THE HEIGHT OF THE IMAGE, and the top of her hair is "
        "close to the top edge of the frame. This is a TIGHT close-up on a "
        "face, not a medium shot of a seated child. Do not pull back, do not "
        "widen, do not shrink her, do not include more of the room.\n"
        "  - HER HAIR IS IN A HIGH CURLY PONYTAIL, gathered up at the back of "
        "her head with a pink tie, with long springy curls falling from it "
        "past her jaw and loose curls around her face. It is NOT short, NOT "
        "cropped, and NOT worn loose. The ponytail is a locked design detail "
        "and it does not come out between the two frames."
    ),
}


# Technique 2 from #345: light the graded detail rather than only drawing it.
# A hairline rim drawn correctly and then lost in a dim warm key reads to the
# validator as a solid dark frame.  This is not a departure from the identity
# sheet - `thin_wire_rectangular` already says the rims catch a small metallic
# highlight - it is the same frames rendered so they survive being small.
LIT_DETAIL = {
    "Gabe": (
        "GABE'S GLASSES, LIGHTING NOTE - this is the single most-failed detail "
        "in this scene, and it fails on how it is LIT, not on how it is drawn. "
        "Render the rims as BRUSHED SILVER WIRE catching a bright specular "
        "highlight along the top edge of each lens, so the frame reads as a "
        "thin bright metal line rather than a dark one. Leave a clear GAP OF "
        "LIT SKIN between the top of the rim and his eyebrow - his brow must be "
        "visible above the frame, warmly lit, not shadowed. Put extra warm key "
        "on his face so the rims never fall into shadow. Hairline-thin rims "
        "drawn correctly but lost in a dim key read as thick black plastic. "
        "SHAPE, equally graded: each lens is RECTANGULAR - clearly WIDER THAN "
        "IT IS TALL, with a straight flat TOP EDGE and squared outer corners. "
        "Never round, never oval, never circular; a small circular lens is "
        "scored as wrong an eyewear as a thick black one. This holds even when "
        "he is small in frame or in the background - if his head is only a few "
        "dozen pixels tall, draw the rims as two short bright horizontal "
        "strokes rather than letting them collapse into dots."
    ),
    "Jenny": (
        "JENNY'S SKIN TONE, LIGHTING NOTE: keep her clearly MEDIUM BROWN and "
        "the darkest skin tone in the frame even where the light is cool or "
        "dim - warm lamplight must not wash her toward the others, and cool "
        "phone or window light must not grey her out. "
        "JENNY'S HAIR, equally graded: DARK BROWN and CURLY - springy, defined, "
        "separated curls with a BROKEN, bumpy silhouette, gathered into a "
        "ponytail with loose curls escaping at the temples. Never a smooth "
        "sleek straight fall of hair. This holds in the background and at small "
        "size: if she is far from camera, draw the ponytail's outline as a "
        "ragged clumped shape rather than a smooth teardrop."
    ),
    "Leo": (
        "LEO'S HAIR: unmistakably BLONDE / golden, the lightest hair in the "
        "frame, and it must still read blonde where the room light is warm "
        "amber or where he is backlit - never let it darken to brown."
    ),
}


def _build_end_prompt(shot: dict, identity_lines: dict[str, str],
                      notes: str = "", plated: bool = True) -> str:
    sid = shot["shot_id"]
    chars = shot.get("characters", []) or []
    wardrobe = shot.get("wardrobe", {}) or {}
    props = shot.get("key_props", []) or []
    camera = shot.get("camera", "")

    L: list[str] = []
    L.append(
        f"Generate the LAST FRAME of shot {sid} of an animated feature film - "
        "the frame the shot ends on."
    )
    L.append("")
    L.append(
        "THIS IS A MATCHED PAIR. The first frame of this shot already exists "
        "and is approved. Your frame is the SAME SHOT five seconds later: same "
        "room, same camera, same lens, same cast, same wardrobe, same lighting "
        "design, same art style. A viewer must read the two frames as the "
        "beginning and the end of one continuous take, not as two different "
        "shots. Only the MOMENT has advanced."
    )
    L.append("")

    if plated:
        L.append(
            "THE FIRST FRAME IS ATTACHED, at deliberately LOW RESOLUTION. It is "
            "the APPROVED, ON-MODEL opening frame of this very shot - the "
            "people in it are the correct people and are drawn correctly. Keep "
            "ALL of it: the camera position and focal length, the room, the "
            "furniture and its placement, the props, the light sources and "
            "their colour, and the characters' identities, wardrobe and "
            "positions. Its softness is an artifact of the downscale - render "
            "your own frame at full crisp detail. Change ONLY what the action "
            "below says has changed."
        )
        L.append("")
    else:
        L.append(
            "THE ONLY IMAGES ATTACHED ARE THE LOCKED CHARACTER TURNAROUNDS. "
            "They are the character designs for this film and they are the only "
            "authority on what each person looks like - face, hair, skin tone, "
            "build, age, glasses, facial hair. There is no picture of this shot "
            "attached; the staging is written out for you below and you are "
            "composing the frame from that description."
        )
        L.append("")
        L.append("STAGING - build the frame exactly as described:")
        L.append(END_STAGING[sid])
        L.append("")

    L.append(f"THE ACTION - what this LAST frame shows:")
    L.append(END_ACTION[sid])
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
            "WARDROBE for THIS shot - MANDATORY and IDENTICAL to the first "
            "frame. This OVERRIDES whatever the character wears in their "
            "turnaround; a turnaround is an identity card, not a dress code. It "
            "does NOT override anything in the identity block above. Nobody "
            "changes clothes between the first frame and the last:"
        )
        for name, desc in wardrobe.items():
            extra = regen.WARDROBE_DETAIL.get(name, "")
            L.append(f"  - {name}: {desc}" + (f" ({extra})" if extra else ""))
        L.append("")
    if props:
        L.append("KEY PROPS - all of these must still be visible:")
        for p in props:
            L.append(f"  - {p}")
        L.append("")

    if chars:
        L.append(
            f"HEADCOUNT: EXACTLY {len(chars)} "
            f"{'person' if len(chars) == 1 else 'people'} appear in this frame "
            f"({', '.join(chars)}) and nobody else. Do not add a background "
            "figure, a sibling, a passer-by or a reflection of a person."
        )
        L.append("")
    L.append(f"CAMERA / FRAMING for the whole shot: {camera}")
    L.append(
        "Read the camera note as describing the WHOLE shot. Your frame is the "
        "END of that move: if the note says PUSH, the push has finished; if it "
        "says TRACK, the track has arrived; if it says STATIC, the camera is "
        "in exactly the same place it started."
    )
    L.append("")
    L.append(
        "CONTINUITY TEST: if your frame were cut directly after the first "
        "frame, the only visible changes should be the ones listed under THE "
        "ACTION. Do not change the camera angle, the focal length, the room, "
        "the furniture, the props, the colour of the light or anyone's "
        "clothes. Do not add or remove a person. Do not re-stage the shot."
    )
    L.append("")
    L.append(
        "SCREEN DIRECTION - do NOT mirror this frame. Every left/right in the "
        "staging above is the LEFT and RIGHT of the finished picture as the "
        "audience sees it. A character described as facing SCREEN LEFT must "
        "have their nose pointing toward the LEFT edge of your image, and the "
        "set dressing must appear on the side of frame it is named on. "
        "Flipping the composition horizontally breaks the cut even if "
        "everything in it is otherwise correct, and it is the single most "
        "common way a matched pair fails."
    )
    L.append("")
    if shot.get("location") == "front_entryway":
        L.append(
            "SETTING: the front hall / foyer of the family home in the "
            "evening - warm interior lamp light, a window onto a dark stormy "
            "night. Any lightning is visible OUTSIDE through a window only; "
            "never draw a bolt over interior walls, furniture or a person."
        )
    else:
        L.append(
            "SETTING: the family living room in the evening - warm interior "
            "lamp light, large windows onto a dark stormy night. Any lightning "
            "is visible OUTSIDE through a window only; never draw a bolt over "
            "interior walls, furniture or a person."
        )
    L.append("")
    if sid in EXTRA_NOTE:
        L.append(EXTRA_NOTE[sid])
        L.append("")
    L.append(regen.STYLE)
    if sid != "1A":
        # 1A's approved START panel is itself in a flatter 2D cartoon style, so
        # for that one shot matching the pair means NOT asking for 3D.  Every
        # other v5 start panel is fully rendered CG, and the first pass of end
        # panels drifted 1D and 1G to flat 2D, which would make the clip change
        # medium halfway through.
        L.append("")
        L.append(
            "ART STYLE - MATCH THE FIRST FRAME. This is FULLY RENDERED 3D CG "
            "feature animation: volumetric light with visible falloff, soft "
            "subsurface skin, individually shaded hair, fabric with weave and "
            "wrinkle, real depth of field, contact shadows. It is NOT a flat "
            "2D cartoon, NOT cel-shaded, NOT vector illustration, NOT line art "
            "with flat fills, and NOT a comic panel. If your frame looks flatter "
            "or more graphic than the first frame, it is wrong."
        )

    risks = [regen.HIGH_RISK[n] for n in chars if n in regen.HIGH_RISK]
    if risks:
        L.append("")
        L.append("FINAL CHECK before you render - the details this scene loses most often:")
        for r in risks:
            L.append(f"  - {r}")
    lit = [LIT_DETAIL[n] for n in chars if n in LIT_DETAIL]
    if lit:
        L.append("")
        L.append(
            "LIGHT THE GRADED DETAILS, do not merely draw them. A small "
            "high-contrast attribute rendered correctly and then left in "
            "shadow is scored as if it were drawn wrong:"
        )
        for x in lit:
            L.append(f"  - {x}")
    if notes:
        L.append("")
        L.append(f"CORRECTIONS FROM THE PREVIOUS ATTEMPT - fix these: {notes}")
    return "\n".join(L)


def generate_end_panel(client, shot: dict, out_path: Path, identity_lines,
                       model: str, notes: str = "",
                       plate_max_edge: int = 640,
                       force_plate: bool = False) -> bool:
    sid = shot["shot_id"]
    plated = force_plate or sid in PLATED
    if not plated and sid not in END_STAGING:
        raise KeyError(
            f"No END_STAGING description for {sid}; write one from the v5 start "
            "panel before running plateless."
        )

    parts: list = []
    start_panel = START_DIR / f"scene-01-{sid}-start.png"
    if plated:
        if not start_panel.exists():
            raise FileNotFoundError(f"v5 start panel missing: {start_panel}")
        parts.append(types.Part.from_text(
            text=("FIRST FRAME OF THIS SHOT - the APPROVED, ON-MODEL opening "
                  "frame, attached at deliberately LOW RESOLUTION. Everything "
                  "in it is correct, including the people. Reproduce it exactly "
                  "and advance only the moment:")))
        parts.append(regen._img_to_part(start_panel, max_edge=plate_max_edge))
    else:
        print(f"  [{sid}] plateless: no start frame attached, staging carried "
              "as text (face large in frame)", flush=True)

    for name in shot.get("characters", []) or []:
        ref_path = regen._resolve_char_ref(name)
        if plated:
            caption = (f"CHARACTER TURNAROUND - this is the REAL {name}, the "
                       f"locked design. The first frame already draws {name} "
                       f"correctly; use this sheet to keep them that way:")
        else:
            caption = (f"CHARACTER TURNAROUND - this is the REAL {name}, the "
                       f"locked design for this film, front / three-quarter / "
                       f"side / back. It is the ONLY authority on what {name} "
                       f"looks like. Read the face and the glasses off this "
                       f"sheet, at this level of detail, and carry them into "
                       f"the frame:")
        parts.append(types.Part.from_text(text=caption))
        parts.append(regen._img_to_part(ref_path))

    parts.append(types.Part.from_text(
        text=_build_end_prompt(shot, identity_lines, notes, plated=plated)))

    print(f"[{sid}] generating END panel with {model} "
          f"({'plated' if plated else 'PLATELESS'}, "
          f"{len(shot.get('characters', []) or [])} char refs)...", flush=True)
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


# ---------------------------------------------------------------------------
# Gate loop
# ---------------------------------------------------------------------------

def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"cap_usd": 8.00, "image_calls": 0, "image_cost": 0.0,
            "validation_calls": 0, "validation_cost": 0.0,
            "video_calls": 0, "video_cost": 0.0, "entries": []}


def save_ledger(led: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=2))


def ledger_total(led: dict) -> float:
    return led["image_cost"] + led["validation_cost"] + led["video_cost"]


PRESENCE_GATE = 0.60


def _identity_failures(d: dict, expected: list[str] | None = None) -> list[str]:
    """Identity-gate failures for one panel.

    Note the two checks that are NOT about a score being low. A frame in which
    the validator finds none of the expected cast produces an EMPTY
    `character_identity` map, and `min()` over nothing is not a failure - so a
    naive "any score below 0.60" gate passes it vacuously. That is not
    hypothetical: on this task an attempt came back as a desert canyon with a
    Roman arch in it, scored `character_presence 0.30, location_match 0.30`,
    and was promoted as shot 1C's end panel because it had no identity scores
    to fail. An anchor frame with the wrong people in it is the exact thing
    #341 measured as worse than no anchor at all, and an anchor frame with NO
    people in it is worse still. So: every expected character must actually
    have been scored, and presence has to clear its own gate.
    """
    agg = d.get("aggregate_scores") or {}
    ident = agg.get("character_identity") or {}
    out: list[str] = []

    failing = {n for n, v in ident.items()
               if isinstance(v, (int, float)) and v < IDENTITY_GATE}
    out += [r for r in d.get("reasons", [])
            if any(r.startswith(f"{n} identity") for n in failing)]

    if expected:
        unscored = [n for n in expected if not isinstance(ident.get(n), (int, float))]
        if unscored:
            out.append(
                "not scored at all - the validator did not find "
                + ", ".join(unscored)
                + " in the frame, so their identity was never checked. Put "
                "every listed character in the frame, clearly visible."
            )
        presence = agg.get("character_presence")
        if isinstance(presence, (int, float)) and presence < PRESENCE_GATE:
            out += [r for r in d.get("reasons", [])
                    if r.startswith("character_presence")] or [
                f"character_presence {presence:.2f}: the wrong people, or no "
                "people, are in this frame."]
    return out


def _notes_from_reasons(reasons: list[str]) -> str:
    if not reasons:
        return ""
    return (
        "The previous attempt was rejected by the automated identity gate for "
        "exactly these reasons. Each one names an attribute, what the locked "
        "turnaround says, and what you drew instead. Fix every one, and LIGHT "
        "the corrected attribute so it is unmistakable at the scale it appears "
        "in frame: " + " | ".join(reasons) +
        " || IMPORTANT: the previous attempt's STAGING and its ACTION were "
        "correct and were NOT the reason it was rejected. Keep the same camera "
        "position and focal length, the same room, the same furniture and "
        "props, the same lighting and the same end-of-shot moment. This is a "
        "targeted retouch of specific character attributes on an otherwise "
        "correct frame. Do not move the camera to fit the correction in."
    )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--max-attempts", type=int, default=2)
    ap.add_argument("--budget", type=float, default=1.20,
                    help="sub-budget for this step, checked against the shared "
                         "ledger's running total")
    ap.add_argument("--model", default=regen.MODEL)
    ap.add_argument("--delay", type=float, default=10.0)
    ap.add_argument("--force-plate", action="store_true",
                    help="attach the ON-MODEL v5 start panel as a plate even on "
                         "the close shots. See the 'plate retry' note in "
                         "docs/research/scene01-v5-render.md: #345's reason for "
                         "dropping the plate was that it was off-model, which "
                         "the v5 start panels are not.")
    ap.add_argument("--suffix", default="",
                    help="attempt-filename suffix, e.g. -p for a plate retry")
    ap.add_argument("--plate-edge", type=int, default=None,
                    help="override the plate downscale. #345's 640px default "
                         "exists to stop an off-model FACE being copied; on a "
                         "shot with no face large in frame a sharper plate is "
                         "safe and holds the staging better.")
    args = ap.parse_args(argv)

    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set", file=sys.stderr)
        return 2

    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    identity_lines = regen.load_identity_lines()

    manifest = json.loads(MANIFEST.read_text())
    wanted = set(args.shots) if args.shots else None
    shots = [s for s in manifest if wanted is None or s["shot_id"] in wanted]

    led = load_ledger()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VAL_DIR.mkdir(parents=True, exist_ok=True)

    summary_path = ROOT / "work/end-summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else []
    summary = [r for r in summary if r["shot_id"] not in {s["shot_id"] for s in shots}]

    step_start = ledger_total(led)
    for shot in shots:
        sid = shot["shot_id"]
        notes = ""
        best = None
        for attempt in range(1, args.max_attempts + 1):
            spent_step = ledger_total(led) - step_start
            if spent_step + IMAGE_COST > args.budget:
                print(f"!! BUDGET STOP before {sid} attempt {attempt} "
                      f"(step spend ${spent_step:.3f} of ${args.budget:.2f})")
                break
            if ledger_total(led) + IMAGE_COST > led["cap_usd"]:
                print(f"!! HARD CAP STOP before {sid} attempt {attempt}")
                break

            cand = OUT_DIR / f"scene-01-{sid}-end{args.suffix}-a{attempt}.png"
            ok = generate_end_panel(
                client, shot, cand, identity_lines, args.model, notes,
                plate_max_edge=(args.plate_edge
                                or PLATE_MAX_EDGE.get(attempt, 448)),
                force_plate=args.force_plate)
            led["image_calls"] += 1
            led["image_cost"] += IMAGE_COST
            led["entries"].append({"kind": "image", "shot": sid,
                                   "attempt": attempt, "usd": IMAGE_COST})
            save_ledger(led)
            if not ok:
                print(f"  [{sid}] attempt {attempt}: generation failed")
                time.sleep(args.delay)
                continue

            res = sv.validate_panel(
                shot=shot, panel_path=cand,
                characters_dir=CHAR_DIR, locations_dir=LOC_DIR,
                keyframes_dir=ROOT / "work/keyframes",
                backend="gemini", model=sv.DEFAULT_GEMINI_MODEL,
                identity_sheet=SHEET,
            )
            d = res.to_dict()
            cost = round(sv.estimate_cost(
                sv.DEFAULT_GEMINI_MODEL, res.usage["input_tokens"],
                res.usage["output_tokens"]), 4)
            d["estimated_cost_usd"] = cost
            d["attempt"] = attempt
            d["panel"] = str(cand.relative_to(ROOT))
            (VAL_DIR / f"{sid}{args.suffix}-a{attempt}.json").write_text(
                json.dumps(d, indent=2))
            led["validation_calls"] += 1
            led["validation_cost"] += cost
            led["entries"].append({"kind": "validate", "shot": sid,
                                   "attempt": attempt, "usd": cost})
            save_ledger(led)

            ident = (d.get("aggregate_scores") or {}).get("character_identity") or {}
            fails = _identity_failures(d, shot.get("characters") or [])
            worst = min([v for v in ident.values()
                         if isinstance(v, (int, float))], default=1.0)
            print(f"  [{sid}] end attempt {attempt}: identity "
                  + (", ".join(f"{k} {v}" for k, v in ident.items())
                     or "n/a (no cast)")
                  + f"  -> {'IDENTITY PASS' if not fails else 'IDENTITY FAIL'}"
                  + f"  overall={'PASS' if d['overall_pass'] else 'FAIL'}")
            for r in fails:
                print(f"      {r}")

            if best is None or worst > best["worst"]:
                best = {"attempt": attempt, "panel": cand, "result": d,
                        "worst": worst, "identity_pass": not fails}
            if not fails:
                break
            notes = _notes_from_reasons(fails)
            time.sleep(args.delay)

        if best is None:
            summary.append({"shot_id": sid, "status": "NO_IMAGE"})
            summary.sort(key=lambda r: r["shot_id"])
            summary_path.write_text(json.dumps(summary, indent=2))
            continue
        final = OUT_DIR / f"scene-01-{sid}-end.png"
        final.write_bytes(best["panel"].read_bytes())
        (VAL_DIR / f"{sid}-final.json").write_text(json.dumps(best["result"], indent=2))
        summary.append({
            "shot_id": sid,
            "status": "IDENTITY_PASS" if best["identity_pass"] else "IDENTITY_FAIL",
            "plated": args.force_plate or sid in PLATED,
            "attempts_used": best["attempt"],
            "overall_pass": best["result"]["overall_pass"],
            "identity": (best["result"]["aggregate_scores"] or {}).get("character_identity"),
            "wardrobe": (best["result"]["aggregate_scores"] or {}).get("character_wardrobe"),
            "reasons": best["result"]["reasons"],
        })
        summary.sort(key=lambda r: r["shot_id"])
        summary_path.write_text(json.dumps(summary, indent=2))
        time.sleep(args.delay)

    print("\n=== END PANEL SUMMARY ===")
    for row in summary:
        print(f"{row['shot_id']}: {row['status']} "
              f"(attempts {row.get('attempts_used')}) "
              f"overall={row.get('overall_pass')}")
    print(f"\nStep spend ${ledger_total(led) - step_start:.3f}; "
          f"running total ${ledger_total(led):.3f} of ${led['cap_usd']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
