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

    def test_background_characters_are_not_held_to_plate_scale(self, gate, plate_bgr):
        """1D's manifest marks Mia and Leo '(background, on couch)'. Requiring
        wide-plate colour coverage from them manufactures a failure."""
        two_shot = ContinuityGate(shot="1D")
        wardrobe = next(
            c for c in two_shot.check_image(plate_bgr).checks if c.name == "wardrobe"
        )
        assert wardrobe.status == check.NA
        assert "background per manifest" in wardrobe.detail


class TestScope:
    """The plate is a wide. Scoring a close-up on it proves nothing - say so."""

    def test_wide_shot_runs_the_geometry_checks(self):
        assert ContinuityGate(shot="1A").covers_plate

    def test_close_up_shot_does_not(self):
        assert not ContinuityGate(shot="1H").covers_plate

    def test_no_shot_assumes_the_frame_should_hold_the_plate(self):
        assert ContinuityGate().covers_plate

    def test_close_up_geometry_is_na_with_the_manifest_reason(self, plate_bgr):
        result = ContinuityGate(shot="1H").check_image(plate_bgr)
        geometry = [c for c in result.checks if c.name != "wardrobe"]
        assert {c.status for c in geometry} == {check.NA}
        assert "not a wide" in geometry[0].detail

    def test_a_frame_with_nothing_measured_is_not_a_pass(self, plate_bgr):
        """1F has no characters and is a close-up insert: every check is n/a."""
        result = ContinuityGate(shot="1F").check_image(plate_bgr)
        assert not result.conclusive
        assert check.frame_verdict(result).strip() == "INCONCLUSIVE"

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

    def test_one_applied_check_is_enough_to_be_conclusive(self):
        result = check_video.ClipResult(
            video="c.mp4", shot="1B", duration=5.0, requested_frames=1, tolerate=0,
        )
        result.frames.append((0.0, check.FrameResult("t=0", "1B", [
            check.Check("layout_match", check.NA, None, None, "not a wide"),
            check.Check("wardrobe", check.PASS, 0.9, 0.35, "ok"),
        ])))
        assert result.verdict == "PASS"
        assert result.skipped_checks == ["layout_match"]


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

    def test_inconclusive_exits_one_by_default(self, plate_bgr, tmp_path, capsys):
        """1F is a close-up insert with no characters: nothing can be measured."""
        clip = _write_clip(tmp_path / "insert.mp4", plate_bgr)
        assert check_video.main([str(clip), "--shot", "1F"]) == 1
        assert "INCONCLUSIVE" in capsys.readouterr().out

    def test_allow_inconclusive_exits_zero(self, plate_bgr, tmp_path):
        clip = _write_clip(tmp_path / "insert.mp4", plate_bgr)
        assert check_video.main([str(clip), "--shot", "1F", "--allow-inconclusive"]) == 0

    def test_tolerate_cannot_turn_inconclusive_into_pass(self, plate_bgr, tmp_path):
        """--tolerate is about failing frames, not unmeasured ones."""
        clip = _write_clip(tmp_path / "insert.mp4", plate_bgr)
        assert check_video.main([str(clip), "--shot", "1F", "--tolerate", "9"]) == 1
