#!/usr/bin/env python3
"""Scene 1 continuity gate for STILL frames.

Scores one image against the locked Scene 1 living-room plate and the locked
Scene 1 manifest from the Asset Bible.  OpenCV only - no vision API, no network,
$0.00 per call.  This is the gate CLAUDE.md's "Validation Gates" rule asks for
before anything is generated from an artifact.

What it actually measures
-------------------------
Four checks, each PASS / FAIL / n/a:

  staging_orientation  The locked staging puts the TV screen-left and Jenny's
                       armchair screen-right.  The frame's left band is matched
                       against the plate's TV band and its right band against
                       the plate's chair band, then the same comparison is run
                       crossed.  If crossed wins, the room is mirrored.
  layout_match         Mean hue/saturation-histogram correlation across the
                       plate's named regions (tv, lamp, couch, window, kitchen,
                       chair, jenny, floor).  Catches "this is a different room".
  couch_occupancy      Fraction of the couch band that is NOT couch upholstery,
                       i.e. how much of the couch is occupied, as a ratio of the
                       plate's own occupancy.  Catches kids added or vanished.
  wardrobe             Per-character costume-colour coverage relative to the
                       plate, for the characters the manifest says are in this
                       shot.  Characters with no swatch in the plate spec are
                       reported n/a, never silently passed.

Scope: the plate is a WIDE establishing frame, so the three geometry checks only
apply to a wide shot.  When --shot names a manifest entry whose camera line is a
close-up or a medium, they report n/a - and if NOTHING was measured the verdict
is INCONCLUSIVE, not PASS, because a clip nobody looked at is not a cleared clip.

What it does NOT measure: character identity.  A colour histogram cannot tell
Mia from another dark-haired girl in a magenta top.  Identity is the paid vision
validator's job (`scripts/validate/shot_validator.py`).  This gate is the cheap
geometric pre-filter that runs on every frame.

Paths
-----
Plate, plate spec and bible are resolved in this order, first hit wins:
    1. CLI flag            --plate / --plate-spec / --bible
    2. Environment         CONTINUITY_PLATE / CONTINUITY_PLATE_SPEC / CONTINUITY_BIBLE
    3. Repo default        the pinned copies next to this file

(Historically these were hardcoded to /workspace/... absolute paths, which only
resolved inside one sandbox.  The repo defaults below replace them.)

Usage
-----
    python check.py FRAME.png
    python check.py FRAME.png --shot 1A --json
    python check.py FRAME.png --plate /path/to/plate.jpg --verbose

Exit code 0 if the frame passes, 1 if it fails or is INCONCLUSIVE (see
--allow-inconclusive), 2 on a usage/IO error.

For video, use check_video.py, which wraps this module.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent

DEFAULT_PLATE = HERE / "plate" / "scene-01-1A-plate.jpg"
DEFAULT_PLATE_SPEC = HERE / "scene-01-plate.json"
DEFAULT_BIBLE = HERE / "bible" / "scene-01.json"

#: Every frame and the plate are resized to this width before comparison, so a
#: 360p test render and a 1080p hero render score the same way.
WORK_WIDTH = 512

PASS, FAIL, NA = "PASS", "FAIL", "n/a"


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def resolve_path(cli: str | None, env_var: str, default: Path) -> Path:
    """First of: CLI flag, environment variable, repo default."""
    for candidate in (cli, os.environ.get(env_var)):
        if candidate:
            return Path(candidate).expanduser()
    return default


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass
class Check:
    """One measurement and its verdict."""

    name: str
    status: str  # PASS | FAIL | n/a
    score: float | None
    threshold: float | None
    detail: str

    @property
    def failed(self) -> bool:
        return self.status == FAIL

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "score": None if self.score is None else round(float(self.score), 4),
            "threshold": self.threshold,
            "detail": self.detail,
        }


@dataclass
class FrameResult:
    """The verdict for a single frame."""

    source: str
    shot: str | None
    checks: list[Check] = field(default_factory=list)

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if c.failed]

    @property
    def applied(self) -> list[Check]:
        """Checks that actually ran. The rest were n/a and prove nothing."""
        return [c for c in self.checks if c.status != NA]

    @property
    def conclusive(self) -> bool:
        """False when every check was n/a - a verdict of PASS would be vacuous."""
        return bool(self.applied)

    @property
    def passed(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "shot": self.shot,
            "passed": self.passed,
            "conclusive": self.conclusive,
            "failed_checks": [c.name for c in self.failures],
            "skipped_checks": [c.name for c in self.checks if c.status == NA],
            "checks": [c.to_dict() for c in self.checks],
        }


# ---------------------------------------------------------------------------
# Image primitives
# ---------------------------------------------------------------------------


def load_bgr(src: str | Path | np.ndarray) -> np.ndarray:
    """Accept a path or an already-decoded BGR array (check_video passes arrays)."""
    if isinstance(src, np.ndarray):
        img = src
    else:
        img = cv2.imread(str(src), cv2.IMREAD_COLOR)
        if img is None:
            raise OSError(f"could not read image: {src}")
    return img


def to_working_size(img: np.ndarray) -> np.ndarray:
    """Normalise to a fixed width, keeping aspect, so scores are resolution-free."""
    h, w = img.shape[:2]
    if w == WORK_WIDTH:
        return img
    return cv2.resize(
        img, (WORK_WIDTH, max(1, round(h * WORK_WIDTH / w))), interpolation=cv2.INTER_AREA
    )


def crop(img: np.ndarray, box: Sequence[float]) -> np.ndarray:
    """Crop a normalised [x0, y0, x1, y1] box, clamped to at least 1px each way."""
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box
    a, b = int(round(x0 * w)), int(round(y0 * h))
    c, d = int(round(x1 * w)), int(round(y1 * h))
    c, d = max(c, a + 1), max(d, b + 1)
    return img[max(0, b) : min(h, d), max(0, a) : min(w, c)]


def hs_histogram(patch: np.ndarray) -> np.ndarray:
    """Hue x saturation histogram, min-max normalised. The region signature."""
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [18, 8], [0, 180, 0, 256])
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist


def hist_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Correlation of two signatures, clipped to [0, 1]."""
    return float(max(0.0, cv2.compareHist(a, b, cv2.HISTCMP_CORREL)))


