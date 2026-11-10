# OpenDev frontend visual refinement

## Scope

Built on the existing PayPal-inspired OpenDev design at `9c31550`; the starting
working tree was clean. Changes are limited to frontend presentation, isolated
frontend tests and design documentation. No backend, API client, authentication
context, payment handler, model pipeline, database, migration or dependency version
was changed. No component was deleted; routing remains hash based.

An AST inspection confirmed all 17 existing async request-handler bodies remained
byte-for-byte identical across 11 UI modules. Real browser request assertions also
checked the existing project create/edit, reward, expense, roadmap, GitHub sync,
checkout and chat payloads. No commit, push or deployment was performed.

## Design changes

- Original data-free SVG/CSS workflow artwork, compact editorial hero, clearer
  feature strip and discovery transition. The brand message is retained.
- Refined navigation, active indicators, account dropdown, theme icon transition,
  mobile avatar fallback and keyboard dismissal.
- Page-scoped search, balanced responsive discovery cards, semantic project status,
  aligned repository/goal/action rows, and clearer pagination.
- Project overview, funding/budget panels and reward cards. Recorded funding and
  progress use the existing summary response and authoritative goal, with currency
  and integer guards; overfunded amounts remain visible while the visual bar caps.
- Three primary financial KPIs; the campaign goal remains immediately visible.
  Reconciliation details and source limitations remain accessible. Filters are
  labeled native disclosures, with readable scope summaries instead of raw JSON.
- Numbered project/reward/expense form sections and a desktop helper column.
  Form names, validation rules, submit functions and payloads are retained.
- Distinct chat messages, requested/returned execution indicators, source cards,
  refined composer, empty state and suggested questions; cancellation/retry and
  citation safety are unchanged.
- Timeline toolbar, read-only/manager labels, selected milestone and confirmation
  panel. Vendor scheduling, drag/resize, dependencies and save logic are unchanged.
- Contribution history, return/receipt summary, expense records, public evidence,
  GitHub controls and maintainer profile styling.
- Shared `PageHeading`, `SectionHeading`, `MetricCard`, `StatusBadge`, `FormSection`
  and `EmptyState`, plus `HeroVisual` and additions to the existing original icons.
- Central theme/typography/spacing/motion tokens, no remote fonts or stock images,
  and preserved light-default/saved-choice/cross-tab/storage-disabled behavior.

`DESIGN.md` documents product priorities, original identity, palette, system font
stack, type/spacing scales, layouts, component states, breakpoints, accessibility,
motion, data labeling and theme behavior.

## Actual browser verification

The unchanged application was rendered in local Chromium with isolated synthetic
API fixtures. No real financial records or provider accounts were used. A health
probe found no backend listener at `127.0.0.1:8000`, so the fixture approach explicitly
permitted by the brief was used. The browser test loads the real `index.html` and
`src/main.tsx`; screenshots are browser captures, not generated mockups.

All 23 scenes were rendered at 360, 390, 768, 1280 and 1440px in light and dark:
landing, discovery, project overview, rewards, empty chat, answered chat, timeline,
transparency, analytics, charts, public expense evidence, create project, account
menu, My Projects, maintainer profile, contribution history, funding return,
contribution receipt, edit draft, expense editor, reward editor, roadmap manager,
and GitHub sync controls. This is 230 scene/theme/viewport combinations.

Assertions checked page-level overflow, overlapping grid cards and application
button touch targets. The additional contract journey verified search/pagination,
form payloads, Sandbox order payload/idempotency key, explicit capture UI, requested
LLM/returned LLM labels, filters, account Escape/focus, long financial values at
360px and reduced motion. The final run recorded **zero runtime exceptions, zero
console error calls, and zero unhandled mock API requests**.

Representative screenshots were visually inspected and refinements made to goal
visibility, metric alignment, mobile account identity, filter composition and
scroll positioning. The original browser theme smoke separately verifies keyboard
mode switching, storage persistence, cross-tab sync, opposite OS preference,
blocked storage, SDK theme changes, error retry and anonymous route protection.

Measured token contrast: light body 16.84:1, muted text 6.06:1, primary button 4.98:1,
input boundary 3.22:1; dark body 18.01:1, muted text 8.81:1, primary button 5.39:1,
input boundary 3.57:1. These are tested token pairs, not a claim of a complete
third-party widget accessibility audit.

## Screenshots and evidence

- 13 before captures: `/workspace/work/design-before/`.
- 94 matrix/stress/empty-state captures after refinement:
  `/workspace/work/design-matrix/`.
- Updated matching theme-smoke captures: `/workspace/work/design-after/`.
- Machine-readable scene/contract evidence: `design-matrix/evidence.json` under
  that work directory; `matrix-evidence.json` separately records the viewport run.
- Bundle measurements and request-handler audit are retained in the same work
  directory. These are local QA outputs, not application assets or production data.

## Tests

Baseline: 87 unit tests, typecheck, lint, production build and theme browser smoke
passed. Final results:

| Check | Result |
| --- | --- |
| `npm test` | 89 passed; original assertions retained; two funding-progress regressions added |
| `npx tsc -b` | Passed |
| `npm run lint` | Passed; same two pre-existing AuthContext warnings |
| `npm run build` | Passed; existing large lazy SDK chunk warnings remain |
| `npm run test:design-browser` | Passed: complete viewport/theme matrix and exact request contracts |
| `npm run test:theme-browser` | Passed |
| `node tests/browser-chat-smoke.mjs` | Passed: modes, citations, retry, cancellation, rate limits, privacy, mobile |
| `node tests/browser-analytics-smoke.mjs` | Passed: Community charts/grid, filters, CSV, license gate and error/empty states |
| `npm run test:gantt-browser` | Passed: real drag/resize proposals, confirmation, version conflict, mobile/read-only boundaries |
| `git diff --check` | Passed |

Existing source-transpilation test harnesses were extended only to compile the new
shared UI dependency. No original assertions were removed or relaxed. An existing
analytics smoke assertion caught the funding goal being hidden by a disclosure;
the UI was corrected. A simultaneous-browser startup failure was resolved by
running SDK checks sequentially without changing that test.

## Bundle measurement

Measurements use emitted files from identical production builds and Node
`gzipSync` defaults for both snapshots. kB means 1,000 bytes. The total below covers
JS/CSS, including lazy SDK chunks; unchanged vendor font files are excluded.

| Asset group | Before | After | Raw change | Gzip before → after |
| --- | ---: | ---: | ---: | ---: |
| Initial application JavaScript | 318.27 kB | 303.31 kB | -14.96 kB | 92.27 → 89.55 kB |
| Initial application CSS | 19.20 kB | 42.38 kB | +23.18 kB | 5.05 → 9.16 kB |
| All emitted JavaScript/CSS | 5276.12 kB | 5325.86 kB | +49.74 kB | 1512.84 → 1526.04 kB |

Initial JavaScript fell by 4.7% by deferring the expense and maintainer screens;
existing chat, analytics and Gantt lazy loading remains intact. The added design
styles increased CSS, so combined initial JS/CSS gzip transfer rose by about 1.39
kB. Across all emitted JS/CSS, gzip grew by about 13.20 kB (0.9%). No new runtime
package, downloaded font, raster illustration or animation library was added.

## Remaining limits

- Optional licensed AG Studio is not installed here; its default license/activation
  gate was tested, but licensed Studio rendering was not visually verified.
- External GitHub OAuth, PayPal, storage and real model operation were not exercised
  in this UI-only task. Existing request behavior was preserved and tested locally.
- Large Gantt/Community SDK chunks remain lazy loaded. No broad-device performance
  claim or Safari/Firefox acceptance is made from Chromium screenshots.
- Existing authentication lint warnings were left unchanged because authentication
  logic is outside scope. Existing filter URL persistence behavior is retained.

## Start the frontend

With the existing backend available on port 8000 and its allowed frontend origin
configured as usual:

```sh
cd /workspace/OpenDev/frontend
VITE_API_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/#/explore`. Frontend fixture browser checks do not need a
backend or financial records. With Chromium installed, run:

```sh
OPENDEV_SCREENSHOT_DIR=/tmp/opendev-design npm run test:design-browser
```

## Complete file inventory

- `DESIGN.md`
- `docs/frontend-visual-refinement.md`
- `frontend/package.json`
- `frontend/src/App.css`
- `frontend/src/App.tsx`
- `frontend/src/components/Accountability.tsx`
- `frontend/src/components/AnalyticsExport.tsx`
- `frontend/src/components/FinancialFacts.tsx`
- `frontend/src/components/GitHubProgress.tsx`
- `frontend/src/components/HeroVisual.tsx`
- `frontend/src/components/Icon.tsx`
- `frontend/src/components/ProjectAIChat.css`
- `frontend/src/components/ProjectAIChat.tsx`
- `frontend/src/components/ProjectAnalytics.css`
- `frontend/src/components/ProjectAnalytics.tsx`
- `frontend/src/components/ProjectAnalyticsCommunity.tsx`
- `frontend/src/components/ProjectProgress.tsx`
- `frontend/src/components/Roadmap.tsx`
- `frontend/src/components/RoadmapTimeline.css`
- `frontend/src/components/RoadmapTimeline.tsx`
- `frontend/src/components/Transparency.tsx`
- `frontend/src/components/UI.tsx`
- `frontend/src/components/auth/GithubLogin.tsx`
- `frontend/src/design/analyticsTheme.ts`
- `frontend/src/design/product.css`
- `frontend/src/index.css`
- `frontend/src/pages/Expenses.tsx`
- `frontend/src/pages/Funding.tsx`
- `frontend/src/pages/Maintainer.tsx`
- `frontend/src/pages/Projects.tsx`
- `frontend/tests/analytics.test.mjs`
- `frontend/tests/browser-design-smoke.mjs`
- `frontend/tests/design-fixture.mjs`
- `frontend/tests/transparency.test.mjs`
