# DSDM — The Process / Lifecycle

The DSDM lifecycle describes how a project flows from initial idea to delivered,
embedded solution. It has **six phases**. The two outer phases (Pre-Project and
Post-Project) sit outside the project proper; the four inner phases are where
the project lives. Crucially, **Evolutionary Development is iterative** — the
team loops within it, and may also loop back to Foundations as understanding
grows.

```
        ┌───────────────┐
        │  PRE-PROJECT   │   "Should we do this at all?"
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │  FEASIBILITY   │   "Is it technically & financially viable?"
        └───────┬───────┘
                │
        ┌───────▼───────┐
        │  FOUNDATIONS   │   "Enough scope, design & plan to start (EDUF)"
        └───────┬───────┘
                │
        ┌───────▼────────────────────┐
        │   EVOLUTIONARY DEVELOPMENT  │ ◄─┐  iterate in timeboxes
        │   (iterate in timeboxes)    │ ──┘
        └───────┬─────────────────────┘
                │
        ┌───────▼───────┐
        │  DEPLOYMENT    │   "Release the increment into use"
        └───────┬───────┘   (may loop back to Evolutionary Development
                │            for the next increment)
        ┌───────▼───────┐
        │  POST-PROJECT  │   "Did we realise the expected benefits?"
        └───────────────┘
```

## 1. Pre-Project

**Purpose:** Make sure only the *right* projects are started and that they are
set up correctly.

- Identify a candidate project and capture the initial business problem/idea.
- Confirm it aligns to business priorities.
- Secure initial commitment and funding to investigate further.

**Key product:** *Terms of Reference* (a high-level statement of the overall
objective and justification for the project).

## 2. Feasibility

**Purpose:** Establish whether the project is **technically feasible** and
**financially justifiable** — at a high level, with low effort.

- A first-cut assessment of the technical solution options.
- A first-cut cost/benefit and risk view.
- Just enough analysis to decide whether to proceed — *no detailed design*.

**Key products:** *Feasibility Assessment*, *Outline Plan*.

## 3. Foundations

**Purpose:** Establish a firm but minimal baseline — the **EDUF (Enough Design
Up Front)** that lets development start with confidence, while keeping detail
deliberately light so the solution can still evolve.

Establishes understanding across three dimensions:

| Dimension | Question answered | Product |
|-----------|-------------------|---------|
| **Business** | Why, what value, what scope? | Business Case, Prioritised Requirements List (PRL) |
| **Solution** | What will it look like, technically & functionally? | Solution Architecture Definition (SAD) |
| **Management** | How will it be delivered & controlled? | Delivery Plan, Management Approach Definition |

**Key products:** *Business Case*, *Prioritised Requirements List (PRL)*,
*Solution Architecture Definition (SAD)*, *Development Approach Definition
(DAD)*, *Delivery Plan*, *Management Approach Definition (MAD)*.

## 4. Evolutionary Development

**Purpose:** Iteratively and incrementally **build the solution** on top of the
foundations, converging on something fit for business purpose.

- Work is organised into **Timeboxes** (typically 2–4 weeks — see
  [05-practices.md](05-practices.md)).
- The team applies **iterative development**, **modelling**, and **continuous
  testing**.
- Requirements are continuously elaborated and re-prioritised with **MoSCoW**.
- Produces *Evolving Solution* increments and supporting *Timebox Reviews*.

This phase **loops**: each timebox refines and extends the solution, with
frequent demonstrations and feedback. The team may revisit Foundations if scope
understanding changes materially.

**Key products:** *Evolving Solution* (the developing product itself),
*Timebox Plan*, *Timebox Review Record*.

## 5. Deployment

**Purpose:** Get an increment of the solution **into operational use** and
realise its value. Deployment may happen multiple times (one per increment).

Sub-activities:
- **Assemble** — bring together everything needed to release.
- **Review** — confirm the increment is fit to deploy.
- **Deploy** — release into the live business environment.

**Key products:** *Deployed Solution*, *Project Review Report* (captures lessons
and confirms what was delivered vs. expected).

After deployment, the project may **loop back** to Evolutionary Development for
the next increment, or proceed to close.

## 6. Post-Project

**Purpose:** After the solution has been in use for a while, check whether the
**expected business benefits** were actually realised.

- Conducted *after* the project has formally closed.
- Compares actual benefits against the Business Case.
- Feeds organisational learning.

**Key product:** *Benefits Assessment*.

## Iteration & flow summary

- **Pre-Project / Feasibility / Foundations** are largely sequential and
  *light-touch* — establish just enough to start safely.
- **Evolutionary Development** is the heartbeat: short, fixed timeboxes that
  iterate.
- **Deployment** can repeat per increment; the loop back to Evolutionary
  Development is what makes delivery *incremental*.
- **Post-Project** closes the loop on *value*, not just delivery.

Next: [05-practices.md](05-practices.md) — the techniques that power the
lifecycle.
