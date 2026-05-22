"""Unit tests for the pipeline orchestrator.

These tests prove the loop logic with ZERO paid API calls:

  * a shot that passes first try
  * a shot that fails twice then passes on retry, with corrective
    reasons being fed forward
  * a shot that exhausts its per-shot retry cap and is ESCALATED
  * a shot that the no-progress guard escalates because scores
    are flat across attempts
  * a low budget cap that halts the run cleanly mid-scene, leaving the
    rest of the manifest as pending so a later resume can continue
  * resumability: a killed run re-instantiated with the same paths
    picks up where it left off and stitches once everything resolves
  * the STOP kill switch halts the run at the next check
  * stitching: only approved clips are concatenated, escalated clips
    are excluded

Run with::

    python3 -m pytest scripts/pipeline/test_orchestrator.py -v
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.pipeline.cost_governor import CostGovernor
from scripts.pipeline.orchestrator import (
    ExistingClipsGenerator,
    Orchestrator,
    StubGenerator,
    StubValidator,
    stitch_clips,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_clip(path: Path, *, color: str = "black", seconds: float = 0.5) -> Path:
    """Create a tiny, valid MP4 in ``path`` via ffmpeg. Used as the stub clip."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c={color}:s=64x64:d={seconds}:r=10",
            "-pix_fmt", "yuv420p",
            str(path),
        ],
        check=True,
    )
    return path


def _make_manifest(path: Path, shot_ids: list[str]) -> Path:
    manifest = [
        {
            "shot_id": sid,
            "location": "test_room",
            "characters": [],
            "wardrobe": {},
            "key_props": ["nothing"],
            "camera": "static, 2s",
        }
        for sid in shot_ids
    ]
    path.write_text(json.dumps(manifest, indent=2))
    return path


def _make_gov(
    tmp_path: Path,
    *,
    per_run_usd: float = 100.0,
    per_shot_attempts: int = 3,
    per_run_attempts: int = 30,
    progress_min_delta: float = 0.05,
    progress_window: int = 2,
    run_id: str = "test_orchestrator",
) -> CostGovernor:
    return CostGovernor(
        run_id=run_id,
        per_run_usd=per_run_usd,
        daily_usd=1000.0,
        per_shot_attempts=per_shot_attempts,
        per_run_attempts=per_run_attempts,
        progress_min_delta=progress_min_delta,
        progress_window=progress_window,
        state_dir=tmp_path / "gov",
        daily_state_path=tmp_path / "gov-daily.json",
        kill_switch_path=tmp_path / "STOP",
        report_dir=tmp_path / "reports",
        dry_run=False,
    )


def _make_orch(
    tmp_path: Path,
    *,
    manifest_path: Path,
    generator,
    validator,
    governor: CostGovernor,
    label: str = "Test Scene",
    stitch: bool = True,
) -> Orchestrator:
    return Orchestrator(
        manifest_path=manifest_path,
        generator=generator,
        validator=validator,
        governor=governor,
        references_dir=tmp_path / "refs",
        work_dir=tmp_path / "work",
        scene_label=label,
        report_dir=tmp_path / "reports",
        fetch_references_from_r2=False,
        stitch_on_complete=stitch,
    )


# ---------------------------------------------------------------------------
# Basic happy-path
# ---------------------------------------------------------------------------


def test_shot_passes_first_try(tmp_path):
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["s1"])
    gen = StubGenerator(clip_path=clip)
    val = StubValidator(script={"s1": [(0.95, True, [])]})
    gov = _make_gov(tmp_path)
    orch = _make_orch(tmp_path, manifest_path=manifest, generator=gen, validator=val, governor=gov)

    report = orch.run_scene()

    assert report.approved == ["s1"]
    assert report.escalated == []
    assert orch.shots["s1"].status == "approved"
    assert len(orch.shots["s1"].attempts) == 1
    assert orch.shots["s1"].final_clip is not None
    assert Path(orch.shots["s1"].final_clip).exists()
    assert report.total_spent_usd == pytest.approx(0.24 + 0.05)


