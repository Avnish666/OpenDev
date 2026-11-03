# Phase 6 Step 5: application analytics and secure public CSV exports

Deployment remains **NO-GO**. This integrates the existing workspace and adds bounded
read-only CSV projections; it does not add accounting formulas, a database table,
migration, paid export feature, AI agent, private export or background service.
The preceding Step 4 was committed/pushed as e5ce99e at the user's request before
this implementation. Step 5 changes are separate and uncommitted.

## Files and integrated navigation

Created:

- `backend/app/services/analytics_exports.py`: allowlisted projections, CSV writer,
  formula neutralization, generation slots, quota and database/encoding budget.
- `backend/tests/test_analytics_exports.py`: export security, scope, completeness,
  resource-bound, parity and synthetic performance regressions.
- `frontend/src/api/analyticsExport.ts`: shared filtered download client.
- `frontend/src/components/AnalyticsExport.tsx`: renderer-independent controls.
- `docs/phase6-dashboard-exports.md`: this report.

Modified:

- Backend analytics router, analytics service and analytics_development service:
  export routes, independent internal page materialization limits and a reusable
  milestone predicate. Existing public dashboard limits/defaults remain unchanged.
- `frontend/src/App.tsx`: public Analytics navigation/landing route and project suffix.
- `frontend/src/pages/Projects.tsx`: active project selection and existing workspace
  opening at the analytics route; existing project details remain present.
- `frontend/src/components/ProjectAnalytics.tsx`: one shared export control section.
- `frontend/src/components/Transparency.tsx`, `ProjectProgress.tsx`,
  `frontend/src/pages/Maintainer.tsx`: analytics links beside relevant public records.
- Frontend analytics unit tests and Chromium analytics harness: navigation, download,
  error/cancel behavior and both renderer variants.

`#/analytics` lists the existing active public projects for analytics selection.
`#/projects/{id}/analytics` opens the existing ProjectPage and its single lazy
ProjectAnalytics workspace. A hash-change listener also opens it when navigating
from progress/transparency within the same project. Existing Financial Overview,
Spending & Evidence, Development Progress and Maintainer Track Record presets,
shared filters, reset, timestamp/completeness notices and source links remain.
No second analytics dashboard or replacement for Bryntum, chat, ledger or profiles
was created. Maintainer participation listings link their public projects to analytics.
API active-project authorization remains authoritative for signed-out and owner users.

## Export API

All routes are public read-only GETs under:

`/api/projects/{project_id}/analytics/export/{dataset}`

Supported dataset literals:

| Dataset | Data / CSV scope |
| --- | --- |
| expenses | Complete filtered published expense rows, including public vendor/description, reported date, amount_cents, support boolean and public category-finding count |
| financial | One full-project authoritative funding/spending/coverage summary, goal and public finding count, plus explicitly named filtered expense total/subtotal |
| budget | Full-project category allocation, reported_spending_cents, remaining_cents and overspend_cents from authoritative variance |
| roadmap | Complete filtered current-project public milestone history rows: title/status, original/current/asserted dates, timing, revisions and reopened indicator |
| github | Retained filtered issue/PR/milestone count summaries and recent commit-sample count; unavailable remains blank/unknown rather than zero |
| maintainer-delivery | Complete filtered delivery rows for the request project's current owner's active public projects, preserving row project IDs and owner-only attribution |

Every row includes request_project_id, exported_record_count, currency, as_of and
scope. Source project_id is additionally retained on roadmap/owner-history rows.
The first row includes applied compatible filters (JSON) and public limitations;
subsequent rows leave those repeated long columns blank. All rows belong to the same
read snapshot/filter set. Empty datasets produce one explicit metadata row with
exported_record_count=0 and blank record fields, not an invented expense/milestone.
The scope column distinguishes project_full_totals, complete_filtered_records,
retained_snapshot_summary and owner_active_projects.

Monetary columns ending `_cents` are exact integer minor units in the currency
column. For the current source schema that currency is USD. Negative variance or
funding-minus-reports is still a numeric amount, not a wallet/bank balance. No
floating-point money conversion or independently calculated accounting total occurs.
Exact partial refunds remain unavailable; exclusions use original affected captures.

