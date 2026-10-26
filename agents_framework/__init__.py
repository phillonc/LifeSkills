"""DSDM Agents Framework.

A lightweight, dependency-free framework for orchestrating *agents* that use
*tools* to complete *tasks* — modelled directly on the DSDM Agile Project
Framework.

Mapping:
    DSDM role        -> Agent
    DSDM technique   -> Tool   (MoSCoW, timeboxing, ...)
    DSDM product     -> Task   (the artefact a task produces)
    DSDM project     -> Crew   (orchestrates agents + tasks)

See ``docs/08-agents-framework.md`` for the full guide.
"""

from .core.tool import Tool, ToolResult
from .core.agent import Agent
from .core.task import Task, TaskResult
from .core.crew import Crew, CrewResult, Process

__all__ = [
    "Tool",
    "ToolResult",
    "Agent",
    "Task",
    "TaskResult",
    "Crew",
    "CrewResult",
    "Process",
]

__version__ = "0.1.0"
