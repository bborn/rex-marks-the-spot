#!/usr/bin/env python3
"""Scene 1 shot 1A at 720p: four takes, one generation per invocation.

Task #340.  This is the first production-resolution footage in the Omni
evaluation - everything before it was 360p probes.

The experiment is a 2x2: camera motion (slow push-in vs held frame) crossed
with duration (5s vs 10s).  Task #336's gate report found that the only 1A clip
that ever passed was Omni image_to_video from the validated v4 panel at
360p/5s (`G2`), and that the same panel and prompt family at 10s (`G3`) failed
its last frame because the push-in travelled far enough to take the wide plate
out of frame.  So both variables are worth separating.

    T1  5s   push-in     T3  10s  push-in
    T2  5s   held        T4  10s  held

Prompts are child-explicit on purpose: Phases 0.5-0.7 measured that naming
children is clear for everything except children alone in a police vehicle, and
this is a living room.  Wardrobe is copied out of
docs/process/continuity/bible/scene-01.json; the "do not invent" clauses (kids
on the couch not the floor, no glasses on Mia, Leo in dinosaur pyjamas, the TV
showing a cartoon, an empty windowsill) are stated as negatives in the prompt
because that is the only place the model reads them.

One take per invocation so spend stays observable between calls, and every run -
success or hard failure - writes a JSON sidecar next to the mp4.

Usage:
    python scripts/video/run_scene01_1A_720p.py <T1|T2|T3|T4> <workdir>

<workdir>/in must hold scene-01-1A-start.png (the validated v4 panel):
    rclone copy r2:rex-assets/storyboards/v4/scene-01/scene-01-1A-start.png <workdir>/in/
"""

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from video.omni_flash import OmniFlashGenerator  # noqa: E402


# Everything the four takes share: who is in frame, what they are wearing, and
# what must NOT appear.  Identical across all four so the only differences
# between takes are the camera clause and the duration.
STAGING = (
    "Hold this exact composition, framing and art style. "
    "Mia, an 8-year-old girl with dark curly hair in a magenta polka-dot t-shirt "
    "and blue jeans, and her little brother Leo, a 5-year-old boy in green "
    "dinosaur-pattern pajamas holding a green plush dinosaur, are the two kids; "
    "both stay seated together on the couch in the middle of the frame. "
    "Their teenage babysitter Jenny, dark brown hair in a ponytail, stays in the "
    "armchair at screen right looking down at her phone. Their parents Nina, in an "
    "elegant black formal dress, and Gabe, in a black tuxedo, stay standing in the "
    "kitchen area behind the couch. The old TV at screen left keeps playing a "
    "colourful cartoon. Rain and a stormy sky continue outside the windows. The "
    "toy dinosaurs stay on the floor. "
    "The kids do not get off the couch and do not sit on the floor. Mia does not "
    "wear glasses. Leo stays in his dinosaur pajamas. No new characters enter. "
    "Nothing new appears on the windowsill; it stays empty. "
)

AUDIO = "No dialogue. No music. No sound effects. Silent."

# The G2/G3 motion clause, verbatim.
PUSH_IN = "Camera only: a slow, gentle push-in. "

# The control: hold the plate's framing, allow only breathing.
HELD = (
    "Camera: hold this framing. No push-in, no zoom, no pan, no reframe - only a "
    "very slight handheld drift, as if the camera is breathing. "
)

RUNS = {
    "T1": dict(duration=5, prompt=STAGING + PUSH_IN + AUDIO),
    "T2": dict(duration=5, prompt=STAGING + HELD + AUDIO),
    "T3": dict(duration=10, prompt=STAGING + PUSH_IN + AUDIO),
    "T4": dict(duration=10, prompt=STAGING + HELD + AUDIO),
}

RESOLUTION = "720p"
PANEL = "scene-01-1A-start.png"

# Hard cap from the task.  Checked against the running total in the sidecars
# before every call, so a run that would breach it never leaves the machine.
HARD_CAP_USD = 4.00


def spent_so_far(outdir: Path) -> float:
    total = 0.0
    for sidecar in outdir.glob("*.json"):
        try:
            total += float(json.loads(sidecar.read_text()).get("billed_usd") or 0.0)
        except (ValueError, OSError):
            pass
    return round(total, 6)


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in RUNS:
        print(__doc__)
        return 2

    name, workdir = sys.argv[1], Path(sys.argv[2])
    spec = RUNS[name]
    indir, outdir = workdir / "in", workdir / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    panel = indir / PANEL
    if not panel.exists():
        print(f"ERROR: validated panel not found at {panel}")
        return 2

    gen = OmniFlashGenerator()
    duration = spec["duration"]
    estimate = gen.estimate_cost(duration, RESOLUTION)
    already = spent_so_far(outdir)
    if already + estimate > HARD_CAP_USD:
        print(
            f"REFUSING {name}: ${already:.4f} already billed + ~${estimate:.4f} "
            f"estimated would breach the ${HARD_CAP_USD:.2f} cap."
        )
        return 1
    print(
        f"[{name}] {duration}s @ {RESOLUTION}  est ${estimate:.4f}  "
        f"(billed so far ${already:.4f}, cap ${HARD_CAP_USD:.2f})"
    )

    out_mp4 = outdir / f"{name}_raw.mp4"
    sidecar = outdir / f"{name}.json"
    record = {
        "take": name,
        "task": "image_to_video",
        "resolution": RESOLUTION,
        "duration_seconds": duration,
        "prompt": spec["prompt"],
        "first_frame": str(panel),
        "estimate_usd": estimate,
    }
    try:
        res = gen.generate(
            spec["prompt"],
            str(out_mp4),
            duration_seconds=duration,
            aspect_ratio="16:9",
            resolution=RESOLUTION,
            task="image_to_video",
            first_frame=str(panel),
        )
        record.update(
            status="ok",
            file=res.file_path,
            billed_usd=res.estimated_cost,
            generation_time_seconds=res.generation_time_seconds,
            metadata=res.metadata,
        )
        print(f"[{name}] OK  billed=${res.estimated_cost:.4f}  {res.file_path}")
    except Exception as exc:  # a hard failure IS a result - record it verbatim
        record.update(
            status="failed",
            error_type=type(exc).__name__,
            error=str(exc),
            traceback=traceback.format_exc(),
            billed_usd=0.0,
        )
        print(f"[{name}] FAILED {type(exc).__name__}: {exc}")

    sidecar.write_text(json.dumps(record, indent=2, default=str))
    print(f"[{name}] total billed now ${spent_so_far(outdir):.4f}")
    return 0 if record["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
