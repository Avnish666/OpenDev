# Phase 3 Step 6: release readiness

Assessment date: 2026-11-02. **NO-GO for public deployment today.** Local integration
and container checks pass, but licensing, live browser/provider checks, and
free-tier operational limits require closure. No deployment, production access,
production migration, commit or push was performed.

## Architecture and end-to-end evidence

React → FastAPI routers → service layer → typed SQLAlchemy/PostgreSQL. GitHub OAuth
creates a random, hashed, expiring database session. Backend-only HTTPX exchanges
Sandbox PayPal OAuth credentials, creates database-priced orders and captures them;
verified webhooks reconcile contributions and exactly-one reward entitlement.
Reported expenses remain separate from capture records. Private Supabase objects
are validated, hashed and downloaded into bounded temporary storage; isolated
PyMuPDF/Tesseract workers produce private observations, not financial writes.
Deterministic comparisons generate findings; append-only human opinions never
certify payment or silently change an expense. Public ledger projections reuse
read-only, repeatable-read accountability snapshots and approved redactions only.

`backend/tests/test_release_journey.py` adds a full HTTP workflow with **real cookie
authentication**, real migrated local PostgreSQL and actual local PDF processing:
OAuth state rejection/login → project creation and GitHub association → reward →
publication → second-user login → Sandbox order/capture → verified and duplicate
webhook → exactly one entitlement/history → maintainer login → expense → private
receipt upload → extraction → amount discrepancy → immutable review/history →
expense publication → approved separate redaction → logout → anonymous ledger.
GitHub OAuth/repository responses, PayPal HTTP transport, and private storage bytes
are mocked. Browser PayPal approval is represented by an APPROVED provider response.
This is not a live GitHub, PayPal or Supabase test, nor a browser automation test.

Additional tests check private-response cache headers and preserve existing Phase 1
users/projects/budgets when upgrading through all later migrations. Earlier tests
continue covering permission matrices, amounts, duplicates, rollback, refunds,
reversals, concurrency, extraction versions and public disclosure.

## Changes

- `backend/app/main.py`: default no-store/no-referrer/nosniff headers for API responses,
  including private profile/history and HTTP authorization errors.
- `backend/tests/test_release_journey.py`: integrated journey and security/migration regressions.
- `backend/Dockerfile`, `backend/.dockerignore`: minimal non-root Python 3.12/Debian
  OCR runtime, source allowlist, healthcheck and PORT binding; no startup migrations.
- `frontend/src/api/client.ts`: unset VITE_API_URL now uses same-origin /api rather
  than constructing an `undefined/api/...` URL.
- `frontend/tests/transparency.test.mjs`, `frontend/package.json`: Node test runner
  exercises actual TypeScript-transpiled API/money helpers, mocked fetch/error paths
  and React server-rendered signed-out loading UI. No new dependency.
- `.github/workflows/ci.yml`: adds migration drift, frontend tests and existing lint
  to existing CI. Hosted Actions was not triggered here.
- `scripts/release-container-smoke.py`: local, synthetic, bounded container smoke.
- `scripts/dependency-license-inventory.py`, `docs/dependency-license-inventory.json`:
  reproducible installed Python metadata/frontend lockfile inventory.

## Security audit

No new critical exploitable defect was confirmed. This is a scoped source review
and regression suite, not a penetration test or assurance of zero vulnerabilities.

| Priority | Finding | Disposition |
| --- | --- | --- |
| High, release gate | Arbitrary untrusted PDF/image decoding is process-limited, not an OS security sandbox; concurrent uploads can launch multiple validators. No application rate/total-project-storage quota exists. | Keep public launch blocked pending ingress limits, abuse policy and hostile-file/load validation; do not claim memory/CPU limits prevent all decoder exploits. No confirmed code-execution exploit found. |
| High, historical credential risk | AGENTS reports a previously committed credential-looking sample. | Do not read/use it here. Owner must confirm revocation/rotation and historical exposure; removal from the current tree would not revoke it. |
| Medium, fixed | Profile, funding history and some errors had no explicit no-store policy. | API-wide response headers now forbid caching and referrer propagation; regression checks representative private/error routes. |
| Medium, configuration blocker | Separate cross-site static/frontend and API origins lose current SameSite=Lax cookies on fetch. | Preserve current CSRF/cookie semantics; require verified same-site routing. Never solve by disabling CSRF. |
| Medium, existing | Abandoned/cancelled/denied limited-tier attempts permanently reserve capacity. | Conservative anti-oversell behavior retained. Use unlimited tiers for a controlled demo; durable provider reconciliation needed before enabling limited tiers broadly. |
| Medium, existing | Missing notification/uncertain checkout recovery is manual; tokens fetched per API call. | Operator reconciliation and provider monitoring required. No invented refund amounts or unsafe automatic stock release. |
| Medium, existing | Redaction approval is maintainer attestation; hidden text/metadata may remain. Signed URLs remain usable until expiry. | Manually inspect true redaction; short-lived signing and reauthorization retained. No automatic publication of originals. |
| Low | OAuth callback query codes could enter access logs in a default server configuration. | Container disables Uvicorn access logs. Hosting/reverse-proxy log retention/redaction must also be checked. |
| Low | Two existing AuthContext lint warnings and Starlette HTTPX deprecation. | Reported; unrelated rewrites avoided. |

