# Reproducible local synthetic demonstration

Use an isolated developer machine or this managed cloud workspace. All campaigns,
repository links, funding/refunds/webhook records, receipts and activity below are
**synthetic fixtures**, not verified provider operations. No checkout, upload,
OAuth login or live model is needed for the default public walkthrough.

## 1. Install and select the local environment

From the repository root, install the prerequisites and dependencies in the root
README. Create your own virtual environment or, in the prepared cloud workspace,
activate `/workspace/opendev-env/bin/activate`. Keep production configuration absent.
No `.env` copying or credential values are required. The Python demo wrappers disable ambient application dotenv loading; provide the explicit selectors below instead. Each terminal used for the demo
must export the same values:

```sh
export APP_ENV=testing
export OPENDEV_DEMO=synthetic-local
export CHECKOUT_ENABLED=false
export RECEIPT_PROCESSING_ENABLED=false
export LLM_ENABLED=false
export FRONTEND_URL=http://127.0.0.1:5173
export DATABASE_URL=postgresql+psycopg://opendev@127.0.0.1:55438/opendev_test_demo_local
export TEST_DATABASE_URL="$DATABASE_URL"
export VITE_API_URL=''
```

Clear any unrelated Studio evaluation/licensed flags for the default Community demo.
The backend demo guard rejects production/non-loopback targets, other DB names,
host/service overrides and enabled checkout/receipt/LLM flags **before application
configuration is imported**. Only the narrow synthetic search_path option is accepted
for isolated tests. The frontend launcher rejects Studio activation.

## 2. Start disposable PostgreSQL and migrate

Docker example: only a local, disposable synthetic database uses trust authentication.
It must never be used as a production authentication policy. The port binds loopback.
Do not start a second container if this exact fixture already exists; inspect/reuse
only your own demo container. Creation of an existing database fails without replacing it.

```sh
docker run --name opendev-demo-postgres -d --shm-size=256m \
  -e POSTGRES_USER=opendev -e POSTGRES_HOST_AUTH_METHOD=trust \
  -p 127.0.0.1:55438:5432 postgres:16
docker exec opendev-demo-postgres pg_isready -U opendev
# Repeat the readiness check until accepting connections, then create once:
docker exec opendev-demo-postgres createdb -U opendev opendev_test_demo_local
python -c "import sys; sys.path.insert(0,'backend'); from app.acceptance.demo import local_database; local_database(); print('Local demo target validated')"
(cd backend && python -m alembic upgrade head && python -m alembic check)
python scripts/demo-data.py --environment local-test > /tmp/opendev-demo-manifest.json
python scripts/demo-data.py --environment local-test > /tmp/opendev-demo-manifest-again.json
cmp /tmp/opendev-demo-manifest.json /tmp/opendev-demo-manifest-again.json
```

Stop on any error. A blocked seed exits 2 with a redacted reason; do not continue to
launch against unrelated data. Seeding uses one transaction and a DB advisory lock,
adds no schema changes, never drops/truncates or overwrites existing user data, and
returns the same manifest on repeat. A conflicting fixture marker is rejected.
Change to a new explicitly local `opendev_test_demo_*` DB rather than resetting data.
Do not run downgrade, stamp unexecuted migrations or any production migration.

This task used the existing dedicated `opendev-phase7-postgres` fixture on port 55437
and a fresh `opendev_test_demo_step6` database. The commands above use a distinct
portable name/port; the setup does not depend on a pre-existing cloud service.
The verified schema head is `b7a200000001`.

## 3. Start unchanged authorization and the Community frontend

Terminal A, root, activated Python environment and exports above:

```sh
python scripts/local-demo.py
```

Terminal B, root, same exports:

```sh
node frontend/demo.mjs
```

The API binds `127.0.0.1:8000`; Vite binds `127.0.0.1:5173` with strict port selection
and a same-origin `/api` proxy to that API. No public listener/tunnel is created.
Open `http://127.0.0.1:5173/#/explore`. Use manifest IDs; a fresh database normally
has project 1, expense 2, owner 1 and private draft 3. Do not assume those IDs if a
manifest says otherwise. `/api/health` must be ok and `/api/db-health` connected.
Check both through the Vite origin as well as the API.

## 4. Fixture facts and boundaries

Two public campaigns and one private draft; synthetic maintainer/backer identities
without email/avatar; unlimited reward tier; four contributions; one immutable refund
record and synthetic event IDs; three published expenses plus a private draft;
private original and approved-redaction **metadata only**; three main-project
milestones with deadline history and a dependency; one earlier-release milestone;
one issue, one merged PR, one sampled commit and a timestamped sync fixture.

