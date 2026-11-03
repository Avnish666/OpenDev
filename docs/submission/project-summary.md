# OpenDev — Funding with inspectable accountability

OpenDev helps backers inspect how an open-source project's recorded funding,
published spending and delivery commitments relate to each other. Maintainers
publish campaigns, budgets, evidence and roadmap changes in one place.

## Problem

Campaign funding alone says little about reported expenses, promised deliverables,
changing deadlines or reward fulfillment. Repository activity is useful evidence,
but issue closure does not independently establish delivery.

## Solution and users

Visitors explore public campaigns. Backers inspect financial evidence, progress and
rewards. Maintainers connect public repositories, plan budgets and report spending
and commitments. Public dashboards and cited answers reuse authorized projections
of the same records while original receipts and review notes remain private.

## Core features and differentiators

Campaign/reward management; PayPal Sandbox order/capture and idempotent webhook
reconciliation; immutable exact refund observations with conservative unknowns;
reported expenses and approved-redaction metadata; private bounded receipt extraction;
GitHub observation snapshots; Bryntum Community roadmap and deadline history;
maintainer outcomes with samples; financial/development Community dashboards and
CSV; deterministic accountability answers with provenance citations and bounded
optional Ollama orchestration.

The differentiator is keeping monetary calculations deterministic, private source
material out of public tools, and assertions separate from independently verified
facts. No trust score, fraud determination, bank balance, escrow or multi-merchant
payout capability is claimed.

## Technology and present status

React/TypeScript/Vite; FastAPI, SQLAlchemy, psycopg, PostgreSQL and Alembic;
GitHub OAuth/REST; PayPal Sandbox REST (HTTPX, APIMatic-assisted development);
private Supabase storage; pypdf/PDFium/Tesseract; Bryntum Gantt Community;
AG Grid/Charts Community; optional isolated AG Studio 3.0.0 evaluation; optional Ollama.

The submitted material is a **local synthetic demonstration package**. Real
PayPal/webhook/Supabase/hosted OAuth and Ollama acceptance are unverified; public
deployment remains **NO-GO**. Sponsor rule compliance, prize eligibility, project
approval, a public URL and a completed video are not claimed.
