# Phase 6 Step 3: development progress and maintainer analytics

Deployment remains **NO-GO**. This extends the existing public analytics endpoint,
Community renderer and isolated optional AG Studio 3.0.0 integration. It introduces
no new accounting/development tables, migration, payment operation, AI agent,
subscription, composite reputation score, production deployment, commit or push.
The uncommitted Phase 6 Step 2 implementation is preserved.

## Files created and modified in this step

Created:

- `backend/app/services/analytics_development.py`: bounded public development adapter.
- `backend/tests/test_analytics_development.py`: development, attribution, reward,
  privacy, read-only and representative performance regressions.
- `frontend/src/components/DevelopmentFacts.tsx`: common KPI/interpretation/exact-value
  tables, GitHub evidence links, owner history and reward/reporting metrics.
- `frontend/src/components/DevelopmentCommunity.tsx`: Community charts and history grid.
- `frontend/studio/developmentDashboard.ts`: installed-SDK preconfigured report state.
- `docs/phase6-development-analytics.md`: this report.

Modified:

- `backend/app/routers/analytics.py`, `schemas/analytics.py`, `services/analytics.py`:
  independent milestone paging and shared development/GitHub/reward datasets.
- `backend/app/services/accountability.py`, `services/transparency.py`: optional
  request-local batched public inputs to the existing financial calculator.
- `backend/app/services/credibility.py`, `schemas/credibility.py`: immutable revision
  counts, explicit eligible/revoked/refunded/reversed reward indicators, reusable
  derived history, batched public reporting metadata and financial inputs.
- `backend/tests/test_analytics.py`: response-cap test accepts internal batching
  kwargs; existing financial performance/parity checks still run unchanged.
- `frontend/src/api/analytics.ts`: typed development contracts, explicit public
  Studio projections, exclusive-state and eligible-reward presentation adapters.
- `frontend/src/components/ProjectAnalytics.tsx`, `ProjectAnalyticsCommunity.tsx`,
  `ProjectAnalytics.css`, `src/studio-renderer.d.ts`: dashboard selection,
  independent history paging and renderer props/styles.
- `frontend/studio/ProjectAnalyticsStudioRenderer.tsx`: selects financial or development
  preconfigured report in view mode; financial dashboard remains available.
- `frontend/src/App.tsx`, `components/ProjectProgress.tsx`: roadmap deep link opens the
  existing project/Bryntum section. No Gantt scheduling or source-write code changed.
- `frontend/tests/analytics-fixture.mjs`, `analytics.test.mjs`,
  `browser-analytics-smoke.mjs`: development fixtures, adapter/renderer/SDK and Chromium
  acceptance alongside financial regressions.
- `docs/phase6-analytics-foundation.md`, `phase6-financial-analytics.md`: follow-on links.

No dependency, lockfile, database model or migration changed. FinancialFacts and
financialDashboard were created in the preceding uncommitted Step 2, not this step.

## Reused APIs and contract additions

The existing `GET /api/projects/{id}/analytics/overview` remains the single analytics
response, schema_version `1`, with active-project authorization and one REPEATABLE
READ / READ ONLY transaction. Owners receive the same public data as visitors.
There is no unnecessary second project/maintainer analytics endpoint.

New query parameter `milestone_offset`: default 0, bounds 0–10,000. It is independent
of expense `offset` and filters. Existing `limit` (default 50, bounds 1–100) controls
page size. Milestones sort by ID ascending; offsets beyond total return an empty
page without changing full-scope counts. Expense ordering/filtering and finance stay
unchanged. Current public owner scope remains bounded to 20 active owned projects;
checked source scopes remain at most 10,000 records, with a 256 KiB response cap.
Available issue/PR/GitHub-milestone snapshot scopes above 10,000 records return 413.
These bounds reject excess scope rather than silently publish partial KPI totals.

The existing `development` object now contains:

- Full project `counts` from `progress.counts`, which uses `credibility.delivery_rows`.
- Bounded `milestones` extending the existing public DeliveryRow: `revision_count`,
  `deadline_revision_count`, `overdue`, `deadline_shift_days`, `delivery_delay_days`.
- `total`, `limit`, `offset`; counts stay independent of the page and expense filters.
- `github`: availability, safe repository name, retained snapshot counts, sanitized
  sync status, observation time, snapshot age, up to ten issue/PR/milestone records,
  at most 30 sampled commits, `exhaustive=false`, and explicit limitations.
- Previous `github_counts`, `last_successful_sync_at`, `github_stale` stay compatible.

