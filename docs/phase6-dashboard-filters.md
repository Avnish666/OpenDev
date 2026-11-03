# Phase 6 Step 4: shared dashboard filters and predefined views

Deployment remains **NO-GO**. Community remains the default; Studio stays isolated,
optional, lazy and restricted to local evaluation or properly licensed use. No table,
migration, AI agent, paid service, persistent layout, source-record write, production
migration, deployment, commit or push is introduced.

## Files

Created `backend/app/schemas/dashboard_filters.py`,
`backend/tests/test_dashboard_filters.py`, `frontend/src/api/dashboardFilters.ts`
and this report.

Modified backend analytics router/schema/service and analytics_development service;
frontend analytics API, ProjectAnalytics shell, Community renderer, DevelopmentCommunity,
DevelopmentFacts, Studio renderer declaration and Studio renderer; App hash-route
parsing; analytics unit tests and Chromium harness. Existing financial/development
calculators, authorization, payment processing, roadmap history, packages and
lockfiles are preserved.

## Shared schema and widget scope

DashboardFilters combines existing category/date_from/date_to/evidence/sort with
strict server dimensions and local display choices. Applied and draft state are
separate. Apply dashboard filters commits changes, resets both independent page
offsets and cancels obsolete requests. Reset all filters restores defaults and
clears shared URL choices. Empty dates and all selectors clear individual conditions.
Controls stay accessible in every view, so retained cross-view filters remain visible.

| Dimension | Affected data/widgets | Fixed scope |
| --- | --- | --- |
| category, expense dates, public evidence | Expense grid, complete filtered category/month aggregates and reported subtotal | Project funding, budget and evidence-overview totals |
| discrepancy all/with/without | Same expense grid/aggregates, based on authoritative full-project category overrun | Private receipt findings remain unavailable; full public finding count unchanged |
| milestone_status | Current-project milestone counts, status chart, deadline/history page | Owner historical delivery metrics |
| planned_from/planned_to | Current revised milestone end/deadline date, inclusive; same filtered counts/page | Original immutable deadlines and owner historical scope |
| delivery all/delivered/undelivered | Current delivered status versus other states, including cancelled | Delivery remains a maintainer assertion |
| outcome | Existing timing values on_time, late, unknown, not_currently_delivered; filters current-project commitments | Never substitutes project history for owner-wide historical metrics |
| github_category | issue, pull_request, milestone, commit or all; only selected retained types appear | Repository sync metadata and snapshot limitations |
| github_freshness | Individual observation last_synced_at before or at/after calculation minus six hours; commit sample uses repository observation time | Overall sync stale flag remains separate, including failed attempts |
| participation all/owner/team | Displayed complete role counts and Studio role bars | Owner outcome/financial history remains owner-only; team results are not reassigned |
| reward all/fulfilled/pending | Displayed eligible fulfillment indicators and reward slices | Original eligible denominator, issued/excluded counts and privacy |

The controls distinguish expense dates, revised milestone deadlines and observation
age. No capture-date or comparable activity-window filter is invented. Overdue is
still derived from current deadlines and overlaps in-progress status. Reward slices
may display a subset; they do not recompute the authoritative fulfillment rate.
Owner history is intentionally not filtered to an invented owner-wide cohort: the
available contract exposes complete owner indicators rather than every owner record.

Applied choices and scope explanations are visible above the renderer. Filters do
not change source records or visibility. Unknown/missing original delivery dates
retain existing unknown timing; planned deadlines are required by the source model.

## API changes

The existing GET /api/projects/{id}/analytics/overview accepts the typed dimensions
above, and returns dashboard_filters describing server choices. Dates must parse as
calendar dates and start <= end; reversed/invalid values return 422. Literal enums
reject unsupported categories/states. Existing category length, limit 1–100,
expense offset/milestone_offset 0–10,000, response cap and source bounds remain.

Expense discrepancy selection intersects normalized category values from the
existing public budget variance, then passes the identical predicate into ledger
and grouped SQL expense queries. No OCR/reviewer finding becomes public. Funding,
conservative refund exclusions, budget variance and coverage calculations are reused.

Milestone predicates run over the already bounded authoritative derived history
before counts and stable ID-ascending pagination. Original deadlines/timing values
are not recalculated in React. GitHub filters operate on bounded project snapshot
queries before counts and ten-row previews; filtered issue/PR counts agree with the
selected retained scope. PR merged remains an overlapping closed subset. Commit
samples remain at most 30 observations. Filtered snapshot queries add a fixed number
of reads, not per-row SQL. Empty eligible scopes produce empty rows and zero filtered
counts; unavailable repositories preserve null counts and withhold source metadata.

