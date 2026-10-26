# DSDM — Core Practices

DSDM relies on five mutually reinforcing practices. Together they make
"fix time & cost, flex features" actually work in day-to-day delivery.

1. [MoSCoW Prioritisation](#1-moscow-prioritisation)
2. [Timeboxing](#2-timeboxing)
3. [Iterative Development](#3-iterative-development)
4. [Facilitated Workshops](#4-facilitated-workshops)
5. [Modelling & Prototyping](#5-modelling--prototyping)

---

## 1. MoSCoW Prioritisation

MoSCoW gives every requirement an unambiguous priority so the team always knows
what *must* be delivered versus what is negotiable. The letters stand for:

| Code | Priority | Meaning |
|------|----------|---------|
| **M** | **Must Have** | Without it, the delivery is *unusable* / has no value. Non-negotiable for this delivery. Defines the **Minimum Usable Subset (MUS)**. |
| **S** | **Should Have** | Important and painful to leave out, but the solution is still viable without it (perhaps with a workaround). |
| **C** | **Could Have** | Wanted/desirable, but less impactful if left out. The first things dropped under pressure. |
| **W** | **Won't Have this time** | Agreed to be *out of scope* for this delivery (but recorded, possibly for a future one). |

*(The lowercase "o"s simply make the acronym pronounceable.)*

### The golden ratio: ~60 / 20 / 20

To protect "deliver on time," DSDM recommends balancing effort across a timebox
so that **Must Haves are no more than ~60% of the effort**, with roughly **20%
Should Have** and **20% Could Have**:

```
 Effort in a Timebox
 ┌──────────────────────────────┬──────────┬──────────┐
 │  MUST HAVE  (≈60%)            │ SHOULD   │ COULD    │
 │                              │ (≈20%)   │ (≈20%)   │
 └──────────────────────────────┴──────────┴──────────┘
                                  └── contingency buffer ──┘
```

The **Should** and **Could** Haves form a built-in **contingency**. If things go
wrong, Could Haves (then Should Haves) are sacrificed first — the deadline and
the Must Haves are protected. This is *why* DSDM can promise on-time delivery
without compromising quality.

### MoSCoW rules of thumb
- "Must" = *Minimum Usable SubseT* — not "I'd really like this."
- Priorities can be re-evaluated each timebox.
- If Must Haves exceed ~60%, the timebox is over-committed and high-risk.

---

## 2. Timeboxing

A **Timebox** is a fixed period of time (typically **2–4 weeks**) with a fixed
end date, within which the team delivers an agreed, prioritised set of work.
**The deadline never moves — the scope flexes** (via MoSCoW) to fit.

### Structured Timebox

DSDM describes a structured timebox with three steps:

```
 ┌────────────┐   ┌──────────────────────────────┐   ┌──────────────┐
 │ KICK-OFF   │ → │  INVESTIGATE → REFINE →       │ → │ CLOSE-OUT    │
 │ (agree     │   │  CONSOLIDATE (the build loop) │   │ (review &    │
 │  objectives│   │                              │   │  accept)     │
 └────────────┘   └──────────────────────────────┘   └──────────────┘
```

- **Kick-Off** — confirm the timebox objectives and acceptance criteria.
- **Investigate** — agree in detail what will be delivered and how.
- **Refine** — do the bulk of the development and testing iteratively.
- **Consolidate** — tie up loose ends and ensure everything meets quality.
- **Close-Out** — review against objectives; the business formally accepts.

Daily **stand-ups** keep the timebox on track day-to-day.

---

## 3. Iterative Development

Rather than building each element once and hoping it's right, DSDM **iterates**:
build → demonstrate/test → get feedback → refine. Each pass converges the
solution closer to genuine business need.

Benefits:
- Errors and misunderstandings surface **early and cheaply**.
- The business sees tangible progress frequently and can steer.
- Change is embraced as part of *converging on the right answer*, not as
  failure.

Iterative development operates *inside* timeboxes and across the Evolutionary
Development phase.

---

## 4. Facilitated Workshops

A **Facilitated Workshop** is a structured, time-bound meeting led by a
**neutral Workshop Facilitator**, designed to achieve a specific objective
(e.g. agreeing scope, prioritising requirements, resolving a design question)
with the right stakeholders in the room.

Key ingredients:
- A **neutral facilitator** who owns the *process*, not the content.
- The **right participants** with authority to decide.
- A **clear objective** and agreed outputs.
- Outputs **owned and actioned** by participants, not the facilitator.

Workshops accelerate decision-making and shared understanding — directly
supporting *"collaborate"* and *"communicate continuously and clearly."*

---

## 5. Modelling & Prototyping

DSDM uses **models** (diagrams, sketches) and **prototypes** to communicate
ideas quickly and unambiguously — a picture or a working prototype removes far
more uncertainty than pages of prose.

- **Models** improve shared understanding and explore options cheaply.
- **Prototypes** make the abstract tangible, surface real feedback, and
  validate that the team is building the right thing.
- Both keep documentation **lean** — model *enough* to communicate, no more.

---

## How the practices reinforce each other

| Want to… | …rely on |
|----------|----------|
| Deliver on time | Timeboxing + MoSCoW (contingency buffer) |
| Build the right thing | Iterative Development + Modelling/Prototyping |
| Decide fast, together | Facilitated Workshops |
| Protect quality | Iterative testing within timeboxes |
| Stay in control | Timebox reviews + visible MoSCoW priorities |

Next: [06-products.md](06-products.md) — the artefacts DSDM produces.
