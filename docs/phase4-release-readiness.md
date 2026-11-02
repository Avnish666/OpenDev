# Phase 4 Step 6: integration, security and reliability review

Assessment: 2026-11-03 (Asia/Calcutta). **NO-GO for deployment.** Phase 4 local
integration is validated; existing licensing, security and live-service gates
remain open. No production credentials, Neon migrations, deployment, commit or
push were used. Payment and expense processing logic was not changed.

## Architecture and scope

The existing modular monolith is preserved: React/TypeScript/Vite → FastAPI
routers → services → typed SQLAlchemy/PostgreSQL. GitHub REST observations occupy
separate snapshot/run tables. OpenDev commitments, evidence links, immutable status
history and dependency edges are separate from those observations and from finance.
GitHub never changes milestone delivery status. Delivery requires an authorized,
reasoned, versioned maintainer assertion; it is not independent verification.

Public progress and credibility reuse read-only repeatable-read snapshots and the
existing financial accounting service. Funding comes from recorded eligible Sandbox
captures; reported spending and document support are distinct. Original deadlines
come from the earliest immutable creation event, including draft preparation;
a separate first-publication commitment date is not recorded. Attribution covers
current owners of active projects; team membership is separately identified.

The actual installed widget is Bryntum Gantt **Community 8.0.0-beta.1**, loaded on
demand, with explicit confirmation before a versioned date-only PATCH. It uses
local calendar dates, an exclusive display end for inclusive committed dates,
manual scheduling, and no automatic dependency propagation or completion percentage.

Reviewed sources include AGENTS.md, the Phase 3 readiness report, all five Phase 4
implementation guides, routers/services/schemas/models, migrations and tests.
AGENTS.md contains historical onboarding status; installed packages and current
source establish this review's actual status. The checkout already contained
uncommitted Steps 3–5; those changes have been preserved.

## Test results and integration evidence

| Check | Result |
| --- | --- |
| Complete backend suite | **257 passed, 0 failed/skipped**, 135.96 s; 247 preceding + 10 Step 6 cases |
| Complete frontend suite | **26 passed, 0 failed/skipped** |
| Additional database-backed Chromium journey | **1 passed**, same HTTP journey with browser scheduling enabled |
| Installed Community Chromium smoke | Passed all named checks; no runtime exceptions |
| Fresh local Alembic upgrade and `alembic check` | Passed; no model drift |
| TypeScript `npx tsc -b` and production build | Passed |
| Repository Oxlint | Passed; two existing AuthContext warnings |
| Python compilation / whitespace | Passed |
| `pip check`, `npm ls --all` | Passed |
| npm online advisory audit | 0 reported vulnerabilities at review time |
| Dependency/license inventory | 32 Python distributions, 79 npm lock entries; nine Bryntum Community packages all exact beta.1/MIT |

Starlette's existing HTTPX TestClient deprecation remains. Vite reports the existing
large lazy chunk. No Python online advisory or OS vulnerability scan was performed;
package compatibility and npm's advisory result are not a security certification.
The production JS scan found no backend-secret variable names or database URL
markers; no actual secret values were accessed, so this is only a heuristic.
Hosted CI was not triggered.

`backend/tests/test_phase4_release.py` exercises real cookie OAuth state rejection,
login, project creation, draft privacy, publication, GitHub import (milestones,
non-PR issues, merged PR and commit), four evidence types, required change reasons,
date revision, explicit in-progress/submitted/delivered transitions, immutable
original deadline, late-delivery credibility, public summary, logout and signed-out
privacy/write rejection. Financial records remain unchanged. GitHub OAuth,
repository ownership and REST HTTP responses are mocked; PostgreSQL is real and
freshly migrated locally.

