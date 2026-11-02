# Phase 4 Step 5: public project progress dashboard

Deployment remains **NO-GO**. No Phase 5 agent, AG Studio, paid component, new table,
migration, deployment, commit or push is introduced by this step. Existing pending
Steps 3–4 changes are preserved. Payment processing and reward/expense write logic
are unchanged.

## Files and component integration

Created:

- `backend/app/schemas/progress.py`: explicit public summary contract.
- `backend/app/services/progress.py`: coherent project summary and bounded previews.
- `backend/app/routers/progress.py`: public GET-only route.
- `backend/tests/test_progress.py`: aggregation, privacy, freshness and query-budget tests.
- `frontend/src/api/progress.ts`: typed response, safe GitHub links and timing label.
- `frontend/src/components/ProjectProgress.tsx`: unified dashboard.
- `frontend/tests/progress-fixture.mjs`: synthetic frontend/browser fixture.
- `docs/phase4-progress-dashboard.md`: this guide.

Modified:

- `backend/app/main.py`: register the summary route.
- `backend/app/services/credibility.py`: batch history/repository loads for delivery
  projections while preserving the existing original-deadline rules.
- `backend/app/services/roadmap.py`: extract reusable public history projection;
  existing manager/private history behavior is preserved.
- `backend/app/services/github_progress.py`, `backend/app/routers/github_progress.py`:
  extract/reuse the existing activity projection, preserving its response contract.
- `backend/app/services/accountability.py`: batch approved-public-document coverage
  for public snapshots. Private analysis and all financial formulas remain unchanged.
- `frontend/src/pages/Projects.tsx`: active projects mount the unified Progress section;
  non-active maintainer management views retain their existing roadmap/GitHub controls.
- `frontend/tests/transparency.test.mjs`: summary rendering and safe-source tests.
- `frontend/tests/browser-gantt-smoke.mjs`: run actual Community interactions inside
  the unified dashboard and test mobile sizing/list switching.

ProjectProgress contains exactly one existing Roadmap component, preserving the list,
management/history controls and lazy-loaded Bryntum view. It does not initialize a
second chart. Overview, roadmap, GitHub and delivery-history navigation uses keyboard-
accessible buttons and focusable sections, avoiding conflict with the app's hash
router. Maintainer GitHub controls reuse GitHubProgress on demand. The detailed
Transparency component mounts only when the user opens the ledger: no duplicated
expense tables. Funding/expense/fulfillment management outside Progress is retained.

## Public API

**GET `/api/projects/{id}/progress-summary`**

No authentication required; even owner cookies do not broaden the projection.
Only active projects are eligible. Draft/paused/completed/nonexistent projects return
404; invalid path IDs return 422. Writes return 405. Responses inherit no-store,
no-referrer and nosniff headers. No API token or storage/provider request is involved.

One dedicated PostgreSQL REPEATABLE READ / READ ONLY transaction covers all summary
fields:

- project_id and the project's stable github_repository_id;
- calculated_at and internal roadmap_updated_at;
- counts for each roadmap state, overdue unfinished, distinct reopened milestones,
  original-deadline on-time/late assertions and delivered-unknown timing;
- unique active linked issue and merged-PR counts, nullable when source unavailable;
- github_available and linked_evidence_stale (nullable when no available links to assess);
- sync: last successful time, stale flag and a safe latest-attempt projection with
  started_at/completed_at/status/error_code. Private/retained run counters are omitted;
- snapshot_age_seconds measured at calculation, never a live timer;
- existing activity projection with up to ten issues/PRs, current stored metadata,
  counts and the existing recent default-branch commit sample; null if unavailable;
- up to ten synchronized GitHub milestones;
- ten recently updated delivery-history preview rows with original/current deadlines,
  current delivery assertion, timing and reopened flags;
- ten recent roadmap change events projected with the existing **public** history
  allowlist, preserving public reasons without frozen/private source JSON;
- a small owner-only public delivery summary, identity, sample size and profile link;
- concise financial summary from the existing public transparency/accountability
  service, plus relevant public source API paths and limitations.

Reused APIs/components retain their contracts: roadmap/list/history/dependencies,
GitHub sync/activity/milestones/status, maintainer profile, and financial transparency/
ledger. The new endpoint is necessary to give overview cards one consistent snapshot;
child pages and refreshes still have separate calculation times.

