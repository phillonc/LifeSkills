"""Task factories that map DSDM products onto the agents framework.

Each factory returns a :class:`~agents_framework.core.task.Task` whose handler
reads inputs/products from the shared crew context and writes a new DSDM product
back into it.

Expected crew inputs (seed the context via ``Crew.kickoff(inputs=...)``):

* ``raw_requirements`` : list[str | dict]  — feeds the PRL
* ``costs`` / ``benefits`` : list[float]   — feed the business case
* ``timebox_capacity`` : float             — feeds the timebox plan
* ``risks`` : list[dict]                   — feed the risk log

Products written to the context:

* ``prl``          (Prioritised Requirements List)
* ``moscow``       (MoSCoW assessment + Minimum Usable Subset)
* ``business_case``
* ``timebox_plan``
* ``risk_log``
"""

from __future__ import annotations

from typing import Any, Dict

from ..core.agent import Agent
from ..core.task import Task


def build_prl_task(agent: Agent) -> Task:
    """Foundations: normalise raw requirements into a PRL."""

    def handler(agent: Agent, context: Dict[str, Any]) -> Any:
        raw = context.get("raw_requirements")
        if raw is None:
            raise KeyError("context is missing 'raw_requirements'")
        return agent.use("requirements_analysis", items=raw).unwrap()["prl"]

    return Task(
        name="Build Prioritised Requirements List",
        description="Normalise raw requirements into a clean, prioritised list.",
        agent=agent,
        handler=handler,
        produces="prl",
        expected_output="A list of {id, title, priority, effort} requirements.",
    )


def prioritise_task(agent: Agent) -> Task:
    """Foundations: assess the PRL against MoSCoW rules."""

    def handler(agent: Agent, context: Dict[str, Any]) -> Any:
        prl = context.get("prl")
        if not prl:
            raise KeyError("context is missing 'prl' (run build_prl_task first)")
        return agent.use("moscow_prioritisation", prl=prl).unwrap()

    return Task(
        name="MoSCoW prioritisation review",
        description="Extract the Minimum Usable Subset and check the 60/20/20 balance.",
        agent=agent,
        handler=handler,
        produces="moscow",
        expected_output="MUS, effort split, and balance warnings.",
    )


def business_case_task(agent: Agent) -> Task:
    """Foundations: summarise the business case."""

    def handler(agent: Agent, context: Dict[str, Any]) -> Any:
        costs = context.get("costs", [])
        benefits = context.get("benefits", [])
        return agent.use(
            "business_case",
            costs=costs,
            benefits=benefits,
            period_years=context.get("period_years", 1.0),
        ).unwrap()

    return Task(
        name="Build business case",
        description="Summarise cost vs benefit into a viability snapshot.",
        agent=agent,
        handler=handler,
        produces="business_case",
        expected_output="Net benefit, ROI, payback and a viability flag.",
    )


def plan_timebox_task(agent: Agent) -> Task:
    """Evolutionary Development: plan the first timebox from the PRL."""

    def handler(agent: Agent, context: Dict[str, Any]) -> Any:
        prl = context.get("prl")
        if not prl:
            raise KeyError("context is missing 'prl' (run build_prl_task first)")
        capacity = context.get("timebox_capacity")
        if capacity is None:
            raise KeyError("context is missing 'timebox_capacity'")
        return agent.use(
            "timebox_planner",
            prl=prl,
            capacity=capacity,
            length_weeks=context.get("timebox_length_weeks", 2),
        ).unwrap()

    return Task(
        name="Plan timebox",
        description="Fit prioritised work into a fixed-capacity timebox.",
        agent=agent,
        handler=handler,
        produces="timebox_plan",
        expected_output="Included vs deferred items and utilisation for the timebox.",
    )


def risk_assessment_task(agent: Agent) -> Task:
    """Cross-cutting: score and rank project risks."""

    def handler(agent: Agent, context: Dict[str, Any]) -> Any:
        return agent.use("risk_log", risks=context.get("risks", [])).unwrap()

    return Task(
        name="Assess risks",
        description="Score risks by exposure and surface the top risk.",
        agent=agent,
        handler=handler,
        produces="risk_log",
        expected_output="Risks ranked by exposure (probability x impact).",
    )
