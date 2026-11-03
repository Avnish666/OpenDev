# Phase 6 Step 6: analytics release-readiness audit

Assessment: 2026-11-03, Asia/Calcutta. **NO-GO for public deployment; continued local
synthetic development is supported.** This is a scoped review and reproducible test
record, not a penetration-test or licensing certificate. No production data,
migration, deployment, paid service, new product feature, commit, push or merge was
used for Step 6.

## Repository, architecture and scope

Initial branch main, HEAD fb5d5fc (Phase 6 Step 5 done), clean working tree. Step 4
is e5ce99e. The request's assertion that Step 5 was uncommitted was superseded by
the user's later explicit commit/push instruction. All six CSV routes, shared React
controls and integration links were inspected and present; no missing implementation
was recreated. Earlier documentation is a historical snapshot, not the current git
state. Existing work was preserved; no reset/clean/discard ran.

Reviewed Phase 6 Steps 1–5 documentation, Phase 3–5 release reports, current
routers/services/schemas/models, filter projections, renderers, installed vendor
contracts/license metadata and regression infrastructure. The modular monolith
remains React/TypeScript/Vite -> FastAPI -> public authorization -> REPEATABLE READ /
READ ONLY SQLAlchemy/PostgreSQL snapshot. It reuses authoritative financial accounting,
immutable roadmap/credibility rules and retained GitHub snapshots. No new accounting
source, aggregate table, persistent report or analytics microservice exists.

Community uses MIT AG Charts/AG Grid. The optional Studio alias and dynamic import
resolve the isolated commercial implementation only in explicitly configured builds.
Both use the same public datasets, external filters and backend CSV routes.
Studio initialState/view mode, absent AI/editor configuration and React lifecycle
remain unchanged. Download controls sit outside the renderer.

## Files changed

Product fix: `frontend/src/api/dashboardFilters.ts`.
Regression coverage: modified `frontend/tests/analytics.test.mjs`; new
`backend/tests/test_analytics_release.py` and
`frontend/tests/browser-analytics-journey.mjs`.
Audit artifacts: this report and `docs/phase6-performance.json`.
No financial/payment/milestone service, model, migration, package or lockfile changed.

## Data integrity review

Full regression coverage and the new real-database journey verify captured completed
funding, pending/denied/uncaptured exclusions, original-amount refund/reversal
exclusions, published-only spending, normalized budgets, date filters and one expense
contribution despite multiple approved redactions/extraction records. Exact partial
refund amounts are unavailable; conservative full-capture exclusion and explicit
notes remain. Funding minus reported expenditure is not a verified bank balance.
No frontend/model financial aggregation or payment-processing change was introduced.

Milestone states remain exclusive; overdue/reopened/timing indicators overlap those
states. Original deadlines come from earliest immutable creation, including draft
preparation; current edits cannot improve original-baseline delivery timing. Matching
current asserted delivery dates determine on-time/late; missing/inconsistent dates
remain unknown. Reopened/cancelled commitments, owner versus team participation,
eligible reward denominators and Insufficient history/Unavailable semantics retain
the Phase 4 definitions. There is no composite trust score or independent-delivery
badge. Raw GitHub activity never changes delivery state.

Public project scope remains active-only, including owner-cookie requests. Owner
history uses current ownership and public active projects, so historical ownership,
archived/non-active work and first-publication deadlines are not reconstructed.
GitHub counts describe retained observations, commits are sampled, deleted records
may remain, and per-record age differs from overall sync success. No comparable
activity trend or funding history is fabricated. Financial, owner and filtered
project scopes remain explicitly distinguished.

## Confirmed defect and fixes

| Severity | Finding | Correction / evidence |
| --- | --- | --- |
| Low: validation/integration | URL calendar validation accepted 0000-01-01 and serialized it. Python/backend calendar dates reject year zero, so a copied filter URL could put valid public analytics into a 422 error state. | Require year >= 1 in the existing URL-date helper. A new frontend regression checks parsing and serialization for planned/expense year-zero dates. No accounting/date arithmetic changed. |
| Test harness corrections | The new real journey initially sent a keyboard activation before the financial view was stable, then reused a selector from a document being navigated away from. | Wait for the actual view and landing document; exercise native Space activation on the focused Apply button. Exact parsed CSV IDs/amounts are compared with the real filtered API. These were test synchronization errors, not additional product vulnerabilities. |

