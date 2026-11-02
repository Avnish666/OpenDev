# Phase 3 Step 2 — Private Receipt and Invoice Storage

## Implemented scope

Supabase Storage holds private file bytes; the application's existing PostgreSQL
connection (Neon in deployment) holds document metadata. No production database,
Supabase project or bucket was accessed or created during implementation. Live
Supabase credentials/bucket are absent, so real storage behavior remains unverified.
The existing payment processing and expense financial semantics are unchanged.
No AI extraction, automatic approval, antivirus guarantee or payment verification
is included. All uploaded content and filenames remain untrusted.

### Files and migration

New backend files:

- `app/models/expense_document.py`
- `app/schemas/document.py`
- `app/services/documents.py`
- `app/services/document_validation_worker.py`
- `app/services/storage.py`
- `app/routers/documents.py`
- `tests/test_documents.py`
- `migrations/versions/23145456c6e9_add_private_expense_documents.py`

Model/router registration extends `app/models/__init__.py` and `app/main.py`.
`requirements-app.txt` adds Pillow 12.2.0 and pypdf 6.12.0 for parsing, not AI.
New frontend `components/ExpenseDocuments.tsx` and `pages/Expenses.tsx` provide
receipt selection/upload/download, publication review, and a minimal expense
create/edit/publish interface (Step 1 had no frontend expense interface). Project
pages embed it; the API client adds a binary-upload helper and CSS styles selects.

Revision `23145456c6e9` follows `d488822839b2`. It only creates `expense_documents`,
indexes and constraints. Required metadata fields are present, with RESTRICT FKs
to expense/uploader, unique random storage key, SHA-256 format/MIME/size checks,
and private/published status constraints. Additional `redacted_from_id`,
`approved_by` and `approved_at` preserve explicit human redaction review. The DB
forbids publishing originals without a redacted-source/reviewer relationship.
The new migration refuses destructive downgrade; old migrations are unchanged.

## API contracts

All write endpoints use existing GitHub session authentication, project owner/
maintainer authorization and trusted-Origin CSRF protection. Ordinary collaborators
and managers of another project are denied. Missing/private IDs return 404 on reads;
permission is checked before Storage is contacted or a URL is signed.

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/api/expenses/{expense_id}/documents` | Streams one file, validates actual bytes, creates private metadata/object; 201. Optional `redacted_from_id=<UUID>` links a separately redacted candidate to a document on the **same expense**. |
| GET | `/api/expenses/{expense_id}/documents` | Managers see their private documents; public callers see only explicitly approved/published redacted documents on published expenses/public projects. `limit` 1–100 (default 20), `offset` >=0. |
| GET | `/api/documents/{document_id}/download` | Authorizes caller, verifies bucket privacy, returns `{url, expires_in:60}` for a signed attachment download. |
| POST | `/api/documents/{document_id}/publish` | Additional human-review endpoint. Requires exact boolean `{ "redaction_reviewed": true }`, a separate redacted source, published expense and visible project. |
| POST | `/api/documents/{document_id}/unpublish` | Makes the evidence private and clears approval. Already issued links can work until their 60-second expiry. |

**Upload is a raw binary body, not multipart/form-data.** This avoids accepting a
large multipart request into a parser before the application can reject it.
Supply `X-Filename` as the percent-encoded original filename. Browser code sends
one File directly; authentication cookies and Origin are handled as existing API
requests. Content-Type is advisory and never trusted for validation. Metadata,
publication status, uploader and storage keys are not accepted from clients.

Example against a **local/test** backend, using your own authenticated browser
session through the UI, or equivalent cookie-authenticated API client:

```http
POST /api/expenses/123/documents
Origin: <exact FRONTEND_URL>
X-Filename: invoice.pdf
Content-Type: application/pdf

<raw PDF bytes>
```

Metadata responses omit storage keys, hashes, role credentials and signed URLs.
Managers get a `duplicate_in_project` flag computed by SHA-256 across that project's
expenses; duplicates are flagged, not overwritten or silently rejected. Public
callers do not receive duplicate flags that could disclose private evidence.
Signed URLs inherently contain the random object path and are bearer capabilities;
that is the one necessary storage-key disclosure. Do not log or share them.
Responses use `Cache-Control: no-store` and `Referrer-Policy: no-referrer`.

## Upload security and publication

- Limit: **5 MiB (5,242,880 bytes)**, nonempty. Both advertised Content-Length and
  actual streamed bytes are checked. No `request.body()` or multipart buffering.
  A temporary file is removed on success/failure; stream deadline is 20 seconds.
- UUID object paths are independent of expense IDs and filenames. Filename path
  segments are removed; controls/overlong names rejected. No upserts or client keys.
- SHA-256 is computed incrementally during streaming. Full image/PDF decoding
  rejects extension-only spoofing, truncated content and invalid parser structures.
- The validator runs in a separate POSIX/Linux process with no inherited credentials,
  256 MiB address-space cap, five-second CPU limit and eight-second parent timeout.
  Diagnostics are discarded; no contents/metadata are logged. This contains resource
  abuse but is not an OS security sandbox or a malware scan.
- PNG/JPEG decoding is capped at 20 million pixels; trailing data is rejected.
  PDFs must be unencrypted, parse strictly, contain 1–100 pages and end correctly.
  Forms, JavaScript, open actions, launch actions and attachments are rejected.
  Some otherwise-valid interactive invoices will be rejected by this conservative
  policy; export a flattened static PDF/image instead.
- Originals **always remain private**. Prepare a redacted file locally using proper
  redaction, not a visual overlay alone; remove hidden text, metadata and secrets.
  Upload it as a separate candidate, review it and explicitly approve publication.
  Identical bytes cannot be declared a redacted version of the source.
- Review is a human attestation, not technical proof of correct redaction. The UI
  warns about hidden data. Public evidence also requires a published expense and
  project status active/paused/completed. The expense's evidence_status stays
  `unverified`; document existence/publication never proves a transfer.
- Files are offered as attachment downloads with generated safe download names,
  not embedded previews. Users must still treat downloaded documents as untrusted.

## Supabase configuration (manual, before live verification)

1. Use a Supabase project on the available free plan and create a **private** bucket,
   for example `expense-evidence`. Do not enable public access. Set its allowed MIME
   types to application/pdf, image/png and image/jpeg and size limit to 5 MiB.
   Do not add anonymous/browser read, list, write or update policies for this bucket.
   Browser users access evidence only through the backend authorization routes.
2. Configure server-side environment variables through secure environment settings:
   `SUPABASE_URL=https://<project-ref>.supabase.co`, `SUPABASE_STORAGE_BUCKET`, and
   `SUPABASE_SERVICE_ROLE_KEY`. Never put the service-role key in Vite variables,
   source code, logs, chat, or a committed environment file. The adapter supports
   standard hosted Supabase project URLs; local HTTP/custom domains are not enabled.