def test_shot_fails_then_passes_on_retry(tmp_path):
    """A shot that fails twice then passes on its third attempt, and
    forwards the validator's corrective reasons into each retry's
    GenerationRequest.prior_reasons."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["s1"])

    captured_prior_reasons: list[list[str]] = []

    def capture(req):
        captured_prior_reasons.append(list(req.prior_reasons))

    gen = StubGenerator(clip_path=clip, before_generate=capture)
    val = StubValidator(
        script={
            "s1": [
                (0.40, False, ["wardrobe drift on Mia"]),
                (0.60, False, ["hair color off on Leo"]),
                (1.00, True, []),
            ],
        },
    )
    gov = _make_gov(tmp_path, per_shot_attempts=3)
    orch = _make_orch(tmp_path, manifest_path=manifest, generator=gen, validator=val, governor=gov)

    report = orch.run_scene()

    assert report.approved == ["s1"]
    assert orch.shots["s1"].status == "approved"
    assert len(orch.shots["s1"].attempts) == 3
    # First call had no prior reasons; second call saw the wardrobe drift;
    # third call saw the hair color reason from attempt 2.
    assert captured_prior_reasons[0] == []
    assert captured_prior_reasons[1] == ["wardrobe drift on Mia"]
    assert captured_prior_reasons[2] == ["hair color off on Leo"]


# ---------------------------------------------------------------------------
# Escalation paths
# ---------------------------------------------------------------------------


def test_shot_exhausts_retries_and_is_escalated(tmp_path):
    """When the per-shot retry cap trips, the shot is escalated with the
    cap-exceeded reason, and we do NOT keep looping."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["broken"])
    gen = StubGenerator(clip_path=clip)
    val = StubValidator(
        script={
            "broken": [
                (0.10, False, ["everything wrong"]),
                (0.10, False, ["everything wrong"]),
                (0.10, False, ["everything wrong"]),
                (0.10, False, ["everything wrong"]),
                (0.10, False, ["everything wrong"]),
            ],
        },
    )
    gov = _make_gov(tmp_path, per_shot_attempts=3)
    orch = _make_orch(tmp_path, manifest_path=manifest, generator=gen, validator=val, governor=gov)

    report = orch.run_scene()

    assert report.approved == []
    assert [sid for sid, _ in report.escalated] == ["broken"]
    assert orch.shots["broken"].status == "escalated"
    assert len(orch.shots["broken"].attempts) == 3
    assert "per-shot cap" in (orch.shots["broken"].escalation_reason or "")


def test_no_progress_guard_escalates_flat_scores(tmp_path):
    """Higher per-shot cap so the no-progress guard fires first."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["flat"])
    gen = StubGenerator(clip_path=clip)
    val = StubValidator(
        script={
            "flat": [
                (0.40, False, ["drift"]),
                (0.41, False, ["drift"]),
                (0.42, False, ["drift"]),
                (0.43, False, ["drift"]),
                (0.44, False, ["drift"]),
            ],
        },
    )
    gov = _make_gov(
        tmp_path,
        per_shot_attempts=10,
        progress_min_delta=0.05,
        progress_window=2,
    )
    orch = _make_orch(tmp_path, manifest_path=manifest, generator=gen, validator=val, governor=gov)

    report = orch.run_scene()

    assert [sid for sid, _ in report.escalated] == ["flat"]
    assert orch.shots["flat"].status == "escalated"
    assert "no-progress" in (orch.shots["flat"].escalation_reason or "")


# ---------------------------------------------------------------------------
# Mixed scene — the headline acceptance criterion
# ---------------------------------------------------------------------------


def test_mixed_scene_pass_retry_escalate_in_one_run(tmp_path):
    """A scene with three shots covering all three outcomes."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["sA", "sB", "sC"])
    gen = StubGenerator(clip_path=clip)
    val = StubValidator(
        script={
            "sA": [(1.0, True, [])],
            "sB": [
                (0.40, False, ["wardrobe drift"]),
                (0.55, False, ["wardrobe drift"]),
                (1.00, True, []),
            ],
            "sC": [
                (0.30, False, ["totally broken"]),
                (0.30, False, ["totally broken"]),
                (0.30, False, ["totally broken"]),
                (0.30, False, ["totally broken"]),
            ],
        },
    )
    gov = _make_gov(tmp_path, per_shot_attempts=3)
    orch = _make_orch(tmp_path, manifest_path=manifest, generator=gen, validator=val, governor=gov)

    report = orch.run_scene()

    assert report.approved == ["sA", "sB"]
    assert [sid for sid, _ in report.escalated] == ["sC"]
    # Total attempts: sA=1 + sB=3 + sC=3 = 7
    assert report.total_attempts == 7
    # Stitched output exists and only contains approved clips.
    assert report.stitched_path is not None and Path(report.stitched_path).exists()
    # Report file is real, non-empty markdown.
    assert report.report_path.exists()
    text = report.report_path.read_text()
    assert "sA" in text and "sB" in text and "sC" in text
    assert "ESCALATED" in text.upper() or "escalated" in text


# ---------------------------------------------------------------------------
# Budget halt
# ---------------------------------------------------------------------------


