#!/usr/bin/env python3
"""Re-score one character out of a panel, cropped and enlarged.

Task 345 §8 found that the identity pass reads an attribute differently
depending on how big the head is in frame: the same Gabe pixels scored 0.40
with `eyewear: heavy_dark_rectangular` inside a two-shot and 1.00 with
`eyewear: thin_wire_rectangular` when cropped out of that same panel and shown
to the same validator. Its recommendation was to check a crop before believing
a small-in-frame identity failure. This is that check, for any character.

It does NOT clear a panel - a panel that fails its gate still fails. It tells
you whether you are looking at a drawing defect (which needs a regeneration) or
a scale artifact (which needs the attribute lit so it survives being small, or
a task on the validator - see #346).

Usage:
  python3 scripts/crop_identity_control.py --panel work/v5-end/scene-01-1C-end-e-a1.png \\
      --character Jenny --box 0.70,0.38,0.90,0.72 --wardrobe "coral zip hoodie, on phone"
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

_vspec = importlib.util.spec_from_file_location(
    "shot_validator", ROOT / "scripts/validate/shot_validator.py")
sv = importlib.util.module_from_spec(_vspec)
sys.modules["shot_validator"] = sv
_vspec.loader.exec_module(sv)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--character", required=True)
    ap.add_argument("--box", required=True,
                    help="x0,y0,x1,y1 as fractions of the panel, 0-1")
    ap.add_argument("--wardrobe", default="")
    ap.add_argument("--location", default="living_room")
    ap.add_argument("--out", default=None)
    ap.add_argument("--min-edge", type=int, default=1024,
                    help="upscale the crop so the head is not tiny again")
    args = ap.parse_args(argv)

    panel = Path(args.panel)
    im = Image.open(panel).convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = (float(v) for v in args.box.split(","))
    crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    if max(crop.size) < args.min_edge:
        s = args.min_edge / float(max(crop.size))
        crop = crop.resize((int(crop.size[0] * s), int(crop.size[1] * s)),
                           Image.LANCZOS)
    out_dir = ROOT / "work/control"
    out_dir.mkdir(parents=True, exist_ok=True)
    crop_path = out_dir / f"{panel.stem}-{args.character.lower()}-crop.png"
    crop.save(crop_path)

    shot = {
        "shot_id": f"CONTROL-{args.character.upper()}",
        "location": args.location,
        "characters": [args.character],
        "wardrobe": ({args.character: args.wardrobe} if args.wardrobe else {}),
        "key_props": [],
        "camera": "Cropped and enlarged from a storyboard panel; single figure.",
    }
    res = sv.validate_panel(
        shot=shot, panel_path=crop_path,
        characters_dir=ROOT / "asset-bible/characters",
        locations_dir=ROOT / "work/locations",
        keyframes_dir=ROOT / "work/keyframes",
        backend="gemini", model=sv.DEFAULT_GEMINI_MODEL,
        identity_sheet=ROOT / "scripts/validate/identity-sheets.json",
    )
    d = res.to_dict()
    d["estimated_cost_usd"] = round(sv.estimate_cost(
        sv.DEFAULT_GEMINI_MODEL, res.usage["input_tokens"],
        res.usage["output_tokens"]), 4)
    d["source_panel"] = str(panel)
    d["crop_box"] = args.box
    d["crop_panel"] = str(crop_path)
    out = Path(args.out) if args.out else (
        out_dir / f"{panel.stem}-{args.character.lower()}-control.json")
    out.write_text(json.dumps(d, indent=2))

    ev = ((d.get("aggregate_scores") or {})
          .get("character_identity_evidence") or {}).get(args.character) or {}
    print("crop:  ", crop_path)
    print("score: ", ev.get("score"), ev.get("verdict"))
    print("frame attributes:    ", json.dumps(ev.get("frame_attributes") or {}))
    print("reference attributes:", json.dumps(ev.get("reference_attributes") or {}))
    print("defining mismatches: ", ev.get("defining_mismatches"))
    print("cost: $%.4f" % d["estimated_cost_usd"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
