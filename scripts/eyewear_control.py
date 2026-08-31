#!/usr/bin/env python3
"""Control: can the validator read Gabe's eyewear off his own locked turnaround?

Task 345 kept failing 1I on one attribute - `eyewear: turnaround
thin_wire_rectangular / frame heavy_dark_rectangular` - while the rendered
glasses look like thin wire rims to a human. The reference side of that
comparison is read from `identity-sheets.json`, so it is right by construction;
only the FRAME side is a vision call. This script points that same vision call
at the locked turnaround itself.

If the validator reads `heavy_dark_rectangular` off the approved reference art,
the gate cannot be passed by any panel drawn in this style, and the failure is
the classifier's, not the panel's.

Usage:
  python3 scripts/eyewear_control.py [--panel work/control/gabe_front_from_turnaround.png]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_vspec = importlib.util.spec_from_file_location(
    "shot_validator", ROOT / "scripts/validate/shot_validator.py")
sv = importlib.util.module_from_spec(_vspec)
sys.modules["shot_validator"] = sv
_vspec.loader.exec_module(sv)

SHOT = {
    "shot_id": "CONTROL-GABE",
    "location": "front_entryway",
    "characters": ["Gabe"],
    "wardrobe": {"Gabe": "green and navy plaid flannel shirt, khaki trousers"},
    "key_props": [],
    "camera": "Full-figure front view of the character on a plain background.",
}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel",
                    default=str(ROOT / "work/control/gabe_front_from_turnaround.png"))
    ap.add_argument("--out", default=str(ROOT / "work/control/gabe-eyewear-control.json"))
    args = ap.parse_args(argv)

    res = sv.validate_panel(
        shot=SHOT, panel_path=Path(args.panel),
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
    d["control_panel"] = args.panel
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(d, indent=2))

    ev = ((d.get("aggregate_scores") or {})
          .get("character_identity_evidence") or {}).get("Gabe") or {}
    print("panel:", args.panel)
    print("score:", ev.get("score"), ev.get("verdict"))
    print("frame eyewear:    ", (ev.get("frame_attributes") or {}).get("eyewear"))
    print("reference eyewear:", (ev.get("reference_attributes") or {}).get("eyewear"))
    print("defining mismatches:", ev.get("defining_mismatches"))
    print("cost: $%.4f" % d["estimated_cost_usd"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