No critical/high authorization or financial-mutation exploit was confirmed by this
scoped review. That does not prove absence of undiscovered defects.

## Security findings and disposition

| Severity/status | Review result |
| --- | --- |
| High, inherited unresolved | Hostile-file decoder isolation and historical credential review remain open. No credential/history values were read or rotated, and no document sandbox claim is made. |
| Medium, existing operational risk | Source materialization, response caps, process-local export quota/slots and DB pool/resource behavior still require target-host ingress/concurrency testing. Bounded local tests are not a production DoS guarantee. |
| Medium, release licensing risk | Studio evaluation output contains commercial code even when mounting is runtime-gated. Public rights and inherited PyMuPDF obligations remain unresolved. |
| Low, fixed | Year-zero URL filter acceptance, above. |
| Compatibility limit | Spreadsheet formula tests operate after standards-compliant CSV parsing, not an Excel/LibreOffice execution engine. Downstream stripping/reinterpreting neutralization can reintroduce risk. |

Authorization precedes public projection; active status, project pins and owner-only
scope are server-enforced. Public cookies/frontend flags do not expand exports or
analytics. READ ONLY snapshots and source-before/after assertions protect accounting
and milestone state. Read endpoints require no CSRF token because they have no
financial/source-write side effects; existing authenticated write Origin checks are
unchanged and exercised by preceding suites. API no-store/no-referrer/nosniff headers
remain; CSV attachment filenames contain only validated integer ID/dataset literals.

SQL parameters stay bound, predicates share authoritative services and preflights
bound public source scope. Serialization allowlists exclude originals, OCR, review
notes, backer identity, payment identifiers, credentials and Supabase storage keys.
Published author text remains untrusted and deliberately public. React/Grid text and
validated GitHub link helpers avoid raw HTML/arbitrary navigation; malicious-label
browser checks pass. Browser downloads use fixed filenames, a size-checked CSV blob,
abort guards and revoked object URLs, not URLs supplied by source cells.

No production credential file, backend/.env.example value or historical secret was
read. Tracked file names/configuration and source identifiers are not evidence of
credential rotation. No hosted/private storage/OAuth/payment/model acceptance is
inferred from mocks.

## CSV validation

All six export datasets are present: expenses, financial, budget, roadmap, github,
maintainer-delivery. They use the same authorized filter semantics as dashboards,
complete bounded records rather than the visible page, deterministic ordering,
integer minor-unit columns, currency, as_of, scope and explicit record count.
Financial/budget stay full-project; owner delivery remains owner-active-project
history. Empty results carry metadata with exported_record_count=0.

Tests cover formula operators = + - @, leading whitespace/control/zero-width and
Unicode-normalized forms, commas/quotes/newlines/Unicode, malicious filename text,
private/draft/foreign records, source parity, row/byte/quota/deadline bounds and
full filtered rows. Numeric negative amounts remain numeric; text that could become
a formula is prefixed with an apostrophe after a normalized whitespace/control probe.
CSV quoting alone is not the defense. No spreadsheet office binary was available,
so native spreadsheet opening/formula execution was **not tested**. Test fixtures
and output files contain synthetic data only.

New audit cases hold both generation slots and verify a third request is rejected,
then induce a generation deadline and verify safe 503 plus slot recovery. Limits
remain 1,000 rows, 2 MiB CSV, two generation slots/worker, ten requests per peer/minute,
2,048 peer entries, a cooperative ten-second request budget and per-statement timeout.
Existing source/256 KiB coherent projection caps may reject earlier. Near-maximum
1,000-row actual expense exports were measured successfully; no truncated CSV is
returned on excess scope.

Browser cancellation prevents a late response from starting a download. It is not
proof the upstream synchronous worker or SQL operation stopped immediately; server
budgets remain the bound and real production proxy/disconnect behavior is open.
Driver pool acquisition/OS stalls are not hard process isolation.

## Studio licensing and dependency isolation

