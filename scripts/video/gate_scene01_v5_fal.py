#!/usr/bin/env python3
"""Gate the rendered Scene 1 v5 clips: identity gate + OpenCV staging gate.

Two independent opinions per clip, because they measure different things and
neither one alone clears a shot:

1. `scripts/validate/shot_validator.py` - extracts first / middle / last
   keyframes and grades each against the LOCKED TURNAROUNDS on
   `gemini-3-flash-preview`. This is the gate that matters here: it is the only
   one that can see that a clip has quietly become a different person, and it
   covers all nine shots.
2. `docs/process/continuity/check_video.py --shot <ID>` - the $0.00 OpenCV
   staging gate from #336/#339, scored against the per-shot plate. It knows
   nothing about faces; it knows whether the furniture is still where the plate
   says it is.

The identity verdict here is the same rule the end panels were held to
(`gen_scene01_end_panels._identity_failures`), including the two non-score
checks: every expected character must actually have been scored, and presence
must clear its own gate. A clip in which the validator finds nobody has not
passed anything.

Usage:
  python3 scripts/video/gate_scene01_v5_fal.py                 # all clips found
  python3 scripts/video/gate_scene01_v5_fal.py 1A 1B
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

_gspec = importlib.util.spec_from_file_location(
    "gen_end", ROOT / "scripts/gen_scene01_end_panels.py")
gen_end = importlib.util.module_from_spec(_gspec)
sys.modules["gen_end"] = gen_end
_gspec.loader.exec_module(gen_end)

sv = gen_end.sv          # already loaded by gen_end

MANIFEST = ROOT / "asset-bible/manifests/scene-01.json"
CLIP_DIR = ROOT / "work/fal"
KEYFRAME_DIR = ROOT / "work/fal/keyframes"
OUT = ROOT / "reports/scene-01-v5-render/shot-gate.json"
CHECK_VIDEO = ROOT / "docs/process/continuity/check_video.py"
LEDGER = ROOT / "reports/scene-01-v5-render/ledger.json"


def _layout_range(staging: dict) -> list | None:
    """min/max of the per-frame layout_match score, the gate's headline number."""
    vals = []
    for f in staging.get("frames") or []:
        for c in (f.get("checks") or []):
            if c.get("name") == "layout_match" and isinstance(c.get("score"), (int, float)):
                vals.append(c["score"])
    if not vals:
        # older/other shapes: a flat score dict per frame
        for f in staging.get("frames") or []:
            v = (f.get("scores") or {}).get("layout_match")
            if isinstance(v, (int, float)):
                vals.append(v)
    return [round(min(vals), 3), round(max(vals), 3)] if vals else None


def staging_gate(clip: Path, sid: str) -> dict:
    """The OpenCV staging gate, as a second opinion. $0.00, no network."""
    proc = subprocess.run(
        [sys.executable, str(CHECK_VIDEO), str(clip), "--shot", sid, "--json"],
        capture_output=True, text=True, cwd=str(CHECK_VIDEO.parent),
    )
    try:
        data = json.loads(proc.stdout)
    except Exception:
        return {"verdict": "ERROR", "exit_code": proc.returncode,
                "stderr": proc.stderr.strip()[:400],
                "stdout": proc.stdout.strip()[:400]}
    data["exit_code"] = proc.returncode
    return data


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--suffix", default="")
    args = ap.parse_args(argv)

    manifest = {s["shot_id"]: s for s in json.loads(MANIFEST.read_text())}
    shots = args.shots or sorted(manifest)
    led = json.loads(LEDGER.read_text())

    rows = []
    for sid in shots:
        clip = CLIP_DIR / f"scene-01-{sid}{args.suffix}.mp4"
        if not clip.exists():
            print(f"{sid}: no clip at {clip}")
            continue
        shot = manifest[sid]

        res = sv.validate_shot(
            shot=shot, media_path=clip,
            characters_dir=ROOT / "asset-bible/characters",
            locations_dir=ROOT / "work/locations",
            keyframes_dir=KEYFRAME_DIR / sid,
            backend="gemini", model=sv.DEFAULT_GEMINI_MODEL,
            identity_sheet=ROOT / "scripts/validate/identity-sheets.json",
        )
        d = res.to_dict()
        cost = round(sv.estimate_cost(
            sv.DEFAULT_GEMINI_MODEL, res.usage["input_tokens"],
            res.usage["output_tokens"]), 4)
        d["estimated_cost_usd"] = cost
        led["validation_calls"] += 1
        led["validation_cost"] += cost
        led["entries"].append({"kind": "validate-shot", "shot": sid + args.suffix,
                               "usd": cost})
        LEDGER.write_text(json.dumps(led, indent=2))

        expected = shot.get("characters") or []
        fails = gen_end._identity_failures(d, expected)
        agg = d.get("aggregate_scores") or {}
        staging = staging_gate(clip, sid)

        row = {
            "shot_id": sid,
            "suffix": args.suffix,
            "clip": clip.name,
            "identity_gate": "PASS" if not fails else "FAIL",
            "identity": agg.get("character_identity"),
            "wardrobe": agg.get("character_wardrobe"),
            "presence": agg.get("character_presence"),
            "continuity": agg.get("continuity"),
            "location_match": agg.get("location_match"),
            "artifacts": agg.get("artifacts"),
            "overall_pass": d.get("overall_pass"),
            "identity_failures": fails,
            "reasons": d.get("reasons", []),
            "staging_gate": staging.get("verdict"),
            "staging_frames_scored": staging.get("frames_scored"),
            "staging_frames_failed": staging.get("frames_failed"),
            "staging_failing_checks": staging.get("failing_checks"),
            "staging_applied_checks": staging.get("applied_checks"),
            "staging_skipped_checks": staging.get("skipped_checks"),
            "staging_layout": _layout_range(staging),
            "staging_inconclusive_reason": staging.get("inconclusive_reason"),
            "validation_cost_usd": cost,
        }
        rows.append(row)
        (ROOT / "reports/scene-01-v5-render/shots").mkdir(parents=True, exist_ok=True)
        (ROOT / f"reports/scene-01-v5-render/shots/{sid}{args.suffix}.json"
         ).write_text(json.dumps(d, indent=2))

        print(f"{sid}: identity {row['identity_gate']} "
              f"{json.dumps(row['identity'])}  overall="
              f"{'PASS' if row['overall_pass'] else 'FAIL'}  "
              f"staging={row['staging_gate']}")
        for f in fails:
            print(f"    identity: {f}")
        for r in d.get("reasons", []):
            if not any(f in r for f in fails):
                print(f"    {r}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(OUT.read_text()) if OUT.exists() else []
    by_id = {r["shot_id"] + r.get("suffix", ""): r for r in existing}
    for r in rows:
        by_id[r["shot_id"] + r.get("suffix", "")] = r
    OUT.write_text(json.dumps([by_id[k] for k in sorted(by_id)], indent=2))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
