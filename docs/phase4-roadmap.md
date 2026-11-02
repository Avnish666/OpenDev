# Phase 4 Step 2: project roadmap and funding deliverables

Deployment remains **NO-GO**, as documented in `phase3-release-readiness.md`. Step 1
GitHub synchronization is reused; no provider request, payment processing, expense
logic, receipt extraction, credibility AI or Bryntum installation is added.
Existing uncommitted Step 1 work is preserved.

## Files

Created:

- `backend/app/models/roadmap.py`
- `backend/app/schemas/roadmap.py`
- `backend/app/services/roadmap.py`
- `backend/app/routers/roadmap.py`
- `backend/migrations/versions/975a8a867d0d_add_roadmap_commitments_and_audit_.py`
- `backend/tests/test_roadmap.py`
- `frontend/src/api/roadmap.ts`
- `frontend/src/components/Roadmap.tsx`
- `docs/phase4-roadmap.md`

Modified `backend/app/main.py`, `backend/app/models/__init__.py`,
`frontend/src/pages/Projects.tsx` and `frontend/tests/transparency.test.mjs` for
registration, project-page integration and the roadmap SSR regression.

## Models and migration

Revision **975a8a867d0d** follows **2e1d281b5505** and adds three tables:

- `project_roadmap_milestones`: typed BIGINT ID/project/user FKs, title/description/
  deliverable, planned date interval, nullable actual completion date, checked status,
  display order, version, timestamps. Checks enforce start <= end, positive version,
  nonnegative order, and a completion date exactly when status is delivered.
- `milestone_github_evidence`: UUID, project/milestone, evidence type, canonical ID,
  nullable synchronized snapshot reference, minimal frozen link-time observation,
  creator/time, and optional removal actor/time. Composite FKs bind the link to its
  milestone's project and to the same project's issue/PR/GitHub milestone snapshot.
  Unique milestone/type/canonical ID prevents duplicates. A checked discriminator
  requires the appropriate snapshot reference for each non-commit type.
- `milestone_status_history`: immutable versioned events with actor, previous/new
  status, action, public reason, before/after JSON and timestamp. Events cover creation,
  edits, reordering, statuses, linking and unlinking. Unique milestone/version prevents
  two audit events claiming the same revision. A PostgreSQL trigger rejects UPDATE
  and DELETE. Privileged database administrators can bypass controls; use a separate
  migration role and least-privilege runtime role.

Project, user and snapshot references use RESTRICT semantics. There are project/
parent indexes for listings. The migration only creates these tables/indexes and
the history trigger/function; no existing schema/data is rewritten. Destructive
rollback is prohibited. No previous migration was edited. Applied only to newly
created local disposable test databases, never Neon.

## Commitment and transition rules

A new milestone starts **planned**, version 1. Creation is immediately part of the
public roadmap if its project is active; there is no separate per-milestone publish
flag. On draft projects, only owners/maintainers can view and prepare commitments.
When the project becomes active, its roadmap and prior commitment history become
public. Do not enter confidential content even during draft preparation.

Allowed status transitions:

| From | Allowed next statuses |
| --- | --- |
| planned | in_progress, cancelled |
| in_progress | planned, submitted_for_review, cancelled |
| submitted_for_review | in_progress, delivered, cancelled |
| delivered | in_progress |
| cancelled | planned |

No implicit transition is triggered by GitHub synchronization or the passage of
time. A maintainer explicitly submits for review, then explicitly records delivered.
This workflow does not provide independent reviewer approval: the same maintainer
may submit and report delivery. UI/API label it as a maintainer assertion.
Submission and delivery require at least one active supporting link, **not** a closed
issue or merged PR. A link is supporting evidence, not a proof of fulfillment.

Delivery sets actual_completion_date to the server UTC calendar date of that status
assertion. It is not a retrospectively verified release date. Reopening delivery
clears the current date but preserves the prior status/date in immutable history.
To revise a delivered commitment, reopen to in_progress, return to planned, then edit.