Active-project authorization runs before data return, even with owner cookies.
Cross-project/private evidence/backer identities remain excluded. The whole response
still uses one existing REPEATABLE READ / READ ONLY snapshot and explicit as_of.
No new endpoint, source-write callback, financial formula or migration is needed.

## URL and lifecycle

Only declared enum choices and valid calendar dates are serialized into the hash
route query. Free-text category, arbitrary fields, secrets, credentials, amounts,
record IDs and private analytics are not serialized. Unknown enums/keys and invalid
calendar dates are ignored when parsing; reversed ranges reset to defaults. The App
matches its route before the query, so a copied project URL still opens that project.
URL parsing initializes a new analytics session; Apply/Reset use replaceState rather
than polluting back history. View preference/custom layouts are not persisted.

Filters survive view/renderer switching. Controls that do not affect a particular
widget are explicitly scoped; changing views never turns an expense filter into a
funding/owner-history filter. There is no incompatible private data scope to retain.
Unmount/project change aborts the request and resets project-keyed state. Rapid
server changes abort the older request and ignore late results. Local role/reward
selection uses complete bounded aggregates, a stable server-query key, and causes
no network request. Server filtering remains necessary for paginated expense and
milestone cohorts. Plain view/renderer switching also does not refetch.

## Community and predefined layouts

Financial Overview retains full financial KPI/coverage and budget context.
Spending & Evidence emphasizes expense charts/table and omits the overview KPI cards.
Development Progress retains filtered development cards/charts/history and evidence.
Maintainer Track Record shows owner metrics, roles, eligible rewards and per-project
reporting without presenting project milestone cards as owner history.

These are fixed presets, not a widget editor. Shared filter controls provide
category/date/status/clear interactions through native labeled inputs/selects/forms.
The supported read-only Grid now allows single-row selection and current-page
sorting, with server date ordering and stable global milestone ID order preserved.
Chart-to-filter gestures are not exposed; visible equivalent controls avoid a hidden
second filtering state and remain usable by keyboard. Responsive existing filter
layout wraps on mobile. Empty/loading/error and license-fallback states are retained.

## Studio capabilities and limitations

Installed 3.0.0 declarations were inspected for AgFiltersState.page/widget,
AgFilterState.field/model, logical/condition operators and AgReportState pages,
widgetLayout and initialState. Existing real data-source definitions, widget types,
formats and view-mode configuration remain checked by the separate installed-SDK
TypeScript build. No unsupported cross-filter API is invented.

Native page filters over paged expense rows or already aggregated funding sources
cannot safely reproduce server cohorts/financial subtotals. They are therefore not
exposed as a second authoritative filter state. The explicit equivalent external
controls apply shared server predicates first; Studio receives exactly the same
filtered authorized sources as Community. Complete local role/reward projections
also feed both renderers. This is a deliberate external-control integration, not a
claim of native click-to-crossfilter support.

The four presets select configured widgets from the existing official initialState
report, compact their widgetLayout row positions, and recreate the view-only instance
on view/source changes. Financial/spending use existing financial sources;
development/maintainer use existing development sources. Shared facts retain exact
scope/denominators and accessible alternatives. No unrestricted editing, AI panel,
local aggregate-based money rule, report save or backend write is enabled. React/SDK
lifecycle disposes replaced instances. Lazy module resolution, loopback-only
evaluation checks and appropriate licensed-key requirement remain unchanged.
Commercial trial warnings/watermarks are expected and not suppressed. Evaluation
output must not be publicly hosted. No subscription/key or public rights obtained.

## Verification and performance

**478 backend tests passed, 0 failed/skipped**, 285.33 seconds (12 new cases).
**81 frontend tests passed, 0 failed/skipped** (four new cases). Both TypeScript
configurations, Community production and isolated Studio evaluation builds passed.
Lint passed with only the two inherited AuthContext warnings. Migration upgrade and
check passed with no drift at unchanged head 8c6072dabc59. Compilation/whitespace
checks passed. Existing TestClient deprecation and large lazy bundle warnings remain.
The initial new discrepancy fixture failed because its supposedly non-overrun category
had no allocation and therefore correctly overran zero budget; adding the intended
fixture allocation fixed the test without changing the financial rules.

| Local API workload (three samples) | Median ms | SQL statements | Response bytes |
| --- | --- | --- | --- |
| 1,000 expenses, ten captures, unfiltered | 67.277 | 29 | 44,967 |
| Same source, inclusive Apr–Jun expense dates (249 matching) | 73.235 | 29 | 43,798 |

