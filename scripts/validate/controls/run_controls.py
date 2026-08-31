#!/usr/bin/env python3
"""Adversarial regression harness for the identity validator.

Runs ``shot_validator`` over a set of cases whose ground truth was established
by a human looking at the images, and checks the validator reproduces it.

The point of this file is that the validator can never again silently
rubber-stamp: if every case comes back PASS, this harness exits non-zero.

    # fetch fixtures from R2 once (~10 MB), then run
    python scripts/validate/controls/run_controls.py --fetch
    python scripts/validate/controls/run_controls.py --backend gemini --model gemini-2.5-flash

    # machine-readable, for CI
    python scripts/validate/controls/run_controls.py --json reports/controls.json
    echo $?      # 0 = every case matched its ground truth, 1 = a regression

Fixtures live outside git (they are large binaries; see CLAUDE.md) and are
pulled from R2 with rclone into --cache-dir, default .validator-controls/.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import shot_validator as sv  # noqa: E402

SPEC = HERE / "control-set.json"
MANIFEST = HERE / "control-manifest.json"
R2 = "r2:rex-assets/"


def fetch_fixtures(cache: Path) -> None:
    spec = json.loads(SPEC.read_text())
    f = spec["fixtures"]
    jobs = [
        (f["characters"]["r2_prefix"], cache / "characters", f["characters"]["files"]),
        (f["panels"]["r2_prefix"], cache / "panels", f["panels"]["files"]),
        (f["clips"]["r2_prefix"], cache / "clips", f["clips"]["files"]),
    ]
    if "panels_v5_attempts" in f:
        jobs.append((f["panels_v5_attempts"]["r2_prefix"], cache / "panels-v5",
                     f["panels_v5_attempts"]["files"]))
    for prefix, dest, files in jobs:
        dest.mkdir(parents=True, exist_ok=True)
        missing = [n for n in files if not (dest / n).exists()]
        if not missing:
            continue
        cmd = ["rclone", "copy", R2 + prefix, str(dest)]
        for n in missing:
            cmd += ["--include", n]
        print(f"[fetch] {prefix} -> {dest} ({len(missing)} file(s))", flush=True)
        subprocess.run(cmd, check=True)

    # Mid-frame extraction for the video controls.
    for mp4 in sorted((cache / "clips").glob("*.mp4")):
        jpg = mp4.with_name(mp4.stem + "-mid.jpg")
        if jpg.exists():
            continue
        dur = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", str(mp4)], text=True).strip())
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{dur / 2:.3f}",
            "-i", str(mp4), "-frames:v", "1", "-q:v", "2", str(jpg)], check=True)
        print(f"[frame] {jpg.name}", flush=True)

    # The deliberate mislabel: an identity sheet whose row NAMED Nina holds
    # Jenny's attributes. This is where the reference now lives, so this is
    # where the mislabel has to go to probe anything.
    real = json.loads(sv.DEFAULT_IDENTITY_SHEET.read_text())
    bad = json.loads(json.dumps(real))
    bad["characters"]["Nina"] = json.loads(json.dumps(real["characters"]["Jenny"]))
    bad["_comment"] = ("DELIBERATELY MISLABELLED control fixture: the row named "
                       "Nina is Jenny's. Never use this for real validation.")
    (cache / "identity-sheets-mislabel.json").write_text(json.dumps(bad, indent=2) + "\n")
    print("[mislabel] identity-sheets-mislabel.json (Nina row <- Jenny)", flush=True)


def resolve_image(cache: Path, rel: str) -> Path:
    return cache / rel


def run(args: argparse.Namespace) -> int:
    spec = json.loads(SPEC.read_text())
    manifest = json.loads(MANIFEST.read_text())
    shots = {s["shot_id"]: s for s in manifest}
    cache = Path(args.cache_dir)

    if args.fetch:
        fetch_fixtures(cache)

    backend = args.backend
    model = args.model or sv._default_model_for_backend(backend)
    client = sv._make_client(backend)

    only = set(args.only.split(",")) if args.only else None
    rows, in_tok, out_tok = [], 0, 0

    for case in spec["cases"]:
        if only and case["id"] not in only:
            continue
        img = resolve_image(cache, case["image"])
        if not img.exists():
            print(f"[skip] missing fixture {img} (run with --fetch)", file=sys.stderr)
            continue
        chars_dir = cache / case["characters_dir"]
        shot = shots[case["shot"]]
        print(f"[control] {case['id']} ({case['kind']}) -> {img.name}", flush=True)

        sheet = case.get("identity_sheet")
        res = sv.validate_panel(
            identity_crop=args.identity_crop,
            identity_sheet=(cache / sheet) if sheet else None,
            shot=shot,
            panel_path=img,
            characters_dir=chars_dir,
            locations_dir=cache / "locations",
            keyframes_dir=cache / "keyframes",
            backend=backend,
            model=model,
            client=client,
        )
        in_tok += res.usage["input_tokens"]
        out_tok += res.usage["output_tokens"]
        ids = res.aggregate_scores.get("character_identity", {})

        problems = []
        want = case.get("expect_overall")
        got = "PASS" if res.overall_pass else "FAIL"
        if want is not None and got != want:
            problems.append(f"overall {got}, expected {want}")
        for name, ceiling in (case.get("expect_identity_below") or {}).items():
            sc = ids.get(name)
            if sc is None:
                problems.append(f"identity[{name}] not scored (expected < {ceiling})")
            elif sc >= ceiling:
                problems.append(f"identity[{name}]={sc:.2f}, expected < {ceiling}")
        for name, floor in (case.get("expect_identity_at_or_above") or {}).items():
            sc = ids.get(name)
            if sc is None:
                problems.append(f"identity[{name}] not scored (expected >= {floor})")
            elif sc < floor:
                problems.append(f"identity[{name}]={sc:.2f}, expected >= {floor}")

        # What the validator actually READ off the frame, per character. This is
        # the assertion that matters for the scale cases: a score can come out
        # right for the wrong reason, an attribute cannot.
        ev = res.aggregate_scores.get("character_identity_evidence", {})
        for name, wanted in (case.get("expect_frame_attribute") or {}).items():
            got_attrs = (ev.get(name) or {}).get("frame_attributes") or {}
            for attr, want_val in wanted.items():
                got_val = got_attrs.get(attr)
                if got_val != want_val:
                    problems.append(
                        f"{name}.{attr} read as {got_val!r}, expected {want_val!r}")

        rows.append({
            "id": case["id"],
            "kind": case["kind"],
            "graded_on": {n: (e or {}).get("graded_on") for n, e in ev.items()},
            "crop_gain": {n: ((e or {}).get("crop") or {}).get("gain") for n, e in ev.items()},
            "crop_changed": {n: (e or {}).get("crop_changed") for n, e in ev.items()
                             if (e or {}).get("crop_changed")},
            "frame_attributes": {n: (e or {}).get("frame_attributes") for n, e in ev.items()},
            "expect_overall": want,
            "identity_evidence": res.aggregate_scores.get("character_identity_evidence", {}),
            "got_overall": got,
            "identity": ids,
            "identity_no_reference": res.aggregate_scores.get("character_identity_no_reference", []),
            "reasons": res.reasons,
            "notes": {n: i.get("notes", "") for n, i in
                      (res.keyframes[0].get("character_identity") or {}).items()},
            "problems": problems,
            "ok": not problems,
            "usage": res.usage,
        })
        mark = "ok " if not problems else "REGRESSION"
        print(f"    {mark} {got} | " + ", ".join(f"{k}={v:.2f}" for k, v in ids.items()), flush=True)
        for p in problems:
            print(f"      ! {p}", flush=True)

    cost = sv.estimate_cost(model, in_tok, out_tok)
    n_ok = sum(r["ok"] for r in rows)
    n_pass_overall = sum(r["got_overall"] == "PASS" for r in rows)

    print()
    print(f"{'case':<32} {'kind':<14} {'want':<5} {'got':<5} result")
    for r in rows:
        print(f"{r['id']:<32} {r['kind']:<14} {str(r['expect_overall'] or 'n/a'):<5} "
              f"{r['got_overall']:<5} {'ok' if r['ok'] else 'REGRESSION'}")
    print()
    n_cropped = sum(1 for r in rows for v in r["graded_on"].values() if v == "crop")
    n_graded = sum(1 for r in rows for v in r["graded_on"].values() if v)
    print(f"identity graded on a per-character crop for {n_cropped}/{n_graded} "
          f"character readings ({'crop pass ON' if args.identity_crop else 'crop pass OFF'})")
    print(f"{n_ok}/{len(rows)} cases match ground truth. "
          f"backend={backend} model={model} "
          f"tokens={in_tok}/{out_tok} cost=${cost:.4f} "
          f"(${cost / max(len(rows), 1):.4f} per image)")

    # A validator that passes everything is not a validator, even if by some
    # accident that matched the table. Guard the failure mode explicitly.
    rubber_stamp = bool(rows) and n_pass_overall == len(rows)
    if rubber_stamp:
        print("REGRESSION: every control case returned PASS - the validator is "
              "rubber-stamping, adversarial cases included.", file=sys.stderr)

    # The mirror-image failure. A validator that fails everything is just as
    # useless as one that passes everything, and it would sail through a control
    # set made only of adversarial cases. At least one case must come back with
    # every visible character at or above the identity gate.
    clean = [r for r in rows
             if r["identity"] and all(v >= 0.6 for v in r["identity"].values())]
    fails_everything = bool(rows) and not clean
    if fails_everything:
        print("REGRESSION: no control case scored every visible character at or "
              "above the identity gate - the validator is failing everything, "
              "which detects nothing.", file=sys.stderr)
    else:
        print(f"clean-pass guard: {len(clean)} case(s) scored every visible "
              f"character at or above the gate ("
              f"{', '.join(r['id'] for r in clean) or 'none'})")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps({
            "backend": backend, "model": model,
            "identity_crop": args.identity_crop,
            "usage": {"input_tokens": in_tok, "output_tokens": out_tok},
            "estimated_cost_usd": round(cost, 4),
            "cost_per_image_usd": round(cost / max(len(rows), 1), 4),
            "cases_ok": n_ok, "cases_total": len(rows),
            "rubber_stamp": rubber_stamp,
            "fails_everything": fails_everything,
            "clean_cases": [r["id"] for r in clean],
            "results": rows,
        }, indent=2))
        print(f"Wrote {args.json}")

    return 0 if (n_ok == len(rows) and not rubber_stamp
                 and not fails_everything and rows) else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cache-dir", default=".validator-controls",
                   help="Where R2 fixtures are cached (gitignored).")
    p.add_argument("--fetch", action="store_true",
                   help="Pull any missing fixtures from R2 before running.")
    p.add_argument("--backend", default=sv.DEFAULT_BACKEND, choices=["claude", "gemini"])
    p.add_argument("--no-identity-crop", dest="identity_crop", action="store_false",
                   default=True,
                   help="Grade identity on the whole frame (the pre-346 behaviour) "
                        "instead of on a per-character crop. Use it to reproduce a "
                        "before/after table on the same cases.")
    p.add_argument("--model", default=None)
    p.add_argument("--only", default=None, help="Comma-separated case ids.")
    p.add_argument("--json", default=None)
    return run(p.parse_args())


if __name__ == "__main__":
    sys.exit(main())
