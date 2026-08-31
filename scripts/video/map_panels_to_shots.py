#!/usr/bin/env python3
"""Score storyboard panels against every Scene 1 shot's plate.

Written for task #341, which had to work out which `scene-01-panel-NN-*.png`
belongs to which shot id rather than assume `panel-01` is `1A`.  The mapping
turned out to be sequential (01->1A ... 09->1I), confirmed independently by
`scripts/generate_scene01_all_panels.py`'s own `desc` strings and by
`storyboards/act1/scene-01-home-evening.md`.

What this script adds is the second half of that question: not "which shot is
this panel" but "would this panel clear that shot's gate".  It puts every named
image through every shot's entry in `scene-01-plate.json` and prints the layout
scores as a matrix, which is how #341 established that the `panel-NN` pairs are
the March pre-lock set and cannot be used as a production `<LAST_FRAME>`.

Free - OpenCV only, no network, no spend.

    python scripts/video/map_panels_to_shots.py work/panels/scene-01-panel-0*.png
    python scripts/video/map_panels_to_shots.py --json out.json panels/*.png
"""

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONT = ROOT / "docs/process/continuity"
SHOTS = ["1A", "1B", "1C", "1D", "1E", "1F", "1G", "1H", "1I"]


def _python() -> str:
    """Prefer the project venv, fall back to whatever is running this."""
    venv = ROOT / ".venv/bin/python"
    return str(venv) if venv.exists() else sys.executable


def score(image: pathlib.Path, shot: str) -> dict:
    proc = subprocess.run(
        [_python(), "check.py", str(image.resolve()), "--shot", shot,
         "--json", "--allow-inconclusive"],
        cwd=CONT, capture_output=True, text=True)
    if proc.returncode not in (0, 1) or not proc.stdout:
        raise SystemExit(f"check.py failed on {image} --shot {shot}:\n{proc.stderr}")
    d = json.loads(proc.stdout)
    lm = next((c for c in d["checks"] if c["name"] == "layout_match"), None)
    return {
        "layout": lm.get("score") if lm else None,
        "verdict": "PASS" if d["passed"] else ("FAIL" if d["conclusive"]
                                               else "INCONCLUSIVE"),
        "failed_checks": d.get("failed_checks") or [],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("--json", help="also write the raw scores here")
    args = ap.parse_args()

    rows = {}
    for p in args.images:
        img = pathlib.Path(p)
        rows[img.stem.replace("scene-01-", "")] = {s: score(img, s) for s in SHOTS}

    hdr = "image".ljust(18) + "".join(s.rjust(8) for s in SHOTS) + "   best plate"
    print(hdr)
    print("-" * len(hdr))
    for name, r in rows.items():
        best = max(SHOTS, key=lambda s: (r[s]["layout"] or -1))
        cells = "".join((f"{r[s]['layout']:.3f}" if r[s]["layout"] is not None
                         else "  -  ").rjust(8) for s in SHOTS)
        print(name.ljust(18) + cells + f"   {best} ({r[best]['verdict']})")

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(rows, indent=2))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
