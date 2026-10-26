# Framework Overview — the DSDM-Agency Agents Framework

- **Repository:** `DSDM-Agency`
- **Package:** `agents_framework/`
- **Language:** Python, **dependency-free** (pytest only, for the test suite)
- **Install:** `pip install -e ".[dev]"`
- **Demo:** `python -m examples.foundations_to_timebox`

The companion document [`08-agents-framework.md`](08-agents-framework.md) is the
API guide. This page is the operating overview: what the framework is for, what
it deliberately does not do, the agents inside it, and worked scenarios from the
simplest run to a full engagement.

---

## What it does

The agents framework maps **DSDM onto four primitives**, one-to-one:

| Framework concept | DSDM concept |
|---|---|
| **Agent** | A DSDM role (Business Analyst, Project Manager, …) |
| **Tool** | A DSDM technique (MoSCoW, Timeboxing, Risk Log, …) |
| **Task** | A DSDM product (Prioritised Requirements List, Business Case, …) |
| **Crew** | A DSDM project (orchestrates agents + tasks) |

A `Crew.kickoff(inputs=…)` seeds a shared context, runs its tasks in order, and
each task writes its **product** back into that context under a named key. The
next task reads it. `CrewResult.output("moscow")` fetches a product by name;
`CrewResult.ok` and `.errors` tell you whether the engagement held together.

Every technique is a real, deterministic calculation — the MoSCoW tool extracts
the Minimum Usable Subset and checks the 60/20/20 effort balance; the timebox
planner fits prioritised work into a fixed capacity and reports what was
deferred; the business case computes net benefit, ROI, payback and a viability
flag; the risk log ranks by exposure (probability × impact).

## Best suited for

- **Modelling a DSDM engagement in code** — the Foundations products and a first
  Evolutionary Development timebox, computed rather than asserted.
- **Teaching and reference.** The four primitives map so directly onto DSDM that
  the code reads as the method.
- **Embedding DSDM techniques elsewhere.** The tools are usable standalone:
  `MoSCoWPrioritisationTool()(prl=…)` needs no crew, no agent and no network.
- **Environments with no dependency budget.** It imports nothing outside the
  standard library.
- **Deterministic, testable planning.** No LLM call, no clock, no network — the
  same inputs give the same products every time.

## What it is not

- **Not an LLM agent framework.** An `Agent` here is a DSDM *role* holding
  tools, not a language model. `Agent.execute` runs a task handler; it does not
  prompt anything.
- **Not a runtime for delivery.** It plans, prioritises and computes. Running an
  actual delivery with phase agents is the `dsdm-agents` repository.
- **Not parallel.** `Process.SEQUENTIAL` is the only process; anything else
  raises `NotImplementedError`. Tasks share one context, in order, by design.
- **Not a full DSDM lifecycle.** Five task factories cover the Foundations
  products and the first timebox. Deployment and Post-Project are documented in
  `docs/` but not implemented as tasks.
- **Not tolerant of a missing input.** A task whose context key is absent raises
  `KeyError` naming the key and, where it applies, the task you should have run
  first. That is the intended behaviour — a silently empty product is worse.

---

## Agents in this framework

Five DSDM roles, from [`agents_framework/agents/dsdm_agents.py`](../agents_framework/agents/dsdm_agents.py).

| Agent | Goal | Tools |
|---|---|---|
| **Business Analyst** — `business_analyst()` | Turn business needs into a clear, MoSCoW-prioritised requirements list | `requirements_analysis`, `moscow_prioritisation` |
| **Business Visionary** — `business_visionary()` | Keep the solution aligned to business value and justify it commercially | `business_case` |
| **Project Manager** — `project_manager()` | Deliver on time by planning timeboxes and managing risk | `timebox_planner`, `risk_log` |
| **Technical Coordinator** — `technical_coordinator()` | Ensure the solution is technically coherent and meets agreed standards | *(none yet)* |
| **Team Leader** — `team_leader()` | Facilitate day-to-day progress and remove blockers | *(none yet)* |

Technical Coordinator and Team Leader are defined with no tools: they exist as
roles for a crew's shape and for future techniques, and calling `.use()` on them
will not find a tool. See [`docs/03-roles.md`](03-roles.md) for the full role
definitions.

### Tools (DSDM techniques)