With `PHASE4_BROWSER_JOURNEY=1`, this same test starts local Uvicorn and Vite with a
same-origin proxy. Actual Chromium uses the real synthetic database session, renders
the installed Gantt against real API data, confirms a new deadline, and checks the
persisted immutable history. It removes its cookie and checks anonymous access.
The Python journey then submits/asserts delivery and verifies credibility and
public-dashboard calculations. No simulated completed contributions are created.
This bridges browser/API/schema/persistence; it is not live GitHub login or a
hosted HTTPS cookie acceptance test.

The separate two-task Chromium fixture covers real mouse dragging/right-edge
resizing, cancel/confirmation, required reasons, successful versioned save, HTTP
409 and 500 recovery, dependency arrows, stale evidence, hostile-title escaping,
visitor controls, 390 px viewport, timeline/list switching, repeated destruction,
summary-error fallback, lazy module requests and local date mapping in
America/Los_Angeles (DST boundary) and Pacific/Kiritimati (UTC+14).

Earlier tests remain authoritative for concurrency, cycle prevention, cross-project
links, immutable UPDATE/DELETE rejection, cancelled/reopened milestones, current
versus original deadlines, owner/collaborator attribution, refund/reversal and
entitlement exclusions, insufficient history, public evidence/privacy, stale
sources and transaction rollback. Their source was inspected and the full suite
was rerun, rather than relying on preceding summaries.

## Security findings and fixes

No new critical exploitable defect was confirmed. This is a scoped source review,
not a penetration test.

| Severity / status | Finding and evidence | Disposition |
| --- | --- | --- |
| Medium, fixed | Collection verified canonical repository ID before name-based paging but did not recheck a renamed/reused name before persistence. A mocked late identity mismatch reproduced acceptance of the wrong binding in the old flow. | Revalidate public named repository ID/full name before snapshot writes. Mismatch/private/unavailable results fail atomically and suppress known unavailable public sources; prior snapshots remain retained. Regression tests cover late mismatch/private responses. |
| Medium, fixed | Naive commit timestamps could be stored by collection then fail the aware-datetime response contract. | Reject missing timezone before persistence; regression verifies failed run and unchanged snapshots. |
| Medium, fixed | One SQL upsert per GitHub record; overlapping pages were not deduplicated before batch persistence. | Canonical-ID deduplication (newest updated observation for issues/PRs), batches of at most 100; regression covers 2/100/500 provider rows and repeated sync. Counters mean unique observations in this run. |
| Medium, fixed | Maintainer project listing/participation made one membership-role query per team project. | Batch membership lookup. Regression compares one versus thirteen projects with equal query count and correct roles. |
| Medium, open scaling risk | Credibility still performs financial/GitHub aggregation per owned project; internal history loading grows with the owner's public history even when previews are short. | Measured below. Reuses authoritative accounting instead of duplicating financial rules. No claim of unlimited free-tier capacity; ingress limits and a reviewed batch/materialized read design remain necessary before broad launch. |
| Medium, existing beta risk | Large prerelease Gantt chunk, transient browser allocations and limited browser/device coverage. | Exact version pinned, local assets/notices, list fallback, cleanup/GC diagnostics. No automatic upgrade or assertion of leak-free operation. |
| High, inherited release gates | Untrusted decoder isolation/abuse limits and historical credential exposure lack verified closure. | Keep NO-GO; see blocker table. |

Public summary, financial ledger and credibility always exclude non-active projects,
even for an owner. Authenticated management views may deliberately expose that
manager's own drafts; anonymous users cannot use them. GitHub public activity is
withheld after known private/unavailable/identity-changing results. Public history
allowlists commitment fields; frozen source payloads/private audit details are not
returned. Approved separate redactions alone are public evidence. Originals, OCR,
review notes, backer identities, capture IDs, service credentials and storage keys
are excluded from public aggregates. Explicitly public commitment reasons remain
public author text.

