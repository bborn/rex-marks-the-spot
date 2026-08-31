#!/usr/bin/env python3
"""Live smoke test for the fal provider - two cheap renders, hard spend cap.

This is plumbing verification, NOT production output.  It proves the wrapper
submits, polls, fetches, strips audio and lands the clip on R2; it does not
claim the clips pass any validation gate, and nothing downstream should consume
them.  Quality comparison against Omni is a separate task and needs the identity
validator (#342) first.

Two runs, both 5s at 480P ($0.05/s = $0.25 each, $0.50 total):

  A  first frame AND last frame, from LOCAL copies of Scene 1 v4 panels 1A and
     1B - exercises the data-URI path plus ``end_image_url`` conditioning.
  B  first frame only, from the panel's PUBLIC R2 URL - exercises URL
     passthrough, which is what the pipeline will actually use at scale.

Usage:
    export FAL_KEY=...            # never printed or written to a sidecar
    python scripts/video/run_fal_verify.py <A|B|both> <workdir>

The script refuses to start a run that would push cumulative spend (read from
the sidecars already in ``workdir``) past ``SPEND_CAP_USD``.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from video.fal_video import FalVideoGenerator  # noqa: E402


SPEND_CAP_USD = 2.00

RESOLUTION = "480P"
DURATION_SECONDS = 5

R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"
PANEL_1A = "storyboards/v4/scene-01/scene-01-1A-start.png"
PANEL_1B = "storyboards/v4/scene-01/scene-01-1B-start.png"

# Panel 1A is the wide establishing shot of the living room; 1B is the medium on
# Leo.  The prompt describes the move between them and nothing else - the two
# frames carry the content.
PROMPT_A = (
    "Slow, steady push in from the wide view of the family living room toward "
    "the small boy sitting cross-legged on the couch hugging his plush "
    "dinosaur. Warm interior lamplight, storm darkness outside the windows. "
    "The camera move is smooth and continuous. No cuts."
)
PROMPT_B = (
    "Static wide shot of the family living room in the evening. Gentle "
    "ambient life: the television flickers, curtains stir faintly. The camera "
    "does not move. No cuts."
)

RUNS = {
    "A": dict(
        label="first+last frame conditioning (local files -> data URI)",
        prompt=PROMPT_A,
        first_frame=None,  # filled in with the local download
        last_frame=None,
        use_local=True,
    ),
    "B": dict(
        label="first frame only (public R2 URL passthrough)",
        prompt=PROMPT_B,
        first_frame=f"{R2_PUBLIC}/{PANEL_1A}",
        last_frame=None,
        use_local=False,
    ),
}


def spent_so_far(outdir: Path) -> float:
    """Sum the published-rate cost of every clip already rendered here."""
    total = 0.0
    for sidecar in outdir.glob("*.mp4.json"):
        try:
            total += float(json.loads(sidecar.read_text()).get("estimated_cost_usd", 0))
        except Exception:
            pass
    return round(total, 4)


def fetch_panels(indir: Path) -> tuple[str, str]:
    """Pull the two v4 panels out of R2 so run A has local files to encode."""
    indir.mkdir(parents=True, exist_ok=True)
    paths = []
    for key in (PANEL_1A, PANEL_1B):
        dest = indir / Path(key).name
        if not dest.exists():
            subprocess.run(
                ["rclone", "copyto", f"r2:rex-assets/{key}", str(dest)], check=True
            )
        paths.append(str(dest))
    return paths[0], paths[1]


def probe_streams(path: str) -> list[str]:
    """Stream codec types in a file, so 'audio was stripped' is a measurement."""
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return [f"ffprobe failed: {proc.stderr.strip()[:200]}"]
    return [s["codec_type"] for s in json.loads(proc.stdout).get("streams", [])]


def run_one(name: str, workdir: Path) -> int:
    spec = dict(RUNS[name])
    indir, outdir = workdir / "in", workdir / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    gen = FalVideoGenerator()
    cost = gen.estimate_cost(DURATION_SECONDS, RESOLUTION)
    already = spent_so_far(outdir)
    if already + cost > SPEND_CAP_USD:
        print(
            f"REFUSING: ${already:.2f} already spent here + ${cost:.2f} for this "
            f"run would exceed the ${SPEND_CAP_USD:.2f} cap."
        )
        return 2

    if spec.pop("use_local"):
        first, last = fetch_panels(indir)
        spec["first_frame"], spec["last_frame"] = first, last

    out_mp4 = outdir / f"fal_verify_{name}.mp4"
    print(f"=== run {name}: {spec['label']}")
    print(f"    budget: ${already:.2f} spent, ${cost:.2f} for this clip, "
          f"cap ${SPEND_CAP_USD:.2f}")

    res = gen.generate(
        spec["prompt"],
        str(out_mp4),
        duration_seconds=DURATION_SECONDS,
        resolution=RESOLUTION,
        first_frame=spec["first_frame"],
        last_frame=spec["last_frame"],
        r2_path=f"video/fal-verify/{out_mp4.name}",
        run=name,
        purpose="provider plumbing verification, not gate-passing output",
    )

    streams = probe_streams(res.file_path)
    print(f"    streams after strip: {streams}")
    print(f"    cost:  ${res.estimated_cost:.4f}")
    print(f"    r2:    {res.metadata['r2_url']}")
    print(f"    total spend in {outdir}: ${spent_so_far(outdir):.2f}")

    # Fold the measurement into the sidecar so the audit trail is one file.
    sidecar = Path(str(out_mp4) + ".json")
    data = json.loads(sidecar.read_text())
    data["ffprobe_streams_after_strip"] = streams
    sidecar.write_text(json.dumps(data, indent=2, default=str))

    if "audio" in streams:
        print("    FAIL: an audio stream survived the strip")
        return 1
    return 0


def main() -> int:
    which, workdir = sys.argv[1], Path(sys.argv[2])
    names = ["A", "B"] if which == "both" else [which]
    for name in names:
        rc = run_one(name, workdir)
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
