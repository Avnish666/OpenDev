# Phase 1 Step 7

## Development setup

Use Python 3.12, PostgreSQL, and Node 22.12+ (or Node 24). Keep the existing checkout
and GitHub authentication configuration. No new frontend dependencies are required.

1. Activate the backend Python environment. The prepared cloud environment uses
   `/workspace/opendev-env/bin/activate`. The checked-in `backend/requirements.txt`
   still lacks web application dependencies; in a fresh virtual environment install
   `fastapi uvicorn sqlalchemy alembic "psycopg[binary]" python-dotenv pytest httpx`.
   Dependency manifest repair is a separate existing issue.
2. Configure `DATABASE_URL` to a verified isolated local PostgreSQL database,
   `APP_ENV=development`, and `FRONTEND_URL=http://localhost:5173`. Configure the
   existing GitHub OAuth client ID, backend-only secret, and callback URL through
   secure environment settings. Never use credentials from the sample file/history.
3. From `backend/`, review the new revision and run `alembic upgrade head` **only
   against the verified local development database**. Production application requires
   separate explicit approval. Run `python -m uvicorn app.main:app --reload`.
4. From `frontend/`, run `npm ci`. Set `VITE_API_URL=http://localhost:8000`, then
   `npm run dev`. Use the same hostname consistently for frontend and API cookies.
5. Sign in through the existing GitHub flow. Create a draft with a public repository
   personally owned by that GitHub account. Enter integer USD cents and budget
   allocations totaling the goal. My Projects links to private draft details,
   editing, reward creation/editing, and publication. Explore shows active projects.

## Endpoints

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/api/projects/{id}/rewards` | Owner/maintainer creates a reward tier. |
| GET | `/api/projects/{id}/rewards` | Public sees active tiers of active projects; managers also see inactive tiers and drafts. |
| PATCH | `/api/projects/{id}/rewards/{tier_id}` | Owner/maintainer edits tier; `quantity_limit: null` removes its limit. |
| GET | `/api/me/projects` | Authenticated owner's/maintainer's projects, paginated with `limit` and `offset`. |
| PATCH | `/api/projects/{id}` | Owner/maintainer edits draft title, description, goal and/or budget. |
| POST | `/api/projects/{id}/publish` | Owner/maintainer publishes a draft after budget and live GitHub ownership/repository-ID verification. |
| GET | `/api/projects` | Existing public discovery endpoint, active projects only. |
| GET | `/api/projects/{id}` | Extended details: budget, public maintainer profiles, and caller's management permission. Drafts return 404 to non-managers. |

Existing creation/authentication endpoints remain in use. Every write uses the
existing exact trusted-Origin check plus session authentication and authorization.
Project identity, owner, currency, repository, and status cannot be set via PATCH.
Rewards support USD to match project creation. Benefits are structured objects:
`[{"title":"Beta access","description":"Preview releases"}]`.

## Migration

`f7a100000007_add_reward_tiers.py` follows `ec107b8b4763`, adds only `reward_tiers`,
its project foreign key/index, positive price/quantity and USD checks, and a unique
project/name expression index using trimmed, case-insensitive names. Benefits use
JSON. Timestamps are server-created; SQLAlchemy updates `updated_at` on changes.
No existing migration is modified. Destructive downgrade is intentionally blocked;
use reviewed forward migrations. Applied only to newly created local test databases.

## Tests

Create a **new local test database** whose name starts with `opendev_test_`, migrate
it with Alembic, and set both `DATABASE_URL` and `TEST_DATABASE_URL` to its URL
(`postgresql+psycopg://...`). From `backend/` run `python -m pytest -q`.
Tests refuse non-local/non-test-named targets and roll back fixtures rather than
truncating or deleting real data. GitHub verification is mocked in integration
tests; tests do not call GitHub or require real OAuth secrets. Without
`TEST_DATABASE_URL`, integration tests explicitly skip; health tests alone are
not complete validation.

Frontend checks, from `frontend/`: `npx tsc -b`, `npm run build`, `npm run lint`.

## Security and limitations

- Publication rechecks GitHub ownership against the original owner, not the acting
  maintainer. Ownership transfers or private repositories prevent publication.
  Repository association is immutable here; transfers require future workflow work.
- Draft details/budgets/rewards require owner or maintainer permissions. Ordinary
  collaborators cannot manage them. Inactive rewards are hidden publicly.
- Project row locks serialize edits/publication/reward writes; uniqueness is also
  enforced by PostgreSQL. Financial values are integer cents. There are no payment,
  contribution, entitlement, stock-decrement, or escrow operations in this step.
- Only drafts can be edited; active project financial terms cannot be changed here.
  Rewards can be deactivated. Their quantity is a planned cap, not remaining stock.
- OAuth registration and browser login require configured external credentials.
  No automated browser end-to-end run or live GitHub verification was performed.
- Existing backend dependency declaration/CI gaps and the previously identified
  credential-looking sample remain separate issues. Assess exposed credentials.
- Existing AuthContext lint warnings and TestClient deprecation warnings remain.
  No production migration, commit, push, deployment, or paid dependency is included.

## Verification results

- Backend: 20 passed, zero failed/skipped, on a freshly migrated isolated local
  PostgreSQL database (18 Step 7 cases plus two existing health cases).
- Alembic upgrade: passed; `alembic check`: no new upgrade operations detected.
- TypeScript check and Vite production build: passed.
- Oxlint: completed with two pre-existing warnings in `AuthContext.tsx`; no new
  page-code warnings. Backend TestClient reports its existing HTTPX deprecation.

## File inventory

Created:

- `backend/app/models/reward_tier.py`
- `backend/app/schemas/reward.py`
- `backend/app/services/project_management.py`
- `backend/app/routers/me.py`
- `backend/migrations/versions/f7a100000007_add_reward_tiers.py`
- `backend/tests/test_projects.py`
- `frontend/src/pages/Projects.tsx`
- `docs/phase1-step7.md`

Modified:

- `backend/app/core/auth.py` (optional session authentication)
- `backend/app/main.py` (register My Projects router)
- `backend/app/models/__init__.py` (register reward metadata)
- `backend/app/routers/projects.py` (management/reward endpoints and private details)
- `backend/app/schemas/project.py` (draft edits, detail output, budget validation)
- `frontend/src/api/client.ts` (typed project/reward API access)
- `frontend/src/App.tsx` (page navigation using dependency-free hash routes)
- `frontend/src/App.css` (responsive forms, cards, and navigation)

The root `AGENTS.md` was already an untracked file from the preceding task and was
preserved. Existing authentication flows and project creation services were reused.