def test_budget_halt_stops_mid_scene_cleanly(tmp_path):
    """A budget cap that allows ~one shot's worth of spend halts the run
    after the first shot. The rest of the manifest stays pending so a
    later resume can continue."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["a", "b", "c"])
    gen = StubGenerator(clip_path=clip)
    val = StubValidator(
        script={
            "a": [(1.0, True, [])],
            "b": [(1.0, True, [])],
            "c": [(1.0, True, [])],
        },
    )
    # Each shot's gen+val costs $0.24+$0.05 = $0.29. Two would be $0.58.
    # Cap of $0.35 lets shot 'a' complete but blocks shot 'b'.
    gov = _make_gov(tmp_path, per_run_usd=0.35)
    orch = _make_orch(tmp_path, manifest_path=manifest, generator=gen, validator=val, governor=gov)

    report = orch.run_scene()

    assert report.halted is True
    assert "per-run cap" in (report.halted_reason or "")
    assert report.approved == ["a"]
    assert orch.shots["b"].status == "pending"
    assert orch.shots["c"].status == "pending"
    # No stitched file because not all shots resolved.
    assert report.stitched_path is None


def test_budget_halt_block_is_recorded_as_failed_attempt(tmp_path):
    """A pre-generation budget block leaves a clear failed-attempt entry
    so the run report explains WHY shot 'b' has no clip."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["a", "b"])
    gen = StubGenerator(clip_path=clip)
    val = StubValidator(
        script={"a": [(1.0, True, [])], "b": [(1.0, True, [])]},
    )
    gov = _make_gov(tmp_path, per_run_usd=0.35)
    orch = _make_orch(tmp_path, manifest_path=manifest, generator=gen, validator=val, governor=gov)
    orch.run_scene()
    b_attempts = orch.shots["b"].attempts
    assert len(b_attempts) == 1
    assert b_attempts[0].error == "budget_blocked_pre_generation"
    assert b_attempts[0].clip_path is None


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------


def test_stop_file_halts_run_on_next_check(tmp_path):
    """Dropping the STOP file after shot s1 is approved should halt the
    run before s2 starts, leaving s2 untouched for a later resume."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["s1", "s2"])
    gen = StubGenerator(clip_path=clip)
    val = StubValidator(
        script={"s1": [(1.0, True, [])], "s2": [(1.0, True, [])]},
    )
    gov = _make_gov(tmp_path)
    stop_path = tmp_path / "STOP"

    def on_event(name, data):
        if name == "shot_approved" and data.get("shot_id") == "s1":
            stop_path.write_text("halt\n")

    orch = Orchestrator(
        manifest_path=manifest,
        generator=gen,
        validator=val,
        governor=gov,
        references_dir=tmp_path / "refs",
        work_dir=tmp_path / "work",
        scene_label="Test",
        report_dir=tmp_path / "reports",
        fetch_references_from_r2=False,
        on_event=on_event,
    )
    report = orch.run_scene()

    assert orch.shots["s1"].status == "approved"
    assert orch.shots["s2"].status == "pending"
    assert report.halted is True
    assert "kill switch" in (report.halted_reason or "").lower()


# ---------------------------------------------------------------------------
# Resumability
# ---------------------------------------------------------------------------


def test_resume_after_kill_continues_from_where_it_left_off(tmp_path):
    """First Orchestrator instance halts at the budget cap; a fresh
    instance built with the same work_dir + a wider cap picks up the
    remaining shots without redoing the approved one."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["a", "b", "c"])
    gen = StubGenerator(clip_path=clip)
    val_kwargs = {
        "script": {
            "a": [(1.0, True, [])],
            "b": [(1.0, True, [])],
            "c": [(1.0, True, [])],
        },
    }

    # Round 1: tight cap, only 'a' finishes.
    gov1 = _make_gov(tmp_path, per_run_usd=0.35, run_id="resume_run")
    orch1 = _make_orch(
        tmp_path, manifest_path=manifest,
        generator=gen, validator=StubValidator(**val_kwargs),
        governor=gov1,
    )
    r1 = orch1.run_scene()
    assert r1.approved == ["a"]
    assert orch1.shots["b"].status == "pending"

    # Round 2: clear the halt by using a fresh governor with a roomier
    # cap (in practice the operator would `reset_halt()` or start a new
    # run id), keep same orchestrator work_dir/state.
    gov2 = _make_gov(tmp_path, per_run_usd=5.0, run_id="resume_run_2")
    orch2 = _make_orch(
        tmp_path, manifest_path=manifest,
        generator=gen, validator=StubValidator(**val_kwargs),
        governor=gov2,
    )
    # The resumed orchestrator should see 'a' as already approved.
    assert orch2.shots["a"].status == "approved"
    assert orch2.shots["a"].final_clip is not None
    r2 = orch2.run_scene()
    assert r2.approved == ["a", "b", "c"]
    # Round 2's governor only paid for 'b' and 'c' — 'a' was not regenerated.
    assert r2.total_spent_usd == pytest.approx(2 * 0.29)
    # Stitched output exists in round 2.
    assert r2.stitched_path is not None and Path(r2.stitched_path).exists()