def mean_lab(patch: np.ndarray) -> np.ndarray:
    """Mean CIELAB colour of a patch, as float. Used for swatch matching."""
    return cv2.cvtColor(patch, cv2.COLOR_BGR2LAB).reshape(-1, 3).mean(axis=0).astype(np.float64)


def lab_coverage(img: np.ndarray, reference: np.ndarray, delta_e: float) -> float:
    """Fraction of pixels within `delta_e` of `reference` in Lab space.

    A crude but stable stand-in for CIE76: OpenCV's 8-bit Lab puts L on 0..255
    and a/b on 0..255 with a 128 offset, so distances are consistently scaled
    even if they are not true delta-E units. The threshold is tuned in those
    units, which is why it lives in the plate spec rather than being a constant.
    """
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    dist = np.linalg.norm(lab - reference.astype(np.float32), axis=2)
    return float((dist <= delta_e).mean())


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------


class ContinuityGate:
    """Scores frames against one locked plate.

    Construct once and reuse - the plate signatures are computed in __init__, so
    scoring N video frames costs one plate decode, not N.
    """

    def __init__(
        self,
        plate: str | Path | None = None,
        spec: str | Path | None = None,
        bible: str | Path | None = None,
        shot: str | None = None,
    ) -> None:
        self.plate_path = resolve_path(plate, "CONTINUITY_PLATE", DEFAULT_PLATE)
        self.spec_path = resolve_path(spec, "CONTINUITY_PLATE_SPEC", DEFAULT_PLATE_SPEC)
        self.bible_path = resolve_path(bible, "CONTINUITY_BIBLE", DEFAULT_BIBLE)
        self.shot = shot

        if not self.plate_path.exists():
            raise OSError(
                f"locked plate not found: {self.plate_path}\n"
                "Fetch it with:  rclone copy "
                "r2:rex-assets/storyboards/v4/scene-01/scene-01-1A-start.png <dir>/\n"
                "or point --plate / $CONTINUITY_PLATE at your own copy."
            )
        self.spec = json.loads(self.spec_path.read_text())
        self.thresholds = self.spec["thresholds"]

        self.plate = to_working_size(load_bgr(self.plate_path))
        self.plate_mirrored = cv2.flip(self.plate, 1)

        self._region_sig = {
            name: hs_histogram(crop(self.plate, box))
            for name, box in self.spec["regions"].items()
        }
        self._mirror_sig = {
            name: hs_histogram(crop(self.plate_mirrored, box))
            for name, box in self.spec["regions"].items()
        }
        self._band_sig = {
            name: hs_histogram(crop(self.plate, box)) for name, box in self.spec["bands"].items()
        }
        self._swatch_lab = {
            name: mean_lab(crop(self.plate, box))
            for name, box in self.spec["swatches"].items()
        }
        self._plate_couch_occupancy = self._couch_occupancy(self.plate)
        self._plate_wardrobe = {
            name: self._swatch_coverage(self.plate, name) for name in self._swatch_lab
        }
        # A costume colour that already covers most of the plate is measuring the
        # room's lighting, not the costume, so it cannot tell us the character is
        # there. Disqualify those swatches up front rather than reporting a
        # confident ratio built on nothing.
        cap = self.thresholds["swatch_max_plate_coverage"]
        self.degenerate_swatches = {
            name for name, coverage in self._plate_wardrobe.items() if coverage > cap
        }

        self.manifest = self._load_manifest()
        self.framing = (self.manifest or {}).get("camera", "")
        # With no --shot we cannot know the framing, so assume the frame is
        # meant to hold the plate and run every check.
        self.covers_plate = self.manifest is None or "wide" in self.framing.lower()

    # -- bible ------------------------------------------------------------

    def _load_manifest(self) -> dict[str, Any] | None:
        """The manifest entry for --shot, or None if no shot was named."""
        if self.shot is None:
            return None
        if not self.bible_path.exists():
            raise OSError(
                f"bible manifest not found: {self.bible_path}\n"
                "Fetch it with:  rclone copy "
                "r2:rex-assets/asset-bible/manifests/scene-01.json <dir>/\n"
                "or point --bible / $CONTINUITY_BIBLE at your own copy."
            )
        entries = json.loads(self.bible_path.read_text())
        for entry in entries:
            if entry.get("shot_id") == self.shot:
                return entry
        known = ", ".join(e.get("shot_id", "?") for e in entries)
        raise KeyError(f"shot {self.shot!r} not in {self.bible_path} (have: {known})")

    # -- measurements -----------------------------------------------------

    def _couch_occupancy(self, img: np.ndarray) -> float:
        """Share of the couch band that is not bare upholstery."""
        patch = crop(img, self.spec["regions"]["couch"])
        reference = self._swatch_lab.get("couch_upholstery")
        if reference is None:  # spec without a couch swatch: nothing to measure
            return float("nan")
        bare = lab_coverage(patch, reference, self.thresholds["couch_delta_e"])
        return 1.0 - bare

    def _swatch_coverage(self, img: np.ndarray, swatch: str) -> float:
        """Share of the whole frame close to a costume's plate colour."""
        return lab_coverage(img, self._swatch_lab[swatch], self.thresholds["swatch_delta_e"])

    #: Manifest wardrobe notes that mean "present, but small in frame".
    MINOR_ROLE_HINTS = ("background", "partial", "ots", "off-screen", "frame edge", "blurred")

    @classmethod
    def _is_minor(cls, note: str) -> bool:
        note = note.lower()
        return any(hint in note for hint in cls.MINOR_ROLE_HINTS)

    # -- checks -----------------------------------------------------------

    def _check_staging(self, frame: np.ndarray, layout: Check) -> Check:
        """Is Jenny's armchair still screen-right of the TV?

        Straight: frame-left vs plate-left, frame-right vs plate-right.
        Crossed:  frame-left vs plate-right, frame-right vs plate-left.
        A mirrored room scores better crossed.

        Only meaningful once we already believe this is the plate's room. When
        layout_match has failed, the two bands match the plate about equally
        badly in both directions and the winner is noise - measured on the
        veo3-v4 clips, where a correctly staged but entirely different living
        room scored straight=0.582 / crossed=0.597 and was called mirrored. So
        a failed layout downgrades this to n/a rather than stacking a second,
        bogus reason onto one real break.
        """
        if layout.failed:
            return Check(
                name="staging_orientation",
                status=NA,
                score=None,
                threshold=None,
                detail="layout_match failed - not the plate's room, so left/right "
                "band comparison carries no signal",
            )
        left = hs_histogram(crop(frame, self.spec["bands"]["left"]))
        right = hs_histogram(crop(frame, self.spec["bands"]["right"]))
        straight = (
            hist_similarity(left, self._band_sig["left"])
            + hist_similarity(right, self._band_sig["right"])
        ) / 2
        crossed = (
            hist_similarity(left, self._band_sig["right"])
            + hist_similarity(right, self._band_sig["left"])
        ) / 2
        margin = self.thresholds["staging_margin"]
        gap = straight - crossed
        ok = gap >= margin
        return Check(
            name="staging_orientation",
            status=PASS if ok else FAIL,
            score=gap,
            threshold=margin,
            detail=(
                f"straight={straight:.3f} crossed={crossed:.3f}; "
                + (
                    "TV band left / chair band right, as locked"
                    if ok
                    else "left and right bands match the plate better SWAPPED - "
                    "room reads as mirrored (chair no longer screen-right of TV)"
                )
            ),
        )

    def _check_layout(self, frame: np.ndarray) -> Check:
        per_region = {
            name: hist_similarity(hs_histogram(crop(frame, box)), self._region_sig[name])
            for name, box in self.spec["regions"].items()
        }
        score = float(np.mean(list(per_region.values())))
        limit = self.thresholds["layout_match"]
        worst = sorted(per_region.items(), key=lambda kv: kv[1])[:3]
        return Check(
            name="layout_match",
            status=PASS if score >= limit else FAIL,
            score=score,
            threshold=limit,
            detail="weakest regions: "
            + ", ".join(f"{n}={v:.2f}" for n, v in worst),
        )

    def _check_couch(self, frame: np.ndarray) -> Check:
        plate_value = self._plate_couch_occupancy
        if not np.isfinite(plate_value) or plate_value <= 0:
            return Check("couch_occupancy", NA, None, None, "no couch swatch in plate spec")
        value = self._couch_occupancy(frame)
        ratio = value / plate_value
        lo = self.thresholds["couch_occupancy_min_ratio"]
        hi = self.thresholds["couch_occupancy_max_ratio"]
        if ratio < lo:
            detail = "couch reads emptier than the plate - occupants may have vanished"
            status = FAIL
        elif ratio > hi:
            detail = "couch reads far busier than the plate - extra bodies or a different couch"
            status = FAIL
        else:
            detail = "occupancy consistent with the plate"
            status = PASS
        return Check(
            name="couch_occupancy",
            status=status,
            score=ratio,
            threshold=lo,
            detail=f"{detail} (frame={value:.3f} plate={plate_value:.3f} ratio={ratio:.2f}, "
            f"allowed {lo:.2f}-{hi:.2f})",
        )

    def _check_wardrobe(self, frame: np.ndarray) -> Check:
        """Costume-colour coverage for the characters this shot is meant to contain."""
        mapping = self.spec.get("wardrobe", {})
        if self.manifest is None:
            expected = list(mapping)
        else:
            expected = list(self.manifest.get("characters", []))
        if not expected:
            return Check("wardrobe", NA, None, None, "manifest lists no characters for this shot")

        limit = self.thresholds["wardrobe_min_ratio"]
        missing, thin, unchecked = [], [], []
        ratios: list[float] = []
        wardrobe_notes = (self.manifest or {}).get("wardrobe", {})
        for character in expected:
            swatch = mapping.get(character)
            if swatch is None or swatch not in self._swatch_lab:
                unchecked.append(character)
                continue
            plate_value = self._plate_wardrobe[swatch]
            if plate_value <= 0 or swatch in self.degenerate_swatches:
                unchecked.append(character)
                continue
            # Coverage ratios are calibrated against the plate, where everyone
            # is at wide-establishing scale. The manifest flags characters the
            # shot deliberately pushes to the background or the frame edge;
            # holding those to plate-scale coverage just invents failures.
            if self._is_minor(wardrobe_notes.get(character, "")):
                unchecked.append(f"{character} (background per manifest)")
                continue
            ratio = self._swatch_coverage(frame, swatch) / plate_value
            ratios.append(ratio)
            if ratio < limit:
                (missing if ratio < limit / 2 else thin).append(f"{character}={ratio:.2f}")

        if not ratios:
            return Check(
                "wardrobe", NA, None, None,
                "nothing measurable here - " + ", ".join(unchecked),
            )

        score = float(np.min(ratios))
        bits = []
        if missing:
            bits.append("absent: " + ", ".join(missing))
        if thin:
            bits.append("thin: " + ", ".join(thin))
        if unchecked:
            bits.append("no swatch: " + ", ".join(unchecked))
        if not bits:
            bits.append(f"all {len(ratios)} checkable costumes present")
        return Check(
            name="wardrobe",
            status=FAIL if (missing or thin) else PASS,
            score=score,
            threshold=limit,
            detail="; ".join(bits),
        )

    # -- entry point ------------------------------------------------------

    def check_image(self, src: str | Path | np.ndarray, label: str | None = None) -> FrameResult:
        """Score one frame. `src` may be a path or a decoded BGR array."""
        frame = to_working_size(load_bgr(src))
        source = label if label is not None else (src if isinstance(src, str) else str(src))
        if isinstance(src, np.ndarray) and label is None:
            source = "<array>"

        # The plate is a WIDE establishing frame. A close-up or a medium simply
        # does not contain the TV, the armchair or the couch band, so scoring it
        # on plate geometry manufactures failures that say nothing about the
        # shot. The bible already records the intended framing, so use it.
        if not self.covers_plate:
            reason = (
                f"shot {self.shot} is not a wide: manifest camera reads "
                f"{self.framing!r} - the locked plate is not in frame"
            )
            geometry = [
                Check(name, NA, None, None, reason)
                for name in ("staging_orientation", "layout_match", "couch_occupancy")
            ]
        else:
            layout = self._check_layout(frame)
            geometry = [self._check_staging(frame, layout), layout, self._check_couch(frame)]

        return FrameResult(
            source=str(source),
            shot=self.shot,
            checks=[*geometry, self._check_wardrobe(frame)],
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def add_gate_arguments(parser: argparse.ArgumentParser) -> None:
    """Flags shared with check_video.py, so both tools resolve paths identically."""
    parser.add_argument("--plate", help=f"locked plate image (default: {DEFAULT_PLATE})")
    parser.add_argument("--plate-spec", help=f"plate regions/thresholds JSON (default: {DEFAULT_PLATE_SPEC})")
    parser.add_argument("--bible", help=f"Scene 1 manifest JSON (default: {DEFAULT_BIBLE})")
    parser.add_argument("--shot", help="manifest shot id, e.g. 1A. Enables the wardrobe check.")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")


def frame_verdict(result: FrameResult) -> str:
    if not result.passed:
        return FAIL.ljust(12)
    return (PASS if result.conclusive else "INCONCLUSIVE").ljust(12)


def format_frame(result: FrameResult, verbose: bool = False) -> str:
    lines = [f"{frame_verdict(result)}  {result.source}"]
    for check in result.checks:
        if not verbose and check.status == PASS:
            continue
        if not verbose and check.status == NA and result.conclusive:
            continue
        score = "    -" if check.score is None else f"{check.score:7.3f}"
        lines.append(f"    [{check.status:4}] {check.name:20} {score}  {check.detail}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score a still frame against the locked Scene 1 plate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("frame", help="image to score")
    add_gate_arguments(parser)
    parser.add_argument(
        "--allow-inconclusive", action="store_true",
        help="exit 0 when no check could be applied (default: exit 1)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="show passing checks too")
    args = parser.parse_args(argv)

    try:
        gate = ContinuityGate(args.plate, args.plate_spec, args.bible, args.shot)
        result = gate.check_image(args.frame)
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_frame(result, args.verbose))

    if not result.passed:
        return 1
    return 0 if (result.conclusive or args.allow_inconclusive) else 1


if __name__ == "__main__":
    sys.exit(main())
