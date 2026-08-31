#!/usr/bin/env python3
"""Measure how far a clip's camera actually travels, in the clip's own frame.

Affine ECC registration of each sampled frame against the clip's OWN first
frame, downsampled to 640x360.  ``scale`` is how much the frame has zoomed in
relative to frame 0; ``shift`` is the residual translation in 640x360 pixels.

This is the measurement #340 used to show that the same push-in prompt travels
about six times less at 720p than at 360p (docs/research/scene01-1A-720p.md);
the script itself was never committed, so it is written here to that
description.  It is free - OpenCV only, no network, no spend.

    python scripts/video/camera_travel.py clip.mp4 [clip2.mp4 ...] [--samples 5]
    python scripts/video/camera_travel.py work/out/*.mp4 --json out.json
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

WIDTH, HEIGHT = 640, 360


def _gray(frame):
    small = cv2.resize(frame, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0


def measure(path: str, samples: int = 5) -> dict:
    """Register `samples` evenly spaced frames against the clip's first frame."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {path}")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    if total < 2:
        raise SystemExit(f"{path}: too few frames ({total})")

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ok, first = cap.read()
    if not ok:
        raise SystemExit(f"{path}: cannot read frame 0")
    ref = _gray(first)

    # Frame 0 plus `samples` points spread to the last frame, so the table
    # reads 0% / 25% / 50% / 75% / end for the default of 5.
    idx = [0] + [round((i + 1) * (total - 1) / samples) for i in range(samples)]
    rows = []
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
    for n in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, n)
        ok, frame = cap.read()
        if not ok:
            continue
        cur = _gray(frame)
        warp = np.eye(2, 3, dtype=np.float32)
        try:
            cv2.findTransformECC(ref, cur, warp, cv2.MOTION_AFFINE, criteria, None, 5)
            # The warp maps a point x in the reference onto W.x in the
            # current frame, so a push-in - which magnifies about the centre -
            # gives a linear part larger than identity.  scale > 1 is zoomed in.
            det = float(np.linalg.det(warp[:, :2]))
            scale = np.sqrt(abs(det)) if det else float("nan")
            shift = (round(float(warp[0, 2]), 1), round(float(warp[1, 2]), 1))
            converged = True
        except cv2.error:
            scale, shift, converged = float("nan"), (0.0, 0.0), False
        rows.append({
            "frame": n,
            "t": round(n / fps, 2),
            "pct": round(100.0 * n / (total - 1)),
            "scale": round(scale, 4) if scale == scale else None,
            "shift": shift,
            "converged": converged,
        })

    duration = (total - 1) / fps
    end = rows[-1]["scale"]
    return {
        "clip": Path(path).name,
        "frames": total,
        "fps": round(fps, 3),
        "duration_seconds": round(duration, 3),
        "samples": rows,
        "end_scale": end,
        "zoom_rate_pct_per_s": (round(100.0 * (end - 1.0) / duration, 2)
                                if end and duration else None),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--samples", type=int, default=4,
                    help="sample points after frame 0 (default 4 -> 25/50/75/end)")
    ap.add_argument("--json", help="also write the raw measurements here")
    args = ap.parse_args()

    out = [measure(c, args.samples) for c in args.clips]

    hdr = f"{'clip':>10}  " + "  ".join(f"{r['pct']}%".rjust(6)
                                        for r in out[0]["samples"])
    print(hdr + "   end shift    zoom rate")
    print("-" * (len(hdr) + 24))
    for r in out:
        cells = "  ".join((f"{s['scale']:.3f}" if s["scale"] else " n/c ").rjust(6)
                          for s in r["samples"])
        sh = r["samples"][-1]["shift"]
        rate = r["zoom_rate_pct_per_s"]
        rate_s = f"{rate:>5.1f}%/s" if rate is not None else "  n/c   "
        print(f"{r['clip'][:10]:>10}  {cells}   ({sh[0]:>6.1f},{sh[1]:>6.1f})"
              f"   {rate_s}")

    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