No document download URL, private receipt, OCR result, reviewer finding/note,
backer/user/email, payment/order/capture/account identifier, credential or storage
key is an export column. User-authored vendor/description/roadmap text is included
only where its existing record is explicitly public; the application cannot infer
whether an author accidentally wrote sensitive content into a published description.
GitHub item titles are not required in the summary export; no provider HTML is rendered.

## Filters, consistency and pagination

The endpoints accept the existing typed category/evidence/date_from/date_to/sort,
public scope and DashboardDimensions parameters. Expense dates and current revised
milestone deadlines have inclusive endpoints; invalid/reversed ranges return 422.
Status/outcome/GitHub category/freshness/discrepancy enums retain Step 4 semantics.

Expense exports reuse the same normalized category/discrepancy selection and public
ledger predicates as dashboard rows/SQL aggregates. Budget/funding exports keep
project totals unchanged under expense filters; the financial CSV separately names
its filtered subtotal. Roadmap exports apply the shared milestone predicate before
stable ID ordering. Owner history uses the same milestone predicate on the owner's
complete active-project history, in existing created_at/ID-descending history order;
it never substitutes team participation for owned outcomes. GitHub summaries reuse
the filtered retained snapshot counts, not the ten-row preview as if it were history.

The frontend omits pagination. Unknown offset/limit query choices cannot truncate
exports: export routes ignore pagination and either return the whole eligible
bounded dataset or reject it. They never silently return the visible 50-row page.
Expense and roadmap internal materialization windows are independently selected:
only the requested record export asks for a 1,001-row lookahead. Other datasets ask
for one incidental page row while retaining full authoritative summaries. This avoids
materializing an unrelated full milestone page for a financial/expense export.

Display-only participation/reward choices are not record-export filters. Download
controls explicitly disclose this, as well as owner-history scope, row/byte bounds,
minor units, self-reported delivery, incomplete snapshots and partial refunds.

## CSV and header security

The standard-library csv.writer uses CRLF records and correct double-quote/comma/
embedded-newline escaping. The response is UTF-8 with a BOM for spreadsheet import.
CSV quoting alone is not treated as formula protection.

For every string cell, the formula probe applies Unicode NFKC normalization and
removes whitespace plus Unicode Cc/Cf characters. If the resulting leading character
is `=`, `+`, `-` or `@`, the original text is prefixed with an apostrophe. A leading
ASCII control or Unicode format character also causes neutralization, including tab,
CR/LF and zero-width prefixes. This covers formula-like cells after CSV parsing,
not just the bytes before quotes. Original text otherwise remains unchanged; numeric
server values (including negative amounts), booleans and typed ISO dates remain
values rather than being transformed into formula-like text.

Tests parse the generated CSV again and verify neutralization for direct operators,
leading whitespace/control/newline/zero-width cases and fullwidth compatibility
characters. Quoting, commas, Unicode and embedded line breaks round-trip correctly.
A neutralizing apostrophe is intentionally part of dangerous string cells. Downstream
consumers must not strip it and then open those cells as formulas. Arbitrary future
spreadsheet re-save/import settings cannot be guaranteed by a CSV download.

Filenames use only the validated integer project ID and allowlisted dataset literal:
`opendev-project-{id}-{dataset}.csv`. Project titles never enter HTTP headers or
filenames. The browser independently constructs the same safe filename and downloads
a temporary object URL; it never navigates to a URL or filename supplied by CSV cells.
Responses use text/csv, attachment disposition, no-store, nosniff and no-referrer.

## Authorization and resource limits

Each export independently runs the same active public project authorization inside
an existing REPEATABLE READ / READ ONLY snapshot. Owner cookies do not expand it.
Draft/paused/completed/missing projects return 404; private scope/invalid fields
return 422. Project-specific selectors and owner active-project scope enforce
isolation. No original/private evidence table is projected or source record mutated.

Bounds:

