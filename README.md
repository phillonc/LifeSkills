# LifeSkills

LifeSkills Quest is a life-skills learning application. This repository contains the implemented web app, DSDM framework, tests, requirements, source documents, resource-curation proposal and UI screenshots.

## Run

Python 3.9+ with SQLite support. No third-party runtime packages are required.

```bash
cd apps/life-skills
LIFE_SKILLS_DEV=1 python server.py
```

Open http://127.0.0.1:8080. Register and open the verification link from the private local `data/outbox.jsonl` file. Development mode is loopback-only. Never commit runtime data or credentials. Production requires HTTPS, SMTP and the outstanding operational checks in the app README.

## Contents

| Path | Contents |
|---|---|
| [Application](apps/life-skills/README.md) | Accounts, learning, saved practice, goals, analytics, journal, budgets and savings |
| [Full scope](apps/life-skills/FULL_SCOPE.md) | Complete four-document target and remaining delivery gates |
| [Requirements](apps/life-skills/requirements.json) | 359 traceable requirements, nine domains, 88 topics and 440 subtopics |
| [Sources](apps/life-skills/sources/) | Four original supplied Life Skills documents |
| [Resource curation](apps/life-skills/RESOURCE_CURATION.md) | Proposed source discovery, evidence, rights review and agent responsibilities |
| [UI images](docs/ui/README.md) | 20 actual screen captures, desktop/mobile overviews and ZIP |
| [Evidence](apps/life-skills/evidence/) | Recorded HTTP and rendered-browser acceptance results |
| [DSDM framework](agents_framework/) | Deterministic agents, tools and tasks used by the delivery runner |
| [Framework documentation](docs/DSDM_AGENCY_README.md) | Original framework overview and documentation index |

## Verify

From repository root:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m examples.life_skills_delivery
```

Framework tests use pytest. Optional browser QA uses Playwright. Test-only dependencies and commands are in the [app README](apps/life-skills/README.md). GitHub Actions runs framework/API tests and rendered Chromium checks.

## Status and provenance

The implemented app is a controlled single-host Python/SQLite pilot with 75 foundation lessons across 15 topics. The full platform remains incomplete. Native clients, reviewed curriculum across all domains, AI coaching, marketplace/community, commercial integrations and production quality targets remain required work. Activity time is an estimate, reminders are in-app, and savings contributions are self-reported records.

Code and documentation were brought over from [phillonc/DSDM-Agency](https://github.com/phillonc/DSDM-Agency), including the merged Life Skills delivery and resource-curation document. The destination repository's existing licence is preserved. Original framework documentation remains under `docs/`.
