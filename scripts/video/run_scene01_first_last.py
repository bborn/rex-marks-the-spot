#!/usr/bin/env python3
"""Scene 1 shots 1B/1D/1F/1H at 720p: first-frame-only vs first+last-frame.

Task #341.  Follows #340 (shot 1A at 720p, four takes, all four gated) and
depends on the per-shot plates from #339.

The question is the one the May 23 post left open: Omni takes a ``<LAST_FRAME>``
as well as a ``<FIRST_FRAME>``, so does anchoring the end of a clip improve how
well it holds the locked composition?

Only 1B, 1D, 1F and 1H are rendered.  1A is done, and 1C/1E/1G/1I are
``can_clear: no`` in scene-01-plate.json - their plates can convict a clip but
cannot acquit one, so rendering them would produce footage the gate cannot
clear.  See VIDEO-GATE.md's discrimination matrix.

Three take kinds, and the difference between them is ONLY which media are bound:

    <SHOT>A   <FIRST_FRAME> = the shot's locked v4 panel.               (baseline)
    <SHOT>B   <FIRST_FRAME> = <LAST_FRAME> = that same locked panel.    (anchored)
    <SHOT>C   <FIRST_FRAME> = locked panel, <LAST_FRAME> = the
              scene-01-panel-NN-end.png that maps to this shot.         (probe)

The prompt text is byte-identical between a shot's A, B and C takes, so any
difference in the gate scores is attributable to the frame binding and nothing
else.

Why B anchors on the shot's OWN start panel rather than on an end panel: the
``scene-01-panel-NN-start/end`` pairs in ``r2:rex-assets/storyboards/v4/scene-01/``
are NOT part of the validated v4 set despite sharing its prefix.  They are the
March 2026 pre-lock generation - a different living room, a flat-panel TV where
the locked plate has a CRT, off-model wardrobe, and in 1D's case the two-shot is
mirrored.  Scored against their own shots' plates with ``check.py``, all four of
the end panels this task would have used fail or come back inconclusive:

    panel-02-end vs 1B   FAIL          layout 0.472, wardrobe 0.280
    panel-04-end vs 1D   FAIL          staging mirrored (-0.073)
    panel-06-end vs 1F   INCONCLUSIVE  layout 0.011
    panel-08-end vs 1H   FAIL          layout 0.356, wardrobe 0.056

CLAUDE.md's Validation Gates rule is explicit that a storyboard panel is not
trusted because it exists, so those panels cannot be a production last frame.
The C take exists anyway, once, on 1B only, because binding two *identical*
images as first and last frame cannot by itself distinguish "the anchor held the
composition" from "the model ignored a redundant tag" - one probe with a
genuinely different last frame is what makes the B result readable.

Prompts are child-explicit on purpose: Phases 0.5-0.7 measured that naming
children is clear for everything except children alone in a police vehicle, and
this is a living room.  Wardrobe comes from asset-bible/manifests/scene-01.json;
the "do not invent" clauses are stated as negatives because the prompt is the
only place the model reads them.

Usage:
    python scripts/video/run_scene01_first_last.py <TAKE> <workdir>

    TAKE is one of: 1BA 1BB 1BC 1DA 1DB 1DC 1FA 1FB 1FC 1HA 1HB 1HC

<workdir>/in must hold the locked panels (and, for a C take, the mapped end
panel):
    rclone copy r2:rex-assets/storyboards/v4/scene-01/ <workdir>/in/ \
        --include 'scene-01-1?-start.png' --include 'scene-01-panel-0?-end.png'
"""

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from video.omni_flash import OmniFlashGenerator  # noqa: E402


# --- camera clauses, verbatim from run_scene01_1A_720p.py so the numbers in
# --- this task and #340 are comparable --------------------------------------

AUDIO = "No dialogue. No music. No sound effects. Silent."

PUSH_IN = "Camera only: a slow, gentle push-in. "

HELD = (
    "Camera: hold this framing. No push-in, no zoom, no pan, no reframe - only a "
    "very slight handheld drift, as if the camera is breathing. "
)


# --- per-shot staging -------------------------------------------------------
# Each block: who is in frame and where, what they are wearing, what the props
# are doing, then the negatives.  Read off the shot's own locked v4 panel and
# cross-checked against that shot's manifest entry.

