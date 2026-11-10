# OpenDev visual identity

## Direction

Premium fintech meets developer infrastructure. Build on the existing original
OpenDev bracket mark, clear blue actions, navy surfaces and the message:
“Fund open source. Track every milestone.” PayPal/Pentagram inform confident
composition; Linear informs density and control precision; Stripe informs financial
hierarchy; GitHub informs repository and evidence presentation. No proprietary
logos, fonts, illustrations or copied layouts are used.

## Product priorities

Visitors discover public projects. Backers inspect funding, expenses and delivery
before choosing a reward. Maintainers create drafts and publish evidence. The UI
must distinguish recorded funding, reported expenses and calculated differences.
A receipt is not payment verification; delivery is a maintainer assertion. Sandbox
labels stay visible. Model execution badges always describe actual returned mode.

## Tokens and typography

`frontend/src/index.css` owns colors, spacing, typography, radius, shadow and motion
tokens. `frontend/src/design/analyticsTheme.ts` owns the SDK's resolved chart/grid
colors, which canvas renderers cannot inherit as CSS variables. Keep these palettes
aligned. System typography avoids font downloads, licensing ambiguity and layout
shifts; no external font service or new runtime dependency is required.

- Body: 15px / 1.65; compact supporting text: 12–13px / 1.6.
- Hero: responsive 44–72px, tight tracking, 1.06 line height.
- Page title: 32–48px; section: 24–30px; card: 17–20px.
- Money and metric values use tabular numerals and restrained tracking.
- Spacing: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64px.
- Radii: controls 10px, cards 16px, major panels 24px, status pills fully round.
- Shadows: a subtle resting shadow and a modest interactive elevation.

Light surfaces are white on cool neutral backgrounds with navy text. Dark surfaces
are layered navy on #090F1C with bright readable text. Muted text and primary button
labels meet 4.5:1 target contrast; form boundaries target 3:1. Blue communicates
actions; green, amber and red communicate actual semantic state only. Drafts and
unknown states use neutral badges.

## Layout and shared primitives

The app container is at most 1440px with responsive 18–64px side gutters. Navigation
stays compact and sticky; project navigation scrolls within its own region when
necessary. Sections have a title, short context and nearby actions. Long evidence
and calculation details remain available in clearly labeled native disclosures.

`components/UI.tsx` provides PageHeading, SectionHeading, MetricCard, StatusBadge,
FormSection and EmptyState. `HeroVisual.tsx` is a lightweight, explicitly labeled
workflow illustration, not a financial dashboard or fictional campaign. New custom
SVG icons extend the existing original Icon component.

- Discovery: clear page-scoped search, consistent cards, aligned goal/CTA rows.
- Project: overview, funding/budget, reward tiers, progress/evidence, assistant and
  analytics. Existing subnavigation and lazy feature entry points remain usable.
- Forms: numbered field groups, readable hints, unchanged names/constraints/payloads,
  and a secondary checklist column on wide screens.
- Financial dashboard: primary recorded-funding/spending/difference KPIs first;
  reconciliation details and source limitations remain visible below. Filters are
  grouped into expense, evidence and development controls. No filters silently
  change financial scope.
- Tables: exact values, clear headers, local horizontal scrolling, tabular numerals.
- Chat: distinct messages, visible requested/returned execution mode, question chips,
  structured source cards, clear limitations and a calm input composer.
- Gantt: style the surrounding toolbar/details/confirmation; preserve the vendor
  widget and scheduling behavior. Its native theme follows explicit color-scheme.
- Checkout/history: status and reward entitlement are separate. Sandbox remains
  explicit; no frontend state implies successful capture.

## Responsive and accessibility rules

Check 360, 390, 768, 1280 and 1440px in both themes. Cards use one column on phones,
two on tablets and up to three where appropriate. Forms stack on phones; desktop
helper panels collapse into normal flow. No page-level horizontal scrolling;
financial tables, project navigation and Gantt own their scroll regions.

Touch targets are at least 44px. Preserve semantic headings, field labels, alerts,
focus rings and native details behavior. The mobile menu supports focus entry,
Escape, closing on navigation and keyboard return. The account dropdown supports
keyboard dismissal. Respect prefers-reduced-motion and avoid motion as an indicator
of payment, delivery or AI success.

## Motion and performance

Use 160–220ms color/elevation transitions and a small theme icon transition. The
hero uses CSS/SVG only with gentle connector emphasis. Reduce motion disables all
nonessential animations. Keep AG/Bryntum and chat lazy-loaded, avoid image/font
requests and reserve loading space. Record build output before and after; report
large vendor chunks as an existing limitation, not as a new optimization claim.

## Theme behavior

Light remains the default. The explicit saved choice wins over device preference.
The existing early HTML bootstrap, guarded localStorage writes, cross-tab sync and
storage-disabled behavior are preserved. All application surfaces and SDK themes
follow the same explicit selection.

## Scope and validation

This refinement changes frontend presentation and documentation only. Backend,
OAuth/payment logic, API contracts, form payloads/validation, model selection,
financial calculations, database records and migration history remain untouched.
Synthetic fixtures live only in isolated browser tests; never ship fixture data as
application content. Capture before/after renders, exercise both themes at all five
widths, verify interaction requests, run npm test, tsc -b, lint and production build.
No commit, push or deployment is part of this task.
