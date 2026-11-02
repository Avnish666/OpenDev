# Phase 4 Step 3: Bryntum Gantt Community

Deployment remains **NO-GO** under `phase3-release-readiness.md`. This step does not
resolve the PDF licensing, hostile-file isolation, historical credential or live-
service release blockers. No deployment, production migration, commit or push.

## Installation, documentation and licenses

Installed exact **8.0.0-beta.1** packages:

- `@bryntum/gantt-community`
- `@bryntum/gantt-react-community`
- `@bryntum/core-community` (direct declaration for documented local icon CSS imports)

Their six other declared Community dependencies are all the same version. All nine
package manifests and LICENSE files declare **MIT, copyright Bryntum 2009–2026**.
No Business, Enterprise or trial package is installed. Versions and integrity hashes
are locked in package-lock.json. This is a **beta** release, not a claim of stable
vendor compatibility with every browser.

Inspection before implementation:

- `npm view @bryntum/gantt-community version license homepage dist.tarball --json`
- `npm pack @bryntum/gantt-community@8.0.0-beta.1 --ignore-scripts` and inspection of
  the archive's README, LICENSE, package.json and TypeScript declaration locations.
- Installed Gantt README/AGENTS, React wrapper README and
  `lib/BryntumGantt.d.ts`, Gantt `gantt.d.ts`, TaskDrag/TaskResize/Dependencies source,
  TaskModelCommunity and engine GanttCoreEvent manual-scheduling implementation.

The versioned **official shipped documentation** confirms CSS setup, React >=18,
TypeScript >=4.2, Vite >=5 and Community TaskDrag/TaskResize/Dependencies. The wrapper
quick start documents BryntumGantt and BryntumGanttProps. Current online guide links:
https://bryntum.com/products/gantt/docs/guide/Gantt/quick-start/react and
https://bryntum.com/products/gantt/docs/guide/Gantt/basics/feature-availability .
The installed declarations/source govern the code; higher-tier examples were not
assumed to work in Community. No SDK/API name was guessed from a paid product.

Exact installation commands (from frontend/):

```sh
npm install --save-exact @bryntum/gantt-community@8.0.0-beta.1 --ignore-scripts
npm install --save-exact @bryntum/gantt-react-community@8.0.0-beta.1 --ignore-scripts
npm install --save-exact @bryntum/core-community@8.0.0-beta.1 --ignore-scripts
```

MIT notices for all installed packages and upstream third-party notices are retained
at `frontend/public/third-party/bryntum-community-notices.txt`, copied into static
builds. Font Awesome code is MIT and bundled fonts use SIL OFL 1.1; its notices are
included. We import solid icons locally, preventing Bryntum's missing-font CDN
fallback. No icons/API assets are fetched from a CDN by this integration. Generic
vendor notices mention optional commercial products; that is not evidence those
packages are installed. Existing PyMuPDF obligations remain separate and unresolved.

## Files

Created:

- `frontend/src/api/gantt.ts`: typed mapping, calendar-date conversions, graph
  validation, bounded paginated loading and versioned schedule save helper.
- `frontend/src/components/RoadmapTimeline.tsx` and `.css`: actual Community React
  component, proposal/confirmation workflow, details, evidence and responsive sizing.
- `frontend/tests/gantt.test.mjs`: adapter/save/privacy/dependency regression tests.
- `frontend/tests/browser-gantt-smoke.mjs`: local Chromium/CDP smoke with synthetic
  HTTP fixtures, not real provider/backend credentials.
- `frontend/public/third-party/bryntum-community-notices.txt`.
- `backend/app/models/roadmap_dependency.py`,
  `backend/app/services/roadmap_dependencies.py`,
  `backend/app/routers/roadmap_dependencies.py`,
  `backend/tests/test_roadmap_dependencies.py`.
- `backend/migrations/versions/8c6072dabc59_add_roadmap_dependency_links.py`.
- `docs/phase4-bryntum.md`.

Modified frontend package.json/package-lock.json, existing Roadmap.tsx for the
Timeline/list switch and render-error boundary, backend router/model registration.
Existing list creation/editing/status/evidence/history controls remain available.
No previous migration or existing financial service was modified.

## Exact imports and APIs

Runtime imports:

```ts
import { BryntumGantt, type BryntumGanttProps } from '@bryntum/gantt-react-community';
import type { TaskModelConfig } from '@bryntum/gantt-community';
import '@bryntum/core-community/fontawesome/css/fontawesome.css';
import '@bryntum/core-community/fontawesome/css/solid.css';
import '@bryntum/gantt-community/gantt.css';
import '@bryntum/gantt-community/svalbard.css';
```

One structural stylesheet and one theme, as documented. The existing Roadmap lazy-
loads the timeline with React Suspense, plus an error boundary that offers the list
when module loading or widget rendering fails. The wrapper owns widget initialization
and destruction. No extra application-owned widget instance or duplicate roadmap store.

