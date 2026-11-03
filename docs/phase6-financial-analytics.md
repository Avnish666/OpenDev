# Phase 6 Step 2: financial analytics dashboard

Phase 6 Step 3 adds [development and maintainer analytics](phase6-development-analytics.md),
independent history paging and request-local public query batching. See that report
for current development contracts and updated performance measurements.

Deployment remains **NO-GO**. Community is the default. Studio remains an isolated,
optional local evaluation or appropriately licensed renderer. No paid subscription,
AI feature, payment processing change, accounting table, migration, deployment,
commit or push is part of this work.

## Files

Created:

- `frontend/src/components/FinancialFacts.tsx`: shared financial definitions, coverage,
  sortable accessible budget table, expense chart alternatives and public detail links.
- `frontend/studio/financialDashboard.ts`: typed, preconfigured official Studio state.
- `docs/phase6-financial-analytics.md`: this report.

Modified:

- `backend/app/schemas/analytics.py`, `routers/analytics.py`, `services/analytics.py`:
  filtered grouped expense contracts, query validation, public finding count and
  explicit unavailable funding-trend contract.
- `backend/app/services/transparency.py`: shared expense-query predicates and optional
  date/canonical-category constraints; analytics can reuse its already-calculated
  snapshot instead of calculating it again inside the ledger. Existing public ledger
  defaults and response contracts are preserved.
- `backend/tests/test_analytics.py`: financial grouping, filters, bounds, dates,
  evidence, privacy, no-history, representative performance and normalization tests.
- `frontend/src/api/analytics.ts`: typed filters/datasets and allowlisted Studio adapter.
- `frontend/src/components/ProjectAnalytics.tsx`, `ProjectAnalyticsCommunity.tsx`,
  `ProjectAnalytics.css`: shared filters, financial overview, responsive charts/grid,
  pagination, errors, reset and safe monetary presentation.
- `frontend/src/App.tsx`, `components/Transparency.tsx`: a shareable public expense
  route reusing the existing public detail component and authorized ledger API.
- `frontend/studio/ProjectAnalyticsStudioRenderer.tsx`: preconfigured view-mode report.
- `frontend/tests/analytics-fixture.mjs`, `analytics.test.mjs`,
  `browser-analytics-smoke.mjs`: adapter/renderer and actual Chromium acceptance.
- `docs/phase6-analytics-foundation.md`: link to this follow-on contract.

No dependency or lockfile changed. Commercial dependencies remain confined to the
previously authorized optional Studio installation.

## Financial definitions and public scope

All full-project money and evidence totals still delegate to
`transparency.overview` → `accountability.snapshot(db, project, None)`. The request
runs inside the existing REPEATABLE READ / READ ONLY transaction; calculations do
not modify source records. The browser never calculates a funding balance from rows.

| Metric | Meaning |
| --- | --- |
| Funding goal | Current campaign goal, in project currency |
| Gross completed PayPal contributions | Original captured completed/refunded/reversed contributions; capture IDs deduplicated by existing service/database constraint |
| Refund-affected capture exclusions | Original amounts of currently refund-affected captures, **not exact refunded amounts** |
| Reversal-affected capture exclusions | Original amounts of currently reversed captures |
| Net recorded funding | Authoritative gross minus both exclusions; pending/denied/failed/uncaptured records do not count |
| Published reported spending | Published maintainer expense claims in project currency; drafts excluded |
| Funding minus reported expenditure | Calculated difference; **not a verified bank balance**, cash, escrow or independent vendor-payment evidence |
| Document-supported reported spending | Published expense amounts with approved, published public redactions, each expense counted once |
| Without public supporting documents | Exclusive remaining public coverage bucket; private documents might still exist |
| Public unresolved financial findings | Number of distinct currently over-budget public categories, not a sum of findings repeated on expense rows |
| Last calculated | Transaction calculation timestamp, not last source update, capture time or settlement time |

Partial refunds are deliberately conservative: the existing integration does not
retain exact refund amounts, so the full affected capture is excluded. The exact
refund total remains null. UI text explicitly distinguishes exclusions from refunds.
Private OCR/findings/reviewer opinions and original/private receipt metadata never
enter these datasets; private discrepancy counts remain null/unknown publicly.
Approved documents do not prove vendor payment. Multiple receipts never multiply an
expense's count or amount. Public category findings make no individual payment or
fraud allegation.

Budget allocation, reported spending, remaining allocation and overrun are copied
from the authoritative budget variance. Unallocated categories show zero planned
allocation and an over-budget indicator where applicable. Category comparisons follow
that service's stripped Unicode casefold keys, including Straße/STRASSE equivalence.
All server calculations use integer minor units. Charts convert to major units only
for presentation. Exact-value text uses the existing guarded integer money formatter;
unsafe JavaScript integers are withheld/warned rather than shown as rounded money.

