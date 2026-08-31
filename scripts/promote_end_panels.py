#!/usr/bin/env python3
"""Promote one chosen end-panel attempt per shot, re-checking its gate first.

`gen_scene01_end_panels.py` promotes the best attempt OF ITS OWN RUN. Across
several runs that is the wrong rule - a later run aimed at a staging problem can
promote a worse identity score over a good earlier one, which is exactly what
happened to 1D here. This makes the choice explicit and re-derives the summary
from the chosen attempt's own validator JSON, so the reported numbers are the
numbers of the file that shipped.

It REFUSES to promote an attempt that does not pass the identity gate, including
the two non-score checks in `_identity_failures` (every expected character
actually scored, and presence above its own gate).

Usage:
  python3 scripts/promote_end_panels.py                 # use CHOSEN below
  python3 scripts/promote_end_panels.py --check-only
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "gen_end", ROOT / "scripts/gen_scene01_end_panels.py")
gen = importlib.util.module_from_spec(_spec)
sys.modules["gen_end"] = gen
_spec.loader.exec_module(gen)

OUT_DIR = ROOT / "work/v5-end"
VAL_DIR = ROOT / "work/val-end"
MANIFEST = ROOT / "asset-bible/manifests/scene-01.json"

# shot -> attempt tag.  The tag is the part between "-end" and ".png" in the
# candidate filename: "-a1", "-d-a1", "-plate-a1" and so on.  Why each one:
#
#   1A  a1        first pass, plated; clean pair, no retry needed
#   1B  a1        first pass, plateless; clean pair
#   1C  f-a2      the only 1C attempt where Nina, Gabe AND Jenny all clear
#   1D  d-a1      the run that held the 3D style; the later -g attempt aimed at
#                 Nina's sleeves and lost Gabe and Leo, so it is not promoted
#   1E  plate-a1  plateless kept mirroring her; the on-model plate fixed it
#   1F  a1        first pass, plated, no cast
#   1G  d-a2      the sharper-plate run, after the end action was corrected to
#                 "the kids have turned BACK to the TV"
#   1H  d-a1      the run with the ponytail and framing notes
#   1I  a2        second attempt of the first pass, plateless
CHOSEN = {
    "1A": "a1",
    "1B": "a1",
    "1C": "f-a2",
    "1D": "d-a1",
    "1E": "plate-a1",
    "1F": "a1",
    "1G": "d-a2",
    "1H": "d-a1",
    "1I": "a2",
}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args(argv)

    manifest = {s["shot_id"]: s for s in json.loads(MANIFEST.read_text())}
    summary, bad = [], []
    for sid, tag in CHOSEN.items():
        panel = OUT_DIR / f"scene-01-{sid}-end-{tag}.png"
        vjson = VAL_DIR / f"{sid}-{tag}.json"
        if not panel.exists() or not vjson.exists():
            bad.append(f"{sid}: missing {panel.name} or {vjson.name}")
            continue
        d = json.loads(vjson.read_text())
        expected = manifest[sid].get("characters") or []
        fails = gen._identity_failures(d, expected)
        agg = d.get("aggregate_scores") or {}
        row = {
            "shot_id": sid,
            "attempt_tag": tag,
            "panel": panel.name,
            "plated": sid in gen.PLATED or tag.startswith("plate"),
            "identity_gate": "PASS" if not fails else "FAIL",
            "identity": agg.get("character_identity"),
            "wardrobe": agg.get("character_wardrobe"),
            "presence": agg.get("character_presence"),
            "location_match": agg.get("location_match"),
            "artifacts": agg.get("artifacts"),
            "overall_pass": d.get("overall_pass"),
            "reasons": d.get("reasons", []),
        }
        summary.append(row)
        print(f"{sid}: identity {row['identity_gate']}  "
              f"{json.dumps(row['identity'])}  overall={row['overall_pass']}")
        if fails:
            bad.append(f"{sid}: " + "; ".join(fails))
            for f in fails:
                print(f"    {f}")

    if bad:
        print("\nREFUSING TO PROMOTE - these do not pass the identity gate:")
        for b in bad:
            print("  " + b)
        return 1
    if args.check_only:
        print("\nall chosen attempts pass the identity gate (nothing written)")
        return 0

    for row in summary:
        src = OUT_DIR / row["panel"]
        (OUT_DIR / f"scene-01-{row['shot_id']}-end.png").write_bytes(src.read_bytes())
        (VAL_DIR / f"{row['shot_id']}-final.json").write_text(
            (VAL_DIR / f"{row['shot_id']}-{row['attempt_tag']}.json").read_text())
    summary.sort(key=lambda r: r["shot_id"])
    out = ROOT / "reports/scene-01-v5-render/end-panels.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print(f"\npromoted {len(summary)} end panels; summary -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