Title/description/deliverable/date edits require planned status. Order may change in
any status. **Every edit, status change, link and unlink requires a 10–2000 character
public reason**, including draft edits (stronger than the minimum published-change
rule). Original and new commitments are preserved in history; nothing is silently
erased. Nullable patch fields cannot be explicitly cleared. Both creation and partial
edits validate the resulting date range, text sizes and integer order.

Reorder with PATCH display_order. Values need not be contiguous or unique; ties sort
by ID. A single reorder edits only that milestone and records its prior/new order.
There is no bulk reorder endpoint or cross-milestone dependency scheduling in Step 2.

## GitHub evidence

Canonical numeric GitHub IDs are required for issue/PR/milestone links, **not** local
issue numbers or arbitrary URLs. Commits require a full lowercase 40-character SHA
already present in this project's Step 1 synchronized default-branch sample. The
service never fetches user-provided URLs or trusts URL host text as ownership proof.
A public, synchronized repository snapshot must match the project's fixed GitHub
repository ID. Cross-project snapshots and unknown identifiers return 422.

Existing Step 1 data supplies the latest stored observed state/merge timestamps. Closed PRs are
not counted merged unless merged_at is non-null. GitHub issue and milestone closure
counts remain separate from roadmap delivery status. No precise completion percentage
is calculated. Milestone-associated counts on GitHub itself can include PRs; roadmap
issue and merged-PR indicators count their distinct evidence types.

A link stores a minimal frozen observation and canonical reference. Repository
renames use the latest synchronized full_name to construct canonical links without
changing project ownership/payment association. GitHub-deleted items remain in Step
1 snapshots; roadmap does not infer deletion from incremental absence. For commits
that leave the recent sample, the original SHA/link survives with stale=true and
snapshot_available=false. Other references are protected by RESTRICT FKs against
accidental snapshot deletion. Last-observed timestamps remain explicit.

Evidence is stale if Step 1 status is stale/failed/running, its observation is over
six hours old, the current sample is absent, or the repository is known inaccessible.
As in Step 1, GitHub visibility is last checked at synchronization, not continuously.
Deleted items may remain apparently fresh until time/next observations reveal staleness;
no live existence guarantee is made.

For public visitors when the repository is known inaccessible/private, source IDs,
URLs, source state and merge signals are withheld, while the public roadmap claim
and count/type of its own linked references remain visible. Public history always
projects commitment/status fields only and omits evidence identifiers/frozen snapshot
JSON. Managers can inspect retained source metadata for accountability/recovery.
Public reasons are deliberately public text; users must not put secrets/private
source snippets into them. The server cannot infer whether arbitrary author-written
roadmap prose contains personal information.

DELETE evidence performs a **soft unlink**, records removal actor/time and an audit
event, and leaves the database source intact. Re-linking a removed source reuses its
unique link row, with a new audit event. Removal of the final link is blocked while
submitted/delivered; reopen first. There is no roadmap hard-delete endpoint.

## API contracts

All writes require the existing session, owner/maintainer authorization and exact
trusted Origin CSRF guard. Ordinary collaborators and unrelated maintainers cannot
write. Unknown IDs return 404; active public projects are readable anonymously.
Non-active projects are readable only by their managers. Responses inherit no-store/
no-referrer headers. Read collections/history use a REPEATABLE READ / READ ONLY
snapshot; writes lock project then milestone and use atomic history/state commits.

| Method / path | Request / response |
| --- | --- |
| POST `/api/projects/{id}/roadmap` | Commitment body below; 201 full milestone. |
| GET `/api/projects/{id}/roadmap` | `{items,total,limit,offset}`, ordered display_order then ID. `limit` 1–100 (default 20), offset >=0. |
| PATCH `/api/roadmap/{milestone_id}` | expected_version, reason, subset of commitment fields; full updated milestone. |
| POST `/api/roadmap/{milestone_id}/evidence` | expected_version, reason, evidence_type, canonical_id string; full updated milestone. |
| DELETE `/api/roadmap/{milestone_id}/evidence/{uuid}` | JSON body expected_version and reason; full milestone after soft unlink. |
| POST `/api/roadmap/{milestone_id}/status` | expected_version, reason, status; full updated milestone. |
| GET `/api/roadmap/{milestone_id}/history` | Version-descending event list, same pagination bounds; public projection excludes source metadata. |