Reviewed controls and evidence:

- OAuth uses a random HttpOnly state cookie, constant-time comparison, ten-minute
  cookie lifetime and Secure cookies in production. Invalid state is tested.
  Session secrets are randomly generated, stored only as SHA-256 hashes, expire in
  seven days and are revoked on logout; the journey tests logout and hashed storage.
  GitHub tokens are not persisted or returned. Third-party cookie policies need a browser check.
- All authenticated financial/document/review writes enforce exact trusted Origin
  and database authorization; collaborator/other-project tests deny writes and IDOR.
  PayPal webhook authentication is provider signature verification, not browser CSRF.
- Order amounts/currency use stored tier snapshots, never client values. Before
  capture, provider order, intent, merchant, custom ID, amount and currency must
  match. Canonical capture/order binding is checked before an entitlement is granted.
- Webhook signature verification must return SUCCESS before claiming an event.
  Failed verification/reconciliation rolls back. Stable provider request keys,
  row locks and unique event/order/capture/entitlement constraints cover duplicates.
  Pending/denied/stale events cannot grant or undo terminal revocation.
- Refund/reversal terminal events revoke entitlements, including out-of-order events.
  Actual delivered benefits cannot be recalled by software.
- Supabase host is constrained, redirects disabled, bucket must report private before
  upload/download/signing; service-role authorization stays backend-only. Uploads
  enforce 5 MiB streaming bounds, UUID names/no upsert, SHA-256 and content validation.
  Database-persistence failures attempt object cleanup; ambiguous commits require reconciliation.
- Validator: 256 MiB address space, 5 CPU seconds, 8-second parent timeout. Extraction:
  320 MiB address space, 50 CPU seconds, 60-second parent timeout; process-group kill
  includes OCR; Tesseract is single-threaded, English, 12 seconds/page. Upload PDF
  validation allows up to 100 pages; extraction deliberately rejects more than five.
- Originals, raw OCR, processing errors, storage keys and reviewer notes stay private.
  New transparency routes allow only active projects and published expenses, even
  for owners. Older expense/document APIs intentionally retain active/paused/completed
  visibility. Public findings cover published category overruns only; private counts
  are null, not a false zero. Public approved evidence is explicitly human-reviewed.
- SQL uses parameterized SQLAlchemy; literal wildcard search is escaped. Public
  schemas whitelist fields. Storage/provider errors are sanitized; credentials and
  document bodies are not application log messages. This does not audit host logs.

## Financial consistency and partial refunds

The existing contribution table stores the original captured amount and current
status, not refund transaction IDs/amounts; the webhook table stores only event ID,
type and timestamp, not provider bodies. Therefore authoritative **persisted exact
partial-refund totals cannot be recovered** from these records. We did not query
real provider accounts or invent them from OCR. Original amounts of refund/reversal-
affected captures remain conservatively excluded in full. Exact refunds remain null
with the existing disclosure. A future reconciled refund ledger needs a new reviewed
schema/API contract and historical provider reconciliation.

Tests verify gross/net funding, pending/denied exclusion, duplicate constraints,
refund/reversal exclusion, one expense despite multiple receipts, current extraction
version selection, unchanged financial records after verification/review, and public
financial totals equal to the authoritative snapshot. The journey independently
asserts 500 captured cents and 1000 reported cents; a negative difference is permitted
and never described as available money or verified bank balance.

## Migration audit and checklist

Single linear chain, nine revisions:

1. `89b3d67b1bc5`: users and unique GitHub/email identifiers.
2. `a16c29b1462e`: sessions, unique token hash and user FK/index.
3. `ec107b8b4763`: projects, budgets, membership and constraints/FKs.
4. `f7a100000007`: reward tiers and normalized project/name uniqueness.
5. `6527bb06f9b7`: contributions, events, entitlements; unique capture/order/event/
   user-checkout/contribution-entitlement keys.
