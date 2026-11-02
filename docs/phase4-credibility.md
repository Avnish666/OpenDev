# Phase 4 Step 4: Maintainer track record and delivery history

Deployment remains **NO-GO**. This step does not remove any licensing, security,
resource-limit or live-service acceptance blocker. No paid API, AI rating, composite
trust score, new database table, cache or migration is introduced. Existing pending
Step 3 work is preserved; financial, milestone and GitHub records are read-only.

## Files

Created:

- `backend/app/schemas/credibility.py`: explicit public response allowlists.
- `backend/app/services/credibility.py`: deterministic owner-only outcome calculations.
- `backend/app/routers/credibility.py`: three public, read-only endpoints.
- `backend/tests/test_credibility.py`: fairness, attribution, timing and privacy tests.
- `frontend/src/api/credibility.ts`: typed contracts, indicator display and safe source links.
- `frontend/src/pages/Maintainer.tsx`: public profile, separate indicator sections,
  paginated participation/delivery history and source/project links.
- `docs/phase4-credibility.md`: this guide.

Modified backend/app/main.py for registration; frontend/src/App.tsx adds the public
`#/maintainers/{user_id}` route; frontend/src/pages/Projects.tsx links maintainers to
profiles; frontend/tests/transparency.test.mjs covers public rendering, insufficient
history and source-link safety. No dependency or schema change for Step 4.

## Scope, identity and attribution

Stable internal user IDs and GitHub IDs identify the profile. Username and a GitHub
profile/avatar URL are public presentation, not a permanent identity key. Avatar
URLs are generated from GitHub IDs; no email, session token or raw user record is
serialized. Missing users return 404; existing users without owned public history
still have an accessible profile with **Insufficient history** indicators.

Public scope intentionally follows existing project/roadmap/transparency detail
permissions: **active projects only**. Draft, paused and completed project IDs,
counts, titles and associated outcomes are excluded even for signed-in owners.
This is a current publicly accessible track record, **not all lifetime work**.
Historical commitments on projects no longer active can leave the profile scope.
Supporting publicly archived/completed projects would need an explicit coordinated
publication policy, not an exception that leaks currently protected details here.

Project.owner_id determines owner attribution. Other membership rows identify
maintainer or collaborator participation. A project appears once; ownership takes
precedence over a simultaneous team membership. Outcome indicators use **owned
projects only**; a collaborator/maintainer does not inherit the entire project's
success, delay, spending or reward obligations. Team participation is listed without
an outcome score. Historical ownership/role transfers are not recorded in the
current schema; attribution therefore uses current ownership, with that limitation
shown. GitHub observations describe repositories/teams, not individual authorship.

All endpoints deliberately ignore requester privileges: signing in cannot expand
this public projection. They run inside the existing dedicated PostgreSQL
REPEATABLE READ / READ ONLY snapshot, with API-wide no-store/no-referrer headers.
No provider/storage/model calls or source writes occur during profile calculation.

## Indicator contract

Every indicator exposes key, label, numerator, denominator (nullable when there is
no meaningful ratio), sample_size, state, formula, calculated_at, last_updated_at,
limitations and permitted source_links. Fractions are shown as **n / d**, never an
opaque weighted rating. There is no arbitrary minimum-sample threshold. Empty
samples show **Insufficient history**; unsupported measures show **Unavailable**,
not zero performance. One observation is visibly a sample of one, not a robust
reputation conclusion.

`calculated_at` is the database snapshot time. `last_updated_at` is the last known
source mutation time when available, otherwise null. These are not a provider
verification timestamp. Separate API requests/pages have separate snapshots;
refresh if concurrent publication changes pagination.

## Delivery formulas

Sample scope: unique roadmap milestone IDs on owned active projects. Creation,
status, commitment and evidence events reuse immutable MilestoneStatusHistory.

| Key | Calculation |
| --- | --- |
| public_projects_owned | Count distinct owned active project IDs; no ratio. |
| published_milestones | Count roadmap milestone IDs in that public ownership scope; no ratio. |
| asserted_delivered | Current delivered milestone count / all scoped milestones. |
| ever_asserted_delivered | Distinct milestones with any immutable delivered status assertion / all scoped milestones. Repeated delivery never adds a second milestone. |
| overdue_planned | Currently planned milestones whose **current** end date is before today's UTC date / all currently planned milestones. Due today is not overdue. |
| delivered_on_time | Current delivered milestones with a matching immutable actual date <= original deadline / current delivered milestones with known comparable dates. |
| delivered_late | Same denominator, actual date > original deadline. |
| unknown_delivery_timing | Delivered milestones lacking a usable original deadline or matching immutable delivery date / current delivered count. These are excluded from on-time/late denominators. |
| cancelled | Currently cancelled milestones / all scoped milestones. |
| reopened | Distinct milestones with any immutable delivered-to-other-status transition / all scoped milestones. Repeated reopenings do not inflate it. |
| delivery_evidence | Current delivered milestones with recorded links active at their latest delivery assertion / delivered milestones whose repository evidence is publicly available. Missing/private repository evidence is excluded, not called absent. |
| independently_reviewed | Unavailable: there is no real independent delivery-review mechanism. No verified badge or fabricated count. |