## API contract

Existing endpoint extended additively (schema_version stays `1`):

`GET /api/projects/{id}/analytics/overview`

| Parameter | Default / validation |
| --- | --- |
| limit | 50; 1–100 |
| offset | 0; 0–10,000, expense page only |
| scope | public only |
| category | empty/all; max 100 characters; stripped/casefold exact category |
| evidence | all, supported, unsupported; approved public redactions only |
| date_from / date_to | Optional parsed calendar dates, inclusive; invalid/reversed ranges return 422 |
| sort | date_desc or date_asc; date and ID together give deterministic tie ordering |

New fields:

- `expense_analysis.categories`: `{key, expense_count, amount_cents}` for all matching
  reports, independent of the expense page. At most 200 normalized categories.
- `expense_analysis.months`: same shape, key `YYYY-MM`, at most 120 observed months.
- `expense_analysis.expense_count`, `reported_spending_cents`: filtered full-scope totals.
- `expense_analysis.date_basis=maintainer_reported_expense_date`.
- `expense_filters`: applied category/evidence/date/order values; absent dates are null.
- `public_unresolved_finding_count`: full-project public category-overrun count.
- `funding_trend: {available:false, reason}`.

Expense filter predicates are shared with the public ledger. Grouping uses bounded
source reads and SQL integer SUM/COUNT, with canonical category merging. Supporting
documents use EXISTS, so multiple receipts cannot fan out expense groups. No per-row
query is introduced. Categories with equivalent Unicode spellings are resolved once
per category-filtered request. The grouped datasets are new presentation datasets;
funding/budget/coverage formulas are not duplicated.

Funding, budget, evidence overview and public findings remain **full-project** when
expense filters change. Expense grid and expense category/month charts use the same
filtered source. Both renderers receive the same authorized response. Development
preview remains the first bounded page; expense paging does not move that preview.
The UI no longer couples next/previous expense buttons to milestone counts.

Existing source preflight limits (20 active owned projects, 10,000 records per checked
source) and 256 KiB response cap remain. Excess group counts return 413 with a
narrow-filter explanation, never silent truncation. Public endpoints require an
active project, even with an owner cookie; other project statuses/missing IDs return
404, private scope 422. No backer identities, capture IDs, storage keys, original
receipt IDs, OCR, private reviewer notes or private draft expenses are returned.
No new private analytics endpoint or document-fetching capability exists.

## Dates, freshness and funding history

Months use maintainer-reported expense dates. They are neither receipt upload dates
nor PayPal capture dates, and they do not independently establish when payment
occurred. ExpenseCreate and database constraints require a valid non-null date;
invalid/missing dates cannot be substituted with upload/calculation time. Only
observed months appear, sorted chronologically. Empty intervals are not fabricated
zero observations. Dates/range tests cover invalid calendars, inclusive endpoints,
reversed ranges, sparse periods and empty results.

A reliable **funding trend is omitted**. Contribution.created_at is checkout creation,
not capture time; webhook receipt time is not settlement time. Records do not retain
capture timestamps or dated exact refund/reversal amounts. Current-state exclusions
cannot reconstruct historical adjusted balances. Neither renderer synthesizes a
funding chart or historic snapshots from these fields. The reason is visible in
both views and the API. No PayPal code or stored payment data changed.

Each refresh/filter/page request has its own snapshot. Concurrent publication may
shift offset pages; refresh reconciles them. Calculation time is not source freshness.
Existing public owner/development limits and query materialization costs remain.

## Community renderer

Actual MIT AG Charts Community 14.2.0 / AG Grid Community 36.2.0 provide:

- Financial cards and full public coverage counts/amounts, with explicit limitations.
- Grouped budget allocation/spending/remaining bars (negative remaining = overrun).
- Filtered category pie, observed monthly expense bars and full-project public
  document-coverage pie. Empty sources produce useful text states, not dummy rows.
- Sortable, read-only paged expense grid; global date ordering comes from server
  filters, while header sorting is explicitly labeled as current-page sorting.
- Shared category/date/evidence/order controls, Apply/Reset, bounded next/previous,
  refresh/loading/error recovery and date-range feedback.
- Accessible labeled chart regions, exact category/month text alternatives, sortable
  budget table, non-color-only overrun status, and public expense links.

The new `#/projects/{project_id}/expenses/{expense_id}` route reuses the existing
public ExpenseDetail component; its GET ledger detail rechecks active-project,
project and publication visibility. No private management page is linked.

No Enterprise module is imported into Community. No custom HTML chart tooltip is
used; React/grid default text rendering escapes hostile source labels. Mobile chart
and grid regions remain contained at a 390px viewport. Formal screen-reader and
broader-browser certification are still separate acceptance work.

