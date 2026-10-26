# Life Skills delivery boundary

This repository previously contained a deterministic DSDM planning framework, not a Life Skills application. This increment adds a locally runnable responsive web app and independent acceptance tests. It does not establish completion of the entire enhanced platform strategy.

## Source requirements

The four supplied source files are preserved in `sources/`. The PRD defines the core personal development and financial learning product. The enhanced strategy adds a considerably larger platform roadmap. Source market comparisons, prices, scientific assertions and outcome forecasts have not been independently verified.

## DSDM responsibility

| Code | Owner | Responsibility | Evidence |
|---|---|---|---|
| A1 | Business Analyst | PRD decomposition and MoSCoW plan | `python -m examples.life_skills_delivery` |
| A2 | Solution Developer | App implementation | File hashes in runner output |
| A3 | Solution Tester | Independent HTTP acceptance and privacy tests | Test output in runner evidence |
| A4 | Project Manager | Bound scope and surface remaining work | This record and generated timebox plan |

The Python framework uses explicit task handlers. Developer and QA coding work was performed by separate assistant agents. The reproducible runner records implementation evidence and executes tests. It does not autonomously generate or deploy software. `agents.xml` records the roles and assignments. No MCP server or external AI provider is required by this increment.

## Requirements still requiring delivery or independent acceptance

| Code | Requirement | Release implication |
|---|---|---|
| R1 | Native iOS and Android apps, voice learning, AR practice and robust offline sync | Responsive browser UI does not satisfy native app delivery |
| R2 | AI coaching personalities, predictive interventions and cross-skill recommendation models | No AI coaching service is deployed |
| R3 | Peer marketplace, mentoring, community moderation, reviews and real-world validation | Requires its own end-to-end journeys and safeguards |
| R4 | Bank, calendar, health, employer, IoT, social OAuth and analytics integrations | External integrations must be configured and independently tested |
| R5 | Expert-reviewed multimedia, all introductory domains and accredited credentials | Educational seed content requires editorial and expert validation |
| R6 | Subscriptions, payments, corporate portals and household profiles | Commercial platform scope remains outside this increment |
| R7 | Production email delivery, HTTPS deployment, encrypted storage, monitoring, backup restoration and incident operations | Must be configured and exercised before a public launch |
| R8 | 10,000 concurrent users, horizontal scale, availability targets, WCAG conformance and penetration testing | No certification or production capacity evidence is claimed |
| R9 | JWT authentication specified by PRD | Initial implementation uses revocable server-side cookie sessions instead |

These are explicit remaining requirements, not completed features. Local acceptance results only establish the behaviors exercised by the named tests. Rendered Chromium desktop/mobile workflow evidence is now recorded in `evidence/browser-acceptance.json`. Full accessibility, other browser engines and deployment readiness still need their own evidence.

## Reproduce

From repository root:

```sh
python -m examples.life_skills_delivery
python -m pytest -q
```

The app needs Python 3.9+ and no third-party runtime packages. The existing framework regression tests need the repository's `dev` extra. Run instructions and environment settings are in `README.md` in this directory. The app creates its SQLite runtime data on first launch. Runtime databases, email tokens and sessions must never be committed.
