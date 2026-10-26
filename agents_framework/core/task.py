"""Task abstraction.

A :class:`Task` is a unit of work assigned to an agent. Each task typically
produces a DSDM *product* (recorded in ``produces``), which the
:class:`~agents_framework.core.crew.Crew` writes back into the shared context so
later tasks can build on it.

The work itself lives in ``handler(agent, context) -> output``. Keeping the
handler explicit (rather than free-text instructions for an LLM) makes the
framework deterministic and unit-testable, while leaving room to plug an
LLM-backed handler in later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from .agent import Agent

# A handler receives the executing agent and the shared crew context.
TaskHandler = Callable[[Agent, Dict[str, Any]], Any]


@dataclass
class Task:
    """A unit of work, assigned to an agent, that produces a DSDM product."""

    name: str
    description: str
    agent: Agent
    handler: TaskHandler
    produces: str = ""           # DSDM product / context key this task outputs
    expected_output: str = ""    # human-readable description of the output

    def run(self, context: Dict[str, Any]) -> "TaskResult":
        """Execute this task via its assigned agent."""
        return self.agent.execute(self, context)


@dataclass
class TaskResult:
    """The outcome of running a task."""

    task: str
    agent: str
    ok: bool
    output: Any
    produces: str = ""
    error: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        status = "ok" if self.ok else f"error: {self.error}"
        return f"<TaskResult {self.task!r} by {self.agent!r} [{status}]>"
