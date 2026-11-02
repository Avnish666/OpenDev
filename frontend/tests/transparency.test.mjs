import { before, after, test } from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

let folder, displayMoney, transparencyAPI, Transparency, GitHubProgress, Roadmap;
before(async () => {
  folder = await mkdtemp(join(import.meta.dirname, '.compiled-'));
  for (const file of ['api/client.ts', 'api/transparency.ts', 'components/Transparency.tsx', 'components/GitHubProgress.tsx', 'components/Roadmap.tsx']) {
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