## Metric definitions

No completion percentage, trust score, arbitrary weight or AI inference.

| Indicator | Formula / interpretation |
| --- | --- |
| Published commitments | All roadmap milestone IDs on this active project, once each. There is no per-milestone publication flag; project visibility controls publication. |
| State counts | Count authoritative current status: planned, in_progress, submitted_for_review, delivered, cancelled. Delivered is a maintainer assertion. |
| Overdue unfinished | Current planned/in_progress/submitted_for_review rows with current end date before today's UTC date. Due today, cancelled and delivered are excluded. |
| Reopened | Distinct milestones whose immutable history ever changes delivered to another status; repeat reopenings do not inflate it. |
| On-time / late | Reuse credibility's immutable creation deadline and latest matching current delivery assertion. Actual <= original is on time; actual > original is late. Missing/inconsistent history stays unknown. |
| Timing fraction | on_time / (on_time + late), explicitly dated delivery assertions only. A zero denominator shows Insufficient history. Unknown timing is displayed separately, never silently counted as on time. |
| Linked issues | Distinct canonical issue IDs in non-removed project evidence links, not number of links across milestones and not Issues-API PR entries. |
| Linked merged PRs | Distinct linked PR canonical IDs with a non-null synchronized merged_at. Closed alone does not count merged. |
| Owner history | Same deterministic delivery projection over the current owner's active public projects. Team membership is not credited with the entire owner's outcomes. |
| Financial fields | Direct projection of existing transparency.overview/accountability.snapshot values; no second accounting implementation. |

Original deadline means the earliest immutable creation commitment, including draft
planning; first public deadline was not separately recorded. Current deadline edits
cannot retroactively improve on-time delivery. Current overdue planning can change
when planned dates change and is deliberately a different measure. Original/current
dates and public reasons remain visible through previews and full milestone history.

Financial overview uses recorded completed Sandbox captures, existing conservative
refund/reversal exclusions, published reported expenses and approved-redaction
coverage. Exact partial refunds remain unavailable. Funding minus reports is a
calculated difference, not available cash, verified bank balance or vendor payment.
Public accountability findings cover published category overruns only; private OCR/
reviewer findings and counts are not published. Full ledger details remain on demand.

## Freshness and failure handling

The UI separately labels last successful GitHub sync, last attempt/start/finish,
internal roadmap update, and summary calculation time. A recent attempt is not
substituted for success. Failed syncs retain previous valid observations and their
age; no activity is never described as abandonment. Missing source data is explicitly
unavailable, with no fabricated zero merge count.

Source-specific freshness is independent of sync freshness: linked issue/PR/GitHub-
milestone last-observed timestamps are batched through a single union/min query;
commit links are checked against the recent sample. Any observation over six hours
old, missing current commit, or stale sync marks available links stale. An empty
linked scope is null/unassessed. Roadmap details preserve their individual warnings.
GitHub deletion and visibility are only observed during synchronization: retained
records can remain and a newly private repository is not detected by a database-only
GET. That existing limitation is displayed, not bypassed with new provider calls.

When a repository is known private/unavailable, activity/metadata/source counts are
withheld; public roadmap assertions still appear. The sync envelope excludes stored
run counters so an old successful run cannot indirectly reveal hidden source counts.
Public change previews include only commitment/status fields, never evidence snapshot
JSON. Reasons are author-declared public roadmap text; they are not private financial
review notes. No raw commit messages or HTML descriptions are rendered.

The dashboard supports loading/error/empty states and manual refresh. A summary
failure leaves the existing roadmap and ledger access available. The roadmap's own
error boundary/list fallback and Gantt confirmation/version-conflict behavior remain
intact. No auto-sync, auto-reschedule or automatic delivered transition is added.

## Query behavior and consistency

Summary reads have a fixed number of SQL queries rather than per-milestone or per-
expense lookups. Immutable history and repository records are loaded in batches.
The public financial snapshot now obtains approved document support in one query,
then applies the existing coverage and accounting formulas. Private receipt analysis
retains its existing authorization and behavior. A regression test compares query
counts before/after adding twelve milestones and twelve expenses and requires the
same query count.

