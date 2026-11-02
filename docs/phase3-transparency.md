# Phase 3 Step 5: Public Financial Transparency Ledger

## Files and scope

Created:

- `backend/app/schemas/transparency.py`: public response allowlists.
- `backend/app/services/transparency.py`: active-project authorization, public projections, search and pagination.
- `backend/app/routers/transparency.py`: three anonymous read APIs.
- `backend/tests/test_transparency.py`: public contract, visibility, financial and privacy regression tests.
- `frontend/src/api/transparency.ts`: typed API contracts and safe money display.
- `frontend/src/components/Transparency.tsx`: public overview, category charts, ledger and expense detail.
- `frontend/src/components/Transparency.css`: responsive layout, accessible table and chart styling.
- `docs/phase3-transparency.md`: this guide.

Modified `backend/app/main.py` to register the router and
`frontend/src/pages/Projects.tsx` to embed the public section on active project
pages. Existing expense management stays available to maintainers; signed-out
visitors get the dedicated public ledger. No payments, accountability algorithms,
models, dependencies, storage policy or existing migrations were changed.
No database migration is needed.

## API contracts

All three APIs require no session. A maintainer cookie does not expand their data
scope. All responses set `Cache-Control: no-store` and `Referrer-Policy: no-referrer`.
Only `active` projects are eligible, even for their owners. Draft, paused, completed,
unknown and other non-active project requests return 404. The older expense and
accountability APIs retain their existing visibility policies.

### GET `/api/projects/{id}/transparency`

Returns:

- `financial_summary`: existing Step 4 `AccountabilitySnapshot` with anonymous/public
  evidence scope, authoritative integer minor-unit funding, reported spending,
  budget variance and evidence coverage.
- `public_findings`: category, fixed finding code, severity, safe explanation,
  `unresolved=true`, and `scope=published_category_totals`.
- `public_unresolved_discrepancy_count`: count of distinct over-budget categories.
- `private_discrepancy_count=null`: private receipt discrepancies are unavailable,
  not claimed to be absent.
- `finding_policy`: the explicit public disclosure boundary.
- `last_updated_at`: calculation timestamp, with `timestamp_basis` explaining that
  this is a refresh time, not the time of the latest ledger change or settlement.

Every endpoint uses Step 4's REPEATABLE READ / READ ONLY snapshot transaction.
Financial calculations delegate to `accountability.snapshot(..., None)`; no
second accounting implementation or aggregate table exists.

Gross completed funding includes captured completed/refunded/reversed contribution
records; pending, denied, failed and uncaptured contributions are excluded. Original
amounts of refund/reversal-affected contributions are excluded from net funding.
Partial refund amounts are not stored by the existing integration: the entire
affected capture is conservatively excluded and exact refund totals remain null.
Reported spending includes published expenses only. Funding minus reported spending
is a calculated difference, never available cash or a verified bank balance.

Coverage counts each expense and its amount once regardless of the number of
approved documents. "Without public evidence" does not assert that private
supporting documents do not exist. No independent vendor payment is verified.

### GET `/api/projects/{id}/ledger`

Query parameters:

| Parameter | Default | Rules |
| --- | --- | --- |
| `limit` | 20 | 1–100 |
| `offset` | 0 | Nonnegative |
| `sort` | `date_desc` | `date_desc` or `date_asc` |
| `q` | empty | Maximum 200 characters; case-insensitive literal substring in published vendor, description or category |
| `category` | empty | Maximum 100 characters; trimmed, case-insensitive exact category |
| `evidence` | `all` | `all`, `supported`, `unsupported`; public approved evidence only |

Returns `project_id`, `items`, filtered `total`, `limit`, `offset`, `sort`, and
`calculated_at`. Ordering is expense date followed by ID, both in the selected
direction. SQL search is parameterized; `%` and `_` are literal search characters.
Offsets beyond the filtered total return an empty list.

Each item exposes only `id`, `project_id`, `currency`, `category`, `vendor`,
`description`, `amount_cents`, `expense_date`, `updated_at`,
`public_evidence_status`, `evidence`, `findings`, and
`independently_payment_matched=false`. Expense timestamps come from expense records.

### GET `/api/projects/{id}/ledger/{expense_id}`

Returns the same public ledger-entry schema. Cross-project, unknown and unpublished
expenses return 404. It cannot be used to reach draft details.

## Evidence publication and discrepancy policy

Only explicitly published, approved redacted documents associated with a published
expense are listed. Each public document exposes **only its application document ID,
MIME type and approved-redacted status**. No original filename, uploader, original
source ID, storage key, hash, signed URL, extraction ID, OCR content, processing
error, private finding or reviewer note is included.

Download buttons call the existing `/api/documents/{id}/download` endpoint only on
click. That endpoint rechecks current authorization and signs a roughly 60-second
URL. Revoked approval prevents new downloads; already issued URLs may remain usable
until expiry. The UI does not persist signed URLs and requires HTTPS. Storage
configuration and its private bucket remain unchanged. Missing storage configuration
produces an error; it never falls back to a public bucket.

