"""Unit tests for the identity scorer - pure Python, no API calls, $0.00.

These cover the half of the validator that is arithmetic. The other half - can
the vision model actually read a frame - is covered by run_controls.py, which
costs a few cents and needs network.

    python -m pytest scripts/validate/controls/test_identity_scoring.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import shot_validator as sv  # noqa: E402


def row(**over):
    """A row that matches Gabe's sheet, with overrides."""
    base = {
        "hair_colour": "dark_brown", "hair_length": "short",
        "hair_texture": "wavy", "build": "heavy_set",
        "eyewear": "thin_wire_rectangular", "facial_hair": "stubble",
        "apparent_age": "adult", "skin_tone": "light",
        "hair_styling": "worn_loose", "face_shape": "round",
    }
    base.update(over)
    return base


def score_one(frame_row, ref_row=None, visible=True):
    fr = dict(frame_row, _visible=visible)
    return sv.score_identity({"X": fr}, {"X": ref_row or row()}, ["X"])["X"]


# --- the ladders -----------------------------------------------------------

def test_identical_rows_are_a_full_match():
    r = score_one(row())
    assert r["score"] == 1.0
    assert r["verdict"] == "same_character"
    assert r["defining_mismatches"] == []


def test_pose_and_light_attributes_never_fail_alone():
    """Hair up vs down, and a face read at a different angle, must not fail."""
    r = score_one(row(hair_styling="ponytail", face_shape="oval"))
    assert r["verdict"] == "minor_drift"
    assert r["score"] == 0.75
    assert r["score"] >= sv.GATE["character_identity"]
    assert r["defining_mismatches"] == []


def test_one_step_on_an_ordinal_ladder_is_tolerated():
    """slim/average and light/tan are one step apart: drift, not a new person."""
    assert score_one(row(build="stocky"))["verdict"] == "minor_drift"
    assert score_one(row(skin_tone="pale"))["verdict"] == "minor_drift"


def test_two_steps_on_an_ordinal_ladder_is_defining():
    r = score_one(row(build="slim"))          # heavy_set -> slim
    assert r["defining_mismatches"] == ["build"]
    assert r["score"] < sv.GATE["character_identity"]


def test_glasses_and_facial_hair_fail_on_any_difference():
    """Design elements, not lighting: one step is already a different person."""
    assert score_one(row(eyewear="none"))["defining_mismatches"] == ["eyewear"]
    assert score_one(row(eyewear="heavy_dark_rectangular"))["defining_mismatches"] == ["eyewear"]
    assert score_one(row(facial_hair="clean_shaven"))["defining_mismatches"] == ["facial_hair"]


def test_two_defining_mismatches_reads_as_a_different_person():
    r = score_one(row(eyewear="none", facial_hair="clean_shaven"))
    assert r["verdict"] == "different_person"
    assert r["score"] == 0.1


# --- hair colour adjacency -------------------------------------------------

def test_adjacent_hair_colours_are_lighting():
    """Warm lamplight really does read a shade darker than a white-bg sheet."""
    assert sv._attr_distance(sv._ATTR_BY_KEY["hair_colour"], "blonde", "light_brown") == 1
    r = score_one(row(hair_colour="black"))   # dark_brown -> black
    assert r["defining_mismatches"] == []


def test_non_adjacent_hair_colours_are_defining():
    """Blonde Jenny against a dark-brown turnaround is the canonical catch."""
    assert sv._attr_distance(sv._ATTR_BY_KEY["hair_colour"], "blonde", "dark_brown") == 2
    r = score_one(row(hair_colour="blonde"))
    assert r["defining_mismatches"] == ["hair_colour"]
    assert r["score"] < sv.GATE["character_identity"]


def test_auburn_sits_beside_the_browns_not_beside_blonde():
    d = sv._ATTR_BY_KEY["hair_colour"]
    assert sv._attr_distance(d, "red_auburn", "dark_brown") == 1
    assert sv._attr_distance(d, "red_auburn", "blonde") == 2


def test_unknown_enum_value_does_not_crash_or_silently_pass():
    r = score_one(row(hair_colour="chartreuse"))
    assert r["score"] < 1.0


# --- absence and gaps ------------------------------------------------------

def test_absent_character_is_unverified_not_failed():
    r = score_one(row(), visible=False)
    assert r["no_reference"] is True
    assert r["verdict"] == "not_visible"


def test_character_with_no_sheet_row_is_unverified_not_passed():
    out = sv.score_identity({"X": dict(row(), _visible=True)}, {}, ["X"])["X"]
    assert out["no_reference"] is True
    assert "NOT VERIFIED" in out["notes"]


# --- the gate --------------------------------------------------------------

