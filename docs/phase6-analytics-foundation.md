# Phase 6 Step 1: public analytics foundation

**Deployment remains NO-GO.** This step adds read-only dataset contracts and an
embedded analytics shell, not detailed financial/development dashboards, historical
funding trends, a new agent or a private analytics product. No financial service,
record, schema/migration, paid subscription, deployment, commit or push was changed.

## Packages, official sources and licensing

The requested installation, compatibility and enterprise-licence pages at
`https://www.ag-grid.com/studio/react/` each returned HTTP 403 through this cloud's
network policy. They could not be read here. The official published npm metadata,
vendor README, shipped LICENSE.html and installed TypeScript declarations were
inspected instead. APIs were then checked by typechecking and actual Chromium
initialization, rather than assuming undocumented component props.

Verified installed versions:

| Location | Packages | Version / declared license |
| --- | --- | --- |
| Main frontend | ag-grid-community, ag-grid-react | **36.2.0**, MIT |
| Main frontend | ag-charts-community, ag-charts-react | **14.2.0**, MIT |
| Isolated frontend/studio | ag-studio-react, ag-studio | **3.0.0**, Commercial |
| Isolated Studio transitive dependencies | ag-grid-enterprise | **36.2.0**, Commercial |
| Isolated Studio transitive dependencies | ag-charts-enterprise | **14.2.0**, Commercial |

Studio 3.0.0 metadata requires Grid ~36.2.0 and Charts ~14.2.0; pinned installed
versions match. React 19.3.1 is supplied by the existing application, within the
package's React 17/18/19 peer range. The optional install omits peer copies and Vite
deduplicates React/ReactDOM, preserving one application React instance.

The original request both required Studio and prohibited Enterprise packages.
Actual Studio dependencies require both Enterprise packages above. The user explicitly
allowed **Studio-required Enterprise dependencies only in an isolated optional
installation**. They are therefore confined to `frontend/studio/package.json` and
its independent lockfile/node_modules, not the main package graph. The normal
`frontend/package-lock.json` has no Studio or Enterprise entries. Default bundles
also exclude the Studio implementation. Community is clearly labeled **not AG Studio**.

Vendor README describes Commercial licensing and links a free **45-day** Enterprise
trial. That does not establish permission for unrestricted public hackathon use.
No key was obtained, fabricated, committed or placed in a file. The local evaluation
browser run emitted the vendor's “License Key Not Found / unlocked for trial” banner
and watermark. This is evidence of local SDK initialization, **not** a deployment
license or a conclusion that public use is permitted. Obtain and review appropriate
rights separately before enabling a public licensed build. Existing project license,
PyMuPDF and other deployment gates are unchanged.

## Backend contracts and source formulas

One new efficient-consistency boundary:

`GET /api/projects/{id}/analytics/overview?limit=50&offset=0&scope=public`

Response model `AnalyticsOverview`, schema_version `1`:

| Dataset | Content / authoritative source |
| --- | --- |
| financial + funding_goal_cents | Existing anonymous AccountabilitySnapshot via transparency.overview, and public project's goal; gross captures, refund/reversal exclusions, net, spending and difference |
| budget | Existing category allocations, reported spending, remaining_cents and overspend_cents, without recalculating business formulas |
| expenses | Published expense ID/category/amount/currency/date, approved_public_support boolean and category-finding count; mapped from public ledger entries |
| development | Existing progress counts, paged credibility DeliveryRows (original/current deadlines and delivery assertions), retained GitHub counts, last sync and stale flag |
| maintainer | Current owner's public participation, delivery/reward indicators and per-project reporting coverage from existing credibility.profile |
| metadata | project_id, currency, as_of, public visibility, row totals/limits/offsets, source limitations |

All datasets are retrieved in one existing REPEATABLE READ / READ ONLY transaction.
`as_of` and financial calculated_at use the transaction timestamp. Repository sync
and original/current/asserted dates remain distinct; calculation time is not source
update or settlement. Missing GitHub counts are null, not invented zero activity.
Original deadlines and on-time/late rules remain owned by credibility services.

Integer minor units and existing conservative refund rules are preserved. Gross
captures include refund/reversal-affected original amounts. Net excludes those
captures in full, including partially refunded captures; exact refund totals stay
null. Funding minus reported spending is not bank balance. Published expense
support counts each expense once despite multiple documents/attempts. Public
category findings are not receipt-level accusations or payment verification.
Financial reporting remains per project/currency; no cross-currency owner total or
opaque trust score is introduced. Historical funding time-series are unavailable;
none is synthesized from contribution creation/expense dates.

