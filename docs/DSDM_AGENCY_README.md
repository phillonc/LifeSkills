# DSDM-Agency

Documentation **and a working agents framework** for the **DSDM (Dynamic
Systems Development Method)** — the agile project delivery framework used as the
operating model for the DSDM-Agency.

DSDM fixes **time, cost, and quality** and flexes **features**, using
prioritisation and fixed timeboxes to deliver the most valuable work first, on
time and on budget, without compromising quality.

## Life Skills application

The first runnable LifeSkills Quest web increment lives in [`apps/life-skills/`](../apps/life-skills/README.md). The full four-document product scope is tracked in [`FULL_SCOPE.md`](../apps/life-skills/FULL_SCOPE.md) and [`requirements.json`](../apps/life-skills/requirements.json). This increment does not complete the full platform. Reproduce DSDM planning and app acceptance evidence with `python -m examples.life_skills_delivery`.

## Agents framework

A lightweight, dependency-free Python framework (`agents_framework/`) that maps
DSDM directly onto agents, tools, and tasks:

| Framework concept | DSDM concept |
|-------------------|--------------|
| **Agent** | A DSDM role (Business Analyst, Project Manager, …) |
| **Tool** | A DSDM technique (MoSCoW, Timeboxing, Risk Log, …) |
| **Task** | A DSDM product (Prioritised Requirements List, …) |
| **Crew** | A DSDM project (orchestrates agents + tasks) |

```bash
pip install -e ".[dev]"              # install (pulls in pytest)
pytest -q                            # run the test suite
python -m examples.foundations_to_timebox   # run the end-to-end demo
```

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

Full guide: [docs/08-agents-framework.md](08-agents-framework.md).
Operating overview (best suited for / not for, agents, worked scenarios):
[docs/09-framework-overview.md](09-framework-overview.md).

## Documentation

The full framework documentation lives in [`docs/`]():

| # | Document | Covers |
|---|----------|--------|
| 1 | [Overview](01-overview.md) | What DSDM is, the core "fix time/cost, flex features" idea, and the four pillars |
| 2 | [Philosophy & Principles](02-principles.md) | The philosophy and the eight non-negotiable principles |
| 3 | [Roles](03-roles.md) | Project, solution-team, and supporting roles |
| 4 | [Lifecycle](04-lifecycle.md) | The six phases from Pre-Project to Post-Project |
| 5 | [Practices](05-practices.md) | MoSCoW, Timeboxing, Iterative Development, Facilitated Workshops, Modelling |
| 6 | [Products](06-products.md) | The artefacts DSDM produces, by phase |
| 7 | [Glossary](07-glossary.md) | Quick reference for DSDM terminology |
| 8 | [Agents Framework](08-agents-framework.md) | The `agents_framework/` package: agents, tools, tasks, crews |
| 9 | [Framework Overview](09-framework-overview.md) | What the framework is for, what it is *not*, its agents, and worked basic → complex scenarios |

## Quick reference

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

---

DSDM is stewarded by the [Agile Business Consortium](https://www.agilebusiness.org/).
This repository is an independent documentation/reference resource.