## Genuine optional Studio dashboard

Installed 3.0.0 vendor declarations were checked for `AgStudioProperties.initialState`,
`AgReportState`, page `widgets/widgetLayout`, `AgValueWidget`, `AgBarChartGrouped`,
`AgPieChart`, `AgGridWidget`, field format/accessors and qualified source.field
references. Official README and shipped definitions document these contracts. The
current official web state-doc request returned HTTP 403 through this environment;
no successful web-doc review is claimed. Both installed-SDK TypeScript checking and
real browser numeric widgets/charts validate the configuration.

Studio receives a real preconfigured `initialState` report, selected financial page,
explicit layout and field definitions, plus the six allowlisted public financial
sources: financial, budget, expenses, expense_categories, expense_months, evidence.
It opens with three numeric KPIs, budget comparison, category/month/coverage charts
and expense table when observations exist. Shared financial facts/tables expose all
other required metrics and accessible alternatives. No manual report building is
needed. Empty sources/widgets are omitted; the real zero-valued financial summary
is retained. Field accessors convert minor units to presentation units and use the
recorded currency formatter.

Chart measures use the supported `first` operation on each unique backend group,
not sums of paged expense rows. A browser check caught that unaggregated chart fields
mounted canvases but showed no data; first-value mapping fixed it. Acceptance now
checks populated charts, real numeric KPIs and grid rows, not mounting alone.

`mode="view"` is explicit. Edit/data/AI panels are not exposed; no AI harness,
expression engine, joins, custom accounting formulas, save/persistence callback or
financial-write callback is configured. Shared server filters apply in both modes.
The Studio instance is recreated when source/page/filter/mobile shape changes because
its initialState is initial-only and source addition/removal is not a reactive API.
Mobile uses a single-column report. Source datasets remain bounded pages/groups.

Existing lazy import, build alias and license gates remain. Normal Community builds
have no Studio SDK chunk. Optional evaluation is loopback-only and must not be
published; a licensed flag plus an operator-supplied valid key and reviewed rights
are required for licensed use. Flags do not grant rights. Trial watermarks/license
warnings were visible during local evaluation and were not suppressed. No key,
subscription or production permission was obtained. See the foundation guide for
isolated installation and vendor license details.

## Validation and measured local performance

Backend: **444 tests passed, 0 failed/skipped**, 231.95 seconds, including 37
analytics cases (22 added in this step). Frontend: **69 tests passed**, none failed/skipped; both main and installed-SDK
TypeScript configurations, Community build, separate Studio evaluation build and
lint passed. Only the two existing AuthContext lint warnings and large lazy
analytics/Gantt bundle warnings remain. Python compilation and whitespace checks
passed. The final full suite includes the Unicode category regression.

Chromium passed both default Community/license-gated and explicit local Studio
variants. Actual chart canvases and grid rows rendered; Studio numeric KPI values
were $40.00/$1,000.00/−$960.00 for its synthetic server fixture. Tests verify populated
Studio charts rather than a blank report, view mode, category/date/evidence/date-order
requests, reset, reversed-date feedback, next-page offset, 390px layout in both
renderers, switching, empty/error/retry states and hostile label escaping. The actual
signed-out App hash route opens the existing public expense detail and amount.
No optional Studio source/package request occurs before selecting Studio. Vendor
trial warnings are expected; no real license key or hosted acceptance was tested.

Environment: Debian 13 Linux, Python 3.12.14, Node 24.19.0/npm 11.9.0,
Chromium 154.0.8037.57, PostgreSQL 16 in local Docker. These are local synthetic,
sequential measurements, without production traffic, external provider, CPU/network
throttling or hosted services. Tests/builds ran in this shared cloud workspace.

The API benchmark compares one expense to **1,000 published expenses, ten completed
captures, 13 categories and 12 observed months**, with a bounded 50-row response.
Three measured full and three date-filtered requests follow the small baseline.
The filtered date interval has 249 matching expenses and three observed months.
SQLAlchemy statement counts include snapshot setup; they are not packet counts.
Owner scope is one project, so constant expense scaling does not establish constant
cost as owner project count increases. Existing services still materialize source
rows and repeat some summary queries; this is not a free-tier capacity claim.

| Local API workload | Median latency | Response bytes | SQLAlchemy statements |
| --- | --- | --- | --- |
| One published expense (one sample) | 51.774 ms | 20,341 | 48 |
| 1,000 published expenses, ten captures (three samples) | 66.976 ms | 32,957 | 48 |
| Same source, inclusive Apr–Jun expense-date filter (three samples) | 71.729 ms | 31,788 | 48 |

