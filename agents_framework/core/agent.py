"""Agent abstraction.

An :class:`Agent` represents a DSDM *role* (e.g. Business Analyst, Project
Manager). It owns a goal and a set of :class:`Tool` instances it is permitted to
use, and it executes :class:`~agents_framework.core.task.Task` objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, TYPE_CHECKING

from .tool import Tool, ToolResult

if TYPE_CHECKING:  # avoid import cycle at runtime
    from .task import Task, TaskResult


@dataclass
class Agent:
    """A DSDM role, equipped with tools, that performs tasks."""

    role: str
    goal: str
    backstory: str = ""
    tools: List[Tool] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._tools_by_name: Dict[str, Tool] = {t.name: t for t in self.tools}

    # -- tool access -------------------------------------------------------
    def has_tool(self, name: str) -> bool:
        return name in self._tools_by_name

    def use(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Invoke one of the agent's tools by name."""
        tool = self._tools_by_name.get(tool_name)
        if tool is None:
            return ToolResult(
                tool_name,
                False,
                error=(
                    f"{self.role!r} has no tool {tool_name!r}; "
                    f"available: {sorted(self._tools_by_name)}"
                ),
            )
        return tool(**kwargs)

    # -- task execution ----------------------------------------------------
    def execute(self, task: "Task", context: Dict[str, Any]) -> "TaskResult":
        """Run ``task`` against the shared ``context`` and return its result."""
        from .task import TaskResult  # local import avoids cycle

        try:
            output = task.handler(self, context)
            return TaskResult(task.name, self.role, True, output, produces=task.produces)
        except Exception as exc:  # noqa: BLE001 - surfaced via TaskResult.error
            return TaskResult(
                task.name, self.role, False, None, produces=task.produces, error=str(exc)
            )

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<Agent {self.role!r} tools={sorted(self._tools_by_name)}>"
