# Phase 4 Step 1: GitHub repository progress synchronization

Deployment remains **NO-GO** under `docs/phase3-release-readiness.md`. This step does
not address licensing, hostile-file isolation, real-service/browser acceptance or
other release blockers. No deployment, production migrations, commit or push.

## Files

Created models, schemas, service and router under
`backend/app/{models,schemas,services,routers}/github_progress.py`, migration
`backend/migrations/versions/2e1d281b5505_add_github_progress_snapshots.py`,
`backend/tests/test_github_progress.py`, `frontend/src/components/GitHubProgress.tsx`
and this guide. Modified model/router registration and frontend project page.
The prior release migration-preservation test now checks Alembic's actual head
rather than assuming the Phase 3 revision is the final revision forever.
No payment, expense, extraction, OAuth-storage or financial-calculation logic changed.

## Database

Revision **2e1d281b5505** follows **a684112224e6** and only creates five tables:

- `github_sync_runs`: UUID attempts, indexed project FK, checked running/completed/
  failed status, timestamps, sanitized error code, counters and optional retry time.
- `github_repository_snapshots`: project PK, unique canonical repository ID,
  allowlisted metadata JSON, ETag, last successful observation, recent commit sample
  and a public-access flag that remains false after a visibility failure until a
  subsequent successful sync.
- `github_milestone_snapshots`: canonical ID, GitHub number, title/description/state,
  due date, GitHub open/closed association counts and last-observed time.
- `github_issue_snapshots`: canonical ID/number, title/state, nullable external
  milestone ID, creation/update/closure timestamps and observation time.
- `github_pr_snapshots`: canonical ID/number, title/state, creation/update/merge
  timestamps and observation time.

Each item table has a project/canonical-ID composite primary key, unique canonical
ID and RESTRICT project FK. Issue milestone IDs are external references, deliberately
not hard FKs: deleted or unimported GitHub milestones must not break issue imports.
GitHub milestone open/closed counts can include associated PRs; our issue counts
exclude Issues API entries with `pull_request`. No aggregate financial tables.
The new migration prohibits destructive downgrade. Old migrations are unchanged.
Only fresh local disposable databases are used to test migration upgrades/drift.

## Official REST wire operations

All calls go to fixed HTTPS `api.github.com`, with JSON Accept, User-Agent and
`X-GitHub-Api-Version: 2022-11-28`. No SDK or invented SDK method names.

- `GET /repositories/{repository_id}`: stable canonical identity lookup, public
  visibility validation and metadata. ETag / If-None-Match / 304 reuse only validated
  metadata, while activity endpoints are still fetched.
- `GET /repos/{owner}/{repo}/milestones?state=all`: full bounded milestone refresh.
- `GET /repos/{owner}/{repo}/issues?state=all&sort=updated&direction=desc`: open and
  closed issues, skipping every entry containing `pull_request`; incremental `since`
  after the first successful sync.
- `GET /repos/{owner}/{repo}/pulls?state=all&sort=updated&direction=desc`: PR snapshots,
  using the REST list response's `merged_at`, not closed state, to identify merges.
- `GET /repos/{owner}/{repo}/commits?per_page=30`: most recent default-branch sample,
  storing only canonical SHA and committer date, not messages/emails. Empty-repository
  409 responses produce an empty sample.

Reference contracts: https://docs.github.com/en/rest/repos/repos ,
https://docs.github.com/en/rest/issues/milestones ,
https://docs.github.com/en/rest/issues/issues ,
https://docs.github.com/en/rest/pulls/pulls ,
https://docs.github.com/en/rest/commits/commits and
https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api .
No live GitHub calls were made in this task; tests assert REST requests via transport
mocks. Official documentation links are provided for operator verification.