- At most **1,000 data rows**; larger complete filtered scopes return 413.
- At most **2 MiB encoded CSV**; byte excess returns 413 with narrow-filter guidance.
- Existing analytics source limits (including 20 owned projects, 10,000 checked
  source rows, 200 category groups/120 months and 256 KiB coherent projection cap)
  also apply. Thus 1,000 is a maximum, not a promise for every long-text dataset.
- Two generation slots per worker, nonblocking admission; busy requests return 429.
- Ten requests per direct client peer per 60-second window; 2,048 bounded peer
  entries. Quota rejection returns 429 and Retry-After. Forwarded headers are not
  trusted to choose identity; users sharing a proxy may share its quota.
- A cooperative **10-second** SQL/generation deadline, with each SQL statement
  capped at the remaining deadline or five seconds. The encoder checks the deadline
  per output row. Database/deadline errors return a controlled 503 without SQL text.

The generator uses bounded in-memory StringIO/UTF-8 output rather than a background
queue or an unbounded stream. It checks row counts before writing and text/encoded
size during/after writing. A write/read-only transaction and slots are released on
success or error. No CSV is stored in a new application table or backend file.

Per-statement budgets do not preempt pool acquisition, arbitrary Python/OS stalls
or memory allocation. Existing bounded source materialization remains part of the
cost. Peer quotas/slots are worker-local, not distributed ingress protection. These
limits require target-host capacity validation and do not close inherited NO-GO gates.

## Shared Community and Studio controls

AnalyticsExport appears once outside the renderer. It uses the applied filter state,
a dataset selector, Download CSV, progress/error status and Cancel. A ref prevents
duplicate concurrent calls; cancellation/filter/project changes abort the request,
and an aborted response cannot initiate a download. Blob URLs are revoked after use.
Errors map status codes to safe messages and never render backend response bodies.

Both Community and optional Studio use these endpoints. No AG Grid/Charts Enterprise
or Studio-specific export API is invoked. Existing preconfigured Studio initialState,
view-only mode, lazy lifecycle and isolated dependencies are unchanged; installed-SDK
TypeScript validation still runs. Studio trial warnings remain visible. Appropriate
rights are still required for public use and evaluation output must stay local.

## Automated verification, browser acceptance and measurements

**508 backend tests passed, 0 failed/skipped**, 283.82 seconds (30 new cases).
**85 frontend tests passed, 0 failed/skipped** (four new cases). Both TypeScript
configurations, Community and separate Studio builds, lint, compilation and
whitespace checks passed. Local migration upgrade/check reported no drift at head
8c6072dabc59. Existing TestClient deprecation, two AuthContext lint warnings and
large lazy bundle warnings remain. A final six-dataset smoke passed after sorting GitHub summary metrics explicitly;
its first attempt lacked local database connectivity under restricted execution,
and the authorized fresh-database rerun passed all six cases. The earlier full run passed 507 cases before
the final independent-window regression; the final run includes that regression.

Both Chromium variants passed actual CSV file creation/readback, safe fixed filename,
UTF-8, disabled duplicate controls, cancellation, safe 429 errors, signed-out global
Analytics links and the existing expense route. Existing four-preset/filter/mobile/
license-gate/populated-chart checks also passed. Browser HTTP fixtures are synthetic;
backend security/source integrity uses real migrated local PostgreSQL.

Environment: shared Debian 13 cloud, Python 3.12.14, PostgreSQL 16 Docker,
Node 24.19.0/npm 11.9.0 and Chromium 154.0.8037.57. No live provider or target-host
performance is measured.

| Synthetic expense export (one instrumented TestClient request) | Result |
| --- | --- |
| Complete published dataset | 200 rows, one project |
| Request latency with tracemalloc enabled | 196.746 ms |
| SQLAlchemy statements | 30 |
| CSV response bytes | 32,989 |
| Peak traced Python request allocations | 1,988,844 bytes |
| Writer record boundary | 1,000 accepted, 1,001 rejected |
| Encoded response cap | 2 MiB, subject to earlier source/projection caps |

The memory sample is not process RSS, native/DB memory or worst-case long-text
1,000-row capacity. SQLAlchemy counts exclude driver-level budget set_config
statements; those add wire work. One local sample is not a percentile, throughput
or production claim. Every complete dataset must fit both row and byte/source caps.

