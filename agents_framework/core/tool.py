"""Tool abstraction.

A :class:`Tool` is a single, well-defined capability an agent can invoke. Tools
are deterministic and side-effect-light by default so the framework runs without
any external services or LLMs. Calling a tool always returns a :class:`ToolResult`
so callers never have to wrap invocations in try/except.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ToolResult:
    """The outcome of invoking a tool.

    ``ok`` is ``False`` when the tool raised; ``error`` then holds the message.
    """

    tool: str
    ok: bool
    output: Any = None
    error: Optional[str] = None

    def unwrap(self) -> Any:
        """Return the output, or raise if the tool failed."""
        if not self.ok:
            raise RuntimeError(f"tool {self.tool!r} failed: {self.error}")
        return self.output


class Tool(ABC):
    """Base class for all tools.

    Subclasses set ``name``/``description`` and implement :meth:`run`. Invoke a
    tool by *calling* it (``tool(**kwargs)``) which wraps :meth:`run` and returns
    a :class:`ToolResult`.
    """

    name: str = "tool"
    description: str = ""

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Perform the tool's work and return its raw output."""

    def __call__(self, **kwargs: Any) -> ToolResult:
        try:
            return ToolResult(self.name, True, self.run(**kwargs))
        except Exception as exc:  # noqa: BLE001 - surfaced via ToolResult.error
            return ToolResult(self.name, False, error=str(exc))

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<Tool {self.name!r}>"
