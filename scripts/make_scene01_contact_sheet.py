#!/usr/bin/env python3
"""Build a v4-vs-v5 side-by-side contact sheet for Scene 1.

One row per shot: v4 panel on the left, v5 panel on the right, with the
shot id, the shot's cast, and each version's worst identity score printed
between them. Nine rows, one image, so the difference is readable without
opening eighteen files.

Usage:
  python3 scripts/make_scene01_contact_sheet.py --out work/scene-01-v4-vs-v5.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ["1A", "1B", "1C", "1D", "1E", "1F", "1G", "1H", "1I"]

CELL_W = 720
GUTTER = 24
HEADER_H = 110
LABEL_H = 84
MARGIN = 28


def _font(size: int, bold: bool = False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""),
        "/usr/share/fonts/truetype/liberation/LiberationSans%s.ttf" % ("-Bold" if bold else "-Regular"),
    ]
    for n in names:
        if Path(n).exists():
            return ImageFont.truetype(n, size)
    return ImageFont.load_default()


def _fit(path: Path, w: int) -> Image.Image:
    im = Image.open(path).convert("RGB")
    h = int(im.height * (w / im.width))
    return im.resize((w, h), Image.LANCZOS)


def _scores(path: Path) -> tuple[str, str]:
    """Return (headline, detail) for a validation json."""
    if not path.exists():
        return ("no validation on record", "")
    d = json.loads(path.read_text())
    ident = (d.get("aggregate_scores") or {}).get("character_identity") or {}
    nums = [v for v in ident.values() if isinstance(v, (int, float))]
    if not nums:
        return ("no cast in shot", "gate: %s" % ("PASS" if d.get("overall_pass") else "FAIL"))
    worst = min(nums)
    verdict = "IDENTITY PASS" if worst >= 0.60 else "IDENTITY FAIL"
    detail = "  ".join(f"{k} {v:.2f}" for k, v in ident.items())
    return (f"{verdict}   worst {worst:.2f}", detail)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v4-dir", default="work/v4")
    ap.add_argument("--v5-dir", default="work/v5")
    ap.add_argument("--v4-val-dir", default="work/val-v4")
    ap.add_argument("--v5-val-dir", default="work/val")
    ap.add_argument("--out", default="work/scene-01-v4-vs-v5.png")
    a = ap.parse_args()

    v4d, v5d = ROOT / a.v4_dir, ROOT / a.v5_dir
    rows = []
    for sid in SHOTS:
        p4 = v4d / f"scene-01-{sid}-start.png"
        p5 = v5d / f"scene-01-{sid}-start.png"
        i4 = _fit(p4, CELL_W) if p4.exists() else None
        i5 = _fit(p5, CELL_W) if p5.exists() else None
        h = max([im.height for im in (i4, i5) if im] or [400])
        rows.append((sid, i4, i5, h))

    total_w = MARGIN * 2 + CELL_W * 2 + GUTTER
    total_h = HEADER_H + sum(h + LABEL_H + GUTTER for _, _, _, h in rows) + MARGIN

    sheet = Image.new("RGB", (total_w, total_h), (18, 18, 22))
    d = ImageDraw.Draw(sheet)
    f_title, f_head, f_lab, f_small = _font(34, True), _font(22, True), _font(20, True), _font(16)

    d.text((MARGIN, 24), "Scene 1 storyboard panels - v4 (rejected) vs v5 (regenerated on-model)",
           font=f_title, fill=(240, 240, 245))
    d.text((MARGIN, 68),
           "Identity scored by scripts/validate/shot_validator.py (gemini-3-flash-preview) "
           "against scripts/validate/identity-sheets.json. Gate = 0.60.",
           font=f_small, fill=(150, 150, 160))

    y = HEADER_H
    for sid, i4, i5, h in rows:
        x4, x5 = MARGIN, MARGIN + CELL_W + GUTTER
        d.text((x4, y), f"{sid}  -  v4", font=f_head, fill=(230, 120, 120))
        d.text((x5, y), f"{sid}  -  v5", font=f_head, fill=(120, 210, 150))
        head4, det4 = _scores(ROOT / a.v4_val_dir / f"{sid}.json")
        head5, det5 = _scores(ROOT / a.v5_val_dir / f"{sid}-final.json")
        d.text((x4, y + 28), head4, font=f_lab, fill=(230, 150, 150))
        d.text((x4, y + 52), det4, font=f_small, fill=(160, 160, 168))
        d.text((x5, y + 28), head5, font=f_lab, fill=(150, 220, 175))
        d.text((x5, y + 52), det5, font=f_small, fill=(160, 160, 168))
        yy = y + LABEL_H
        if i4:
            sheet.paste(i4, (x4, yy))
        if i5:
            sheet.paste(i5, (x5, yy))
        y = yy + h + GUTTER

    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"wrote {out} ({sheet.width}x{sheet.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