API middleware sets `Cache-Control: no-store`, `Referrer-Policy: no-referrer` and
`X-Content-Type-Options: nosniff`, including authorization errors. Authenticated
writes retain exact trusted-Origin CSRF and database permission checks. No tokens
are persisted by GitHub sync or disclosed in sanitized failures. The optional
server-only sync token is used only for the fixed official API host, with redirects
disabled. Frontend source review found no raw HTML rendering/eval sinks; React text,
Bryntum `htmlEncode` and text renderer are regression-tested with hostile titles.
Provider text must remain untrusted data, including for future AI consumers.

## Measured performance and capacity limits

Raw observations and measurement scope are in `phase4-benchmark-results.json`.
Synthetic data only, local PostgreSQL/HTTPX mocks; no external latency. Hardware:
Linux 6.18.57 x86_64/glibc 2.41, Python 3.12.14, Node 24.19.0, five visible logical
CPUs; cgroup allowance 4 CPUs and 32 GiB RAM. This is **not Render Free hardware**.
HTTP timings include TestClient routing, service queries, serialization and response
validation. One warmup + three measured requests, median shown; no latency assertion.

| Scenario | Progress summary SQL / median | Credibility SQL / median | Delivery page SQL / median |
| --- | --- | --- | --- |
| 1 owned project, 35 commitments/history rows, 21 published expenses, 80 issues, 40 PRs | 31 / 29.84 ms | 23 / 17.65 ms | 7 / 9.21 ms |
| 8 owned projects, 280 commitments/history rows, 161 expenses, 640 issues, 320 PRs | 31 / 29.87 ms | 128 / 66.69 ms | 7 / 11.21 ms |

No contributions or documents were seeded in these performance scenarios. Financial
and entitlement correctness uses the separate integration tests. The unused second
project from the standard fixture belongs to another owner and is outside aggregation.
The summary response was about 17.8 KB in both scenarios; credibility grew from
18.3 KB to 47.5 KB. Query count is flat per milestone/expense for public summaries,
but **credibility is approximately 8 + 15 × owned projects** in these scenarios.
Batching team roles does not resolve that remaining per-owned-project cost.

| Initial import fixture | All session SQL statements* | Snapshot/run/repository INSERT statements | Mock GitHub HTTP reads | Elapsed sample |
| --- | --- | --- | --- | --- |
| 1 milestone, 2 issue rows (1 unique), 2 PRs | 12 | 5 | 6 | 337.86 ms |
| 1 milestone, 100 issue rows (99 unique), 100 PRs | 12 | 5 | 6 | 67.74 ms |
| 1 milestone, 500 issue rows (499 unique), 500 PRs | 20 | 13 | 14 | 325.26 ms |

*The engine event counter excludes BEGIN/COMMIT and the separate advisory-lock
connection; the fixture auth/owner is already resolved. These are single initial
samples, not a throughput percentile. First-use initialization explains why the
smallest sample may be slower. Upserts grow by batches, not individual records.
Same-project concurrency is separately tested: second request gets 409 while the
first completes; interruption recovery marks an orphan running attempt failed.
Different-project parallel capacity and DB pool saturation were not load-tested.

Peak process RSS during the full pytest run was 243,552–244,192 KiB at these
benchmarks. This is cumulative in-process test/API peak after preceding OCR/tests,
not incremental service memory, PostgreSQL memory, or a production worker estimate.
A separate benchmark-only run measured 92,548–95,364 KiB. Chromium's two-task Vite
renderer samples, including post-navigation collection diagnostics, are retained
in the JSON artifact; they are not worst-case or production bundle measurements.
For two tasks the renderer used 34,364,968 bytes of JS heap; after navigation it
used 59,947,064 bytes, falling to 38,359,496 after explicit diagnostic GC. These
are sampled V8 heap values, not whole-browser RSS. A growing uncollected heap
alone cannot establish a leak. Short navigation tests
cannot exclude slow leaks or native/DOM memory retention.

