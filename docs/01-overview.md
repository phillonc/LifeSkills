# DSDM — Overview

**DSDM (Dynamic Systems Development Method)** is an agile project delivery
framework. Originally created in 1994 as a vendor-independent, non-proprietary
approach to Rapid Application Development (RAD), it has evolved into a general
framework for delivering projects of any kind — not just software. It is now
stewarded by the **Agile Business Consortium** and is often referred to as the
**DSDM Agile Project Framework (AgilePF)**.

## What problem does DSDM solve?

Many agile methods (e.g. Scrum, XP) focus primarily on *building the product* —
the team-level delivery loop. DSDM complements this by wrapping delivery in the
**project and governance context** an organisation needs: a clear lifecycle,
defined roles spanning business and technical stakeholders, and explicit
controls. In short:

> DSDM answers *"how do we run an agile **project** end-to-end, with the
> business fully engaged and on time and on budget?"* rather than only
> *"how does the team build the next increment?"*

This makes DSDM a natural fit for the **DSDM-Agency**: a delivery model where
the business need drives the work, time and cost are fixed, and *scope* flexes
to fit.

## The core idea: fix time & cost, flex features

Traditional ("waterfall") projects fix the **features** and let **time** and
**cost** vary — which is why they slip and overrun. DSDM inverts this. It fixes
**time, cost, and quality** up front and varies the **features** delivered,
using prioritisation (MoSCoW) to guarantee that the most valuable, essential
features are always delivered first.

```
        Traditional                         DSDM / Agile
   ┌──────────────────┐               ┌──────────────────┐
   │     FEATURES     │  ← fixed      │  TIME COST QUALITY│  ← fixed
   ├──────────────────┤               ├──────────────────┤
   │  TIME  │  COST   │  ← vary       │     FEATURES      │  ← vary
   └──────────────────┘               └──────────────────┘
```

Because the **Must Have** features are guaranteed and lower-priority items
(Should/Could Have) act as a *contingency buffer*, DSDM can deliver on time and
on budget without compromising quality.

## The four pillars of DSDM

DSDM is built on four interlocking sets of ideas. Each has its own document in
this folder:

| Pillar | What it is | Document |
|--------|------------|----------|
| **Philosophy & Principles** | The eight principles that underpin every decision | [02-principles.md](02-principles.md) |
| **People (Roles)** | Defined business + technical + management roles | [03-roles.md](03-roles.md) |
| **Process (Lifecycle)** | Six phases from Pre-Project to Post-Project | [04-lifecycle.md](04-lifecycle.md) |
| **Practices** | MoSCoW, Timeboxing, Iterative Development, Facilitated Workshops, Modelling | [05-practices.md](05-practices.md) |

Supporting material:

- [06-products.md](06-products.md) — the artefacts ("products") DSDM produces.
- [07-glossary.md](07-glossary.md) — quick reference for DSDM terminology.
- [08-agents-framework.md](08-agents-framework.md) — the `agents_framework/`
  package that maps DSDM roles/techniques/products onto agents, tools, and tasks.

## When to use DSDM

DSDM works well when:

- The **business need is clear** but the detailed solution is not.
- **Time-to-market** matters and a fixed deadline exists.
- Business users **can and will** be actively involved throughout.
- An **incremental delivery** of value is acceptable (and desirable).

It is less suited to environments where the full scope is genuinely fixed and
non-negotiable, or where business stakeholders cannot commit time to the project.

## How this maps to the DSDM-Agency

The DSDM-Agency uses this framework as its operating model:

1. Every engagement starts from a **business need**, not a feature list.
2. Engagements are run in **fixed timeboxes** with flexible scope.
3. Work is prioritised with **MoSCoW** so essential value lands first.
4. Both **business and delivery roles** are staffed from day one.
5. Delivery is **iterative and incremental**, with continuous collaboration.

Read on in [02-principles.md](02-principles.md) for the foundations.
