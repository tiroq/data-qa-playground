"""Availability and uncertainty of raw events for one business key.

The context is independent of DQ findings: a confirmed anomaly can coexist
with incomplete coverage of the source/target event population.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class SideQuality:
    # At least one malformed row may belong to this key and side.
    possibly_excluded: bool = False
    # An excluded row could change the maximum version or its payload.
    latest_uncertain: bool = False


@dataclass(frozen=True, slots=True)
class CheckContext:
    source: SideQuality = field(default_factory=SideQuality)
    target: SideQuality = field(default_factory=SideQuality)

    def for_side(self, side: Literal["source", "target"]) -> SideQuality:
        if side == "source":
            return self.source
        if side == "target":
            return self.target
        raise ValueError(f"Unknown side {side!r}")
