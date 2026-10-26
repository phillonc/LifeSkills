"""Timebox planner tool.

Fits prioritised requirements into a fixed-capacity timebox. Must Haves are
always committed (the deadline flexes nothing essential); Should then Could Haves
fill the remaining capacity in priority order. Won't Haves are excluded. If the
Must Haves alone exceed capacity, the timebox is flagged as over-committed.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..core.tool import Tool

_PRIORITY_ORDER = {"M": 0, "S": 1, "C": 2}


class TimeboxPlannerTool(Tool):
    name = "timebox_planner"
    description = "Plan a fixed-length timebox by fitting MoSCoW-prioritised work to capacity."

    def run(
        self,
        prl: List[Dict[str, Any]],
        capacity: float,
        length_weeks: int = 2,
    ) -> Dict[str, Any]:
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        candidates = [r for r in prl if r["priority"] != "W"]
        candidates.sort(key=lambda r: _PRIORITY_ORDER.get(r["priority"], 3))

        must_effort = sum(float(r["effort"]) for r in candidates if r["priority"] == "M")

        included: List[Dict[str, Any]] = []
        deferred: List[Dict[str, Any]] = []
        used = 0.0
        for req in candidates:
            effort = float(req["effort"])
            if req["priority"] == "M":  # always committed
                included.append(req)
                used += effort
            elif used + effort <= capacity:
                included.append(req)
                used += effort
            else:
                deferred.append(req)

        warnings: List[str] = []
        if must_effort > capacity:
            warnings.append(
                f"Must Have effort ({must_effort}) exceeds capacity ({capacity}) — "
                "timebox is over-committed; renegotiate scope or capacity."
            )

        return {
            "length_weeks": length_weeks,
            "capacity": capacity,
            "committed_effort": round(used, 2),
            "utilisation_pct": round(used / capacity * 100, 1),
            "included": included,
            "deferred": deferred,
            "warnings": warnings,
        }
