"""Crew orchestration.

A :class:`Crew` is the project-level orchestrator: it runs a list of tasks with
a chosen :class:`Process` and threads a shared ``context`` dict through them.
Each task's output is stored back into the context under its ``produces`` key
(falling back to the task name), so downstream tasks can consume upstream
products — mirroring how DSDM products feed forward through the lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from .agent import Agent
from .task import Task, TaskResult


class Process(str, Enum):
    """How a crew runs its tasks."""

    SEQUENTIAL = "sequential"  # one after another, sharing context


@dataclass
class CrewResult:
    """Aggregate outcome of a crew run."""

    results: List[TaskResult]
    context: Dict[str, Any]

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results)

    @property
    def errors(self) -> List[TaskResult]:
        return [r for r in self.results if not r.ok]

    def output(self, key: str, default: Any = None) -> Any:
        """Fetch a produced product from the final context."""
        return self.context.get(key, default)


@dataclass
class Crew:
    """Orchestrates agents and tasks for a DSDM engagement."""

    agents: List[Agent]
    tasks: List[Task]
    process: Process = Process.SEQUENTIAL
    verbose: bool = False

    def kickoff(self, inputs: Dict[str, Any] | None = None) -> CrewResult:
        """Run the crew, seeding the context with ``inputs``."""
        if self.process is not Process.SEQUENTIAL:
            raise NotImplementedError(f"unsupported process: {self.process}")

        context: Dict[str, Any] = dict(inputs or {})
        results: List[TaskResult] = []

        for task in self.tasks:
            if self.verbose:
                print(f"-> {task.agent.role}: {task.name}")
            result = task.run(context)
            results.append(result)

            if result.ok:
                key = result.produces or task.name
                context[key] = result.output
            elif self.verbose:
                print(f"   ! {result.error}")

        return CrewResult(results, context)
