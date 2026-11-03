# Phase 7 Step 2: remediation and deployment preparation

Assessment: 2026-11-03, Asia/Calcutta. **NO-GO for public deployment.** This step
changes code and prepares a reviewable Community artifact; it does not deploy,
access production credentials, rotate credentials, migrate Neon, buy services,
rewrite history, commit or push. Owner verification of credential rotation remains
required. The Step 1 register remains authoritative with the amendments below.

## Scope and changed files

The checkout remains `main` at `fb5d5fc`. All initially uncommitted Phase 6 Step 6
and Phase 7 Step 1 work was preserved. Nothing was staged. No existing migration
was edited. Changes in this step:

| Area | Files and purpose |
| --- | --- |
| PDF engine | `backend/requirements-app.txt`, `app/services/receipt/{pdf_backend,worker,provider,findings}.py`: replace PyMuPDF with pinned PDFium, preserve OCR/text/evidence, version results and compare invoices across old/new extractors |
| Resource control | `app/services/decoder_limits.py`, `services/documents.py`, `document_validation_worker.py`: shared decoder admission, bounded validator stdout, process-group timeout cleanup, kernel limits/no-new-privileges |
| Refund ledger | `app/models/funding.py`, model exports, `services/{funding,paypal,refunds}.py`, `schemas/funding.py`, `routers/funding.py`: verified refund resource lookup, immutable records, cumulative totals, replay and reversal handling |
| Migration | New `backend/migrations/versions/b7a200000001_add_exact_refund_observations.py`: additive nullable total, ledger, constraints and append-only/monotonic triggers |
| Public accounting | `services/{accountability,expenses}.py`, `schemas/accountability.py`, `agent/financial_reasoning.py`; frontend `api/analytics.ts`, `FinancialFacts.tsx`, `AnalyticsExport.tsx`: consistent known/unknown refund accounting and disclosures |
| Container/configuration | Both Dockerfiles, `deploy/README.md`, `backend/.env.example`, `.gitignore`, `scripts/{release-container-smoke,release-credential-audit}.py`: root-owned readable code, required merchant ID, backup ignores, restricted smoke profile, working-only credential scan |
| Regression fixtures | `backend/tests/pdf_fixtures.py`, extraction/payment/release-journey tests; new `test_phase7_{refunds,documents}.py`; frontend analytics test: independent PDF generation, old-schema preservation, refund races/amount checks and real resource bounds |
| Evidence | This report, Step 1 register amendments, PDFium notice/credential review JSON, final dependency inventory and before/after Python advisory JSON |

Paths abbreviated under `app/` are beneath `backend/`; frontend component paths
are beneath `frontend/src/components/`. Existing Step 1 same-origin static hosting
and the six original Step 6 files remain in place. No new public product feature,
refund initiation endpoint or external payment flow was added.

## Confirmed defects fixed

1. The validator still buffered subprocess stdout in a parent PIPE. It now spools
   to a private regular file, rejects more than 4 KiB before reading, reads at most
   4,097 bytes and kills/drains the worker process group on timeout. The worker's
   file limit is now 4 KiB so ordinary JSON output works; it no longer assumes a
   zero file limit constrains pipes. Step 1's extraction-output bound is retained.
2. Validation and extraction could run simultaneously under independent controls.
   They now share one nonblocking decoder slot per API process, reducing combined
   native-memory pressure. Upload validation returns 429/Retry-After; extraction
   records a private busy failure that needs an authorized retry. DB advisory
   extraction serialization across instances remains. This is not global ingress
   admission: concurrent streaming uploads/storage still need limits.
3. Worker resource restrictions now prohibit core dumps, cap descriptors at 64 and
   set Linux `no_new_privs` before native processing/OCR. Address-space/CPU/file and
   wall-clock bounds remain. Image decompression warnings become errors. PDF size,
   text count, page dimensions and raster allocation are bounded before expensive
   stages; native objects and temporary files close on exceptions.
4. A late refund could change an already reversed contribution back to refunded.
   Reversal now wins permanently; refunded/reversed rewards remain revoked and the
   original capture is not subtracted twice. Pending/denied/failed captures cannot
   be counted as completed by a refund notification.