`maintainer` retains participation, owned-project delivery/reward indicators and
per-project public financial reporting metrics. New `project_rewards` separates this
project's obligations from the owner's other active projects. Public Indicator
contracts retain numerator, denominator, sample_size, state, formula, timestamps and
limitations. No individual entitlement/contribution/backer record or private note
is projected. Source APIs remain existing roadmap/history, GitHub activity,
transparency/ledger and `/api/maintainers/{id}/credibility`.

Non-active projects return 404, even for owners; private scope is rejected.
Cross-project snapshots/milestones and other owners' outcomes cannot enter the
request project/owner projection. Current ownership/visibility defines scope, so it
is not a complete lifetime or historical-ownership archive.

## Metric definitions

| Metric | Definition / limitation |
| --- | --- |
| Published roadmap milestones | All distinct milestone IDs on this active project. No separate milestone publication flag exists. |
| Exclusive status distribution | Planned, in progress, submitted for review, delivered (maintainer asserted), cancelled. These alone sum to total. |
| Overdue unfinished | Existing Phase 4 rule: planned/in-progress/submitted current deadlines before today UTC; due today, delivered and cancelled are excluded. This overlaps state counts. |
| Asserted delivered | Currently delivered status; GitHub issue closure/PR merge never sets it. |
| Reopened | Distinct commitments ever transitioned from delivered to another status in immutable history. It can overlap a current state. |
| On-time / late | Latest matching current delivery assertion compared to earliest immutable creation deadline, including draft preparation. Unknown original/matching dates remain unknown. |
| Timing denominator | Only current deliveries with known comparable original and actual dates. UI shows on_time / (on_time + late); no completion percentage. |
| Original / revised / actual | Exact calendar dates retained separately. Current deadline revisions never replace the original on-time baseline. Actual means maintainer assertion, not independently verified release. |
| Recorded revisions | Immutable events after creation, including status/evidence/order/text changes. Not just edits to dates. |
| Deadline revisions | Immutable edits changing a previously known planned end date. Missing historical baselines are not fabricated. |
| Deadline shift / delivery delay | Backend integer calendar-day difference from original deadline; null if original/actual comparison unavailable. Negative means earlier; zero is a real same-day comparison. |
| GitHub counts | Retained synchronized issue open/closed, PR open/closed/merged and GitHub milestone open/closed counts. Merged is an overlapping subset of closed PRs, not another exclusive status. |
| Last successful sync | Stored successful run timestamp, distinct from latest attempt, individual observation and calculation time. |
| Owner outcomes | Current owner's active public projects only. Maintainer/collaborator project participation is shown separately; team results are not attributed to every participant. |
| Eligible entitlements | Completed captured contributions in project currency, entitlement granted/fulfilled, unique entitlement/contribution relation. |
| Fulfillment | Eligible fulfilled / all eligible granted-or-fulfilled entitlements. Pending uses the same denominator. Zero denominator means Insufficient history. |
| Issued / excluded | Issued counts all persisted entitlement IDs; excluded = issued minus currently eligible, including refund/reversal/revocation/invalid states. |
| Refunded / reversed / revoked | Explicit supported excluded subsets; revoked may overlap refund/reversal, so these are not added into a pie or another total. Exact partial-refund financial limitation remains. |
| Overdue rewards | Unavailable: there is no fulfillment deadline. Fulfillment is a maintainer mark; source status-change timestamps are also unknown. |
| Financial reporting coverage | Existing per-owned-project public reporting indicators and document-supported expense amounts; no cross-currency aggregation or new financial formulas. Documents do not prove payment. |

Empty/new history is explicitly Insufficient history; unsupported independent review
and overdue rewards are Unavailable. A count of zero published commitments is a
source count, not a zero reputation score. Historical asserted delivery is distinct
from current delivery, including reopened/cancelled commitments. Unknown timing is
never silently counted as on time. Calendar strings are rendered as strings and
backend day arithmetic uses date objects; no browser timezone conversion is applied.

## GitHub snapshot integrity and freshness

The adapter uses stored observations only; viewing analytics never synchronizes or
calls GitHub. Issues already exclude Issues-API PR entries; merged_at determines PR
merge status. GitHub milestones are separate from OpenDev commitments. Charts group
current retained statuses, not dates from incomparable partial sync windows.

Initial imports are bounded. Deleted items can remain retained after a later sync;
empty incremental collections do not erase those observations. Commits are only the
recent default-branch sample, with SHA/date/source links, not complete history or
personal productivity. No repository lifetime total, certified delivery, abandonment
judgment or activity trend is inferred. Up to ten item previews and 30 commits are
explicitly labeled samples, independent of full retained status counts.

