"""Pipeline orchestrator: FULLY validate-gated generate->validate->regenerate loop.

This is the brain of the self-correcting animation pipeline. EVERY stage is
self-validating: a stage's output cannot be used by the next stage until it
has PASSED validation against the locked Asset Bible references.

Per-shot pipeline (each gate blocks the next):

  PANEL GATE  ->  VIDEO GATE  ->  STITCH GATE

  1. PANEL GATE
     - Validate the storyboard panel (still image) against character
       turnarounds, wardrobe spec, expected characters present, location,
       and artifacts.
     - On FAIL: regenerate the panel (Gemini image-to-image from locked
       turnarounds, wardrobe per manifest), re-validate, repeat under the
       cost governor's per-item retry caps.
     - On EXHAUSTED retries: escalate the shot. The video stage is then
       structurally unreachable for that shot - we never call video
       generation for a panel that did not pass.

  2. VIDEO GATE
     - Generate video using the panel-that-passed as the start frame.
     - Validate against the bible. Regenerate failures within the
       cost-governor caps; escalate on exhaustion.

  3. STITCH GATE
     - Only shots whose video stage passed are included in the cut.
     - The assembled cut is validated for cross-shot continuity. A failing
       stitch is reported but does not loop.

Every gate decision (pass / fail / regenerated / escalated) for every
stage is recorded in the run report.

The orchestrator:

  * Is killable (honors the STOP file via the cost governor).
  * Is resumable (per-shot state is flushed to disk after every state
    change, so a killed process restarts where it left off).
  * Never stitches until every shot is approved or escalated.
  * Stitches ONLY the approved shots, into ``reports/scene-XX-stitched.mp4``.
  * Writes a human-readable run report to ``reports/scene-XX-run.md``.

See ``test_orchestrator.py`` for unit tests that demonstrate the loop with
zero paid API calls (StubGenerator + StubValidator).

CLI usage::

    # Stub-mode demo (zero paid calls):
    python3 -m scripts.pipeline.orchestrator demo

    # Real validator + an existing-clips generator (no paid generation,
    # but real vision API calls — bounded by the $15 cap):
    python3 -m scripts.pipeline.orchestrator run \\
        --manifest asset-bible/manifests/scene-01.json \\
        --references-dir asset-bible \\
        --work-dir footage/scene-01 \\
        --generator existing_clips \\
        --validator real \\
        --budget 15.00 \\
        --scene-label "Scene 1"

    # Full real run with the browser-driven generator (requires a working
    # mitte session — see MitteSeedanceGenerator docstring):
    python3 -m scripts.pipeline.orchestrator run \\
        --manifest asset-bible/manifests/scene-01.json \\
        --references-dir asset-bible \\
        --work-dir footage/scene-01 \\
        --generator mitte \\
        --validator real \\
        --budget 15.00
"""

from __future__ import annotations

import abc
import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from .cost_governor import (
    BudgetExceeded,
    CostGovernor,
    KillSwitchTripped,
    NoProgress,
    PipelineHalted,
    RetryCapExceeded,
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class GenerationRequest:
    """Inputs handed to a Generator for one attempt at one shot."""

    shot: dict
    attempt_index: int  # 0-based attempt number for this shot
    prior_reasons: list[str]  # validator reasons from the previous attempt
    character_refs: dict[str, Path]  # name -> turnaround image
    location_ref: Optional[Path]
    start_frame: Optional[Path]  # storyboard panel = ideal first frame
    output_path: Path  # where the Generator must write its clip
    prior_clip: Optional[Path] = None  # path returned by the previous attempt


@dataclass
class GenerationResult:
    """Returned by a Generator. The orchestrator records ``cost_units`` of
    ``cost_action`` against the cost governor."""

    clip_path: Path
    cost_action: str  # pricing-table key, e.g. ``"mitte_seedance_5s_shot"``
    cost_units: float  # e.g. number of 5s shots, seconds, calls
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationOutcome:
    """Compact summary the orchestrator needs from any validator backend.

    ``score`` is a single 0..1 number used by the no-progress guard. We
    compute it as the mean of the rubric sub-scores so a steady upward
    trend across retries means real improvement.
    """

    passed: bool
    score: float
    reasons: list[str]
    cost_action: Optional[str] = None  # e.g. "anthropic_vision_call"
    cost_units: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class AttemptRecord:
    """Per-attempt audit log entry for a shot."""

    index: int
    started_at: str
    clip_path: Optional[str]
    gen_cost_action: Optional[str]
    gen_cost_units: float
    gen_cost_usd: float
    val_cost_action: Optional[str]
    val_cost_units: float
    val_cost_usd: float
    passed: bool
    score: float
    reasons: list[str]
    error: Optional[str] = None  # set if the generator/validator raised


@dataclass
class ShotState:
    """Persisted state for a single shot across restarts.

    The ``attempts``/``final_clip``/``escalation_reason``/``last_*`` fields
    track the VIDEO gate (kept under their original names for backward
    compatibility). The ``panel_*`` fields track the new PANEL gate.

    A shot's overall ``status`` is set to ``approved`` only after BOTH
    gates have passed; if the panel gate escalates, the shot is escalated
    and the video gate is structurally unreachable.
    """

    shot_id: str
    status: str = "pending"  # pending | approved | escalated | skipped

    # PANEL gate state
    panel_status: str = "pending"  # pending | passed | escalated | skipped
    panel_attempts: list[AttemptRecord] = field(default_factory=list)
    panel_path: Optional[str] = None
    panel_escalation_reason: Optional[str] = None
    panel_last_reasons: list[str] = field(default_factory=list)
    panel_last_score: float = 0.0

    # VIDEO gate state (legacy field names kept)
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_clip: Optional[str] = None
    escalation_reason: Optional[str] = None
    last_reasons: list[str] = field(default_factory=list)
    last_score: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class PanelGenerationRequest:
    """Inputs handed to a PanelGenerator for one panel attempt."""

    shot: dict
    attempt_index: int  # 0 = use manifest panel as-is; >=1 = regenerate
    prior_reasons: list[str]
    character_refs: dict[str, Path]
    location_ref: Optional[Path]
    output_path: Path
    existing_panel: Optional[Path]  # manifest's panel image, if available
    prior_panel: Optional[Path] = None


@dataclass
class PanelGenerationResult:
    """Returned by a PanelGenerator. Same shape as GenerationResult, but the
    payload is a still image rather than a video clip."""

    panel_path: Path
    cost_action: str  # pricing-table key, e.g. ``"gemini_image"``
    cost_units: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StitchValidationOutcome:
    """Result of validating the assembled cut."""

    passed: bool
    reasons: list[str] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# Generator interface + implementations
# ---------------------------------------------------------------------------


class Generator(abc.ABC):
    """A Generator turns one ``GenerationRequest`` into one clip on disk.

    Implementations MUST:
      * Write the clip to ``request.output_path`` (the orchestrator picks
        a unique path per attempt, so the Generator can assume it owns it).
      * Return a ``GenerationResult`` describing the spend in terms the
        ``CostGovernor`` pricing table understands.
      * Raise on any failure rather than returning a bad path; the
        orchestrator turns exceptions into a failed attempt and lets the
        retry/escalation loop handle them.
    """

    name: str = "generator"

    @abc.abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult: ...

    def cost_estimate(self, request: GenerationRequest) -> tuple[str, float]:
        """Pre-call estimate so the governor can authorize spend BEFORE we
        actually generate. Default: ask the implementation for a one-call
        estimate via a class attribute or override this method."""
        if hasattr(self, "default_cost"):
            return self.default_cost  # type: ignore[return-value]
        return ("mitte_seedance_5s_shot", 1.0)


class StubGenerator(Generator):
    """Returns a canned 1-second silent MP4 for tests.

    Optionally accepts a ``per_shot_clips`` dict so different shots can
    return different files. Always reports a fake cost in the governor's
    pricing table so budget tests look realistic without spending money.
    """

    name = "stub"

    def __init__(
        self,
        *,
        clip_path: Path,
        per_shot_clips: Optional[dict[str, Path]] = None,
        cost_action: str = "mitte_seedance_5s_shot",
        cost_units: float = 1.0,
        before_generate: Optional[Callable[[GenerationRequest], None]] = None,
    ) -> None:
        self.clip_path = Path(clip_path)
        self.per_shot_clips = per_shot_clips or {}
        self.default_cost = (cost_action, cost_units)
        self.before_generate = before_generate

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if self.before_generate is not None:
            self.before_generate(request)
        src = self.per_shot_clips.get(request.shot["shot_id"], self.clip_path)
        if not src.exists():
            raise FileNotFoundError(f"stub clip not found: {src}")
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, request.output_path)
        action, units = self.default_cost
        return GenerationResult(
            clip_path=request.output_path,
            cost_action=action,
            cost_units=units,
            metadata={"source": str(src), "stub": True},
        )


class ExistingClipsGenerator(Generator):
    """Pulls the manifest's ``panel_url`` / paired clip from R2 (or a local
    mirror) and returns it as if it had just been generated.

    Useful for end-to-end testing of the orchestrator + real validator
    without any paid generation calls. Cost is recorded as the equivalent
    mitte spend so reports look like a real run.

    Strategy for finding the clip:
      1. Look in ``local_clips_dir`` for ``scene-XX-{shot_id}-clip.mp4``.
      2. If not present, derive a URL from the manifest's ``panel_url``
         (replace ``-start.png`` with ``-clip.mp4``) and download.
    """

    name = "existing_clips"
    default_cost = ("mitte_seedance_5s_shot", 1.0)

    def __init__(
        self,
        *,
        local_clips_dir: Optional[Path] = None,
        download_dir: Optional[Path] = None,
        cost_action: str = "mitte_seedance_5s_shot",
        cost_units: float = 1.0,
        scene_slug: str = "scene-01",
    ) -> None:
        self.local_clips_dir = local_clips_dir
        self.download_dir = download_dir
        self.default_cost = (cost_action, cost_units)
        self.scene_slug = scene_slug

    def _candidate_local(self, shot: dict) -> Optional[Path]:
        if self.local_clips_dir is None:
            return None
        slug = self.scene_slug
        for name in (
            f"{slug}-{shot['shot_id']}-clip.mp4",
            f"{slug}-{shot['shot_id']}.mp4",
            f"{shot['shot_id']}.mp4",
        ):
            p = self.local_clips_dir / name
            if p.exists():
                return p
        return None

    def _candidate_url(self, shot: dict) -> Optional[str]:
        url = shot.get("panel_url")
        if not url:
            return None
        # The manifest panel_url is the start-frame PNG; sibling clip is
        # the same path with `-start.png` replaced by `-clip.mp4`.
        if url.endswith("-start.png"):
            return url[: -len("-start.png")] + "-clip.mp4"
        if url.endswith("-start.jpg"):
            return url[: -len("-start.jpg")] + "-clip.mp4"
        return None

    def generate(self, request: GenerationRequest) -> GenerationResult:
        shot = request.shot
        # 1) local
        local = self._candidate_local(shot)
        if local is not None:
            request.output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(local, request.output_path)
            action, units = self.default_cost
            return GenerationResult(
                clip_path=request.output_path,
                cost_action=action,
                cost_units=units,
                metadata={"source": str(local), "via": "local"},
            )
        # 2) download
        url = self._candidate_url(shot)
        if url is None:
            raise RuntimeError(
                f"No existing clip available for {shot['shot_id']} (no local "
                f"file, no derivable URL from panel_url={shot.get('panel_url')})"
            )
        if self.download_dir is not None:
            self.download_dir.mkdir(parents=True, exist_ok=True)
            cached = self.download_dir / f"{self.scene_slug}-{shot['shot_id']}-clip.mp4"
        else:
            cached = request.output_path
        if not cached.exists():
            _download_to(url, cached)
        if cached != request.output_path:
            shutil.copyfile(cached, request.output_path)
        action, units = self.default_cost
        return GenerationResult(
            clip_path=request.output_path,
            cost_action=action,
            cost_units=units,
            metadata={"source": url, "via": "download"},
        )


