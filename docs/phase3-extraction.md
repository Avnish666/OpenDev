# Phase 3 Step 3 — Private Receipt Intelligence

## Implemented architecture

The baseline is deterministic and free: existing private Supabase object → bounded
authenticated download → size/hash/content revalidation → isolated local worker →
PyMuPDF text or Tesseract OCR → Pydantic observations → deterministic findings →
separate private PostgreSQL extraction/audit records. No paid AI API, local language
model, new service, Redis, Kafka or automatic public release is used.

Original upload, document authorization/redaction/publication, expense financial
summaries and PayPal processing are reused, not rebuilt. Extraction is restricted
to original documents; redacted publication copies return 409 so processing cannot
mistake an intentionally incomplete public copy for the original.

### Files

Created:

- `backend/app/models/receipt_extraction.py`
- `backend/app/schemas/extraction.py`
- `backend/app/routers/extractions.py`
- `backend/app/services/receipt/parser.py`
- `backend/app/services/receipt/findings.py`
- `backend/app/services/receipt/provider.py`
- `backend/app/services/receipt/pipeline.py`
- `backend/app/services/receipt/worker.py`
- `backend/migrations/versions/357405104f17_add_private_receipt_extractions_and_.py`
- `backend/tests/test_extractions.py`
- `frontend/src/components/ReceiptExtraction.tsx`
- `docs/phase3-extraction.md`

Modified model/router registration, `backend/app/services/storage.py` (authenticated
bounded download helper), `backend/requirements-app.txt`, `.github/workflows/ci.yml`
(OCR test runtime), `frontend/src/api/client.ts` (status-bearing errors), and
`frontend/src/components/ExpenseDocuments.tsx` (manager-only extraction controls).
No applied migration or payment-processing code is modified.

`ExtractionProvider` is an interface for a future provider; only `LocalProvider`
is instantiated. Adding a remote model is a separate reviewed task, not a config
flag that can silently send private documents away. Financial rules/comparisons
always stay in deterministic application code.

## Records, state and retries

Migration **357405104f17**, following 23145456c6e9, adds only:

- `receipt_extractions`: required extraction fields, a reported-expense snapshot,
  status constraint, document FK/index, and unique `(expense_document_id,
  extraction_version)` claim.
- `receipt_extraction_attempts`: extraction FK/index, triggering user FK, attempt
  status, sanitized error code, and started/completed timestamps.

The new migration refuses destructive downgrade. Review/apply only against a
verified local/test database; production migration requires explicit approval.
Existing migration history is unchanged.

Version `local-rules-v1` identifies the current rule/worker contract. Increment the
version whenever extraction semantics change after release. Repeating a completed
request reuses its record without downloading or OCR again. A failed record remains
failed until POST with `{"retry":true}`; attempts are appended rather than erased.
Failures never overwrite financial records or fabricate successful observations.

States are **pending → processing → completed/failed**. A durable pending row is
committed before processing. A transaction-scoped PostgreSQL advisory lock on a
**dedicated, open transaction/connection** admits one worker across application
instances using that database. Metadata commits use a separate connection, so they
do not release admission. This also avoids leaking session advisory locks through
transaction-pooling connections. Requests that find capacity occupied return 202
with the existing pending/processing record.

This is bounded **request-driven processing**, not a background queue. Pending
records do not run automatically. Press Extract again when capacity is available.
If the server restarts, an unfinished processing lease can be reclaimed after
**180 seconds**, recording the abandoned attempt as WORKER_RESTARTED and appending
another attempt. Active workers cannot be taken over while they hold admission.
No FastAPI BackgroundTasks durability claim is made.

All processing endpoints are synchronous FastAPI worker endpoints, keeping download,
DB waits and subprocess waits off the async event loop. Long requests can still be
interrupted by a client/proxy/free-instance restart. Fetch the private record and
retry according to its state; do not assume a disconnected request failed before
its durable result was stored. Two database connections are needed during work.