| Tool name | Class | Computes |
|---|---|---|
| `requirements_analysis` | `RequirementsAnalysisTool` | Normalises raw requirements into a PRL of `{id, title, priority, effort}` |
| `moscow_prioritisation` | `MoSCoWPrioritisationTool` | Minimum Usable Subset, effort split, 60/20/20 balance warnings |
| `business_case` | `BusinessCaseTool` | Net benefit, ROI, payback, viability flag |
| `timebox_planner` | `TimeboxPlannerTool` | Included vs deferred items, utilisation |
| `risk_log` | `RiskLogTool` | Risks ranked by exposure (probability × impact) |

### Tasks (DSDM products)

| Task factory | Produces (context key) | Requires in context |
|---|---|---|
| `build_prl_task(agent)` | `prl` | `raw_requirements` |
| `prioritise_task(agent)` | `moscow` | `prl` |
| `business_case_task(agent)` | `business_case` | `costs`, `benefits`, optional `period_years` |
| `plan_timebox_task(agent)` | `timebox_plan` | `prl`, `timebox_capacity`, optional `timebox_length_weeks` |
| `risk_assessment_task(agent)` | `risk_log` | `risks` |

---

## Basic scenarios

### 1. Install and verify

```bash
pip install -e ".[dev]"
pytest -q
```

### 2. Run the end-to-end demo

```bash
python -m examples.foundations_to_timebox
```

It assembles a three-agent crew, seeds a sample engagement, and prints the
MoSCoW assessment, business case, timebox plan and risk log.

### 3. The smallest useful crew

```python
from agents_framework import Crew
from agents_framework.agents import business_analyst, project_manager
from agents_framework.tasks import build_prl_task, prioritise_task, plan_timebox_task

analyst, manager = business_analyst(), project_manager()

crew = Crew(
    agents=[analyst, manager],
    tasks=[build_prl_task(analyst), prioritise_task(analyst), plan_timebox_task(manager)],
)

result = crew.kickoff(inputs={
    "raw_requirements": [{"title": "login", "priority": "M", "effort": 5}],
    "timebox_capacity": 10,
})

result.output("moscow")["minimum_usable_subset"]
```

### 4. Use one technique on its own

No crew, no agent:

```python
from agents_framework.tools import MoSCoWPrioritisationTool, TimeboxPlannerTool

prl = [{"id": "R1", "title": "login", "priority": "Must", "effort": 5}]

moscow = MoSCoWPrioritisationTool()(prl=prl).unwrap()
plan   = TimeboxPlannerTool()(prl=prl, capacity=13, length_weeks=2).unwrap()
```

`Tool.__call__` returns a `ToolResult`; `.unwrap()` gives you the value or
raises.

---

## Complex scenarios

### A full Foundations pass, then the first timebox

This is the shape of a real engagement — five products, three roles, one
context.

```python
from agents_framework import Crew
from agents_framework.agents import business_analyst, business_visionary, project_manager
from agents_framework.tasks import (
    build_prl_task, prioritise_task, business_case_task,
    risk_assessment_task, plan_timebox_task,
)

analyst, visionary, manager = business_analyst(), business_visionary(), project_manager()

crew = Crew(
    agents=[analyst, visionary, manager],
    tasks=[
        build_prl_task(analyst),        # → prl
        prioritise_task(analyst),       # → moscow      (needs prl)
        business_case_task(visionary),  # → business_case
        risk_assessment_task(manager),  # → risk_log
        plan_timebox_task(manager),     # → timebox_plan (needs prl)
    ],
    verbose=True,
)

result = crew.kickoff({
    "raw_requirements": [
        {"title": "User can log in",           "priority": "Must",  "effort": 5},
        {"title": "User can reset password",   "priority": "Must",  "effort": 3},
        {"title": "Dashboard with key metrics","priority": "Should","effort": 8},
        {"title": "Export report to PDF",      "priority": "Could", "effort": 5},
        {"title": "Dark mode theme",           "priority": "Could", "effort": 2},
        {"title": "Native mobile app",         "priority": "Won't", "effort": 20},
    ],
    "costs":    [40_000, 15_000],     # build + run
    "benefits": [80_000, 30_000],     # year-1 + ongoing
    "period_years": 1.0,
    "timebox_capacity": 13,           # effort points the team can deliver
    "timebox_length_weeks": 2,
    "risks": [
        {"description": "Key business user unavailable", "probability": 0.4, "impact": 8},
        {"description": "Third-party API unstable",      "probability": 0.6, "impact": 5},
        {"description": "Scope creep on dashboard",      "probability": 0.5, "impact": 3},
    ],
})
```

### Read the products, and handle a failed engagement

