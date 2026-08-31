#!/usr/bin/env python3
"""Generate → validate → retry loop for the Scene 1 v5 panel set.

For each shot: generate a panel with regen_scene01_v5, run the repaired
identity validator against the locked identity sheet, and if the IDENTITY gate
fails, feed the validator's own failure reasons back into the next attempt as
corrections. Hard cap of 3 attempts per panel, then move on and report it.

The identity gate is the one that decides done-ness here (that is the task):
`overall_pass` is recorded too, because it also folds in presence / wardrobe /
location / artifacts, but a location or artifact wobble does not send a panel
back through image generation.

Usage:
  python3 scripts/run_scene01_v5_gate.py                 # all 9
  python3 scripts/run_scene01_v5_gate.py 1A 1D           # subset
  python3 scripts/run_scene01_v5_gate.py --max-attempts 3 --budget 4.00
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

_vspec = importlib.util.spec_from_file_location("shot_validator", ROOT / "scripts/validate/shot_validator.py")
sv = importlib.util.module_from_spec(_vspec)
sys.modules["shot_validator"] = sv
_vspec.loader.exec_module(sv)

MANIFEST = ROOT / "asset-bible/manifests/scene-01.json"
CHAR_DIR = ROOT / "asset-bible/characters"
LOC_DIR = ROOT / "work/locations"
OUT_DIR = ROOT / "work/v5"
VAL_DIR = ROOT / "work/val"
SHEET = ROOT / "scripts/validate/identity-sheets.json"
LEDGER = ROOT / "work/ledger.json"

IMAGE_COST = 0.04      # gemini-3-pro-image-preview, per generated image
IDENTITY_GATE = 0.60


def _load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"image_calls": 0, "image_cost": 0.0, "validation_cost": 0.0, "runs": []}


def _save_ledger(led: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=2))


def _identity_failures(result_dict: dict) -> list[str]:
    """Return the validator's own reason strings for identity failures only."""
    ident = (result_dict.get("aggregate_scores") or {}).get("character_identity") or {}
    failing = {n for n, v in ident.items() if isinstance(v, (int, float)) and v < IDENTITY_GATE}
    if not failing:
        return []
    return [r for r in result_dict.get("reasons", [])
            if any(r.startswith(f"{n} identity") for n in failing)]


def _notes_from_reasons(reasons: list[str]) -> str:
    if not reasons:
        return ""
    return (
        "The previous attempt was rejected by the automated identity gate for "
        "exactly these reasons. Each one names an attribute, what the locked "
        "turnaround says, and what you drew instead. Fix every one, and make "
        "the corrected attribute unmistakable at the scale it appears in frame: "
        + " | ".join(reasons)
        + " || IMPORTANT: the previous attempt's STAGING was correct and was NOT "
        "the reason it was rejected. Reproduce the staging reference frame as "
        "closely as before - same camera position and focal length, same "
        "distance to the couch, same furniture, same background room, same "
        "props in the same places, same lighting. This is a targeted retouch of "
        "specific character attributes on an otherwise-approved frame, not a "
        "new take on the shot. Do not move the camera to fit the correction in."
    )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--budget", type=float, default=4.00)
    ap.add_argument("--model", default=regen.MODEL)
    ap.add_argument("--delay", type=float, default=10.0)
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

    led = _load_ledger()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VAL_DIR.mkdir(parents=True, exist_ok=True)

    summary_path = ROOT / "work/summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else []
    summary = [r for r in summary if r["shot_id"] not in {s["shot_id"] for s in shots}]
    for shot in shots:
        sid = shot["shot_id"]
        notes = ""
        best = None
        for attempt in range(1, args.max_attempts + 1):
            spent = led["image_cost"] + led["validation_cost"]
            if spent + IMAGE_COST > args.budget:
                print(f"!! BUDGET STOP before {sid} attempt {attempt} "
                      f"(spent ${spent:.3f} of ${args.budget:.2f})")
                break

            cand = OUT_DIR / f"scene-01-{sid}-start-a{attempt}.png"
            # Escalate on retry: shrink the staging reference further so its
            # off-model faces lose even more of their pull, while the layout
            # (low-frequency) survives.
            staging_edge = {1: 640, 2: 512, 3: 416}.get(attempt, 416)
            ok = regen.generate_panel(client, shot, cand, identity_lines,
                                      args.model, notes,
                                      staging_max_edge=staging_edge)
            led["image_calls"] += 1
            led["image_cost"] += IMAGE_COST
            _save_ledger(led)
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
            d["estimated_cost_usd"] = round(sv.estimate_cost(
                sv.DEFAULT_GEMINI_MODEL, res.usage["input_tokens"],
                res.usage["output_tokens"]), 4)
            d["attempt"] = attempt
            d["panel"] = str(cand.relative_to(ROOT))
            (VAL_DIR / f"{sid}-a{attempt}.json").write_text(json.dumps(d, indent=2))
            led["validation_cost"] += d["estimated_cost_usd"]
            _save_ledger(led)

            ident = (d.get("aggregate_scores") or {}).get("character_identity") or {}
            fails = _identity_failures(d)
            worst = min([v for v in ident.values() if isinstance(v, (int, float))], default=1.0)
            print(f"  [{sid}] attempt {attempt}: identity "
                  + (", ".join(f"{k} {v}" for k, v in ident.items()) or "n/a (no cast)")
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
            summary.append({"shot_id": sid, "status": "NO_IMAGE", "attempts": args.max_attempts})
            continue
        final = OUT_DIR / f"scene-01-{sid}-start.png"
        final.write_bytes(best["panel"].read_bytes())
        (VAL_DIR / f"{sid}-final.json").write_text(json.dumps(best["result"], indent=2))
        summary.append({
            "shot_id": sid,
            "status": "IDENTITY_PASS" if best["identity_pass"] else "IDENTITY_FAIL",
            "attempts_used": best["attempt"],
            "chosen_attempt": best["attempt"],
            "overall_pass": best["result"]["overall_pass"],
            "identity": (best["result"]["aggregate_scores"] or {}).get("character_identity"),
            "wardrobe": (best["result"]["aggregate_scores"] or {}).get("character_wardrobe"),
            "reasons": best["result"]["reasons"],
        })
        summary.sort(key=lambda r: r["shot_id"])
        summary_path.write_text(json.dumps(summary, indent=2))
        time.sleep(args.delay)

    led["runs"].append({"shots": [s["shot_id"] for s in shots]})
    _save_ledger(led)
    print("\n=== SUMMARY ===")
    for row in summary:
        print(f"{row['shot_id']}: {row['status']} "
              f"(attempts {row.get('attempts_used')}) overall={row.get('overall_pass')}")
    print(f"\nSpend: images ${led['image_cost']:.3f} + validation "
          f"${led['validation_cost']:.4f} = ${led['image_cost']+led['validation_cost']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
