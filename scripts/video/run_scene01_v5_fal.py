#!/usr/bin/env python3
"""Render all nine Scene 1 shots on fal (MiniMax H3), first AND last frame.

This is the first Scene 1 render from on-model panels. Everything before it
inherited the off-model v4 cast.

Each shot is conditioned on BOTH v5 panels - `image_url` = the validated
`-start` panel, `end_image_url` = the validated `-end` panel - which is the
thing this provider exists for. Task #341 measured last-frame anchoring moving
a close-up from 0.231 to 0.741 on the continuity gate, and also measured that
anchoring to an OFF-MODEL last frame is worse than no anchor at all, which is
why `promote_end_panels.py` refuses to ship an end panel that fails identity.

The panels are passed as their PUBLIC R2 URLs, not as data URIs: it keeps the
request body small and it is what the pipeline does at scale.

Both copies of every clip are kept. H3 always attaches an AAC track and there
is no parameter to turn it off, so the raw download goes to R2 untouched and a
stream-copied audio-free version (`ffmpeg -c:v copy -an`) goes beside it. fal's
own CDN URLs expire in about a week, so nothing is left there.

Spend is checked against the SHARED ledger (`reports/scene-01-v5-render/
ledger.json`, which already carries the end-panel generation spend) before every
single render call, against the task's hard $8.00 cap.

Usage:
  python3 scripts/video/run_scene01_v5_fal.py                 # all nine
  python3 scripts/video/run_scene01_v5_fal.py 1A 1B           # subset
  python3 scripts/video/run_scene01_v5_fal.py --suffix -r2 1F # a regeneration
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from video.fal_video import FalVideoGenerator  # noqa: E402

R2_PUBLIC = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"
PANEL_BASE = "storyboards/v5/scene-01"
R2_OUT = "animation-tests/scene01-v5-fal"
LEDGER = ROOT / "reports/scene-01-v5-render/ledger.json"
OUT_DIR = ROOT / "work/fal"

RESOLUTION = "768P"
DURATION_SECONDS = 5      # H3's billable floor; trim in the edit, not here

# Shared across every prompt.  The two panels carry the content; the prompt
# carries the MOVE and the do-not-invent rules.  Wording follows #340, which
# measured that naming the children explicitly is not a filter risk in a
# domestic interior.
NEGATIVES = (
    "No new characters enter the frame and nobody leaves it. Nobody changes "
    "clothes. Nobody stands up or sits down unless described above. Any "
    "lightning stays OUTSIDE the windows, never over an interior wall, over "
    "furniture or over a person. No text, no captions, no subtitles, no "
    "on-screen graphics, no watermark. One continuous take - no cuts, no "
    "dissolves, no shot changes."
)
AUDIO = "No dialogue. No music. No sound effects. Silent."

MOVES = {
    "1A": (
        "Static wide shot of the family living room in the evening. The camera "
        "does not move at all: no push, no pan, no zoom, no reframe. Inside "
        "the held frame, the storm outside the windows builds to a bright "
        "forked lightning flash and cold blue light washes through the room; "
        "the old television at screen left flickers and a band of static rolls "
        "through its picture; the small boy in dinosaur pajamas turns his head "
        "away from the television toward his parents; the older girl beside "
        "him glances toward the windows. The teenage babysitter in the "
        "armchair does not look up from her phone. Everyone stays seated and "
        "standing exactly where they are."
    ),
    "1B": (
        "A slow, gentle push in on the small boy sitting cross-legged on the "
        "couch hugging his green plush dinosaur. The move is smooth, "
        "continuous and small - the framing tightens only slightly. He tips "
        "his head down toward the toy in his arms and breaks into a quick "
        "delighted grin. The toy dinosaurs on the cushions stay where they "
        "are. His sister stays cropped at the extreme left edge of frame."
    ),
    "1C": (
        "A smooth, slow tracking move with the woman in the black evening gown "
        "in the front hall. She finishes fastening her earring, lowers both "
        "hands, settles the small black purse against her hip and turns her "
        "head back over her shoulder to call into the living room, her mouth "
        "moving as she talks. The man in the tuxedo waits by the front door. "
        "The teenage babysitter stays curled in the armchair on her phone. The "
        "camera move is gentle and continuous."
    ),
    "1D": (
        "Static two-shot of the man in the tuxedo and the woman in the black "
        "gown standing in the living room. The camera holds - no push, no pan, "
        "no zoom. He lowers his wrist from checking his watch, lifts his head "
        "toward her and opens both hands away from his sides in an exasperated "
        "gesture, talking. She turns to face him, pats the side of her hip as "
        "if feeling for a pocket and holds one palm up, asking him something. "
        "Behind them the two children stay on the couch and the teenage "
        "babysitter stays in the armchair on her phone."
    ),
    "1E": (
        "Static close-up on the teenage babysitter looking down at her phone, "
        "its screen lighting her face from below. The camera holds - no push, "
        "no pan, no zoom. Her thumb taps the screen and a small cheerful smile "
        "spreads across her face. She does NOT look up and she does not turn "
        "her head; her eyes stay on the phone the whole time. The blurred "
        "living room behind her is still."
    ),
    "1F": (
        "Static close-up insert on the old television. The camera holds - no "
        "push, no pan, no zoom. There are no people in this shot. The cartoon "
        "picture jitters; horizontal scan lines roll down through it; grey "
        "static swells across the screen; and a bright blue-white flash blooms "
        "out of the middle of the picture, throwing blue light onto the wooden "
        "cabinet and the wall around it."
    ),
    "1G": (
        "Static over-the-shoulder shot from behind two children sitting on the "
        "floor watching television, seen from behind. The camera holds - no "
        "push, no pan, no zoom. The children glance back over their shoulders "
        "toward their parents and then turn back to the cartoon, so they end "
        "the shot facing the television again with their backs to camera. "
        "Behind them the mother in the black gown turns toward them and lifts "
        "one hand in a small goodbye wave, and the father in the tuxedo "
        "half-turns toward the door. There are exactly two children in this "
        "shot."
    ),
    "1H": (
        "A very slow, very small push in on the young girl's face as she looks "
        "up at her parents. The move is barely perceptible and completely "
        "smooth. She finishes speaking and closes her mouth, her eyebrows lift "
        "in the middle, and her eyes shine as she waits for an answer. The "
        "blurred foreground shapes at the extreme left and right edges of "
        "frame stay where they are. The lightning outside the window fades."
    ),
    "1I": (
        "Static two-shot of the man in the tuxedo and the woman in the black "
        "gown facing each other in the front hall by the door. The camera "
        "holds. He lifts his chin to meet her eyes, opens one hand from his "
        "side in a small conceding gesture and speaks a single word; the hard "
        "set of her glare releases, her shoulders drop, a small satisfied "
        "smile appears and she turns toward the front door and reaches for the "
        "brass knob. Exactly two people are in this shot and nobody else."
    ),
}


def load_ledger() -> dict:
    return json.loads(LEDGER.read_text())


def save_ledger(led: dict) -> None:
    LEDGER.write_text(json.dumps(led, indent=2))


def ledger_total(led: dict) -> float:
    return led["image_cost"] + led["validation_cost"] + led["video_cost"]


def probe_streams(path: Path) -> list[str]:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return [f"ffprobe failed: {proc.stderr.strip()[:200]}"]
    return [s["codec_type"] for s in json.loads(proc.stdout).get("streams", [])]


def strip_audio(src: Path, dest: Path) -> None:
    proc = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-c:v", "copy", "-an", str(dest)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not dest.exists():
        raise RuntimeError(f"ffmpeg strip failed: {proc.stderr.strip()[:400]}")


def rclone_copyto(local: Path, key: str) -> str:
    subprocess.run(["rclone", "copyto", str(local), f"r2:rex-assets/{key}"],
                   check=True)
    return f"{R2_PUBLIC}/{key}"


def grab_frames(clip: Path, sid: str, out_dir: Path) -> list[Path]:
    """first / middle / last stills, for the report and for eyeballing."""
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(clip)],
        capture_output=True, text=True).stdout.strip() or DURATION_SECONDS)
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for label, t in (("first", 0.05), ("mid", dur / 2), ("last", max(0.0, dur - 0.12))):
        dest = out_dir / f"{sid}-{label}.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}",
             "-i", str(clip), "-frames:v", "1", "-q:v", "3", str(dest)],
            check=True)
        made.append(dest)
    return made


# Applied to a REGENERATION of a shot that failed the identity gate on Gabe's
# eyewear. #345 measured that the rims are usually drawn right and lost in a dim
# key, and the crop control in this task reproduced that at the video stage: the
# same pixels read `thin_wire_rectangular` cropped and `heavy_dark_rectangular`
# in frame. So the retry aims at the READOUT - keep the rims lit - rather than
# re-rolling the dice on an unchanged prompt.
LIT_RIMS = (
    "Keep the man's eyeglasses reading as THIN BRIGHT SILVER WIRE rectangles "
    "throughout the shot: a specular highlight running along the top of each "
    "lens, a clear gap of warmly lit skin between the rim and his eyebrow, and "
    "enough key light on his face that the rims never fall into shadow and "
    "never thicken into dark plastic frames. He stays heavy-set and stubbled, "
    "with the same round full face, for the whole clip."
)

MIA_HAIR = (
    "The older girl keeps her long dark curly hair gathered in a HIGH CURLY "
    "PONYTAIL with long springy curls falling from it past her jaw; her hair "
    "never shortens, never comes down and never straightens."
)


def render_one(gen: FalVideoGenerator, sid: str, led: dict, cap: float,
               suffix: str, extra_prompt: str = "",
               use_end_frame: bool = True) -> dict | None:
    cost = gen.estimate_cost(DURATION_SECONDS, RESOLUTION)
    total = ledger_total(led)
    if total + cost > cap:
        print(f"!! CAP STOP before {sid}: ${total:.3f} spent + ${cost:.3f} "
              f"would cross the ${cap:.2f} cap")
        return None

    first = f"{R2_PUBLIC}/{PANEL_BASE}/scene-01-{sid}-start.png"
    last = (f"{R2_PUBLIC}/{PANEL_BASE}/scene-01-{sid}-end.png"
            if use_end_frame else None)
    parts = [MOVES[sid]]
    if extra_prompt:
        parts.append(extra_prompt)
    parts += [NEGATIVES, AUDIO]
    prompt = "\n\n".join(parts)

    raw = OUT_DIR / f"scene-01-{sid}{suffix}-raw.mp4"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== {sid}{suffix}: 768P {DURATION_SECONDS}s first+last frame "
          f"(${cost:.2f}; ${total:.3f} spent of ${cap:.2f})", flush=True)

    res = gen.generate(
        prompt, str(raw),
        duration_seconds=DURATION_SECONDS,
        resolution=RESOLUTION,
        first_frame=first,
        last_frame=last,
        strip_audio=False,               # keep the raw; strip into a second file
        upload_to_r2=True,
        r2_path=f"{R2_OUT}/raw/scene-01-{sid}{suffix}-raw.mp4",
        shot_id=sid,
        scene="scene-01",
        panel_set="v5",
        first_frame_url=first,
        last_frame_url=last,
    )

    led["video_calls"] += 1
    led["video_cost"] += res.estimated_cost
    led["entries"].append({"kind": "video", "shot": sid + suffix,
                           "usd": res.estimated_cost})
    save_ledger(led)

    clean = OUT_DIR / f"scene-01-{sid}{suffix}.mp4"
    strip_audio(raw, clean)
    raw_streams, clean_streams = probe_streams(raw), probe_streams(clean)
    clean_url = rclone_copyto(clean, f"{R2_OUT}/scene-01-{sid}{suffix}.mp4")

    frames = grab_frames(clean, sid + suffix, OUT_DIR / "frames")
    for f in frames:
        rclone_copyto(f, f"{R2_OUT}/frames/{f.name}")

    row = {
        "shot_id": sid,
        "suffix": suffix,
        "resolution": RESOLUTION,
        "requested_duration_seconds": DURATION_SECONDS,
        "actual_duration_seconds": res.duration_seconds,
        "estimated_cost_usd": round(res.estimated_cost, 4),
        "generation_time_seconds": round(res.generation_time_seconds, 1),
        "first_frame_url": first,
        "last_frame_url": last,
        "anchored": bool(last),
        "raw_r2_url": res.metadata.get("r2_url"),
        "clip_r2_url": clean_url,
        "frames_r2": [f"{R2_PUBLIC}/{R2_OUT}/frames/{f.name}" for f in frames],
        "raw_streams": raw_streams,
        "stripped_streams": clean_streams,
        "local_clip": str(clean.relative_to(ROOT)),
        "prompt": prompt,
    }
    sidecar = OUT_DIR / f"scene-01-{sid}{suffix}.json"
    sidecar.write_text(json.dumps(row, indent=2))
    print(f"    {res.duration_seconds:.2f}s, ${res.estimated_cost:.3f}, "
          f"raw={raw_streams} stripped={clean_streams}")
    print(f"    {clean_url}")
    if "audio" in clean_streams:
        print("    WARNING: an audio stream survived the strip")
    return row


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--cap", type=float, default=8.00)
    ap.add_argument("--suffix", default="",
                    help="filename suffix for a regeneration, e.g. -r2")
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--lit-rims", action="store_true",
                    help="append the LIT_RIMS clause (retry for a shot that "
                         "failed the identity gate on Gabe's eyewear)")
    ap.add_argument("--mia-hair", action="store_true",
                    help="append the MIA_HAIR clause")
    ap.add_argument("--no-end-frame", action="store_true",
                    help="render from the FIRST FRAME ONLY. The right choice "
                         "when the end panel is not usable as an anchor - "
                         "#341 measured a bad anchor as worse than none.")
    args = ap.parse_args(argv)

    extra = "\n\n".join(
        [c for c, on in ((LIT_RIMS, args.lit_rims), (MIA_HAIR, args.mia_hair))
         if on])

    shots = args.shots or list(MOVES)
    unknown = [s for s in shots if s not in MOVES]
    if unknown:
        print(f"unknown shots: {unknown}", file=sys.stderr)
        return 2

    gen = FalVideoGenerator()
    led = load_ledger()
    print(f"running total before this step: ${ledger_total(led):.3f} "
          f"of ${args.cap:.2f}")

    rows = []
    for sid in shots:
        try:
            row = render_one(gen, sid, led, args.cap, args.suffix,
                             extra_prompt=extra,
                             use_end_frame=not args.no_end_frame)
        except Exception as exc:
            # A moderation block or a bad parameter on one shot must not throw
            # away the eight that rendered.
            print(f"    {sid} FAILED: {type(exc).__name__}: {exc}")
            rows.append({"shot_id": sid, "suffix": args.suffix,
                         "error": f"{type(exc).__name__}: {exc}"})
            continue
        if row is None:
            break
        rows.append(row)
        time.sleep(args.delay)

    out = ROOT / f"reports/scene-01-v5-render/renders{args.suffix}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(out.read_text()) if out.exists() else []
    by_id = {r["shot_id"]: r for r in existing}
    for r in rows:
        by_id[r["shot_id"]] = r
    out.write_text(json.dumps([by_id[k] for k in sorted(by_id)], indent=2))

    print(f"\nrendered {len([r for r in rows if 'error' not in r])} of "
          f"{len(shots)}; running total ${ledger_total(led):.3f} "
          f"of ${args.cap:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
