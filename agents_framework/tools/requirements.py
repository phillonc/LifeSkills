"""Requirements analysis tool.

Normalises a raw list of requirements into a clean **Prioritised Requirements
List (PRL)** — the DSDM Foundations product. Accepts plain strings or dicts and
canonicalises the MoSCoW priority and effort estimate of each item.
"""

from __future__ import annotations

from typing import Any, Dict, List, Union

from ..core.tool import Tool

_PRIORITY_ALIASES = {
    "M": "M", "MUST": "M",
    "S": "S", "SHOULD": "S",
    "C": "C", "COULD": "C",
    "W": "W", "WONT": "W", "WON'T": "W", "WILLNOT": "W",
}

RawRequirement = Union[str, Dict[str, Any]]


def _canonical_priority(value: Any) -> str:
    key = str(value).strip().upper().replace(" ", "")
    if key in _PRIORITY_ALIASES:
        return _PRIORITY_ALIASES[key]
    # Fall back to first letter (handles "Must have", "Could-have", etc.)
    first = key[:1]
    if first in {"M", "S", "C", "W"}:
        return first
    raise ValueError(f"unrecognised MoSCoW priority: {value!r}")


class RequirementsAnalysisTool(Tool):
    name = "requirements_analysis"
    description = "Normalise raw requirements into a Prioritised Requirements List (PRL)."

    def run(self, items: List[RawRequirement], default_priority: str = "S") -> Dict[str, Any]:
        if not isinstance(items, list):
            raise TypeError("items must be a list of strings or dicts")

        prl: List[Dict[str, Any]] = []
        for index, raw in enumerate(items, start=1):
            item: Dict[str, Any] = {"title": raw} if isinstance(raw, str) else dict(raw)

            title = str(item.get("title", "")).strip()
            if not title:
                raise ValueError(f"requirement #{index} has no title")

            priority = _canonical_priority(item.get("priority", default_priority))
            try:
                effort = float(item.get("effort", 1))
            except (TypeError, ValueError):
                raise ValueError(f"requirement {title!r} has a non-numeric effort")
            if effort < 0:
                raise ValueError(f"requirement {title!r} has negative effort")

            prl.append(
                {
                    "id": item.get("id", f"R{index:03d}"),
                    "title": title,
                    "priority": priority,
                    "effort": effort,
                }
            )

        return {"prl": prl, "count": len(prl)}