**Original deadline** is taken from the earliest immutable `created` event's
planned_end_date, including draft preparation. The schema does not record the first
public commitment separately; we disclose that distinction instead of inventing it.
Later edits, Gantt rescheduling, cancellation or reopening cannot replace this
baseline to improve the on-time metric. Current overdue planning is separately
labelled: rescheduling can affect current overdue status, not original-deadline
success. Draft preparation dates can make the baseline conservative.

Delivery timing uses the latest immutable delivered assertion and requires it to
match the current row's actual_completion_date. A reopened milestone is not currently
delivered and is excluded from current delivery ratios. Re-delivery uses the latest
assertion against the original deadline, not its earliest favorable assertion.
Missing/inconsistent history produces unknown timing rather than assumed success.
Actual dates remain maintainer assertions, not independently established release dates.

Evidence membership is reconstructed from link/unlink history **up to the delivery
version**. A source linked afterward cannot retroactively become supporting evidence
at delivery. No raw frozen source JSON or reviewer reason is returned. Counts mean
links were declared, not that the links prove fulfillment; live deletion/freshness
limits from Steps 1–2 still apply. Public source paths point to permitted roadmap and
history APIs; project links lead to the existing roadmap/list/timeline UI.

## Reward fulfillment formulas

Existing unique entitlement/contribution records are the only source. No invented
delivery deadlines, payment amounts or new reward statuses:

- Issued = count persisted entitlement IDs, including those later revoked.
- Eligible = completed captured contributions in the project's currency, with an
  entitlement currently granted or fulfilled.
- Fulfilled numerator = eligible entitlement IDs marked fulfilled.
- Fulfillment denominator = all eligible entitlement IDs. Zero denominator means
  **Insufficient history**, not 0% or a failing reputation.
- Pending numerator = eligible granted IDs; same denominator.
- Excluded/revoked = issued minus eligible; ratio denominator issued. Refunded,
  reversed, pending/noncompleted contributions, currency mismatches and revoked
  entitlement states are excluded even if an inconsistent row still says fulfilled.
- Overdue rewards = unavailable/null because **no fulfillment deadline is stored**.

An entitlement is counted once through its unique contribution FK, never through
webhook, receipt or milestone joins. Marked fulfillment is a maintainer report;
already delivered benefits cannot be recalled by revocation. Fulfillment notes,
backer/user/order/capture/contribution/entitlement identifiers are not disclosed.
No fulfillment mutation timestamp exists, so source last_updated_at is **unknown**;
we do not substitute issuance time for completion time. The permitted source link
for these private-record aggregates is the public credibility projection itself;
individual backer histories remain private and are not offered as public evidence.

## Financial reporting and GitHub

For each owned active project, **transparency.overview** delegates to the existing
accountability snapshot. Money is integer minor units and remains grouped by
project/currency, never summed across unlike currencies. The result includes:

- reporting_available = at least one published expense claim, with a binary
  indicator and the underlying published-report sample size;
- published reported spending and document-supported reported cents;
- approved public evidence coverage = expenses with >=1 approved redaction /
  published expenses, each expense and amount counted once despite multiple receipts;
- unresolved public findings = count published category-budget overruns from Step 5.
  Private receipt findings/counts/review notes are withheld. This is not a total
  private-discrepancy count and is not proof of fraud;
- last reporting activity = latest published expense updated_at or currently approved
  redaction approved_at. Private uploads/draft edits do not affect it. There is no
  complete publication/unpublication history to reconstruct removed disclosures.

Existing refund/reversal exclusions and the exact-partial-refund limitation are
preserved in notes. Neither a receipt nor an OCR observation proves vendor payment.
A financial reporting endpoint existing with no expenses is not itself a reporting
track record: the profile states no published reports yet.

GitHub indicators reuse stored public Step 1 snapshots and synchronization status:
closed non-PR issues / observed issue snapshots; merged_at PRs / observed PR
snapshots; recent default-branch commit sample count (no full-history denominator).
No claim of individual authorship/productivity. Known inaccessible/private repository
metadata/counts are unavailable, with source links withheld. Missing/stale sync is
labelled; deleted records may remain in snapshots and commits are only sampled.
GitHub evidence does not certify delivery or support an AI-generated credibility score.

## APIs and frontend

| Endpoint | Contract |
| --- | --- |
| GET `/api/maintainers/{user_id}/credibility` | Public identity, scope/attribution, participation counts, separate delivery/reward indicators and per-owned-project financial/GitHub sections, timestamps and limitations. No score or confidential backer detail. |
| GET `/api/maintainers/{user_id}/projects` | `{items,total,limit,offset,calculated_at}`; each item has ID/title/active status/role/public project link. Ordered project ID ascending. |
| GET `/api/maintainers/{user_id}/delivery-history` | Same pagination envelope; owner-only public milestones, ordered created_at descending then ID descending. Original/current deadlines, current asserted actual date, timing/unknown, ever-delivered/reopened flags, permitted delivery evidence count, independently_reviewed=false and source links. |

