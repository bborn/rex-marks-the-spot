#!/usr/bin/env python3
"""Score every existing Scene 1 clip on R2 with the continuity gate.

This is the script that produced the table in VIDEO-GATE.md. It reads clips and
writes a report - it generates nothing and calls no paid API. $0.00 to re-run.

    # one-time, ~54 MB
    rclone copy r2:rex-assets/animation-tests/omni-1.1-flash-phase0/  clips/phase0/       --include '*.mp4'
    rclone copy r2:rex-assets/animation-tests/scene01-seedance-mitte/ clips/mitte/        --include '*.mp4'
    rclone copy r2:rex-assets/animation-tests/scene01-panel01-mvp/    clips/panel01-mvp/  --include '*.mp4'

    python score_corpus.py ./clips report.json report.csv

Each entry pairs a clip with the manifest shot it was made for, because the gate
needs the shot to know the intended framing. A clip that is not a Scene 1 shot
at all (an empty-room probe, a reference-image probe) is listed with shot None.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check import ContinuityGate  # noqa: E402
import check_video  # noqa: E402

FRAMES = 5

# (family, R2 directory under animation-tests/, path below the clips root, manifest shot)
CORPUS: list[tuple[str, str, str, str | None]] = [
    ("Phase 0 (Omni 1.1 Flash)", "omni-1.1-flash-phase0", "phase0/G1_text_to_video.mp4", None),
    ("Phase 0 (Omni 1.1 Flash)", "omni-1.1-flash-phase0", "phase0/G2_image_to_video.mp4", "1A"),
    ("Phase 0 (Omni 1.1 Flash)", "omni-1.1-flash-phase0", "phase0/G3_image_to_video.mp4", "1A"),
    ("Phase 0 (Omni 1.1 Flash)", "omni-1.1-flash-phase0", "phase0/G4_reference_to_video.mp4", None),
    ("Phase 0 (Omni 1.1 Flash)", "omni-1.1-flash-phase0", "phase0/PROBE_12refs.mp4", "1A"),
    ("Seedance / mitte shots", "scene01-seedance-mitte", "mitte/shots/01-shot-1A.mp4", "1A"),
    ("Seedance / mitte shots", "scene01-seedance-mitte", "mitte/shots/02-shot-1B.mp4", "1B"),
    ("Seedance / mitte shots", "scene01-seedance-mitte", "mitte/shots/03-shot-1C.mp4", "1C"),
    ("Seedance / mitte shots", "scene01-seedance-mitte", "mitte/shots/04-shot-1D.mp4", "1D"),
    ("Seedance / mitte shots", "scene01-seedance-mitte", "mitte/shots/05-shot-1G.mp4", "1G"),
    ("Seedance / mitte shots", "scene01-seedance-mitte", "mitte/shots/06-shot-1H.mp4", "1H"),
    ("Seedance / mitte shots", "scene01-seedance-mitte", "mitte/shots/07-shot-1I.mp4", "1I"),
    ("Seedance / mitte assembly", "scene01-seedance-mitte",
     "mitte/shots/scene-01-parents-leaving.mp4", "1A"),
    ("Google Flow", "scene01-seedance-mitte", "mitte/flow-veo-1A.mp4", "1A"),
    ("Google Flow", "scene01-seedance-mitte", "mitte/flow-veo-1A-frames.mp4", "1A"),
    ("Google Flow", "scene01-seedance-mitte", "mitte/flow-veo-1C.mp4", "1C"),
    ("Google Flow", "scene01-seedance-mitte", "mitte/flow-omni-1D.mp4", "1D"),
    ("Veo panel-01 MVP", "scene01-panel01-mvp", "panel01-mvp/scene01-panel01-veo2-v1.mp4", "1A"),
    ("Veo panel-01 MVP", "scene01-panel01-mvp", "panel01-mvp/scene01-panel01-veo2-v2.mp4", "1A"),
    ("Veo panel-01 MVP", "scene01-panel01-mvp", "panel01-mvp/scene01-panel01-veo3-v1.mp4", "1A"),
    ("Veo panel-01 MVP", "scene01-panel01-mvp",
     "panel01-mvp/scene01-panel01-veo3-v2-stable.mp4", "1A"),
    ("Veo panel-01 MVP", "scene01-panel01-mvp",
     "panel01-mvp/scene01-panel01-veo3-v3-ultrastable.mp4", "1A"),
    ("Veo panel-01 MVP", "scene01-panel01-mvp",
     "panel01-mvp/scene01-panel01-veo3-v4-anchored.mp4", "1A"),
    ("Veo panel-01 MVP", "scene01-panel01-mvp", "panel01-mvp/scene01-panel01-veo31-v1.mp4", "1A"),
]

CHECK_NAMES = ("staging_orientation", "layout_match", "couch_occupancy", "wardrobe")


def worst_scores(result: check_video.ClipResult) -> dict[str, float | None]:
    """Lowest score each check reached across the sampled frames."""
    out: dict[str, float | None] = {}
    for name in CHECK_NAMES:
        values = [
            c.score for _, frame in result.frames for c in frame.checks
            if c.name == name and c.score is not None
        ]
        out[name] = min(values) if values else None
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 2
    root, json_out, csv_out = Path(argv[1]), Path(argv[2]), Path(argv[3])

    gates: dict[str | None, ContinuityGate] = {}
    rows, blobs = [], []
    for family, r2_dir, rel, shot in CORPUS:
        clip = root / rel
        if not clip.exists():
            print(f"MISSING       {rel}  (not downloaded - see the rclone lines above)")
            continue
        if shot not in gates:
            gates[shot] = ContinuityGate(shot=shot)
        result = check_video.score_video(clip, gates[shot], frames=FRAMES)

        blob = result.to_dict()
        blob["family"], blob["r2_dir"] = family, r2_dir
        blobs.append(blob)

        scores = worst_scores(result)
        rows.append({
            "family": family,
            "clip": clip.name,
            "shot": shot or "-",
            "duration_s": f"{result.duration:.1f}",
            "frames": "".join("P" if f.passed else "F" for _, f in result.frames),
            "verdict": result.verdict,
            "failing": " ".join(result.failing_checks) or "-",
            "not_measured": " ".join(result.skipped_checks) or "-",
            **{f"worst_{k}": ("" if v is None else f"{v:.3f}") for k, v in scores.items()},
        })
        print(f"{result.verdict:12s}  {clip.name:44s} {rows[-1]['frames']}  {rows[-1]['failing']}")

    if not rows:
        print("nothing scored - is the clips root right?")
        return 2

    json_out.write_text(json.dumps(blobs, indent=2))
    with csv_out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    tally = {v: sum(r["verdict"] == v for r in rows) for v in ("PASS", "FAIL", "INCONCLUSIVE")}
    print(f"\n{len(rows)} clips: " + ", ".join(f"{n} {k}" for k, n in tally.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