Step 4 has no approved publication channel for private extraction findings. Step 5
therefore publishes only deterministic category budget-overrun findings derived
entirely from already-published financial records. It does **not** sanitize private
OCR by simply removing snippets or treat approval of a redaction as approval of an
original's extraction. Findings on an expense detail describe its category total,
not an allegation about that expense. No private reviewer opinion is published or
used to clear an issue. No fraud or payment-certification assertion is made.

The public count is deliberately not a total of all private discrepancies. A future
explicit finding-publication workflow is needed to disclose receipt mismatches;
there is no implicit publication or new review write endpoint in this step.

## Frontend

The public project page includes:

- Overview cards for gross/net funding, refund/reversal exclusions, reported spending,
  calculated difference and public document support counts/amounts.
- Budget allocation/spending bars with exact text values. Color is supplementary;
  decorative bars are hidden from screen readers and use a labelled per-category scale.
- Text category breakdown, safe unresolved findings and financial limitations.
- Search/category/evidence/order filters, loading/error/empty states, paginated table
  with column headers and caption, and an expandable expense detail panel.
- Approved-redaction download actions, refresh controls and calculation timestamps.

The frontend shows integer values safely using BigInt for formatting; amounts beyond
JavaScript's safe integer range display a warning instead of rounded financial
figures. No new chart package, AG Studio, paid API or LLM is involved.

## Validation

The full backend suite and local migration checks use the existing isolated local
PostgreSQL harness `/workspace/opendev-setup/test-step7.py`. It creates a fresh
`opendev_test_*` database; no Neon connection or production migration is used.
The new tests reuse migrated local-schema fixtures from Step 4.

Regression coverage includes active/draft/non-active visibility, published/draft
expense isolation, gross/net/refund/reversal rules, budget variance, multiple
documents without inflated coverage, safe public findings, private download denial,
approved redaction access and revocation, private notes/OCR/key exclusion even for
owners, filtering/pagination/tie sorting, cross-project access, empty projects,
read-only routes, and the actual response fields consumed by the TypeScript UI.
These are API contract checks, not a browser end-to-end test.

Validation results:

- **173 backend tests passed, 0 failed, 0 skipped**, including 20 new transparency
  cases and all 153 preceding tests. One existing Starlette/HTTPX deprecation warning.
- Fresh local migration to head and `alembic check`: passed; no new upgrade operations.
- `npx tsc -b`, `npm run build`, and `npm run lint`: passed. Lint reports only the
  two existing AuthContext warnings, with no new transparency warnings.
- Python compilation and `git diff --check`: passed.

The first run had three fixture failures because the test attempted to insert
published documents without approval; the existing database correctly rejected
those rows. The fixtures now represent unapproved documents as private, and the
full suite passes without weakening any constraint.

## Manual browser verification

1. Use the existing local backend/frontend setup with a verified local/test database.
   Do not copy production credentials. No new environment variables are required.
2. Open an active project in a signed-out/incognito browser. Confirm the public
   Financial Transparency section loads without login, including an empty project.
3. With synthetic Sandbox contributions, compare cards to database completed captures,
   refund/reversal exclusions and published expenses. Confirm pending/failed funding
   and draft expenses do not contribute. Read the partial-refund disclosure.
4. Add published expenses with different dates/categories and a tied date. Test search,
   literal `%`/`_`, category/evidence filters, sorting, pagination and empty results.
5. Inspect an expense; verify vendor, amount, description, date and evidence labels.
   Check category overspend appears as a category-level unresolved finding.
6. Upload an original and an unapproved redaction through existing maintainer controls.
   Confirm neither appears in public JSON or downloads. Approve a distinct redaction
   after manually reviewing its contents; confirm only that public document appears.
7. Download approved evidence; confirm a short-lived HTTPS URL. Revoke approval and
   try generating a fresh URL. Existing issued URLs may last until their expiry.
8. Inspect Network responses for all three APIs while signed out and as an owner:
   no storage paths, signed URLs, filenames, OCR, original IDs or private notes.
   Cross-project/draft details must return 404. Private discrepancies remain withheld.
9. Test narrow screens, keyboard navigation, focus indicators and a screen reader.
   All chart values must remain available as text. Simulate offline/API/storage errors
   and retry using Refresh public ledger.

## Remaining limitations and operational concerns

- Exact partial refunds and independent vendor-payment evidence are unavailable.
- Public findings cover published category overruns only, not withheld receipt findings.
- Approval is an existing maintainer attestation; software cannot guarantee that a
  human actually removed all personal information from an approved file. Inspect
  redactions and published vendor/descriptions before approval/publication.
- Snapshot requests and ledger pages are separately consistent transactions, not one
  shared snapshot across browser requests. Offset pages may shift under concurrent
  publication; refresh to reconcile changes.
- Reusing uncached Step 4 calculations for each page favors correctness over scale.
  Large projects may need query batching, rate limits and subsequently justified
  caching. Public downloads have the existing signed-URL expiry window.
- Live Supabase, hosted CI, browser/accessibility execution and deployment remain
  manual verification. No production credentials, migrations, deployment, commit
  or push are part of this task.