Failed sync preserves old observations and last success, with stale=true and the
separate failed attempt shown. Missing/private/identity-mismatched repository data
has null counts/name and empty source lists, rather than invented zero activity.
Sync attempts exclude run counters. Visibility is only checked during sync; a new
private transition between syncs cannot be detected by a database-only read.
Per-record observations may be old even after a recent incremental sync.

GitHub links reuse the existing validated githubSource helper. Source titles remain
plain escaped text. No raw commit messages, provider HTML, backer identities,
private projects, OCR, originals, signed storage URLs or reviewer notes are added.

## Community configuration

The existing selector offers Financial analytics and Development analytics. Both
use one authorized response, the same Community package registrations and the same
license gates. Financial cards/charts, filters and expense grid remain functional.

Development uses AG Charts Community bar/pie series and AG Grid Community only:

- KPI cards for total/current delivery/in-progress/overdue/cancelled/reopened/timing.
- Bar distribution of five exclusive current roadmap states.
- Original-deadline comparison bars for server-calculated revised shift and asserted
  delivery delay on the current page. Unique ID/title labels avoid merging duplicate
  milestone titles. Missing comparisons are omitted; exact dates remain in tables.
- Retained GitHub status bars, clearly marking the overlapping merged PR subset.
- Eligible project reward fulfilled/pending pie, omitted without eligible observations.
- Read-only sortable history grid and exact semantic table with original/current/
  actual dates, timing, overdue/reopened indicators and revision counts.
- Safe GitHub issue/PR/milestone/commit links, snapshot freshness, owner/team separation,
  per-indicator sample sizes/formulas, per-project reporting coverage and profile links.

Global history order is stable ID ascending; grid header sorting is current-page
sorting. Previous/Next milestone buttons use milestone_offset, separately from
expenses. Loading/error/retry and license-unavailable recovery stay in the shared
shell. Labels, exact text tables, non-color indicators, flexible chart regions and
contained grid scrolling support keyboard/mobile use. Formal screen-reader and
broader-device acceptance are still separate work.

`#/projects/{id}/roadmap` opens/focuses the existing ProjectProgress roadmap section,
where the existing Bryntum Community list/timeline switch lives. No second Gantt,
automatic scheduling, deadline save or status write is introduced.

## Official optional Studio configuration

The installed 3.0.0 `AgReportState`, page widgets/widgetLayout, `AgWidgetState`, field
formats/references and initialState contracts are reused exactly as in Step 2.
Both Studio TypeScript compilation and real Chromium populated widgets verify the
installed package APIs. Official vendor declarations/README are the reference;
web documentation access was already denied by environment policy in Steps 1–2,
and no successful current web-document retrieval is claimed here.

`developmentDashboard` supplies a real selected Development report page with:

- Three Value KPIs: total, maintainer-asserted delivered, overdue unfinished.
- Grouped-bar roadmap state distribution and deadline comparison.
- Milestone history Grid with original/current/asserted dates and revision fields.
- Retained GitHub status bar and recent sampled commit Grid when available.
- Owner delivery metric Grid with explicit denominators/sample sizes/states.
- Owner versus team-participation bar.
- Eligible reward pie and project reward metrics Grid.

Shared DevelopmentFacts exposes all other required KPI, freshness, owner reward and
financial reporting details and accessible alternatives. The selected view controls
which preconfigured report is mounted; financialDashboard remains available.
Empty unsupported sources/widgets are omitted rather than populated with dummy
history. Studio status/chart measures use first on unique backend groups; commitment
labels include unique milestone IDs. No joins, expression-based accounting or
paged-row sums compute business facts. Numeric/null schema is explicitly typed so
missing timing is not inferred as text/zero. All flat data sources are allowlisted;
extra source properties/private notes do not pass through the adapter.

Studio is explicitly mode=view, with no edit/data/AI panels, AI harness, persistence
or source-write callbacks. It remains lazy-loaded, isolated and loopback-evaluation
or appropriately licensed only. Community imports no Enterprise module and the
main lockfile remains free of Studio/Enterprise dependencies. Trial watermark/key
warnings were visible and were not suppressed. No key, subscription or unrestricted
public Studio rights were obtained. Evaluation asset output must remain local.

## Query optimization and measurements