class MitteSeedanceGenerator(Generator):
    """Browser-driven mitte (Seedance) generator.

    mitte has NO API; this driver uses Playwright to:

      * load a saved storage_state JSON (cookies / localStorage) so we can
        skip interactive login — set ``storage_state`` or
        ``MITTE_STORAGE_STATE`` env var
      * open the generation page
      * attach the storyboard panel as the start frame and the character
        turnarounds as references
      * paste a prompt assembled from the shot manifest + corrective
        feedback from the previous validator pass
      * **make sure the audio toggle is OFF** — per the project's
        mitte verdict notes, mitte audio generation trips a content filter
        and burns credits for nothing
      * submit, wait for the render to complete, download the MP4

    Browser code is isolated here on purpose: if mitte changes its DOM
    tomorrow, the rest of the pipeline keeps working. Failures are loud:
    we save a screenshot + HTML dump under ``debug_dir`` and raise so the
    orchestrator marks the attempt failed and either retries or escalates.
    """

    name = "mitte"
    default_cost = ("mitte_seedance_5s_shot", 1.0)

    def __init__(
        self,
        *,
        storage_state: Optional[Path] = None,
        base_url: str = "https://mitte.ai/",
        headless: bool = True,
        debug_dir: Optional[Path] = None,
        wait_timeout_s: float = 300.0,
        cost_action: str = "mitte_seedance_5s_shot",
        cost_units: float = 1.0,
    ) -> None:
        self.storage_state = storage_state
        self.base_url = base_url
        self.headless = headless
        self.debug_dir = debug_dir or Path("reports/mitte-debug")
        self.wait_timeout_s = wait_timeout_s
        self.default_cost = (cost_action, cost_units)

    def _build_prompt(self, request: GenerationRequest) -> str:
        shot = request.shot
        parts = [
            f"Animated shot {shot['shot_id']}.",
            f"Location: {shot.get('location', 'unknown')}.",
            f"Camera: {shot.get('camera', 'static')}.",
        ]
        if shot.get("characters"):
            parts.append("Characters in this shot: " + ", ".join(shot["characters"]) + ".")
        for name, desc in (shot.get("wardrobe") or {}).items():
            parts.append(f"{name} wardrobe: {desc}.")
        if shot.get("key_props"):
            parts.append("Key props: " + "; ".join(shot["key_props"]) + ".")
        if request.prior_reasons:
            parts.append(
                "CORRECTIONS from previous attempt — address these specifically: "
                + "; ".join(request.prior_reasons[:5])
                + "."
            )
        parts.append("Do NOT generate audio.")
        return "\n".join(parts)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Install with "
                "`pip install playwright && playwright install chromium` "
                "before using MitteSeedanceGenerator."
            ) from exc

        self.debug_dir.mkdir(parents=True, exist_ok=True)
        prompt = self._build_prompt(request)
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        shot_id = request.shot["shot_id"]

        # All Playwright work is wrapped so a single brittle step doesn't
        # blow up the whole run: on failure we screenshot + dump HTML and
        # raise a clean message the orchestrator can record.
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            ctx_kwargs: dict[str, Any] = {"accept_downloads": True}
            if self.storage_state is not None and Path(self.storage_state).exists():
                ctx_kwargs["storage_state"] = str(self.storage_state)
            context = browser.new_context(**ctx_kwargs)
            page = context.new_page()
            try:
                page.goto(self.base_url, wait_until="domcontentloaded")
                # mitte's actual selectors are not under our control. We
                # try the most stable affordances first and bail loudly if
                # they're missing — that's the signal the UI moved and
                # this driver needs an update.
                _click_first(
                    page,
                    selectors=[
                        "text=New generation",
                        "text=Create",
                        "[data-testid='new-generation']",
                    ],
                    description="open generation dialog",
                )
                # Disable audio so we never trip the content filter that
                # has burned credits on prior runs.
                _set_toggle_off(
                    page,
                    selectors=[
                        "text=Audio",
                        "[data-testid='audio-toggle']",
                    ],
                    description="audio toggle",
                )
                # Attach start frame
                if request.start_frame is not None:
                    _attach_file(
                        page,
                        path=request.start_frame,
                        selectors=[
                            "input[type=file][accept*='image']",
                            "[data-testid='start-frame-upload']",
                        ],
                        description="start frame",
                    )
                # Attach reference images (characters + location)
                for ref_path in list(request.character_refs.values()) + (
                    [request.location_ref] if request.location_ref else []
                ):
                    _attach_file(
                        page,
                        path=ref_path,
                        selectors=[
                            "[data-testid='reference-upload']",
                            "input[type=file][accept*='image']",
                        ],
                        description="reference image",
                    )
                # Paste prompt
                _fill_first(
                    page,
                    selectors=[
                        "textarea[placeholder*='prompt']",
                        "textarea",
                        "[data-testid='prompt-input']",
                    ],
                    value=prompt,
                    description="prompt",
                )
                # Submit
                _click_first(
                    page,
                    selectors=[
                        "text=Generate",
                        "[data-testid='generate-submit']",
                        "button[type=submit]",
                    ],
                    description="submit generation",
                )
                # Wait for the rendered clip download link to appear.
                _wait_for_completion(
                    page, timeout_s=self.wait_timeout_s, description="render"
                )
                with page.expect_download() as dl_info:
                    _click_first(
                        page,
                        selectors=[
                            "text=Download",
                            "[data-testid='download-clip']",
                        ],
                        description="download clip",
                    )
                dl = dl_info.value
                dl.save_as(str(request.output_path))
            except Exception as exc:
                ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                page.screenshot(
                    path=str(self.debug_dir / f"{shot_id}-{ts}.png"),
                    full_page=True,
                )
                (self.debug_dir / f"{shot_id}-{ts}.html").write_text(
                    page.content(), encoding="utf-8"
                )
                raise RuntimeError(
                    f"MitteSeedanceGenerator failed at step: {exc} "
                    f"(debug artifacts in {self.debug_dir})"
                ) from exc
            finally:
                context.close()
                browser.close()

        action, units = self.default_cost
        return GenerationResult(
            clip_path=request.output_path,
            cost_action=action,
            cost_units=units,
            metadata={"via": "mitte", "headless": self.headless},
        )


def _click_first(page, selectors: list[str], description: str) -> None:
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=5_000)
            page.click(sel)
            return
        except Exception:
            continue
    raise RuntimeError(f"could not {description}: none of {selectors} present")


def _set_toggle_off(page, selectors: list[str], description: str) -> None:
    """Best-effort: click the toggle if its aria-checked is 'true'."""
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=3_000)
            checked = el.get_attribute("aria-checked")
            if checked == "true":
                el.click()
            return
        except Exception:
            continue
    # Audio toggle missing on this page is OK — many flows default to off.


def _attach_file(page, path: Path, selectors: list[str], description: str) -> None:
    for sel in selectors:
        try:
            page.set_input_files(sel, str(path), timeout=5_000)
            return
        except Exception:
            continue
    raise RuntimeError(f"could not attach {description}: none of {selectors} present")


def _fill_first(page, selectors: list[str], value: str, description: str) -> None:
    for sel in selectors:
        try:
            page.fill(sel, value, timeout=5_000)
            return
        except Exception:
            continue
    raise RuntimeError(f"could not fill {description}: none of {selectors} present")


