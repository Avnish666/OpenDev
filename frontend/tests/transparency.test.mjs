import { progressFixture } from './progress-fixture.mjs';
import { before, after, test } from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let folder, displayMoney, transparencyAPI, Transparency, GitHubProgress, Roadmap, MaintainerProfile, MetricCards, credibility, ProjectProgress, ProgressOverview, GitHubActivity, progress;
before(async () => {
  folder = await mkdtemp(join(import.meta.dirname, '.compiled-'));
  for (const file of ['components/UI.tsx', 'api/client.ts', 'api/transparency.ts', 'components/Transparency.tsx', 'components/GitHubProgress.tsx', 'components/Roadmap.tsx', 'api/credibility.ts', 'pages/Maintainer.tsx', 'api/progress.ts', 'components/ProjectProgress.tsx']) {
    let source = await readFile(new URL('../src/' + file, import.meta.url), 'utf8');
    source = source.replace('import.meta.env', "({ VITE_API_URL: 'https://api.invalid' })");
    source = source.replace("import './Transparency.css';", '');
    let { outputText } = ts.transpileModule(source, { compilerOptions: {
      target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX,
    }});
    outputText = outputText.replace(/from '(\.[^']+)'/g, (_, path) => `from '${path}.js'`);
    const destination = join(folder, file.replace(/\.tsx?$/, '.js'));
    await mkdir(join(destination, '..'), { recursive: true });
    await writeFile(destination, outputText);
  }
  ({ displayMoney, transparencyAPI } = await import(pathToFileURL(join(folder, 'api/transparency.js'))));
  ({ default: Transparency } = await import(pathToFileURL(join(folder, 'components/Transparency.js'))));
  ({ default: GitHubProgress } = await import(pathToFileURL(join(folder, 'components/GitHubProgress.js'))));
  ({ default: Roadmap } = await import(pathToFileURL(join(folder, 'components/Roadmap.js'))));
  ({ default: MaintainerProfile, MetricCards } = await import(pathToFileURL(join(folder, 'pages/Maintainer.js'))));
  credibility = await import(pathToFileURL(join(folder, 'api/credibility.js')));
  ({ default: ProjectProgress, ProgressOverview, GitHubActivity } = await import(pathToFileURL(join(folder, 'components/ProjectProgress.js'))));
  progress = await import(pathToFileURL(join(folder, 'api/progress.js')));
});
after(async () => { if (folder) await rm(folder, { recursive: true, force: true }); });

test('exact minor-unit formatting and unsafe integer guard', () => {
  assert.equal(displayMoney(1234, 'USD'), '12.34 USD');
  assert.equal(displayMoney(-1, 'USD'), '-0.01 USD');
  assert.match(displayMoney(Number.MAX_SAFE_INTEGER + 1, 'USD'), /safe browser display range/);
});

test('public UI renders its accessible loading state without an auth provider', () => {
  const html = renderToStaticMarkup(createElement(Transparency, { projectId: 5 }));
  assert.match(html, /Financial Transparency/);
  assert.match(html, /role="status"/);
  assert.match(html, /Loading financial transparency/);
});

test('public client uses ledger contracts, encoded filters and safe errors', async () => {
  const original = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => ({ project_id: 5, items: [], total: 0 }) };
  };
  try {
    await transparencyAPI.overview(5);
    const result = await transparencyAPI.ledger(5, new URLSearchParams({ q: '% & private', limit: '10', offset: '0' }));
    await transparencyAPI.detail(5, 8);
    assert.equal(result.total, 0);
    assert.match(calls[0].url, /\/api\/projects\/5\/transparency$/);
    assert.match(calls[1].url, /q=%25\+%26\+private/);
    assert.match(calls[2].url, /\/ledger\/8$/);
    assert.ok(calls.every(c => c.options.method === 'GET' && c.options.body === undefined));
    globalThis.fetch = async () => ({ ok: false, status: 404, json: async () => ({ detail: 'Project not found' }) });
    await assert.rejects(transparencyAPI.overview(5), /Project not found/);
  } finally { globalThis.fetch = original; }
});


test('GitHub loading and maintainer-only sync controls render without authentication context', () => {
  const visitor = renderToStaticMarkup(createElement(GitHubProgress, { projectId: 5, canManage: false, active: true }));
  const manager = renderToStaticMarkup(createElement(GitHubProgress, { projectId: 5, canManage: true, active: true }));
  assert.match(visitor, /Loading repository progress/);
  assert.doesNotMatch(visitor, />Sync GitHub</);
  assert.match(manager, />Sync GitHub</);
  assert.match(visitor, /does not prove funded deliverables/);
});


test('Roadmap renders public loading and maintainer-only create controls', () => {
  const visitor = renderToStaticMarkup(createElement(Roadmap, { projectId: 5, canManage: false }));
  const manager = renderToStaticMarkup(createElement(Roadmap, { projectId: 5, canManage: true }));
  assert.match(visitor, /Loading roadmap/);
  assert.doesNotMatch(visitor, />Create milestone</);
  assert.match(manager, />Create milestone</);
  assert.match(visitor, /never automatically mark delivery/);
});


test('maintainer profile loads publicly without an auth provider', () => {
  const html = renderToStaticMarkup(createElement(MaintainerProfile, { userId: 1 }));
  assert.match(html, /Loading public maintainer profile/);
  assert.match(html, /No trust score/);
});

