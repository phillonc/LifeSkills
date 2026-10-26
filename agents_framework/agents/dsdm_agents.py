"""Factory functions for DSDM-role agents.

Each factory returns an :class:`~agents_framework.core.agent.Agent` pre-loaded
with the tools that role typically wields. See ``docs/03-roles.md`` for the role
definitions.
"""

from __future__ import annotations

from ..core.agent import Agent
from ..tools import (
    BusinessCaseTool,
    MoSCoWPrioritisationTool,
    RequirementsAnalysisTool,
    RiskLogTool,
    TimeboxPlannerTool,
)


def business_analyst() -> Agent:
    """Analyses and prioritises requirements (owns the PRL and MoSCoW)."""
    return Agent(
        role="Business Analyst",
        goal="Turn business needs into a clear, MoSCoW-prioritised requirements list.",
        backstory="Bridges business and technical members; clarifies and models requirements.",
        tools=[RequirementsAnalysisTool(), MoSCoWPrioritisationTool()],
    )


def business_visionary() -> Agent:
    """Holds the vision and owns the business case."""
    return Agent(
        role="Business Visionary",
        goal="Keep the solution aligned to business value and justify it commercially.",
        backstory="Communicates the vision and makes higher-level prioritisation calls.",
        tools=[BusinessCaseTool()],
    )


def project_manager() -> Agent:
    """Plans timeboxes and keeps the project visibly in control."""
    return Agent(
        role="Project Manager",
        goal="Deliver on time by planning timeboxes and managing risk.",
        backstory="Provides high-level agile leadership and empowers the delivery team.",
        tools=[TimeboxPlannerTool(), RiskLogTool()],
    )


def technical_coordinator() -> Agent:
    """The technical authority ensuring solution coherence."""
    return Agent(
        role="Technical Coordinator",
        goal="Ensure the solution is technically coherent and meets agreed standards.",
        backstory="Owns the architecture and advises on technical governance.",
        tools=[],
    )


def team_leader() -> Agent:
    """Servant-leader coordinating the Solution Development Team."""
    return Agent(
        role="Team Leader",
        goal="Facilitate day-to-day progress and remove blockers for the team.",
        backstory="Peer leader, ideally elected by the Solution Development Team.",
        tools=[],
    )



def solution_developer() -> Agent:
    """Owns implementation and reproducible delivery evidence."""
    return Agent(role="Solution Developer", goal="Build working increments against acceptance criteria.")


def solution_tester() -> Agent:
    """Independently verifies acceptance criteria and reports defects."""
    return Agent(role="Solution Tester", goal="Verify behavior, isolation and regression evidence.")
