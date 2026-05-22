"""Unit tests for ``scripts.pipeline.cost_governor``.

Run with::

    python3 -m pytest scripts/pipeline/test_cost_governor.py -v

Tests use ``tmp_path`` for all state files so the real ledger at
``scripts/pipeline/state/`` is never touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.pipeline.cost_governor import (
    PRICING,
    BudgetExceeded,
    CostGovernor,
    KillSwitchTripped,
    NoProgress,
    PipelineHalted,
    RetryCapExceeded,
)


def _make_gov(tmp_path: Path, **overrides) -> CostGovernor:
    """Build a CostGovernor that writes only into ``tmp_path``."""
    defaults = dict(
        run_id="test_run",
        per_run_usd=10.0,
        daily_usd=1000.0,
        per_shot_attempts=3,
        per_run_attempts=10,
        progress_min_delta=0.05,
        progress_window=2,
        state_dir=tmp_path / "state",
        daily_state_path=tmp_path / "daily.json",
        kill_switch_path=tmp_path / "STOP",
        report_dir=tmp_path / "reports",
        dry_run=False,
    )
    defaults.update(overrides)
    return CostGovernor(**defaults)


# ---------------------------------------------------------------------------
# Pricing table integrity (locks CLAUDE.md-sourced values)
# ---------------------------------------------------------------------------


def test_pricing_table_matches_claudemd():
    """The pricing values must match the cost table in CLAUDE.md / task brief."""
    assert PRICING["gemini_image"]["usd_per_unit"] == pytest.approx(0.04)
    assert PRICING["veo3_fast_seconds"]["usd_per_unit"] == pytest.approx(0.15)
    assert PRICING["veo3_seconds"]["usd_per_unit"] == pytest.approx(0.40)
    assert PRICING["veo31_seconds"]["usd_per_unit"] == pytest.approx(0.40)
    assert PRICING["pvideo_draft_seconds"]["usd_per_unit"] == pytest.approx(0.005)
    assert PRICING["pvideo_standard_seconds"]["usd_per_unit"] == pytest.approx(0.02)
    assert PRICING["mitte_seedance_5s_shot"]["usd_per_unit"] == pytest.approx(0.24)
    assert PRICING["mitte_credit"]["usd_per_unit"] == pytest.approx(0.001)
    assert PRICING["anthropic_vision_call"]["usd_per_unit"] == pytest.approx(0.05)


# ---------------------------------------------------------------------------
# Ledger math
# ---------------------------------------------------------------------------


def test_ledger_math_sums_correctly(tmp_path):
    gov = _make_gov(tmp_path)
    gov.record_spend("gemini_image", 3)               # 3 * 0.04 = 0.12
    gov.record_spend("veo3_fast_seconds", 8)          # 8 * 0.15 = 1.20
    gov.record_spend("mitte_seedance_5s_shot", 2)     # 2 * 0.24 = 0.48
    assert gov.total_spent_usd == pytest.approx(0.12 + 1.20 + 0.48)
    assert len(gov.ledger) == 3
    assert gov.remaining_run_usd == pytest.approx(10.0 - 1.80)


def test_estimate_uses_pricing_table(tmp_path):
    gov = _make_gov(tmp_path)
    assert gov.estimate("veo3_seconds", 5) == pytest.approx(2.00)
    assert gov.estimate("anthropic_vision_call", 4) == pytest.approx(0.20)


def test_unknown_pricing_key_raises(tmp_path):
    gov = _make_gov(tmp_path)
    with pytest.raises(KeyError):
        gov.estimate("not_a_real_action", 1)


def test_record_spend_metadata_includes_shot_id(tmp_path):
    gov = _make_gov(tmp_path)
    entry = gov.record_spend(
        "gemini_image", 1, metadata={"prompt": "hi"}, shot_id="shotA"
    )
    assert entry.metadata["shot_id"] == "shotA"
    assert entry.metadata["prompt"] == "hi"


# ---------------------------------------------------------------------------
# Per-run cap enforcement
# ---------------------------------------------------------------------------


def test_per_run_cap_blocks_check(tmp_path):
    gov = _make_gov(tmp_path, per_run_usd=1.00)
    # 4 gemini images = $0.16, fine.
    assert gov.check_can_spend("gemini_image", 4) is True
    gov.record_spend("gemini_image", 4)
    # 6 veo3 seconds = $2.40, blocked.
    assert gov.check_can_spend("veo3_seconds", 6) is False
    assert gov.halted is True
    assert "per-run cap" in (gov.halted_reason or "")


def test_per_run_cap_strict_raises(tmp_path):
    gov = _make_gov(tmp_path, per_run_usd=0.10)
    with pytest.raises(BudgetExceeded):
        gov.check_can_spend_strict("veo3_seconds", 1)


def test_halted_governor_refuses_all_further_spend(tmp_path):
    gov = _make_gov(tmp_path, per_run_usd=0.10)
    with pytest.raises(BudgetExceeded):
        gov.check_can_spend_strict("veo3_seconds", 1)
    # Even cheap actions are now refused.
    with pytest.raises(PipelineHalted):
        gov.record_spend("gemini_image", 1)
    with pytest.raises(PipelineHalted):
        gov.check_can_spend_strict("gemini_image", 1)


def test_reset_halt_clears_state(tmp_path):
    gov = _make_gov(tmp_path, per_run_usd=0.10)
    with pytest.raises(BudgetExceeded):
        gov.check_can_spend_strict("veo3_seconds", 1)
    gov.reset_halt()
    assert gov.halted is False
    # And we can spend again, within the cap.
    gov.record_spend("gemini_image", 1)


def test_record_spend_also_enforces_caps(tmp_path):
    """Defense in depth: caller who skips the pre-check still cannot
    blow the budget, because record_spend re-validates."""
    gov = _make_gov(tmp_path, per_run_usd=0.05)
    with pytest.raises(BudgetExceeded):
        gov.record_spend("gemini_image", 5)  # 5 * 0.04 = 0.20 > 0.05


# ---------------------------------------------------------------------------
# Daily cap (shared across runs via the daily-spend file)
# ---------------------------------------------------------------------------


def test_daily_cap_shared_across_runs(tmp_path):
    daily = tmp_path / "shared_daily.json"
    gov1 = _make_gov(
        tmp_path,
        run_id="runA",
        per_run_usd=1000.0,
        daily_usd=0.50,
        state_dir=tmp_path / "stateA",
        daily_state_path=daily,
    )
    gov1.record_spend("gemini_image", 10)  # $0.40, fine

    gov2 = _make_gov(
        tmp_path,
        run_id="runB",
        per_run_usd=1000.0,
        daily_usd=0.50,
        state_dir=tmp_path / "stateB",
        daily_state_path=daily,
    )
    # gov2 sees the prior $0.40 of daily spend; another $0.20 would exceed.
    with pytest.raises(BudgetExceeded):
        gov2.check_can_spend_strict("gemini_image", 5)


# ---------------------------------------------------------------------------
# Retry / no-progress
# ---------------------------------------------------------------------------


def test_per_shot_retry_cap(tmp_path):
    gov = _make_gov(tmp_path, per_shot_attempts=3)
    for _ in range(3):
        gov.register_attempt("shotX", score=None)
    with pytest.raises(RetryCapExceeded):
        gov.register_attempt("shotX", score=None)


def test_per_run_attempt_cap(tmp_path):
    gov = _make_gov(tmp_path, per_shot_attempts=100, per_run_attempts=4)
    gov.register_attempt("a")
    gov.register_attempt("b")
    gov.register_attempt("c")
    gov.register_attempt("d")
    with pytest.raises(RetryCapExceeded):
        gov.register_attempt("e")
    # Per-run cap halts the governor.
    assert gov.halted is True


def test_no_progress_escalation(tmp_path):
    """Three attempts with effectively-flat scores should escalate."""
    gov = _make_gov(
        tmp_path,
        per_shot_attempts=10,
        progress_min_delta=0.05,
        progress_window=2,
    )
    gov.register_attempt("flat", score=0.40)
    gov.register_attempt("flat", score=0.41)
    with pytest.raises(NoProgress):
        gov.register_attempt("flat", score=0.42)
    assert gov.shots["flat"].escalated


def test_no_progress_does_not_fire_when_score_improves(tmp_path):
    gov = _make_gov(
        tmp_path,
        per_shot_attempts=10,
        progress_min_delta=0.05,
        progress_window=2,
    )
    gov.register_attempt("rising", score=0.40)
    gov.register_attempt("rising", score=0.50)
    # 0.40 -> 0.50 over 2 attempts is +0.10, well above the 0.05 threshold,
    # so this should NOT raise.
    gov.register_attempt("rising", score=0.55)
    assert not gov.shots["rising"].escalated


def test_escalated_shot_refuses_future_attempts(tmp_path):
    gov = _make_gov(tmp_path, per_shot_attempts=2)
    gov.register_attempt("s")
    gov.register_attempt("s")
    with pytest.raises(RetryCapExceeded):
        gov.register_attempt("s")
    with pytest.raises(RetryCapExceeded):
        gov.register_attempt("s")


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------


def test_kill_switch_blocks_check_and_record(tmp_path):
    stop = tmp_path / "STOP"
    gov = _make_gov(tmp_path, kill_switch_path=stop)
    gov.record_spend("gemini_image", 1)        # fine before STOP exists
    stop.write_text("halt\n")
    with pytest.raises(KillSwitchTripped):
        gov.check_can_spend_strict("gemini_image", 1)
    with pytest.raises(PipelineHalted):
        gov.record_spend("gemini_image", 1)


def test_kill_switch_blocks_register_attempt(tmp_path):
    stop = tmp_path / "STOP"
    gov = _make_gov(tmp_path, kill_switch_path=stop)
    stop.write_text("halt\n")
    with pytest.raises(KillSwitchTripped):
        gov.register_attempt("shot1")


# ---------------------------------------------------------------------------
# Dry-run mode
# ---------------------------------------------------------------------------


def test_dry_run_marks_entries_and_still_enforces_caps(tmp_path):
    gov = _make_gov(tmp_path, per_run_usd=0.10, dry_run=True)
    entry = gov.record_spend("gemini_image", 1)
    assert entry.dry_run is True
    # Dry-run still consumes the budget — that's the point.
    with pytest.raises(BudgetExceeded):
        gov.record_spend("veo3_seconds", 1)


def test_dry_run_default_off(tmp_path):
    gov = _make_gov(tmp_path)
    entry = gov.record_spend("gemini_image", 1)
    assert entry.dry_run is False


# ---------------------------------------------------------------------------
# Crash recovery — state survives a process restart
# ---------------------------------------------------------------------------


def test_ledger_survives_simulated_crash(tmp_path):
    gov = _make_gov(tmp_path, run_id="crash_demo")
    gov.record_spend("gemini_image", 5, shot_id="shot_a")     # $0.20
    gov.record_spend("veo3_fast_seconds", 4, shot_id="shot_a")  # $0.60
    gov.register_attempt("shot_a", score=0.5)

    state_path = gov.state_path
    assert state_path.exists()
    saved = json.loads(state_path.read_text())
    assert len(saved["ledger"]) == 2
    assert saved["shots"]["shot_a"]["attempts"] == 1

    # Simulate crash: drop the in-memory governor, build a new one with
    # the same paths.
    del gov
    gov2 = _make_gov(tmp_path, run_id="crash_demo")
    assert len(gov2.ledger) == 2
    assert gov2.total_spent_usd == pytest.approx(0.80)
    assert gov2.shots["shot_a"].attempts == 1
    assert gov2.shots["shot_a"].scores == [0.5]


def test_halted_state_survives_crash(tmp_path):
    gov = _make_gov(tmp_path, per_run_usd=0.05, run_id="halted_run")
    with pytest.raises(BudgetExceeded):
        gov.record_spend("veo3_seconds", 1)
    assert gov.halted is True

    gov2 = _make_gov(tmp_path, per_run_usd=0.05, run_id="halted_run")
    assert gov2.halted is True
    with pytest.raises(PipelineHalted):
        gov2.record_spend("gemini_image", 1)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def test_summary_has_expected_keys(tmp_path):
    gov = _make_gov(tmp_path)
    gov.record_spend("gemini_image", 2)
    gov.register_attempt("s1", score=0.5)
    s = gov.summary()
    for key in (
        "run_id", "halted", "halted_reason",
        "total_spent_usd", "per_run_usd", "remaining_run_usd",
        "daily_usd", "daily_spent_usd", "remaining_daily_usd",
        "total_attempts", "per_run_attempts", "shots", "ledger_entries",
    ):
        assert key in s
    assert s["ledger_entries"] == 1
    assert s["total_attempts"] == 1


def test_write_report_creates_markdown(tmp_path):
    gov = _make_gov(tmp_path)
    gov.record_spend("gemini_image", 3, shot_id="shotZ")
    gov.register_attempt("shotZ", score=0.4)
    out = gov.write_report()
    assert out.exists()
    text = out.read_text()
    assert "Cost report" in text
    assert "gemini_image" in text
    assert "shotZ" in text