The endpoint deliberately remains public-only even with owner/maintainer cookies.
Only active projects are eligible. Draft/paused/completed/missing projects return
404; scope=private/manager_private returns 422. Existing authenticated private APIs
and membership checks are unchanged; no private analytics endpoint is offered.
No raw receipts, document IDs/keys/filenames, OCR, review notes, backer/payment
identifiers, credentials or Supabase metadata are analytics fields. Public ledger
vendor/descriptions are also omitted from analytics row datasets.

Bounds: limit 1–100, offset 0–10,000; default 50 shared by expense/milestone pages.
The response is capped at 256 KiB. Owner scope above 20 active owned projects or
10,000 rows in each inspected expense/contribution/document/milestone/history
source scope returns 413. Expense and milestone row pages have independent totals;
financial/category totals and status counts are not silently truncated to a page.
No automatic all-page download or unbounded chart payload is added.

The adapter reuses authoritative services, rather than reimplementing aggregation.
Some existing services recalculate related summaries and materialize records; the
coherent endpoint is not a claim of optimal query count or target-host throughput.
Avoiding repeated source queries/batching can be evaluated later with explicit
performance evidence. Capacity limits do not replace process/ingress quotas or a
production DB pool/load test. Cache-Control/no-referrer/nosniff middleware applies.

## React shell and Community renderer

Active project details offer **Open project analytics**. The shell and each renderer
are lazy-loaded; initial project navigation does not fetch chart libraries. Public
analytics use the existing VITE_API_URL, same-origin/cookie handling and no-store.
The client rejects mismatched project/schema/visibility/currency and private-audience
envelopes. Unmount/project change aborts and ignores stale responses. Loading,
refresh, generic safe errors, paging, empty data and responsive navigation are present.

ProjectAnalyticsCommunity registers actual standalone Charts `AllCommunityModule`
and Grid `AllCommunityModule`. The similarly named Charts integrated module is not
the standalone API; installed declarations caught that difference during setup.
Only MIT features are used: bar comparison, category pie, sortable/filterable/read-only
grid, summary cards and exact textual category alternatives. No enterprise imports,
row grouping, pivoting, integrated charting or license bypass is used in this renderer.

Chart values use server-provided category allocation/spending; no frontend expense
aggregation or financial variance calculation exists. The expense category chart uses
the authoritative full published category totals, separate from the paged grid.
Amounts are labeled with currency/minor units and cards use existing safe BigInt
formatting. Unsafe JavaScript integers are not plotted; cards warn and the Studio
adapter rejects unsafe monetary datasets instead of silently rounding. Browser JSON
cannot preserve arbitrary-size integers as numbers; exact API integer inspection is
required for such data. No invented percentages or time points are displayed.

Grid text uses default safe rendering; charts have no custom HTML tooltips. React
text nodes render categories/limitations. Hostile category HTML was exercised in
Chromium and created no executable image/markup. Grid has a bounded-height local
scroll region on mobile; the overall page remains within a 390px viewport. Charts
also have accessible exact-value text alternatives. Full screen-reader and broader
browser certification remain separate acceptance work.

## Optional Studio integration and configuration

The shell's renderer selector supports community and studio, with Community default.
Normal builds resolve a tiny unavailable stub and contain no commercial SDK chunk.
A build-time alias selects the isolated implementation only when dependencies exist
and explicit evaluation/licensed configuration allows it. Type-only host adapter
contracts do not pretend to be SDK declarations: the actual optional renderer is
separately checked against installed `AgStudio`/`AgDataSourcesDefinition` types.

The official component receives documented `data={sources}` and `mode="edit"`, with
an explicit 650px parent height, width 100% and `studioId`. Edit mode here is a local
report workspace for this foundation: it can arrange reports in browser memory,
not modify OpenDev source records. No report/state persistence, backend save callback,
private fetch, custom calculated business rule or Studio AI harness is configured.
React/SDK lifecycle owns destruction; switching back to Community was exercised.
Detailed preconfigured Studio dashboards are reserved for later Phase 6 steps.

`studioData` provides explicitly allowlisted flat `sources: [{id, data}]` arrays:
financial, budget, expenses, development, maintainer_delivery, reward_fulfillment,
github_counts and reporting_coverage. Money stays in minor units; source times and
nullable missing values remain explicit. There are no relationships/implicit joins
or client-created history. Empty sources remain in the adapter contract but are
omitted at SDK initialization because an empty schema cannot be inferred; no fake
row is inserted. Backend schema, pages and limitations remain visible in the shell.

Renderer settings:

- `VITE_ANALYTICS_RENDERER=community` (default) or studio selects initial view.
- `ANALYTICS_STUDIO_EVALUATION=true` permits the optional SDK build; runtime mounting
  additionally requires localhost/127.0.0.1/[::1]. This is not public trial deployment.
