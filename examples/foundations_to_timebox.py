"""End-to-end example: from Foundations to a planned first timebox.

Run with:

    python -m examples.foundations_to_timebox

It assembles a crew of DSDM-role agents, seeds a sample engagement, and runs the
Foundations products (PRL, MoSCoW, business case, risk log) followed by planning
the first Evolutionary Development timebox.
"""

from __future__ import annotations

import json

from agents_framework import Crew
from agents_framework.agents import (
    business_analyst,
    business_visionary,
    project_manager,
)
from agents_framework.tasks import (
    build_prl_task,
    business_case_task,
    plan_timebox_task,
    prioritise_task,
    risk_assessment_task,
)


def main() -> None:
    analyst = business_analyst()
    visionary = business_visionary()
    manager = project_manager()

    crew = Crew(
        agents=[analyst, visionary, manager],
        tasks=[
            build_prl_task(analyst),
            prioritise_task(analyst),
            business_case_task(visionary),
            risk_assessment_task(manager),
            plan_timebox_task(manager),
        ],
        verbose=True,
    )

    inputs = {
        "raw_requirements": [
            {"title": "User can log in", "priority": "Must", "effort": 5},
            {"title": "User can reset password", "priority": "Must", "effort": 3},
            {"title": "Dashboard with key metrics", "priority": "Should", "effort": 8},
            {"title": "Export report to PDF", "priority": "Could", "effort": 5},
            {"title": "Dark mode theme", "priority": "Could", "effort": 2},
            {"title": "Native mobile app", "priority": "Won't", "effort": 20},
        ],
        "costs": [40_000, 15_000],          # build + run
        "benefits": [80_000, 30_000],       # year-1 + ongoing
        "period_years": 1.0,
        "timebox_capacity": 13,             # effort points the team can deliver
        "timebox_length_weeks": 2,
        "risks": [
            {"description": "Key business user unavailable", "probability": 0.4, "impact": 8},
            {"description": "Third-party API unstable", "probability": 0.6, "impact": 5},
            {"description": "Scope creep on dashboard", "probability": 0.5, "impact": 3},
        ],
    }

    result = crew.kickoff(inputs)

    print("\n=== Crew result ({}) ===".format("OK" if result.ok else "ERRORS"))
    for key in ("moscow", "business_case", "timebox_plan", "risk_log"):
        print(f"\n--- {key} ---")
        print(json.dumps(result.output(key), indent=2, default=str))

    if not result.ok:
        print("\nErrors:")
        for err in result.errors:
            print(f"  - {err.task}: {err.error}")


if __name__ == "__main__":
    main()