def _wait_for_completion(page, timeout_s: float, description: str) -> None:
    """Poll for a 'Download' button or a completed state token."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for sel in (
            "text=Download",
            "[data-testid='download-clip']",
            "[data-state='completed']",
        ):
            try:
                if page.locator(sel).first.is_visible():
                    return
            except Exception:
                pass
        time.sleep(3.0)
    raise TimeoutError(f"{description} did not complete within {timeout_s}s")


def _download_to(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "rex-orchestrator/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"download failed for {url}: {exc}") from exc


# ---------------------------------------------------------------------------
# Validator interface + implementations
# ---------------------------------------------------------------------------


class Validator(abc.ABC):
    name: str = "validator"

    @abc.abstractmethod
    def validate(
        self,
        *,
        shot: dict,
        media_path: Path,
        character_refs: dict[str, Path],
        location_ref: Optional[Path],
        prior_keyframe: Optional[Path],
        work_dir: Path,
    ) -> ValidationOutcome: ...

    def cost_estimate(self) -> tuple[str, float]:
        """Pre-call cost estimate. Default: 1 anthropic vision call."""
        return ("anthropic_vision_call", 1.0)


class StubValidator(Validator):
    """Scriptable pass/fail for tests.

    ``script`` maps ``shot_id -> list[ValidationOutcome | (score, passed, reasons)]``.
    On each call for a shot, the next entry from its list is returned. If
    the list is exhausted, the last entry is reused.
    """

    name = "stub"

    def __init__(
        self,
        *,
        script: dict[str, list[Any]],
        cost_action: str = "anthropic_vision_call",
        cost_units: float = 1.0,
    ) -> None:
        self.script = {
            sid: [self._coerce(e) for e in entries] for sid, entries in script.items()
        }
        self._idx: dict[str, int] = {sid: 0 for sid in self.script}
        self._cost = (cost_action, cost_units)

    @staticmethod
    def _coerce(entry: Any) -> ValidationOutcome:
        if isinstance(entry, ValidationOutcome):
            return entry
        if isinstance(entry, tuple) and len(entry) == 3:
            score, passed, reasons = entry
            return ValidationOutcome(
                passed=bool(passed),
                score=float(score),
                reasons=list(reasons),
            )
        raise TypeError(f"unsupported script entry: {entry!r}")

    def cost_estimate(self) -> tuple[str, float]:
        return self._cost

    def validate(
        self,
        *,
        shot: dict,
        media_path: Path,
        character_refs: dict[str, Path],
        location_ref: Optional[Path],
        prior_keyframe: Optional[Path],
        work_dir: Path,
    ) -> ValidationOutcome:
        sid = shot["shot_id"]
        if sid not in self.script:
            raise KeyError(f"StubValidator has no script for shot {sid!r}")
        entries = self.script[sid]
        idx = min(self._idx[sid], len(entries) - 1)
        self._idx[sid] = idx + 1
        out = entries[idx]
        # Carry our cost-action through so the orchestrator records spend.
        action, units = self._cost
        out.cost_action = action
        out.cost_units = units
        return out


class RealValidator(Validator):
    """Wraps ``scripts.validate.shot_validator.validate_shot``.

    Real vision API calls — but cheap (the Scene 1 baseline run was ~$0.04
    total). Cost is recorded as one ``anthropic_vision_call`` per keyframe;
    that's an upper-bound estimate the cost governor can budget against.
    """

    name = "real"

    def __init__(
        self,
        *,
        backend: Optional[str] = None,
        model: Optional[str] = None,
        keyframes_per_shot: int = 3,
    ) -> None:
        self.backend = backend
        self.model = model
        self.keyframes_per_shot = keyframes_per_shot
        self._client = None
        self._effective_backend: Optional[str] = None
        self._effective_model: Optional[str] = None

    def cost_estimate(self) -> tuple[str, float]:
        # ~3 keyframes -> 3 vision calls per shot, upper-bound.
        return ("anthropic_vision_call", float(self.keyframes_per_shot))

    def _lazy_init(self) -> None:
        if self._client is not None:
            return
        # Import lazily so unit tests don't pay the import cost or require
        # the SDKs to be installed.
        from scripts.validate import shot_validator as sv

        backend = self.backend or sv.DEFAULT_BACKEND
        model = self.model or sv._default_model_for_backend(backend)
        self._client = sv._make_client(backend)
        self._effective_backend = backend
        self._effective_model = model

    def validate(
        self,
        *,
        shot: dict,
        media_path: Path,
        character_refs: dict[str, Path],
        location_ref: Optional[Path],
        prior_keyframe: Optional[Path],
        work_dir: Path,
    ) -> ValidationOutcome:
        from scripts.validate import shot_validator as sv

        self._lazy_init()
        keyframes_dir = work_dir / "keyframes"
        keyframes_dir.mkdir(parents=True, exist_ok=True)

        # ``validate_shot`` expects characters_dir / locations_dir, not
        # already-resolved paths. We point them at a temporary scratch
        # directory built from the references we already resolved.
        scratch_chars = work_dir / "scratch" / "characters"
        scratch_locs = work_dir / "scratch" / "locations"
        scratch_chars.mkdir(parents=True, exist_ok=True)
        scratch_locs.mkdir(parents=True, exist_ok=True)
        for name, path in character_refs.items():
            tgt = scratch_chars / (
                f"{name.lower()}_turnaround_APPROVED{path.suffix.lower()}"
            )
            if not tgt.exists():
                shutil.copyfile(path, tgt)
        if location_ref is not None:
            tgt = scratch_locs / f"storyboard-{shot['shot_id']}{location_ref.suffix.lower()}"
            if not tgt.exists():
                shutil.copyfile(location_ref, tgt)

        result = sv.validate_shot(
            shot=shot,
            media_path=media_path,
            characters_dir=scratch_chars,
            locations_dir=scratch_locs,
            keyframes_dir=keyframes_dir,
            prior_keyframe=prior_keyframe,
            backend=self._effective_backend,
            model=self._effective_model,
            client=self._client,
        )
        # Build a single 0..1 score for the no-progress guard: mean of the
        # rubric sub-scores plus mean character-identity score.
        agg = result.aggregate_scores or {}
        sub = [
            float(agg.get("character_presence", 0.0)),
            float(agg.get("location_match", 0.0)),
            float(agg.get("continuity", 0.0)),
            float(agg.get("artifacts", 0.0)),
        ]
        ids = agg.get("character_identity") or {}
        if ids:
            sub.append(sum(ids.values()) / len(ids))
        score = sum(sub) / len(sub) if sub else 0.0
        action, units = self.cost_estimate()
        return ValidationOutcome(
            passed=bool(result.overall_pass),
            score=round(score, 4),
            reasons=list(result.reasons or []),
            cost_action=action,
            cost_units=units,
            raw=result.to_dict(),
        )


# ---------------------------------------------------------------------------
# Panel generator + validator interfaces (PANEL GATE)
# ---------------------------------------------------------------------------


class PanelGenerator(abc.ABC):
    """A PanelGenerator regenerates a storyboard PANEL (still image).

    On attempt 0 the orchestrator's panel gate uses the manifest's panel
    as-is (no regeneration). Attempt 1+ are produced by this generator
    using the locked character turnarounds + the manifest's wardrobe spec
    as image-to-image conditioning. Implementations MUST:

      * Write the panel image to ``request.output_path``.
      * Return a ``PanelGenerationResult`` describing spend.
      * Raise on failure; the orchestrator records it as a failed attempt.
    """

    name: str = "panel_generator"

    @abc.abstractmethod
    def generate(self, request: PanelGenerationRequest) -> PanelGenerationResult: ...

    def cost_estimate(self, request: PanelGenerationRequest) -> tuple[str, float]:
        if hasattr(self, "default_cost"):
            return self.default_cost  # type: ignore[return-value]
        return ("gemini_image", 1.0)


class StubPanelGenerator(PanelGenerator):
    """Returns canned PNGs for tests. Supports per-attempt panel sequences.

    ``per_shot_panels`` maps ``shot_id -> list[Path]``. On attempt N for a
    shot, the Nth entry from that list is returned (the last entry is
    reused once the list is exhausted). Reports a fake cost in the
    governor's pricing table so budget tests look realistic.
    """

    name = "stub_panel"

    def __init__(
        self,
        *,
        panel_path: Optional[Path] = None,
        per_shot_panels: Optional[dict[str, list[Path]]] = None,
        cost_action: str = "gemini_image",
        cost_units: float = 1.0,
        before_generate: Optional[Callable[[PanelGenerationRequest], None]] = None,
    ) -> None:
        self.default_panel = Path(panel_path) if panel_path else None
        self.per_shot_panels: dict[str, list[Path]] = {
            sid: [Path(p) for p in paths]
            for sid, paths in (per_shot_panels or {}).items()
        }
        self.default_cost = (cost_action, cost_units)
        self.before_generate = before_generate

    def _pick(self, shot_id: str, attempt: int) -> Path:
        panels = self.per_shot_panels.get(shot_id)
        if panels:
            idx = min(attempt, len(panels) - 1)
            return panels[idx]
        if self.default_panel is None:
            raise RuntimeError(
                f"StubPanelGenerator has no panel for {shot_id!r}"
            )
        return self.default_panel

    def generate(self, request: PanelGenerationRequest) -> PanelGenerationResult:
        if self.before_generate is not None:
            self.before_generate(request)
        src = self._pick(request.shot["shot_id"], request.attempt_index)
        if not src.exists():
            raise FileNotFoundError(f"stub panel not found: {src}")
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, request.output_path)
        action, units = self.default_cost
        return PanelGenerationResult(
            panel_path=request.output_path,
            cost_action=action,
            cost_units=units,
            metadata={"source": str(src), "stub": True},
        )


class GeminiPanelGenerator(PanelGenerator):
    """Real Gemini image-to-image panel regeneration.

    Uses the locked character turnarounds + location plate as conditioning
    references, and an instruction prompt built from the shot manifest and
    the prior validator's failure reasons. Output: one PNG written to the
    requested path. Cost is recorded as ``gemini_image`` units.

    The actual Gemini API call is isolated here so failures (network,
    quota, content filter) raise cleanly into the orchestrator's failed-
    attempt path rather than corrupting state.
    """

    name = "gemini_panel"
    default_cost = ("gemini_image", 1.0)

    def __init__(
        self,
        *,
        model: str = "gemini-2.5-flash-image",
        cost_action: str = "gemini_image",
        cost_units: float = 1.0,
    ) -> None:
        self.model = model
        self.default_cost = (cost_action, cost_units)
        self._client = None

    def _lazy_client(self):
        if self._client is None:
            from google import genai  # type: ignore
            import os as _os
            api_key = _os.environ.get("GEMINI_API_KEY") or _os.environ.get(
                "GOOGLE_API_KEY"
            )
            if not api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is not set; cannot run GeminiPanelGenerator."
                )
            self._client = genai.Client(api_key=api_key)
        return self._client

    def _build_prompt(self, request: PanelGenerationRequest) -> str:
        shot = request.shot
        parts = [
            f"Generate a single STORYBOARD PANEL for shot {shot['shot_id']}.",
            f"Location: {shot.get('location', 'unknown')}.",
            f"Camera framing: {shot.get('camera', 'static')}.",
        ]
        if shot.get("characters"):
            parts.append(
                "Characters PRESENT in this panel (ALL of them must be "
                "visible if expected, NO unexpected extras): "
                + ", ".join(shot["characters"]) + "."
            )
        for name, desc in (shot.get("wardrobe") or {}).items():
            parts.append(
                f"{name} wardrobe (use this exact description; the character "
                f"turnaround is the IDENTITY reference, NOT a wardrobe spec): {desc}."
            )
        if shot.get("key_props"):
            parts.append("Key props in frame: " + "; ".join(shot["key_props"]) + ".")
        parts.append(
            "Strict identity match: faces, hair (color + style), skin tone, "
            "and build MUST match the provided character turnaround references."
        )
        if request.prior_reasons:
            parts.append(
                "CORRECTIONS from the prior panel attempt — fix these "
                "specifically: " + "; ".join(request.prior_reasons[:5]) + "."
            )
        parts.append(
            "Output: one square or 16:9 storyboard panel PNG, clean illustration "
            "style consistent with the locked references; no text overlays."
        )
        return "\n".join(parts)

    def generate(self, request: PanelGenerationRequest) -> PanelGenerationResult:
        from google.genai import types  # type: ignore

        client = self._lazy_client()
        prompt = self._build_prompt(request)

        # Conditioning images: character turnarounds, then location plate.
        contents: list[Any] = [prompt]
        for ref in list(request.character_refs.values()) + (
            [request.location_ref] if request.location_ref else []
        ):
            raw = Path(ref).read_bytes()
            mime = (
                "image/png" if str(ref).lower().endswith(".png") else "image/jpeg"
            )
            contents.append(types.Part.from_bytes(data=raw, mime_type=mime))

        response = client.models.generate_content(
            model=self.model,
            contents=contents,
        )
        # Find an inline image part in the response.
        out_path = request.output_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        wrote = False
        try:
            candidates = response.candidates or []
            for cand in candidates:
                for part in cand.content.parts or []:
                    inline = getattr(part, "inline_data", None)
                    if inline is None or not getattr(inline, "data", None):
                        continue
                    data = inline.data
                    if isinstance(data, str):
                        import base64 as _b64
                        data = _b64.b64decode(data)
                    out_path.write_bytes(data)
                    wrote = True
                    break
                if wrote:
                    break
        except Exception as exc:
            raise RuntimeError(
                f"GeminiPanelGenerator response parse error: {exc}"
            ) from exc
        if not wrote:
            raise RuntimeError(
                "GeminiPanelGenerator: response contained no inline image data"
            )

        action, units = self.default_cost
        return PanelGenerationResult(
            panel_path=out_path,
            cost_action=action,
            cost_units=units,
            metadata={"model": self.model},
        )


class PanelValidator(abc.ABC):
    """Validates a still PANEL image against the locked Asset Bible."""

    name: str = "panel_validator"

    @abc.abstractmethod
    def validate(
        self,
        *,
        shot: dict,
        panel_path: Path,
        character_refs: dict[str, Path],
        location_ref: Optional[Path],
        work_dir: Path,
    ) -> ValidationOutcome: ...

    def cost_estimate(self) -> tuple[str, float]:
        return ("anthropic_vision_call", 1.0)


class StubPanelValidator(PanelValidator):
    """Scriptable pass/fail for panel-gate tests.

    ``script`` maps ``shot_id -> list[ValidationOutcome | (score, passed, reasons)]``.
    Mirrors ``StubValidator`` semantics so panel tests look familiar.
    """

    name = "stub_panel_validator"

    def __init__(
        self,
        *,
        script: dict[str, list[Any]],
        cost_action: str = "anthropic_vision_call",
        cost_units: float = 1.0,
    ) -> None:
        self.script = {
            sid: [StubValidator._coerce(e) for e in entries]
            for sid, entries in script.items()
        }
        self._idx: dict[str, int] = {sid: 0 for sid in self.script}
        self._cost = (cost_action, cost_units)

    def cost_estimate(self) -> tuple[str, float]:
        return self._cost

    def validate(
        self,
        *,
        shot: dict,
        panel_path: Path,
        character_refs: dict[str, Path],
        location_ref: Optional[Path],
        work_dir: Path,
    ) -> ValidationOutcome:
        sid = shot["shot_id"]
        if sid not in self.script:
            raise KeyError(f"StubPanelValidator has no script for shot {sid!r}")
        entries = self.script[sid]
        idx = min(self._idx[sid], len(entries) - 1)
        self._idx[sid] = idx + 1
        out = entries[idx]
        action, units = self._cost
        out.cost_action = action
        out.cost_units = units
        return out


class RealPanelValidator(PanelValidator):
    """Wraps ``scripts.validate.shot_validator.validate_panel``.

    The same rubric the video validator uses, applied to a single still
    image. One vision call per panel attempt.
    """

    name = "real_panel"

    def __init__(
        self,
        *,
        backend: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.backend = backend
        self.model = model
        self._client = None
        self._effective_backend: Optional[str] = None
        self._effective_model: Optional[str] = None

    def cost_estimate(self) -> tuple[str, float]:
        return ("anthropic_vision_call", 1.0)

    def _lazy_init(self) -> None:
        if self._client is not None:
            return
        from scripts.validate import shot_validator as sv

        backend = self.backend or sv.DEFAULT_BACKEND
        model = self.model or sv._default_model_for_backend(backend)
        self._client = sv._make_client(backend)
        self._effective_backend = backend
        self._effective_model = model

    def validate(
        self,
        *,
        shot: dict,
        panel_path: Path,
        character_refs: dict[str, Path],
        location_ref: Optional[Path],
        work_dir: Path,
    ) -> ValidationOutcome:
        from scripts.validate import shot_validator as sv

        self._lazy_init()
        keyframes_dir = work_dir / "panel-keyframes"
        keyframes_dir.mkdir(parents=True, exist_ok=True)
        scratch_chars = work_dir / "scratch" / "characters"
        scratch_locs = work_dir / "scratch" / "locations"
        scratch_chars.mkdir(parents=True, exist_ok=True)
        scratch_locs.mkdir(parents=True, exist_ok=True)
        for name, path in character_refs.items():
            tgt = scratch_chars / (
                f"{name.lower()}_turnaround_APPROVED{path.suffix.lower()}"
            )
            if not tgt.exists():
                shutil.copyfile(path, tgt)
        if location_ref is not None:
            tgt = scratch_locs / (
                f"storyboard-{shot['shot_id']}{location_ref.suffix.lower()}"
            )
            if not tgt.exists():
                shutil.copyfile(location_ref, tgt)

        result = sv.validate_panel(
            shot=shot,
            panel_path=panel_path,
            characters_dir=scratch_chars,
            locations_dir=scratch_locs,
            keyframes_dir=keyframes_dir,
            backend=self._effective_backend,
            model=self._effective_model,
            client=self._client,
        )
        agg = result.aggregate_scores or {}
        sub = [
            float(agg.get("character_presence", 0.0)),
            float(agg.get("location_match", 0.0)),
            float(agg.get("artifacts", 0.0)),
        ]
        ids = agg.get("character_identity") or {}
        if ids:
            sub.append(sum(ids.values()) / len(ids))
        wds = agg.get("character_wardrobe") or {}
        if wds:
            sub.append(sum(wds.values()) / len(wds))
        score = sum(sub) / len(sub) if sub else 0.0
        action, units = self.cost_estimate()
        return ValidationOutcome(
            passed=bool(result.overall_pass),
            score=round(score, 4),
            reasons=list(result.reasons or []),
            cost_action=action,
            cost_units=units,
            raw=result.to_dict(),
        )


# ---------------------------------------------------------------------------
# Stitch validator interface (STITCH GATE)
# ---------------------------------------------------------------------------


class StitchValidator(abc.ABC):
    """Validates the assembled cut once stitching has completed.

    The stitch gate is non-looping: a failing stitch is reported but the
    pipeline does not retry stitch (re-running ffmpeg concat would not fix
    a cross-shot continuity problem; that requires regenerating one of the
    approved shots, which is a human-review decision).
    """

    name: str = "stitch_validator"

    @abc.abstractmethod
    def validate(
        self,
        *,
        manifest: list[dict],
        stitched_path: Path,
        approved_shots: list[str],
        work_dir: Path,
    ) -> StitchValidationOutcome: ...

    def cost_estimate(self) -> tuple[str, float]:
        return ("anthropic_vision_call", 0.0)


class AlwaysPassStitchValidator(StitchValidator):
    """Pass as long as the stitched file exists and is non-empty.

    Useful default for stub-tested runs and for not blocking the report on
    a fancier continuity check that has not been wired up yet.
    """

    name = "stitch_size_check"

    def validate(
        self,
        *,
        manifest: list[dict],
        stitched_path: Path,
        approved_shots: list[str],
        work_dir: Path,
    ) -> StitchValidationOutcome:
        if not stitched_path.exists():
            return StitchValidationOutcome(
                passed=False,
                reasons=[f"stitched output missing: {stitched_path}"],
            )
        size = stitched_path.stat().st_size
        if size <= 0:
            return StitchValidationOutcome(
                passed=False,
                reasons=[f"stitched output is empty: {stitched_path}"],
            )
        return StitchValidationOutcome(
            passed=True,
            notes=f"stitched {len(approved_shots)} clip(s); {size} bytes",
        )


class StubStitchValidator(StitchValidator):
    """Scriptable pass/fail for stitch-gate tests."""

    name = "stub_stitch"

    def __init__(self, *, outcome: StitchValidationOutcome) -> None:
        self._outcome = outcome

    def validate(
        self,
        *,
        manifest: list[dict],
        stitched_path: Path,
        approved_shots: list[str],
        work_dir: Path,
    ) -> StitchValidationOutcome:
        return self._outcome


# ---------------------------------------------------------------------------
# Reference resolution
# ---------------------------------------------------------------------------


_R2_BASE = "https://pub-97d84d215bf5412b8f7d32e7b9047c54.r2.dev"


def resolve_references(
    shot: dict,
    *,
    references_dir: Path,
    download_dir: Path,
    fetch_from_r2: bool = True,
) -> tuple[dict[str, Path], Optional[Path], Optional[Path]]:
    """Find the locked turnarounds + location plate + start frame for a shot.

    Looks first under ``references_dir/characters`` and
    ``references_dir/locations``; falls back to fetching the canonical
    files from R2 into ``download_dir`` so the orchestrator works on a
    fresh checkout where these aren't on disk.
    """
    char_dir = references_dir / "characters"
    loc_dir = references_dir / "locations"
    char_dir.mkdir(parents=True, exist_ok=True)
    loc_dir.mkdir(parents=True, exist_ok=True)

    char_refs: dict[str, Path] = {}
    for ch in shot.get("characters", []):
        slug = ch.lower()
        local = char_dir / f"{slug}_turnaround_APPROVED.png"
        if not local.exists() and fetch_from_r2:
            url = f"{_R2_BASE}/asset-bible/characters/{slug}_turnaround_APPROVED.png"
            target = download_dir / "characters" / f"{slug}_turnaround_APPROVED.png"
            try:
                if not target.exists():
                    _download_to(url, target)
                local = target
            except Exception:
                continue
        if local.exists():
            char_refs[ch] = local

    location_ref: Optional[Path] = None
    location = shot.get("location")
    if location:
        local = loc_dir / f"{location}.png"
        if not local.exists() and fetch_from_r2:
            url = f"{_R2_BASE}/asset-bible/locations/{location}.png"
            target = download_dir / "locations" / f"{location}.png"
            try:
                if not target.exists():
                    _download_to(url, target)
                local = target
            except Exception:
                local = local  # leave as-is; orchestrator will treat missing as None
        if local.exists():
            location_ref = local

    start_frame: Optional[Path] = None
    panel_url = shot.get("panel_url")
    if panel_url:
        suffix = ".png" if panel_url.endswith(".png") else ".jpg"
        target = download_dir / "start-frames" / f"{shot['shot_id']}{suffix}"
        try:
            if not target.exists():
                _download_to(panel_url, target)
            start_frame = target
        except Exception:
            start_frame = None

    return char_refs, location_ref, start_frame


# ---------------------------------------------------------------------------
# Stitching
# ---------------------------------------------------------------------------


def stitch_clips(clip_paths: list[Path], out_path: Path) -> Path:
    """Concat clips losslessly via ffmpeg's concat demuxer."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_path = out_path.with_suffix(".concat.txt")
    with open(list_path, "w") as f:
        for p in clip_paths:
            abs_p = str(p.resolve()).replace("'", "'\\''")
            f.write(f"file '{abs_p}'\n")
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0",
            "-i", str(list_path),
            "-c", "copy",
            str(out_path),
        ],
        check=True,
    )
    return out_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