Requests are anonymous by default. Optional **backend-only `GITHUB_SYNC_TOKEN`**
enables configured authentication if needed for quota. Never reuse/store login
OAuth tokens or introduce frontend secrets. Use minimal public-repository read
permissions; do not grant unnecessary write/admin access. Token values never enter
models, responses or logs. Authorization headers are sent only to the fixed host;
redirects are disabled and pagination never follows arbitrary Link destinations.

## Synchronization, retries and consistency

Synchronous FastAPI worker endpoint, request-driven, no paid scheduler or background
queue. Project owner/maintainer authorization and exact trusted-Origin CSRF guard
run before collection. A dedicated connection holds a PostgreSQL transaction
advisory lock keyed by project; competing requests receive 409. Metadata writes use
the existing get_db session. A durable running attempt is committed before I/O.

If a process dies, its lock releases but its attempt can remain running. The next
sync that obtains the lock marks orphan running attempts INTERRUPTED, then starts a
new attempt. No worker lease takeover while another lock is held. Status marks
running/failed attempts stale; a user can refresh and retry after interruption.

All provider responses are collected and Pydantic-validated before atomic upserts
and success timestamp commit. Invalid JSON/schema, missing timestamps, wrong IDs,
private/missing repositories, network failures or resource limits fail the attempt
without replacing snapshots. A failed database write rolls back the observation
transaction. Previous successful data and last-successful-sync time remain available
to managers. Rate-limited failures record retry_at; the database-wide cooldown conservatively
protects the shared anonymous-IP/configured-token quota. Retries before that time return
429 with Retry-After and do not call GitHub. No tight-loop or implicit HTTP retry.
After transient failures, a maintainer explicitly retries the whole bounded batch.

Limits: ten-second HTTP phase timeouts, an 80-second collection deadline checked
between reads, 2 MB decompressed body per response, 100 items/page and at most five
pages per milestone/issue/PR collection. The final blocking HTTP read can extend
past the collection deadline by its read timeout. Link rel=next decides whether
another fixed-path numbered page is needed; untrusted URLs are never followed.
Hitting the cap fails the entire attempt with PAGE_LIMIT; a large initial repository
needs future resumable backfill rather than a falsely successful truncated import.

Issues use a ten-minute overlap before the previous successful run's **start** time.
PRs use updated-desc ordering and stop after the page crosses that cutoff. Milestones
are refreshed each run. GitHub's API does not provide a multi-request transaction:
changes during paging may require another sync. Clock skew and GitHub eventual
consistency can still affect incremental freshness. Commit sampling is explicitly
not a complete commit history or a productivity score.

Repository renames are resolved using the original canonical ID and current
full_name. A new repository at the old name cannot silently replace that identity.
The project/payment repository association is not rewritten. Same-ID ownership
transfers remain observations of that repository, not renewed owner verification.
Visibility failures hide public activity; a later unrelated error cannot restore it.
Public visibility is last checked at sync time, not on every database-only GET.
A repository made private between syncs can remain visible until the next sync;
do not promise immediate revocation or automatic continuous synchronization.

Upserts reflect edited issue/PR/milestone data. Deleted records are **retained**,
never silently deleted or assumed complete. last_synced_at on each record is its
last observation. Counts are retained-snapshot counts, not guaranteed current
GitHub totals. Incremental absence cannot establish deletion; no tombstone inference.
Per-record revision history is not stored: sync attempts are retained but snapshots
hold the latest observed values. A future event/history model is outside Step 1.

## Application APIs

All responses inherit API-wide no-store/no-referrer headers. Public reads require
an active project; draft/paused/completed activity and milestones return 404 even
for managers. Managers may inspect sync-status and trigger sync on non-active
projects. Ordinary collaborators/backers/other-project managers cannot trigger.
Known unavailable/private repository data returns 404 to public readers; managers
can inspect retained data/errors for an active project.

