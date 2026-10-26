# LifeSkills Quest: full delivery scope

The delivery target is the complete Life Skills app described by all four supplied documents. The initial web increment is part of that target. Native apps, AI coaching, community, commercial features and integrations remain required work until accepted.

`requirements.json` is the traceable backlog. Each requirement has a stable `LS-*` ID, source file/section/line, functions, acceptance criteria, priority, delivery stage, dependencies, implementation status and evidence list. No requirement is marked complete merely because a catalog title, stub or screen exists. Acceptance evidence is mapped per record. Two narrow requirements (online lesson autosave and financial goal tracking) are accepted for the pilot. Related larger capabilities remain partly implemented until their remaining criteria pass.

## F1: Curriculum coverage

| Domain | Topics | Named subtopics |
|---|---:|---:|
| Personal Development | 9 | 45 |
| Financial Skills | 6 | 30 |
| Social and Communication Skills | 10 | 50 |
| Professional Skills | 9 | 45 |
| Health and Wellness | 7 | 35 |
| Household Management | 10 | 50 |
| Critical Thinking and Awareness | 10 | 50 |
| Safety and Security | 10 | 50 |
| Miscellaneous Skills | 17 | 85 |
| **Total** | **88** | **440** |

Curriculum IDs `LS-CUR-001` through `LS-CUR-088` preserve every named subtopic from the introduction. Each subtopic needs reviewed instruction, objectives, a practical exercise, assessment feedback and accessible media. The EI seminar adds seven records covering its agenda, scripts, role play, self-assessment, mindfulness, goal setting and review requirements. A title-only entry is discovery coverage, not delivered teaching content.

## F2: Platform coverage

| IDs | Scope |
|---|---|
| LS-PLT-001–005 | Account lifecycle, learning, progress, goals and financial tools |
| LS-PLT-006–007 | Personalization, recommendations and five AI coach roles |
| LS-PLT-008–010 | Family learning, community, mentorship, marketplace and events |
| LS-PLT-011–014 | Subscriptions, commerce, institutional portals, evidence and integrations |
| LS-PLT-015–020 | Native apps, offline/voice/AR, operations, analytics, creator studio, simulation and APIs |
| LS-PRD-* | Every functional, UX, content and integration bullet from PRD sections 4–8 |
| LS-AC-* | All 28 original Gherkin scenarios, retaining Given/When/Then details |
| LS-STR-* | All 117 strategy feature, commercial, launch and metric clauses |
| LS-DATA-* | Five explicit strategy data models with their fields |

Overlapping requirements are retained as source clauses linked to canonical platform capabilities. They must share implementation evidence where behavior is identical rather than being counted as separate delivered features. Source commercial prices and market differentiation claims remain proposals, not verified market facts.

## D1: Delivery sequence and acceptance gates

| Stage | Delivery | Completion gate |
|---|---|---|
| S1 | Core learner account, learning, goals, progress and financial workflows | Independent end-to-end account, isolation, scoring, persistence and calculator tests plus UI acceptance |
| S2 | Complete nine-domain curriculum, EI seminar, authoring/review, API and portability | All 88 topics and 440 subtopics have reviewed substantive content and mapped acceptance evidence |
| S3 | Native iOS/Android, offline/voice/AR, AI coaching, personalization and simulations | Device and sync tests, provider configuration, consent controls and evaluated coaching responses |
| S4 | Family, community, mentoring, marketplace, events and real-world evidence | Complete participant/host/moderator journeys with privacy, reporting and dispute tests |
| S5 | Subscriptions, physical commerce, institutions, external integrations and outcome analytics | Provider sandbox and reconciliation tests, entitlement/isolation tests and working partner flows |
| S6 | Production rollout and all quality targets | Accessibility audit, supported-browser/device evidence, penetration test, load test, backup restore drill and monitored deployment |

Quality work starts in S1 and continues in every stage. S6 is the final evidence gate, not permission to postpone security or accessibility. The stages do not assert dates or capacity that have not been established. The strategy's original 1–6/6–12/12–24 month milestones remain source planning assumptions.

## D2: Implementation courses of action

| Area | Current increment | Full target course of action |
|---|---|---|
| Runtime/data | Dependency-free local Python and SQLite | Preserve accepted domain behavior behind versioned APIs, add production services and managed relational persistence when needed for tested scaling targets |
| Authentication | Revocable cookie sessions | Explicitly resolve PRD JWT requirement before production acceptance, with OAuth and safe token storage for native clients |
| Content | Seed lessons and full catalog | Versioned authoring, expert review, references, accessible media, locale/jurisdiction review and publication gates |
| AI | No deployed coaching provider | Configure an authorized provider, explicit memory consent, deletion, bounded specialist behavior and evaluation evidence |
| Integrations | Local tools | Provider adapters with scoped permissions, encrypted credentials, revocation, idempotent webhooks and sandbox evidence |
| Native/offline | Responsive browser experience | Native clients with authenticated API access, tested cache invalidation, conflict handling, voice and device capability integration |

These are engineering courses of action, not claims that infrastructure or external accounts exist.

## R1: Source conflicts to resolve without dropping scope

1. **R1.1** The strategy's first-phase library says 50 skills across six domains. The introduction specifies 88 topics across nine domains. Treat 50/six as an intermediate launch slice and retain all 88/nine as the final target.
2. **R1.2** The PRD focuses on 15 topics and 75 named subtopics. It specifies 45 personal-development subtopics. This is a subset of the 440-subtopic full catalog.
3. **R1.3** The EI source first totals 240 minutes using 75 minutes of practical work. Later variants use 60 minutes and sum to 225 despite a 240-minute label. Use a reviewed 240-minute agenda and explicitly allocate every activity minute.
4. **R1.4** The PRD asks for JWT. The first web increment uses server-side sessions. Record the difference and obtain technical acceptance or deliver JWT where required.
5. **R1.5** Short EI script drafts do not provide the stated 30/60 minutes of teaching. Expand activities and facilitator instructions, then validate duration. Claims about fixed IQ or guaranteed health outcomes require editorial correction and evidence.
6. **R1.6** Currency, cultural adaptation, tax, lending, first aid, emergency and legal material need jurisdiction-specific content. US-dollar examples and UK user context do not establish a universal financial or regulatory rule.

## A1: Evidence workflow

For each `LS-*` record, the Developer maps implementation paths and commits, then QA attaches named automated or manual evidence. Change `implementation_status` only after inspecting the implementation. Change `acceptance_status` to accepted only after its criteria pass. An integration is incomplete while represented only by configuration fields or a simulated response. A curriculum item is incomplete while represented only by a title or generic template.

The final release gate is zero required backlog items without accepted evidence, with any explicit source change recorded by the Product Owner. Pending records are delivery work, not discarded scope.

## F3: Second increment evidence

The app now saves and resumes lesson reflection/quiz drafts, supports all four learning-goal templates, records bounded activity estimates, displays UTC activity/topic tables and in-app due reminders, and tracks self-reported savings targets and contributions. Existing learner and topic-goal records survive the additive schema upgrade.

Independent HTTP tests cover private ownership, replay prevention, derived goal windows, money precision, exports/deletion and migration. Rendered Chromium tests cover registration, resume/reload, rejected-save recovery, savings contributions, analytics and mobile navigation. Evidence is under `evidence/`; the optional rendered runner is `scripts/browser-acceptance.cjs`. This evidence does not certify accessibility, other browser engines, live email or production scale.

The full target remains 359 requirements. No completion percentage is inferred from the number of code files, catalog titles, tests or narrow accepted requirements.