6. `d488822839b2`: reported expenses, positive BIGINT/USD/status checks, RESTRICT FKs.
7. `23145456c6e9`: private documents, size/hash/content-type/public-approval checks.
8. `357405104f17`: versioned extraction/attempts, unique document/version and FKs.
9. `a684112224e6`: finding-review audits, unique actor/request key and immutable
   UPDATE/DELETE rejection trigger.

All upgrade functions create new tables/indexes/constraints (and the final trigger/
function), with no drops, financial data rewrite or required column added to populated
old tables. Existing records therefore do not need fabricated backfills. Tests run
the whole chain on a fresh local database and preserve Phase 1 rows across later
upgrades. Existing audit tests verify UPDATE and DELETE rejection. Runtime superusers
can bypass controls: separate migration-owner and least-privilege runtime roles.

Some historical downgrades DROP user/project/payment data; newer downgrades raise.
**Never run downgrade or reset against Neon.** Applied migrations remain unchanged.
No new migration is introduced by Step 6.

Before any approved deployment:

- Verify exact database target without printing credentials; snapshot/backup via the
  provider, and test restoration in an isolated test target under the available plan.
- Inspect `alembic current`, `alembic heads`, and this chain. Check for manual schema
  drift; do not stamp unexecuted migrations to hide errors.
- Rehearse upgrade and preservation on a disposable local/staging copy using synthetic
  data; run `alembic upgrade head`, `alembic check`, and the test suite there.
- Obtain explicit production migration approval. Run one migration process from the
  release image using a direct Neon migration connection, not request startup.
- Verify head, FK/unique constraints and audit trigger; verify row totals after upgrade.
  If app rollback is needed, restore compatible application code and use a reviewed
  forward migration for schema repair; never automate destructive downgrades.

## Dependency and licensing audit

The generated inventory records **32 installed Python runtime/test distributions**
and **70 frontend lockfile entries**. Every npm entry declares a license; metadata
is evidence of a declaration, not proof all embedded/transitive notices are complete.
Python runtime dependencies were resolved and `pip check` passed during the clean
Docker build. Legacy scientific `backend/requirements.txt` is excluded from the
application image and was not treated as a deployable dependency set.

Main declarations: React/TypeScript/Vite/FastAPI/SQLAlchemy/Alembic/pytest are MIT;
Uvicorn/HTTPX/pypdf/python-dotenv are BSD-3-Clause; Pillow is MIT-CMU; psycopg and
its binary wheel are LGPL-3.0-only. Binary wheels also bundle native libraries;
review libpq/OpenSSL and bundled notices/source obligations before redistribution.
Tesseract is Apache-2.0, Leptonica uses BSD-style terms; Debian/Python base images
contain further system packages and their `/usr/share/doc/*/copyright` notices.
Preserve those and vendor license notices in distribution. This inventory is not
an OS-package SBOM or an online vulnerability/CVE assessment.

**PyMuPDF 1.26.7 metadata explicitly says GNU AFFERO GPL 3.0 / Artifex commercial
dual license.** MuPDF is also an AGPL component. The free route requires assessing
the combined application's AGPL obligations, including any applicable corresponding-
source offer for network users under AGPL section 13, copyright notices, build/
installation material and compatible dependency licensing. A public GitHub repo
alone is not evidence that every obligation has been met. No repository root LICENSE
is present. Do not unilaterally license contributors' code or claim legal compliance.
An authorized licensing decision/review is a **release blocker**, not permission to
buy a commercial license.

If the intended distribution cannot meet the AGPL requirements, a practical free
alternative to evaluate is **pypdf for digital text plus pypdfium2/PDFium for rendering
and the existing Tesseract OCR**. pypdf is already present; pypdfium2 declares
Apache-2.0/BSD-3-Clause terms and bundles PDFium/third-party notices that need their
own review. It requires a deliberate provider implementation, extraction-version
bump, raster resource tests and licensing verification. No engine was silently replaced.

Sources to review: https://pymupdf.readthedocs.io/en/latest/about.html ,
https://www.gnu.org/licenses/agpl-3.0.html , https://github.com/pypdfium2-team/pypdfium2 ,
https://render.com/docs/free , https://render.com/docs/docker and
https://render.com/docs/redirects-rewrites . Official documentation retrieval was
attempted here but failed with network URL errors; current provider quotas/rewrites
and current upstream license documentation were not independently fetched. Installed
version metadata and local container execution are the evidence available.

## Render Free preparation

Docker is appropriate because Python-native builds cannot assume permission to
install Tesseract/English language data. Use backend/ as Docker build context and
`backend/Dockerfile`; do not install the legacy scientific requirements. The image:

- Uses Python 3.12 Debian bookworm, pinned direct Python requirements and
  `tesseract-ocr`/`tesseract-ocr-eng` from Debian, with no model download or paid API.
- Runs UID 10001, copies only application/migration files with matching ownership,
  excludes .env/git/tests/caches, sets one OpenMP thread and one Uvicorn worker.
- Binds `0.0.0.0:$PORT`, has a local `/api/health` healthcheck and disables access logs.
  Migrations are never run at boot. `/api/db-health` is a separate database check.
- Uses ephemeral /tmp only for private scratch data, never as receipt storage.
- Supports an optional build-only proxy CA mount, never baked into image layers.

The first non-root smoke failed on source permissions; COPY ownership was corrected
and the rebuilt image passed. Under a local **512 MiB / 1 CPU test cap**: synthetic
health became reachable in **4.14–9.94 seconds** across successful samples, idle
usage was **about 65 MiB**, digital PDF plus PNG OCR took **1.54–1.68 seconds**, and
observed child peak RSS was **78,732–79,312 KiB**.
UID was 10001, PORT 10031 was honored and the PDF total was exactly 1234 cents.
This is one synthetic sample, not a worst-case load benchmark or a measurement on
Render. The 512 MiB cap is our test condition; verify the current free plan's actual
limits and terms before provisioning. English OCR executed successfully in the image.

Docker tag/base and apt/transitive dependencies remain time-varying; archive the
verified image digest and inventory, or pin reviewed digests/full dependency hashes
for byte-for-byte rebuilds. This provides a tested recipe, not a bit-reproducible image.

After blockers are closed and deployment approval is given:

1. Select Render Docker Web Service on the **Free** plan; root directory backend,
   Dockerfile Dockerfile. Do not provision paid workers/disks or a Render paid DB.
2. Configure backend secret names below in the provider UI; keep production secrets
   out of builds and Vite. Point to the separately approved Neon database, use TLS,
   size pools for the free connection allowance (OCR/snapshots use extra connections).
3. Configure `/api/health` health-check path and let the image use the supplied PORT.
   Rehearse cold starts, restart/lease recovery, large files and concurrent uploads.
4. Frontend static build uses Node 22, `npm ci`, `npm test`, `npm run lint`,
   `npm run build`; publish frontend/dist. Vite supports same-origin API URLs by default.
5. Configure and verify a same-origin `/api/*` reverse proxy to the backend on the
   chosen free static host, including OAuth callback routing and Set-Cookie behavior,
   or another explicitly verified same-site topology. Register GitHub's callback on
   the browser-visible API origin. FRONTEND_URL must equal the browser Origin exactly,
   without a trailing slash/path. Do not assume unrelated `onrender.com` subdomains
   are same-site (public-suffix rules and browser policies matter). If the selected
   free host cannot preserve proxy cookies, this deployment topology is **blocked**.
6. Register the public HTTPS Sandbox webhook endpoint; verify real signature delivery,
   full approval/capture and refunds with synthetic accounts. Do not change the
   hardcoded Sandbox API host or use live credentials.
7. Monitor request latency, worker errors, memory, temporary disk, DB connections,
   stale processing records and free-tier quotas. Free sleep/restarts mean request-
   driven extraction and webhook retries need explicit operational recovery.

Required variable **names only**:

- Backend: `APP_ENV`, `DATABASE_URL`, `FRONTEND_URL`, `GITHUB_CLIENT_ID`,
  `GITHUB_CLIENT_SECRET`, `GITHUB_CALLBACK_URL`, `PAYPAL_CLIENT_ID`,
  `PAYPAL_CLIENT_SECRET`, `PAYPAL_MERCHANT_ID`, `PAYPAL_WEBHOOK_ID`, `SUPABASE_URL`,
  `SUPABASE_STORAGE_BUCKET`, `SUPABASE_SERVICE_ROLE_KEY`, `PORT`.
- Frontend: optional public `VITE_API_URL`. No GitHub/PayPal/Supabase secret in Vite.
- Isolated tests only: `TEST_DATABASE_URL` (alongside DATABASE_URL pointing at the
  same fresh local `opendev_test_*` database).

## Reproducing the local checks

From backend/, install requirements-dev.txt into a Python 3.12 environment and
provision Tesseract/English data. Create a new **local** opendev_test_* PostgreSQL
database, set DATABASE_URL and TEST_DATABASE_URL to it, then run
`python -m alembic upgrade head`, `python -m alembic check`, and `python -m pytest -q`.
The existing cloud harness `/workspace/opendev-setup/test-step7.py` automates this
without touching Neon. From frontend/, use `npm ci`, `npm test`, `npx tsc -b`,
`npm run build` and `npm run lint`.

