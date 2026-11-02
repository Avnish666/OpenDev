/** Synthetic local Chromium/CDP smoke; never contacts the backend or real providers. */
import { progressFixture } from './progress-fixture.mjs';
import { createServer } from 'vite';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';

const rows = [1, 2].map(id => ({ id, project_id: 5, title: `Synthetic beta ${id}`, description: 'Synthetic commitment', deliverable_description: 'Publish a documented beta release', planned_start_date: '2026-11-01', planned_end_date: '2026-11-05', actual_completion_date: null, status: 'planned', display_order: id, version: 7, evidence: [{ id: 'synthetic', evidence_type: 'issue', canonical_id: '201', url: 'https://github.com/example/project/issues/1', state: 'closed', merged: null, stale: true }], development_signals: { closed_issues: 1 }, notice: 'Maintainer assertion, not independently verified.' }));
let writes = [], fail = 0, failSummary = false;
const server = await createServer({ envDir: '/tmp/opendev-empty-env', server: { host: '127.0.0.1', port: 0 }, appType: 'custom' });
server.middlewares.use(async (req, res, next) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/gantt-smoke') {
    res.setHeader('Content-Type', 'text/html');
    res.end(await server.transformIndexHtml('/gantt-smoke', `<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body><div id="root"></div><script type="module">import React from 'react';import { Widget } from '@bryntum/core-community';import { formatDate } from '/src/api/gantt.ts';window.smokeGantt=()=>Widget.fromElement(document.querySelector('.b-gantt'));window.smokeDates=()=>window.smokeGantt().project.taskStore.records.map(t=>[formatDate(t.startDate),formatDate(t.endDate)]);import { createRoot } from 'react-dom/client';import Timeline from '/src/components/ProjectProgress.tsx';createRoot(document.getElementById('root')).render(React.createElement(Timeline,{projectId:5,canManage:new URLSearchParams(location.search).get('manage')==='1'}));</script></body></html>`)); return;
  }
  if (!url.pathname.startsWith('/api/')) { next(); return; }
  res.setHeader('Content-Type', 'application/json');
  if (req.method === 'PATCH') {
    let body = ''; req.on('data', c => { body += c; }); req.on('end', () => {
      const data = JSON.parse(body); writes.push(data);
      if (fail) { res.statusCode = fail; res.end(JSON.stringify({ detail: 'Milestone changed; refresh' })); return; }
      Object.assign(rows[0], data, { version: rows[0].version + 1 }); res.end(JSON.stringify(rows[0]));
    }); return;
  }
  if (url.pathname.endsWith('/progress-summary')) { if(failSummary){res.statusCode=503;res.end(JSON.stringify({detail:'Synthetic summary unavailable'}));return;}const data=progressFixture();data.counts.total=rows.length;data.counts.planned=rows.length;data.owner.delivery={...data.counts};res.end(JSON.stringify(data)); return; }
  if (url.pathname.endsWith('/sync-status')) res.end(JSON.stringify({ last_successful_sync_at: '2026-11-01T12:00:00Z', stale: true }));
  else if (url.pathname.endsWith('/dependencies')) res.end(JSON.stringify({ items: [{ id: 1, project_id: 5, from_id: 1, to_id: 2 }], total: 1 }));
  else res.end(JSON.stringify({ items: rows, total: rows.length }));
});
await server.listen();
const port = server.httpServer.address().port;
const profile = await mkdtemp(join(tmpdir(), 'opendev-gantt-browser-'));
const chromium = spawn('/usr/bin/chromium', ['--headless', '--no-sandbox', '--disable-dev-shm-usage', '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
let ws;
try {
  let devPort;
  for (let i = 0; i < 100; i++) { try { devPort = (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; break; } catch { await new Promise(r => setTimeout(r, 100)); } }
  assert.ok(devPort, 'Chromium did not start');
  const target = await (await fetch(`http://127.0.0.1:${devPort}/json/new?http://127.0.0.1:${port}/gantt-smoke?manage=1`, { method: 'PUT' })).json();
  ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let seq = 0; const pending = new Map(); const errors = []; const requests = [];
  ws.addEventListener('message', ({ data }) => { const message = JSON.parse(data); if (message.id) { const callback = pending.get(message.id); pending.delete(message.id); if (message.error) callback.reject(message.error); else callback.resolve(message.result); } if (message.method === 'Network.requestWillBeSent') requests.push(message.params.request.url); if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails.text + ': ' + (message.params.exceptionDetails.exception?.description ?? '')); });
  const call = (method, params = {}) => new Promise((resolve, reject) => { const id = ++seq; pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params })); });
  await call('Performance.enable'); await call('Runtime.enable'); await call('Page.enable'); await call('Network.enable'); await call('Network.setCacheDisabled',{cacheDisabled:true}); await call('Emulation.setTimezoneOverride',{timezoneId:'America/Los_Angeles'}); await call('Page.navigate',{url:`http://127.0.0.1:${port}/gantt-smoke?manage=1`});
  const evaluate = async expression => { if (expression.includes('const ') && !expression.startsWith('(()=>')) expression = '(()=>{' + expression + '})()'; const result = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true }); if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails)); return result.result.value; };
  async function wait(expression) { for (let i = 0; i < 200; i++) { if (await evaluate(expression)) return; if (errors.length) throw new Error(errors.join('\n')); await new Promise(r => setTimeout(r, 100)); } throw new Error('Timed out: '+expression+'\n'+await evaluate('document.body.innerText')); }
  await wait("[...document.querySelectorAll('button')].some(b=>b.textContent==='Timeline')");
  assert.equal(requests.some(url=>url.includes('RoadmapTimeline.tsx') || url.includes('@bryntum_gantt')),false,'Gantt must not be fetched by list view');
  await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Timeline').click()");
  await wait("document.querySelectorAll('.b-gantt-task-wrap').length === 2");
  await evaluate("document.querySelector('.b-gantt').scrollIntoView()");
  await wait("document.querySelectorAll('.b-sch-dependency').length > 0");
  assert.equal(errors.length, 0);
  assert.deepEqual(await evaluate('window.smokeDates()'),[['2026-11-01','2026-11-06'],['2026-11-01','2026-11-06']]);
  assert.ok(requests.some(url=>url.includes('RoadmapTimeline.tsx')));
  console.log('PASS: real Community tasks/dependency arrows, local DST dates, lazy module request');
  const memory = [{ stage:'two_tasks_rendered',metrics:(await call('Performance.getMetrics')).metrics.filter(m=>['JSHeapUsedSize','JSHeapTotalSize','Nodes','Documents','JSEventListeners'].includes(m.name)) }];
  const box = await evaluate("(()=>{const r=document.querySelector('.b-gantt-task').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()");
  await call('Input.dispatchMouseEvent', { type:'mouseMoved', x:box.x, y:box.y });
  await call('Input.dispatchMouseEvent', { type:'mousePressed', x:box.x, y:box.y, button:'left', clickCount:1 });
  for (let i=1;i<=5;i++) { await call('Input.dispatchMouseEvent', { type:'mouseMoved', x:box.x+i*15, y:box.y, buttons:1 }); await new Promise(r=>setTimeout(r,60)); }
  await call('Input.dispatchMouseEvent', { type:'mouseReleased', x:box.x+75, y:box.y, button:'left', clickCount:1 });
  await wait("document.body.innerText.includes('Confirm commitment date change')");
  assert.equal(writes.length,0);
  await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Cancel date change').click()");
  await wait("!document.body.innerText.includes('Confirm commitment date change')");
  console.log('PASS: actual task drag proposes confirmation without changing backend dates');
  await wait("[...document.querySelectorAll('button')].some(b=>b.textContent==='Timeline')");
  await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Timeline').click()");
  await wait("document.querySelectorAll('.b-gantt-task-wrap').length === 2");
  await evaluate("document.querySelector('.b-gantt').scrollIntoView()");
  const endBox = await evaluate("(()=>{const r=document.querySelector('.b-gantt-task').getBoundingClientRect();return {x:r.right-2,y:r.y+r.height/2};})()");
  await call('Input.dispatchMouseEvent', { type:'mouseMoved', x:endBox.x, y:endBox.y });
  await new Promise(r=>setTimeout(r,150));
  await call('Input.dispatchMouseEvent', { type:'mousePressed', x:endBox.x, y:endBox.y, button:'left', clickCount:1 });
  for(let i=1;i<=5;i++){await call('Input.dispatchMouseEvent',{type:'mouseMoved',x:endBox.x+i*12,y:endBox.y,buttons:1});await new Promise(r=>setTimeout(r,60));}
  await call('Input.dispatchMouseEvent', { type:'mouseReleased', x:endBox.x+60, y:endBox.y, button:'left', clickCount:1 });
  await wait("document.body.innerText.includes('Confirm commitment date change')");
  assert.equal(writes.length,0);
  await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Cancel date change').click()");
  console.log('PASS: actual right-edge resize also requires confirmation without writing');


  await evaluate(`document.querySelector('select[value]'); const select=[...document.querySelectorAll('select')].find(s=>s.textContent.includes('Choose a milestone'));select.value='1';select.dispatchEvent(new Event('change',{bubbles:true}));`);
  await wait("document.body.innerText.includes('Propose planned dates')");
  assert.ok(await evaluate("document.body.innerText.includes('stale observation')"));
  await evaluate(`const form=[...document.querySelectorAll('form')].find(f=>f.textContent.includes('Propose planned dates'));form.querySelector('[name=start]').value='2026-11-02';form.querySelector('[name=end]').value='2026-11-06';form.requestSubmit();`);
  await wait("document.body.innerText.includes('Confirm commitment date change')");
  assert.equal(writes.length, 0);
  await evaluate(`const form=document.querySelector('[aria-label="Confirm schedule change"]');form.querySelector('textarea').value='Synthetic confirmed scheduling reason';form.requestSubmit();`);
  await wait("document.body.innerText.includes('2026-11-02 → 2026-11-06')");
  assert.equal(writes.length, 1); assert.equal(writes[0].expected_version, 7); assert.equal('status' in writes[0], false);
  console.log('PASS: selected details, stale evidence and confirmed versioned save');
  await wait("document.body.innerText.includes('Propose planned dates') && !document.body.innerText.includes('Confirm commitment date change')");
  fail = 409;
  await evaluate(`const form=[...document.querySelectorAll('form')].find(f=>f.textContent.includes('Propose planned dates'));form.querySelector('[name=start]').value='2026-11-03';form.requestSubmit();`);
  await wait("document.body.innerText.includes('Confirm commitment date change')");
  await evaluate(`const form=document.querySelector('[aria-label="Confirm schedule change"]');form.querySelector('textarea').value='Synthetic conflicting scheduling reason';form.requestSubmit();`);
  await wait("document.body.innerText.includes('Original dates remain visible')");
  assert.equal(rows[0].planned_start_date, '2026-11-02');
  console.log('PASS: 409 conflict restores authoritative dates');
  fail = 500;
  await wait("document.body.innerText.includes('Propose planned dates')");
  await evaluate(`const form=[...document.querySelectorAll('form')].find(f=>f.textContent.includes('Propose planned dates'));form.querySelector('[name=start]').value='2026-11-03';form.requestSubmit();`);
  await wait("document.body.innerText.includes('Confirm commitment date change')");
  const beforeInvalid=writes.length;
  await evaluate(`const form=document.querySelector('[aria-label="Confirm schedule change"]');form.querySelector('textarea').value='';form.requestSubmit();`);
  assert.equal(writes.length,beforeInvalid);
  await evaluate(`const form=document.querySelector('[aria-label="Confirm schedule change"]');form.querySelector('textarea').value='Synthetic server failure scheduling reason';form.requestSubmit();`);
  await wait("document.body.innerText.includes('Original dates remain visible')");
  assert.equal(rows[0].planned_start_date,'2026-11-02');
  console.log('PASS: required confirmation reason and 500 failure preserve authoritative dates');
  fail = 0;
  rows[1].title='<img src=x onerror="window.__ganttInjected=1">';
  await call('Emulation.setTimezoneOverride',{timezoneId:'Pacific/Kiritimati'});
  await call('Page.navigate', { url: `http://127.0.0.1:${port}/gantt-smoke` });
  await wait("[...document.querySelectorAll('button')].some(b=>b.textContent==='Timeline')");
  await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Timeline').click()");
  await wait("document.querySelectorAll('.b-gantt-task-wrap').length === 2");
  await evaluate("document.querySelector('.b-gantt').scrollIntoView()");
  assert.deepEqual(await evaluate('window.smokeDates()[0]'),['2026-11-02','2026-11-07']);
  assert.equal(await evaluate('window.__ganttInjected || 0'),0);
  assert.equal(await evaluate("document.querySelector('.b-gantt img') !== null"),false);
  await evaluate(`const select=[...document.querySelectorAll('select')].find(s=>s.textContent.includes('Choose a milestone'));select.value='1';select.dispatchEvent(new Event('change',{bubbles:true}));`);
  await wait("document.body.innerText.includes('Publish a documented beta release')");
  assert.equal(await evaluate("document.body.innerText.includes('Propose planned dates')"), false);
  await call('Emulation.setDeviceMetricsOverride', { width:390,height:844,deviceScaleFactor:1,mobile:true });
  await wait("document.querySelector('.opendev-gantt').getBoundingClientRect().width <= 390");
  await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Milestone list').click()");
  await wait("document.querySelectorAll('.b-gantt').length === 0");
  await wait("document.body.innerText.includes('Read milestone history')");
  assert.equal(errors.length, 0);
  console.log('PASS: public progress dashboard mobile layout and timeline/list switching');
  for(let i=0;i<3;i++){
    await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Timeline').click()");
    await wait("document.querySelectorAll('.b-gantt').length === 1");
    await evaluate('void(window.previousGantt=window.smokeGantt())');
    await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Milestone list').click()");
    await wait("document.querySelectorAll('.b-gantt').length === 0 && window.previousGantt.isDestroyed");
    await wait("document.body.innerText.includes('Read milestone history')");
  }
  assert.equal(writes.length,3,'Read-only navigation must not write');
  console.log('PASS: UTC+14 date mapping, hostile title escaping, repeated mount/destroy without extra writes');
  failSummary = true;
  await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Refresh progress summary').click()");
  await wait("document.body.innerText.includes('Synthetic summary unavailable')");
  await wait("document.body.innerText.includes('Read milestone history')");
  console.log('PASS: summary error is accessible and preserves the usable roadmap fallback');

  memory.push({stage:'after_repeated_navigation',metrics:(await call('Performance.getMetrics')).metrics.filter(m=>['JSHeapUsedSize','JSHeapTotalSize','Nodes','Documents','JSEventListeners'].includes(m.name))});
  await call('HeapProfiler.collectGarbage');
  memory.push({stage:'after_navigation_explicit_gc_diagnostic',metrics:(await call('Performance.getMetrics')).metrics.filter(m=>['JSHeapUsedSize','JSHeapTotalSize','Nodes','Documents','JSEventListeners'].includes(m.name))});
  await writeFile(join(tmpdir(),'opendev-phase4-browser.json'),JSON.stringify({scope:'Synthetic two-task Vite dev page; sampled Chromium renderer metrics; final explicit GC diagnostic only, no peak/leak guarantee',memory},null,2)+'\n');
  console.log('MEASUREMENT: '+JSON.stringify(memory));
  console.log('PASS: signed-out read-only timeline with no scheduling controls or runtime exceptions');
} finally {
  ws?.close(); const exited = new Promise(r => { if (chromium.exitCode !== null) r(); else chromium.once('exit', r); });
  chromium.kill('SIGTERM'); await server.close();
  await exited; await rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
}
