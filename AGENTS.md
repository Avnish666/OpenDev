# Open-Source Funding and Accountability Platform

## Mission and product boundaries

Build a transparent, AI-powered crowdfunding platform for open-source software
projects. Maintainers publish projects and raise funds. Backers contribute through
PayPal and receive maintainer-defined rewards, including subscription discounts,
beta access, early releases, and recognition.

The platform differentiates itself through financial transparency, evidence-backed
AI accountability, GitHub development progress tracking, maintainer credibility
based on previous funded projects, and backer reward fulfillment tracking.

Do not claim actual escrow or multi-merchant payout functionality. Keep every
payment operation in PayPal Sandbox. Respect the zero-budget requirement; verify
licensing and free-tier availability before introducing tools or services.

## User roles

- **Visitor:** Discover projects and inspect public data.
- **Backer:** Contribute through PayPal; receive reward entitlements; view funding
  history and project progress; inspect published receipts and expense reports;
  ask AI questions about project accountability.
- **Maintainer:** Connect and verify GitHub repositories; create campaigns; define
  budget allocations and reward tiers; add collaborators; publish expenses and
  supporting evidence; define development milestones; track and fulfill rewards.

## Architecture

Preserve the existing React frontend and FastAPI backend as a modular monolith.
Extend established configuration, database, and client integration points instead
of recreating infrastructure or splitting into new services.

- **Frontend:** React, TypeScript, and Vite. Planned financial dashboards use AG
  Studio; planned roadmaps use Bryntum Gantt Community. Neither is installed in
  this checkout. Confirm suitable zero-budget licensing before adoption.
- **Backend:** FastAPI, SQLAlchemy 2 typed mappings, Alembic, and PostgreSQL.
  Separate API routers, services, schemas, and database models as features grow.
  Keep application setup and router registration in `backend/app/main.py`; keep
  business logic in services rather than expanding the entry point.
- **External services:** GitHub OAuth and REST API; PayPal Orders v2 and Webhooks;
  APIMatic PayPal Context Plugin for API integration assistance; Render deployment;
  Neon PostgreSQL; private document storage for receipts; Postman for API testing.
  These are intended integrations, not evidence that each is implemented.
- **AI:** Multimodal receipt extraction, financial inconsistency detection, GitHub
  milestone analysis, maintainer track-record analysis, and evidence-backed
  explanations of project progress and spending. Keep financial analysis read-only.

### Existing layout and integration points

- `backend/app/main.py`: FastAPI application, configured CORS, `/api/health`, and
  `/api/db-health`; registers authentication and project routers.