Installed ag-studio/ag-studio-react **3.0.0** and optional ag-grid-enterprise **36.2.0** /
ag-charts-enterprise **14.2.0** declare Commercial licenses. They remain nested in
frontend/studio's separate graph/lockfile. Default frontend lockfile has no Studio
or Enterprise entries; the normal build contains the unavailable stub, no Studio SDK
renderer chunk. Chromium confirms no optional package request before Studio selection.
Community builds without a key, and a UI selector alone cannot introduce a missing
commercial renderer into the default bundle.

Optional evaluation mounts only on loopback; a licensed build additionally requires
operator configuration/key and real SDK/license validation. Neither flags nor a
nonempty string establish legal rights. Studio properties/types confirm initialState,
view mode and supported configuration; public editing/AI/persistence are absent.
The real database journey switches Studio/Community repeatedly and verifies one
mounted instance, removal on switch and equivalent public facts. Trial warnings/
watermarks were visible and not suppressed. Evaluation assets must not be published.
No license key/evaluation credential was created or committed. Legal approval is
still required for Studio public use; no claim of trial production authorization.

Dependency compatibility: Python pip check and root npm ls pass. The online default
npm audit returned zero reported advisories at audit time. This is not an OS/Python/
commercial-graph vulnerability certification. Existing root legal/distribution review
and PyMuPDF AGPL obligations are unchanged.

## Community and real end-to-end browser testing

The new opt-in journey runs the actual React app, local Uvicorn/FastAPI and a migrated
disposable PostgreSQL schema. Only external GitHub is mocked. Signed-out authentication
uses the actual missing-session 401 path rather than treating None as an authenticated
User. Fixtures seed captures/refunds/reversals, two expenses, multiple redactions,
revised/delivered/in-progress/cancelled commitments, rewards and stored GitHub data.

Executed default Community and explicit local Studio variants: public project ->
Analytics -> all four presets; actual chart canvases/Grid rows; original/current
dates; native keyboard Apply; category filtering and chart/grid scope; complete CSV
file download; parsed CSV ID/category/amount agreement with real API; 6,000-cent net,
2,500-cent published reports and one supported expense despite multiple documents;
unpublished export 404; 390 px layout; repeated navigation. Studio variant additionally
runs three Community/Studio mount/unmount cycles with a single mounted root and
checks the same public 60.00 USD funding fact. This is a DOM/lifecycle check, not a
proof of leak-free long-session/native memory behavior.

The separate mock-API Chromium suites also pass rapid change/late response suppression,
empty/error/reset, safe URL parameters, local selections without refetch, pagination,
all presets, hostile labels, license-unavailable fallback, repeated switching, file
creation, fixed filename/UTF-8, disabled duplicate exports, Cancel and safe 429 errors.
Existing Bryntum/chat/profile interfaces remain intact; no Gantt scheduling or source
writes were added. Keyboard/native-label checks are not an assistive-technology audit.

## Performance and test results

**515 backend tests passed, 0 failed/skipped**, 289.94 seconds (508 preceding
plus seven audit cases). **86 frontend tests passed, 0 failed/skipped** (85 preceding
plus the year-zero regression). The full suite runs the real journey's HTTP/source
variant by default; additionally executed actual Community and Studio Chromium
variants each passed. Main and installed-SDK TypeScript, both builds, lint,
compilation/whitespace and local Alembic upgrade/check passed. Migration head remains
8c6072dabc59; no model/migration change. pip check and npm ls passed; npm's default
graph advisory audit reported zero. Existing TestClient deprecation, two AuthContext
lint warnings and large lazy analytics/Gantt chunks remain. Vendor trial warnings
were visible in local Studio runs. No warnings were suppressed.

Artifacts: [phase6-performance.json](phase6-performance.json) stores actual sample
arrays, SQL/payload/allocation counts and synthetic workload conditions. New row-count
scenarios have ten measured requests after a warmup, with tracemalloc enabled during
timing. Test-only peer quotas are cleared between benchmark requests; normal quota
behavior is tested separately rather than disabled in application code. Nearest-rank empirical p95 with ten values is the largest sample; these are
not statistically established production p95 estimates. The older owner-scaling
helper retains three samples and is labeled separately in the artifact.