5. Exact refund amounts/IDs were discarded. The additive ledger now records
   verified completed refunds, bounds cumulative amounts and preserves transaction
   and event idempotency. See the accounting contract below.
6. Duplicate-invoice detection was hardcoded to `local-rules-v1`, which broke with
   the deliberate extractor upgrade. It now compares completed results from both
   the known old version and the current version without deleting historical data.
7. Runtime app ownership previously allowed the app UID to modify its code. Both
   images now use root-owned, explicitly readable code/config/migrations/assets.
   The first ownership-only build inherited restrictive source permissions and
   could not start; explicit `u=rwX,go=rX` permissions corrected that regression.
8. `PAYPAL_MERCHANT_ID` is required for server-side payee validation but was absent
   from the environment example/deployment table. Both now document it as a
   placeholder/runtime setting, never a browser variable.
9. Version-specific advisory review confirmed affected Pillow/pypdf pins. They now
   use Pillow 13.0.0 and pypdf 6.21.4; the post-update 32-package metadata review
   reports no advisory entries. See the scoped evidence and limitations below.

## Licensing decision: implement the permissive PDF path

Path A was assessed: keeping PyMuPDF 1.26.7 requires an authorized AGPL/commercial
decision, contributor/application rights and compatibility assessment, notices,
complete corresponding source/build/install material and the applicable remote-user
source offer. A public repository alone does not establish compliance. No paid
license or unilateral application license was authorized.

**Path B is implemented:** `pypdfium2==5.14.0` replaces PyMuPDF in the web dependency
manifest and runtime text/raster adapter. pypdf 6.21.4 remains the BSD structure
validator/writer; Pillow 13.0.0 remains MIT-CMU image handling; Tesseract remains
Apache-licensed English OCR. PDFium's wrapper declares BSD-3-Clause/Apache-2.0 plus
bundled dependency licenses. Its Linux x64 wheel retains 18 bundled notice files,
including PDFium/component notices; their installed paths and SHA-256 hashes are
recorded in [`phase7-pdfium-license-review.json`](phase7-pdfium-license-review.json).
The new image retains wheel `.dist-info` license material. This is an inventory of
the actual wheel, not a legal opinion about the whole application.
Its PDFium build is `156.0.8076.0` with no optional build flags declared; bundled
dependency notices include PDFium, FreeType, ICU, libjpeg-turbo, OpenJPEG and others.

The adapter extracts native character text/boxes, groups lines, and converts
PDFium positions to displayed top-left PDF points, including rotation. Sparse pages
render at bounded resolution for the existing Tesseract pipeline. Forms are disabled
for rendering and upload validation still rejects active/embedded/form content.
No JavaScript runtime, remote document service or paid OCR was introduced.

Compatibility evidence includes digital/scanned PDFs, PNG/JPEG OCR, page limits,
all four page rotations with box bounds, corrupt/encrypted objects, native kernel
resource limits and the authenticated expense-to-evidence journey. PyMuPDF was
uninstalled from the local test environment; the new image also verifies its absence.
Test PDFs now use pypdf/Pillow, so successful tests cannot rely on the old engine.

Behavior differences: PDFium's text grouping/font interpretation and OCR raster
can differ from MuPDF, particularly for complex layout/fonts. This is not a claim
of universal OCR accuracy. Coordinates remain typed PDF points or image pixels;
new extraction version is **`pdfium-rules-v2`**. Old records/reviews remain intact;
the current-version endpoint can require re-extraction, as its existing contract
specifies, while private accountability can still select older retained evidence.
There is no bulk re-OCR or production migration of extracted content. Pages over
50,000 points, over 100,000 native characters/page, aggregate text/line limits or
unrenderable input fail closed rather than allocate without bounds. Extraction is
still limited to five pages (upload structural validation allows at most 100).

Decision scope: the new runtime no longer introduces MuPDF's AGPL obligation.
Application/contributor licensing, complete third-party notices and any obligations
for earlier artifacts remain owner review items. There is still no root project
LICENSE; none was invented. Optional AG Studio 3.0.0/Enterprise remains Commercial,
local evaluation only and excluded from Community. Bryntum Community remains pinned
MIT-declared beta.1; beta/device acceptance remains open.