From repository root, `docker build -t opendev-release-test backend` creates the
runtime image; `python scripts/release-container-smoke.py` starts an isolated,
512 MiB-limited local container with synthetic config, asserts health/PDF/OCR, then
stops and removes only that test container. No database/provider connection is
made by this smoke. In managed cloud builds, preserve proxy settings and provide
`--secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt` if needed; do not disable
TLS verification. The script deliberately targets the local Docker socket.

`python scripts/dependency-license-inventory.py` prints the installed Python metadata
and npm lock inventory; capture it to a review artifact in the selected test
Python environment. No production secrets or .env files are read by these scripts.

## Supabase and live manual acceptance checklist

No live Supabase/GitHub/PayPal/Neon/Render call was tested here.

- Confirm the chosen Supabase free project's bucket is private in provider settings
  and via the authenticated bucket API. Confirm anonymous original object GETs fail;
  service-role material is server-only and never logged/bundled.
- With synthetic files and a test DB, upload originals; inspect hashing/metadata,
  duplicate flags, rejection of bad MIME/oversize/encrypted/active PDFs, cleanup after
  simulated metadata failure and recovery after interrupted uploads.
- Process digital/scanned PDF, PNG and JPEG. Check extraction failures/retries,
  interrupted-worker leases and concurrency after a free-instance restart. Exercise
  near-limit valid files under actual host memory/timeouts, not just the sample.
- Approve a truly redacted separate file; signed-out visitor can obtain a 60-second
  download. Originals/unapproved variants/OCR/reviews remain denied. Revoke approval
  and confirm no fresh URL can be created; previously issued URLs may outlive revocation.
- In two browser accounts on deployed HTTPS, test GitHub OAuth state/secure cookies,
  logout/expiration, same-site fetch and hostile/missing Origin rejection.
- Create/review/publish a project and rewards; verify the repository ownership check.
  Test actual Sandbox buyer approval/return/cancel, capture, exactly-one entitlement,
  backer-isolated history and maintainer fulfillment. No simulated completed contributions.
- Resend actual signed completion, delayed pending/denied, refund and reversal events;
  verify no duplicate grant or inflated total and rollback/redelivery on failure.
  Simulator-only events cannot prove real order binding. Check provider/host access logs
  for tokens, OAuth codes, signed URLs and document content.
- Inspect public ledger without login on desktop/mobile: amounts match stored records,
  filters/pagination/errors/empty states work, budget findings are scoped, private
  receipts/notes/keys are absent. Test keyboard/screen-reader use and offline recovery.
- Validate no private secrets are present in built JS or static-host build logs; only
  public configuration is allowed. A local token-name/connection-URL scan is a heuristic,
  not a search against actual production secrets, which were deliberately not accessed.

## Verification results and recommendation

- **176 backend tests passed; 0 failed, 0 skipped** (173 prior plus three release
  cases). Existing Starlette/HTTPX deprecation warning remains.
- **3 frontend assertions passed; 0 failed/skipped**: exact money formatting,
  auth-independent loading rendering, API filters/contracts and error handling.
  They run on Node's test runner with actual TypeScript transpilation and React
  server rendering, not a DOM/browser click-through. The managed filesystem sandbox
  initially reported only a file-level test pass; the final run used supported
  child-process access and explicitly reported all three named assertions.
- TypeScript and Vite production build passed. Repository **Oxlint** passed with
  two existing AuthContext warnings. ESLint is not installed/configured; a separate
  ESLint run was not claimed or substituted with an unsolicited toolchain migration.
- Fresh local PostgreSQL upgrades, forward preservation test and `alembic check`
  passed. No pending model drift; no destructive downgrades executed.
- Clean Docker image dependency install and pip compatibility check passed, followed
  by the bounded non-root startup/PDF/OCR smoke. Docker source ownership was fixed
  after the first smoke failure. No Render deployment ran.
- Frontend dist scan found no backend-secret variable names or PostgreSQL URL
  markers. Actual production secret values were not read for comparison; this
  heuristic cannot certify the absence of every possible credential.
- Whitespace and Python compilation checks passed. Hosted CI, live provider/storage
  flows, actual browser interactions/accessibility and worst-case load remain unrun.

**NO-GO** until: licensing/distribution decision, historical credential review,
verified same-site browser topology, real Sandbox and private-storage flow,
current free-tier plan/quotas, hostile/concurrent-file resource testing and an abuse/
rate-limit policy are closed. A controlled local demo with mocked providers is
validated; this does not authorize deployment.