Typed wrapper configuration uses height, readOnly, columns (HTML-encoded name),
project.tasks/dependencies, viewPreset, snap and day timeResolution. TaskRenderer
returns a DomConfig **text** value, avoiding raw HTML from titles. Selection uses
onTaskClick and an accessible HTML select. Zoom presets verified in the installed
Scheduler preset registry: `dayAndWeek`, `weekAndDayLetter`, `monthAndYear`.

Events used: onBeforeTaskDrag, onTaskDrag, onBeforeTaskDropFinalize,
onBeforeTaskResize and onBeforeTaskResizeFinalize. The package types document
context.async and context.finalize(false). Proposed drag dates come from the typed
onTaskDrag startDate/endDate event; right-edge resize uses the typed context.endDate
and the authoritative original start date. No cast invents missing event properties.

TaskDrag and right-edge TaskResize are enabled only for authorized managers and
planned tasks. BasicTaskEdit, CellEdit, TaskMenu, TaskDragCreate, automatic task
creation and editable tooltips are disabled. Dependency creation in the widget is
disabled with `dependenciesFeature: { allowCreate: false }`. No critical path,
baselines, paid task editor, resource scheduling or enterprise functionality.

## Data and dates

Existing `RoadmapMilestone` IDs remain unchanged. The adapter orders display_order
then ID and maps title/name, planned dates, status, deliverable text and development
signals; the source row remains authoritative and is never mutated. Metadata also
preserves stale evidence flags. Full row details and GitHub links remain outside
Bryntum, with last successful GitHub synchronization and stale warnings visible.
No percentDone field, progress column or calculated delivery percentage is supplied.
Issue closure and PR merges remain development signals, separate from delivery.

OpenDev end dates are **inclusive** calendar dates; Bryntum intervals use an exclusive
end. The adapter adds one local calendar day when rendering and subtracts one when
forming a proposal. Same-day commitments render a full day, not a fabricated delivery
milestone. Parsing/formatting uses local year/month/day fields, never UTC ISO slicing.
Date validation rejects impossible dates and reversed intervals. DST regression tests
run through America/New_York calendar boundaries. Only day-granularity proposals
are persisted; there is no timezone-dependent time-of-day commitment.

Every task is **manuallyScheduled=true**. The installed engine source explicitly
preserves manually scheduled positions/durations despite dependencies. Backend
scheduling writes never touch another milestone. This integration never computes
or persists a contractual date from dependency relationships.

## Confirmed save workflow

1. A manager drags a planned task, resizes its end, or uses the accessible date form.
2. The widget operation is **rejected** using finalize(false), then the wrapper is
   remounted from authoritative rows. The gesture only opens an application proposal;
   it does not optimistically rewrite the visible committed dates or backend.
3. Show the old dates in details, proposed dates in confirmation, and require a
   10–2000 character **public reason** for every save, even on a draft project.
4. Explicit Confirm sends PATCH `/api/roadmap/{id}` with only expected_version,
   reason, planned_start_date and planned_end_date. No status, delivery date, funds
   or other task dates are included. The existing backend enforces manager permission,
   planned status, date validity, version and immutable before/after history.
5. Success reloads authoritative rows. Cancel, HTTP failure or 409 keeps/rebuilds the
   original rows. A conflict displays a refresh instruction rather than auto-retrying
   with a new version. The timeline exposes a Reload action.

Visitors have readOnly=true globally and non-draggable/non-resizable task records,
no scheduling forms and no save capability in the helper. Server authorization and
CSRF remain mandatory; client controls are not the security boundary. Reaching a bar
end date never changes status. Delivered/in-progress/cancelled/submitted commitments
cannot be rescheduled without following existing reopen/return-to-planned rules.

## Dependencies: supported, read-only visualization

Community supports dependency arrows. Stored edges are simple finish-to-start
relationships mapped to `{ id, fromTask, toTask, type: 2 }`. Their dates may overlap
or violate the suggested ordering: arrows describe a declared relationship and do
not enforce/reschedule contractual dates. No lag or scheduling solver is exposed.

Because Step 2 had no dependency storage, additive revision **8c6072dabc59** follows
975a8a867d0d and adds only `roadmap_dependencies`: ID, indexed project ID, predecessor
and successor IDs. Composite FKs bind both ends to milestones of the same project;
unique project/from/to and a non-self check protect basic integrity. Service-level
cycle detection runs while holding the existing project write lock, so concurrent
opposite edges cannot create a cycle. The frontend independently rejects foreign,
missing, duplicate, self and circular edges. Direct privileged SQL can bypass the
service's cycle rule; there is no claim of database-wide DAG enforcement.

APIs:

- GET `/api/projects/{id}/roadmap/dependencies`: `{items,total,limit,offset}`;
  limit 1–100 (default 100), offset >=0. Same public-active/manager-private scope as
  the existing roadmap and a read-only consistent snapshot.
- POST same path: from_id, to_id, expected_version of the predecessor, and public
  reason. Owner/maintainer + CSRF; 201 edge. Increments predecessor version and
  appends dependency_linked to existing immutable roadmap history. No dates/status change.
