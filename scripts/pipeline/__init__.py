"""Self-correcting animation pipeline modules.

The :mod:`scripts.pipeline.cost_governor` module enforces hard spend caps
and runaway-loop circuit breakers across every paid call in the pipeline.
Other pipeline components must import and consult ``CostGovernor`` before
each paid action.
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

__all__ = [
    "BudgetExceeded",
    "CostGovernor",
    "KillSwitchTripped",
    "NoProgress",
    "PRICING",
    "PipelineHalted",
    "RetryCapExceeded",
]