## Endpoints and privacy

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/api/documents/{document_id}/extract` | Project owner/maintainer only, authenticated session and trusted-Origin CSRF. Empty body or `{}` triggers initial processing; `{"retry":true}` retries a failure. Returns 200 terminal or 202 pending/processing. |
| GET | `/api/documents/{document_id}/extraction` | Private current-version observations/findings and attempt history; 404 if no current-version record exists. |
| GET | `/api/expenses/{expense_id}/discrepancies` | Owner/maintainer only; returns that expense's current-version extraction records/findings. |

Even approved, published evidence does **not** make its extraction public. Visitors,
backers, ordinary collaborators and maintainers of another project cannot retrieve
private snippets. Membership is checked on each read and again before returning a
processed result. Responses use no-store/no-referrer. Raw filenames, keys, storage
credentials, complete OCR text, or unfiltered parser errors are not exposed by the
extraction API. Small private evidence snippets are deliberately retained.

Storage reads use `/storage/v1/object/authenticated/{bucket}/{key}` with server
credentials through the existing Storage configuration, never a signed/public URL.
The bucket must still report private. Streamed and advertised sizes are bounded,
then SHA-256 and size must match the upload metadata. Existing isolated document
validation is reused before extracting. Corrupt/encrypted/unsupported content fails
safely, including objects that changed after upload. No live Supabase project was
accessed in automated tests.

## Limits and local dependencies

Verified development environment: Python 3.12.14, Pillow 12.2.0, Pydantic 2.14.2,
**PyMuPDF 1.26.7**, and `/usr/bin/tesseract` 5.5.0 with `eng`/`osd` data. PyMuPDF
1.26.7 has no Python runtime dependency set; latest 2.0 pulled unnecessary layout/
ONNX packages during evaluation, so those newly installed packages were removed
and 1.26.7 pinned. `pip check` reports no broken dependencies.

PyMuPDF is **AGPL/commercial dual-licensed**. The free baseline uses the AGPL route;
confirm the project's distribution/network-use license obligations before deployment.
No commercial license or paid service is purchased by this task.

- Existing input limit: 5 MiB (5,242,880 bytes), PNG/JPEG/PDF only.
- Private download: 64 KiB chunks, 20-second streaming deadline plus bounded HTTP
  connect/read waits; no following redirects.
- Existing validation worker: 256 MiB address space, five-second CPU limit and
  eight-second parent timeout; existing encrypted/active-PDF protections remain.
- Extraction: at most **five PDF pages**. More pages fail PAGE_LIMIT rather than
  silently returning a partial invoice total. Text extraction is preferred when a
  page has at least 30 text characters; sparse/scanned pages use OCR.
- Images retain existing 20-million-pixel input protection, are safely opened with
  Pillow, oriented, and downsampled for OCR. Rasterized PDF pages are bounded to
  roughly 2000 pixels on the longest side.
- Worker: 320 MiB address-space limit, 50-second CPU cap and 60-second parent wall
  timeout. Tesseract: fixed absolute binary, fixed `eng`/PSM 6/TSV arguments, one
  OpenMP thread and 12-second timeout per page. Commands are never built from text.
- TSV output capped at 2 MB; scratch-file writes capped at 8 MiB; text capped at
  100,000 characters/3,000 lines. The result schema limits snippets, items and pages.
  Worker output is checked against a 250 KB limit.
- Timeout kills the extraction process group, including OCR subprocesses. OCR scratch
  files live inside the parent-owned temporary directory, so normal failures and
  timeout cleanup remove downloaded files and full OCR text. A hard container/process
  crash can leave private temporary files until ephemeral disk cleanup; monitor `/tmp`.
- The parser/OCR processes inherit no application credentials. Resource isolation
  is not an OS security sandbox or a guarantee that a file is malware-free.

One active worker reduces load on a free Render instance but does not guarantee
that every valid file will fit its RAM. Tesseract and the parent also use memory;
worst-case files can fail resource limits or cause a platform restart. Rate-limit
triggers and monitor memory/DB connections before wider use. Only sanitized error
codes are stored, never parser tracebacks or raw receipt bodies.

For Linux/Docker runtime provisioning, install Tesseract and its English data before
starting the app (do not run this as a request-time operation):

```sh
apt-get update
apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng fonts-dejavu-core
python -m pip install -r backend/requirements-app.txt
/usr/bin/tesseract --version
/usr/bin/tesseract --list-langs
```

The build environment may require a Docker-based Render runtime to install OS
packages; a native free build must not assume sudo/apt is available. This task does
not deploy or change hosting. CI now installs the OCR runtime on its Ubuntu runner.
POSIX resource limits/process groups are required; Windows is not supported by this
worker implementation. No new model downloads, OCR API keys or paid API keys exist.

## Extraction rules, evidence and accuracy limits

All observations allow **null** with confidence unknown. Each supported field has
confidence and up to two sources with page, bounded text snippet and a bounding box
when available (PDF points or image pixels). No full text is stored. Coordinates
are evidence locators, not proof that OCR was correct.

English deterministic labels supported:

- Vendor/Merchant/Supplier/Sold by labels; Invoice Number/No/ID/# labels.
- ISO `YYYY-MM-DD` labelled document dates. Ambiguous numeric dates stay unknown.
- Explicit USD/EUR/GBP/CAD/AUD/CHF codes on currency or monetary lines. `$` alone
  is ambiguous and does not become USD automatically.
- Separate labelled grand/invoice total, subtotal, tax/VAT, discount, previous
  balance, amount paid and amount due. Amount due/paid/balances never substitute
  for grand total. Conflicting total/currency candidates remain null and are marked
  ambiguous. No rounding: accepted amounts use exactly two decimal places, parsed
  via Decimal to integer cents; unsupported separators/formats stay unknown.
- Explicit `Item: description 12.34` rows only. Complex tables/quantities are not
  inferred. An absent item is not invented.
- Explicit Paid/Unpaid/Partially Paid **document claims**; they never establish
  actual payment and never create contributions.

Digital labelled values get rule-confidence high; OCR confidence degrades with its
word confidence. Confidence is an indicator, **not a calibrated probability**.
This baseline deliberately leaves many ordinary unlabelled merchant receipts,
non-English layouts, handwritten/rotated/skewed poor scans, decimal-comma amounts,
ambiguous dates, multi-currency receipts and complex invoice tables unknown. It
cannot determine whether an invoice is authentic, a transfer occurred, or redaction
was done correctly. No general real-world accuracy percentage is claimed.

Synthetic labelled fixtures verify exact total 1234 cents, subtotal 1000, tax 234,
vendor and currency through digital PDF, scanned PDF, PNG and JPEG, using the real
local OCR executable. These fixtures are high-contrast English text; this is not
a representative receipt benchmark.

## Findings and financial integrity

Findings include code, severity, reported/extracted value, explanation, evidence
reference and review status `human_review_required`. Mismatches with high extraction
confidence are warnings; weak evidence is informational. The engine checks:

- exact integer amount and currency differences;
- normalized vendor and ISO date differences;
- missing vendor/date/currency/total;
- possible subtotal + tax − identified discounts versus grand-total inconsistency,
  without assuming unrecognized fees or discounts prove an error;
- same vendor/invoice identifier on another expense in the same project;
- existing exact-file hash duplicates in that project;
- published reported category spending over its allocated budget, reusing Step 1.

All are review prompts, **not fraud findings**. No extraction route edits an Expense,
its evidence status/publication, a contribution/capture, or a reward entitlement.
Observed cents never enter the authoritative financial ledger. Read results are
compared against the **current** reported expense and category budget; if a draft
changed after processing, `comparison_is_stale` flags the saved comparison snapshot.
Previously processed invoices also learn about later project duplicates without
re-downloading/OCR. Stored findings retain the completion-time comparison for audit.

## Tests and manual verification

Automated tests use only synthetic content, private HTTPX Storage mocks and newly
created isolated local PostgreSQL databases. They exercise the real local worker
and OCR, corrupt/encrypted/oversized/unsupported objects, exact totals amid multiple
amounts, unknown/weak values, mismatches, duplicates, permission/CSRF/cross-project
checks, pending capacity, stale-worker recovery, failed retries and independent-
session concurrent requests/retries. They verify timeout process-group cleanup and
that expense, completed contribution and entitlement records are unchanged.

To run locally: install `backend/requirements-dev.txt`, provision Tesseract as above,
set DATABASE_URL and TEST_DATABASE_URL to a fresh local `opendev_test_*` database,
apply migrations **only there**, then run `python -m pytest -q` and `alembic check`
from backend. The prepared `/workspace/opendev-setup/test-step7.py` harness creates
such a database and runs the full suite. Frontend checks: `npx tsc -b`,
`npm run build`, `npm run lint`. GitHub-hosted CI itself is not invoked by this task.

Manual verification after configuring the existing private Supabase service:

1. Apply the reviewed migration to a verified local/test database. Keep any Neon/
   production migration a separate, explicitly approved action.
2. Sign in as a project owner/maintainer. Upload a synthetic original with labelled
   vendor/date/total, then click Extract Receipt in the expense's private documents.
   Inspect processing state, observations/confidence/sources beside reported values,
   findings, and human-review warnings.
3. Repeat with a scanned PDF, PNG and JPEG. Upload missing-field and multi-total
   fixtures and verify null/uncertainty rather than invented values.
4. Retry completed work and confirm one record/attempt; fail a download and explicitly
   retry, confirming separate attempt history. Run concurrent requests from two tabs.
5. Interrupt/restart a worker. After three minutes retry and inspect WORKER_RESTARTED;
   confirm pending work does not claim to run automatically.
6. Test a collaborator, backer, visitor and owner of another project: all extraction
   results/snippets stay private even if the document has a public redacted version.
7. Compare ledger rows before/after and inspect the network: authenticated Storage
   downloads only, no signed URL creation, no model API calls, no expense/funding edits.
8. Review memory/timeouts on the actual free hosting runtime with synthetic documents.
   Confirm Tesseract binary/data availability and ensure logs do not capture snippets.

Live Supabase/browser/free-instance restart verification is not performed here.
Existing receipt redaction and financial validation remain separate human workflows.
No production secrets, production database changes, deployment, commit or push are
part of Phase 3 Step 3 implementation.

## Recorded validation results

- **137 backend tests passed, zero failed/skipped**: 24 extraction cases plus 113
  existing tests. Storage was mocked; OCR/PDF processing used the actual local tools.
- Upgrade of migration 357405104f17 passed on a newly created local database;
  `alembic check` reported no pending differences. No old migration was edited.
- Concurrent initial requests and failed-job retries on independent DB sessions
  produced one record per document/version and one worker attempt per retry wave.
- TypeScript checks, frontend production build and Oxlint passed. Two pre-existing
  AuthContext warnings and the existing TestClient HTTPX deprecation remain.
- Backend compilation, dependency compatibility (`pip check`) and diff whitespace
  checks passed. GitHub-hosted CI, live Supabase, browser E2E and Render restart/memory
  behavior were not executed here and remain manual verification requirements.