```python
if not result.ok:
    for err in result.errors:
        print(f"{err.task}: {err.error}")

mus        = result.output("moscow")["minimum_usable_subset"]
viability  = result.output("business_case")
plan       = result.output("timebox_plan")
top_risk   = result.output("risk_log")[0]
```

A crew does not stop at the first failure — every `TaskResult` is collected, so
`result.errors` shows you all of them at once.

### Ordering is a contract, not a preference

`prioritise_task` and `plan_timebox_task` both read `prl`. Put either before
`build_prl_task` and you get:

```
KeyError: context is missing 'prl' (run build_prl_task first)
```

The dependency graph is expressed by ordering plus these explicit checks. There
is no scheduler that will reorder them for you.

### Re-plan a timebox without recomputing Foundations

Because products live in the context, you can seed a second crew with the first
crew's output:

```python
second = Crew(agents=[manager], tasks=[plan_timebox_task(manager)])
replan  = second.kickoff({
    **result.context,          # carries prl, moscow, business_case, risk_log
    "timebox_capacity": 8,     # a smaller team this sprint
    "timebox_length_weeks": 1,
})
replan.output("timebox_plan")
```

This is the framework's answer to "what if we had less capacity?" — re-run one
task against the same Foundations.

### Add a technique of your own

A tool is a class with a `name` and a `run`:

```python
from agents_framework.core.tool import Tool

class FacilitatedWorkshopTool(Tool):
    name = "facilitated_workshop"
    def run(self, *, attendees, agenda):
        return {"attendees": attendees, "decisions": [], "agenda": agenda}
```

Attach it to a role, wrap it in a task factory that declares `produces=…`, and
it composes with everything above.

---

## The DSDM reference this framework encodes

**The eight principles**

1. Focus on the business need
2. Deliver on time
3. Collaborate
4. Never compromise quality
5. Build incrementally from firm foundations
6. Develop iteratively
7. Communicate continuously and clearly
8. Demonstrate control

**MoSCoW** — Must Have · Should Have · Could Have · Won't Have this time

**The six phases** — Pre-Project → Feasibility → Foundations →
Evolutionary Development → Deployment → Post-Project

The task factories currently cover Foundations and the first Evolutionary
Development timebox.

---

## Relationship to the other DSDM frameworks

| Repository | Framework | Shape |
|---|---|---|
| **`DSDM-Agency`** (this one) | `agents_framework/` | Dependency-free crew library — DSDM roles, techniques and products as code |
| **`dsdm-agents`** | Python phase agents + delivery rooms | A full lifecycle runtime with persistent multi-agent state |
| **`lhs-agents`** | `agents/dsdm-dev/` | Requirements decomposition and TDD-first planning inside the LocalHighStreet platform |

All three are specified to ship the same **Requirement → PRD → TRD → TASKS**
pipeline (`WF-PRTT-001`) against one byte-identical spec —
`lhs-agents/docs/WORKFLOW-PRD-TRD-TASKS.md`. Run the same requirement through
each and the three `TASKS.md` files should differ only in the agent names: same
task IDs, same traceability, same ordering. A change to the stages, gates, ID
schemes or document headings is a change to that spec, applied to all three
repositories together.

> **Current state:** this repository does not yet contain
> `agents_framework/workflow/`. The shared pipeline is specified for it but not
> present here; the crew library above is what this package provides today.

---

## Cautions

- **`Process.SEQUENTIAL` is the only supported process.** Setting anything else
  raises `NotImplementedError` rather than silently degrading.
- **Task order is the dependency graph.** Nothing reorders for you.
- **Technical Coordinator and Team Leader carry no tools yet.** `agent.use(...)`
  on them will not resolve.
- **`ToolResult.unwrap()` raises on failure.** Check the result rather than
  unwrapping blind inside a handler you want to keep running.

## See also

- [`08-agents-framework.md`](08-agents-framework.md) — the API guide
- [`01-overview.md`](01-overview.md) · [`02-principles.md`](02-principles.md) · [`03-roles.md`](03-roles.md) · [`04-lifecycle.md`](04-lifecycle.md) · [`05-practices.md`](05-practices.md) · [`06-products.md`](06-products.md) · [`07-glossary.md`](07-glossary.md)
- [`examples/foundations_to_timebox.py`](../examples/foundations_to_timebox.py)
- DSDM is stewarded by the [Agile Business Consortium](https://www.agilebusiness.org/); this repository is an independent reference resource.