| Method / path | Contract |
| --- | --- |
| POST `/api/projects/{id}/github/sync` | No body required. Owner/maintainer session + trusted Origin. Returns RunResponse (200 with completed or failed attempt); 409 concurrent, 429 cooldown, 401/403 auth denial. Durable failures use sanitized error_code, timestamps and counters, not provider text. |
| GET `/api/projects/{id}/github/sync-status` | latest attempt, last_successful_sync_at, stale, and signal-not-completion notice. No previous attempts yields null timestamps/stale=true. |
| GET `/api/projects/{id}/github/activity` | sync envelope, allowlisted repository metadata, retained open/closed issue and PR counts, merged count, issue/PR page and commit sample. `limit=20` (1–100), `offset=0` (>=0), independently applied to each issue/PR list; updated descending + canonical-ID tie break. |
| GET `/api/projects/{id}/github/milestones` | sync envelope, total, items; same pagination bounds, milestone number then canonical-ID order. |

Stale means no successful sync, success older than six hours, or latest attempt
not completed. A record can still be retained after deletion despite a fresh run.
API IDs and numbers with the repository full_name provide canonical GitHub references;
UI escapes titles/descriptions and does not render untrusted HTML.

## Frontend and manual verification

Project details include GitHub sync controls for managers, refresh/status/last-success
and stale/error states, milestone pagination, issue/PR/merge counts and a default-
branch commit-sample count. Signed-out active projects use database-only reads.
No Bryntum, credibility score, automatic deliverable completion or paid package.

1. Review the additive migration and apply **only on a verified local/test database**.
   Production migrations need separate approval. Start the existing API/frontend;
   no new environment variable is required for anonymous public GitHub reads.
2. On an active project you own, click Sync GitHub. Compare canonical repo ID,
   current full_name, milestone IDs/numbers and issue/PR counts to GitHub. Check one
   closed-but-unmerged PR is not counted merged. Counts are observations, not proof.
3. Edit/reopen/close a milestone or issue in a synthetic public repo and sync again;
   confirm upsert/no duplicates. Rename that test repo and confirm its identity stays.
4. Test two tabs triggering simultaneously, API timeout, rate-limit cooldown, malformed
   mocks and process restart. Confirm prior data survives; running attempts recover
   on the next admitted sync, not on a nonexistent background worker.
5. Test collaborator/outsider writes, missing/hostile Origin, draft project public
   access, and known private/deleted repository denial. Do not test with real private
   data. Confirm no token/provider-body in browser network responses or logs.
6. Browse while signed out, narrow viewport and keyboard-only. Check empty/loading/
   stale/error labels, milestone pagination and explicit retained-count caveats.
7. Compare expense/contribution totals before and after syncing; they must not change.
   Live GitHub/browser checks are manual and were not performed here.

## Automated verification

- Full backend suite: **194 passed, zero failed/skipped** (176 preceding cases and
  18 GitHub sync cases), with the existing Starlette/HTTPX deprecation warning.
- Final shared-quota cooldown and payment-record invariance refinements are checked
  again by the focused GitHub suite: **18 passed, zero failed/skipped**.
- Fresh local upgrade through 2e1d281b5505 and `alembic check`: passed, no model drift.
- Four frontend tests passed, including signed-out GitHub loading and maintainer-only
  button rendering. TypeScript, Vite production build and Oxlint passed; only the
  two existing AuthContext warnings remain. These are SSR/API tests, not browser E2E.
- Python compilation and `git diff --check`: passed.

Tests use mocked GitHub HTTP and isolated local PostgreSQL schemas. They cover
initial/repeated imports, milestone edits, issue/PR separation, merged PRs, rename,
missing/private/identity-mismatched repositories, conditional metadata, safe
pagination (including an untrusted Link), page cap/timeouts, rate-limit cooldown,
malformed late responses with atomic rollback, orphan recovery, concurrent calls,
owner/maintainer/collaborator/outsider/anonymous permissions, CSRF, active-project
visibility, stable snapshot counts, optional secret exclusion and unchanged
expense/contribution records. Live GitHub/browser checks remain manual.
No deployment, production migration, commit or push; NO-GO remains in force.
