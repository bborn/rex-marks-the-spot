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


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
