#!/usr/bin/env python3
"""Scene 1 continuity gate for VIDEO shots.

A thin wrapper around check.py.  It samples N frames out of a clip with ffmpeg
and runs the *existing* still-image gate on each one - the geometry lives in
check.py and is not duplicated here.  Sampling several frames is the whole
point: a shot that starts on the locked staging and drifts halfway through is
exactly the failure a first-frame-only check misses.

    $0.00 per clip.  OpenCV + ffmpeg, no vision API, no network.

Policy
------
Three verdicts:  PASS, FAIL, INCONCLUSIVE.  INCONCLUSIVE means no check could be
applied to any sampled frame - typically a close-up scored against the wide 1A
plate - and it exits 1, because a clip nobody measured has not been cleared.
`--allow-inconclusive` flips that to 0 if your pipeline accepts it.

By default every sampled frame must pass.  `--tolerate N` allows N failing
frames, for the case where one sample lands on a lightning flash or a whip pan
and the shot is otherwise clean.  Raising it is a judgement call and the JSON
records what was tolerated, so it stays auditable.

Usage
-----
    python check_video.py SHOT.mp4
    python check_video.py SHOT.mp4 --shot 1A --frames 9 --verbose
    python check_video.py SHOT.mp4 --json > report.json
    python check_video.py SHOT.mp4 --keep-frames ./out/    # save the samples

Gating a pipeline:

    for f in shots/*.mp4; do
        python check_video.py "$f" --shot 1A || { echo "BLOCKED: $f"; exit 1; }
    done

Exit code 0 if the clip passes, 1 if it fails or is INCONCLUSIVE, 2 on a
usage/IO error.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2

# check.py sits next to this file. Import it rather than reimplementing it.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check import (  # noqa: E402
    ContinuityGate,
    FrameResult,
    add_gate_arguments,
    format_frame,
)

DEFAULT_FRAMES = 5


# ---------------------------------------------------------------------------
# ffmpeg / ffprobe
# ---------------------------------------------------------------------------


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise OSError(f"{name} not found on PATH - install ffmpeg to score video")
    return path


def probe_duration(video: Path) -> float:
    """Clip duration in seconds. Container duration, falling back to the stream."""
    for entry in ("format=duration", "stream=duration"):
        out = subprocess.run(
            [
                require_tool("ffprobe"), "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", entry,
                "-of", "default=nw=1:nk=1",
                str(video),
            ],
            capture_output=True, text=True, check=False,
        ).stdout.strip().splitlines()
        for line in out:
            try:
                value = float(line)
            except ValueError:
                continue
            if value > 0:
                return value
    raise OSError(f"could not read a duration from {video} - is it a video file?")


def sample_times(duration: float, count: int) -> list[float]:
    """`count` evenly spaced timestamps, offset to sit inside the clip.

    Midpoints of equal slices rather than endpoints: the last frame of an mp4 is
    a common decode-failure spot, and the first frame of an image-to-video clip
    is just the source panel, which would pass trivially.
    """
    if count < 1:
        raise ValueError("--frames must be at least 1")
    return [duration * (i + 0.5) / count for i in range(count)]


def extract_frames(video: Path, times: list[float], outdir: Path) -> list[tuple[float, Path]]:
    """Pull one PNG per timestamp. Skips timestamps ffmpeg cannot decode."""
    ffmpeg = require_tool("ffmpeg")
    outdir.mkdir(parents=True, exist_ok=True)
    frames: list[tuple[float, Path]] = []
    for index, t in enumerate(times):
        target = outdir / f"{video.stem}_f{index:02d}_{t:07.3f}s.png"
        subprocess.run(
            [ffmpeg, "-v", "error", "-ss", f"{t:.3f}", "-i", str(video),
             "-frames:v", "1", "-y", str(target)],
            capture_output=True, check=False,
        )
        if target.exists() and target.stat().st_size > 0:
            frames.append((t, target))
    if not frames:
        raise OSError(f"ffmpeg extracted no frames from {video}")
    return frames


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class ClipResult:
    video: str
    shot: str | None
    duration: float
    requested_frames: int
    tolerate: int
    frames: list[tuple[float, FrameResult]] = field(default_factory=list)

    @property
    def failed_frames(self) -> list[tuple[float, FrameResult]]:
        return [(t, r) for t, r in self.frames if not r.passed]

    @property
    def conclusive(self) -> bool:
        """Did any check actually run on any frame?

        A close-up scored against the wide plate skips every geometry check, so
        it can come back with nothing measured. Calling that PASS would clear a
        shot nobody looked at, which is the exact failure the Validation Gates
        rule exists to prevent.
        """
        return any(frame.conclusive for _, frame in self.frames)

    @property
    def verdict(self) -> str:
        if len(self.failed_frames) > self.tolerate:
            return "FAIL"
        return "PASS" if self.conclusive else "INCONCLUSIVE"

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"

    @property
    def skipped_checks(self) -> list[str]:
        """Check names that were n/a on every frame that ran."""
        names = [c.name for _, frame in self.frames for c in frame.checks]
        skipped = {c.name for _, frame in self.frames for c in frame.checks if c.status == "n/a"}
        applied = {c.name for _, frame in self.frames for c in frame.applied}
        return [n for n in dict.fromkeys(names) if n in skipped - applied]

    @property
    def failing_checks(self) -> list[str]:
        """Check names that failed on at least one frame, worst-first."""
        counts: dict[str, int] = {}
        for _, result in self.frames:
            for check in result.failures:
                counts[check.name] = counts.get(check.name, 0) + 1
        return [name for name, _ in sorted(counts.items(), key=lambda kv: -kv[1])]

    def to_dict(self) -> dict[str, Any]:
        return {
            "video": self.video,
            "shot": self.shot,
            "verdict": self.verdict,
            "passed": self.passed,
            "conclusive": self.conclusive,
            "duration_seconds": round(self.duration, 3),
            "frames_requested": self.requested_frames,
            "frames_scored": len(self.frames),
            "frames_failed": len(self.failed_frames),
            "tolerate": self.tolerate,
            "failing_checks": self.failing_checks,
            "skipped_checks": self.skipped_checks,
            "frames": [
                dict(timestamp=round(t, 3), **result.to_dict()) for t, result in self.frames
            ],
        }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_video(
    video: str | Path,
    gate: ContinuityGate,
    frames: int = DEFAULT_FRAMES,
    tolerate: int = 0,
    keep_frames: str | Path | None = None,
) -> ClipResult:
    """Sample `frames` stills out of `video` and run the still gate on each."""
    video = Path(video)
    if not video.exists():
        raise OSError(f"video not found: {video}")

    duration = probe_duration(video)
    times = sample_times(duration, frames)

    workdir = Path(keep_frames) if keep_frames else Path(tempfile.mkdtemp(prefix="contgate-"))
    try:
        extracted = extract_frames(video, times, workdir)
        result = ClipResult(
            video=str(video), shot=gate.shot, duration=duration,
            requested_frames=frames, tolerate=tolerate,
        )
        for t, path in extracted:
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None:
                continue
            result.frames.append((t, gate.check_image(image, label=f"t={t:.2f}s")))
        if not result.frames:
            raise OSError(f"no sampled frame from {video} could be decoded")
        return result
    finally:
        if keep_frames is None:
            shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def format_clip(result: ClipResult, verbose: bool = False) -> str:
    head = (
        f"{result.verdict:12s}  {result.video}"
        f"  [{len(result.frames) - len(result.failed_frames)}/{len(result.frames)} frames pass"
        f", {result.duration:.2f}s"
        + (f", shot {result.shot}" if result.shot else "")
        + (f", tolerate {result.tolerate}" if result.tolerate else "")
        + "]"
    )
    lines = [head]
    if result.failing_checks:
        lines.append("    failing checks: " + ", ".join(result.failing_checks))
    if result.skipped_checks:
        lines.append("    not measured:   " + ", ".join(result.skipped_checks))
    if result.verdict == "INCONCLUSIVE":
        lines.append(
            "    nothing was measured on any frame - this clip is NOT cleared. "
            "It needs a plate for its own framing."
        )
    for t, frame in result.frames:
        if not verbose and frame.passed:
            continue
        lines.append("  " + format_frame(frame, verbose).replace("\n", "\n  "))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score a video shot against the locked Scene 1 plate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("video", help="clip to score")
    add_gate_arguments(parser)
    parser.add_argument(
        "--frames", type=int, default=DEFAULT_FRAMES,
        help=f"how many evenly spaced frames to sample (default: {DEFAULT_FRAMES})",
    )
    parser.add_argument(
        "--tolerate", type=int, default=0, metavar="N",
        help="allow N failing frames before the clip fails (default: 0, all must pass)",
    )
    parser.add_argument("--keep-frames", metavar="DIR", help="write the sampled frames here")
    parser.add_argument(
        "--allow-inconclusive", action="store_true",
        help="exit 0 when no check could be applied (default: INCONCLUSIVE exits 1, "
        "because a clip nobody measured is not a cleared clip)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="show passing frames too")
    args = parser.parse_args(argv)

    if args.frames < 1:
        print("error: --frames must be at least 1", file=sys.stderr)
        return 2
    if args.tolerate < 0:
        print("error: --tolerate must be zero or positive", file=sys.stderr)
        return 2

    try:
        gate = ContinuityGate(args.plate, args.plate_spec, args.bible, args.shot)
        result = score_video(
            args.video, gate,
            frames=args.frames, tolerate=args.tolerate, keep_frames=args.keep_frames,
        )
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_clip(result, args.verbose))

    if result.verdict == "PASS":
        return 0
    if result.verdict == "INCONCLUSIVE" and args.allow_inconclusive:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