- `ANALYTICS_STUDIO_LICENSED=true` **and** an operator-supplied
  `VITE_AG_STUDIO_LICENSE_KEY` enable a licensed optional build. The SDK's actual
  LicenseManager validates that key; flags alone confer no legal entitlement.
- Missing packages/configuration, nonlocal evaluation or absent licensing gives a
  clear unavailable message and a Return to Community button. Initialization/import
  exceptions have an error boundary with the same recovery path.

License keys used by browser SDKs are browser-visible configuration, not backend
credentials. Never commit them or confuse them with OpenDev agent/storage/payment
credentials. `.env`/`.env.*` are ignored under frontend; none was created here.
Evaluation builds still contain commercial asset bytes: do **not** publish them
merely because runtime mounting is gated. Licensed hosting requires rights review
and all existing NO-GO gates. No AG Studio AI config or OpenDev model key is supplied.

## Installation and manual verification

Default Community path from frontend/:

```sh
npm ci --include=dev
npm test
npx tsc -b
npm run build
npm run lint
node tests/browser-analytics-smoke.mjs
```

Optional user-authorized Studio installation, separate lockfile and dependencies:

```sh
# Run after the main frontend dependencies exist; omit duplicate React peers.
npm --prefix studio ci --omit=peer
npx tsc -p studio/tsconfig.json
TEST_STUDIO=1 node tests/browser-analytics-smoke.mjs
# Explicit local evaluation only; no publication:
ANALYTICS_STUDIO_EVALUATION=true npm run dev -- --host 127.0.0.1
# Or inspect a separate evaluation build without replacing the default dist:
ANALYTICS_STUDIO_EVALUATION=true npm run build -- --outDir /tmp/opendev-studio-build
```

Do not place that evaluation output on a public host. A licensed environment must
supply its reviewed configuration securely; no key example/value is included.

With a migrated isolated local opendev_test_* database, from backend/:

```sh
source /workspace/opendev-setup/local-env.sh
APP_ENV=testing python -m pytest -q
python -m alembic upgrade head
python -m alembic check
```

Open a synthetic active project as a signed-out visitor and choose Open project
analytics. Compare cards/category rows to the transparency API; approve multiple
redactions through existing controls and verify one expense amount in coverage.
Check refund notes, empty data, paging, stale GitHub, original deadlines, safe HTML,
keyboard/grid focus, refresh errors, 390px mobile and route changes. Compare owner
versus signed-out analytics: no private expansion. In a default build Studio must
be unavailable; in an explicit local evaluation build test Studio initialization,
its visible trial warning, report workspace and return to Community. Do not create
or publish real private documents for these tests.

## Verified results, bundles and limits

- **422 backend tests passed**, none failed/skipped: the 407 preceding plus 15 new
  analytics cases. Funding/refunds, budget, expense/evidence mapping, development/
  owner data, public/private/draft/cross-project boundaries, paging/size bounds and
  financial immutability are covered. No new migration; head stays `8c6072dabc59`.
- **62 frontend tests passed**, none failed/skipped: 55 preceding plus seven analytics
  cases. Main and optional Studio TypeScript checks passed; production builds,
  lint, compilation, whitespace and Alembic consistency passed.
- Chromium ran both default Community/unlicensed and explicitly enabled local
  Studio variants. Actual Community charts/grid and official Studio 3.0.0 initialized;
  renderer switching, empty/error recovery, hostile text, mobile and cleanup passed.
  Vendor trial watermark/license warning was expected, not suppressed. No key used.
- Verified default lockfile has no Studio/Enterprise package and default assets have
  no Studio renderer chunk; optional build has a separate Studio chunk. Standard
  Community build remains valid without installing the optional directory.

Observed default JS chunks: shell **4.77 KB / 2.04 KB gzip**, Community renderer
**2549.77 KB / 736.77 KB gzip**, unavailable stub **0.11 KB / 0.11 KB gzip**.
The optional evaluation Studio renderer was **5270.24 KB / 1467.11 KB gzip**;
Community remains separately lazy-loaded in that build. These are bundle sizes,
not peak browser memory or mobile load benchmarks. Both analytics and the existing
Gantt exceed Vite's 500KB warning threshold. Existing two AuthContext lint warnings
and Starlette/HTTPX deprecation remain. No hosted CI or production performance claim.

Next steps: build detailed financial/development dashboards on these contracts,
profile source-query/materialization costs, evaluate smaller Community module
registrations and low-memory chart/grid budgets, decide authorized Studio rights,
and test a real licensed configuration before public use. Private analytics, full
historical trends and report persistence require separate scoped work. Existing
PyMuPDF, credential-history, hostile-file isolation, live Sandbox/storage, hosting,
cookie/proxy, refund and beta-library gates remain open. **NO-GO remains.**
