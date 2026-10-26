# LifeSkills Quest pilot

Runnable responsive web application delivered as the first increment of the four supplied Life Skills documents. This is a single-host pilot, not the entire ecosystem strategy or a production release.

## Run

Python 3.9+ with SQLite support. No third-party packages or API keys required.

```bash
cd apps/life-skills
LIFE_SKILLS_DEV=1 python server.py
```

Open http://127.0.0.1:8080. Register an account with a name, email, password, confirmation, and consent. In explicit development mode, email links are written to `data/outbox.jsonl`. Open the verification link before signing in. Development mode must bind to loopback and does not expose an outbox HTTP route. Do not use real personal information in development.

For a different port, set both URL and argument:

```bash
LIFE_SKILLS_DEV=1 LIFE_SKILLS_BASE_URL=http://127.0.0.1:8090 python server.py --port 8090
```

Data defaults to `data/life-skills.sqlite3`. Override with `LIFE_SKILLS_DB=/absolute/path/database.sqlite3`. Keep data outside source control and configure appropriate backup retention.

## Implemented

- Registration, one-use expiring verification, resend, sign-in, optional 30-day session, sign-out, and password reset. Passwords use salted PBKDF2-SHA256 with 310,000 iterations. Session and email tokens are stored as hashes. Cookies are HttpOnly and SameSite Strict, with Secure on HTTPS URLs. Password reset invalidates existing sessions.
- Editable profile and interests, interest-based next course, topic search and filtering, 9 personal development topics and 6 financial topics with 5 foundation lessons each.
- Five distinct Emotional Intelligence lessons adapted from the supplied outline. Exercise reflection plus server-graded quizzes are required to complete lessons. Remaining topics contain brief topic-level foundations with different subtopic practice focuses, not a full expert-reviewed curriculum. Completion records persist per user.
- Dashboard, topic and overall progress, recent activity, practice-day streak, first/10/25-lesson and goal-achievement badges. Four goal templates cover complete-topic, consecutive daily practice, distinct lesson skill building and weekly time targets, with server-derived progress and in-app reminders for deadlines within three days or overdue. Reminders are displayed when the app is opened, with no background/email notification delivery.
- Lesson reflection and quiz draft autosave, dashboard resume and reload recovery. Failed saves keep the lesson visible during navigation. No personal drafts are stored in localStorage. Recorded active time is a browser activity estimate, bounded by server elapsed time and a 120-second cap per save. Reporting uses UTC days and Monday-based weeks, with 14-day completion/time tables and per-topic duration.
- Private reflection journal with mood labels, creation and deletion.
- Savings targets with self-reported contributions, derived balance/status, contribution removal and goal deletion. This records planning data and performs no bank transfer.
- Monthly budget with adjustable suggested allocations, expense entry/deletion, over-plan indicators, simple/compound interest, fixed-rate loan calculator, investment growth projection, and year-by-year balances.
- Profile JSON export and password-confirmed account deletion cascading to personal application records. Development delivery messages for that email are removed on deletion.
- Responsive navigation, associated form labels, keyboard focus, skip link, status messages, password manager autocomplete, light/dark themes, escaped user content, no third-party browser scripts, and reduced-motion CSS. No WCAG conformance claim without an independent audit.

## Runtime files and packages

| Path | Purpose |
|---|---|
| `server.py` | HTTP API, auth, SQLite schema, mail, financial calculations |
| `learning.py` | Additive schema upgrades, drafts, activity, goal progress and savings summaries |
| `scripts/start.py` | Create runtime data directory and start server |
| `scripts/browser-acceptance.cjs` | Optional Playwright browser acceptance, isolated temporary server/data |
| `tests/test_learning.py` | Goal, draft, savings, activity and legacy-schema tests |
| `content.json` | Seeded foundation curriculum and server-only answer keys |
| `static/index.html` | App document |
| `static/app.js` | Auth, dashboard, library, lessons, journal, goals, tools, settings |
| `static/styles.css` | Responsive light/dark styling |
| `data/life-skills.sqlite3` | Runtime personal data, never commit |
| `data/outbox.jsonl` | Local development email delivery, never commit |