Sources reviewed: installed package metadata/bundled license files;
[pypdfium2 5.14.0 metadata](https://pypi.org/pypi/pypdfium2/5.14.0/json),
[pypdfium2 licensing](https://github.com/pypdfium2-team/pypdfium2#licensing),
[PyMuPDF 1.26.7 metadata](https://pypi.org/pypi/PyMuPDF/1.26.7/json),
[GNU AGPL §§1, 5, 6, 13](https://www.gnu.org/licenses/agpl-3.0.html).
Public metadata/installed notices were checked; this task does not claim a fresh
legal signoff or public Studio entitlement.

## Dependency advisory remediation

Version-specific PyPI advisory metadata found affected original pins: Pillow
12.2.0 (80 advisory entries) and pypdf 6.12.0 (67 entries). These entries contain
aliases/duplicates and are **not 147 unique vulnerabilities**. The pre-update
record is preserved in `phase7-step2-python-advisories-before.json`. Pillow 12.3.0
still returned 55 entries; therefore the pinned remediation uses **Pillow 13.0.0**
(Python ≥3.11, compatible with this Python 3.12 image) and **pypdf 6.21.4**. Their
MIT-CMU/BSD licenses are unchanged. All receipt, malicious-input, fixture-generation
and application regressions are rerun after updating the pins and rebuilding both
images. No other dependency was upgraded speculatively.

The final declared runtime/test closure and licenses are recorded in
[`phase7-step2-dependency-inventory.json`](phase7-step2-dependency-inventory.json).
The post-update version-specific advisory check is recorded in
[`phase7-step2-python-advisories.json`](phase7-step2-python-advisories.json).
All 32 queries succeeded and returned zero advisory entries after remediation.
This is public PyPI metadata for 32 installed declared distributions, not a full
Python/native/OS vulnerability audit or a guarantee of no undisclosed flaws.
Sources: [Pillow 13.0.0](https://pypi.org/pypi/Pillow/13.0.0/json),
[pypdf 6.21.4](https://pypi.org/pypi/pypdf/6.21.4/json). Native PDFium, Tesseract and
Debian build/package security still require the release supply-chain review.

## Exact partial-refund contract

PayPal's official public Payments v2 OpenAPI **2.12** was retrieved from
[paypal-rest-api-specifications](https://github.com/paypal/paypal-rest-api-specifications/blob/main/openapi/payments_payment_v2.json).
The `refund` schema supplies `id`, `amount`, completion status, parent HATEOAS links
and optional `seller_payable_breakdown.total_refunded_amount`: the cumulative gross
amount refunded from the original capture. `REFUNDED` and `PARTIALLY_REFUNDED` are
distinct capture states. No live account or production secret was queried.

Processing contract:

1. Verify the signed Sandbox webhook, claim its unique event ID transactionally,
   lock the contribution and validate the capture/order/merchant binding using the
   existing authoritative Sandbox endpoints. Stored capture bindings permit late
   terminal events after an Orders resource expires.
2. Fetch **only** the fixed Sandbox `GET /v2/payments/refunds/{id}` route; never
   follow webhook URLs. Check resource ID, exact fixed-host parent-capture link,
   completed status, matching USD and strictly parsed positive minor units. No
   floats, exponents, rounding, negative, zero or over-capture amounts are accepted.
   This platform currently supports USD contributions, not arbitrary currency scales.
3. Insert one immutable `paypal_refunds` row per authoritative refund ID, storing
   contribution/capture/event binding, amount/currency, optional cumulative amount
   and observation time. Different event IDs for the same refund do not add it
   again; conflicting ID bindings/amounts fail. Same event IDs return duplicate.
4. PostgreSQL locks the parent, bounds the sum of unique refunds and each cumulative
   observation by the original capture, prevents record updates/deletion and parent
   rebinding, and maintains nondecreasing cumulative totals. Out-of-order observations
   cannot reduce the total. The webhook claim and financial/reward effects commit
   together; invalid/pending/provider failures roll back the claim for safe retry.
5. An authoritative cumulative refund observation establishes the recorded total,
   even when individual earlier refund IDs were not locally retained. A verified
   **fully `REFUNDED` capture** establishes its original gross amount as fully
   refunded; it supersedes a stale partial total without fabricating missing refund
   IDs. `PARTIALLY_REFUNDED` alone does not establish an exact amount. Individual
   historical transaction completeness and live settlement remain unknown.
6. A completed refund without a cumulative field can be recorded individually, but
   an unknown historical cumulative total stays NULL. A later distinct refund with
   a cumulative observation can establish it. Duplicate refund IDs preserve their
   original immutable observation. No historical partial amounts are guessed or
   backfilled from contribution creation time, expenses or OCR.

For known cumulative totals, public financial/transparency/analytics/CSV and AI
use the retained portion of the capture: **capture minus recorded refund total**.
For unknown refund-affected rows, the whole original capture remains excluded.
Reversals exclude the entire capture and win over later refunds/completions, without
double subtraction. `exact_refund_total_cents` is nullable: any affected unknown row
or absence of authoritative observations keeps it unavailable. It is an observed
gross-refund total, not a live balance or a verified settlement/net-of-fees figure.
No reliable dated funding trend is introduced: observation time is not refund or
capture time. No refund initiation/money movement endpoint was added.

Any refund continues the existing conservative reward policy: revoke eligibility,
retain fulfillment notes/history and never automatically regrant it on late
completion. Pending/denied/failed captures remain excluded and confer no rewards.
Abandoned limited-tier reservations are unchanged; local time alone cannot prove
a payment failed. Exact historical reconciliation and real Sandbox recovery still
require owner/provider acceptance, so P7-07 is partially remediated, not globally closed.

## Container and untrusted-document status

The combined Community image uses Node 24/Python 3.12 Bookworm, English Tesseract,
one Uvicorn worker, UID 10001, root-owned readable code, configurable `PORT`,
`/api/health` liveness and a separate `/api/db-health` check. No startup migrations,
storage provisioning, model downloads or access logs. Root `.dockerignore` excludes
secrets, Git history, tests/dependency trees and the optional Studio installation.

Validation uses 256 MiB address space, 5 CPU seconds, 8-second parent wall timeout
and 4 KiB stdout/file cap. Extraction uses 320 MiB address space, 50 CPU seconds,
60-second parent wall timeout and 8 MiB file cap; parent reads at most 250,001 bytes.
OCR has a 12-second per-page timeout, one OpenMP thread and a 2 MiB TSV read bound.
Input is at most 5 MiB; image dimensions, PDF pages/object traversal and rendered
pixels are bounded. Descriptor/core/no-new-privileges settings are inherited by OCR.
Output/temp handles are scoped and extraction timeout kills/drains the process group.

The reproducible local smoke profile additionally enforces **512 MiB container RAM,
one CPU, 32 PIDs, read-only root, 64 MiB noexec/nosuid/nodev tmpfs, dropped capabilities,
no-new-privileges and no network**. It exercises digital PDF, scanned PDF and PNG OCR,
non-root execution and absence of PyMuPDF. The no-network profile is a synthetic
smoke test, not the deployable app's required provider topology. It cannot prove
Render supports the same controls or that sustained worst-case traffic fits Free.

**P7-03 remains open:** parser and web app still share UID/process visibility and
filesystem/network permissions during normal application execution. Empty child
environments/no-new-privileges/validation are not an exploit sandbox. Global ingress,
storage quotas, total container/native memory, worker separation, hostile-file load,
abuse policy and host-supported containment need acceptance. A free owner-controlled
isolated runner may be necessary if the intended host cannot enforce the boundary;
do not mount a Docker socket into the web application. No complete isolation claim.

## Credential safety and required runtime names

Rotation status: **owner verification required; no confirmation was supplied**.
Review the redacted Step 1 database/GitHub OAuth exposure findings in
[`phase7-credential-review.json`](phase7-credential-review.json). Do not test or
extract historical values. This step adds/uses the scanner's `--working-only` mode:
it reads zero historical blobs and emits identifiers/categories only. See
[`phase7-step2-credential-review.json`](phase7-step2-credential-review.json).

Current source has no tracked live `.env`/key paths, examples contain placeholders,
build contexts exclude credential files, and client artifacts are scanned for
backend-secret/database markers. These checks cannot establish historical revocation
or detect every disguised secret. CI workflow uses synthetic PostgreSQL settings and
has no environment dump/secret-print step. Historical hosted CI logs remain unreviewed.

| Runtime names | Handling |
| --- | --- |
| `APP_ENV=production`, `PORT`, `FRONTEND_DIST` | Non-secret process settings; image supplies static directory, host supplies port |
| `FRONTEND_URL`, `GITHUB_CALLBACK_URL`, `GITHUB_CLIENT_ID` | Exact same-origin HTTPS/callback registration; client ID is not a backend secret |
| `DATABASE_URL`, `GITHUB_CLIENT_SECRET` | Backend host secret UI only; replace exposed credentials, no Git/build arguments |
| `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_WEBHOOK_ID`, `PAYPAL_MERCHANT_ID` | Sandbox configuration, expected receiver; client secret backend-only |
| `SUPABASE_URL`, `SUPABASE_STORAGE_BUCKET`, `SUPABASE_SERVICE_ROLE_KEY` | Private bucket; service-role credential backend-only |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Optional approved private inference endpoint/model; no weights in image; Render localhost cannot reach a laptop |
| `VITE_API_URL=''`, `VITE_ANALYTICS_RENDERER=community` | Public build configuration; no GitHub/PayPal/storage/database secret in any Vite variable |

No Studio key/Enterprise installation belongs in the public artifact. Studio
evaluation uses only its isolated directory and a separate local build output.
No shared session signing secret exists: random session tokens are hashed in DB.

Owner checklist: identify and revoke/rotate genuine exposed database/OAuth credentials;
review provider access/activity, CI/artifacts/forks and incident scope; update only
backend secret settings; recycle connections and invalidate affected sessions if
needed; record owner/timestamp/provider-side revocation and safe acceptance evidence.
If more credential categories were exposed, use the relevant provider's supported
rotation procedure and verify old keys are disabled. Do not paste replacement values
into chat/reports, authenticate with leaked values or rewrite history without approval.

## Same-origin hosting and service prerequisites

Use the reviewed [`deploy/Dockerfile`](../deploy/Dockerfile) from repository context
`.`. Render settings: Docker web service, Dockerfile `deploy/Dockerfile`, native
HTTPS hostname, health path `/api/health`, automatic deployment disabled. Verify
current Free availability/terms/quotas before creating anything. No service was created.
Frontend and `/api` share one origin; Vite API URL is empty. Configure `APP_ENV=production`,
exact HTTPS `FRONTEND_URL` without trailing slash, and the same origin plus
`/api/auth/github/callback` registered at GitHub.

Preserve Secure/HttpOnly/SameSite=Lax cookies, state lifetime/path, seven-day hashed
sessions, exact-Origin CSRF and single-origin credentialed CORS. Do not loosen them
to work around hosting. Validate OAuth/cancel/logout/session expiry with two users
over actual HTTPS, as well as unknown-route and cache behavior. Suppress callback
query codes in edge logs. Verify trusted proxy/client-IP handling for per-peer quotas
and disconnect/cancellation; do not trust arbitrary forwarded headers.

Neon: use the intended role/database, current free connection/storage budgets and
verified TLS. Prefer a hostname-matching verified connection, e.g. driver options
`sslmode=verify-full` and `sslrootcert=/etc/ssl/certs/ca-certificates.crt` after checking
provider guidance. Use the direct endpoint for reviewed migrations; verify pooler
compatibility/limits for the application. Existing pool is 3 + 2 overflow **per engine**,
not a global budget; account for the extraction lock connection, workers and operators.

Supabase: create/verify a private bucket outside this task, validate anonymous direct
denial, approval/redaction boundaries, 60-second signed-link expiry and cleanup.
Maintainer approval does not remove hidden PDF text/metadata; true redaction needs
synthetic manual inspection. PayPal remains Sandbox; test approval/cancel/capture,
signature replay, multiple refunds, reversals and outages with authorized test accounts.
Ollama requires a reachable approved private free endpoint, model terms/capability,
semantic/injection/citation acceptance and capacity evidence. No live inference was run.

## Migration, backup and recovery runbook — manual only

New linear head: **`b7a200000001`**, parent `8c6072dabc59`. The migration adds a
nullable `contributions.refund_total_cents`, immutable refund table/index and guard
triggers. Existing amounts, captures, rewards, events, receipt/review and roadmap
audit rows remain intact. No historical totals are defaulted to zero. Fresh upgrade,
Phase 1 → payment-era → current-head preservation, constraints and append-only trigger
compatibility are tested locally. There is no destructive downgrade: the new revision
deliberately refuses it, as other audit migrations do.

The following are instructions for a **separately approved operator**, not commands
executed against Neon here. First review/commit the exact artifact only with approval;
identify the database/role and current revision without printing its URL; schedule
a write freeze/maintenance window and verify PayPal's webhook retry/reconciliation
plan. Keep dumps, logs and database credentials outside the repository, access-restricted
and encrypted/protected under the owner's retention policy. Do not use a public CI
artifact for a database backup.

Use an owner-created libpq service file/secret binding; never put a password in the
command or report. `PGSERVICEFILE` refers to that private file, not a checked-in example.
Have a compatible `pg_dump`/`pg_restore` version. Example manual backup commands:

```sh
set -eu
umask 077
export PGSERVICEFILE=/secure/opendev-pg-service.conf
export PGSERVICE=opendev-approved
review_backup_dir=/secure/opendev-backup
mkdir "$review_backup_dir"
pg_dump --format=custom --no-owner --no-acl --file "$review_backup_dir/pre-step2.dump"
pg_restore --list "$review_backup_dir/pre-step2.dump" > "$review_backup_dir/pre-step2.manifest"
sha256sum "$review_backup_dir/pre-step2.dump" > "$review_backup_dir/pre-step2.sha256"
```

Do not overwrite an existing backup: choose a new access-restricted directory for
each run and verify the dump exists, its checksum and the restore rehearsal. A
successful dump/list alone is not proof of a recoverable backup. Record pre-upgrade
revision and financial record counts/totals in a protected audit record without PII.

Restore into an approved **empty disposable rehearsal database**, not over the live
target. Its distinct libpq service must be selected explicitly:

```sh
PGSERVICE=opendev-restore-check pg_restore --no-owner --no-acl --exit-on-error \
  --single-transaction --dbname='service=opendev-restore-check' \
  /secure/opendev-backup/pre-step2.dump
```

Compare users/projects, original captured amounts/IDs, entitlement states/notes,
webhook IDs and append-only audits before/after upgrade. Rehearse on the restored
copy with only its securely supplied `DATABASE_URL`. Once the production migration
is separately approved, run in `backend/` with the reviewed pinned environment and
the approved direct target's URL injected through its secret mechanism:

```sh
python -m alembic current
python -m alembic heads
python -m alembic upgrade b7a200000001
python -m alembic check
python -m alembic current
```

Expect exactly head `b7a200000001` and no schema drift; compare protected before/after
counts/totals and trigger behavior with synthetic records in rehearsal. Test fresh
installation separately. Never replace target identity with the historical example.
Do not run migration automatically on web startup or from multiple app instances.
On failure, keep writes/traffic paused and preserve evidence; prefer a reviewed
forward correction. A restore requires explicit operator approval and reconciliation
of post-backup payment/webhook activity. Never blindly downgrade, delete audit rows,
reset schema or restore a stale dump over live financial writes. The new schema is
additive, but an old binary does not implement the new refund semantics; code rollback
therefore also requires a reviewed maintenance/reconciliation plan.

## Verification results

| Check | Final result / scope |
| --- | --- |
| Complete backend suite, patched pins, fresh migrated PostgreSQL 16 | **552 passed**, zero failures/errors/skips, **2 warnings**, 332.51 seconds |
| Complete frontend suite | **87 passed**, zero failures/skips/cancellations |
| Main and isolated Studio TypeScript checks | Both pass |
| Community and separate local Studio evaluation builds | Both pass; existing >500 kB chunk warnings remain; default `dist` is Community |
| Lint | Exit 0; two existing AuthContext warnings (component exports, set-state-in-effect) |
| Fresh Alembic upgrade/check | Pass at `b7a200000001`, no schema drift |
| Phase 1 → payment-era → head preservation | Pass in full suite: users/project/budget, captured/refunded amounts, NULL unknown totals, entitlement note/state and event ID preserved; no ledger backfill |
| Refund/security regressions | 24 new payment cases plus 9 new document/kernel cases pass within the full suite, including concurrent event/refund-ID replay and DB append-only/sum/monotonic constraints |
| Community/Studio mock-API Chromium smoke | Both pass, sequentially |
| PostgreSQL-backed Community Chromium | **1 passed**, 6 intentionally deselected, one existing deprecation warning; 7.97 seconds |
| PostgreSQL-backed isolated local Studio Chromium | **1 passed**, 6 intentionally deselected, one existing deprecation warning; 14.70 seconds; vendor no-key/trial banners expected |
| Community and backend-only Docker builds | Both pass with patched pins, root-owned readable app files, non-root startup |
| Both restricted Docker OCR smoke runs | Pass for digital PDF, scanned PDF and PNG total extraction; 512 MiB/1 CPU/32 PIDs/read-only root/64 MiB tmpfs/no network/dropped capabilities enforced |
| Same-origin patched image with local DB | Root/asset and health/DB health 200; anonymous profile 401/no-store; unknown API 404/no-store; Secure/HttpOnly/Lax state; untrusted CORS withheld and logout 403 |
| Dependency checks | Local/image `pip check` and main `npm ls --all` pass; optional standalone React-peer diagnostic unchanged (see below) |
| Advisory metadata | 32/32 final PyPI version queries succeed, zero reported entries; both main/optional npm audits report zero known vulnerabilities/no audit errors |
| License metadata | 32 Python distributions, 92 main npm lock entries; PDFium 18 bundled notice files retained; no MuPDF in local environment or either image |
| Credential/build/index checks | Working-only scan reads no historical blobs; current candidates zero; no live tracked environment/key files; default client secret/DB markers absent, no Studio SDK/Enterprise in main lock/bundle; whitespace clean and index empty |

The two final backend warnings are the existing Starlette HTTPX TestClient
deprecation and pypdf's deprecation of `add_js` in the synthetic hostile-PDF fixture.
The latter still constructs/rejects the hostile document; it is not runtime
JavaScript execution. No warning or intentionally deselected check is counted as a pass.
Optional Studio deliberately omits duplicate React/ReactDOM peers and resolves the
parent app's copies. Its standalone `npm ls` diagnostic remains nonzero for those
omitted local peers; types/build/browser pass, not a public license approval.

Early attempts were corrected and rerun: an unmapped imported pytest fixture,
an incomplete synthetic agent request, the version-specific invoice query,
PDFium native-object context management, and a test that incorrectly assumed a
kernel-limited short write must terminate the process. The first ownership-only
image could not read restrictive copied files; explicit read permissions fixed it.
Complete pre-advisory runs passed 551, then 552 tests as the full-refund-status
case was added; the **final 552 result above is after both security pin updates**.
Chromium sources did not change during those library-only updates; full backend
and both container OCR checks were repeated after them.

Final local image IDs (not published/deployed):

- Community: `sha256:7d94e8ef22b2028ce283034cd182309eb6ec2ced475605a94d70f4cb1dcc8424`.
- API-only: `sha256:4cc83ff425669770d98af7e13d59423371bd95063911709f230f904a21d8f527`.

Restricted Community smoke: startup 7.60 seconds, processing 2.49 seconds,
maximum individual child RSS 62,940 KiB, post-run container 67.42 MiB/512 MiB.
API-only: startup 6.84 seconds, processing 2.43 seconds, child RSS 62,256 KiB,
post-run 67.46 MiB/512 MiB. These are one-run synthetic measurements on this cloud
host, not sustained peak aggregate native memory, worst-case hostile load, Render
Free acceptance or throughput guarantees. The combined image separately verified
Pillow 13.0.0, pypdf 6.21.4 and PDFium wrapper 5.14.0, UID 10001, root code owner and
no app write access. Liveness/DB smoke did not contact GitHub/PayPal/Supabase/Ollama.
No hosted provider, CI logs or production migration acceptance is implied.

Reproduce with a fresh migrated **local `opendev_test_*`** database only, setting
both `DATABASE_URL` and `TEST_DATABASE_URL` explicitly to that same target:

```sh
# backend/
APP_ENV=testing python -m alembic upgrade head
APP_ENV=testing python -m alembic check
APP_ENV=testing python -m pytest -q
PHASE6_BROWSER_JOURNEY=1 APP_ENV=testing python -m pytest -q -s tests/test_analytics_release.py -k real_public
TEST_STUDIO=1 PHASE6_BROWSER_JOURNEY=1 APP_ENV=testing python -m pytest -q -s tests/test_analytics_release.py -k real_public

# frontend/; optional dependencies remain isolated, installed with --prefix studio ci --omit=peer
npm test
npx tsc -b
npx tsc -p studio/tsconfig.json --noEmit
npm run lint
npm run build
ANALYTICS_STUDIO_EVALUATION=true npm run build -- --outDir /tmp/opendev-phase7-step2-studio-build
node tests/browser-analytics-smoke.mjs
TEST_STUDIO=1 node tests/browser-analytics-smoke.mjs

# repository root; optional public CA mount for managed environments
docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt \
  -f deploy/Dockerfile -t opendev-review:phase7-step2 .
python scripts/release-container-smoke.py --image opendev-review:phase7-step2
python scripts/release-credential-audit.py --working-only
```

Run Vite browser variants sequentially because their optimizer cache is shared.
The Studio evaluation output is local, never public. Main dependency tree, installed
`pip check`, npm advisory checks, license inventory and schema consistency supplement
functional checks; they do not constitute a complete Python/native/OS CVE audit.

## Remaining blockers and exact next actions

| Register item | Step 2 disposition / required next evidence |
| --- | --- |
| P7-01 credentials | **Open, high**: owner revocation/rotation and incident/CI/artifact review; current working hygiene cannot revoke history |
| P7-02 licensing | Runtime MuPDF dependency removed and permissive replacement tested; **owner application/contributor rights, notices and prior-artifact obligations remain open** |
| P7-03 documents | Resource/admission/privilege/output controls improved and tested; **OS exploit isolation/global ingress/storage/host acceptance remain open** |
| P7-04 free infrastructure | Local constrained smoke is evidence for its synthetic workload only; actual current Render/Neon quotas, sustained native RSS/concurrency, recovery/proxy behavior unverified |
| P7-05 HTTPS auth/logs | Same-origin candidate retained; actual OAuth registration, Secure cookie behavior through HTTPS edge, two-user cache/access and log/proxy acceptance open |
| P7-06 / P7-07 payments | Exact new observations/replays locally supported; live Sandbox verification/reconciliation and unknown historical refund coverage remain open |
| P7-08 storage | Live private bucket, true redaction, expiry/revocation/cleanup acceptance open |
| P7-09 AI | Free model rights, private connectivity, real tool calling/semantic/adversarial/capacity acceptance open |
| P7-10 limited tiers | Conservative abandoned reservations unchanged; durable provider reconciliation needed before broad use |
| P7-11 Studio | Public rights unverified; optional only and absent from Community |
| P7-12 / P7-13 / P7-14 | Beta/mobile/broader-browser/large-bundle, CI/supply-chain/notices and native spreadsheet/re-save acceptance remain open |

Next manual actions, in order: (1) owner verifies revocation/incident scope; (2)
owner approves application/notice/licensing record; (3) infrastructure proves document
containment and zero-budget capacity; (4) payments/storage/AI owners perform approved
synthetic live-provider acceptance and historical reconciliation; (5) rehearse encrypted
backup/restore and the reviewed migration on an approved isolated copy; (6) review
the frozen artifact, all open gates and concrete deployment settings, then obtain
**separate approval** before committing/pushing, creating a public host or migrating
the approved target. No traffic should be admitted until the required public gates
have verification evidence. No optional Studio use without explicit supporting rights.

**Recommendation: NO-GO for public deployment; GO for continued isolated remediation
and review.** Code-level progress does not establish owner-controlled revocation,
historical ledger completeness, legal authorization, exploit containment or service
capacity. No production action was performed.
