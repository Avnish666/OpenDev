# Review-only same-origin deployment artifact

This configuration is prepared for review. It does not authorize deployment.
Step 3 adds required production startup checks and backend release controls. See
[the current preflight](../docs/phase7-deployment-preflight.md) and
[environment manifest](environment-manifest.json). Production defaults disable new
checkout/capture, receipt upload/extraction and LLM access; webhook reconciliation,
authorized reads and deterministic evidence remain. Provider credentials are still
required for existing integration paths. Do not enable controls as a substitute for
owner acceptance, credential rotation or deployment approval.
The release recommendation is **NO-GO**; see
[`docs/phase7-deployment-preparation.md`](../docs/phase7-deployment-preparation.md)
for the current refund migration, backup/recovery and acceptance runbook, and the
[blocker register](../docs/phase7-release-blockers.md).

Build from the repository root with Docker BuildKit:

```sh
docker build -f deploy/Dockerfile -t opendev-review:phase7 .
```

Managed environments with a TLS inspection proxy can supply the public trust
bundle as a BuildKit secret, without disabling TLS verification:

```sh
docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt \
  -f deploy/Dockerfile -t opendev-review:phase7 .
```

The root `.dockerignore` whitelists application/build inputs and excludes `.env`,
Git history, optional Studio, dependency directories and private key material.
The build installs only Community frontend dependencies. No Studio license or
backend secret is a build argument or Vite variable. Base images and apt packages
still float within their named versions: record immutable image digests and the
OS package inventory before an approved release. This is a repeatable build recipe,
not a promise of byte-for-byte reproducibility or complete dependency notices.

## Proposed free topology, after separate acceptance and approval

Use one Render Docker web service with its native HTTPS hostname. Its edge
terminates TLS and forwards requests to FastAPI; FastAPI serves the built React
application and `/api` on the same origin. This avoids cross-site fetch cookies
and requires neither a paid domain nor a new proxy service. Use Dockerfile path
`deploy/Dockerfile`, Docker context `.`, health path `/api/health`, and disable
automatic deployments during release preparation. Verify current Free availability,
terms and resource limits before creating anything; no Render service was created.

Configure these **runtime names in the host secret/configuration UI**, never Git:

| Name | Requirement |
| --- | --- |
| `APP_ENV` | `production`, so OAuth and session cookies are Secure. |
| `FRONTEND_URL` | Exact public HTTPS origin, no trailing slash or path. |
| `GITHUB_CALLBACK_URL` | That origin plus `/api/auth/github/callback`; match the OAuth registration exactly. |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | Separately provisioned/rotated OAuth application settings. |
| `DATABASE_URL` | Reviewed Neon PostgreSQL connection URL with TLS and a bounded connection budget. Do not use the historical example. |
| `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_WEBHOOK_ID`, `PAYPAL_MERCHANT_ID` | Sandbox application and expected receiving merchant only; callback path `/api/paypal/webhook`. |
| `SUPABASE_URL`, `SUPABASE_STORAGE_BUCKET`, `SUPABASE_SERVICE_ROLE_KEY` | Private bucket; backend-only service-role credential. |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Reachable approved private inference endpoint and tested tool-capable model, if enabled. `localhost` in Render does not reach a developer laptop. |

The platform supplies `PORT`. `FRONTEND_DIST=/app/frontend-dist` is built into this
image. `VITE_API_URL` is empty at build time; the browser uses relative `/api` paths.
The image runs one Uvicorn worker as UID 10001. Do not increase worker count without
reassessing worker-local quotas, validation admission, database pools and RAM.
Existing cookies remain HttpOnly/SameSite=Lax with Secure in production; CSRF
requires the exact configured Origin and CORS permits that one origin.

Startup runs the application only. Migrations, storage provisioning, model
downloads, secret rotation and live provider calls are not startup actions.
`/api/health` checks liveness; `/api/db-health` separately checks database access.
OCR has English language data. Ollama/model weights are not installed in the image.
PDF text/raster processing uses pypdfium2 5.14.0 (not PyMuPDF); retain its bundled
PDFium/dependency license notices. Code/migrations/assets are root-owned and readable,
not writable by the app UID. Decoder no-new-privileges/resource limits remain
incomplete exploit containment. See the Step 2 report before using this artifact.

Do not run the schema command against production in this step. A separately
approved operator must back up and rehearse the forward migration first, then run
`alembic upgrade head` once against the approved target before accepting traffic.
No downgrade of append-only audit history is a safe rollback strategy.

## Required acceptance before use

Record actual HTTPS login/callback/logout, cookie attributes, trusted/untrusted
Origins, CORS, two-account authorization, signed webhook replay, private storage
expiry/revocation, proxy disconnect/cancellation and cold starts. Rehearse database
restore and record retention/cleanup. Free-tier capacity must be measured with
concurrent uploads, validation, OCR, export and database queries; local idle memory
does not validate Render capacity. The image is not an OS sandbox for decoders.
If the free host cannot provide an approved containment/resource boundary, keep
public release blocked and evaluate an isolated owner-controlled free runner.
