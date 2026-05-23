"""EvidenceRecord: a piece of cross-layer evidence linking a question to data.

Evidence is accumulated during the profiling loop and summarized in the report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceRecord:
    evidence_id: str
    question_id: str            # which diagnostic question this addresses
    plan_id: str                # which observation plan produced this
    observer: str               # which observer collected it
    layer: str
    finding: str                # human-readable summary of what was found
    data_ref: str               # path to supporting file (e.g. metrics.csv)
    attrs: dict[str, Any] = field(default_factory=dict)
    confidence: str = "low"     # low | medium | high
