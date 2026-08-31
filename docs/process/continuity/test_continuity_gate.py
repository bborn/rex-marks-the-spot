#!/usr/bin/env python3
"""Tests for the Scene 1 continuity gate (check.py and check_video.py).

Offline and free: every fixture is either the pinned plate that ships next to
the code or something synthesised from it with ffmpeg. Nothing here touches R2,
a vision API or the network.

The assertions that matter are the adversarial ones - mirror the plate, empty
the couch, recolour a costume - because a gate that only ever sees good frames
proves nothing.

Run:  cd docs/process/continuity && python -m pytest test_continuity_gate.py -v
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check  # noqa: E402
import check_video  # noqa: E402
from check import ContinuityGate  # noqa: E402

HERE = Path(__file__).resolve().parent
PLATE = HERE / "plate" / "scene-01-1A-plate.jpg"
BIBLE = HERE / "bible" / "scene-01.json"
SPEC = json.loads((HERE / "scene-01-plate.json").read_text())
SHOTS = list(SPEC["shots"])
PLATES = {s: HERE / SPEC["shots"][s]["plate"] for s in SHOTS}

needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not on PATH",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gate():
    return ContinuityGate(shot="1A")


@pytest.fixture(scope="module")
def plate_bgr():
    img = cv2.imread(str(PLATE), cv2.IMREAD_COLOR)
    assert img is not None, f"pinned plate missing or unreadable: {PLATE}"
    return img


def _status(result, name):
    return next(c for c in result.checks if c.name == name).status


def _write_clip(path: Path, image: np.ndarray, seconds: float = 2.0) -> Path:
    """A still held for `seconds` - a clip whose every frame is `image`."""
    png = path.with_suffix(".png")
    cv2.imwrite(str(png), image)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-loop", "1", "-i", str(png),
         "-t", str(seconds), "-r", "12", "-pix_fmt", "yuv420p", "-y", str(path)],
        check=True, capture_output=True,
    )
    return path


# ---------------------------------------------------------------------------
# The still gate - the part check_video.py is not allowed to reimplement
# ---------------------------------------------------------------------------


class TestStillGate:
    def test_the_plate_passes_its_own_gate(self, gate, plate_bgr):
        result = gate.check_image(plate_bgr, label="plate")
        assert result.passed, [c.to_dict() for c in result.failures]

    def test_mirrored_room_fails_staging(self, gate, plate_bgr):
        """The locked staging is TV screen-left, Jenny's chair screen-right."""
        result = gate.check_image(cv2.flip(plate_bgr, 1), label="mirrored")
        assert _status(result, "staging_orientation") == check.FAIL
        assert not result.passed

    def test_emptied_couch_fails_occupancy(self, gate, plate_bgr):
        """Paint the couch band in its own upholstery colour: nobody is on it."""
        frame = check.to_working_size(plate_bgr).copy()
        h, w = frame.shape[:2]
        x0, y0, x1, y1 = gate.spec["regions"]["couch"]
        upholstery = check.crop(
            check.to_working_size(plate_bgr), gate.spec["swatches"]["couch_upholstery"]
        ).reshape(-1, 3).mean(axis=0)
        frame[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = upholstery
        result = gate.check_image(frame, label="empty couch")
        assert _status(result, "couch_occupancy") == check.FAIL

    def test_unrelated_image_fails_layout(self, gate):
        rng = np.random.default_rng(0)
        noise = rng.integers(0, 255, (768, 1376, 3), dtype=np.uint8)
        result = gate.check_image(noise, label="noise")
        assert _status(result, "layout_match") == check.FAIL
        assert not result.passed

    def test_resolution_does_not_change_the_verdict(self, gate, plate_bgr):
        """A 360p test render and a 1080p render of the same frame score alike."""
        small = cv2.resize(plate_bgr, (640, 360), interpolation=cv2.INTER_AREA)
        big = cv2.resize(plate_bgr, (1920, 1080), interpolation=cv2.INTER_CUBIC)
        scores = []
        for img in (small, big):
            layout = next(
                c for c in gate.check_image(img).checks if c.name == "layout_match"
            )
            scores.append(layout.score)
        assert scores[0] == pytest.approx(scores[1], abs=0.05)


class TestWardrobe:
    def test_degenerate_swatches_are_reported_not_passed(self, gate):
        """Black formalwear in a dim room is unmeasurable - say so, don't pass it."""
        assert gate.degenerate_swatches, "expected some swatch to be disqualified"
        result = gate.check_image(cv2.imread(str(PLATE)), label="plate")
        wardrobe = next(c for c in result.checks if c.name == "wardrobe")
        assert "no swatch" in wardrobe.detail

    def test_missing_costume_colour_fails(self, gate, plate_bgr):
        """Desaturate the frame: Mia's magenta and Leo's green stop existing."""
        grey = cv2.cvtColor(cv2.cvtColor(plate_bgr, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        result = gate.check_image(grey, label="greyscale")
        assert _status(result, "wardrobe") == check.FAIL

    def test_shot_selects_the_manifest_entry(self):
        g = ContinuityGate(shot="1E")
        assert g.manifest["characters"] == ["Jenny"]

    def test_unknown_shot_is_an_error(self):
        with pytest.raises(KeyError):
            ContinuityGate(shot="9Z")

    def test_frame_edge_characters_are_not_held_to_plate_scale(self):
        """1B's manifest marks Mia '(partial frame edge)'. Holding a sliver at
        the edge of frame to full costume coverage manufactures a failure."""
        medium = ContinuityGate(shot="1B")
        wardrobe = next(
            c for c in medium.check_image(cv2.imread(str(medium.plate_path))).checks
            if c.name == "wardrobe"
        )
        assert wardrobe.status == check.PASS  # Leo carries it
        assert "background per manifest" in wardrobe.detail  # Mia does not

    def test_own_plate_can_opt_in_to_measuring_background_characters(self):
        """1D marks Mia, Leo and Jenny background - but 1D's plate IS the
        two-shot, so background scale there is the correct reference and the
        entry says background_characters: measure."""
        two_shot = ContinuityGate(shot="1D")
        assert two_shot.measure_background
        wardrobe = next(
            c for c in two_shot.check_image(cv2.imread(str(two_shot.plate_path))).checks
            if c.name == "wardrobe"
        )
        assert wardrobe.status == check.PASS
        assert "background per manifest" not in wardrobe.detail

    def test_a_swatch_too_small_on_the_plate_is_disqualified(self, tmp_path):
        """The floor at the other end of swatch_max_plate_coverage: a colour
        that barely exists on the plate gives a ratio made of noise."""
        spec = _spec_copy()
        spec["thresholds"]["swatch_min_plate_coverage"] = 0.01
        g = ContinuityGate(spec=_write_spec(spec, tmp_path, "floored.json"), shot="1A")
        # Mia's magenta covers 0.16% of the 1A plate - under a 1% floor.
        assert "mia_top" in g.degenerate_swatches


def _spec_copy() -> dict:
    """The real plate spec, with plate paths made absolute.

    A relative `plate` resolves next to the spec that names it, which is what
    keeps the repo copy self-contained - but a copy written into tmp_path would
    then look for its plates there.
    """
    spec = json.loads((HERE / "scene-01-plate.json").read_text())
    for entry in spec["shots"].values():
        entry["plate"] = str(HERE / entry["plate"])
    return spec


def _write_spec(spec: dict, tmp_path: Path, name: str) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(spec))
    return str(path)


def _spec_without(shot: str, tmp_path: Path) -> str:
    """The real plate spec with one shot's entry removed, to exercise the
    borrowed-plate fallback that every shot took before per-shot plates."""
    spec = _spec_copy()
    spec["shots"].pop(shot)
    return _write_spec(spec, tmp_path, f"no-{shot}.json")


class TestScope:
    """A shot is scored on its own plate. Without one, the old rule applies:
    the 1A wide is only in frame for a wide shot, so say so rather than
    manufacturing a failure."""

    def test_wide_shot_runs_the_geometry_checks(self):
        assert ContinuityGate(shot="1A").covers_plate

    def test_a_close_up_with_its_own_plate_holds_it(self):
        gate = ContinuityGate(shot="1H")
        assert gate.covers_plate
        assert not gate.plate_is_borrowed

    def test_no_shot_assumes_the_frame_should_hold_the_plate(self):
        assert ContinuityGate().covers_plate

    def test_a_close_up_on_a_borrowed_plate_does_not(self, tmp_path):
        gate = ContinuityGate(spec=_spec_without("1H", tmp_path), shot="1H")
        assert gate.plate_is_borrowed
        assert not gate.covers_plate

    def test_borrowed_plate_geometry_is_na_with_the_manifest_reason(
        self, plate_bgr, tmp_path
    ):
        gate = ContinuityGate(spec=_spec_without("1H", tmp_path), shot="1H")
        result = gate.check_image(plate_bgr)
        geometry = [c for c in result.checks if c.name != "wardrobe"]
        assert {c.status for c in geometry} == {check.NA}
        assert "not a wide" in geometry[0].detail

    def test_a_frame_with_nothing_measured_is_not_a_pass(self, plate_bgr, tmp_path):
        """1F has no characters; strip its plate entry too and nothing is left."""
        gate = ContinuityGate(spec=_spec_without("1F", tmp_path), shot="1F")
        result = gate.check_image(plate_bgr)
        assert not result.conclusive
        assert check.frame_verdict(result).strip() == "INCONCLUSIVE"
        assert "no check could be applied" in result.inconclusive_reason

    def test_staging_is_na_once_layout_says_different_room(self, gate):
        """Measured on the veo3-v4 clips: a correctly staged but entirely
        different room scored straight=0.582 / crossed=0.597 and was called
        mirrored. Below the layout threshold the comparison is noise."""
        rng = np.random.default_rng(1)
        noise = rng.integers(0, 255, (720, 1280, 3), dtype=np.uint8)
        result = gate.check_image(noise)
        assert _status(result, "layout_match") == check.FAIL
        assert _status(result, "staging_orientation") == check.NA


# ---------------------------------------------------------------------------
# Per-shot plates - one locked panel per shot, and what each one can prove
# ---------------------------------------------------------------------------


class TestPerShotPlates:
    """Every Scene 1 shot has a validated v4 panel, and that panel is its plate."""

    def test_every_manifest_shot_has_a_plate_entry(self):
        manifest = {e["shot_id"] for e in json.loads(BIBLE.read_text())}
        assert manifest == set(SHOTS)

    @pytest.mark.parametrize("shot", SHOTS)
    def test_the_pinned_plate_for_each_shot_exists(self, shot):
        assert PLATES[shot].exists(), f"missing plate for {shot}"

    @pytest.mark.parametrize("shot", SHOTS)
    def test_each_gate_loads_its_own_plate_not_the_1a_wide(self, shot):
        gate = ContinuityGate(shot=shot)
        assert gate.plate_path == PLATES[shot]
        assert not gate.plate_is_borrowed

    @pytest.mark.parametrize("shot", SHOTS)
    def test_each_plate_never_fails_its_own_gate(self, shot):
        """The plate is the definition of correct for its shot. It may come
        back INCONCLUSIVE - four shots cannot clear anything - but a FAIL would
        mean the regions in the spec do not describe the panel they name."""
        gate = ContinuityGate(shot=shot)
        result = gate.check_image(cv2.imread(str(PLATES[shot])), label=shot)
        assert result.passed, [c.to_dict() for c in result.failures]

    @pytest.mark.parametrize("shot", SHOTS)
    def test_every_plate_measures_at_least_the_minimum(self, shot):
        """A shot entry that cannot support min_applied_checks measurements is
        a plate nobody should have registered."""
        gate = ContinuityGate(shot=shot)
        result = gate.check_image(cv2.imread(str(PLATES[shot])))
        assert len(result.applied) >= gate.min_applied_checks

    def test_only_1a_and_1b_and_1d_get_a_couch_check(self):
        """A close-up has no couch band. Inventing one would measure hair
        against upholstery."""
        with_couch = {
            s for s in SHOTS
            if next(
                c for c in ContinuityGate(shot=s).check_image(
                    cv2.imread(str(PLATES[s]))
                ).checks if c.name == "couch_occupancy"
            ).status != check.NA
        }
        assert with_couch == {"1A", "1B", "1D"}

    def test_shots_whose_costumes_are_unmeasurable_say_so(self):
        """Black formalwear and grey hoodies in a dim room are most of the
        frame. Those shots report wardrobe n/a rather than a bogus pass."""
        no_wardrobe = {
            s for s in SHOTS
            if next(
                c for c in ContinuityGate(shot=s).check_image(
                    cv2.imread(str(PLATES[s]))
                ).checks if c.name == "wardrobe"
            ).status == check.NA
        }
        assert no_wardrobe == {"1C", "1E", "1F", "1G", "1I"}


@pytest.fixture(scope="module")
def leaks():
    """Shots whose gate is cleared by some OTHER shot's locked panel."""
    gates = {s: ContinuityGate(shot=s) for s in SHOTS}
    panels = {s: cv2.imread(str(PLATES[s])) for s in SHOTS}
    found = set()
    for plate in SHOTS:
        for panel in SHOTS:
            if plate == panel:
                continue
            r = gates[plate].check_image(panels[panel])
            # Ask what the verdict would be with can_clear ignored, or the flag
            # would erase the evidence for itself.
            if r.passed and len(r.applied) >= max(1, r.min_applied):
                found.add(plate)
    return found


class TestCrossShotDiscrimination:
    """A plate that another Scene 1 panel walks through cannot clear a clip."""

    def test_can_clear_flags_match_what_is_measured(self, leaks):
        declared = {s for s in SHOTS if not ContinuityGate(shot=s).can_clear}
        assert declared == leaks, (
            "scene-01-plate.json's can_clear flags are stale - re-run "
            "`python score_corpus.py --cross-shot`"
        )

    def test_the_shots_that_can_clear_are_the_ones_we_documented(self, leaks):
        assert set(SHOTS) - leaks == {"1A", "1B", "1D", "1F", "1H"}

    def test_a_plate_that_cannot_clear_still_convicts(self):
        """1I cannot clear a clip, but the 1D panel is a different room and it
        must still come back FAIL, not INCONCLUSIVE."""
        result = ContinuityGate(shot="1I").check_image(cv2.imread(str(PLATES["1D"])))
        assert check.frame_verdict(result).strip() == "FAIL"


class TestPlateSpecShape:
    """1A must behave exactly as it did before per-shot plates."""

    #: The 1A entry as it shipped in task #336, when the spec was flat.
    ORIGINAL_1A = {
        "regions": {
            "tv": [0.00, 0.35, 0.18, 0.85],
            "lamp": [0.11, 0.28, 0.28, 0.65],
            "couch": [0.19, 0.50, 0.65, 0.82],
            "window": [0.28, 0.05, 0.65, 0.45],
            "kitchen": [0.63, 0.10, 0.95, 0.55],
            "chair": [0.72, 0.60, 1.00, 1.00],
            "jenny": [0.82, 0.35, 1.00, 0.78],
            "floor": [0.15, 0.78, 0.75, 1.00],
        },
        "bands": {"left": [0.00, 0.30, 0.25, 1.00], "right": [0.75, 0.30, 1.00, 1.00]},
        "swatches": {
            "mia_top": [0.325, 0.53, 0.385, 0.60],
            "leo_pajamas": [0.425, 0.57, 0.475, 0.66],
            "jenny_hoodie": [0.875, 0.50, 0.925, 0.62],
            "nina_dress": [0.620, 0.42, 0.660, 0.58],
            "gabe_tux": [0.715, 0.38, 0.750, 0.55],
            "couch_upholstery": [0.220, 0.62, 0.300, 0.72],
            "chair_upholstery": [0.770, 0.74, 0.850, 0.86],
        },
        "wardrobe": {
            "Mia": "mia_top", "Leo": "leo_pajamas", "Jenny": "jenny_hoodie",
            "Nina": "nina_dress", "Gabe": "gabe_tux",
        },
    }

    @pytest.mark.parametrize("key", list(ORIGINAL_1A))
    def test_1a_geometry_is_untouched(self, key):
        assert SPEC["shots"]["1A"][key] == self.ORIGINAL_1A[key]

    def test_1a_thresholds_are_untouched(self):
        gate = ContinuityGate(shot="1A")
        for name, value in {
            "layout_match": 0.55, "staging_margin": 0.02,
            "couch_occupancy_min_ratio": 0.45, "couch_occupancy_max_ratio": 2.20,
            "wardrobe_min_ratio": 0.35, "swatch_max_plate_coverage": 0.05,
            "swatch_delta_e": 22.0, "couch_delta_e": 32.0,
        }.items():
            assert gate.thresholds[name] == value, name

    def test_1a_reproduces_the_documented_plate_scores(self, gate, plate_bgr):
        """VIDEO-GATE.md records the plate's own staging gap as 0.275 and its
        layout as 1.000. If those move, every 1A number in the corpus table is
        stale."""
        checks = {c.name: c for c in gate.check_image(plate_bgr).checks}
        assert round(checks["layout_match"].score, 3) == 1.000
        assert round(checks["staging_orientation"].score, 3) == 0.275

    def test_a_shot_can_override_a_scene_wide_threshold(self, tmp_path):
        spec = _spec_copy()
        spec["shots"]["1B"].setdefault("thresholds", {})["layout_match"] = 0.9
        path = _write_spec(spec, tmp_path, "override.json")
        assert ContinuityGate(spec=path, shot="1B").thresholds["layout_match"] == 0.9
        assert ContinuityGate(spec=path, shot="1A").thresholds["layout_match"] == 0.55

    def test_a_flat_legacy_spec_still_loads(self, tmp_path):
        """The pre-per-shot shape, which an ad-hoc --plate-spec is likely to
        have: no `shots` key, everything at the top level."""
        spec = _spec_copy()
        flat = {**spec["shots"]["1A"], "thresholds": spec["thresholds"]}
        path = _write_spec(flat, tmp_path, "flat.json")
        gate = ContinuityGate(spec=path, shot="1A")
        assert gate.regions == self.ORIGINAL_1A["regions"]
        assert gate.check_image(cv2.imread(str(PLATE))).passed

    def test_an_unregistered_shot_borrows_the_default_plate(self, tmp_path):
        gate = ContinuityGate(spec=_spec_without("1C", tmp_path), shot="1C")
        assert gate.plate_is_borrowed
        assert gate.plate_id == "1A"

    def test_plate_flag_still_overrides_the_shot_entry(self):
        gate = ContinuityGate(plate=str(PLATES["1A"]), shot="1H")
        assert gate.plate_path == PLATES["1A"]


# ---------------------------------------------------------------------------
# Path resolution - the /workspace hardcoding this replaced
# ---------------------------------------------------------------------------


class TestPathResolution:
    def test_cli_flag_wins(self, monkeypatch):
        monkeypatch.setenv("CONTINUITY_PLATE", "/from/env.png")
        assert check.resolve_path("/from/cli.png", "CONTINUITY_PLATE", Path("/d")) == Path(
            "/from/cli.png"
        )

    def test_env_beats_default(self, monkeypatch):
        monkeypatch.setenv("CONTINUITY_PLATE", "/from/env.png")
        assert check.resolve_path(None, "CONTINUITY_PLATE", Path("/d")) == Path("/from/env.png")

    def test_default_is_the_repo_copy(self, monkeypatch):
        monkeypatch.delenv("CONTINUITY_PLATE", raising=False)
        assert check.resolve_path(None, "CONTINUITY_PLATE", Path("/d")) == Path("/d")

    def test_defaults_exist_so_the_tool_runs_with_no_flags(self):
        assert check.DEFAULT_PLATE.exists()
        assert check.DEFAULT_PLATE_SPEC.exists()
        assert check.DEFAULT_BIBLE.exists()

    def test_missing_plate_says_how_to_get_one(self, tmp_path):
        with pytest.raises(OSError, match="rclone"):
            ContinuityGate(plate=str(tmp_path / "nope.png"))


# ---------------------------------------------------------------------------
# Frame sampling - "do not sample only the first frame"
# ---------------------------------------------------------------------------


class TestSampling:
    def test_default_is_five_frames(self):
        assert check_video.DEFAULT_FRAMES == 5
        assert len(check_video.sample_times(10.0, check_video.DEFAULT_FRAMES)) == 5

    def test_samples_are_spread_across_the_clip(self):
        times = check_video.sample_times(10.0, 5)
        assert times == [1.0, 3.0, 5.0, 7.0, 9.0]

    def test_never_samples_the_very_first_or_last_frame(self):
        for count in (1, 2, 3, 9, 20):
            times = check_video.sample_times(8.0, count)
            assert times[0] > 0.0
            assert times[-1] < 8.0

    def test_frame_count_is_configurable(self):
        assert len(check_video.sample_times(6.0, 9)) == 9

    def test_zero_frames_is_rejected(self):
        with pytest.raises(ValueError):
            check_video.sample_times(6.0, 0)


# ---------------------------------------------------------------------------
# Aggregation policy
# ---------------------------------------------------------------------------


def _clip_result(pass_flags, tolerate=0):
    """A ClipResult with hand-set per-frame verdicts, so policy is tested alone."""
    result = check_video.ClipResult(
        video="fake.mp4", shot="1A", duration=5.0,
        requested_frames=len(pass_flags), tolerate=tolerate,
    )
    for i, ok in enumerate(pass_flags):
        status, score = (check.PASS, 0.9) if ok else (check.FAIL, 0.1)
        result.frames.append((
            float(i),
            check.FrameResult(f"t={i}", "1A", [
                check.Check("layout_match", status, score, 0.55, "x")
            ]),
        ))
    return result


class TestAggregation:
    def test_default_policy_is_all_frames_must_pass(self):
        assert _clip_result([True] * 5).passed
        assert not _clip_result([True, True, False, True, True]).passed

    def test_tolerate_allows_exactly_n_failures(self):
        assert _clip_result([True, True, False, True, True], tolerate=1).passed
        assert not _clip_result([True, False, False, True, True], tolerate=1).passed

    def test_a_shot_that_drifts_at_the_end_still_fails(self):
        """The whole reason for sampling more than the first frame."""
        assert not _clip_result([True, True, True, True, False]).passed

    def test_failing_checks_are_ranked_by_how_often_they_fire(self):
        result = _clip_result([True, True, True])
        result.frames[0][1].checks = [
            check.Check("layout_match", check.FAIL, 0.1, 0.55, ""),
            check.Check("wardrobe", check.FAIL, 0.1, 0.35, ""),
        ]
        result.frames[1][1].checks = [check.Check("layout_match", check.FAIL, 0.1, 0.55, "")]
        assert result.failing_checks[0] == "layout_match"

    def test_json_shape_is_stable_for_the_pipeline(self):
        payload = _clip_result([True, False]).to_dict()
        for key in (
            "video", "shot", "verdict", "passed", "conclusive", "duration_seconds",
            "frames_requested", "frames_scored", "frames_failed", "tolerate",
            "failing_checks", "skipped_checks", "frames",
        ):
            assert key in payload
        assert payload["frames"][0]["timestamp"] == 0.0
        assert payload["frames"][1]["passed"] is False

    def test_a_clip_where_nothing_ran_is_inconclusive_not_pass(self):
        result = check_video.ClipResult(
            video="closeup.mp4", shot="1H", duration=5.0, requested_frames=2, tolerate=0,
        )
        for i in range(2):
            skipped = [check.Check(n, check.NA, None, None, "not a wide")
                       for n in ("staging_orientation", "layout_match")]
            result.frames.append((float(i), check.FrameResult(f"t={i}", "1H", skipped)))
        assert result.verdict == "INCONCLUSIVE"
        assert not result.passed
        assert result.skipped_checks == ["staging_orientation", "layout_match"]

    def test_one_applied_check_is_not_enough_to_clear_a_clip(self):
        """The 02-shot-1B regression, encoded. One colour measurement passing
        while the room behind Leo is the wrong room is not a clearance."""
        result = check_video.ClipResult(
            video="c.mp4", shot="1B", duration=5.0, requested_frames=1, tolerate=0,
        )
        result.frames.append((0.0, check.FrameResult("t=0", "1B", [
            check.Check("layout_match", check.NA, None, None, "no regions"),
            check.Check("wardrobe", check.PASS, 0.9, 0.35, "ok"),
        ], min_applied=2)))
        assert result.verdict == "INCONCLUSIVE"
        assert result.applied_checks == ["wardrobe"]
        assert "only 1 of 2 checks" in result.inconclusive_reason

    def test_two_applied_checks_do_clear_a_clip(self):
        result = check_video.ClipResult(
            video="c.mp4", shot="1B", duration=5.0, requested_frames=1, tolerate=0,
        )
        result.frames.append((0.0, check.FrameResult("t=0", "1B", [
            check.Check("layout_match", check.PASS, 0.8, 0.55, "ok"),
            check.Check("wardrobe", check.PASS, 0.9, 0.35, "ok"),
        ], min_applied=2)))
        assert result.verdict == "PASS"

    def test_a_plate_that_cannot_clear_still_fails_a_broken_frame(self):
        """can_clear:false withholds a PASS. It must not withhold a FAIL:
        a failing measurement is evidence of a real break either way."""
        broken = check.FrameResult("t=0", "1I", [
            check.Check("layout_match", check.FAIL, 0.2, 0.55, "wrong room"),
            check.Check("staging_orientation", check.PASS, 0.3, 0.02, "ok"),
        ], min_applied=2, can_clear=False)
        clean = check.FrameResult("t=0", "1I", [
            check.Check("layout_match", check.PASS, 0.8, 0.55, "ok"),
            check.Check("staging_orientation", check.PASS, 0.3, 0.02, "ok"),
        ], min_applied=2, can_clear=False, cannot_clear_reason="1C passes this gate")
        assert check.frame_verdict(broken).strip() == "FAIL"
        assert check.frame_verdict(clean).strip() == "INCONCLUSIVE"
        assert clean.inconclusive_reason == "1C passes this gate"


# ---------------------------------------------------------------------------
# End to end, against real mp4s synthesised from the pinned plate
# ---------------------------------------------------------------------------


@needs_ffmpeg
class TestEndToEnd:
    def test_a_clip_of_the_plate_passes(self, gate, plate_bgr, tmp_path):
        clip = _write_clip(tmp_path / "good.mp4", plate_bgr)
        result = check_video.score_video(clip, gate, frames=5)
        assert result.passed
        assert len(result.frames) == 5

    def test_a_clip_of_the_mirrored_plate_fails_on_every_frame(
        self, gate, plate_bgr, tmp_path
    ):
        clip = _write_clip(tmp_path / "flipped.mp4", cv2.flip(plate_bgr, 1))
        result = check_video.score_video(clip, gate, frames=5)
        assert not result.passed
        assert len(result.failed_frames) == 5
        assert "staging_orientation" in result.failing_checks

    def test_drift_partway_through_is_caught(self, gate, plate_bgr, tmp_path):
        """Four seconds on the locked plate, then two seconds mirrored. A check
        that only looked near the top of the clip would pass this."""
        good = _write_clip(tmp_path / "a.mp4", plate_bgr, seconds=4)
        bad = _write_clip(tmp_path / "b.mp4", cv2.flip(plate_bgr, 1), seconds=2)
        joined = tmp_path / "drift.mp4"
        listing = tmp_path / "list.txt"
        listing.write_text(f"file '{good}'\nfile '{bad}'\n")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", str(listing), "-c", "copy", "-y", str(joined)],
            check=True, capture_output=True,
        )
        single = check_video.score_video(joined, gate, frames=1)
        assert single.passed, "sanity: one sample lands in the on-model stretch"
        drifted = check_video.score_video(joined, gate, frames=5)
        assert not drifted.passed
        assert "staging_orientation" in drifted.failing_checks

    def test_keep_frames_writes_the_samples_out(self, gate, plate_bgr, tmp_path):
        clip = _write_clip(tmp_path / "good.mp4", plate_bgr)
        out = tmp_path / "frames"
        check_video.score_video(clip, gate, frames=3, keep_frames=out)
        assert len(list(out.glob("*.png"))) == 3

    def test_temp_frames_are_cleaned_up_when_not_kept(self, gate, plate_bgr, tmp_path):
        clip = _write_clip(tmp_path / "good.mp4", plate_bgr)
        before = set(Path(tmp_path).parent.glob("contgate-*"))
        check_video.score_video(clip, gate, frames=2)
        assert not (set(Path(tmp_path).parent.glob("contgate-*")) - before)

    def test_a_non_video_is_a_usage_error_not_a_crash(self, tmp_path):
        junk = tmp_path / "not-a-video.mp4"
        junk.write_bytes(b"nope")
        assert check_video.main([str(junk)]) == 2


# ---------------------------------------------------------------------------
# CLI contracts - both entry points gate a shell pipeline by exit code
# ---------------------------------------------------------------------------


class TestStillCli:
    def test_pass_exits_zero(self, capsys):
        assert check.main([str(PLATE), "--shot", "1A"]) == 0
        assert "PASS" in capsys.readouterr().out

    def test_fail_exits_one(self, tmp_path, plate_bgr, capsys):
        flipped = tmp_path / "flipped.png"
        cv2.imwrite(str(flipped), cv2.flip(plate_bgr, 1))
        assert check.main([str(flipped), "--shot", "1A"]) == 1
        assert "FAIL" in capsys.readouterr().out

    def test_missing_file_exits_two(self, capsys):
        assert check.main(["/no/such/frame.png"]) == 2
        assert "error" in capsys.readouterr().err

    def test_json_is_parseable(self, capsys):
        check.main([str(PLATE), "--shot", "1A", "--json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["passed"] is True
        assert {c["name"] for c in payload["checks"]} == {
            "staging_orientation", "layout_match", "couch_occupancy", "wardrobe"
        }

    def test_runs_without_a_shot(self, capsys):
        """No --shot means no manifest lookup; the plate checks still run."""
        assert check.main([str(PLATE)]) == 0


@needs_ffmpeg
class TestVideoCli:
    def test_pass_exits_zero(self, plate_bgr, tmp_path, capsys):
        clip = _write_clip(tmp_path / "good.mp4", plate_bgr)
        assert check_video.main([str(clip), "--shot", "1A"]) == 0
        assert "PASS" in capsys.readouterr().out

    def test_fail_exits_one(self, plate_bgr, tmp_path):
        clip = _write_clip(tmp_path / "flipped.mp4", cv2.flip(plate_bgr, 1))
        assert check_video.main([str(clip), "--shot", "1A"]) == 1

    def test_tolerate_can_rescue_a_clip(self, plate_bgr, tmp_path, capsys):
        clip = _write_clip(tmp_path / "flipped.mp4", cv2.flip(plate_bgr, 1))
        assert check_video.main([str(clip), "--frames", "2", "--tolerate", "2"]) == 0
        assert "tolerate 2" in capsys.readouterr().out

    def test_negative_tolerate_is_a_usage_error(self, plate_bgr, tmp_path):
        clip = _write_clip(tmp_path / "good.mp4", plate_bgr)
        assert check_video.main([str(clip), "--tolerate", "-1"]) == 2

    def test_zero_frames_is_a_usage_error(self, plate_bgr, tmp_path):
        clip = _write_clip(tmp_path / "good.mp4", plate_bgr)
        assert check_video.main([str(clip), "--frames", "0"]) == 2

    def test_json_reports_every_sampled_frame(self, plate_bgr, tmp_path, capsys):
        clip = _write_clip(tmp_path / "good.mp4", plate_bgr)
        check_video.main([str(clip), "--shot", "1A", "--frames", "4", "--json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["frames_scored"] == 4
        assert len({f["timestamp"] for f in payload["frames"]}) == 4

    def test_plate_override_flag_is_honoured(self, plate_bgr, tmp_path):
        """--plate on the video tool reaches the same resolver check.py uses."""
        clip = _write_clip(tmp_path / "good.mp4", plate_bgr)
        assert check_video.main([str(clip), "--plate", "/no/such/plate.png"]) == 2

    def test_inconclusive_exits_one_by_default(self, tmp_path, capsys):
        """1I's own panel through 1I's own gate: every check passes, and the
        clip is still not cleared, because the 1C panel passes it too."""
        clip = _write_clip(tmp_path / "hall.mp4", cv2.imread(str(PLATES["1I"])))
        assert check_video.main([str(clip), "--shot", "1I"]) == 1
        out = capsys.readouterr().out
        assert "INCONCLUSIVE" in out
        assert "can only FAIL a clip" in out

    def test_allow_inconclusive_exits_zero(self, tmp_path):
        clip = _write_clip(tmp_path / "hall.mp4", cv2.imread(str(PLATES["1I"])))
        assert check_video.main([str(clip), "--shot", "1I", "--allow-inconclusive"]) == 0

    def test_tolerate_cannot_turn_inconclusive_into_pass(self, tmp_path):
        """--tolerate is about failing frames, not unmeasured ones."""
        clip = _write_clip(tmp_path / "hall.mp4", cv2.imread(str(PLATES["1I"])))
        assert check_video.main([str(clip), "--shot", "1I", "--tolerate", "9"]) == 1