3. Allow HTTPS egress to that exact project hostname in cloud environment settings.
   No secret requirement was guessed because the project hostname is unknown.
   Bucket privacy is checked before **each upload and signed URL**, failing closed
   if Storage says public or is unavailable. Keep bucket configuration private:
   a service-role key bypasses RLS and must remain backend-only.
4. Install `backend/requirements-dev.txt` in the Python 3.12 environment. Receipt
   validation requires POSIX resource limits (Linux/Render/Codex Cloud supported).
   Restrict incoming body size/request rate at the deployment proxy as well; the
   application bound does not replace infrastructure resource controls.
5. Review the new migration. Apply `alembic upgrade head` only after verifying a
   local/test DATABASE_URL. Production/Neon migration is a separate approved action.
   Start existing FastAPI/Vite processes with FRONTEND_URL/VITE_API_URL configured.

Official Storage source checked at
https://github.com/supabase/storage/tree/327681449182ade2f9173c968dd8e8ee3c9888fd :
`src/http/routes/object/createObject.ts` (`x-upsert:false` raw upload),
`getSignedURL.ts` (`expiresIn`, `signedURL`), `deleteObjects.ts` (`prefixes` cleanup),
and `bucket/getBucket.ts` (`public` flag). Backend uses HTTPX REST, not guessed SDK
methods. No Supabase SDK or unrelated package was installed.

## Failure recovery

Database and object storage cannot share one atomic transaction. The service
validates first, locks/rechecks expense permission, uploads a new object, flushes
metadata and commits. If metadata persistence fails and no committed row exists,
the new object is deleted. An upload with an uncertain network outcome also tries
cleanup. A provider collision is **never deleted**, preventing removal of an
existing object. Existing objects are never intentionally overwritten.

If cleanup itself fails, the request returns 503 with a document correlation ID
and a sanitized operator log. If a COMMIT outcome cannot be determined because the
database is unavailable, the object is retained rather than risking deletion of
committed evidence. Operators must reconcile those orphan/uncertain objects by
comparing private bucket objects with document metadata; no background cleanup
worker is included. This requires monitoring; an application crash between upload
and metadata persistence can also leave an orphan. Never log secrets or contents
while performing reconciliation.

## Automated and manual verification

Tests use a freshly migrated isolated local PostgreSQL database and HTTPX-mocked
Supabase; no Neon or real bucket is used. The actual resource-limited parser runs
for test PNG/JPEG/PDF uploads. Tests cover authentication/roles, CSRF, IDOR, content
spoofing/truncation/active PDFs, advertised/chunked size limits, hash/UUID metadata,
project duplicates, original privacy, strict human review, source expense binding,
public expense/project visibility, unpublishing, 60-second signing, bucket privacy,
metadata-failure cleanup, cleanup failure reporting and collision protection.

From backend, run pytest against a migrated local `opendev_test_*` database with
DATABASE_URL and TEST_DATABASE_URL set. The prepared
`/workspace/opendev-setup/test-step7.py` harness creates a fresh database, upgrades
it, runs `alembic check`, then the entire suite. From frontend run `npx tsc -b`,
`npm run build`, `npm run lint`.

Manual verification still required after configuring Supabase: upload all three
valid formats; reject invalid/oversized ones; inspect object privacy and UUID keys;
confirm no overwrite; test owner/maintainer/backer/anonymous access and another
project's document UUID; publish only an approved redacted candidate on a published
expense; download and wait more than 60 seconds to confirm URL expiry; unpublish
and confirm no new URL; simulate database/storage failure and inspect cleanup.
Do not use actual sensitive receipts for the first live verification.

No automated browser end-to-end test was run. No production secrets, production
migrations, deployment, commits or pushes are part of this task.

### Validation results

- **113 backend tests passed, zero failed/skipped**: 26 document/security cases plus
  the 87 existing project/payment/expense cases.
- Migration upgrade succeeded on newly created local PostgreSQL; `alembic check`
  reports no model drift. No old migration was changed or downgraded.
- Frontend TypeScript, production build, and Oxlint pass, with two existing
  AuthContext warnings. Backend TestClient retains its existing HTTPX deprecation.
- Backend compilation and `git diff --check` pass.
- Supabase itself, signed-URL expiry over real time, and browser end-to-end uploads
  remain unverified until secure server configuration and a private bucket exist.