STAGING = {
    # Manifest 1B: "Medium shot on Leo, STATIC with slight PUSH, 6s.
    #               Leo center, cross-legged on couch."
    "1B": (
        "Hold this exact composition, framing and art style. "
        "Leo, a 5-year-old boy with tousled blond hair and blue eyes, in green "
        "dinosaur-pattern pajamas, stays sitting cross-legged in the middle of "
        "the grey couch, hugging his small green plush dinosaur. He keeps "
        "watching the television off-screen; the TV glow stays on his face. "
        "His big sister Mia, an 8-year-old girl with dark curly hair in a "
        "magenta star-print t-shirt and blue jeans, stays partly out of frame at "
        "the extreme left edge. The plastic toy dinosaurs stay exactly where "
        "they are on the couch: the brown T-Rex on the cushion to his left, the "
        "reddish Triceratops and the pterodactyl on the cushion to his right. "
        "The bookshelf, the lit floor lamp and the armchair stay in the "
        "background at screen left. Rain and a stormy sky with lightning "
        "continue outside the windows behind the couch. "
        "Leo does not get off the couch and does not stand up. Leo stays in his "
        "dinosaur pajamas and does not change clothes. Mia does not walk into "
        "the frame. No new characters enter. The television is never visible in "
        "frame. Nothing new appears on the couch or the windowsill. "
    ),
    # Manifest 1D: "Two-shot Gabe/Nina, STATIC with occasional REFRAMES, 45s.
    #               Medium shot from waist up."
    "1D": (
        "Hold this exact composition, framing and art style. "
        "Gabe, the dad, dark brown hair, black-framed glasses and light stubble, "
        "in a black tuxedo with a white shirt and black bow tie, stays standing "
        "left of centre looking down at the wristwatch on his wrist. His wife "
        "Nina, auburn wavy shoulder-length hair, in an elegant sleeveless black "
        "formal dress, stays standing at his right, turned towards him. Neither "
        "of them moves out of the frame or swaps sides. "
        "In the background at screen left their two kids stay seated together on "
        "the grey couch: Mia, an 8-year-old girl with dark curly hair in a "
        "magenta star-print t-shirt and blue jeans holding an open book, and her "
        "little brother Leo, a 5-year-old boy in green dinosaur-pattern pajamas "
        "holding a green plush dinosaur. In the background at screen right their "
        "teenage babysitter Jenny, dark brown hair in a high ponytail and a grey "
        "long-sleeved top, stays sitting in the armchair looking down at her "
        "phone. Rain and a stormy sky with lightning continue outside the "
        "windows at the far left; the lamps stay lit. "
        "Gabe and Nina do not change places. The kids do not get off the couch "
        "and do not sit on the floor. Mia does not wear glasses. Leo stays in "
        "his dinosaur pajamas. Jenny does not put her phone down. No new "
        "characters enter. Nothing new appears on the furniture. "
    ),
    # Manifest 1F: "Close-up insert on TV, STATIC, 4s. TV screen fills most of
    #               frame."  No characters in the manifest entry.
    "1F": (
        "Hold this exact composition, framing and art style. "
        "The old boxy wood-cabinet television keeps filling most of the frame, "
        "its rounded glass screen at centre-left and its two round dials and "
        "speaker grille on the wood panel at its right. On the screen a "
        "colourful cartoon keeps playing, smeared and broken up by rolling "
        "horizontal scan lines and static, with the blue electrical flash "
        "flickering across the middle of the picture. Behind the set at screen "
        "right, rain and lightning continue outside the window, the table lamp "
        "stays lit, and the knitted throw stays over the arm of the chair in the "
        "bottom right corner. "
        "The television stays an old boxy cabinet set and never becomes a flat "
        "panel screen. No people enter the frame; there are no characters in "
        "this shot. Nothing new appears in the room. "
    ),
    # Manifest 1H: "Close-up on Mia, SLOW PUSH, 20s. Mia center frame, looking
    #               up at parents off-screen. Emotional anchor of the scene."
    "1H": (
        "Hold this exact composition, framing and art style. "
        "Mia, an 8-year-old girl with voluminous dark brown curly hair worn down, "
        "big brown eyes and freckles, in a magenta star-print t-shirt and blue "
        "jeans, stays seated in the centre of the frame looking up and to her "
        "left at her parents off-screen. Her expression stays worried and "
        "hopeful. Her hair stays curly and worn down. "
        "The warm table lamp stays lit at screen left with the framed picture on "
        "the wall behind it, and rain and a bright lightning flash continue "
        "outside the window at screen right. The soft out-of-focus foreground "
        "shapes at the extreme left and right edges of the frame stay exactly "
        "where they are and stay out of focus. "
        "Mia stays in the magenta t-shirt and does not change clothes. Mia's "
        "hair does not become straight and is not tied back. Mia does not wear "
        "glasses. Mia does not stand up or leave the frame. No new characters "
        "enter and nothing in the foreground comes into focus. "
    ),
}