Pagination limit defaults to 20 and is constrained 1–100; offset >=0. Nonexistent
users return 404, malformed IDs/pagination 422, writes 405. No anonymous writes or
special privileged profile view. Responses use explicit allowlist schemas.

The public `#/maintainers/{id}` page is linked from project maintainer names. It
shows GitHub avatar/identity, ownership versus participation, separate metric cards,
formula/sample/timestamp/limitation disclosures, project roadmap/transparency links,
GitHub evidence, paginated project and dated delivery history, loading/error/empty
states and a Refresh action. No auth provider is required by the profile component.
New maintainers see insufficient history, not a zero trust score. Underlying API
links are constrained to application /api paths; no user-provided external source URL.

## Security, fairness and operational limits

- Source data is self-reported/observed, not proof of promise fulfillment, authenticity,
  payment receipt, fraud, honesty or future performance. No speculative narrative,
  ranking, arbitrary weights, composite rating or automated adverse decision.
- Public scope follows current visibility, which can hide older non-active projects;
  disclose this survivorship limitation rather than implying a complete lifetime record.
- Original deadlines precede any public publication marker, which can conservatively
  count draft planning. No publication/ownership transfer history was fabricated.
- Small samples are explicit. Aggregate counts can permit external inference in very
  small groups; no backer identities or individual financial records are returned.
- Individual rewards cannot be independently audited from the public aggregate alone;
  privacy boundaries are preserved. The profile does not open private histories.
- Original receipts, OCR/extraction IDs/text, storage paths, signatures, tokens, private
  reviewer notes and raw ORM objects are excluded even for signed-in owners.
- Calculations are uncached and may use many per-project/milestone SELECTs. This MVP
  favors consistency over large-account throughput; measure and batch/index/cache
  later if justified. No production scale or live-service verification is claimed.
- Existing browser, PyMuPDF licensing, security/resource and deployment blockers
  remain **NO-GO**. No schema mutation or provider call is part of the profile request.

## Verification

- **236 backend tests passed, zero failed/skipped**, including 16 new credibility
  cases and all 220 preceding cases. Existing Starlette/HTTPX deprecation warning.
- Focused credibility suite also passed **16/16** after strengthening the non-active
  project privacy regression with real owner session cookies.
- Fresh local migration chain through existing Step 3 revision 8c6072dabc59 and
  `alembic check`: passed, no model drift. Step 4 introduces no new migration.
- **21 frontend tests passed, zero failed/skipped**, including new auth-independent
  profile rendering, insufficient/unavailable fraction display and safe source URLs.
- TypeScript, Vite production build, Oxlint, Python compilation and whitespace checks
  passed. The two existing AuthContext lint warnings and existing large Bryntum
  lazy-chunk warning remain. No new warnings were introduced by this step.

Backend tests use fresh local disposable PostgreSQL, mocked GitHub responses and
synthetic history/payment fixtures; no real Sandbox, production database or private
storage service is contacted. Coverage includes no history, owner/team attribution,
multiple projects, original-deadline timing and edits, reopen/cancellation/overdue,
unknown history, links as of delivery rather than retroactive linkage, reward ratio/
revocations/refunds, approved public coverage once per expense, private notes/keys
withheld, non-active project exclusion, stale/private GitHub data, pagination,
anonymous GET-only access and original financial/history records unchanged.
New profile browser acceptance remains manual; frontend checks are SSR/helper tests.

Manual local/test browser acceptance:

1. Open an existing project signed out; follow a maintainer name to their public
   profile. Check avatar/GitHub link, role attribution, indicators and source links.
2. Visit a new user: insufficient history/unavailable independent review, no zero
   rating or fabricated overdue reward. Test invalid user IDs, errors and empty lists.
3. Create a synthetic owned roadmap commitment, deliver on/before its original end,
   and inspect the numerator/sample. Repeat late; move the current deadline later
   and verify original date/timing does not improve. Reopen/redeliver and inspect
   separate current, ever-delivered and reopened counts.
4. Link GitHub evidence before delivery, then another source afterward; confirm the
   latter is not retroactive delivery support. Simulate missing history and stale/
   unavailable repo observations: unknown/unavailable states must remain visible.
5. Compare owner, team maintainer and collaborator profiles. Nonowners get role
   participation, without inheriting another owner's outcome/reward/spending totals.
6. With synthetic Sandbox records, compare issued/eligible/fulfilled/pending/excluded
   counts; refund/reversal/revocation must remove eligibility. No invented deadlines.
7. Publish expenses and multiple approved redactions; compare coverage with existing
   transparency. Draft reports/private originals/private notes must not appear or
   alter public coverage. Never interpret those documents as payment proof.
8. Compare anonymous and owner-cookie responses. Set a test project draft/paused/
   completed and verify it disappears from all three profile endpoints. Inspect
   Network for absence of private backer details, notes, receipts/OCR and storage keys.
9. Test multiple pages/tied creation times, refresh, narrow screens, keyboard/source
   links and loading/offline errors. A public reporting snapshot is not live provider
   verification. Browser acceptance of the new profile remains manual.