Environment: Debian/Linux cloud workspace, Python 3.12.14, PostgreSQL 16 local Docker,
Node 24.19.0/npm 11.9.0, Chromium 154.0.8037.57. The small/medium/1,000-expense cases
use one active project, one normalized expense category/month, no capture or receipt
records. Financial correctness uses separate capture/refund/document cases. This
scope and tracing overhead differ from the previous ten-capture/13-category benchmark;
latency values are not an apples-to-apples production regression comparison.

| Scenario | Median ms | Empirical p95 ms | SQLAlchemy statements | Response bytes | Peak traced Python bytes |
| --- | --- | --- | --- | --- | --- |
| Analytics, 1 expense | 50.07 | 55.231 | 29 | 32,351 | 1,025,534 |
| Analytics, 100 expenses | 62.38 | 69.289 | 29 | 40,471 | 1,103,424 |
| Analytics, 200 expenses | 61.47 | 69.856 | 29 | 40,528 | 1,291,193 |
| Analytics, 1,000 expenses | 117.03 | 124.775 | 29 | 40,549 | 2,718,883 |
| CSV, 1 expense | 53.64 | 57.495 | 30 | 3,243 | 611,035 |
| CSV, 100 expenses | 85.27 | 87.175 | 30 | 16,504 | 1,005,542 |
| CSV, 200 expenses | 104.76 | 110.331 | 30 | 30,004 | 1,581,183 |
| CSV, 1,000 expenses | 361.06 | 787.596 | 30 | 139,005 | 6,339,782 |

Actual 1,000-row files were parsed and their record counts asserted in every sample.
Peak tracing is cumulative over the ten-request scenario, not incremental service
RSS, native/browser/DB memory or a worst-case long-text bound. Budget driver-level
set_config commands are not SQLAlchemy-counted statements; SQL numbers are not total
wire commands. Near-cap export variability is visible in the raw samples.

Large development (without tracemalloc in timing): **500 milestones + 500 immutable
creation records, 2,001 retained issues, 1,001 PRs**, one sampled commit, one project.
Ten requests: **71.571 ms median / 108.490 ms empirical p95, 45 statements, 66,579 bytes**.
Only 50 milestone rows and ten GitHub previews return, with full-scope counts. The
owner-scaling regression separately compares one versus six owned projects and
requires constant statement counts. No expense/milestone-count N+1 was detected.

The former 1,000-expense baseline was 29 statements/approximately 67 ms; the query
bound remains 29. The previous 200-row CSV was approximately 197 ms/30 statements/
1.9 MiB traced allocations; current traces show 30 statements, approximately 105 ms
median and 1.51 MiB peak over this different short-text sample. Differences in
workload, warmup, tracing/host load and sample sizes prevent a production speedup or
regression claim. No major newly confirmed SQL bottleneck justified changing business
rules; source materialization and transfer size remain the main scaling risks.

Mock-API Vite browser measurements include initialization and 50 ms polling and are
recorded in the earlier Phase 6 reports; current runs verify the same actual charts,
filters and downloads. The additional real-DB runs took about 7 seconds Community
and 13–15 seconds Studio for the complete journey, including startup/navigation/cleanup,
not just render latency. No production throughput or low-memory device claim.

| Final production JS artifact | KB | gzip KB |
| --- | --- | --- |
| Default analytics shell | 15.00 | 5.16 |
| Default Community renderer | 2,568.11 | 741.44 |
| Optional Studio renderer | 5,278.01 | 1,469.58 |
| Optional build Community renderer | 2,554.37 | 738.04 |
| Optional shared facts/adapters | 13.88 | 4.04 |

The tiny URL validation fix leaves large renderer chunks unchanged. Default dist
contains no Studio SDK renderer, only StudioUnavailable. No paid cache or speculative
optimization was added. Lazy loading defers substantial cost; it does not make these
bundles suitable for an unmeasured free-tier/mobile deployment.


## Release blocker register

