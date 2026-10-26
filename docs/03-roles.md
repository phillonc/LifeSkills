# DSDM — Roles & Responsibilities

DSDM defines a clear set of roles so that the **right people** with the **right
responsibilities** are engaged throughout. Roles are grouped by colour-coded
"interest" in the official framework:

- 🟧 **Orange — Project-level roles** (direction & governance)
- 🟦 **Blue — Solution Development Team roles** (build the solution)
- 🟩 **Green — Supporting/other roles** (assist as needed)

> A *role* is not the same as a *person*. One person may hold several roles, and
> a single role may be shared — but every responsibility must be owned.

## Project-level roles (direction & governance) 🟧

### Business Sponsor
The most senior project-level role. Owns the **business case** and the budget.
The ultimate decision-maker for the project, responsible for keeping it
financially and commercially viable, and for resolving escalated issues
quickly. *Accountable for the project's success.*

### Business Visionary
Holds the **vision** for the solution and how it delivers business value.
More involved than the Sponsor day-to-day; ensures the solution stays aligned
to the business objectives, communicates the vision to the team, and makes
higher-level requirement and prioritisation decisions.

### Project Manager
Provides high-level **agile project leadership** — planning at a high level,
managing the working environment, monitoring progress against the agile plan,
and handling risk and configuration at the project level. Empowers the
Solution Development Team rather than micro-managing it.

### Technical Coordinator
The project's **technical authority**. Ensures the solution is technically
coherent, meets the agreed technical standards, and that the technical aspects
of the project hang together. Owns the system architecture and advises on
technical governance.

## Solution Development Team roles 🟦

These roles form the empowered, self-organising team that produces the solution
within each timebox.

### Team Leader
Leads the Solution Development Team as a **servant-leader / peer**. Focuses on
day-to-day team coordination, facilitating progress, removing blockers, and
ensuring the team works collaboratively. Ideally elected by the team.

### Business Ambassador
The **voice of the business** inside the team. A day-to-day representative of
the user community who provides business input, makes detailed requirement and
acceptance decisions, and ensures what is built genuinely meets user needs.
*Critical role* — the project depends on real, available business involvement.

### Business Analyst
Supports communication between business and technical members. Facilitates and
clarifies **requirements**, ensures the business needs are properly analysed
and modelled, and that the right things are built for the right reasons.

### Solution Developer
**Builds** the solution. Interprets business requirements and turns them into a
deployable increment that meets the agreed quality standard, collaborating
closely with the Business Ambassador.

### Solution Tester
**Tests** the solution continuously and collaboratively (not just at the end),
working with the team to define and execute tests against agreed acceptance
criteria. Testing is integrated throughout, supporting *"never compromise
quality."*

## Supporting / other roles 🟩

These contribute as required rather than full-time.

### Business Advisor
A subject-matter expert called in to give specialist business input (e.g. a
specific regulatory, legal, or operational viewpoint). Often a peer of the
Business Ambassador for a specific area.

### Workshop Facilitator
A **neutral** person who plans, manages, and facilitates the **Facilitated
Workshops**, ensuring they meet their objectives. Has no stake in the outcome —
their job is the process, not the content.

### DSDM Coach
Helps a team that is **new to DSDM** (or needs to improve) apply the framework
effectively, providing guidance, mentoring, and tailoring advice.

## Role map (at a glance)

```
 PROJECT LEVEL (Direction & Governance) 🟧
 ┌───────────────────┐   ┌────────────────────┐
 │ Business Sponsor   │   │ Technical          │
 │ Business Visionary │   │ Coordinator        │
 │ Project Manager    │   │                    │
 └─────────┬──────────┘   └─────────┬──────────┘
           │                        │
 SOLUTION DEVELOPMENT TEAM 🟦       │
 ┌─────────────────────────────────┴───────────┐
 │ Team Leader                                  │
 │ Business Ambassador     Solution Developer   │
 │ Business Analyst        Solution Tester      │
 └──────────────────────────────────────────────┘

 SUPPORTING ROLES 🟩
 Business Advisor · Workshop Facilitator · DSDM Coach
```

## Responsibility split: business vs. technical

A defining strength of DSDM is **mandatory business representation** in the
delivery team. Compare:

| Concern | Business side | Technical side |
|---------|---------------|----------------|
| Direction | Business Sponsor, Business Visionary | Technical Coordinator |
| Day-to-day decisions | Business Ambassador, Business Analyst | Solution Developer, Team Leader |
| Quality / acceptance | Business Ambassador, Business Advisor | Solution Tester |

Next: [04-lifecycle.md](04-lifecycle.md) — how the work flows through phases.