test('new and unsupported indicators are not rendered as zero reputation', () => {
  const base = { key: 'delivery', label: 'Delivery', numerator: 0, denominator: 0, sample_size: 0, state: 'insufficient_history', formula: 'Count public records', calculated_at: '2026-11-02T12:00:00Z', last_updated_at: null, limitations: ['No independent review'], source_links: [] };
  assert.equal(credibility.indicatorValue(base), 'Insufficient history');
  assert.equal(credibility.indicatorValue({ ...base, state: 'unavailable', numerator: null }), 'Unavailable');
  assert.equal(credibility.indicatorValue({ ...base, state: 'recorded', numerator: 1, denominator: 2 }), '1 / 2');
  const html = renderToStaticMarkup(createElement(MetricCards, { items: [base] }));
  assert.match(html, /Insufficient history/); assert.match(html, /Sample size: 0/);
  assert.doesNotMatch(html, /0%/);
});

test('public source links stay on configured API paths', () => {
  assert.match(credibility.sourceHref('/api/roadmap/1/history'), /\/api\/roadmap\/1\/history$/);
  assert.throws(() => credibility.sourceHref('https://evil.invalid/private'));
  assert.throws(() => credibility.sourceHref('//evil.invalid'));
});


test('public progress renders loading, keyboard navigation and one roadmap/list switch', () => {
  const html = renderToStaticMarkup(createElement(ProjectProgress, { projectId: 5, canManage: false }));
  assert.match(html, /Loading public progress summary/);
  assert.match(html, /Project progress sections/);
  assert.equal((html.match(/>Timeline<\/button>/g) ?? []).length, 1);
  assert.doesNotMatch(html, /Maintainer GitHub sync controls/);
  assert.doesNotMatch(html, /Create milestone/);
});

test('empty progress has missing-data and insufficient-history disclosures', () => {
  const data = progressFixture();
  const overview = renderToStaticMarkup(createElement(ProgressOverview, { data }));
  assert.match(overview, /Insufficient history/);
  assert.match(overview, /Stale or missing GitHub data/);
  assert.match(overview, /not available cash/);
  assert.match(renderToStaticMarkup(createElement(GitHubActivity, { data })), /No conclusion about abandonment/);
});

test('progress separates original-deadline timing from unfinished commitments', () => {
  const data = progressFixture(); Object.assign(data.counts, { total: 6, delivered: 3, on_time: 1, late: 1, unknown_delivery_timing: 1, reopened: 2, overdue_unfinished: 2 });
  assert.equal(progress.onTimeLabel(data.counts), '1 / 2 dated delivery assertions were on time');
  const html = renderToStaticMarkup(createElement(ProgressOverview, { data }));
  assert.match(html, /2 overdue unfinished/); assert.match(html, /1 delivered with unknown timing/);
});

test('failed sync preserves displayed observations and distinct timestamps', () => {
  const data = progressFixture(); data.sync.latest = { status: 'failed', started_at: '2026-11-02T11:00:00Z', completed_at: '2026-11-02T11:01:00Z', error_code: 'RATE_LIMITED' }; data.sync.last_successful_sync_at = '2026-11-01T12:00:00Z'; data.snapshot_age_seconds = 86400;
  const html = renderToStaticMarkup(createElement(ProgressOverview, { data }));
  assert.match(html, /Last successful GitHub sync/); assert.match(html, /Last attempted GitHub sync/); assert.match(html, /86400 seconds/); assert.match(html, /preserves previous observations/);
});

test('GitHub titles render as escaped text and sources reject injected URLs', () => {
  const data = progressFixture(); data.github_available = true; data.activity = { repository: { full_name: 'owner/repo' }, issues: [{ github_id: 1, number: 1, title: '<img src=x onerror=alert(1)>', state: 'closed', updated_at: '2026-11-01T12:00:00Z' }], pull_requests: [], recent_commits: [] };
  const html = renderToStaticMarkup(createElement(GitHubActivity, { data }));
  assert.match(html, /&lt;img/); assert.doesNotMatch(html, /<img src=x/);
  assert.equal(progress.githubSource('owner/repo', 'issues', 1), 'https://github.com/owner/repo/issues/1');
  assert.throws(() => progress.githubSource('https://evil.invalid', 'issues', 1));
  assert.throws(() => progress.githubSource('owner/..', 'issues', 1));
});

test('funding progress uses recorded funding and the same-currency project goal', () => {
  const data = progressFixture(); data.financial.net_recorded_funding_cents = 4000;
  const html = renderToStaticMarkup(createElement(ProgressOverview, { data, fundingGoalCents: 10000, currency: 'USD' }));
  assert.match(html, /40\.0%/);
  assert.match(html, /<progress[^>]*value="4000"[^>]*max="10000"/);
  assert.match(html, /40\.00 USD recorded \/ 100\.00 USD goal/);
  for (const props of [{ fundingGoalCents: 0, currency: 'USD' }, { fundingGoalCents: 10000, currency: 'EUR' }, { fundingGoalCents: Number.MAX_SAFE_INTEGER + 1, currency: 'USD' }]) {
    assert.doesNotMatch(renderToStaticMarkup(createElement(ProgressOverview, { data, ...props })), /<progress/);
  }
});

test('overfunded progress preserves the actual amount while bounding the visual bar', () => {
  const data = progressFixture(); data.financial.net_recorded_funding_cents = 15000;
  const html = renderToStaticMarkup(createElement(ProgressOverview, { data, fundingGoalCents: 10000, currency: 'USD' }));
  assert.match(html, /150\.0%/);
  assert.match(html, /150\.00 USD recorded \/ 100\.00 USD goal/);
  assert.match(html, /<progress[^>]*value="10000"[^>]*max="10000"/);
});
