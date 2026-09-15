#!/usr/bin/env python3
"""Build the Scene 2 restage comparison sheet.

Puts the rejected plate and the two restage options side by side at the same
height so Bruno can read all three van stagings at a glance, and pick one.

    .venv/bin/python scripts/factory/build_s2_restage_sheet.py
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
FACTORY_PLAN = Path(os.environ.get("FACTORY_PLAN", Path.home() / "factory-plan"))
OUT_DIR = REPO_ROOT / "renders" / "factory" / "s2" / "restage-v3"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
BG = (18, 20, 26)
FG = (238, 238, 240)
DIM = (150, 154, 166)
BAD = (226, 96, 88)
GOOD = (118, 200, 138)

PANEL_W = 900
PAD = 36
GAP = 28

PANELS = [
    (
        FACTORY_PLAN / "omni" / "s2" / "s2-restage-t2.png",
        "CURRENT PLATE - REJECTED",
        BAD,
        [
            "Van shows its rear quarter to the approach.",
            "Nearest feature on that surface is the TAIL LIGHT.",
            "Omni take: Gabe grabs the tail light, then vanishes.",
        ],
    ),
    (
        OUT_DIR / "s2-restage-broadside.png",
        "OPTION A - BROADSIDE",
        GOOD,
        [
            "Van parallel to the driveway, full flank to camera.",
            "Sliding door + front door, both handles readable.",
            "Nina's run line ends on the sliding door handle.",
        ],
    ),
    (
        OUT_DIR / "s2-restage-nosein.png",
        "OPTION B - NOSE-IN",
        GOOD,
        [
            "Van angled, front three-quarter to the approach.",
            "Front passenger door AND sliding door both presented.",
            "Two adjacent handles at the end of the run.",
        ],
    ),
]


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def main() -> int:
    title_f = _font("DejaVuSans-Bold.ttf", 34)
    sub_f = _font("DejaVuSans.ttf", 21)
    label_f = _font("DejaVuSans-Bold.ttf", 26)
    body_f = _font("DejaVuSans.ttf", 20)

    shots = []
    for path, label, colour, lines in PANELS:
        if not path.exists():
            raise SystemExit(f"missing panel: {path}")
        im = Image.open(path).convert("RGB")
        h = round(PANEL_W * im.height / im.width)
        shots.append((im.resize((PANEL_W, h), Image.LANCZOS), label, colour, lines))

    img_h = max(s[0].height for s in shots)
    caption_h = 46 + len(PANELS[0][3]) * 30
    head_h = 130
    sheet_w = PAD * 2 + PANEL_W * 3 + GAP * 2
    sheet_h = head_h + img_h + caption_h + PAD

    sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
    d = ImageDraw.Draw(sheet)
    d.text((PAD, 30), "SCENE 2 - EXT. HOUSE, NIGHT: van restage v3", font=title_f, fill=FG)
    d.text(
        (PAD, 76),
        "One change only: where the van sits and which way it faces. "
        "House, storm, wardrobe, faces and Pixar look are held.",
        font=sub_f,
        fill=DIM,
    )

    for i, (im, label, colour, lines) in enumerate(shots):
        x = PAD + i * (PANEL_W + GAP)
        sheet.paste(im, (x, head_h))
        d.rectangle(
            [x, head_h, x + PANEL_W - 1, head_h + im.height - 1],
            outline=colour,
            width=3,
        )
        y = head_h + im.height + 14
        d.text((x, y), label, font=label_f, fill=colour)
        for j, line in enumerate(lines):
            d.text((x, y + 38 + j * 30), line, font=body_f, fill=DIM)

    out = OUT_DIR / "s2-restage-v3-compare.png"
    sheet.save(out)
    print(f"{out}  {sheet.size[0]}x{sheet.size[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