Browser Vite-development observations: default Community initial charts 2,150.72 ms,
filter input/apply 373.73 ms and development selection 205.54 ms. In the evaluation
build: initial Community 1,832.68 ms, filter 352.09 ms, development 285.22 ms,
first lazy Studio widgets 3,078.08 ms and Studio development switch 1,369.00 ms.
These include initialization and 50 ms polling, not production network/device tests.
Actual download completion/content was checked without inventing a download-latency
benchmark.

| Production JS chunk | KB | gzip KB |
| --- | --- | --- |
| Default analytics shell, filters and exports | 14.98 | 5.15 |
| Default Community renderer | 2,568.11 | 741.44 |
| Optional Studio renderer | 5,278.01 | 1,469.58 |
| Optional build Community renderer | 2,554.37 | 738.04 |
| Optional shared facts/adapters | 13.88 | 4.04 |

Shared export UI adds approximately 0.90 KB gzip to the analytics shell versus
Step 4. Studio's commercial chunk is unchanged; default output has no SDK chunk
and the main lockfile remains free of Studio/Enterprise dependencies. Large lazy
analytics/Gantt assets remain an inherited performance concern. Unit/integration coverage
includes all six public endpoints, field/financial/date parity, complete 55-row
filtered results despite a requested visible page, private/draft/cross-project
exclusion, malicious project-title filename safety, formula probes, Unicode/quoting,
row/byte/deadline/rate bounds and read-only records. The writer accepts 1,000 rows and
rejects 1,001; byte/source caps can reject earlier. Internal-window regression ensures
one dataset does not request full unrelated pages.

Frontend tests cover shared controls, safe fixed filenames/object URLs, filter
propagation without page offsets/local display choices, safe errors and aborted
requests. Chromium performs actual headless file downloads into a disposable folder,
reads the resulting UTF-8 CSV, verifies filename/content, duplicate-button disabling,
cancellation, rate-limit messages, signed-out Analytics navigation and existing
public expense routes. Both renderer variants preserve prior filter/mobile/chart
checks. Browser HTTP datasets are synthetic; backend tests separately exercise real
local PostgreSQL and authorization. No live GitHub/PayPal/storage acceptance is claimed.

## Manual acceptance

1. Use only a fresh local opendev_test_* database. Run the full backend suite with
   APP_ENV=testing and optional EXPORT_PERFORMANCE_FILE for synthetic measurements;
   run alembic upgrade head/check locally. Never use Neon/production credentials.
2. From frontend run npm test, npx tsc -b, npx tsc -p studio/tsconfig.json,
   npm run lint/build and both browser-analytics-smoke variants (TEST_STUDIO=1 only
   with the separately installed permitted local Studio evaluation).
3. Signed out, open Analytics, select an active project, then all four presets.
   Follow analytics links from project/progress/transparency/maintainer listings.
   Existing chat, timeline/list and ledger must remain available.
4. Apply expense/category/evidence/discrepancy/date and milestone/outcome filters.
   Download corresponding CSVs; compare complete records/totals with API sources,
   not just the visible page. Confirm funding/budget scope and owner-history scope.
5. Verify BOM/Unicode, commas/quotes/newlines and neutralized formula-like titles in
   a disposable spreadsheet with formula execution disabled for inspection.
6. Exercise no matches, unknown/private/cross-project IDs, source/byte/row limits,
   ten-request quota, cancelled/rapid repeated downloads and offline retry. Inspect
   safe attachment headers and absence of private fields. Check mobile/keyboard/
   assistive-technology behavior; automated Chromium is not a full accessibility audit.
7. Test the same endpoints/controls in Studio without an editor or paid export API.
   Do not publish evaluation assets or infer public rights from trial initialization.

Known limits remain: conservative partial refunds, incomplete/deleted retained GitHub
records, maintainer-asserted delivery, mutable current public eligibility across
separate downloads, current-owner attribution, existing source/payload bounds,
worker-local quotas and unverified production resources/proxies/legal/service gates.
**Deployment remains NO-GO. No production migration, deployment or Step 5 push.**