def _keyframe(identity_scores, **over):
    data = {
        "character_presence": {"score": 1.0, "expected": [], "observed": [],
                               "missing": [], "unexpected": []},
        "character_identity": {
            n: {"score": s, "no_reference": False, "verdict": "v", "notes": ""}
            for n, s in identity_scores.items()},
        "character_wardrobe": {},
        "location_match": {"score": 1.0, "notes": "", "no_reference": False},
        "continuity": {"score": 1.0, "notes": "", "no_prior_shot": True,
                       "same_location_as_prior": False},
        "artifacts": {"score": 1.0, "notes": "", "detected": []},
        "reasons": [],
    }
    data.update(over)
    return data


def test_gate_fails_on_a_single_off_model_character():
    ok, reasons = sv._gate_keyframe(_keyframe({"A": 1.0, "B": 0.4}), ["A", "B"])
    assert ok is False
    assert any("B identity" in r for r in reasons)


def test_gate_is_not_the_models_to_assert():
    """A model claiming overall_pass cannot override the computed gate."""
    kf = _keyframe({"A": 0.1})
    kf["overall_pass"] = True
    ok, _ = sv._gate_keyframe(kf, ["A"])
    assert ok is False


def test_missing_location_plate_is_reported_not_passed():
    kf = _keyframe({"A": 1.0})
    kf["location_match"] = {"score": 0.0, "notes": "", "no_reference": True}
    ok, reasons = sv._gate_keyframe(kf, ["A"])
    assert ok is True  # cannot fail on a check that could not run...
    assert any("location not verified" in r for r in reasons)  # ...but it is said out loud


# --- aggregation -----------------------------------------------------------

def test_a_failing_keyframe_is_not_averaged_away():
    """0.10 / 1.00 / 1.00 used to aggregate to 0.70 and clear the 0.60 gate."""
    kfs = [
        {"character_identity": {"A": {"score": s, "no_reference": False}},
         "character_wardrobe": {}, "overall_pass": s >= 0.6, "reasons": []}
        for s in (0.1, 1.0, 1.0)
    ]
    agg, passed, _ = sv._aggregate(kfs)
    assert agg["character_identity"]["A"] == 0.1
    assert agg["character_identity_mean"]["A"] == 0.7
    assert passed is False


# --- the shipped sheet -----------------------------------------------------

def test_shipped_identity_sheet_is_well_formed():
    sheets = sv.load_identity_sheets()
    assert sheets, "no identity sheet shipped"
    assert sv.validate_identity_sheet(sheets) == []


def test_shipped_sheet_covers_the_scene_one_cast():
    sheets = sv.load_identity_sheets()
    for name in ("Gabe", "Nina", "Mia", "Leo", "Jenny"):
        assert name in sheets, f"{name} has no locked identity row"


def test_locked_cast_is_pairwise_distinguishable():
    """If two characters' rows are identical the validator cannot tell them
    apart, and a swapped character would score a perfect match."""
    sheets = sv.load_identity_sheets()
    names = sorted(sheets)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            scored = sv.score_identity(
                {a: dict(sheets[b], _visible=True)}, {a: sheets[a]}, [a])[a]
            assert scored["score"] < sv.GATE["character_identity"], (
                f"{b}'s attributes score {scored['score']} against {a}'s row - "
                f"the sheet cannot tell them apart")


def test_control_set_still_contains_a_true_positive():
    """A control set of nothing but failures cannot detect a fail-everything
    validator, which is the mirror image of the bug being fixed here."""
    spec = json.loads((Path(__file__).parent / "control-set.json").read_text())
    kinds = [c["kind"] for c in spec["cases"]]
    assert "true-positive" in kinds
    assert "adversarial" in kinds


# --- per-character crop (task 346) -----------------------------------------
#
# The geometry half of the scale fix: pure arithmetic over boxes, so it is
# tested here rather than at a few cents a run in the control set.

W, H = 1376, 768


def test_crop_rect_is_head_and_upper_body():
    # A head 55px tall near the right edge, roughly Gabe in 1A attempt 1.
    head = [254, 741, 326, 781]
    rect = sv.character_crop_rect(head, [250, 720, 760, 830], W, H)
    x0, y0, x1, y1 = rect
    hy0, hy1 = 254 / 1000 * H, 326 / 1000 * H
    hh = hy1 - hy0
    assert y0 < hy0, "crop must include headroom above the hair"
    assert y1 > hy1 + 2 * hh, "crop must include the chest, not just the head"
    assert x0 < 741 / 1000 * W and x1 > 781 / 1000 * W
    assert 0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H


def test_crop_rect_is_clamped_to_the_frame():
    # Head jammed into the top-left corner: the padded rect would go negative.
    rect = sv.character_crop_rect([0, 0, 60, 40], None, W, H)
    assert rect[0] >= 0 and rect[1] >= 0
    assert rect[2] <= W and rect[3] <= H


def test_crop_rect_needs_a_box():
    assert sv.character_crop_rect(None, None, W, H) is None