Before changes, the same synthetic 1,000-expense/ten-capture request was measured
again: three full requests had median 80.121 ms, 48 SQL statements and 32,957 bytes;
three Apr–Jun filtered requests had median 80.217 ms, 48 statements and 31,788 bytes.
This remeasurement is separate from Step 2's earlier approximately 67 ms result;
shared-host timing varies. Samples were captured before changing the calculator.

The adapter previously called progress.summary, a financial snapshot inside that
summary, another snapshot inside owner credibility, and repeated milestone history.
The revised adapter batches public contribution/published-expense/allocation/support
inputs once, calls the same authoritative calculator with those request-local inputs,
reuses derived owner history, and batches reporting/approval metadata. It directly
reuses progress.counts rather than retrieving an unused progress-summary payload.
The analytics profile skips unrelated per-owner GitHub profile work; current-project
GitHub is separately bounded and reused. There is no cache table/service, source
rewrite, altered refund arithmetic or persistent aggregate. Private analysis retains
its original authorization and uncached behavior. A parity regression compares
batched and ordinary financial snapshots within the same read transaction.

Final validation: **466 backend tests passed, 0 failed/skipped**, 250.62 seconds
(444 preceding plus 22 development cases). **77 frontend tests passed, 0 failed/skipped**
(69 preceding plus eight development cases). Both TypeScript configurations, main
Community and separate Studio evaluation builds, lint, Python compilation and
whitespace checks passed. Local migration upgrade/check passed with no drift at
unchanged head **8c6072dabc59**. Only the existing Starlette/HTTPX deprecation,
two AuthContext lint warnings and large analytics/Gantt bundle warnings remain.

The resumed local PostgreSQL container was initially stopped; one migration attempt
returned connection refused/starting up before any tests ran. Existing container
recovery completed and a fresh disposable test database was created. The passing
full-suite result above is the subsequent run. No retained schemas or production
data were deleted, and no production migration was attempted.

Measurements are local synthetic tests on Debian 13, Python 3.12.14, PostgreSQL 16
Docker, Node 24.19.0/npm 11.9.0, Chromium 154.0.8037.57, a shared cloud workspace.
Request timings include local TestClient routing/query/serialization/validation,
without real GitHub, paid services or production network traffic. SQLAlchemy counts
include snapshot setup and exclude driver BEGIN/COMMIT; no production throughput,
percentile, worker-memory or target-host capacity claim follows from these samples.

| Full analytics request | Median ms | SQL statements | Response bytes |
| --- | --- | --- | --- |
| Before: 1,000 expenses / ten completed captures | 80.121 | 48 | 32,957 |
| After: same expense/capture scope, expanded development contract | 41.630 | 29 | 44,780 |
| Before: same source, inclusive Apr–Jun expense-date filter (249 matching) | 80.217 | 48 | 31,788 |
| After: same filtered source and expanded contract | 49.325 | 29 | 43,611 |

Three samples each. Final full-request range 37.549–47.308 ms; final filtered range
42.290–50.730 ms. The earlier focused post-change run had approximately 38 ms median;
final-run figures above supersede it. Data values/formulas retain parity while payload
grows with explicit reward/freshness/limitation fields. Removing 19 statements is a
measured structural improvement, not a guarantee of the same timing on other hosts.
A one-expense baseline also uses 29 statements, confirming no expense-count N+1.

| Development scope (one warmup + three measured requests) | Median ms | SQL statements | Response bytes |
| --- | --- | --- | --- |
| One commitment, initial retained issue/PR snapshots | 30.06 | 45 | 34,120 |
| 100 commitments, 201 issues, 101 PRs, one sampled commit | 31.95 | 45 | 66,061 |
| Same development records, six owned active projects | 33.70 | 45 | 77,926 |

The representative fixture revises commitments to supply immutable history and
retains earlier GitHub snapshots across incremental sync; 201/101 include those
retained observations. KPI counts cover all 100 milestones while only 50 history
rows are returned. Query-count regressions require equal statement counts as source
rows and owned project count increase. No new per-row/per-owned-project query loop
exists in this analytics path. The separate preexisting public credibility endpoint
still includes its own per-owner GitHub section; it is not claimed to have constant
cost across unlimited ownership. Source/history materialization, response size and
bounds remain real scaling limits despite fewer round trips.

Optional PHASE6_PERFORMANCE_FILE / PHASE6_DEVELOPMENT_PERFORMANCE_FILE write synthetic
local JSON samples for reproduction. They do not record private user/backer inputs
or send telemetry. The implementation adds no persistent cache or paid service.