The benchmark regression requires statement count to remain independent of expense
row count. Optional PHASE6_PERFORMANCE_FILE records all samples in local JSON; no
request data, backer identity, real receipt or external telemetry is recorded.
Full-request samples ranged 62.625–68.907 ms; filtered samples ranged 70.720–450.786 ms.
The slower sample illustrates shared-host variation; no percentile/throughput claim
is made from three sequential requests.

Browser fixture represents 1,000 reports in two known category/month/evidence groups,
returning at most 50 rows; its mock server provides fixed authoritative aggregates.
It tests actual SDK rendering/filter behavior, not real API latency. Observed default
Community navigation-to-grid/chart was **1,747.96 ms** and filtered input/apply-to-chart
**339.38 ms**. In the separate Studio evaluation run, initial Community was
**1,792.00 ms**, filtered input/apply **374.68 ms**, and lazy Studio selection-to-populated
widgets **2,851.54 ms**. These single-run Vite-development measurements include module
fetch/initialization and 50 ms polling; they are not production load percentiles or
an animation-completion, accessibility or mobile-device hardware benchmark.

| Final production build artifact | JS KB | gzip KB |
| --- | --- | --- |
| Default lazy analytics shell | 7.10 | 2.73 |
| Default Community renderer (includes shared financial facts) | 2,556.34 | 738.41 |
| Default Studio unavailable stub | 0.11 | 0.11 |
| Optional evaluation Studio renderer | 5,273.70 | 1,468.33 |
| Optional build Community renderer | 2,550.84 | 737.13 |
| Optional build shared FinancialFacts | 5.59 | 1.80 |

The default build's root index is 301.89 KB / 88.59 KB gzip. Optional build shell
and shared chunks differ because both renderers reuse financial facts/adapters.
The main lockfile has no Studio or Grid/Charts Enterprise entries, and default dist
has only the unavailable stub rather than a Studio SDK renderer chunk. Large bundles
remain a performance concern; lazy loading prevents their cost on initial project
navigation but does not make analytics small. Peak RSS, low-memory device behavior,
production network budgets and hosted concurrency/latency remain unmeasured.

The first full backend attempt failed after the previously reused fixture database
exhausted Docker PostgreSQL's 64 MiB /dev/shm during migration fixture creation;
PostgreSQL logged a shared-memory resize failure and restarted. This was not counted
as a passing run. No retained schemas/data were deleted. A fresh disposable local
database completed **443 tests** before the final Unicode regression was added;
the final 444-test run includes that regression. Migration head remains 8c6072dabc59;
local upgrade/check reported no schema drift. Existing Starlette/HTTPX deprecation
remains. No production migrations or deployment were run.

## Reproduction and manual browser checks

Use only a fresh isolated local PostgreSQL database whose name begins opendev_test_.
The fixtures retain schemas, so repeatedly using the same database can accumulate
large catalogs. Do not clean production or retained data to make tests pass.

```sh
# backend/; after selecting a verified fresh local DATABASE_URL / TEST_DATABASE_URL:
APP_ENV=testing PHASE6_PERFORMANCE_FILE=/tmp/opendev-financial-api-performance.json python -m pytest -q
python -m alembic upgrade head
python -m alembic check
# frontend/:
npm test
npx tsc -b
npx tsc -p studio/tsconfig.json
npm run lint
npm run build
node tests/browser-analytics-smoke.mjs
TEST_STUDIO=1 node tests/browser-analytics-smoke.mjs
ANALYTICS_STUDIO_EVALUATION=true npm run build -- --outDir /tmp/opendev-studio-build
```

Keep evaluation output private/local. Community needs no optional installation;
optional SDK typecheck/build/browser commands require the separately installed
`studio/` dependencies described in the foundation guide.

Open an active synthetic project's analytics as a signed-out visitor. Compare all
cards/budget/coverage to transparency, attach multiple approved redactions, and
verify each expense counts once. Exercise category, start/end dates, evidence,
date order, reset, next/previous and empty results. Full-project KPI/coverage totals
must stay labeled and unchanged when only expense filters change. Inspect monthly
values against reported dates; sparse months must stay sparse. Follow a public
expense link, return to project, and test a draft/cross-project detail denial.
Simulate 503/offline and refresh recovery. Check keyboard controls, exact table
alternatives and 390px layout. With explicit loopback evaluation, switch to Studio:
preconfigured view-mode widgets must have values/charts without opening an editor,
and filters/mobile/switch-back must work. Inspect Network: Community must request
no optional Studio packages before selection. No private data should appear in JSON.

Financial limitations, exact partial refunds, independent payment verification,
licensing, historical credential review, hostile-file isolation, live Sandbox/private
storage, real Ollama, target-host capacity and cookie/proxy acceptance remain open.
**Deployment remains NO-GO.** No production migration, deployment, commit or push.