| Main project fact | Expected result |
| --- | --- |
| Gross captured fixture amounts | 110000 cents / 1100.00 USD |
| Known cumulative refund exclusion | 5000 cents / 50.00 USD |
| Reversal exclusion | 10000 cents / 100.00 USD |
| Net recorded funding | 95000 cents / 950.00 USD |
| Published spending | 65000 cents / 650.00 USD |
| Calculated difference | 30000 cents / 300.00 USD; not cash |
| Development / Hosting / Documentation spending | 350.00 / 250.00 / 50.00 USD |
| Public unresolved findings | One Hosting category overrun, 50.00 USD |
| Public evidence metadata | One approved fixture; two expenses unsupported publicly |
| Main roadmap | One asserted delivered on time, one revised overdue commitment, one planned |
| Eligible reward fulfillment | One fulfilled of two eligible completed captures; refunded/reversed excluded |

The known refund does not make total historical refund coverage complete: the reversal
fixture has an unknown cumulative refund total, so exact aggregate refunds stay NULL.
GitHub fixture observations are dated 2026-10-01 and correctly become stale. Day-overdue
counts depend on current UTC date. The planned feedback deadline is 2027-12-01;
if replaying after that date it too is overdue. No clock is changed to hide this.
Current-owner history includes both active projects; it is not a separate previous-project cohort.

No receipt bytes exist in Supabase. Show public metadata; **do not click signed download**
as evidence of live storage. Do not click GitHub fixture URLs as if they are real repos.
No browser checkout or upload is attempted. Optional offline native extraction can
be demonstrated by the existing synthetic Docker OCR smoke in the testing guide.

## 5. Acceptance and real screenshots

In a separate test process (not a running API), set TEST_DATABASE_URL to the same
local test target and run:

```sh
(cd backend && python -m pytest -q tests/test_demo_acceptance.py)
node frontend/tests/browser-demo.mjs /tmp/opendev-demo-manifest.json
```

These demo-specific tests create/drop only fresh test schemas, not demo records. The **complete legacy suite needs a different fresh, migrated and never-seeded test database**: some existing fixtures use rollback transactions over its public schema and assume no baseline rows. Do not run that suite against the seeded demo DB; see the testing guide. The browser checks
public routes, actual chart/Gantt rendering, CSV, cited deterministic chat, signed-out
management denial and private-project 404. It records unaltered PNGs and a hash manifest
under `docs/submission/screenshots`. Review captures for privacy before sharing.
Existing screenshot files are refreshed only by this explicit command.

## 6. Login, creation, receipts and optional technology fallbacks

Public discovery/inspection is the default. Do not click login and claim it succeeded.
The existing local test `tests/test_release_journey.py::test_full_cookie_authenticated_release_journey`
exercises actual OAuth state validation, normal callback/session hashing, repository-backed
project/reward creation, mocked Sandbox flows and synthetic private storage with local
native extraction. Only external GitHub/PayPal/storage responses are mocked. Run it in
a separate test process with testing-only CHECKOUT_ENABLED/RECEIPT_PROCESSING_ENABLED/LLM_ENABLED
set true; this does not change the running demo's flags. Show its terminal result as
**HTTP test evidence, not a recorded browser OAuth login or live provider success**.
There are no auth dependency overrides in the running demo and no shortcut cookie.

AG Studio is optional. If installed and permitted for local evaluation, use the existing
isolated Studio browser journey in the testing guide. It runs only on loopback, keeps
trial notices visible and does not enable Studio in the default demo or image. Do not
publish evaluation assets/captures until the actual terms permit that intended use.
The default recording can use the source/configuration evidence matrix and Community
fallback without claiming a Studio demonstration occurred in that recording.

For real local Ollama, use [Step 5 acceptance commands](phase7-ai-capacity-verification.md#13-exact-future-local-commands)
with an explicitly approved **already-installed** local tool-capable model and synthetic
DB. The guarded default demo intentionally rejects LLM_ENABLED=true; use a separate
normal local test server for that acceptance. No model is installed/downloaded here.
Real inference remains **NOT RUN**; never relabel deterministic chat as generated inference.

## 7. Clean shutdown

Press Ctrl+C in both server terminals; Uvicorn drains with a five-second graceful
shutdown limit and Vite closes its own server. Then stop only the database fixture
you started: `docker stop opendev-demo-postgres`. Retain the container/data for review;
no cleanup command deletes records or volumes. In the cloud verification the dedicated
`opendev-phase7-postgres` was stopped; the original environment database was preserved.
Never publish a loopback demo through a tunnel to satisfy a submission URL field.