Production build: entry JS **300.29 KB / 88.27 KB gzip**; lazy Gantt JS
**1,946.80 KB / 604.00 KB gzip**, lazy CSS **385.38 KB / 68.63 KB gzip**; local font
assets 158.22 KB woff2 and 426.11 KB ttf. Vite's >500 KB chunk warning remains.
CDP verified the widget module is requested on Timeline selection, not initial list
view. Production output has a separate chunk; dev-network checks are not a cold
mobile production download benchmark. UI timeline limits are 1,000 milestones and
1,000 edges; over-limit data falls back to the paginated list.

No Redis, Kafka, paid service, scheduling worker or new caching layer was added.
Current Render/Neon/Supabase plan quotas, connection allowances, free sleep/cold
starts and actual target memory/CPU still require verification. Phase 3's prior
512 MiB/1 CPU container smoke is historical evidence for a small sample, not a
Phase 4 worst-case or hosted capacity test. Synchronous imports may exceed a free
host's request deadline; interruption is retryable but no background scheduler exists.

## Bryntum beta compatibility review

Nine installed Community packages declare MIT and exact 8.0.0-beta.1 dependencies;
existing distribution notices are retained. No paid tier or upgrade was installed.
Installed README/declarations/source and the official tracker were inspected.
The package's `bugs` link redirects from `bryntum/support` to `bryntum/bryntum`.
Relevant upstream reports retrieved during this review:

- [#14103](https://github.com/bryntum/bryntum/issues/14103), open: beta.1 **Scheduler
  Enterprise Timeline** rejects a project config object. This is a different widget
  and tier. OpenDev's actual Community Gantt config rendered successfully; do not
  claim this test resolves the upstream report.
- [#14021](https://github.com/bryntum/bryntum/issues/14021), open: Scheduler 7.3.7
  configured `timeZone` rounds spans twice. OpenDev uses calendar dates without that
  config; local DST/UTC+14 mapping passed. This is related guidance, not confirmation
  of a defect in OpenDev's pinned package.
- [#13788](https://github.com/bryntum/bryntum/issues/13788), closed: generated store
  model-class retention on destruction; maintainer discussion says the fix ships
  in 8.0 and identifies separate dependency-element retention (#13871). That statement
  does not establish which fixes are in this exact beta tarball. Repeated widget
  destruction passes locally, but long-session/large-project heap profiling remains
  an acceptance requirement. ResourceTimeRanges discussed there is not enabled here.

No comprehensive beta errata/security guarantee is available from these checks.
The tested browser is local headless Chromium 154.0.8037.57 (Debian 13), not
Safari/Firefox or a real mobile
screen reader. `--no-sandbox` is a container browser-test constraint, never a backend
document-sandbox recommendation.

## GitHub synchronization contract and limits

Official REST reads: `GET /repositories/{canonical_id}`, `GET /repos/{full_name}`
(final public identity check), `/repos/{full_name}/milestones?state=all`,
`/issues?state=all&sort=updated&direction=desc&since=...`,
`/pulls?state=all&sort=updated&direction=desc`, and `/commits?per_page=30`.
The Issues API PR markers are excluded; merged PRs require `merged_at`.

- At most five 100-record pages per collection, 2 MB per response, 30 recent default-
  branch commits, 10-second HTTP operation timeout and an 80-second checked collection
  budget. This is not a strict hard wall-clock kill (a blocked operation can run to
  its HTTP timeout). Pagination stays on constructed official paths, never follows
  an untrusted Link URL. Reaching the cap with another page aborts the whole import.
- Metadata uses ETags/304; a 304 reuses only metadata, not an assertion that activity
  is unchanged. Final named identity is checked without an ETag. No OAuth token is
  stored; optional configured `GITHUB_SYNC_TOKEN` remains backend-only.
- Issues use last successful **start** minus ten minutes; PRs scan updated-descending
  until the overlap cutoff. Milestones are recollected within the bound. Failed
  attempts do not advance the successful watermark. Edits update retained snapshots;
  deletion does not remove history. Source rows not observed recently can remain stale.
- Run state is committed before collection; snapshot changes and success commit
  together. Failure rolls back the import, preserves valid history, stores a sanitized
  error, and known visibility loss suppresses public source display. Advisory locking
  prevents concurrent same-project imports; retries upsert canonical IDs.
- 403/429 records a shared cooldown across projects, honors reset/Retry-After with
  conservative bounds, and subsequent requests return 429 without calling GitHub.
  There is no immediate automatic retry/sleep loop. Operators retry later; timeouts/
  5xx/malformed/page-limit attempts fail explicitly. Missing repositories, valid
  renames and late identity changes are tested.
- Last success, last attempt, row observation, source update and calculation timestamps
  differ. Status becomes stale after six hours or any latest non-completed attempt;
  linked evidence also checks its own age/sample availability.

**Completed means this bounded attempt committed, not exhaustive import.** A large
initial repository can fail PAGE_LIMIT; a later incremental success can retain old
or deleted snapshots and a limited commit sample. GitHub provides no atomic snapshot
across REST pages: edits and rename races can still interrupt collection. The final
identity check reduces name-reuse contamination, not provider-wide atomicity. Visibility
can change between synchronizations; no live visibility guarantee is made. Unknown
source state cannot certify delivery or imply misconduct.

## Phase 5 read-only evidence interface proposal

Documentation only: no agent, execution endpoint, score, financial write or automated
approval was implemented. Future consumers should use allowlisted public projections
in a read-only snapshot and reauthorize visibility on every retrieval/citation.

| Evidence domain | Authoritative existing entry points | Citation / uncertainty rules |
| --- | --- | --- |
| Project identity and funding | `GET /api/projects/{id}`, `/api/projects/{id}/transparency`; `transparency.overview` | Project ID, currency, integer amounts, calculation timestamp and accounting notes. Sandbox recorded funding is not bank balance/escrow; exact partial refunds remain unknown. |
| Published expenses/evidence | `GET /api/projects/{id}/ledger`, `/ledger/{expense_id}`; `transparency.detail` | Expense ID, published data, approved redaction document ID/hash metadata where exposed. Never originals, private extraction/review endpoints, storage keys or signed bearer URLs in durable citations. A receipt does not prove a transfer. |
| Commitments/dependencies | `GET /api/projects/{id}/roadmap`, `/roadmap/dependencies` | Project/milestone ID + version, planned dates/status and author assertion; active public projects only. |
| Original/revised deadlines | `GET /api/roadmap/{milestone_id}/history`; public `roadmap.history_view` | Immutable history UUID/version/action/time plus milestone ID; record earliest creation separately from later edits. Reasons are public author text, not validated explanations. |
| GitHub signals/source links | `GET /api/projects/{id}/github/activity`, `/milestones`, `/sync-status` | Canonical repository ID + type + GitHub ID or SHA; provider URLs constructed from validated current repo identity/number. Distinguish provider update, observation and sync times; retained/deleted/incomplete samples remain uncertain. |
| Delivery/attribution | `GET /api/maintainers/{id}/credibility`, `/delivery-history`, `/projects` | Maintainer user ID, milestone/history references, current ownership scope, original deadline/timing, formula/sample size. Maintainer assertion only; no personal honesty inference. |
| Reward fulfillment | Public credibility `rewards` aggregates | Numerator/denominator/eligibility formula and calculated time. Never backer IDs/notes; no overdue claim without recorded deadlines; refunded/reversed records excluded as documented. |
| Combined summary/freshness | `GET /api/projects/{id}/progress-summary`; `progress.summary` | Link back to detailed sources, stale flags and limitations. Preview is not exhaustive; calculation time is not verification time. |

Recommended evidence envelope (a **proposed schema**, not a new implemented API):

```json
{
  "schema_version": "proposal-1",
  "source_id": "opendev:project:42:milestone:9:history:history-uuid",
  "project_id": 42,
  "source_type": "roadmap_history",
  "record_id": "history-uuid",
  "record_version": 3,
  "visibility": "public_active_project",
  "claim_kind": "maintainer_assertion",
  "payload": {"planned_end_date": "2026-12-01"},
  "timestamps": {
    "recorded_at": "2026-11-03T00:00:00Z",
    "provider_updated_at": null,
    "observed_at": null,
    "retrieved_at": "2026-11-03T00:01:00Z"
  },
  "citation": {
    "api_path": "/api/roadmap/9/history",
    "record_id": "history-uuid",
    "field_paths": ["after.planned_end_date"],
    "public_page": "#/projects/42"
  },
  "coverage": {"exhaustive": false, "stale": false, "limitations": []},
  "integrity": {"public_projection_sha256": "computed-by-future-consumer"}
}
```

Example IDs/times are illustrative. An aggregation additionally needs formula,
numerator, denominator, sample size, currency and scope; missing values stay null.
GitHub source IDs must include canonical repo ID and record type, not mutable names
alone. Mutable snapshot citations should include observation time/version/hash of
the allowlisted public projection; no existing immutable snapshot archive is implied.
Read every page when coverage is needed; record truncation rather than extrapolate.
Public eligibility can be revoked later; recheck before displaying old citations.

Treat titles, descriptions, reasons and evidence documents as untrusted source data,
never instructions. A future AI explanation may identify evidence and uncertainty,
but only application code performs arithmetic and authorization. Give its database
role SELECT-only access to approved views, or an explicit GET-only API allowlist.
Do not give it payment/capture, expense edit/publish, document publication, sync,
roadmap status or review write credentials. Proposed recommendations must remain
separate from authoritative records and require a human to use the normal protected
workflow. This proposal does not grant future write authority.

## Deployment blockers: unchanged NO-GO

| Gate | Current evidence / required closure |
| --- | --- |
| PyMuPDF/MuPDF AGPL | Installed PyMuPDF 1.26.7 declares AGPL/commercial dual terms. No root project LICENSE/authorized compliance decision. Obtain licensing/distribution review or deliberately evaluate a free replacement; no paid purchase or unilateral licensing. |
| Hostile document processing | Existing resource-limited subprocesses are not OS exploit isolation. Concurrent parser abuse, upload/project quotas, ingress policy, hostile-file and target-host load testing remain open. |
| Historical credential exposure | No credential or history value was opened/used. Owner evidence of revocation/rotation and incident review remains required. |
| Partial refunds | Existing conservative full capture exclusion/revocation remains; exact refund amounts are unavailable. A reconciled refund ledger requires separate reviewed work. No financial logic changed here. |
| PayPal Sandbox live flow | Mocked tests pass; real buyer approval/cancel/capture/signatures/delayed/refund/reversal and operator reconciliation still need a test-account acceptance record. No live payments permitted. Limited-tier abandoned reservations remain a known limitation. |
| Supabase live verification | No live private-bucket/upload/download/expiry/revocation acceptance performed. True redaction, cleanup and service-role isolation must be checked on synthetic test files. |
| HTTPS cookies/domain/logging | Local same-origin Chromium session works, but deployed Secure/SameSite/proxy/CORS/CSRF topology and host log redaction are unverified. Do not disable Origin checks to pass hosting tests. |
| Render/Neon/free-tier resources | Current free quotas not independently verified here. Connection pools, long sync requests, OCR concurrency, cold starts and memory/CPU need target-host evidence. No claim local 32 GiB capacity maps to Free. |
| Bryntum beta/bundle | Pinned Community beta passed local Chromium tests. Large lazy assets, long-session retention, low-memory/mobile/accessibility and broader browser acceptance remain release risks. |

## Manual acceptance and reproduction

Only use a fresh local database whose name starts `opendev_test_`; never point these
commands at Neon. Set `DATABASE_URL` and `TEST_DATABASE_URL` to that same disposable
local database and `APP_ENV=testing`. Install the existing requirements-dev.txt and
OCR runtime as described in Phase 3. From backend/:

```sh
python -m alembic upgrade head
python -m alembic check
python -m pytest -q
PHASE4_BENCHMARK_DIR=/tmp/opendev-phase4-benchmarks python -m pytest -q -s tests/test_phase4_performance.py tests/test_github_progress.py
PHASE4_BROWSER_JOURNEY=1 python -m pytest -q -s tests/test_phase4_release.py::test_cookie_authenticated_development_journey
```

The final command requires frontend dependencies, `/usr/bin/chromium`, Node and
Uvicorn; it starts only loopback test servers and forwards only the synthetic session.
CI's default pytest path uses HTTP scheduling when that flag is absent; no browser
skip is hidden in the 257-test count. The additional opt-in run was executed locally.
The environment's `/workspace/opendev-setup/test-step7.py` automates fresh local DB
creation/migrations/full tests; it is an environment helper, not repository setup.

From frontend/ with existing lockfile dependencies:

```sh
npm test
npx tsc -b
npm run build
npm run lint
npm run test:gantt-browser
npm ls --all
npm audit
```

From root: `git diff --check`, Python compilation, `python -m pip check` in the app
venv, and `python scripts/dependency-license-inventory.py`. Inventory reports declared
licenses, not a complete legal review or OS SBOM. No dependency upgrade is implied.

Before any separately approved deployment, record manual evidence for:

- Real GitHub OAuth/HTTPS cookie login, logout/expiry and hostile/missing Origin;
  create/publish with correct owner and wrong-account denial.
- Public repo initial/repeated sync, rename, inaccessible/private transition,
  rate-limit/retry, pagination cap and stale old evidence. Compare canonical IDs
  and GitHub source links, not just displayed counts.
- Dependency cycles/cross-project rejection and two-tab version conflict; explicit
  Gantt confirmations and immutable original deadlines across reopened/cancelled
  commitments. No automatic delivery after issue closure/PR merge.
- Signed-out views for draft/paused/completed projects, private receipts/OCR/reviews,
  unavailable GitHub sources and backer isolation, including proxy/cache behavior.
- Production lazy asset loading, keyboard/screen-reader list fallback, mobile zoom,
  slow/offline/error recovery, long navigation sessions and large supported timelines
  in target browsers; record heap/native memory rather than assume no leak.
- All inherited licensing, credential, live Sandbox/storage and free-host gates above.
  Rehearse forward migration/backup/restore on an approved test target first.

## Files and migration disposition

Step 6 modified `backend/app/services/github_progress.py`,
`backend/app/schemas/github_progress.py`, the existing uncommitted
`backend/app/services/credibility.py`, `backend/tests/test_github_progress.py`, and
`frontend/tests/browser-gantt-smoke.mjs`. New files:
`backend/tests/test_phase4_release.py`, `backend/tests/test_phase4_performance.py`,
`backend/tests/phase4_browser_support.py`, `frontend/tests/browser-phase4-journey.mjs`,
this report and `docs/phase4-benchmark-results.json`. Other pending files belong to
the preserved Steps 3–5 implementation.

No Step 6 model/schema migration is needed. The twelve-revision linear chain ends
at **8c6072dabc59** (dependency edges), following **975a8a867d0d** (roadmap/history)
and **2e1d281b5505** (GitHub snapshots). Phase 4 upgrades are additive table/index/
constraint/trigger creation; no financial rewrite or destructive upgrade operation.
Fresh local upgrade, no-drift check, history immutability and Phase 1 forward-record
preservation pass. No historical migration changed or destructive downgrade ran.

**Recommendation: GO for continued local development and read-only Phase 5 interface
design; NO-GO for public deployment.** This report does not clear inherited blockers
or authorize production actions.
