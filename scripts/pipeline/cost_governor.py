"""Cost governor: budget caps + runaway-loop circuit breaker.

This module is the SAFETY layer of the self-correcting animation pipeline.
Pipeline code MUST consult ``CostGovernor`` before every paid API call
(image gen, video gen, vision review, etc.) so the system can never spend
unbounded amounts on a failing loop.

Hard guarantees:

* Per-run dollar ceiling and global per-day ceiling. Once hit, the
  governor enters a halted state and refuses all further spend.
* Per-shot retry cap and per-run total-attempt cap.
* No-progress detection: if validation scores stop improving across
  retries, the shot is escalated instead of looped.
* Kill switch: dropping a ``STOP`` file beside this module halts the
  pipeline on the next check.
* Crash-safe ledger: state is flushed to JSON after every record so a
  killed process never loses accounting.

Usage::

    from scripts.pipeline.cost_governor import CostGovernor

    gov = CostGovernor(run_id="scene01")
    gov.check_can_spend_strict("veo3_fast_seconds", 8)   # raises if blocked
    # ... call paid API ...
    gov.record_spend("veo3_fast_seconds", 8, metadata={"shot": "01a"})
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Pricing table — single source of truth, seeded from CLAUDE.md cost notes.
# Every entry is "dollars per unit", where the unit name documents what
# ``units`` means when recording spend (an image, a second of video, etc.).
# Update values here, not in caller code.
# ---------------------------------------------------------------------------

PRICING: dict[str, dict[str, Any]] = {
    # Gemini image generation (nano banana / 2.5 / 3 pro image preview).
    "gemini_image": {"unit": "image", "usd_per_unit": 0.04},
    # Google Veo video models, billed per second of output.
    "veo3_fast_seconds": {"unit": "second", "usd_per_unit": 0.15},
    "veo3_seconds": {"unit": "second", "usd_per_unit": 0.40},
    "veo31_seconds": {"unit": "second", "usd_per_unit": 0.40},
    # P-Video (Replicate) draft + standard 720p, per second.
    "pvideo_draft_seconds": {"unit": "second", "usd_per_unit": 0.005},
    "pvideo_standard_seconds": {"unit": "second", "usd_per_unit": 0.02},
    # mitte Seedance 2 — billed as 1000 credits = $1; a 5s shot is ~240
    # credits, i.e. ~$0.24. Caller passes number of 5s shots.
    "mitte_seedance_5s_shot": {"unit": "shot", "usd_per_unit": 0.24},
    # mitte credits, if the caller knows the credit count directly.
    "mitte_credit": {"unit": "credit", "usd_per_unit": 0.001},
    # Anthropic vision review call. CLAUDE.md notes ~$0.02-0.05; we take
    # the upper end so estimates never under-quote.
    "anthropic_vision_call": {"unit": "call", "usd_per_unit": 0.05},
}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PipelineHalted(Exception):
    """Raised when the governor refuses to authorize further work."""


class BudgetExceeded(PipelineHalted):
    """A spend or estimate would breach a configured dollar cap."""


class RetryCapExceeded(PipelineHalted):
    """Per-shot or per-run retry caps have been reached."""


class NoProgress(PipelineHalted):
    """Successive retries failed to improve validation score; escalate."""


class KillSwitchTripped(PipelineHalted):
    """The on-disk STOP file is present; refuse all work."""


# ---------------------------------------------------------------------------
# Ledger data model
# ---------------------------------------------------------------------------


@dataclass
class LedgerEntry:
    """A single recorded spend event."""

    timestamp: str
    action: str
    units: float
    usd_per_unit: float
    cost_usd: float
    metadata: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ShotAttempts:
    """Tracks regeneration attempts and validation scores for one shot."""

    shot_id: str
    attempts: int = 0
    scores: list[float] = field(default_factory=list)
    escalated: bool = False
    escalation_reason: str | None = None

    def record_attempt(self, score: float | None) -> None:
        self.attempts += 1
        if score is not None:
            self.scores.append(float(score))

    def escalate(self, reason: str) -> None:
        self.escalated = True
        self.escalation_reason = reason

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# CostGovernor
# ---------------------------------------------------------------------------


DEFAULT_PER_RUN_USD = 25.0
DEFAULT_DAILY_USD = 40.0
DEFAULT_PER_SHOT_ATTEMPTS = 3
DEFAULT_PER_RUN_ATTEMPTS = 30
DEFAULT_PROGRESS_DELTA = 0.05
DEFAULT_PROGRESS_WINDOW = 2  # consecutive non-improving attempts -> escalate

# Repo-relative defaults. Tests pass explicit paths to avoid touching these.
_PIPELINE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PIPELINE_DIR.parent.parent
_DEFAULT_STATE_DIR = _PIPELINE_DIR / "state"
_DEFAULT_DAILY_FILE = _PIPELINE_DIR / "state" / "daily_spend.json"
_DEFAULT_KILL_SWITCH = _PIPELINE_DIR / "STOP"
_DEFAULT_REPORT_DIR = _REPO_ROOT / "reports"


class CostGovernor:
    """Enforces dollar caps and retry caps across one pipeline run.

    Parameters
    ----------
    run_id:
        Unique identifier for this run (typically the scene/shot id).
    per_run_usd:
        Hard ceiling on spend for this run. Default conservative $25.
    daily_usd:
        Hard ceiling on spend per UTC day across all runs sharing
        ``daily_state_path``. Default $40.
    per_shot_attempts:
        Max regeneration attempts for any single shot. Default 3.
    per_run_attempts:
        Max total attempts across all shots in this run. Default 30.
    progress_min_delta:
        Validation score must improve by at least this much between
        retries; otherwise it counts as "no progress". Default 0.05.
    progress_window:
        How many consecutive non-improving attempts trigger escalation.
        Default 2.
    pricing:
        Override pricing table (defaults to module-level ``PRICING``).
    state_dir:
        Where per-run ledger JSON files live. Defaults to
        ``scripts/pipeline/state/``.
    daily_state_path:
        Shared file tracking spend per UTC day across runs.
    kill_switch_path:
        File path whose existence halts the governor.
    report_dir:
        Directory for ``write_report`` markdown output.
    dry_run:
        If True, all spend is recorded with ``dry_run=True`` and still
        consumes the budget, but pipeline code is expected to skip the
        actual paid call.
    """

    def __init__(
        self,
        run_id: str,
        *,
        per_run_usd: float = DEFAULT_PER_RUN_USD,
        daily_usd: float = DEFAULT_DAILY_USD,
        per_shot_attempts: int = DEFAULT_PER_SHOT_ATTEMPTS,
        per_run_attempts: int = DEFAULT_PER_RUN_ATTEMPTS,
        progress_min_delta: float = DEFAULT_PROGRESS_DELTA,
        progress_window: int = DEFAULT_PROGRESS_WINDOW,
        pricing: dict[str, dict[str, Any]] | None = None,
        state_dir: Path | str | None = None,
        daily_state_path: Path | str | None = None,
        kill_switch_path: Path | str | None = None,
        report_dir: Path | str | None = None,
        dry_run: bool | None = None,
    ) -> None:
        self.run_id = run_id
        self.per_run_usd = float(per_run_usd)
        self.daily_usd = float(daily_usd)
        self.per_shot_attempts = int(per_shot_attempts)
        self.per_run_attempts = int(per_run_attempts)
        self.progress_min_delta = float(progress_min_delta)
        self.progress_window = int(progress_window)
        self.pricing = pricing or PRICING

        self.state_dir = Path(state_dir) if state_dir else _DEFAULT_STATE_DIR
        self.daily_state_path = (
            Path(daily_state_path) if daily_state_path else _DEFAULT_DAILY_FILE
        )
        self.kill_switch_path = (
            Path(kill_switch_path) if kill_switch_path else _DEFAULT_KILL_SWITCH
        )
        self.report_dir = Path(report_dir) if report_dir else _DEFAULT_REPORT_DIR

        # DRY_RUN env var wins if caller didn't pass an explicit value.
        if dry_run is None:
            dry_run = _truthy_env("COST_GOVERNOR_DRY_RUN") or _truthy_env("DRY_RUN")
        self.dry_run = bool(dry_run)

        self.ledger: list[LedgerEntry] = []
        self.shots: dict[str, ShotAttempts] = {}
        self.halted: bool = False
        self.halted_reason: str | None = None
        self.created_at = _utcnow_iso()

        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / f"run_{_safe_filename(run_id)}.json"

        # Load prior ledger for this run, if present, so a re-invocation
        # after a crash continues exactly where it left off.
        self._load_state()
        # Flush at least once so the file always exists after init.
        self._flush_state()

    # ------------------------------------------------------------------
    # Pricing helpers
    # ------------------------------------------------------------------

    def estimate(self, action: str, units: float) -> float:
        """Convert ``units`` of ``action`` to dollars using the pricing table."""
        if action not in self.pricing:
            raise KeyError(
                f"Unknown pricing key {action!r}. Add it to PRICING or pass "
                f"a custom pricing dict."
            )
        rate = float(self.pricing[action]["usd_per_unit"])
        return rate * float(units)

    # ------------------------------------------------------------------
    # Cap checks (call BEFORE every paid action)
    # ------------------------------------------------------------------

    def check_kill_switch(self) -> None:
        """Raise ``KillSwitchTripped`` if the STOP file exists."""
        if self.kill_switch_path.exists():
            self._halt(f"kill switch present at {self.kill_switch_path}")
            raise KillSwitchTripped(self.halted_reason or "kill switch tripped")

    def check_can_spend(
        self, action: str, units: float, *, shot_id: str | None = None
    ) -> bool:
        """Return True if a spend of ``units`` of ``action`` is allowed.

        Non-raising. Use ``check_can_spend_strict`` to raise on refusal.
        Side effect: if a cap would be breached, the governor halts and
        will refuse ALL subsequent spend until ``reset_halt()`` is called.
        """
        try:
            self.check_can_spend_strict(action, units, shot_id=shot_id)
            return True
        except PipelineHalted:
            return False

    def check_can_spend_strict(
        self, action: str, units: float, *, shot_id: str | None = None
    ) -> float:
        """Raise if a spend of ``units`` of ``action`` would be refused.

        Returns the estimated cost in dollars on success.
        """
        if self.halted:
            raise PipelineHalted(
                f"governor halted: {self.halted_reason}. Call reset_halt() to clear."
            )
        self.check_kill_switch()

        cost = self.estimate(action, units)

        # Per-run cap
        if self.total_spent_usd + cost > self.per_run_usd + 1e-9:
            self._halt(
                f"per-run cap ${self.per_run_usd:.2f} would be exceeded "
                f"(spent ${self.total_spent_usd:.4f}, +${cost:.4f})"
            )
            raise BudgetExceeded(self.halted_reason or "per-run cap exceeded")

        # Daily cap
        daily_spent = self._read_daily_spend(_utc_today())
        if daily_spent + cost > self.daily_usd + 1e-9:
            self._halt(
                f"daily cap ${self.daily_usd:.2f} would be exceeded "
                f"(today ${daily_spent:.4f}, +${cost:.4f})"
            )
            raise BudgetExceeded(self.halted_reason or "daily cap exceeded")

        return cost

    # ------------------------------------------------------------------
    # Spend recording
    # ------------------------------------------------------------------

    def record_spend(
        self,
        action: str,
        units: float,
        *,
        metadata: dict[str, Any] | None = None,
        shot_id: str | None = None,
    ) -> LedgerEntry:
        """Record a paid (or dry-run) action against the ledger.

        Pipeline contract: callers should call ``check_can_spend_strict``
        BEFORE invoking the paid API, and ``record_spend`` AFTER it
        returns. ``record_spend`` itself also enforces caps, so a caller
        that forgets the pre-check still cannot blow the budget.
        """
        if self.halted:
            raise PipelineHalted(
                f"governor halted: {self.halted_reason}. Call reset_halt() to clear."
            )
        self.check_kill_switch()

        cost = self.estimate(action, units)
        rate = float(self.pricing[action]["usd_per_unit"])

        # Re-check caps at record time too — defense in depth.
        if self.total_spent_usd + cost > self.per_run_usd + 1e-9:
            self._halt(
                f"per-run cap ${self.per_run_usd:.2f} exceeded at record_spend "
                f"(spent ${self.total_spent_usd:.4f}, +${cost:.4f})"
            )
            raise BudgetExceeded(self.halted_reason or "per-run cap exceeded")
        today = _utc_today()
        daily_spent = self._read_daily_spend(today)
        if daily_spent + cost > self.daily_usd + 1e-9:
            self._halt(
                f"daily cap ${self.daily_usd:.2f} exceeded at record_spend "
                f"(today ${daily_spent:.4f}, +${cost:.4f})"
            )
            raise BudgetExceeded(self.halted_reason or "daily cap exceeded")

        meta = dict(metadata or {})
        if shot_id is not None:
            meta.setdefault("shot_id", shot_id)
        entry = LedgerEntry(
            timestamp=_utcnow_iso(),
            action=action,
            units=float(units),
            usd_per_unit=rate,
            cost_usd=cost,
            metadata=meta,
            dry_run=self.dry_run,
        )
        self.ledger.append(entry)
        self._write_daily_spend(today, daily_spent + cost)
        self._flush_state()
        return entry

    # ------------------------------------------------------------------
    # Retry / no-progress tracking
    # ------------------------------------------------------------------

    def register_attempt(
        self, shot_id: str, *, score: float | None = None
    ) -> ShotAttempts:
        """Record a regeneration attempt for ``shot_id``.

        Enforces per-shot cap, per-run cap, and the no-progress guard.
        Raises ``RetryCapExceeded`` or ``NoProgress`` if any trigger,
        and marks the shot escalated so future attempts also raise.
        """
        if self.halted:
            raise PipelineHalted(
                f"governor halted: {self.halted_reason}. Call reset_halt() to clear."
            )
        self.check_kill_switch()

        shot = self.shots.get(shot_id)
        if shot is None:
            shot = ShotAttempts(shot_id=shot_id)
            self.shots[shot_id] = shot

        if shot.escalated:
            raise RetryCapExceeded(
                f"shot {shot_id!r} already escalated: {shot.escalation_reason}"
            )

        # Per-shot cap.
        if shot.attempts + 1 > self.per_shot_attempts:
            reason = (
                f"per-shot cap {self.per_shot_attempts} reached for shot {shot_id!r}"
            )
            shot.escalate(reason)
            self._flush_state()
            raise RetryCapExceeded(reason)

        # Per-run cap.
        total_attempts = self.total_attempts + 1
        if total_attempts > self.per_run_attempts:
            reason = (
                f"per-run attempts cap {self.per_run_attempts} reached "
                f"(would be {total_attempts})"
            )
            shot.escalate(reason)
            self._halt(reason)
            self._flush_state()
            raise RetryCapExceeded(reason)

        shot.record_attempt(score)

        # No-progress detection: only meaningful once we have at least
        # ``progress_window + 1`` scores, so we can compare an attempt to
        # the one ``progress_window`` steps before it.
        if score is not None and len(shot.scores) >= self.progress_window + 1:
            recent = shot.scores[-(self.progress_window + 1) :]
            baseline = recent[0]
            no_improvement = all(
                (s - baseline) < self.progress_min_delta for s in recent[1:]
            )
            if no_improvement:
                reason = (
                    f"no-progress: shot {shot_id!r} score did not improve by "
                    f"{self.progress_min_delta} over {self.progress_window} "
                    f"attempts (scores={recent})"
                )
                shot.escalate(reason)
                self._flush_state()
                raise NoProgress(reason)

        self._flush_state()
        return shot

    # ------------------------------------------------------------------
    # State / halt management
    # ------------------------------------------------------------------

    def reset_halt(self) -> None:
        """Clear the halted flag. Caller is responsible for the reason."""
        self.halted = False
        self.halted_reason = None
        self._flush_state()

    @property
    def total_spent_usd(self) -> float:
        return sum(e.cost_usd for e in self.ledger)

    @property
    def total_attempts(self) -> int:
        return sum(s.attempts for s in self.shots.values())

    @property
    def remaining_run_usd(self) -> float:
        return max(0.0, self.per_run_usd - self.total_spent_usd)

    def remaining_daily_usd(self) -> float:
        return max(0.0, self.daily_usd - self._read_daily_spend(_utc_today()))

    def summary(self) -> dict[str, Any]:
        """Snapshot for logs / reporting."""
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
            "halted": self.halted,
            "halted_reason": self.halted_reason,
            "total_spent_usd": round(self.total_spent_usd, 6),
            "per_run_usd": self.per_run_usd,
            "remaining_run_usd": round(self.remaining_run_usd, 6),
            "daily_usd": self.daily_usd,
            "daily_spent_usd": round(self._read_daily_spend(_utc_today()), 6),
            "remaining_daily_usd": round(self.remaining_daily_usd(), 6),
            "total_attempts": self.total_attempts,
            "per_run_attempts": self.per_run_attempts,
            "shots": {sid: s.as_dict() for sid, s in self.shots.items()},
            "ledger_entries": len(self.ledger),
            "state_path": str(self.state_path),
        }

    def write_report(self, path: Path | str | None = None) -> Path:
        """Write a human-readable markdown report for this run."""
        if path is None:
            self.report_dir.mkdir(parents=True, exist_ok=True)
            path = self.report_dir / f"cost_report_{_safe_filename(self.run_id)}.md"
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        s = self.summary()
        lines: list[str] = []
        lines.append(f"# Cost report: {self.run_id}")
        lines.append("")
        lines.append(f"- Created: {s['created_at']}")
        lines.append(f"- Dry run: {s['dry_run']}")
        lines.append(f"- Halted: {s['halted']}")
        if s["halted_reason"]:
            lines.append(f"- Halted reason: {s['halted_reason']}")
        lines.append("")
        lines.append("## Spend")
        lines.append("")
        lines.append(f"- Spent this run: **${s['total_spent_usd']:.4f}** "
                     f"of ${s['per_run_usd']:.2f} cap "
                     f"(remaining ${s['remaining_run_usd']:.4f})")
        lines.append(f"- Spent today: **${s['daily_spent_usd']:.4f}** "
                     f"of ${s['daily_usd']:.2f} daily cap "
                     f"(remaining ${s['remaining_daily_usd']:.4f})")
        lines.append("")
        lines.append("## Attempts")
        lines.append("")
        lines.append(f"- Total attempts: {s['total_attempts']} of "
                     f"{s['per_run_attempts']} cap")
        for sid, shot in s["shots"].items():
            esc = " ESCALATED" if shot["escalated"] else ""
            lines.append(
                f"  - `{sid}`: {shot['attempts']} attempts, "
                f"scores={shot['scores']}{esc}"
            )
            if shot["escalated"]:
                lines.append(f"    - reason: {shot['escalation_reason']}")
        lines.append("")
        lines.append("## Ledger")
        lines.append("")
        if not self.ledger:
            lines.append("_no entries_")
        else:
            lines.append("| time | action | units | $/unit | cost | shot | dry |")
            lines.append("|------|--------|-------|--------|------|------|-----|")
            for e in self.ledger:
                shot = e.metadata.get("shot_id", "")
                lines.append(
                    f"| {e.timestamp} | {e.action} | {e.units} | "
                    f"${e.usd_per_unit:.4f} | ${e.cost_usd:.4f} | {shot} | "
                    f"{'yes' if e.dry_run else 'no'} |"
                )
        lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _halt(self, reason: str) -> None:
        self.halted = True
        self.halted_reason = reason
        self._flush_state()

    def _flush_state(self) -> None:
        """Persist the ledger + retry state atomically to disk."""
        payload = {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
            "halted": self.halted,
            "halted_reason": self.halted_reason,
            "per_run_usd": self.per_run_usd,
            "daily_usd": self.daily_usd,
            "per_shot_attempts": self.per_shot_attempts,
            "per_run_attempts": self.per_run_attempts,
            "progress_min_delta": self.progress_min_delta,
            "progress_window": self.progress_window,
            "ledger": [e.as_dict() for e in self.ledger],
            "shots": {sid: s.as_dict() for sid, s in self.shots.items()},
        }
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def _load_state(self) -> None:
        """Reload ledger + retry state if a prior state file exists."""
        if not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Corrupt state file — start fresh rather than blow up.
            return
        self.created_at = payload.get("created_at", self.created_at)
        self.halted = bool(payload.get("halted", False))
        self.halted_reason = payload.get("halted_reason")
        for raw in payload.get("ledger", []):
            self.ledger.append(
                LedgerEntry(
                    timestamp=raw.get("timestamp", _utcnow_iso()),
                    action=raw["action"],
                    units=float(raw.get("units", 0)),
                    usd_per_unit=float(raw.get("usd_per_unit", 0)),
                    cost_usd=float(raw.get("cost_usd", 0)),
                    metadata=raw.get("metadata", {}) or {},
                    dry_run=bool(raw.get("dry_run", False)),
                )
            )
        for sid, raw in (payload.get("shots") or {}).items():
            self.shots[sid] = ShotAttempts(
                shot_id=raw.get("shot_id", sid),
                attempts=int(raw.get("attempts", 0)),
                scores=[float(x) for x in raw.get("scores", [])],
                escalated=bool(raw.get("escalated", False)),
                escalation_reason=raw.get("escalation_reason"),
            )

    def _read_daily_spend(self, day: str) -> float:
        if not self.daily_state_path.exists():
            return 0.0
        try:
            data = json.loads(self.daily_state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return 0.0
        return float(data.get(day, 0.0))

    def _write_daily_spend(self, day: str, value: float) -> None:
        self.daily_state_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, float] = {}
        if self.daily_state_path.exists():
            try:
                data = json.loads(
                    self.daily_state_path.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                data = {}
        data[day] = float(value)
        tmp = self.daily_state_path.with_suffix(
            self.daily_state_path.suffix + ".tmp"
        )
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, self.daily_state_path)


# ---------------------------------------------------------------------------
# Module helpers
# ---------------------------------------------------------------------------


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _truthy_env(name: str) -> bool:
    val = os.environ.get(name, "")
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _safe_filename(name: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
    return safe or "run"


# ---------------------------------------------------------------------------
# Self-test demo (no paid API calls)
# ---------------------------------------------------------------------------


def _demo() -> int:
    """Self-test demo. Returns 0 on success.

    Simulates two scenarios in isolated state directories so the demo
    is self-contained and never touches a real ledger.
    """
    import tempfile

    print("== cost_governor self-test demo (DRY_RUN, ZERO paid API calls) ==")
    print()

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)

        # --------------------------------------------------------------
        # Scenario A: per-run budget cap halts the pipeline.
        # --------------------------------------------------------------
        print("-- scenario A: per-run budget cap --")
        gov_a = CostGovernor(
            run_id="demo_budget_cap",
            per_run_usd=2.00,            # tiny cap so we hit it fast
            daily_usd=1000.0,            # avoid the daily cap interfering
            state_dir=td_path / "a_state",
            daily_state_path=td_path / "a_daily.json",
            kill_switch_path=td_path / "a_STOP",  # never exists
            report_dir=td_path / "a_reports",
            dry_run=True,
        )

        # Burn ~$0.60 in image gen — well inside the cap.
        for i in range(15):
            gov_a.check_can_spend_strict("gemini_image", 1)
            gov_a.record_spend(
                "gemini_image", 1, metadata={"prompt_idx": i}, shot_id="shotA"
            )
        print(f"  spent so far: ${gov_a.total_spent_usd:.4f}")

        # Now ask for a Veo 3 clip whose cost would blow the cap.
        # 5 seconds * $0.40 = $2.00, plus prior $0.60 = $2.60 > $2.00 cap.
        try:
            gov_a.check_can_spend_strict("veo3_seconds", 5)
        except BudgetExceeded as exc:
            print(f"  BLOCKED: {exc}")

        # Even after the failed check, the governor refuses further work.
        try:
            gov_a.record_spend("gemini_image", 1)
        except PipelineHalted as exc:
            print(f"  halted state holds: {type(exc).__name__}: {exc}")

        report_a = gov_a.write_report()
        print(f"  report: {report_a}")
        print()

        # --------------------------------------------------------------
        # Scenario B: retry cap + no-progress guard.
        # --------------------------------------------------------------
        print("-- scenario B: retry cap + no-progress guard --")
        gov_b = CostGovernor(
            run_id="demo_no_progress",
            per_run_usd=1000.0,
            daily_usd=1000.0,
            per_shot_attempts=5,         # generous so no-progress fires first
            progress_min_delta=0.05,
            progress_window=2,
            state_dir=td_path / "b_state",
            daily_state_path=td_path / "b_daily.json",
            kill_switch_path=td_path / "b_STOP",
            report_dir=td_path / "b_reports",
            dry_run=True,
        )

        # Three attempts with effectively-flat validation scores -> escalate.
        scores = [0.41, 0.42, 0.43]
        try:
            for s in scores:
                gov_b.register_attempt("shot_07b", score=s)
                print(f"  attempt recorded, score={s}")
        except NoProgress as exc:
            print(f"  ESCALATED (no-progress): {exc}")

        # A fresh shot still works fine.
        gov_b.register_attempt("shot_07c", score=0.50)
        print(f"  unrelated shot still allowed, "
              f"total attempts={gov_b.total_attempts}")

        # Hammering shot_07b again raises immediately — it's escalated.
        try:
            gov_b.register_attempt("shot_07b", score=0.99)
        except RetryCapExceeded as exc:
            print(f"  re-attempt on escalated shot refused: {exc}")

        report_b = gov_b.write_report()
        print(f"  report: {report_b}")
        print()

        # --------------------------------------------------------------
        # Scenario C: kill switch.
        # --------------------------------------------------------------
        print("-- scenario C: kill switch --")
        kill = td_path / "c_STOP"
        gov_c = CostGovernor(
            run_id="demo_kill_switch",
            per_run_usd=1000.0,
            daily_usd=1000.0,
            state_dir=td_path / "c_state",
            daily_state_path=td_path / "c_daily.json",
            kill_switch_path=kill,
            report_dir=td_path / "c_reports",
            dry_run=True,
        )
        gov_c.record_spend("gemini_image", 1)
        kill.write_text("halt\n")
        try:
            gov_c.check_can_spend_strict("gemini_image", 1)
        except KillSwitchTripped as exc:
            print(f"  kill switch tripped: {exc}")
        print()

    print("== demo complete, $0 spent (all dry-run, all in tempdir) ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(_demo())