- DELETE `/api/projects/{id}/roadmap/dependencies/{dependency_id}`: JSON
  expected_version and reason; manager + CSRF, 204. Appends dependency_removed
  before removing the edge. Prior relationships remain in audit history.

Dependency editing UI is intentionally absent in this first integration. Authorized
API users may manage audited edges; visitors only see arrows. No unsafe drag-to-link
or automatic propagation. The new migration blocks destructive downgrade and was
applied only to fresh local disposable databases, never production.

## Loading and resource limitations

Timeline loading reads existing roadmap pages, the new edge pages and existing
GitHub sync-status. It caps each collection at **1,000 records** and fails with a
list-fallback message instead of showing a misleading partial graph. API pages are
separate snapshots; concurrent pagination edits may require reload. Duplicate IDs
or dangling/cyclic edges cause a controlled error. There is no new aggregate store.

At the measured build, the lazy timeline JS chunk is about **1.95 MB / 604 KB gzip**,
CSS about **385 KB / 69 KB gzip**, with local Font Awesome font assets. Vite emits its
large-chunk warning; this is recorded, not hidden. The list and ordinary application
code stay in their existing small entry chunk. This beta package footprint needs
mobile/performance acceptance before release. No bundle-size or universal browser
compatibility guarantee is made. Other Phase 3 NO-GO conditions remain unchanged.

## Automated checks

- **220 backend tests passed, zero failed/skipped**: four new dependency cases and
  all 216 preceding cases. Existing Starlette/HTTPX deprecation warning remains.
- Fresh local migration upgrade through 8c6072dabc59 and `alembic check` passed;
  no model drift. No previous migration changed or destructive downgrade executed.
- **18 frontend tests passed, zero failed/skipped**: 13 new adapter/save/graph tests
  plus five preceding tests. They cover mapping, ordering, inclusive dates/DST,
  empty state, public read-only, planned-only editing, reasons, failed updates,
  version conflicts, stale evidence, dependencies and no automatic status changes.
- The **real Community widget passed the local Chromium smoke**, including rendered
  tasks and dependency arrows, actual mouse drag, actual right-edge resize, no write
  before confirmation, selected details/stale evidence, a versioned confirmed save,
  409/original-date recovery and public read-only controls. The final smoke exited
  cleanly with no runtime exceptions. Initial harness/import/cleanup issues were
  corrected; missing-icon CDN fallback was removed by local font imports.
- TypeScript against the installed Community declarations, Vite production build,
  Python compilation and `git diff --check` passed. Oxlint reports only the two
  existing AuthContext warnings; Vite reports the documented large lazy chunk.

Backend tests use isolated local PostgreSQL. Frontend tests and Chromium use
synthetic data/mocked HTTP, not live authentication/provider/backend acceptance.
No paid API, production secret, deployment, production migration, commit or push.

Run from frontend/: `npm test`, `npx tsc -b`, `npm run build`, `npm run lint`.
For the optional real component smoke, run `npm run test:gantt-browser` with a local
`/usr/bin/chromium`. It starts local Vite and Chromium/CDP, serves only synthetic
API fixtures, performs checks and cleans up its own temporary profile. It does not
use real authentication, production data or PayPal/Supabase/GitHub credentials.
The Chromium container smoke uses --no-sandbox; that is a test-harness constraint,
not advice for deployed user browsers or the backend document processing policy.

Run backend/migration checks with the existing isolated local harness or a fresh
local opendev_test_* PostgreSQL database as described in Phase 3. No new production
migration approval is implied.

## Manual acceptance still required

1. Review/apply the new migration only on a verified local/test database. Preserve
   licensing/security NO-GO; do not deploy based on this feature's local tests.
2. Open an active public project signed out. Switch list/timeline, scroll horizontally,
   change day/week/month scales, select bars and dropdown entries. Confirm no date
   editing controls, rendered percentages or automatic delivery status changes.
3. As owner/maintainer, drag/resize a planned task and verify old dates persist until
   explicit confirmation with a public reason. Cancel; then save and inspect the real
   backend's immutable history. Try in-progress/delivered tasks and hostile Origin.
4. Edit from another tab to force a real version conflict, simulate an API failure,
   reload, and confirm no stale overwrite or automatic retry. Check DST/timezones,
   inclusive same-day dates and keyboard-accessible date proposals.
5. Create dependencies via the authenticated local/test API; verify arrows and deny
   self/circular/cross-project links. Dates must not change merely due to edges.
   Remove one edge and inspect retained history.
6. Select issue, merged PR, closed-unmerged PR, GitHub milestone and commit evidence;
   check links, sync timestamp and stale warnings. No source activity certifies delivery.
7. Verify list management/history controls still work, narrow screens, focus order,
   zoom/scroll, screen-reader alternatives, empty/error states, asset failure fallback,
   cold lazy-load performance and large supported timelines in deployed target browsers.
8. Inspect Network: local fonts/styles, no unexpected CDN, trial assets, paid requests,
   secrets or direct client GitHub tokens. Live backend/provider and broad browser
   acceptance remain unexecuted; synthetic smoke is not full deployment verification.