| Item | Classification | Required evidence / rationale |
| --- | --- | --- |
| Year-zero URL validation | Resolved with evidence | New parsing/serialization regression passes; backend-supported year range aligned. |
| Public analytics/CSV local integration | Resolved with scoped evidence | Real PostgreSQL/Chromium journey, source parity/privacy and full regression suites; scope is local synthetic data. |
| PyMuPDF/MuPDF AGPL obligations | Unresolved blocker | Authorized distribution/compliance decision or reviewed replacement; no unilateral license conclusion/purchase. |
| Untrusted file processing/isolation | Unresolved blocker | OS/process isolation, hostile-file/concurrency/ingress and actual host acceptance. |
| Historical credential exposure review | Unresolved blocker | Owner evidence of rotation/revocation and incident review; no secret values accessed here. |
| Live PayPal Sandbox | Unresolved blocker | Real approval/capture/signature/refund/reversal reconciliation on authorized test accounts. No live payment performed. |
| Live Supabase | Unresolved blocker | Private bucket/redaction/signing/expiry/revocation/cleanup acceptance with synthetic files. |
| Live Ollama tool calling | Unresolved blocker | Real server/model/version/capacity and adversarial semantic acceptance; no model download/inference claim. |
| Render Free/Neon capacity | Unresolved blocker | Current quotas, RAM/CPU/pool/cold-start/load and large dashboard transfer behavior on the intended host. Local workstation/cloud timings do not resolve this. |
| Cross-domain cookies/proxy | Unresolved blocker | Production HTTPS Secure/SameSite/CORS/CSRF and disconnect forwarding. Local same-origin signed-out tests are insufficient. |
| Exact partial-refund accounting | Unresolved deployment blocker; local conservative limitation retained | Affected captures excluded in full; exact amounts/historic refund balance unavailable. Needs separately reviewed ledger work. |
| Bryntum beta dependency | Unresolved release risk | Pinned Community beta/local coverage does not establish long-session/device/broader-browser/host acceptance. |
| Studio public licensing | Unresolved blocker for public Studio | Appropriate rights/key/deployment review; isolated local trial initialization does not confer rights. Community does not need Studio, but other gates still block public release. |
| Sampled/retained GitHub, asserted delivery, current-owner history | Accepted limitation for local use | Explicit labels/unknowns/denominators retained; no full audit, verified delivery, authorship or lifetime score claimed. |
| CSV native spreadsheet compatibility | Accepted limited validation, open public acceptance work | Parsed-cell security tests pass; native spreadsheet and downstream import/re-save policies remain to verify. |
| Worker-local quotas/cancellation/resource caps | Accepted local-development limit, open production controls | Not distributed admission or hard worker/OS memory isolation; target-host ingress/proxy tests required. |

## Manual acceptance and Phase 7 handoff

Use a fresh isolated local opendev_test_* database; never substitute Neon/production
credentials. Reproduce full pytest, frontend tests, both TypeScript configurations,
Community and separate evaluation builds, lint, pip check, npm ls/audit and Alembic
upgrade/check. PHASE6_AUDIT_DIR writes synthetic benchmark JSON. To execute actual
browser variants, run PHASE6_BROWSER_JOURNEY=1 pytest tests/test_analytics_release.py
-k real_public, then the same with TEST_STUDIO=1 for permitted local evaluation.
Run both existing browser-analytics-smoke variants for mocked failures/adversarial UI.

Before any separately approved deployment, Phase 7 should:

1. Close or explicitly review every unresolved register item with owner evidence.
2. Exercise real OAuth/two-account HTTPS permission boundaries, hidden projects,
   cross-project exports, cache/proxy behavior and current public revocation.
3. Verify Sandbox capture/refund/reversal and approved private-storage workflows.
4. Test intended spreadsheet applications with synthetic hostile strings and preserve
   neutralization through downstream import policies.
5. Validate low-memory/mobile/slow-network budgets, pool saturation, concurrent export
   rejection/recovery, worker/distributed quotas and cancellation through the actual proxy.
6. Complete keyboard/screen-reader and broader browser/long-session Studio/Gantt cleanup
   acceptance; do not infer these from short Chromium DOM checks.
7. Rehearse approved test migration/backup/restore and review public assets/notices,
   production log redaction, license rights and rollback plans before requesting release.

**Recommendation: NO-GO for public deployment; GO for continued isolated development.**
No inherited blocker was marked resolved merely because analytics tests pass.
