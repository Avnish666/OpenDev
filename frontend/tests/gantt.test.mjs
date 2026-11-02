import { before, after, test } from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
let folder, gantt;
before(async () => {
  folder = await mkdtemp(join(import.meta.dirname, '.compiled-gantt-'));
  for (const name of ['api/client.ts', 'api/gantt.ts']) {
    let source = await readFile(new URL('../src/' + name, import.meta.url), 'utf8');
    source = source.replace('import.meta.env', "({ VITE_API_URL: 'https://api.invalid' })");
    let { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } });
    outputText = outputText.replace(/from '(\.[^']+)'/g, (_, path) => `from '${path}.js'`);
    const destination = join(folder, name.replace(/\.ts$/, '.js')); await mkdir(join(destination, '..'), { recursive: true }); await writeFile(destination, outputText);
  }
  gantt = await import(pathToFileURL(join(folder, 'api/gantt.js')));
});
after(async () => { if (folder) await rm(folder, { recursive: true, force: true }); });
const row = (changes = {}) => ({ id: 1, project_id: 5, title: '<script>unsafe title</script>', description: 'Description', deliverable_description: 'Ship a documented release', planned_start_date: '2026-03-07', planned_end_date: '2026-03-09', actual_completion_date: null, status: 'planned', display_order: 1, version: 7, evidence: [], development_signals: { merged_pull_requests: 1 }, ...changes });
const dates = { milestoneId: 1, start: '2026-04-01', end: '2026-04-05' };
const reason = 'A public explanation for rescheduling.';

test('typed mapping preserves IDs, text, signals and ordering', () => {
  const model = gantt.mapRoadmap([row(), row({ id: 2, display_order: 0 })], [], 5, true);
  assert.deepEqual(model.tasks.map(t => t.id), [2, 1]);
  assert.equal(model.tasks[1].name, row().title);
  assert.equal(model.tasks[1].opendev.deliverable, row().deliverable_description);
  assert.equal(model.tasks[1].opendev.signals.merged_pull_requests, 1);
  assert.equal(model.tasks[1].manuallyScheduled, true);
});
test('calendar dates roundtrip over DST without UTC day shifts', () => {
  const previous = process.env.TZ; process.env.TZ = 'America/New_York';
  try {
    const model = gantt.mapRoadmap([row()], [], 5, false);
    assert.equal(gantt.formatDate(model.tasks[0].endDate), '2026-03-10');
    assert.deepEqual(gantt.proposal(1, model.tasks[0].startDate, model.tasks[0].endDate), { milestoneId: 1, start: '2026-03-07', end: '2026-03-09' });
    assert.equal(gantt.formatDate(gantt.calendarDate('2026-11-01')), '2026-11-01');
  } finally { if (previous === undefined) delete process.env.TZ; else process.env.TZ = previous; }
});
test('same-day milestone has a visible single-day interval', () => {
  const model = gantt.mapRoadmap([row({ planned_end_date: '2026-03-07' })], [], 5, false);
  assert.equal(gantt.formatDate(model.tasks[0].endDate), '2026-03-08');
});
test('invalid dates and intervals rejected', () => {
  assert.throws(() => gantt.calendarDate('2026-02-30'));
  assert.throws(() => gantt.calendarDate('2026-2-3'));
  assert.throws(() => gantt.mapRoadmap([row({ planned_end_date: '2026-01-01' })], [], 5, false));
});
test('empty timeline has no fabricated tasks', () => assert.deepEqual(gantt.mapRoadmap([], [], 5, false), { tasks: [], dependencies: [] }));
test('visitors cannot drag, resize or save', async () => {
  const task = gantt.mapRoadmap([row()], [], 5, false).tasks[0];
  assert.equal(task.readOnly, true); assert.equal(task.draggable, false); assert.equal(task.resizable, false);
  await assert.rejects(gantt.saveSchedule(row(), dates, reason, false), /authorized maintainers/);
});
test('only planned commitments support maintainer drag and resize', async () => {
  assert.equal(gantt.mapRoadmap([row()], [], 5, true).tasks[0].draggable, true);
  for (const status of ['in_progress', 'submitted_for_review', 'delivered', 'cancelled']) {
    const task = gantt.mapRoadmap([row({ status })], [], 5, true).tasks[0]; assert.equal(task.readOnly, true);
    await assert.rejects(gantt.saveSchedule(row({ status }), dates, reason, true));
  }
});
test('confirmed edit sends only versioned date fields and reason', async () => {
  const calls = [];
  await gantt.saveSchedule(row(), dates, reason, true, async (...args) => { calls.push(args); return row(); });
  assert.deepEqual(calls[0], ['/api/roadmap/1', 'PATCH', { expected_version: 7, reason, planned_start_date: dates.start, planned_end_date: dates.end }]);
});
test('change reason and date validation happen before any request', async () => {
  let called = false; const request = async () => { called = true; };
  await assert.rejects(gantt.saveSchedule(row(), dates, 'short', true, request));
  await assert.rejects(gantt.saveSchedule(row(), { ...dates, end: '2026-01-01' }, reason, true, request));
  assert.equal(called, false);
});
test('failed saves and version conflicts preserve authoritative visible inputs', async () => {
  for (const status of [500, 409]) {
    const source = row(); const before = JSON.stringify(source);
    await assert.rejects(gantt.saveSchedule(source, dates, reason, true, async () => { const e = new Error(`Request failed (${status})`); e.status = status; throw e; }));
    assert.equal(JSON.stringify(source), before);
    assert.equal(gantt.formatDate(gantt.mapRoadmap([source], [], 5, true).tasks[0].startDate), source.planned_start_date);
  }
});
test('stale evidence is preserved as a warning, not a completion value', () => {
  const task = gantt.mapRoadmap([row({ evidence: [{ stale: true }] })], [], 5, false).tasks[0];
  assert.equal(task.opendev.stale, true);
  assert.equal('percentDone' in task, false);
});
test('dependencies validate ownership, cycles and duplicates', () => {
  const rows = [row(), row({ id: 2 })]; const edge = { id: 9, project_id: 5, from_id: 1, to_id: 2 };
  assert.equal(gantt.mapRoadmap(rows, [edge], 5, false).dependencies[0].toTask, 2);
  assert.throws(() => gantt.validateDependencies(rows, [{ ...edge, project_id: 6 }], 5));
  assert.throws(() => gantt.validateDependencies(rows, [{ ...edge, to_id: 99 }], 5));
  assert.throws(() => gantt.validateDependencies(rows, [edge, edge], 5));
  assert.throws(() => gantt.validateDependencies(rows, [edge, { ...edge, from_id: 2, to_id: 1 }], 5));
});
test('mapping and schedule writes never infer delivery status', async () => {
  const source = row({ development_signals: { merged_pull_requests: 100, closed_issues: 100 } });
  assert.equal(gantt.mapRoadmap([source], [], 5, true).tasks[0].opendev.status, 'planned');
  await gantt.saveSchedule(source, dates, reason, true, async (_path, _method, body) => { assert.equal('status' in body, false); return source; });
  assert.equal(source.status, 'planned');
});