def test_crop_rect_rejects_a_head_too_small_to_recover():
    # A 2px head has nothing in it to enlarge.
    assert sv.character_crop_rect([500, 500, 502, 503], None, W, H) is None


def test_crop_rect_falls_back_to_the_figure_box():
    rect = sv.character_crop_rect(None, [200, 300, 800, 420], W, H)
    assert rect is not None
    # Upper body only: the crop must stop well above the bottom of the figure.
    assert rect[3] < 800 / 1000 * H


def test_crop_rect_does_not_run_past_the_end_of_the_figure():
    # A head-and-shoulders figure (bust): the torso extension must be clipped.
    rect = sv.character_crop_rect([100, 400, 200, 500], [100, 380, 260, 520], W, H)
    assert rect[3] <= int(round(260 / 1000 * H)) + 1


def test_small_head_gains_a_lot_from_cropping():
    rect = sv.character_crop_rect([254, 741, 326, 781], None, W, H)
    gain, upscale = sv._crop_gain(rect, W, H)
    assert gain > 3.0, f"a 1/14-of-frame head should magnify hard, got {gain}"
    assert upscale <= sv._CROP_MAX_UPSCALE


def test_a_head_that_fills_the_frame_gains_little():
    """The guard that stops the crop pass paying for a duplicate call."""
    rect = sv.character_crop_rect([0, 200, 950, 800], None, 1600, 1600)
    gain, _ = sv._crop_gain(rect, 1600, 1600)
    assert gain < sv._MIN_CROP_GAIN


def test_bad_boxes_are_rejected_not_repaired():
    for bad in (None, [], [1, 2, 3], "0,0,10,10", [10, 10, 5, 20],
                [0, 0, 10, 1200], [-5, 0, 10, 20]):
        assert sv._clean_box(bad) is None
    assert sv._clean_box([10, 20, 30, 40]) == [10, 20, 30, 40]
    assert sv._clean_box(["10", 20.4, 30, 40]) == [10, 20, 30, 40]


def test_observation_table_carries_the_boxes():
    obs = sv._obs_table([{
        "name": "Gabe", "visible": True, "where_in_frame": "right",
        "head_box_2d": [254, 741, 326, 781],
        "figure_box_2d": [250, 720, 760, 830],
        "eyewear": "thin_wire_rectangular",
    }])
    assert obs["Gabe"]["_head_box"] == [254, 741, 326, 781]
    assert obs["Gabe"]["_figure_box"] == [250, 720, 760, 830]


def test_score_records_where_the_frame_side_was_read_from():
    """A crop-graded score must say so, or a report cannot be audited."""
    fr = dict(row(), _visible=True, _identity_source="crop",
              _crop={"cropped": True, "gain": 4.2},
              _wholeframe_attributes=row(eyewear="heavy_dark_rectangular"),
              _crop_changed=["eyewear"])
    out = sv.score_identity({"X": fr}, {"X": row()}, ["X"])["X"]
    assert out["score"] == 1.0
    assert out["graded_on"] == "crop"
    assert out["crop_changed"] == ["eyewear"]
    assert out["wholeframe_attributes"]["eyewear"] == "heavy_dark_rectangular"


def test_default_source_is_the_whole_frame():
    out = sv.score_identity({"X": dict(row(), _visible=True)}, {"X": row()}, ["X"])["X"]
    assert out["graded_on"] == "whole_frame"


def test_crop_pass_does_not_change_the_gate():
    """The fix is about what the model is shown, not about what fails.

    A crop-sourced reading with a defining mismatch must still fail exactly as
    a whole-frame one does. If this test ever passes trivially, the crop pass
    has become a way of not failing.
    """
    for source in ("whole_frame", "crop"):
        fr = dict(row(eyewear="none"), _visible=True, _identity_source=source)
        out = sv.score_identity({"X": fr}, {"X": row()}, ["X"])["X"]
        assert out["score"] < sv.GATE["character_identity"], source
        assert "eyewear" in out["defining_mismatches"]


def test_control_set_covers_both_ends_of_the_scale_bug():
    """A small-in-frame character that is right, and one that is wrong.

    Only the first proves the false FAIL is gone; only the second proves the
    fix did not buy it by softening.
    """
    spec = json.loads((Path(__file__).parent / "control-set.json").read_text())
    by_id = {c["id"]: c for c in spec["cases"]}
    good = by_id["scale-1A-a1-gabe-small-correct"]
    bad = by_id["scale-veo3-v1-gabe-small-wrong"]
    assert good["expect_identity_at_or_above"]["Gabe"] >= sv.GATE["character_identity"]
    assert good["expect_frame_attribute"]["Gabe"]["eyewear"] == "thin_wire_rectangular"
    assert bad["expect_identity_below"]["Gabe"] <= sv.GATE["character_identity"]
    assert bad["expect_overall"] == "FAIL"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
