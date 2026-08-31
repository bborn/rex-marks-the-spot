#!/usr/bin/env python3
"""Rebuild Scene 1 panel 1I without the v4 staging plate (task 345).

1I failed the identity gate three times in task 344, identically, on Gabe's
eyewear: the v4 plate shows heavy black frames at large scale, and in a close
two-shot the downscale that defeats that anchor in a wide shot does not defeat
it. This run drops the plate entirely: the only images the generator sees are
the locked turnarounds, and the staging travels as prose
(`regen_scene01_v5.PLATELESS_STAGING`).

Same gate as 344 - `scripts/validate/shot_validator.py` on
`gemini-3-flash-preview`, scored against `scripts/validate/identity-sheets.json`.

Usage:
  python3 scripts/run_1I_plateless.py --max-attempts 4 --budget 1.00
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

MANIFEST = ROOT / "asset-bible/manifests/scene-01.json"
CHAR_DIR = ROOT / "asset-bible/characters"
LOC_DIR = ROOT / "work/locations"
OUT_DIR = ROOT / "work/v5-1I"
VAL_DIR = ROOT / "work/val-1I"
SHEET = ROOT / "scripts/validate/identity-sheets.json"
LEDGER = ROOT / "work/ledger-1I.json"

IMAGE_COST = 0.04      # gemini-3-pro-image-preview, per generated image
IDENTITY_GATE = 0.60


def _load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"image_calls": 0, "image_cost": 0.0, "validation_calls": 0,
            "validation_cost": 0.0, "attempts": []}


def _save_ledger(led: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=2))


def _identity_failures(d: dict) -> list[str]:
    ident = (d.get("aggregate_scores") or {}).get("character_identity") or {}
    failing = {n for n, v in ident.items()
               if isinstance(v, (int, float)) and v < IDENTITY_GATE}
    if not failing:
        return []
    return [r for r in d.get("reasons", [])
            if any(r.startswith(f"{n} identity") for n in failing)]


def _notes_from_reasons(reasons: list[str]) -> str:
    """Retry note for the plateless path.

    Deliberately different from run_scene01_v5_gate's: there is no staging plate
    to reproduce, so the note must protect the *described* staging instead of a
    picture, or the model re-blocks the shot to make room for the correction.
    """
    if not reasons:
        return ""
    return (
        "The previous attempt was rejected by the automated identity gate for "
        "exactly these reasons. Each names an attribute, what the locked "
        "turnaround says, and what you drew instead. Fix every one and make the "
        "corrected attribute unmistakable at the scale it appears in frame: "
        + " | ".join(reasons)
        + " || Look again at the attached turnaround and copy the eyewear off it "
        "literally: hairline metal wire rims you can see skin through, not a "
        "moulded frame. || The STAGING was NOT the reason for the rejection. "
        "Rebuild the same frame described in STAGING above - same camera height "
        "and distance, both people full-length, same positions, same set "
        "dressing, same light. This is a targeted correction to one character's "
        "face, not a new take on the shot."
    )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", default="1I")
    ap.add_argument("--max-attempts", type=int, default=4)
    ap.add_argument("--start-attempt", type=int, default=1,
                    help="resume the loop at this attempt number, seeding the "
                         "retry note and the best-so-far from the attempt "
                         "before it. Lets the run be stopped to look at the "
                         "pixels without losing the ledger or the retry chain.")
    ap.add_argument("--budget", type=float, default=1.00)
    ap.add_argument("--model", default=regen.MODEL)
    ap.add_argument("--delay", type=float, default=10.0)
    ap.add_argument("--extra-notes", default="",
                    help="appended to the generated retry note")
    args = ap.parse_args(argv)

    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set", file=sys.stderr)
        return 2

    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    identity_lines = regen.load_identity_lines()

    manifest = json.loads(MANIFEST.read_text())
    shot = next(s for s in manifest if s["shot_id"] == args.shot)
    sid = shot["shot_id"]

    led = _load_ledger()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VAL_DIR.mkdir(parents=True, exist_ok=True)

    notes = ""
    best = None
    for prev in range(1, args.start_attempt):
        pj = VAL_DIR / f"{sid}-p{prev}.json"
        if not pj.exists():
            continue
        d = json.loads(pj.read_text())
        ident = (d.get("aggregate_scores") or {}).get("character_identity") or {}
        fails = _identity_failures(d)
        worst = min([v for v in ident.values() if isinstance(v, (int, float))],
                    default=1.0)
        if best is None or worst > best["worst"]:
            best = {"attempt": prev, "panel": OUT_DIR / f"scene-01-{sid}-start-p{prev}.png",
                    "result": d, "worst": worst, "identity_pass": not fails}
        notes = (_notes_from_reasons(fails) + " " + args.extra_notes).strip()
    if args.start_attempt > 1:
        print(f"resuming at attempt {args.start_attempt}; "
              f"best so far = attempt {best['attempt'] if best else None}")

    for attempt in range(args.start_attempt, args.max_attempts + 1):
        spent = led["image_cost"] + led["validation_cost"]
        if spent + IMAGE_COST > args.budget:
            print(f"!! BUDGET STOP before attempt {attempt} "
                  f"(spent ${spent:.3f} of ${args.budget:.2f})")
            break

        cand = OUT_DIR / f"scene-01-{sid}-start-p{attempt}.png"
        ok = regen.generate_panel(client, shot, cand, identity_lines,
                                  args.model, notes, use_staging_plate=False)
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
        d["staging_plate"] = False
        d["panel"] = str(cand.relative_to(ROOT))
        (VAL_DIR / f"{sid}-p{attempt}.json").write_text(json.dumps(d, indent=2))
        led["validation_calls"] += 1
        led["validation_cost"] += d["estimated_cost_usd"]

        ident = (d.get("aggregate_scores") or {}).get("character_identity") or {}
        fails = _identity_failures(d)
        worst = min([v for v in ident.values() if isinstance(v, (int, float))],
                    default=1.0)
        led["attempts"].append({"attempt": attempt, "identity": ident,
                                "identity_pass": not fails,
                                "overall_pass": d["overall_pass"]})
        _save_ledger(led)

        print(f"  [{sid}] attempt {attempt}: identity "
              + ", ".join(f"{k} {v}" for k, v in ident.items())
              + f"  -> {'IDENTITY PASS' if not fails else 'IDENTITY FAIL'}"
              + f"  overall={'PASS' if d['overall_pass'] else 'FAIL'}")
        for r in fails:
            print(f"      {r}")

        if best is None or worst > best["worst"]:
            best = {"attempt": attempt, "panel": cand, "result": d,
                    "worst": worst, "identity_pass": not fails}
        if not fails:
            break
        notes = (_notes_from_reasons(fails) + " " + args.extra_notes).strip()
        time.sleep(args.delay)

    if best is None:
        print("NO_IMAGE")
        return 1
    final = OUT_DIR / f"scene-01-{sid}-start.png"
    final.write_bytes(best["panel"].read_bytes())
    (VAL_DIR / f"{sid}-final.json").write_text(json.dumps(best["result"], indent=2))
    print(f"\nchosen attempt {best['attempt']} -> {final}")
    print(f"identity gate: {'PASS' if best['identity_pass'] else 'FAIL'}")
    print(f"Spend: images ${led['image_cost']:.3f} + validation "
          f"${led['validation_cost']:.4f} = "
          f"${led['image_cost']+led['validation_cost']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