def test_per_shot_state_flushed_after_each_attempt(tmp_path):
    """After every attempt, the state file should be on disk and
    contain that attempt — even if the process were to die immediately
    after."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["s1"])

    snapshots: list[dict] = []
    state_file_box: dict = {}

    def snapshot_after_gen(req):
        sf = state_file_box.get("path")
        if sf and sf.exists():
            snapshots.append(json.loads(sf.read_text()))

    gen = StubGenerator(clip_path=clip, before_generate=snapshot_after_gen)
    val = StubValidator(
        script={
            "s1": [
                (0.30, False, ["x"]),
                (0.40, False, ["x"]),
                (1.0, True, []),
            ],
        },
    )
    gov = _make_gov(tmp_path, per_shot_attempts=3)
    orch = _make_orch(tmp_path, manifest_path=manifest, generator=gen, validator=val, governor=gov)
    state_file_box["path"] = orch.state_path
    orch.run_scene()

    # The state file existed before each generation call (after the prior
    # attempt's flush). On the very first attempt the file exists from
    # _load_state's init flush.
    assert all("s1" in snap["shots"] for snap in snapshots)
    assert len(snapshots) == 3
    # The 2nd and 3rd snapshots should show attempts already recorded.
    assert snapshots[1]["shots"]["s1"]["attempts"][0]["passed"] is False
    assert snapshots[2]["shots"]["s1"]["attempts"][1]["passed"] is False


# ---------------------------------------------------------------------------
# Stitching
# ---------------------------------------------------------------------------


def test_stitch_only_includes_approved_clips(tmp_path):
    """The stitched output must contain exactly the approved clips, in
    manifest order, excluding escalated ones."""
    clip = _make_clip(tmp_path / "stub.mp4")
    manifest = _make_manifest(tmp_path / "m.json", ["s1", "bad", "s2"])
    gen = StubGenerator(clip_path=clip)
    val = StubValidator(
        script={
            "s1": [(1.0, True, [])],
            "bad": [
                (0.1, False, ["x"]),
                (0.1, False, ["x"]),
                (0.1, False, ["x"]),
            ],
            "s2": [(1.0, True, [])],
        },
    )
    gov = _make_gov(tmp_path, per_shot_attempts=3)
    orch = _make_orch(tmp_path, manifest_path=manifest, generator=gen, validator=val, governor=gov)
    report = orch.run_scene()

    assert report.approved == ["s1", "s2"]
    assert [sid for sid, _ in report.escalated] == ["bad"]
    assert report.stitched_path is not None and Path(report.stitched_path).exists()
    # The concat list should reference exactly s1 + s2.
    list_path = report.stitched_path.with_suffix(".concat.txt")
    text = list_path.read_text()
    assert "attempt-00.mp4" in text
    assert text.count("file '") == 2


def test_stitch_helper_concats_two_clips(tmp_path):
    a = _make_clip(tmp_path / "a.mp4", color="red")
    b = _make_clip(tmp_path / "b.mp4", color="blue")
    out = stitch_clips([a, b], tmp_path / "out.mp4")
    assert out.exists()
    # ffprobe duration should be ~ a + b
    dur = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", str(out),
        ],
        text=True,
    ).strip()
    assert float(dur) > 0.7  # 0.5 + 0.5 = 1.0, generous lower bound


# ---------------------------------------------------------------------------
# Generator interface contract
# ---------------------------------------------------------------------------


def test_existing_clips_generator_serves_local_file(tmp_path):
    """ExistingClipsGenerator must prefer a local clip when present."""
    clip = _make_clip(tmp_path / "src" / "scene-01-s1-clip.mp4")
    gen = ExistingClipsGenerator(
        local_clips_dir=tmp_path / "src",
        scene_slug="scene-01",
    )
    from scripts.pipeline.orchestrator import GenerationRequest
    req = GenerationRequest(
        shot={"shot_id": "s1", "panel_url": None},
        attempt_index=0,
        prior_reasons=[],
        character_refs={},
        location_ref=None,
        start_frame=None,
        output_path=tmp_path / "out" / "clip.mp4",
    )
    result = gen.generate(req)
    assert result.clip_path.exists()
    assert result.metadata["via"] == "local"


def test_existing_clips_generator_raises_when_no_source(tmp_path):
    gen = ExistingClipsGenerator(local_clips_dir=tmp_path / "empty", scene_slug="scene-01")
    from scripts.pipeline.orchestrator import GenerationRequest
    req = GenerationRequest(
        shot={"shot_id": "missing", "panel_url": None},
        attempt_index=0,
        prior_reasons=[],
        character_refs={},
        location_ref=None,
        start_frame=None,
        output_path=tmp_path / "out" / "clip.mp4",
    )
    with pytest.raises(RuntimeError, match="No existing clip available"):
        gen.generate(req)