@dataclass
class RunReport:
    scene_label: str
    halted: bool
    halted_reason: Optional[str]
    approved: list[str]
    escalated: list[tuple[str, str]]  # (shot_id, reason)
    skipped: list[str]
    stitched_path: Optional[Path]
    total_attempts: int
    total_spent_usd: float
    estimated_spend_usd: float
    state_path: Path
    report_path: Path
    # Per-stage gate outcomes
    panel_passed: list[str] = field(default_factory=list)
    panel_escalated: list[tuple[str, str]] = field(default_factory=list)
    video_passed: list[str] = field(default_factory=list)
    video_escalated: list[tuple[str, str]] = field(default_factory=list)
    stitch_passed: Optional[bool] = None
    stitch_reasons: list[str] = field(default_factory=list)


class Orchestrator:
    """Closed generate -> validate -> regenerate loop with budget + retry caps."""

    def __init__(
        self,
        manifest_path: Path,
        *,
        generator: Generator,
        validator: Validator,
        governor: CostGovernor,
        references_dir: Path,
        work_dir: Path,
        scene_label: str = "Scene",
        scene_slug: Optional[str] = None,
        report_dir: Optional[Path] = None,
        fetch_references_from_r2: bool = True,
        on_event: Optional[Callable[[str, dict[str, Any]], None]] = None,
        stitch_on_complete: bool = True,
        panel_generator: Optional[PanelGenerator] = None,
        panel_validator: Optional[PanelValidator] = None,
        stitch_validator: Optional[StitchValidator] = None,
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.manifest: list[dict] = json.loads(self.manifest_path.read_text())
        self.generator = generator
        self.validator = validator
        self.governor = governor
        self.references_dir = Path(references_dir)
        self.work_dir = Path(work_dir)
        self.scene_label = scene_label
        self.scene_slug = scene_slug or _scene_slug_from_manifest(self.manifest_path)
        self.report_dir = Path(report_dir) if report_dir else Path("reports")
        self.fetch_references_from_r2 = fetch_references_from_r2
        self.on_event = on_event or (lambda *_: None)
        self.stitch_on_complete = stitch_on_complete

        # Panel gate (PANEL GATE). Both panel_generator and panel_validator
        # are optional for backward compatibility with stub-only video tests.
        # When both are None, the panel gate auto-passes with the manifest's
        # existing panel (if any). When ANY is configured, the gate is fully
        # enforced and video generation is structurally unreachable until
        # the panel passes validation.
        self.panel_generator = panel_generator
        self.panel_validator = panel_validator

        # Stitch gate (STITCH GATE). Defaults to a size-check validator so
        # the gate is always present in some form; tests can override with
        # StubStitchValidator.
        self.stitch_validator = stitch_validator or AlwaysPassStitchValidator()

        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.work_dir / f"{self.scene_slug}-state.json"
        self.shots: dict[str, ShotState] = {}
        self._load_state()
        # Estimate spend for the entire run so we can warn the user up-front.
        self.estimated_spend_usd = self._estimate_run_spend()
        # Stitch gate outcome is populated by run_scene.
        self.stitch_outcome: Optional[StitchValidationOutcome] = None

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _load_state(self) -> None:
        if not self.state_path.exists():
            for shot in self.manifest:
                self.shots[shot["shot_id"]] = ShotState(shot_id=shot["shot_id"])
            self._flush_state()
            return
        try:
            payload = json.loads(self.state_path.read_text())
        except (json.JSONDecodeError, OSError):
            payload = {}
        loaded = payload.get("shots", {}) or {}
        for shot in self.manifest:
            sid = shot["shot_id"]
            raw = loaded.get(sid)
            if raw is None:
                self.shots[sid] = ShotState(shot_id=sid)
                continue
            self.shots[sid] = ShotState(
                shot_id=sid,
                status=raw.get("status", "pending"),
                panel_status=raw.get("panel_status", "pending"),
                panel_attempts=[
                    AttemptRecord(**a) for a in raw.get("panel_attempts", [])
                ],
                panel_path=raw.get("panel_path"),
                panel_escalation_reason=raw.get("panel_escalation_reason"),
                panel_last_reasons=list(raw.get("panel_last_reasons", [])),
                panel_last_score=float(raw.get("panel_last_score", 0.0)),
                attempts=[
                    AttemptRecord(**a) for a in raw.get("attempts", [])
                ],
                final_clip=raw.get("final_clip"),
                escalation_reason=raw.get("escalation_reason"),
                last_reasons=list(raw.get("last_reasons", [])),
                last_score=float(raw.get("last_score", 0.0)),
            )

    def _flush_state(self) -> None:
        payload = {
            "manifest_path": str(self.manifest_path),
            "scene_label": self.scene_label,
            "shots": {sid: s.to_dict() for sid, s in self.shots.items()},
        }
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)

    # ------------------------------------------------------------------
    # Spend estimation
    # ------------------------------------------------------------------

    def _estimate_run_spend(self) -> float:
        """Rough up-front estimate: one panel-validate + one generation +
        one video-validate per shot. If a panel generator is configured,
        we do NOT pre-charge for regeneration since attempt 0 reuses the
        manifest panel."""
        try:
            gen_action, gen_units = self.generator.cost_estimate(
                GenerationRequest(
                    shot=self.manifest[0],
                    attempt_index=0,
                    prior_reasons=[],
                    character_refs={},
                    location_ref=None,
                    start_frame=None,
                    output_path=Path("/dev/null"),
                )
            )
        except Exception:
            gen_action, gen_units = ("mitte_seedance_5s_shot", 1.0)
        val_action, val_units = self.validator.cost_estimate()
        per_shot = self.governor.estimate(gen_action, gen_units) + self.governor.estimate(
            val_action, val_units
        )
        if self.panel_validator is not None:
            pval_action, pval_units = self.panel_validator.cost_estimate()
            per_shot += self.governor.estimate(pval_action, pval_units)
        return per_shot * len(self.manifest)

    # ------------------------------------------------------------------
    # The loop
    # ------------------------------------------------------------------

    def run_scene(self) -> RunReport:
        self.on_event(
            "run_start",
            {
                "scene": self.scene_label,
                "shots": len(self.manifest),
                "estimated_spend_usd": round(self.estimated_spend_usd, 4),
                "budget_usd": self.governor.per_run_usd,
                "resumed_state": any(
                    s.status != "pending" for s in self.shots.values()
                ),
            },
        )

        # The orchestrator NEVER stitches until the loop completes or the
        # governor halts. We track per-shot status only.
        for shot in self.manifest:
            sid = shot["shot_id"]
            state = self.shots[sid]
            if state.status in ("approved", "escalated", "skipped"):
                self.on_event(
                    "shot_skip_already_done",
                    {"shot_id": sid, "status": state.status},
                )
                continue
            # Honor any halt that landed mid-run (e.g. KillSwitchTripped).
            if self.governor.halted:
                self.on_event(
                    "run_halted_before_shot",
                    {"shot_id": sid, "reason": self.governor.halted_reason},
                )
                break
            try:
                self._run_one_shot(shot, state)
            except PipelineHalted as exc:
                # Budget cap / kill switch / per-run attempts cap.
                # The shot may be marked escalated already; if not, leave
                # it pending so a later resume can pick it up.
                self.on_event(
                    "run_halted",
                    {"shot_id": sid, "reason": str(exc), "kind": type(exc).__name__},
                )
                break

        # Build the report and (optionally) stitch.
        report_path = self.report_dir / f"{self.scene_slug}-run.md"
        stitched_path = None
        approved = [
            s.shot_id for s in self.shots.values() if s.status == "approved"
        ]
        escalated = [
            (s.shot_id, s.escalation_reason or "")
            for s in self.shots.values()
            if s.status == "escalated"
        ]
        skipped = [
            s.shot_id for s in self.shots.values() if s.status == "skipped"
        ]
        all_resolved = all(
            self.shots[shot["shot_id"]].status in ("approved", "escalated", "skipped")
            for shot in self.manifest
        )
        if (
            self.stitch_on_complete
            and not self.governor.halted
            and all_resolved
            and approved
        ):
            try:
                stitched_path = stitch_clips(
                    [Path(self.shots[sid].final_clip) for sid in approved if self.shots[sid].final_clip],
                    self.report_dir / f"{self.scene_slug}-stitched.mp4",
                )
                self.on_event(
                    "stitched",
                    {"path": str(stitched_path), "n_clips": len(approved)},
                )
                # ---------- STITCH GATE ----------
                # Validate the assembled cut. A failing stitch gate is
                # reported but does not loop (the fix lies upstream).
                self._run_stitch_gate(
                    stitched_path=stitched_path,
                    approved_shots=approved,
                )
            except Exception as exc:
                self.on_event(
                    "stitch_failed", {"reason": str(exc)}
                )

        total_attempts = sum(
            len(s.attempts) + len(s.panel_attempts)
            for s in self.shots.values()
        )
        # Per-stage outcome lists for the report.
        panel_passed_list = [
            s.shot_id for s in self.shots.values() if s.panel_status == "passed"
        ]
        panel_escalated_list = [
            (s.shot_id, s.panel_escalation_reason or "")
            for s in self.shots.values()
            if s.panel_status == "escalated"
        ]
        video_passed_list = [
            s.shot_id for s in self.shots.values() if s.status == "approved"
        ]
        # A shot is "video-escalated" only if its panel passed but its
        # video gate then failed. Panel-escalated shots are reported
        # separately so the report distinguishes the two failure modes.
        video_escalated_list = [
            (s.shot_id, s.escalation_reason or "")
            for s in self.shots.values()
            if s.status == "escalated" and s.panel_status == "passed"
        ]

        self._write_report(report_path, stitched_path=stitched_path)

        report = RunReport(
            scene_label=self.scene_label,
            halted=self.governor.halted,
            halted_reason=self.governor.halted_reason,
            approved=approved,
            escalated=escalated,
            skipped=skipped,
            stitched_path=stitched_path,
            total_attempts=total_attempts,
            total_spent_usd=round(self.governor.total_spent_usd, 6),
            estimated_spend_usd=round(self.estimated_spend_usd, 6),
            state_path=self.state_path,
            report_path=report_path,
            panel_passed=panel_passed_list,
            panel_escalated=panel_escalated_list,
            video_passed=video_passed_list,
            video_escalated=video_escalated_list,
            stitch_passed=(self.stitch_outcome.passed if self.stitch_outcome else None),
            stitch_reasons=(
                list(self.stitch_outcome.reasons) if self.stitch_outcome else []
            ),
        )
        self.on_event("run_complete", asdict(report))
        return report

    # ------------------------------------------------------------------
    # Per-shot inner loop
    # ------------------------------------------------------------------

    def _run_one_shot(self, shot: dict, state: ShotState) -> None:
        """Run the gated per-shot pipeline: PANEL GATE then VIDEO GATE.

        Video generation is structurally unreachable until the panel gate
        has set ``state.panel_status == 'passed'``. The stitch gate runs
        once at the end of ``run_scene`` over all video-passed shots.
        """
        sid = shot["shot_id"]
        self.on_event("shot_start", {"shot_id": sid})

        # Resolve references once per shot (cached on disk).
        ref_download_dir = self.work_dir / "references"
        char_refs, location_ref, start_frame = resolve_references(
            shot,
            references_dir=self.references_dir,
            download_dir=ref_download_dir,
            fetch_from_r2=self.fetch_references_from_r2,
        )

        # ---------- PANEL GATE ----------
        if state.panel_status != "passed":
            panel_path = self._run_panel_gate(
                shot, state, char_refs, location_ref, start_frame
            )
            if state.panel_status == "escalated":
                # Video stage is structurally unreachable: we return here
                # without ever building a GenerationRequest for video.
                state.status = "escalated"
                state.escalation_reason = (
                    f"panel gate: {state.panel_escalation_reason}"
                )
                self._flush_state()
                self.on_event(
                    "shot_escalated",
                    {
                        "shot_id": sid,
                        "stage": "panel",
                        "reason": state.escalation_reason,
                    },
                )
                return
            # else: panel_status == "passed"; panel_path is the verified
            # storyboard panel to use as the video start frame.
        else:
            panel_path = (
                Path(state.panel_path) if state.panel_path else None
            )

        # ---------- VIDEO GATE ----------
        # By construction we only reach here with a panel that PASSED the
        # panel gate (or, in legacy auto-pass mode, with the manifest's
        # existing panel). The orchestrator's only call site for video
        # generation is below; there is no other code path.
        prior_keyframe = self._prior_keyframe(shot)
        video_start_frame = panel_path if panel_path is not None else start_frame

        while True:
            attempt_idx = len(state.attempts)
            attempt_started = _utcnow_iso()

            # 1) Pre-check: would the governor allow this attempt at all?
            #    register_attempt enforces per-shot/per-run caps + the
            #    no-progress guard; it raises before we spend a cent.
            video_gate_key = f"{sid}::video"
            try:
                last_score = state.last_score if state.attempts else None
                self.governor.register_attempt(video_gate_key, score=last_score)
            except (RetryCapExceeded, NoProgress) as exc:
                state.status = "escalated"
                state.escalation_reason = str(exc)
                self._flush_state()
                self.on_event(
                    "shot_escalated",
                    {"shot_id": sid, "stage": "video", "reason": str(exc)},
                )
                return
            except KillSwitchTripped:
                raise
            except PipelineHalted:
                # Governor already halted -> propagate up so the scene loop ends.
                raise

            # 2) Authorize the generator spend BEFORE calling it.
            req = GenerationRequest(
                shot=shot,
                attempt_index=attempt_idx,
                prior_reasons=list(state.last_reasons),
                character_refs=char_refs,
                location_ref=location_ref,
                start_frame=video_start_frame,
                output_path=self._attempt_clip_path(sid, attempt_idx),
                prior_clip=Path(state.attempts[-1].clip_path)
                if state.attempts and state.attempts[-1].clip_path
                else None,
            )
            gen_action, gen_units = self.generator.cost_estimate(req)
            try:
                self.governor.check_can_spend_strict(
                    gen_action, gen_units, shot_id=sid
                )
            except PipelineHalted:
                # We've already registered an attempt above, so back it out
                # of the shot's score history isn't possible — but the
                # attempt list is what shows up in the report. Mark it as
                # an errored attempt with no spend so the report is honest.
                state.attempts.append(
                    AttemptRecord(
                        index=attempt_idx,
                        started_at=attempt_started,
                        clip_path=None,
                        gen_cost_action=gen_action,
                        gen_cost_units=gen_units,
                        gen_cost_usd=0.0,
                        val_cost_action=None,
                        val_cost_units=0.0,
                        val_cost_usd=0.0,
                        passed=False,
                        score=0.0,
                        reasons=[],
                        error="budget_blocked_pre_generation",
                    )
                )
                self._flush_state()
                raise

            # 3) Generate. Failure -> failed attempt; the retry cap will
            #    eventually escalate if it keeps happening.
            gen_error: Optional[str] = None
            gen_cost_usd = 0.0
            val_cost_usd = 0.0
            val_action = None
            val_units = 0.0
            outcome = ValidationOutcome(passed=False, score=0.0, reasons=[])
            try:
                gen_result = self.generator.generate(req)
                spend_entry = self.governor.record_spend(
                    gen_result.cost_action,
                    gen_result.cost_units,
                    metadata={"shot_id": sid, "stage": "generate", **gen_result.metadata},
                    shot_id=sid,
                )
                gen_cost_usd = spend_entry.cost_usd
            except PipelineHalted:
                raise
            except Exception as exc:
                gen_error = f"generator: {exc}"
                gen_result = None

            # 4) Validate. Skip if generation failed.
            if gen_result is not None:
                val_action, val_units = self.validator.cost_estimate()
                try:
                    self.governor.check_can_spend_strict(
                        val_action, val_units, shot_id=sid
                    )
                except PipelineHalted:
                    state.attempts.append(
                        AttemptRecord(
                            index=attempt_idx,
                            started_at=attempt_started,
                            clip_path=str(gen_result.clip_path),
                            gen_cost_action=gen_result.cost_action,
                            gen_cost_units=gen_result.cost_units,
                            gen_cost_usd=gen_cost_usd,
                            val_cost_action=val_action,
                            val_cost_units=val_units,
                            val_cost_usd=0.0,
                            passed=False,
                            score=0.0,
                            reasons=[],
                            error="budget_blocked_pre_validation",
                        )
                    )
                    self._flush_state()
                    raise
                try:
                    outcome = self.validator.validate(
                        shot=shot,
                        media_path=gen_result.clip_path,
                        character_refs=char_refs,
                        location_ref=location_ref,
                        prior_keyframe=prior_keyframe,
                        work_dir=self.work_dir,
                    )
                except PipelineHalted:
                    raise
                except Exception as exc:
                    gen_error = (gen_error + " | " if gen_error else "") + f"validator: {exc}"
                else:
                    val_spend_entry = self.governor.record_spend(
                        outcome.cost_action or val_action,
                        outcome.cost_units or val_units,
                        metadata={"shot_id": sid, "stage": "validate"},
                        shot_id=sid,
                    )
                    val_cost_usd = val_spend_entry.cost_usd

            # 5) Persist attempt + per-shot state.
            attempt = AttemptRecord(
                index=attempt_idx,
                started_at=attempt_started,
                clip_path=str(gen_result.clip_path) if gen_result else None,
                gen_cost_action=gen_result.cost_action if gen_result else gen_action,
                gen_cost_units=gen_result.cost_units if gen_result else gen_units,
                gen_cost_usd=gen_cost_usd,
                val_cost_action=val_action,
                val_cost_units=val_units,
                val_cost_usd=val_cost_usd,
                passed=outcome.passed,
                score=outcome.score,
                reasons=list(outcome.reasons),
                error=gen_error,
            )
            state.attempts.append(attempt)
            state.last_reasons = list(outcome.reasons)
            state.last_score = outcome.score
            self._flush_state()
            self.on_event(
                "attempt_recorded",
                {
                    "shot_id": sid,
                    "attempt": attempt_idx,
                    "passed": outcome.passed,
                    "score": outcome.score,
                    "gen_cost_usd": round(gen_cost_usd, 4),
                    "val_cost_usd": round(val_cost_usd, 4),
                    "reasons": outcome.reasons[:3],
                    "error": gen_error,
                },
            )

            if outcome.passed:
                state.status = "approved"
                state.final_clip = str(gen_result.clip_path)
                self._flush_state()
                self.on_event("shot_approved", {"shot_id": sid, "attempts": attempt_idx + 1})
                return
            # else: loop and let register_attempt enforce caps on the next pass.

    # ------------------------------------------------------------------
    # Panel gate (PANEL GATE)
    # ------------------------------------------------------------------

    def _run_panel_gate(
        self,
        shot: dict,
        state: ShotState,
        char_refs: dict[str, Path],
        location_ref: Optional[Path],
        existing_panel: Optional[Path],
    ) -> Optional[Path]:
        """Run the panel-gate generate/validate loop for one shot.

        Returns the verified panel ``Path`` on PASS, ``None`` when the gate
        escalates (and ``state.panel_status`` is set accordingly). Video
        generation is only reachable when this returns a Path.

        Attempt 0 reuses the manifest's existing panel (no regeneration
        cost); attempts 1+ invoke ``self.panel_generator`` to redraw the
        panel from the locked turnarounds. If no ``panel_generator`` is
        configured and the first panel fails, the gate escalates because
        no retry is possible.

        When BOTH ``panel_generator`` and ``panel_validator`` are None the
        gate auto-passes (legacy mode) so existing video-only stub tests
        keep working; production setups must pass at least a validator.
        """
        sid = shot["shot_id"]
        gate_key = f"{sid}::panel"

        # Auto-pass legacy mode: no validator AND no generator configured.
        if self.panel_validator is None and self.panel_generator is None:
            state.panel_status = "passed"
            state.panel_path = str(existing_panel) if existing_panel else None
            self._flush_state()
            self.on_event(
                "panel_gate_auto_passed",
                {
                    "shot_id": sid,
                    "reason": "no panel gate configured (legacy mode)",
                    "panel_path": state.panel_path,
                },
            )
            return existing_panel

        # If the validator is missing but a generator is set, that is a
        # misconfiguration — without validation there is no gate.
        if self.panel_validator is None:
            raise RuntimeError(
                "panel_generator was provided without a panel_validator; "
                "the panel gate requires a validator to be a real gate."
            )

        while True:
            attempt_idx = len(state.panel_attempts)
            attempt_started = _utcnow_iso()

            # 1) Retry-cap / no-progress check
            try:
                last_score = (
                    state.panel_last_score if state.panel_attempts else None
                )
                self.governor.register_attempt(gate_key, score=last_score)
            except (RetryCapExceeded, NoProgress) as exc:
                state.panel_status = "escalated"
                state.panel_escalation_reason = str(exc)
                self._flush_state()
                self.on_event(
                    "panel_gate_escalated",
                    {"shot_id": sid, "reason": str(exc)},
                )
                return None
            except KillSwitchTripped:
                raise
            except PipelineHalted:
                raise

            # 2) Acquire a panel for this attempt.
            #    Attempt 0: reuse the manifest's existing panel (no
            #    generator cost). Attempts 1+: regenerate via
            #    self.panel_generator. If attempt 0 has no existing panel,
            #    fall through to the generator.
            panel_path_for_attempt: Optional[Path] = None
            gen_cost_usd = 0.0
            gen_action: Optional[str] = None
            gen_units: float = 0.0
            gen_error: Optional[str] = None
            gen_metadata: dict[str, Any] = {}

            use_existing = attempt_idx == 0 and existing_panel is not None
            if use_existing:
                panel_path_for_attempt = existing_panel
                gen_action = "manifest_panel"  # not a paid action
                gen_units = 0.0
                gen_metadata = {"source": str(existing_panel), "via": "manifest"}
            else:
                if self.panel_generator is None:
                    # No way to regenerate; escalate immediately.
                    state.panel_status = "escalated"
                    state.panel_escalation_reason = (
                        "panel failed and no panel_generator is configured "
                        "to regenerate it"
                    )
                    state.panel_attempts.append(
                        AttemptRecord(
                            index=attempt_idx,
                            started_at=attempt_started,
                            clip_path=None,
                            gen_cost_action=None,
                            gen_cost_units=0.0,
                            gen_cost_usd=0.0,
                            val_cost_action=None,
                            val_cost_units=0.0,
                            val_cost_usd=0.0,
                            passed=False,
                            score=0.0,
                            reasons=[],
                            error="no_panel_generator_for_retry",
                        )
                    )
                    self._flush_state()
                    self.on_event(
                        "panel_gate_escalated",
                        {
                            "shot_id": sid,
                            "reason": state.panel_escalation_reason,
                        },
                    )
                    return None

                preq = PanelGenerationRequest(
                    shot=shot,
                    attempt_index=attempt_idx,
                    prior_reasons=list(state.panel_last_reasons),
                    character_refs=char_refs,
                    location_ref=location_ref,
                    output_path=self._attempt_panel_path(sid, attempt_idx),
                    existing_panel=existing_panel,
                    prior_panel=Path(state.panel_attempts[-1].clip_path)
                    if state.panel_attempts and state.panel_attempts[-1].clip_path
                    else None,
                )
                gen_action, gen_units = self.panel_generator.cost_estimate(preq)
                try:
                    self.governor.check_can_spend_strict(
                        gen_action, gen_units, shot_id=sid
                    )
                except PipelineHalted:
                    state.panel_attempts.append(
                        AttemptRecord(
                            index=attempt_idx,
                            started_at=attempt_started,
                            clip_path=None,
                            gen_cost_action=gen_action,
                            gen_cost_units=gen_units,
                            gen_cost_usd=0.0,
                            val_cost_action=None,
                            val_cost_units=0.0,
                            val_cost_usd=0.0,
                            passed=False,
                            score=0.0,
                            reasons=[],
                            error="budget_blocked_pre_panel_generation",
                        )
                    )
                    self._flush_state()
                    raise

                try:
                    gres = self.panel_generator.generate(preq)
                except PipelineHalted:
                    raise
                except Exception as exc:
                    gen_error = f"panel_generator: {exc}"
                    gres = None

                if gres is not None:
                    spend_entry = self.governor.record_spend(
                        gres.cost_action,
                        gres.cost_units,
                        metadata={
                            "shot_id": sid,
                            "stage": "panel_generate",
                            **gres.metadata,
                        },
                        shot_id=sid,
                    )
                    gen_cost_usd = spend_entry.cost_usd
                    panel_path_for_attempt = gres.panel_path
                    gen_action = gres.cost_action
                    gen_units = gres.cost_units
                    gen_metadata = gres.metadata

            # 3) Validate the panel (or skip validation if generator failed).
            val_action, val_units = self.panel_validator.cost_estimate()
            val_cost_usd = 0.0
            outcome = ValidationOutcome(passed=False, score=0.0, reasons=[])
            if panel_path_for_attempt is not None:
                try:
                    self.governor.check_can_spend_strict(
                        val_action, val_units, shot_id=sid
                    )
                except PipelineHalted:
                    state.panel_attempts.append(
                        AttemptRecord(
                            index=attempt_idx,
                            started_at=attempt_started,
                            clip_path=str(panel_path_for_attempt),
                            gen_cost_action=gen_action,
                            gen_cost_units=gen_units,
                            gen_cost_usd=gen_cost_usd,
                            val_cost_action=val_action,
                            val_cost_units=val_units,
                            val_cost_usd=0.0,
                            passed=False,
                            score=0.0,
                            reasons=[],
                            error="budget_blocked_pre_panel_validation",
                        )
                    )
                    self._flush_state()
                    raise
                try:
                    outcome = self.panel_validator.validate(
                        shot=shot,
                        panel_path=panel_path_for_attempt,
                        character_refs=char_refs,
                        location_ref=location_ref,
                        work_dir=self.work_dir,
                    )
                except PipelineHalted:
                    raise
                except Exception as exc:
                    gen_error = (
                        (gen_error + " | " if gen_error else "")
                        + f"panel_validator: {exc}"
                    )
                else:
                    val_spend = self.governor.record_spend(
                        outcome.cost_action or val_action,
                        outcome.cost_units or val_units,
                        metadata={"shot_id": sid, "stage": "panel_validate"},
                        shot_id=sid,
                    )
                    val_cost_usd = val_spend.cost_usd

            # 4) Record the panel attempt.
            attempt = AttemptRecord(
                index=attempt_idx,
                started_at=attempt_started,
                clip_path=str(panel_path_for_attempt)
                if panel_path_for_attempt
                else None,
                gen_cost_action=gen_action,
                gen_cost_units=gen_units,
                gen_cost_usd=gen_cost_usd,
                val_cost_action=val_action,
                val_cost_units=val_units,
                val_cost_usd=val_cost_usd,
                passed=outcome.passed,
                score=outcome.score,
                reasons=list(outcome.reasons),
                error=gen_error,
            )
            state.panel_attempts.append(attempt)
            state.panel_last_reasons = list(outcome.reasons)
            state.panel_last_score = outcome.score
            self._flush_state()
            self.on_event(
                "panel_attempt_recorded",
                {
                    "shot_id": sid,
                    "attempt": attempt_idx,
                    "passed": outcome.passed,
                    "score": outcome.score,
                    "via": gen_metadata.get("via", "regenerate"),
                    "gen_cost_usd": round(gen_cost_usd, 4),
                    "val_cost_usd": round(val_cost_usd, 4),
                    "reasons": outcome.reasons[:3],
                    "error": gen_error,
                },
            )

            if outcome.passed:
                state.panel_status = "passed"
                state.panel_path = str(panel_path_for_attempt)
                self._flush_state()
                self.on_event(
                    "panel_gate_passed",
                    {
                        "shot_id": sid,
                        "attempts": attempt_idx + 1,
                        "panel_path": state.panel_path,
                    },
                )
                return panel_path_for_attempt
            # else: loop; register_attempt on the next pass enforces caps.

    # ------------------------------------------------------------------
    # Stitch gate (STITCH GATE)
    # ------------------------------------------------------------------

    def _run_stitch_gate(
        self,
        *,
        stitched_path: Path,
        approved_shots: list[str],
    ) -> StitchValidationOutcome:
        try:
            outcome = self.stitch_validator.validate(
                manifest=self.manifest,
                stitched_path=stitched_path,
                approved_shots=approved_shots,
                work_dir=self.work_dir,
            )
        except Exception as exc:
            outcome = StitchValidationOutcome(
                passed=False,
                reasons=[f"stitch_validator raised: {exc}"],
            )
        self.stitch_outcome = outcome
        self.on_event(
            "stitch_gate",
            {
                "passed": outcome.passed,
                "reasons": outcome.reasons,
                "notes": outcome.notes,
            },
        )
        return outcome

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _attempt_panel_path(self, shot_id: str, attempt_idx: int) -> Path:
        panels_dir = self.work_dir / "panels" / shot_id
        panels_dir.mkdir(parents=True, exist_ok=True)
        return panels_dir / f"attempt-{attempt_idx:02d}.png"

    def _attempt_clip_path(self, shot_id: str, attempt_idx: int) -> Path:
        clips_dir = self.work_dir / "clips" / shot_id
        clips_dir.mkdir(parents=True, exist_ok=True)
        return clips_dir / f"attempt-{attempt_idx:02d}.mp4"

    def _prior_keyframe(self, shot: dict) -> Optional[Path]:
        """Last keyframe of the previous shot's final clip, if any.

        We extract it lazily on demand from the approved clip of the
        manifest-order predecessor."""
        sid = shot["shot_id"]
        prev_sid = None
        for s in self.manifest:
            if s["shot_id"] == sid:
                break
            prev_sid = s["shot_id"]
        if prev_sid is None:
            return None
        prev = self.shots.get(prev_sid)
        if not prev or not prev.final_clip:
            return None
        out = self.work_dir / "prior-keyframes" / f"{prev_sid}-last.jpg"
        if out.exists():
            return out
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-sseof", "-0.5",
                    "-i", prev.final_clip,
                    "-update", "1",
                    "-q:v", "3",
                    str(out),
                ],
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
        return out if out.exists() else None

    def _write_report(self, path: Path, *, stitched_path: Optional[Path]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        s = self.governor.summary()
        lines.append(f"# {self.scene_label} - Pipeline Orchestrator Run Report")
        lines.append("")
        lines.append(f"- Generated: {_utcnow_iso()}")
        lines.append(f"- Manifest: `{self.manifest_path}`")
        lines.append(f"- Video generator: `{self.generator.name}`")
        lines.append(f"- Video validator: `{self.validator.name}`")
        lines.append(
            f"- Panel generator: "
            f"`{self.panel_generator.name if self.panel_generator else '(none)'}`"
        )
        lines.append(
            f"- Panel validator: "
            f"`{self.panel_validator.name if self.panel_validator else '(none - legacy auto-pass)'}`"
        )
        lines.append(f"- Stitch validator: `{self.stitch_validator.name}`")
        lines.append(f"- Run state file: `{self.state_path}`")
        lines.append(f"- Governor state file: `{s.get('state_path','?')}`")
        lines.append("")
        lines.append("## Budget summary")
        lines.append("")
        lines.append(
            f"- Up-front estimate for this scene: **${self.estimated_spend_usd:.4f}** "
            f"(generator + validator, one attempt per shot)"
        )
        lines.append(
            f"- Per-run cap: **${s['per_run_usd']:.2f}**  -  "
            f"actually spent so far: **${s['total_spent_usd']:.4f}**  -  "
            f"remaining: **${s['remaining_run_usd']:.4f}**"
        )
        lines.append(
            f"- Daily cap: **${s['daily_usd']:.2f}**  -  "
            f"spent today: **${s['daily_spent_usd']:.4f}**"
        )
        if s["halted"]:
            lines.append(f"- **HALTED**: {s['halted_reason']}")
        lines.append("")

        # Outcome counters
        approved = [s.shot_id for s in self.shots.values() if s.status == "approved"]
        escalated = [s for s in self.shots.values() if s.status == "escalated"]
        pending = [s.shot_id for s in self.shots.values() if s.status == "pending"]
        lines.append("## Shot outcomes")
        lines.append("")
        lines.append(
            f"- Approved: **{len(approved)}** / {len(self.manifest)}  -  "
            f"Escalated: **{len(escalated)}**  -  "
            f"Pending (not yet attempted): **{len(pending)}**"
        )
        lines.append("")
        lines.append("| Shot | Status | Attempts | Last score | Last reasons |")
        lines.append("|------|--------|----------|------------|--------------|")
        for shot in self.manifest:
            st = self.shots[shot["shot_id"]]
            reasons = "; ".join(st.last_reasons[:2]) if st.last_reasons else ""
            if st.status == "escalated":
                reasons = (st.escalation_reason or "").splitlines()[0][:160]
            lines.append(
                f"| {st.shot_id} | **{st.status}** | {len(st.attempts)} | "
                f"{st.last_score:.2f} | {reasons} |"
            )
        lines.append("")

        # Per-stage gate outcomes (PANEL / VIDEO / STITCH).
        lines.append("## Per-stage gate outcomes")
        lines.append("")
        lines.append(
            "| Shot | Panel gate | Panel attempts | Panel score | Video gate | "
            "Video attempts | Video score |"
        )
        lines.append(
            "|------|------------|----------------|-------------|------------|"
            "----------------|-------------|"
        )
        for shot in self.manifest:
            st = self.shots[shot["shot_id"]]
            lines.append(
                f"| {st.shot_id} | **{st.panel_status}** | {len(st.panel_attempts)} | "
                f"{st.panel_last_score:.2f} | **{st.status}** | {len(st.attempts)} | "
                f"{st.last_score:.2f} |"
            )
        lines.append("")
        # Stitch gate row
        if self.stitch_outcome is not None:
            stitch_str = "PASS" if self.stitch_outcome.passed else "FAIL"
            reasons_str = (
                "; ".join(self.stitch_outcome.reasons[:3])
                if self.stitch_outcome.reasons
                else (self.stitch_outcome.notes or "")
            )
            lines.append(
                f"- **Stitch gate**: {stitch_str} ({reasons_str})"
            )
        else:
            lines.append(
                "- **Stitch gate**: not run "
                "(scene did not stitch — see budget/escalation above)"
            )
        lines.append("")

        if escalated:
            lines.append("## Escalations (for human review)")
            lines.append("")
            for st in escalated:
                lines.append(f"### {st.shot_id}")
                lines.append("")
                stage = (
                    "panel"
                    if st.panel_status == "escalated"
                    else "video"
                )
                lines.append(f"- Stage: {stage}")
                lines.append(f"- Reason: {st.escalation_reason}")
                last_reasons = (
                    st.panel_last_reasons
                    if stage == "panel"
                    else st.last_reasons
                )
                if last_reasons:
                    lines.append("- Last validator reasons:")
                    for r in last_reasons[:8]:
                        lines.append(f"  - {r}")
                lines.append("")

        if stitched_path is not None:
            lines.append("## Stitched output")
            lines.append("")
            lines.append(f"- `{stitched_path}` (approved clips only)")
            lines.append("")

        lines.append("## Per-shot attempt log")
        lines.append("")
        for shot in self.manifest:
            st = self.shots[shot["shot_id"]]
            lines.append(f"### {st.shot_id} - shot status: {st.status}")
            lines.append("")

            # Panel-stage table
            lines.append(f"**Panel gate**: {st.panel_status}")
            if st.panel_attempts:
                lines.append("")
                lines.append(
                    "| # | passed | score | gen $ | val $ | error | reasons |"
                )
                lines.append(
                    "|---|--------|-------|-------|-------|-------|---------|"
                )
                for a in st.panel_attempts:
                    err = a.error or ""
                    rstr = "; ".join(a.reasons[:2])
                    lines.append(
                        f"| {a.index} | {'yes' if a.passed else 'no'} | "
                        f"{a.score:.2f} | ${a.gen_cost_usd:.4f} | "
                        f"${a.val_cost_usd:.4f} | {err} | {rstr} |"
                    )
            else:
                lines.append("(no panel attempts recorded)")
            lines.append("")

            # Video-stage table
            lines.append(f"**Video gate**: {st.status}")
            if st.attempts:
                lines.append("")
                lines.append(
                    "| # | passed | score | gen $ | val $ | error | reasons |"
                )
                lines.append(
                    "|---|--------|-------|-------|-------|-------|---------|"
                )
                for a in st.attempts:
                    err = a.error or ""
                    rstr = "; ".join(a.reasons[:2])
                    lines.append(
                        f"| {a.index} | {'yes' if a.passed else 'no'} | "
                        f"{a.score:.2f} | ${a.gen_cost_usd:.4f} | "
                        f"${a.val_cost_usd:.4f} | {err} | {rstr} |"
                    )
            else:
                lines.append("(no video attempts recorded)")
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")


def _scene_slug_from_manifest(manifest_path: Path) -> str:
    stem = manifest_path.stem
    return stem if stem.startswith("scene-") else f"scene-{stem}"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_event(name: str, data: dict[str, Any]) -> None:
    print(f"[{name}] " + json.dumps(data, default=str), flush=True)


def _make_generator(name: str, args: argparse.Namespace) -> Generator:
    if name == "stub":
        return StubGenerator(clip_path=Path(args.stub_clip))
    if name == "existing_clips":
        return ExistingClipsGenerator(
            local_clips_dir=Path(args.existing_clips_dir) if args.existing_clips_dir else None,
            download_dir=Path(args.work_dir) / "downloaded-clips",
            scene_slug=_scene_slug_from_manifest(Path(args.manifest)),
        )
    if name == "mitte":
        return MitteSeedanceGenerator(
            storage_state=Path(args.mitte_storage_state) if args.mitte_storage_state else None,
            headless=not args.mitte_headed,
            debug_dir=Path(args.work_dir) / "mitte-debug",
        )
    raise ValueError(f"unknown generator: {name}")


def _make_validator(name: str, args: argparse.Namespace) -> Validator:
    if name == "real":
        return RealValidator(backend=args.validator_backend, model=args.validator_model)
    if name == "stub_pass":
        return StubValidator(
            script={
                shot["shot_id"]: [(1.0, True, [])]
                for shot in json.loads(Path(args.manifest).read_text())
            },
        )
    raise ValueError(f"unknown validator: {name}")


def _make_panel_generator(name: str, args: argparse.Namespace) -> Optional[PanelGenerator]:
    if name in (None, "none"):
        return None
    if name == "gemini":
        return GeminiPanelGenerator(
            model=getattr(args, "panel_generator_model", None) or "gemini-2.5-flash-image",
        )
    raise ValueError(f"unknown panel generator: {name}")


def _make_panel_validator(name: str, args: argparse.Namespace) -> Optional[PanelValidator]:
    if name in (None, "none"):
        return None
    if name == "real":
        return RealPanelValidator(
            backend=args.validator_backend, model=args.validator_model
        )
    if name == "stub_pass":
        return StubPanelValidator(
            script={
                shot["shot_id"]: [(1.0, True, [])]
                for shot in json.loads(Path(args.manifest).read_text())
            },
        )
    raise ValueError(f"unknown panel validator: {name}")


def cmd_run(args: argparse.Namespace) -> int:
    governor = CostGovernor(
        run_id=args.run_id or _scene_slug_from_manifest(Path(args.manifest)),
        per_run_usd=float(args.budget),
        daily_usd=float(args.daily_budget),
        per_shot_attempts=int(args.per_shot_attempts),
        per_run_attempts=int(args.per_run_attempts),
        state_dir=Path(args.work_dir) / "governor",
        daily_state_path=Path(args.work_dir) / "governor" / "daily.json",
        kill_switch_path=Path(args.work_dir) / "STOP",
        report_dir=Path(args.report_dir or "reports"),
        dry_run=args.dry_run,
    )
    generator = _make_generator(args.generator, args)
    validator = _make_validator(args.validator, args)
    panel_generator = _make_panel_generator(args.panel_generator, args)
    panel_validator = _make_panel_validator(args.panel_validator, args)
    orch = Orchestrator(
        manifest_path=Path(args.manifest),
        generator=generator,
        validator=validator,
        governor=governor,
        references_dir=Path(args.references_dir),
        work_dir=Path(args.work_dir),
        scene_label=args.scene_label or _scene_slug_from_manifest(Path(args.manifest)),
        report_dir=Path(args.report_dir) if args.report_dir else Path("reports"),
        fetch_references_from_r2=not args.no_r2_fetch,
        on_event=_print_event,
        stitch_on_complete=not args.no_stitch,
        panel_generator=panel_generator,
        panel_validator=panel_validator,
    )
    report = orch.run_scene()
    governor.write_report()
    print()
    print(f"== run complete ==")
    print(f"  approved:  {len(report.approved)} / {len(orch.manifest)}")
    print(f"  escalated: {len(report.escalated)}")
    print(f"  spent:     ${report.total_spent_usd:.4f} of ${governor.per_run_usd:.2f} cap")
    print(f"  estimate:  ${report.estimated_spend_usd:.4f}")
    print(f"  report:    {report.report_path}")
    if report.stitched_path:
        print(f"  stitched:  {report.stitched_path}")
    if report.halted:
        print(f"  HALTED:    {report.halted_reason}")
        return 2
    return 0 if not report.escalated else 1


def cmd_demo(args: argparse.Namespace) -> int:
    """In-process stub demo: 3 shots, pass + retry + escalate, $0 paid."""
    import tempfile
    from . import orchestrator as self_mod  # so test code can monkeypatch easily

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # 1) Build a fake 1-frame MP4 clip used by the stub generator.
        clip = td_path / "stub.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi",
                "-i", "color=c=black:s=64x64:d=0.5:r=10",
                "-pix_fmt", "yuv420p",
                str(clip),
            ],
            check=True,
        )
        # 2) Build a 2-shot manifest.
        manifest = [
            {
                "shot_id": "demoA",
                "location": "demo_room",
                "characters": [],
                "wardrobe": {},
                "key_props": ["nothing"],
                "camera": "static, 2s",
            },
            {
                "shot_id": "demoB",
                "location": "demo_room",
                "characters": [],
                "wardrobe": {},
                "key_props": ["nothing"],
                "camera": "static, 2s",
            },
            {
                "shot_id": "demoC",
                "location": "demo_room",
                "characters": [],
                "wardrobe": {},
                "key_props": ["nothing"],
                "camera": "static, 2s",
            },
        ]
        manifest_path = td_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        gen = StubGenerator(clip_path=clip)
        # demoA passes first try. demoB fails twice then passes. demoC
        # fails forever -> escalated after per-shot cap.
        validator = StubValidator(
            script={
                "demoA": [(1.0, True, [])],
                "demoB": [
                    (0.40, False, ["wardrobe drift"]),
                    (0.55, False, ["wardrobe drift"]),
                    (1.0, True, []),
                ],
                "demoC": [
                    (0.30, False, ["totally broken"]),
                    (0.30, False, ["totally broken"]),
                    (0.30, False, ["totally broken"]),
                    (0.30, False, ["totally broken"]),
                ],
            },
        )
        governor = CostGovernor(
            run_id="demo_orchestrator",
            per_run_usd=5.0,
            daily_usd=1000.0,
            per_shot_attempts=3,
            per_run_attempts=20,
            state_dir=td_path / "gov",
            daily_state_path=td_path / "gov-daily.json",
            kill_switch_path=td_path / "STOP",
            report_dir=td_path / "reports",
        )
        orch = self_mod.Orchestrator(
            manifest_path=manifest_path,
            generator=gen,
            validator=validator,
            governor=governor,
            references_dir=td_path / "refs",
            work_dir=td_path / "work",
            scene_label="Demo",
            report_dir=td_path / "reports",
            fetch_references_from_r2=False,
            on_event=_print_event,
        )
        report = orch.run_scene()
        print()
        print("== demo summary ==")
        print(f"  approved:  {report.approved}")
        print(f"  escalated: {[sid for sid, _ in report.escalated]}")
        print(f"  total attempts: {report.total_attempts}")
        print(f"  spent: ${report.total_spent_usd:.4f} of ${governor.per_run_usd:.2f}")
        print(f"  report: {report.report_path}")
        # Quick sanity assertions so the demo IS a smoke test.
        assert "demoA" in report.approved, report
        assert "demoB" in report.approved, report
        assert any(sid == "demoC" for sid, _ in report.escalated), report
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Run the orchestrator on a scene manifest.")
    r.add_argument("--manifest", required=True)
    r.add_argument("--references-dir", default="asset-bible")
    r.add_argument("--work-dir", default="footage/scene-run")
    r.add_argument("--report-dir", default="reports")
    r.add_argument("--scene-label", default=None)
    r.add_argument("--run-id", default=None)
    r.add_argument("--budget", default="15.0",
                   help="Per-run dollar cap (default $15).")
    r.add_argument("--daily-budget", default="40.0")
    r.add_argument("--per-shot-attempts", default=3, type=int)
    r.add_argument("--per-run-attempts", default=30, type=int)
    r.add_argument("--generator", default="existing_clips",
                   choices=["stub", "existing_clips", "mitte"])
    r.add_argument("--validator", default="real", choices=["real", "stub_pass"])
    r.add_argument("--validator-backend", default=None, choices=[None, "claude", "gemini"])
    r.add_argument("--validator-model", default=None)
    r.add_argument("--panel-generator", default="none",
                   choices=["none", "gemini"],
                   help="Panel REGENERATOR for retries. 'none' = no regeneration "
                        "(first-attempt failures escalate); 'gemini' = real "
                        "Gemini image-to-image from the locked turnarounds.")
    r.add_argument("--panel-generator-model", default=None,
                   help="Override the panel generator's model name.")
    r.add_argument("--panel-validator", default="none",
                   choices=["none", "real", "stub_pass"],
                   help="Panel VALIDATOR. 'none' = legacy auto-pass (NOT for "
                        "production scenes); 'real' = same vision rubric as "
                        "the video validator; 'stub_pass' = always-pass stub.")
    r.add_argument("--stub-clip", default=None)
    r.add_argument("--existing-clips-dir", default=None,
                   help="Local dir of pre-generated clips (e.g. footage/scene-01/shots)")
    r.add_argument("--mitte-storage-state", default=None,
                   help="Path to a Playwright storage_state JSON (cookies/login).")
    r.add_argument("--mitte-headed", action="store_true",
                   help="Run mitte browser in headed mode for debugging.")
    r.add_argument("--no-r2-fetch", action="store_true",
                   help="Don't try to download references from R2.")
    r.add_argument("--no-stitch", action="store_true",
                   help="Skip the final ffmpeg stitch.")
    r.add_argument("--dry-run", action="store_true",
                   help="Pass through to the cost governor (still counts spend).")
    r.set_defaults(func=cmd_run)

    d = sub.add_parser("demo", help="Run the in-process stub demo (zero paid calls).")
    d.set_defaults(func=cmd_demo)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