This avoids N+1 requests but does not promise constant runtime or memory: owner
history and project financial records are still read to calculate truthful totals.
Large accounts may later justify batching at the SQL aggregation level, rate limits,
indexes or reviewed caching. There are no stored aggregate tables or silent partial
counts. Preview lists are bounded and explicitly labelled. Different API requests
are not a single shared snapshot, so refreshing the summary after management changes
can reconcile cards with independently loaded roadmap/ledger details.

## Tests and execution

- **247 backend tests passed, zero failed/skipped**, including 11 new dashboard
  cases plus all 236 preceding tests. Existing Starlette/HTTPX warning remains.
- Fresh local migration upgrade through the existing Step 3 head and `alembic check`
  passed with no model drift. No new migration is required for this dashboard.
- **26 frontend tests passed**, including public loading/navigation, empty/history
  states, failed-sync timestamp labels, timing definitions and unsafe GitHub text/URLs.
- TypeScript, Vite production build, Oxlint, Python compilation and whitespace checks
  passed. Only existing AuthContext warnings and the existing large lazy Bryntum
  chunk warning remain; no new dashboard lint warnings.
- Local Chromium synthetic dashboard smoke passed actual Community rendering,
  dependency arrows, drag/right-edge resize proposals, explicit versioned save,
  conflict recovery, visitor read-only behavior and mobile timeline/list switching.
  Error fallback is also exercised without removing roadmap access.

All backend runs use fresh local
opendev_test_* PostgreSQL databases, migrations to the existing Step 3 head and
mocked external services. This step has **no new migration**. Existing pending
8c6072dabc59 belongs to Step 3, not this dashboard.

Frontend tests cover public loading/navigation, a single timeline switch, insufficient
history, failed sync timestamps, safe GitHub URLs and escaped malicious titles.
The real Community widget smoke now runs inside ProjectProgress with synthetic HTTP
fixtures, checking actual drag/right-edge resize confirmation, versioned save, 409
recovery, visitor controls, mobile container sizing, and switching back to the list
without leaving a second chart mounted. Synthetic browser fixtures are not live
backend authentication or provider validation. An initial mobile smoke failure was
a harness mismatch (missing viewport meta); the harness now uses the real app's
viewport configuration and the mobile check passes.

To reproduce: from frontend/, `npm test`, `npx tsc -b`, `npm run build`,
`npm run lint`, and optional `npm run test:gantt-browser` with local Chromium.
For backend/migration checks use the existing fresh-local-DB harness documented in
Phase 3. No production database, provider credentials, deployment or paid service.

## Manual browser acceptance

1. Use a synthetic active public project and local/test database. Open signed out:
   overview, owner profile link, history, GitHub data and ledger access must work.
2. Check public API 404 for draft/paused/completed projects, even with owner cookies.
   Verify no draft expenses, private original IDs, storage URLs, OCR, frozen evidence
   metadata, private reviewer notes, payer/backer identifiers or tokens in JSON.
3. Compare overview totals with the roadmap, maintainer and financial source APIs.
   Edit a planned deadline later and verify original-deadline delivery metrics do not
   improve; cancel/reopen/redeliver and inspect immutable reasons and unknown timing.
4. Sync a synthetic public repository; verify recent issues, closed-unmerged versus
   merged PRs, GitHub milestones and commit sample links. Fail the next sync and
   verify prior observations remain with last-success age and separate failed attempt.
   Make a link old without updating it; a recent overall sync must not hide staleness.
5. Switch list/timeline repeatedly: one lazy Gantt instance, original list controls
   intact. As visitor, no rescheduling writes. As manager, existing versioned edits,
   public reasons, cancellation and failed-save restoration must still work.
6. Open/close the detailed ledger. Only one detailed expense table should appear;
   cards remain concise. Ensure the calculated funding difference is not called cash
   or verified spending. Exercise no reports, no milestones, no activity, unknown
   owner history and summary/API failure recovery.
7. Test keyboard section navigation, source links, small screens, scrolling, focus,
   timeline zoom/list fallback and asset-load failures. Inspect browser Network for
   lazy bundle loading only when Timeline opens and no direct token-bearing API calls.
8. Refresh cards after management changes; account for separate child-view snapshots.
   Live GitHub/PayPal/Supabase/browser-auth and deployment acceptance remain blocked
   by existing NO-GO requirements. Do not deploy on the basis of these local tests.