Chromium passed default Community/unlicensed and explicitly enabled local Studio
variants with financial regressions included. The mock server represents 1,000
expenses plus 102 roadmap commitments, returning 50-row independent pages and known
aggregate counts. Checks verify actual canvases/grids, numeric and non-empty Studio
charts, dashboard/renderer switching, late versus revised dates, stale metadata,
2 / 3 eligible reward ratio, milestone offset=50, unchanged financial filtering,
390 px layout, hostile-label escaping, loading/error/retry, license fallback and
clean teardown. No optional SDK source/package request occurs in Community before
Studio selection. Existing public expense links still open through the signed-out
actual App route. Backend tests separately validate real SQL/schema/privacy/source
immutability; the browser mock is not a live GitHub/backer/authentication benchmark.

| Browser observation | Default build ms | Studio evaluation build ms |
| --- | --- | --- |
| Initial navigation to Community grid/charts | 2,236.30 | 3,208.64 |
| Financial filtering input/apply to charts | 367.33 | 275.40 |
| Community Development selection to charts | 285.81 | 282.96 |
| First lazy Studio selection to financial widgets | Not loaded | 3,403.16 |
| Loaded Studio Development selection to widgets | Not loaded | 1,523.43 |

Single-run Vite development observations with 50 ms polling; initialization,
optimization/cache state and shared-host load differ. These are not production
benchmarks, exact animation-completion measurements or real mobile hardware tests.

| Production JS chunk | KB | gzip KB | Change from Step 2 gzip KB |
| --- | --- | --- | --- |
| Default analytics shell | 8.62 | 3.13 | +0.40 |
| Default Community renderer including financial/development | 2,567.57 | 741.30 | +2.89 |
| Optional Studio renderer | 5,277.46 | 1,469.38 | +1.05 |
| Optional build Community renderer | 2,554.08 | 737.93 | +0.80 |
| Optional shared facts/adapters chunk (emitted FinancialFacts name) | 13.63 | 3.99 | +2.19 |

Root index is 302.21 KB / 88.65 KB gzip; existing lazy Gantt remains approximately
1,946.81 KB / 604.00 KB gzip. Shared chunk boundaries differ across builds, so Studio
SDK chunk deltas alone are not total route cost. Both analytics bundles remain large.
The default lockfile contains no Studio/Enterprise entry; default output contains
only the tiny unavailable stub, no Studio SDK renderer chunk. Studio stays isolated
and opt-in. No claim of low-memory device, browser-RSS or hosted-network acceptance.

## Browser verification and reproduction

From backend/, use a fresh verified local opendev_test_* database and set DATABASE_URL
and TEST_DATABASE_URL to it. Retain fixture data; do not delete production/test data
merely to make checks pass.

```sh
APP_ENV=testing PHASE6_PERFORMANCE_FILE=/tmp/financial.json PHASE6_DEVELOPMENT_PERFORMANCE_FILE=/tmp/development.json python -m pytest -q
python -m alembic upgrade head
python -m alembic check
```

From frontend/ with the main and separately installed optional Studio dependencies:

```sh
npm test
npx tsc -b
npx tsc -p studio/tsconfig.json
npm run lint
npm run build
node tests/browser-analytics-smoke.mjs
TEST_STUDIO=1 node tests/browser-analytics-smoke.mjs
ANALYTICS_STUDIO_EVALUATION=true npm run build -- --outDir /tmp/opendev-step3-studio-build
```

As a signed-out visitor open an active project's analytics, select Development,
and compare counts to roadmap/progress-summary, original/current dates to immutable
history, GitHub counts to retained activity, and reward fractions to public credibility.
Revise an original-late deadline, reopen/cancel a commitment and verify timing/counts
remain properly separated. Exercise milestone pages while financial filters are
active; counts and expense offset must not move together. Follow the existing
roadmap/profile/GitHub links. Test unknown original dates, no history/rewards,
missing/private/stale GitHub and failed API recovery. On localhost with explicit
Studio evaluation, repeat in view mode and ensure widgets start populated, switch
back to financial/Community, and check 390 px layout and escaped hostile labels.
No optional SDK request should occur before selecting Studio. Do not publish the
evaluation build or use real private backers/documents as fixtures.

Delivery remains self-reported; original first-publication dates, historical
ownership, exact partial refunds, reward deadlines, complete GitHub audit/trends,
independent delivery/payment certification and real target-host capacity are not
available. Existing legal/licensing, credential-history, hostile-file isolation,
live Sandbox/private storage, real-model and hosting/cookie/proxy gates remain open.
**Deployment remains NO-GO. No production migration, deployment, commit or push.**