Packages: Python standard library only. `content.json` must remain server-side. The public catalog strips quiz answer indexes and explanations. Static serving is an explicit asset allowlist.

## Deployment configuration

Outside development, require `LIFE_SKILLS_BASE_URL=https://your-host` and SMTP configuration:

- `LIFE_SKILLS_SMTP_HOST`, `LIFE_SKILLS_SMTP_PORT` (587 by default)
- `LIFE_SKILLS_SMTP_USER`, `LIFE_SKILLS_SMTP_PASSWORD` if authentication is required
- `LIFE_SKILLS_MAIL_FROM` as an approved sender

Mail uses STARTTLS with certificate verification through the Python default TLS context. Register/reset operations return service errors when mail delivery fails. No mail provider is simulated in production mode. Run behind a trusted HTTPS reverse proxy. Bind to a private interface and protect the database directory. Database file permissions are restricted to the process owner. TLS, disk encryption, secure backups, external monitoring, mail delivery policy, restore drills, abuse controls, and deployment hardening need operational verification before release.

The stdlib threaded HTTP server and SQLite database are intentionally limited to a local or controlled single-host pilot. Socket timeout is 15 seconds, request JSON maximum is 64 KiB, authentication endpoints are rate limited per observed client IP. Reverse proxy identity is not inferred from untrusted forwarding headers. This does not prove 10,000-user scale, 99.9% uptime, OWASP compliance, or encryption at rest. There is no HTTP/worker concurrency cap, distributed rate limiting, background job queue, schema migration framework, or native mobile build.

## Remaining full-document scope

The intro contains seven further domains beyond Personal Development and Financial Skills. The full strategy also requires AI coaching, 50-skill minimum across six domains, native iOS/Android, offline sync, advanced personalisation and simulations, community/mentor marketplace, expert verification, family and enterprise portals, subscription payments, external bank/health/calendar/IoT integrations, advanced analytics, and international expansion. These features are not implemented by this increment. AI is not represented by scripted responses, and no live bank, health, emergency, insurance, or credential integration is claimed.

PRD items still requiring delivery include social OAuth, rich multimedia, full authored subtopic curriculum, background/email reminders, estimated goal completion dates, dashboard customisation, advanced predictive analytics, administration/content authoring, security/performance audits, and cross-browser/accessibility verification. The supplied EI material contains unsupported or oversimplified scientific claims. This pilot uses practical learning exercises rather than republishing those claims or presenting an EI self-report as a diagnostic score.

## Verification

From repository root:

```bash
python -m examples.life_skills_delivery
python -m pytest -q
```

The app runtime still uses only the Python standard library. Optional browser QA requires Node.js and Playwright 1.62.1, installed outside the app runtime:

```bash
npm install --prefix /tmp/life-skills-browser playwright@1.62.1 --no-audit --no-fund
node /tmp/life-skills-browser/node_modules/playwright/cli.js install chromium
NODE_PATH=/tmp/life-skills-browser/node_modules node apps/life-skills/scripts/browser-acceptance.cjs
```

Use `LIFE_SKILLS_BROWSER_PATH` to select an existing Chromium executable. Linux CI uses the pinned `@sparticuz/chromium@153.0.0` binary package as an alternative to the Playwright browser CDN. Both Node packages are test dependencies only. The script creates its own temporary development database and account, exercises rendered desktop/mobile journeys and deletes test data on exit. Browser evidence covers Chromium, not Safari/Firefox/Edge or a full accessibility audit.

Schema upgrades are additive and run at startup. Existing topic-goal and learner records are preserved. Daily goals count consecutive UTC days with a completed practice or at least 60 seconds of recorded activity after goal creation. Skill goals count distinct completed lessons after creation. Time goals use recorded minutes since creation within the current UTC Monday-based week, so their progress resets in a new week. Topic goals include existing completed lessons.