# Camera clause per shot, taken from that shot's own manifest "camera" field.
#   1B  "STATIC with slight PUSH"          -> push-in
#   1D  "STATIC with occasional REFRAMES"  -> held.  A reframe is exactly what
#       the gate cannot tell apart from drift (VIDEO-GATE limit 2), and #340
#       measured that the held clause is the one that keeps the plate.
#   1F  "STATIC"                           -> held
#   1H  "SLOW PUSH"                        -> push-in
CAMERA = {"1B": PUSH_IN, "1D": HELD, "1F": HELD, "1H": PUSH_IN}

# Derived in this task and stated in docs/research/scene01-first-last-frame.md:
# the panel numbers run in shot order, 01->1A through 09->1I.
END_PANEL = {"1B": "scene-01-panel-02-end.png",
             "1D": "scene-01-panel-04-end.png",
             "1F": "scene-01-panel-06-end.png",
             "1H": "scene-01-panel-08-end.png"}

SHOTS = ["1B", "1D", "1F", "1H"]
RESOLUTION = "720p"
DURATION = 5

# Hard cap from the task.  Checked against the running total in the sidecars
# before every call, so a run that would breach it never leaves the machine.
HARD_CAP_USD = 4.00


def prompt_for(shot: str) -> str:
    """The prompt for a shot.  Identical across that shot's A, B and C takes."""
    return STAGING[shot] + CAMERA[shot] + AUDIO


def frames_for(shot: str, kind: str, indir: Path) -> tuple[Path, Path | None]:
    """(first_frame, last_frame) for one take."""
    start = indir / f"scene-01-{shot}-start.png"
    if kind == "A":
        return start, None
    if kind == "B":
        return start, start
    if kind == "C":
        return start, indir / END_PANEL[shot]
    raise ValueError(f"unknown take kind {kind!r}")


def spent_so_far(outdir: Path) -> float:
    total = 0.0
    for sidecar in outdir.glob("*.json"):
        try:
            total += float(json.loads(sidecar.read_text()).get("billed_usd") or 0.0)
        except (ValueError, OSError):
            pass
    return round(total, 6)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    take, workdir = sys.argv[1], Path(sys.argv[2])
    shot, kind = take[:2], take[2:]
    if shot not in SHOTS or kind not in ("A", "B", "C"):
        print(__doc__)
        return 2

    indir, outdir = workdir / "in", workdir / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    first, last = frames_for(shot, kind, indir)
    for p in [first] + ([last] if last else []):
        if not p.exists():
            print(f"ERROR: panel not found at {p}")
            return 2

    prompt = prompt_for(shot)
    gen = OmniFlashGenerator()
    estimate = gen.estimate_cost(DURATION, RESOLUTION)
    already = spent_so_far(outdir)
    if already + estimate > HARD_CAP_USD:
        print(
            f"REFUSING {take}: ${already:.4f} already billed + ~${estimate:.4f} "
            f"estimated would breach the ${HARD_CAP_USD:.2f} cap."
        )
        return 1
    print(
        f"[{take}] shot {shot} {DURATION}s @ {RESOLUTION}  est ${estimate:.4f}  "
        f"(billed so far ${already:.4f}, cap ${HARD_CAP_USD:.2f})\n"
        f"        first={first.name}  last={last.name if last else '-'}"
    )

    out_mp4 = outdir / f"{take}_raw.mp4"
    sidecar = outdir / f"{take}.json"
    record = {
        "take": take,
        "shot": shot,
        "kind": kind,
        "task": "image_to_video",
        "resolution": RESOLUTION,
        "duration_seconds": DURATION,
        "prompt": prompt,
        "first_frame": str(first),
        "last_frame": str(last) if last else None,
        "estimate_usd": estimate,
    }
    try:
        res = gen.generate(
            prompt,
            str(out_mp4),
            duration_seconds=DURATION,
            aspect_ratio="16:9",
            resolution=RESOLUTION,
            task="image_to_video",
            first_frame=str(first),
            last_frame=str(last) if last else None,
        )
        record.update(
            status="ok",
            file=res.file_path,
            billed_usd=res.estimated_cost,
            generation_time_seconds=res.generation_time_seconds,
            metadata=res.metadata,
        )
        print(f"[{take}] OK  billed=${res.estimated_cost:.4f}  {res.file_path}")
    except Exception as exc:  # a hard failure IS a result - record it verbatim
        record.update(
            status="failed",
            error_type=type(exc).__name__,
            error=str(exc),
            traceback=traceback.format_exc(),
            billed_usd=0.0,
        )
        print(f"[{take}] FAILED {type(exc).__name__}: {exc}")

    sidecar.write_text(json.dumps(record, indent=2, default=str))
    print(f"[{take}] total billed now ${spent_so_far(outdir):.4f}")
    return 0 if record["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
