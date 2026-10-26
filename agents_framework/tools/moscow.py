"""MoSCoW prioritisation tool.

Analyses a Prioritised Requirements List and reports:

* the **Minimum Usable Subset (MUS)** — the Must Have items;
* effort split across Must / Should / Could / Won't;
* whether the timebox respects the DSDM guideline that **Must Haves should be
  no more than ~60%** of delivered effort (leaving Should/Could as contingency).
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..core.tool import Tool

_LABELS = {"M": "Must Have", "S": "Should Have", "C": "Could Have", "W": "Won't Have"}
_MUST_HAVE_CEILING_PCT = 60.0


class MoSCoWPrioritisationTool(Tool):
    name = "moscow_prioritisation"
    description = "Assess a PRL against MoSCoW rules and extract the Minimum Usable Subset."

    def run(self, prl: List[Dict[str, Any]], must_have_ceiling_pct: float = _MUST_HAVE_CEILING_PCT) -> Dict[str, Any]:
        if not prl:
            raise ValueError("prl is empty — nothing to prioritise")

        effort: Dict[str, float] = {k: 0.0 for k in _LABELS}
        for req in prl:
            effort[req["priority"]] += float(req["effort"])

        delivered = effort["M"] + effort["S"] + effort["C"]  # Won't is out of scope
        must_pct = round(effort["M"] / delivered * 100, 1) if delivered else 0.0

        warnings: List[str] = []
        balanced = must_pct <= must_have_ceiling_pct
        if not balanced:
            warnings.append(
                f"Must Have effort is {must_pct}% of delivered effort "
                f"(> {must_have_ceiling_pct}% guideline) — timebox is high risk; "
                "consider re-prioritising or splitting the work."
            )
        if effort["S"] == 0 and effort["C"] == 0:
            warnings.append(
                "No Should/Could Have items — there is no contingency buffer to protect the deadline."
            )

        mus = [r for r in prl if r["priority"] == "M"]
        return {
            "minimum_usable_subset": mus,
            "effort_by_priority": {_LABELS[k]: round(v, 2) for k, v in effort.items()},
            "delivered_effort": round(delivered, 2),
            "must_have_pct": must_pct,
            "balanced": balanced,
            "warnings": warnings,
        }