Full samples ranged 62.045–71.072 ms, filtered 68.207–76.030 ms. These retain the
Step 3 query-count bound; they are new local measurements, not a production
regression claim against earlier differently loaded runs. SQL count does not grow
per expense row. New GitHub observation filters add at most three fixed bounded
queries, not per-item reads. Monetary filters reuse SQL grouping and authoritative
category findings. A local selection triggers zero additional requests, verified in
Chromium. No paid cache was introduced.

| Browser measurement | Community build ms | Studio evaluation build ms |
| --- | --- | --- |
| Navigation to initial Community charts | 1,469.23 | 2,549.20 |
| Expense filter input/apply to charts | 346.43 | 316.97 |
| Community development view to charts | 271.47 | 212.27 |
| First lazy Studio selection to widgets | Not loaded | 2,935.37 |
| Studio development view to widgets | Not loaded | 1,378.65 |

Single-run Vite development observations include initialization and 50 ms polling;
no production/network-throttled percentiles, real mobile hardware, peak RSS or
formal assistive-technology benchmark is claimed. Both browser variants passed
populated charts/grids, all four presets, reset and malicious-text tests. Studio
also opened the compact spending and maintainer layouts without an editor. Rapid
filter-change acceptance delays the older response by 200 ms, applies a newer
cohort, then verifies the older result cannot replace the newer 34-record state.

| Final JS artifact | KB | gzip KB |
| --- | --- | --- |
| Default analytics shell and filter helpers | 12.30 | 4.25 |
| Default Community renderer | 2,568.11 | 741.44 |
| Optional Studio renderer | 5,278.01 | 1,469.58 |
| Optional build Community renderer | 2,554.37 | 738.04 |
| Optional shared facts/adapters | 13.88 | 4.04 |

Bundles remain large. The default build retains only StudioUnavailable, no Studio
SDK chunk, and the main lockfile has no Enterprise/Studio dependency. Presets and
filters do not load a commercial renderer until selection in an authorized build.
 The existing synthetic
API performance regressions cover 1,000 expenses/ten captures and a date-filtered
249-expense cohort; development workloads cover 100 commitments, 201 retained issues,
101 PRs and six owned projects. Browser fixtures cover 1,000 expenses, 102 commitments,
50-row pages, safe public evidence, and mocked failure/late responses. Local tests
use PostgreSQL 16, Python 3.12.14, Node 24.19.0, npm 11.9.0 and Chromium 154 on the
shared Debian cloud workspace, not production hardware/network.

Browser acceptance includes shared status filtering and counts, independent paging,
four presets, URL choices, reset, zero extra API requests for local selection,
rapid changes with an intentionally late response, mobile 390px containment, actual
populated Community/Studio charts/grids, license fallback, switching, and financial
regressions. Backend tests separately verify real SQL aggregate/row agreement and
immutable financial/history source behavior. Native controls/labels and Grid keyboard
support are exercised through the existing browser flow; this is not a screen-reader
certification or real mobile-device performance claim.

## Reproduction and next steps

Use a fresh local opendev_test_* database, with matching DATABASE_URL and
TEST_DATABASE_URL, and existing setup. From backend run APP_ENV=testing python -m
pytest -q, alembic upgrade head and alembic check. From frontend run npm test,
npx tsc -b, npx tsc -p studio/tsconfig.json, npm run lint, npm run build,
node tests/browser-analytics-smoke.mjs and TEST_STUDIO=1 node
tests/browser-analytics-smoke.mjs. Build optional evaluation separately using
ANALYTICS_STUDIO_EVALUATION=true npm run build -- --outDir /tmp/step4-studio-build.

Open an active project signed out, apply category/evidence/discrepancy/date choices,
compare filtered charts/grid/subtotals with the API and confirm funding stays fixed.
Switch all four views and both renderers; use milestone status/outcome/deadline and
GitHub category/freshness controls. Compare immutable original dates and owner totals.
Copy a safe filter URL and reopen analytics, clear controls, exercise empty sets,
rapid Apply, offline recovery, row selection, keyboard controls and mobile. Inspect
Network for no optional Studio load in Community and no local-selection refetch.

Recommended next work: server-backed chart selection only with explicit scope,
owner-wide cohort history only with a bounded authorized contract, formal assistive-
technology/slow-network/device acceptance, and target-host resource profiling. No
persistent layouts or invented historical cohorts are implied. Large bundles,
partial refunds, sampled/deleted GitHub data, self-reported delivery, private finding
publication limits and all inherited security/legal/service gates remain.
**Deployment remains NO-GO. No production migration, deployment, commit or push.**