Example creation:

```json
{
  "title": "Publish beta",
  "description": "A maintainer-reported development commitment",
  "deliverable_description": "Publish a documented beta release with installation instructions",
  "planned_start_date": "2026-11-01",
  "planned_end_date": "2026-12-01",
  "display_order": 0
}
```

Each milestone response includes project/id, the commitment fields, status,
actual_completion_date, version, creator/timestamps, active evidence, development
signal counts and a delivery-assertion notice. It has no financial amounts or
confidence/completion percentage. The frontend exports a flat typed
`RoadmapMilestone` interface with explicit dates/order/version so Step 3 can adapt it
to Gantt without conflating snapshot state with delivery status.

Every write after creation requires the **current expected_version**. A successful
mutation increments it and writes exactly one history entry. Concurrent or replayed
stale writes return 409; clients must refresh and reconsider their decision. This is
optimistic conflict handling, not a general retry-key protocol. Repeated create
requests have no idempotency key and can create distinct milestones: inspect the
roadmap after ambiguous network errors rather than blindly resubmitting creation.

## Tests and verification

- Full backend suite: **216 passed, zero failed/skipped**, including 22 new roadmap
  cases and all 194 preceding cases. One existing Starlette/HTTPX deprecation warning.
- Fresh local migration chain through 975a8a867d0d and `alembic check`: passed,
  no pending model differences. Existing preservation/audit tests remain passing.
- **Five frontend tests passed**, including roadmap signed-out loading and
  maintainer-only create controls. TypeScript, Vite production build and Oxlint
  passed; only the two existing AuthContext warnings remain. These are SSR/API
  assertions, not automated browser interaction tests.
- Python compilation and `git diff --check`: passed.

Tests use local disposable PostgreSQL and mocked Step 1 GitHub responses. Coverage
includes owner/maintainer creation, collaborator/outsider denial, invalid ranges,
reordering/tie sorting, reasoned published commitment history, duplicate/cross-project
links, canonical-ID/URL rejection, issue/merged-PR/milestone/commit linkage, closed-
unmerged PR behavior, frozen rolled-off commit links, staleness/rename/privacy,
active/draft/non-active visibility, delivery/reopening history, immutable SQL audit,
soft-unlink/relink, concurrent stale versions, CSRF and unchanged PayPal/expense rows.
There is no live-service or browser acceptance claim.

Manual local/test verification:

1. Review the new revision and apply only to a verified local/test target; retain
   all existing NO-GO blockers and require separate production approval.
2. As owner and then maintainer, create two dated commitments and change display
   order; verify deterministic ties and a reasoned before/after history. Try an
   invalid interval, short reason, collaborator edit and hostile Origin.
3. Synchronize a synthetic public repo with Step 1. Read canonical IDs from its
   activity/milestone API (the form accepts canonical IDs, not issue/PR numbers).
   Link an issue, a merged PR, a closed-unmerged PR, a GitHub milestone and sampled
   commit. Confirm development counters do not change delivery status.
4. Move planned → in_progress → submitted_for_review → delivered. Confirm a missing
   link blocks submission, each decision requires a public reason, and delivered is
   labelled a maintainer assertion. Reopen; verify historical completion date remains.
5. Unlink/relink evidence; inspect retained audit entries. Try a different project's
   canonical source and a different milestone's evidence UUID; both must be denied.
6. Rename the repo and synchronize; inspect canonical links. Allow a commit to leave
   the sample or simulate repo privacy/deletion; show stale/unavailable signals,
   retain roadmap commitments, withhold source metadata from public history.
7. In two tabs edit the same version simultaneously; one succeeds and one receives
   409. Refresh rather than overwrite. Confirm PayPal/expense records are unchanged.
8. Signed out, verify active-project roadmap/history, and 404 for draft/non-active
   projects. Verify mobile/keyboard navigation, empty/loading/error states and history
   pagination. No browser/live GitHub acceptance was executed automatically.

No dependencies or paid APIs added. No Bryntum installation, delivery certification,
production migration, deployment, commit or push is part of this step.
