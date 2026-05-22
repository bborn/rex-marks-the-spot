"""Self-correcting animation pipeline modules.

The :mod:`scripts.pipeline.cost_governor` module enforces hard spend caps
and runaway-loop circuit breakers across every paid call in the pipeline.

The :mod:`scripts.pipeline.orchestrator` module wires that governor up to
a pluggable Generator + Validator pair to drive the closed
generate -> validate -> regenerate loop for a whole scene.
"""

from .cost_governor import (
    BudgetExceeded,
    CostGovernor,
    KillSwitchTripped,
    NoProgress,
    PRICING,
    PipelineHalted,
    RetryCapExceeded,
)
from .orchestrator import (
    ExistingClipsGenerator,
    Generator,
    GenerationRequest,
    GenerationResult,
    MitteSeedanceGenerator,
    Orchestrator,
    RealValidator,
    RunReport,
    ShotState,
    StubGenerator,
    StubValidator,
    Validator,
    ValidationOutcome,
)

__all__ = [
    "BudgetExceeded",
    "CostGovernor",
    "ExistingClipsGenerator",
    "Generator",
    "GenerationRequest",
    "GenerationResult",
    "KillSwitchTripped",
    "MitteSeedanceGenerator",
    "NoProgress",
    "Orchestrator",
    "PRICING",
    "PipelineHalted",
    "RealValidator",
    "RetryCapExceeded",
    "RunReport",
    "ShotState",
    "StubGenerator",
    "StubValidator",
    "ValidationOutcome",
    "Validator",
]
