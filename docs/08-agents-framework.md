# DSDM Agents Framework

A lightweight, **dependency-free** Python framework for orchestrating *agents*
that use *tools* to complete *tasks* — with every abstraction mapped directly
onto DSDM. It runs on the standard library alone (no LLM or external service
required), which keeps it deterministic and unit-testable, while leaving room to
plug an LLM-backed handler in later.

## The mapping

| Framework concept | DSDM concept | Example |
|-------------------|--------------|---------|
| **Agent** | A DSDM **role** | Business Analyst, Project Manager |
| **Tool** | A DSDM **technique / capability** | MoSCoW, Timeboxing, Risk Log |
| **Task** | A DSDM **product** (artefact) | Prioritised Requirements List |
| **Crew** | A DSDM **project** (orchestration) | A Foundations → Timebox run |

See [03-roles.md](03-roles.md), [05-practices.md](05-practices.md), and
[06-products.md](06-products.md) for the underlying DSDM definitions.

## Layout

```
agents_framework/
  core/
    tool.py      # Tool base class + ToolResult
    agent.py     # Agent (a DSDM role + its tools)
    task.py      # Task + TaskResult
    crew.py      # Crew orchestrator + Process + CrewResult
  tools/         # DSDM technique tools
    requirements.py     # RequirementsAnalysisTool  -> PRL
    moscow.py           # MoSCoWPrioritisationTool   -> MUS + balance check
    timebox.py          # TimeboxPlannerTool         -> fit work to capacity
    business_case.py    # BusinessCaseTool           -> net / ROI / payback
    risk_log.py         # RiskLogTool                -> exposure ranking
  agents/
    dsdm_agents.py       # factories: business_analyst(), project_manager(), ...
  tasks/
    dsdm_tasks.py        # factories: build_prl_task(), plan_timebox_task(), ...
examples/
  foundations_to_timebox.py   # runnable end-to-end demo
tests/                         # pytest suite
```

## Core concepts

### Tool

A single capability. Subclass `Tool`, set `name`/`description`, implement
`run(**kwargs)`. *Calling* a tool returns a `ToolResult` (so callers never need
try/except); `.unwrap()` returns the output or raises.

```python
from agents_framework import Tool

class GreetTool(Tool):
    name = "greet"
    description = "Greet someone."
    def run(self, who):
        return f"Hello, {who}!"

GreetTool()(who="DSDM").unwrap()   # -> "Hello, DSDM!"
```

### Agent

A DSDM role with a goal and a set of permitted tools. It executes tasks and can
invoke its tools by name with `agent.use("tool_name", **kwargs)`.

### Task

A unit of work assigned to an agent. The work lives in a
`handler(agent, context) -> output`, and the task records which DSDM product it
`produces`. Keeping the handler explicit makes runs reproducible.

### Crew

The orchestrator. It runs tasks sequentially, threading a shared `context` dict
through them: each task's output is written back to the context under its
`produces` key, so later tasks consume earlier products — exactly how DSDM
products feed forward through the lifecycle.

## Quick start

```python
from agents_framework import Crew
from agents_framework.agents import business_analyst, project_manager
from agents_framework.tasks import build_prl_task, prioritise_task, plan_timebox_task

analyst = business_analyst()
manager = project_manager()

crew = Crew(
    agents=[analyst, manager],
    tasks=[
        build_prl_task(analyst),     # produces "prl"
        prioritise_task(analyst),    # produces "moscow"
        plan_timebox_task(manager),  # produces "timebox_plan"
    ],
)

result = crew.kickoff(inputs={
    "raw_requirements": [
        {"title": "login",     "priority": "M", "effort": 5},
        {"title": "dashboard", "priority": "S", "effort": 4},
        {"title": "pdf export","priority": "C", "effort": 4},
    ],
    "timebox_capacity": 10,
})

result.output("moscow")["minimum_usable_subset"]   # the Must Haves
result.output("timebox_plan")["deferred"]          # what didn't fit
```

Run the full demo:

```bash
python -m examples.foundations_to_timebox
```

## The bundled tools

| Tool | DSDM technique | Output highlights |
|------|----------------|-------------------|
| `RequirementsAnalysisTool` | Requirements / PRL | Normalised `{id, title, priority, effort}` list |
| `MoSCoWPrioritisationTool` | MoSCoW | Minimum Usable Subset, effort split, 60% balance check |
| `TimeboxPlannerTool` | Timeboxing | Included vs deferred items, utilisation, over-commit warning |
| `BusinessCaseTool` | Business Case | Net benefit, ROI %, payback, viability flag |
| `RiskLogTool` | Demonstrate control | Risks ranked by exposure (probability × impact) |

The MoSCoW and Timebox tools encode real DSDM rules: Must Haves define the
Minimum Usable Subset and are always committed; Should/Could Haves act as the
contingency buffer that protects the deadline; and the planner flags a timebox
whose Must Haves alone exceed capacity.

## Extending it

- **New capability** → subclass `Tool` and add it to an agent's `tools`.
- **New role** → add a factory in `agents/dsdm_agents.py`.
- **New product** → add a task factory in `tasks/dsdm_tasks.py` whose handler
  reads upstream products from `context` and returns the new one.
- **LLM-backed agents** → swap a task's deterministic `handler` for one that
  calls a model; the `Crew`/`Agent`/`Task` contracts are unchanged.

## Development

```bash
pip install -e ".[dev]"   # install with dev extras (pytest)
pytest -q                 # run the test suite
```

← Back to [01-overview.md](01-overview.md)
