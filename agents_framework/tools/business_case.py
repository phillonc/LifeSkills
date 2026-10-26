"""Business case tool.

Computes a simple cost/benefit summary for the DSDM **Business Case** product:
total cost, total benefit, net benefit, ROI and a (linear) payback estimate.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..core.tool import Tool


class BusinessCaseTool(Tool):
    name = "business_case"
    description = "Summarise costs and benefits into a viability snapshot (net, ROI, payback)."

    def run(
        self,
        costs: List[float],
        benefits: List[float],
        period_years: float = 1.0,
    ) -> Dict[str, Any]:
        if period_years <= 0:
            raise ValueError("period_years must be positive")

        total_cost = float(sum(costs))
        total_benefit = float(sum(benefits))
        net = total_benefit - total_cost
        roi_pct = round(net / total_cost * 100, 1) if total_cost else 0.0

        annual_benefit = total_benefit / period_years
        payback_years = round(total_cost / annual_benefit, 2) if annual_benefit > 0 else None

        return {
            "total_cost": round(total_cost, 2),
            "total_benefit": round(total_benefit, 2),
            "net_benefit": round(net, 2),
            "roi_pct": roi_pct,
            "payback_years": payback_years,
            "viable": net > 0,
        }
