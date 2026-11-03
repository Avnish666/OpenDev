# Sponsor integration evidence

This matrix describes inspected implementation and local evidence. Current hackathon
rules, sponsor-specific thresholds, submission eligibility and prize approval were
**not supplied or independently verified**. The owner must check them before selecting
tracks or making compliance claims. No public demo URL is assumed.

| Integration / purpose | Actual package or API | Source evidence | Implementation and verification | Licensing / distribution | Exact local demo |
| --- | --- | --- | --- | --- | --- |
| PayPal Sandbox campaign backing and rewards | Orders v2, Payments/refunds and Webhooks REST via HTTPX; fixed Sandbox endpoints | `backend/app/services/paypal.py`, `services/funding.py`, `routers/funding.py`, `models/funding.py`; `docs/phase2-paypal.md` | Order/capture/signature/refund/reversal/idempotency logic implemented; real DB/normal-cookie synthetic HTTP journey and fake provider transports tested. Real buyer approval/capture/refund and genuine webhook delivery **NOT RUN**. | Provider API terms/Sandbox account acceptance must be checked; no live-money, escrow or multi-merchant payout claim. | Open campaign reward tier and ledger. Show seeded synthetic amounts; do not click checkout. Explain actual server pricing, signature verification and entitlement code. For workflow evidence run the named cookie HTTP journey with mocked providers in the separate test process. |
| APIMatic assistance for PayPal development | APIMatic PayPal Context Plugin 0.4.1, documented setup/guidance | `docs/paypal-context-setup.md`, `docs/phase2-paypal.md`, and actual HTTPX PayPal implementation above | Prior setup/guidance integration is documented. This is development assistance, not an APIMatic production dependency or a claim a generated SDK is used. Plugin live availability in another session is not assumed. | Owner must verify hackathon attribution/evidence requirements and applicable plugin terms; no paid service used. | Show context-setup document and connect its guidance to fixed-host REST implementation and test evidence. Do not invent a plugin screenshot or tool execution from this step. |
| Bryntum Gantt roadmap visualization | `@bryntum/gantt-community`, `gantt-react-community`, `core-community` 8.0.0-beta.1 | `frontend/package.json`, `src/components/RoadmapTimeline.tsx`, `src/api/gantt.ts`, roadmap/dependency APIs; `docs/phase4-bryntum.md` | Real Community tasks/dependency visualization, read-only visitor view and authorized edit/confirm flows implemented. PostgreSQL/Chromium acceptance and genuine Step 6 screenshot exist; fixture GitHub data is not live. | Installed Community packages declare MIT. Preserve bundled notices and verify beta/device behavior; do not substitute commercial Bryntum licensing claims. | Campaign → Roadmap / timeline → Timeline → Month; point to task states and dependency, then Milestone list → Read milestone history. [Actual capture](screenshots/05-bryntum-roadmap.png). |
| AG Studio analytics evaluation | `ag-studio` and `ag-studio-react` 3.0.0, with isolated `ag-grid-enterprise` 36.2.0 and `ag-charts-enterprise` 14.2.0 | `frontend/studio/package.json`, separate lockfile, `ProjectAnalyticsStudioRenderer.tsx`, dashboard definitions, `vite.config.ts` | Real optional SDK adapter/data contracts implemented. Local loopback evaluation browser journeys cover real rendering/switching; notices stay visible. This is not the default Community renderer. No Studio screenshot or public deployment is claimed for this package. | Commercial/evaluation terms. No public entitlement verified. Only perform permitted local evaluation; recording/public sharing rights need separate terms review. Neither flags nor a nonempty key grants rights. | If permitted and already installed, from backend run `TEST_STUDIO=1 PHASE6_BROWSER_JOURNEY=1 python -m pytest -q tests/test_analytics_release.py -k real_public` against a migrated local test DB with testing features enabled only for that process. Existing harness starts loopback Vite/Chromium and selects Studio, then Community. For optional manual evaluation use an isolated build only on loopback; never replace the default demo/image. |
| Community analytics fallback | AG Grid Community 36.2.0; AG Charts Community/React 14.2.0 | `ProjectAnalyticsCommunity.tsx`, `DevelopmentCommunity.tsx`, `FinancialFacts.tsx`, `DevelopmentFacts.tsx`, `api/analytics.ts`, backend analytics/exports | Financial/spending/development/maintainer presets, grids/charts/filter parity and CSV tested. Actual Step 6 screenshots are Community, not Studio evidence. | Community declarations MIT; preserve notices. Normal frontend lock/build/image excludes Studio/Enterprise. | `/#/projects/<id>/analytics`, leave Renderer=Community, change dashboard preset, apply Hosting filter, download expenses CSV, reset. |

## Optional installation and evaluation commands

The default demo needs only root frontend `npm ci`. If the owner chooses a permitted
local Studio evaluation, review current terms first and then install **only** its
separate dependency graph: `npm ci --prefix frontend/studio`. No installation is
needed again when it is already present. Build only into a separate directory:

```sh
cd frontend
ANALYTICS_STUDIO_EVALUATION=true npm run build -- --outDir /tmp/opendev-studio-evaluation
```

A permitted local evaluation is not a license for public publication of these assets.
Keep the default Community build and Docker context free of this graph. Leave genuine
trial notices visible. The existing loopback browser harness is the preferred exact
repeatable evaluation; use the actual terms to decide whether a recorded segment can
be shared with judges. If that cannot be confirmed, omit Studio from the video and
show the implementation/configuration with its verification/rights caveats.

## Owner rule check

Open the actual current competition rules and each sponsor track page; record URLs,
review date, required integration/version/evidence, permitted team/project/license
conditions, video duration and hosting/accessibility requirements. Map each requirement
to inspected evidence above. If a required live integration is unverified, say so and
seek the organizer's permitted local-demo alternative. Never mark sponsor criteria
satisfied from package installation or a mocked test alone.
