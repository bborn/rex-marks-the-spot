#!/usr/bin/env python3
"""Build the Scene 2 restage v4 comparison sheet.

Puts the rejected v3 broadside plate next to the three v4 variations so Bruno
can read the door assignment in all four at a glance.  The v3 panel is the
control: it is the one where the two handles sit at the same pillar and Nina's
hand lands between them.

    .venv/bin/python scripts/factory/build_s2_restage_v4_sheet.py
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
FACTORY_PLAN = Path(os.environ.get("FACTORY_PLAN", Path.home() / "factory-plan"))
FACTORY_UPLOAD = Path(os.environ.get("FACTORY_UPLOAD", Path.home() / "factory-upload"))
OUT_DIR = REPO_ROOT / "renders" / "factory" / "s2" / "restage-v4"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
BG = (18, 20, 26)
FG = (238, 238, 240)
DIM = (150, 154, 166)
BAD = (226, 96, 88)
GOOD = (118, 200, 138)
WARN = (222, 178, 88)

PANEL_W = 860
PAD = 36
GAP = 26
COLS = 2

PANELS = [
    (
        FACTORY_UPLOAD / "s2" / "s2-restage-broadside.png",
        "v3 BROADSIDE - REJECTED (control)",
        BAD,
        [
            "Sliding-door handle and front-door handle sit inches",
            "apart at the B-pillar. Nina's hand is between them.",
            "t3: she opened one door and entered the other; Gabe",
            "climbed in behind her through the same sliding door.",
        ],
    ),
    (
        OUT_DIR / "s2-restage-overthenose-a2.png",
        "v4-B  OVER THE NOSE  (recommended)",
        GOOD,
        [
            "Nina -> front passenger door, hand closed on that handle.",
            "Gabe -> driver's door, foreground, rounding the grille.",
            "Exactly ONE door handle on the van in the whole frame.",
            "Rear of the van cropped out. No sliding door at all.",
        ],
    ),
    (
        OUT_DIR / "s2-restage-noseleft-a2.png",
        "v4-A  NOSE CAMERA-LEFT",
        GOOD,
        [
            "Nina -> front passenger door, hand on the front door",
            "panel by the wing mirror, clutch in her other hand.",
            "Gabe -> driver's door, out at the nose, whole van",
            "between them. Sliding handle a body-width behind her.",
        ],
    ),
    (
        OUT_DIR / "s2-restage-highwide-a3.png",
        "v4-C  RAISED WIDE",
        WARN,
        [
            "Nina -> front passenger door, fingers wrapped on that",
            "handle, forward of the B-pillar. Gabe -> driver's door,",
            "at the nose, hand on the bonnet, swinging around it.",
            "CAVEAT: sliding handle still close behind her hand.",
        ],
    ),
]


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def main() -> int:
    title_f = _font("DejaVuSans-Bold.ttf", 34)
    sub_f = _font("DejaVuSans.ttf", 21)
    label_f = _font("DejaVuSans-Bold.ttf", 25)
    body_f = _font("DejaVuSans.ttf", 19)

    shots = []
    for path, label, colour, lines in PANELS:
        if not path.exists():
            raise SystemExit(f"missing panel: {path}")
        im = Image.open(path).convert("RGB")
        h = round(PANEL_W * im.height / im.width)
        shots.append((im.resize((PANEL_W, h), Image.LANCZOS), label, colour, lines))

    img_h = max(s[0].height for s in shots)
    caption_h = 44 + max(len(p[3]) for p in PANELS) * 28
    cell_h = img_h + caption_h + GAP
    head_h = 148
    rows = (len(shots) + COLS - 1) // COLS
    sheet_w = PAD * 2 + PANEL_W * COLS + GAP * (COLS - 1)
    sheet_h = head_h + cell_h * rows + PAD

    sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
    d = ImageDraw.Draw(sheet)
    d.text(
        (PAD, 28),
        "SCENE 2 - EXT. HOUSE, NIGHT: restage v4, each adult at their OWN front door",
        font=title_f,
        fill=FG,
    )
    d.text(
        (PAD, 74),
        "Gabe drives, Nina rides shotgun. The sliding door is the kids' door and is "
        "out of this shot.",
        font=sub_f,
        fill=DIM,
    )
    d.text(
        (PAD, 104),
        "The three v4 frames differ only in van angle and camera position. "
        "The door assignment is identical in all three.",
        font=sub_f,
        fill=DIM,
    )

    for i, (im, label, colour, lines) in enumerate(shots):
        col, row = i % COLS, i // COLS
        x = PAD + col * (PANEL_W + GAP)
        y = head_h + row * cell_h
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + PANEL_W - 1, y + im.height - 1], outline=colour, width=3)
        cy = y + im.height + 12
        d.text((x, cy), label, font=label_f, fill=colour)
        for j, line in enumerate(lines):
            d.text((x, cy + 36 + j * 28), line, font=body_f, fill=DIM)

    out = OUT_DIR / "s2-restage-v4-compare.png"
    sheet.save(out)
    print(f"{out}  {sheet.size[0]}x{sheet.size[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