- `backend/app/core/config.py`: Loads optional `backend/.env`; reads `APP_ENV`,
  `FRONTEND_URL`, required `DATABASE_URL`, and GitHub OAuth configuration
  (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_CALLBACK_URL`); normalizes
  PostgreSQL driver URLs.
- `backend/app/core/database.py`: SQLAlchemy engine, session factory, declarative
  base, and `get_db` dependency. Reuse these objects.
- `backend/app/models/user.py`: Typed `User` model with GitHub ID, username, email,
  avatar URL, and creation timestamp; exported by `app/models/__init__.py`.
- `backend/alembic.ini`, `backend/migrations/env.py`, and
  `backend/migrations/versions/89b3d67b1bc5_create_users_table.py`: Existing migration
  infrastructure and initial users-table revision. Later revisions create
  `user_sessions` and projects, members, and budgets. Preserve migration history.
- `backend/tests/test_health.py`: Two tests for API health and unknown-route 404.
- `backend/app/core/auth.py`: Cookie-session authentication dependency.
- `backend/app/routers/auth.py`: GitHub login/callback, profile, logout, and trusted
  Origin guard. Services in `backend/app/services/` handle GitHub and hashed sessions.
- `backend/app/routers/projects.py`: Authenticated project creation and public active
  project listing/detail; `schemas/project.py` validates request/response data.
- `backend/app/services/project_service.py`: Transactional draft creation, owner
  membership, and budget allocations; validates categories and funding-goal totals.
- `backend/app/services/github_repository.py`: Public repository ownership verification
  against the authenticated user's GitHub ID; organization ownership is not supported.
- `frontend/src/App.tsx`: GitHub authentication interface, replacing the old health UI.
- `frontend/src/components/auth/GithubLogin.tsx` and `context/AuthContext.tsx`: Login,
  authenticated profile, logout, and application authentication state.
- `frontend/src/api/client.ts`: Cookie-authenticated API requests using `VITE_API_URL`.
- `frontend/package.json`: `dev`, `build` (TypeScript and Vite), `lint` (Oxlint),
  and `preview` commands; use `frontend/package-lock.json` with `npm ci`.
- `.github/workflows/ci.yml`: Backend tests on Python 3.12 and frontend build on
  Node 22. Its presence does not establish successful CI runs.

## Development status: reported versus inspected

The owner reports Phase 0 complete and Phase 1 Steps 1–6 implemented manually.
The latest remote `main`, fetched and inspected on 2026-11-02, is commit
`d4c5fe6c41a55842d703fa6ccab939a68f9ac0bb` ("Phase 1 touches"). The local checkout
was fast-forwarded to that commit without changing application code. The earlier
assessment used stale commit `8d634d2` and incorrectly described Phase 1 as absent.
Always compare the local revision with the remote before making status claims.

### Phase 0

- **Present:** React/FastAPI initialization, PostgreSQL configuration, SQLAlchemy
  sessions and typed user model, Alembic setup, health endpoints, environment-variable
  loading, and GitHub Actions workflow. The previous React health dashboard has now
  been replaced with the Phase 1 authentication UI.
- **Previously validated during cloud onboarding on `8d634d2`:** Frontend build and
  lint, two backend tests, local PostgreSQL migration, health endpoint responses,
  and frontend HTML serving. These results do not validate the new Phase 1 features.
  The environment uses supplemental backend dependencies outside the repository.
- **External and unverified:** GitHub OAuth application registration, reported Render
  deployment, Neon configuration, and actual GitHub Actions run results. No Render
  deployment manifest is committed; dashboard-managed deployment remains possible.
- **Configuration gaps:** No frontend environment example is committed, although
  `VITE_API_URL` is required. `backend/requirements.txt` remains UTF-16 with scientific/
  notebook dependencies and omits FastAPI, Uvicorn, SQLAlchemy, Alembic, psycopg,
  python-dotenv, pytest, and HTTPX. Backend CI does not declare its app/test
  prerequisites. CI does not provision PostgreSQL; existing tests do not use it.
- **Secret hygiene:** `backend/.env.example` has contained a credential-looking
  database URL. Do not reproduce, use, or log credentials from that file or history.
  The owner should assess and rotate/revoke any valid exposed credential. Use safe
  placeholders in examples. `backend/.env` is ignored, but the frontend ignore file
  does not explicitly cover plain `.env`; never commit one.

### Phase 1 Steps 1–6: implementation present

| Capability | Committed evidence |
| --- | --- |
| GitHub OAuth registration | External registration remains unverified; backend configuration supports the client ID, secret, and callback URL. |
| GitHub OAuth backend authentication | `routers/auth.py`, `services/github_auth.py`, and `core/auth.py`; OAuth state checking, user creation/update, current-user endpoint, and logout. |
| Database-backed sessions | `models/session.py`, `services/session_service.py`, and migration `a16c29b1462e`; hashed session tokens and expiration. |
| React GitHub authentication interface | `components/auth/GithubLogin.tsx`, `context/AuthContext.tsx`, API client, and provider in `main.tsx`. |
| Project, collaborator, and budget models | `models/project.py`, `models/project_member.py`, `models/budget_allocation.py`, and migration `ec107b8b4763`. |
| Project creation and public repository ownership verification | `routers/projects.py`, `schemas/project.py`, `services/project_service.py`, and `services/github_repository.py`; trusted-Origin guard, ownership check, draft creation with owner membership, budget validation, and transaction handling. |

Public project listing and detail APIs are also present and restrict results to
active projects. Model-level collaborator support is present; separate collaborator
management endpoints are not implemented. Code presence does not establish that
OAuth, session flows, and project creation have passed end-to-end validation.
Only the two Phase 0 health/404 tests are committed; Phase 1 feature tests are missing.

Validation on `d4c5fe6`: both existing backend tests pass using the prepared Python
environment. Frontend `npm run build` fails with TS6192 at `src/App.tsx:2` because
`useEffect` and `useState` are imported but unused. Frontend lint exits successfully
with four warnings (unused imports and AuthContext React rules). No production migrations or
external OAuth flows were run during this verification.

### Remaining Phase 1 and immediate recommendation

Remaining work includes reward-tier models and management APIs, project discovery/
detail pages, project creation UI, draft publishing, feature tests, security review,
and deployment. Public discovery/detail backend APIs already exist; reuse them.
There is no root project README; the frontend README remains a template.

The next feature task is reward tiers and reward management APIs, extending the
existing project and authentication services without rebuilding Steps 1–6. Add
feature tests and use new Alembic revisions. The backend dependency declarations
also need a separate focused repair before clean-install CI can be trusted. This
document does not authorize a commit, push, deployment, or production migration.

### Later phases

- **Phase 2:** PayPal Sandbox checkout, capture, webhooks, and reward entitlements.
- **Phase 3:** Financial transparency, receipt uploads, AI document extraction,
  and expense validation.
- **Phase 4:** GitHub milestones, Bryntum Gantt, and maintainer credibility.
- **Phase 5:** AI accountability agents and evidence-linked explanations.
- **Phase 6:** AG Studio analytics and dashboards.
- **Phase 7:** Full integration testing, deployment, and hackathon submission.

## Engineering rules

1. Preserve existing code and architecture unless a specific change is required.
   Inspect first, preserve user changes, and do not recreate completed infrastructure.
   Work on one phase task at a time.
2. Separate API routers, services, schemas, and database models. Use SQLAlchemy 2
   typed mappings and reuse the existing base, engine, and session dependency.
3. Use Alembic for schema changes. Never modify an applied migration. Never run
   destructive database operations. Never modify real Neon production data during
   tests; use an isolated local/test database and verify the target first.
4. Never log or reveal credentials, commit `.env` files, or store GitHub/PayPal
   secrets in the frontend. Vite variables are public client configuration.
   Keep receipts in private storage and enforce access controls.
5. Protect authenticated write endpoints against CSRF. Existing CORS configuration
   is not sufficient CSRF protection. Validate authorization server-side.
6. Keep financial operations deterministic, transactional, and idempotent. Never
   trust frontend payment amounts; derive amounts from authoritative server data.
   Keep all payment operations in PayPal Sandbox.
7. Keep AI financial analysis read-only. Link accountability explanations to
   evidence, distinguish inference from verified facts, and never treat a receipt
   alone as proof that payment occurred.
8. Do not claim actual escrow or multi-merchant payout functionality. Respect the
   zero-budget requirement throughout implementation and deployment planning.
9. Add tests for every new important feature. Run relevant backend tests and
   frontend checks; report failed, skipped, and unrun checks accurately.
10. Do not deploy, commit, push, or apply production migrations without explicit
    approval. Do not infer that approval from the roadmap or setup instructions.

## Development and validation

- Use the existing checkout. Cloud tasks are isolated; do not create a Git worktree
  unless explicitly requested.
- Backend working directory: `backend/`. Use Python 3.12 and an activated environment
  with the required app/test dependencies. Set `DATABASE_URL` to an isolated local
  PostgreSQL database; set `FRONTEND_URL` to the frontend origin. Do not copy the
  committed sample database URL. Run `python -m pytest -q` and start development
  with `python -m uvicorn app.main:app --reload`.
- Against a verified local/test database only, apply new migrations with
  `alembic upgrade head`. Production migrations require explicit approval.
- Frontend working directory: `frontend/`. Run `npm ci`, set non-secret
  `VITE_API_URL` to the development API origin, then use `npm run dev`.
  Validate with `npm run build` and `npm run lint`.
- Confirm `/api/health` returns `status: ok`, `/api/db-health` returns
  `status: connected` and `result: 1`, and frontend requests reach the configured API.
  Existing health tests alone do not verify database access or browser integration.
- The prepared cloud instance additionally has `/workspace/opendev-env` and
  `/workspace/opendev-setup/` with pinned supplemental dependencies and local
  PostgreSQL startup helpers. These are environment artifacts, not committed
  project infrastructure or proof that repository-only installation works. Consult
  the saved environment startup instructions and avoid duplicate service processes.

## PayPal guidance availability (Phase 2 preparation only)

APIMatic PayPal Context Plugin 0.4.1 was installed and locally verified in this
cloud task. See `docs/paypal-context-setup.md` for official sources, exact commands,
verification, and activation limitations. Cached skills are readable under
`/home/agent/.codex/plugins/cache/context-plugins/paypal/0.4.1/skills/`; start Python
SDK work with `python/python-getting-started/SKILL.md`. Recheck availability in a
new task; automatic hot-loading and fresh-task restoration were not verified.
This setup does not install a PayPal SDK or authorize payment implementation.
