"""Risk log tool.

Maintains a simple risk register supporting the DSDM principle *demonstrate
control*. Each risk gets an exposure score (probability x impact); risks are
returned sorted from highest exposure to lowest.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..core.tool import Tool


class RiskLogTool(Tool):
    name = "risk_log"
    description = "Score and rank project risks by exposure (probability x impact)."

    def run(self, risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        scored: List[Dict[str, Any]] = []
        for index, risk in enumerate(risks, start=1):
            probability = float(risk.get("probability", 0))
            impact = float(risk.get("impact", 0))
            if not 0 <= probability <= 1:
                raise ValueError(
                    f"risk #{index} probability must be between 0 and 1, got {probability}"
                )
            scored.append(
                {
                    "id": risk.get("id", f"RK{index:03d}"),
                    "description": risk.get("description", ""),
                    "probability": probability,
                    "impact": impact,
                    "exposure": round(probability * impact, 2),
                }
            )

        scored.sort(key=lambda r: r["exposure"], reverse=True)
        return {
            "risks": scored,
            "count": len(scored),
            "top_risk": scored[0] if scored else None,
        }
