/** Actual Chromium integration checks with explicitly synthetic API fixtures only. */
import { createServer } from 'vite';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';
import { progressFixture } from './progress-fixture.mjs';
import { developmentFixture } from './analytics-fixture.mjs';
import { agentFixture } from './agent-fixture.mjs';
let authenticated = false, failProjects = false, emptyProjects = false;
const project = { id: 5, title: '[TEST FIXTURE] OpenDev Observatory', description: 'Synthetic browser test project for public funding, milestones, and evidence. These are test records, not a real campaign.', github_repo_url: 'https://github.com/example/observatory', funding_goal_cents: 1250000, currency: 'USD', status: 'active', owner_id: 9, can_manage: false, maintainers: [{ id: 9, username: 'synthetic-owner', avatar_url: null }], budget: [{ category: 'Development', allocated_cents: 1000000 }, { category: 'Infrastructure', allocated_cents: 250000 }] };
const milestone = { id: 1, project_id: 5, title: 'Synthetic beta release', description: 'Test commitment only', deliverable_description: 'Publish a documented synthetic beta', planned_start_date: '2026-11-01', planned_end_date: '2026-11-08', status: 'planned', display_order: 1, version: 1, evidence: [], development_signals: {}, notice: 'Maintainer assertion only.' };
const server = await createServer({ envDir: '/tmp/opendev-empty-env', server: { host: '127.0.0.1', port: 0 }, appType: 'custom' });
server.middlewares.use(async (req, res, next) => {
 const url = new URL(req.url, 'http://local');
 if (url.pathname === '/theme-smoke') { res.setHeader('Content-Type', 'text/html'); res.end(await server.transformIndexHtml('/theme-smoke', await readFile('index.html', 'utf8'))); return; }
 if (!url.pathname.startsWith('/api/')) { next(); return; }
 res.setHeader('Content-Type', 'application/json');
 if (url.pathname === '/api/auth/me') { res.statusCode = authenticated ? 200 : 401; res.end(JSON.stringify(authenticated ? { id: 9, github_id: 999, username: 'synthetic-owner', avatar_url: null } : {})); }
 else if (url.pathname === '/api/projects' || url.pathname === '/api/me/projects') { res.statusCode = failProjects ? 503 : 200; res.end(JSON.stringify(failProjects ? { detail: 'Synthetic API unavailable' } : emptyProjects ? [] : [project])); }
 else if (url.pathname.endsWith('/rewards')) res.end(JSON.stringify([{ id: 1, name: 'Synthetic supporter', description: 'Test reward only.', price_cents: 2500, currency: 'USD', benefits: [{ title: 'Release updates', description: 'Fixture benefit' }], quantity_limit: null, active: true }]));
 else if (url.pathname.endsWith('/progress-summary')) res.end(JSON.stringify(progressFixture()));
 else if (url.pathname.endsWith('/roadmap')) res.end(JSON.stringify({ items: [milestone], total: 1 }));
 else if (url.pathname.endsWith('/sync-status')) res.end(JSON.stringify({ last_successful_sync_at: null, stale: true }));
 else if (url.pathname.endsWith('/dependencies')) res.end(JSON.stringify({ items: [], total: 0 }));
 else if (url.pathname.endsWith('/analytics/overview')) res.end(JSON.stringify(developmentFixture()));
 else if (url.pathname.endsWith('/agent/query')) res.end(JSON.stringify(agentFixture()));
 else if (url.pathname.endsWith('/contributions')) res.end('[]');
 else if (url.pathname === '/api/projects/5') res.end(JSON.stringify(project));
 else { res.statusCode = 404; res.end('{}'); }
});
await server.listen();
const port = server.httpServer.address().port;
const profile = await mkdtemp(join(tmpdir(), 'opendev-theme-'));
const output = process.env.OPENDEV_SCREENSHOT_DIR || '/workspace/work/theme-screenshots';
await mkdir(output, { recursive: true });
const browser = spawn('/usr/bin/chromium', ['--headless', '--no-sandbox', '--disable-dev-shm-usage', '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
let ws;
try {
 let debugPort; for (let i = 0; i < 100; i++) { try { debugPort = (await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; break; } catch { await new Promise(r => setTimeout(r, 100)); } }
 assert.ok(debugPort, 'Chromium started');
 const target = await (await fetch(`http://127.0.0.1:${debugPort}/json/new?about:blank`, { method: 'PUT' })).json();
 ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
 let seq = 0, navigation = 0; const pending = new Map(), errors = [], checks = [];
 ws.addEventListener('message', ({ data }) => { const m = JSON.parse(data); if (m.id) { const p = pending.get(m.id); pending.delete(m.id); if (m.error) p.reject(m.error); else p.resolve(m.result); } if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails); if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args); });
 const call = (method, params = {}) => new Promise((resolve, reject) => { const id = ++seq; pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params })); });
 const evaluate = async expression => { const r = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value; };
 const wait = async expression => { for (let i = 0; i < 200; i++) { if (await evaluate(expression)) return; assert.equal(errors.length, 0, JSON.stringify(errors)); await new Promise(r => setTimeout(r, 75)); } throw new Error('Timeout: ' + expression + '\n' + await evaluate('document.body.innerText')); };
 const click = text => evaluate(`[...document.querySelectorAll('button')].find(b=>b.textContent===${JSON.stringify(text)}).click()`);
 const go = async hash => { await call('Page.navigate', { url: `http://127.0.0.1:${port}/theme-smoke?run=${++navigation}${hash}` }); await wait("!!document.querySelector('.site-footer') && !document.body.innerText.includes('Checking session')"); };
 const toggle = async () => { await evaluate("document.querySelector('.theme-toggle').click()"); await new Promise(r => setTimeout(r, 100)); };
 const viewport = async width => { await call('Emulation.setDeviceMetricsOverride', { width, height: 1000, deviceScaleFactor: 1, mobile: width < 768 }); };
 const noOverflow = async label => { assert.ok(await evaluate('document.documentElement.scrollWidth <= innerWidth'), label + ' must fit viewport'); checks.push(label); };
 const checkContrast = async () => {
  const ratios = await evaluate(`(() => { const s=getComputedStyle(document.documentElement); const get=k=>s.getPropertyValue(k).trim(); const luminance=hex=>{const rgb=(hex.length===4?[...hex.slice(1)].map(c=>c+c).join(''):hex.slice(1)).match(/.{2}/g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722}; const ratio=(a,b)=>{const x=luminance(get(a)),y=luminance(get(b));return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};return {body:ratio('--text','--bg'),muted:ratio('--muted','--surface'),link:ratio('--link','--surface'),button:ratio('--on-primary','--primary'),field:ratio('--input-border','--surface')}})()`);
  for(const key of ['body','muted','link','button']) assert.ok(ratios[key]>=4.5, `${key} text contrast ${ratios[key]}`);
  assert.ok(ratios.field>=3, `input boundary contrast ${ratios.field}`); checks.push({theme:await evaluate('document.documentElement.dataset.theme'),contrast:ratios});
 };
 const capture = async (name, selector) => { if (selector) await evaluate(`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({block:'start'})`); await new Promise(r => setTimeout(r, 250)); const screenshot = await call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false }); await writeFile(join(output, name + '.png'), Buffer.from(screenshot.data, 'base64')); };
 await call('Runtime.enable'); await call('Page.enable'); await call('Network.enable'); await call('Network.setBlockedURLs', { urls: ['*github.com*','*paypal.com*','*supabase.co*'] });
 await viewport(1440); await go('#/explore'); await wait("!!document.querySelector('.project-card')");
 assert.equal(await evaluate('document.documentElement.dataset.theme'), 'light'); await checkContrast(); await capture('explore-light-1440');
 await call('Page.bringToFront'); await evaluate("document.querySelector('.theme-toggle').focus()"); assert.equal(await evaluate("document.activeElement.classList.contains('theme-toggle')"), true); await call('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r', unmodifiedText: '\r' }); await call('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
 await wait("document.documentElement.dataset.theme==='dark'"); assert.equal(await evaluate("document.querySelector('.theme-toggle').getAttribute('aria-pressed')"), 'true'); assert.equal(await evaluate("localStorage.getItem('opendev-theme')"), 'dark'); await capture('explore-dark-1440');
 await go('#/explore'); assert.equal(await evaluate('document.documentElement.dataset.theme'), 'dark'); await checkContrast();
 await call('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }] }); assert.equal(await evaluate('getComputedStyle(document.documentElement).colorScheme'), 'dark'); checks.push('keyboard toggle, persisted choice, explicit dark overrides OS light');
 for (const width of [360,390,768,1280,1440]) { await viewport(width); await noOverflow(`explore-${width}`); }
 await viewport(390); await evaluate("document.querySelector('.menu-toggle').click()"); await wait("document.activeElement.matches('#main-navigation a')"); await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27}); await wait("document.querySelector('.menu-toggle').getAttribute('aria-expanded')==='false'"); assert.equal(await evaluate("document.activeElement.classList.contains('menu-toggle')"),true); await evaluate("document.querySelector('.menu-toggle').click()"); assert.equal(await evaluate("document.querySelector('.menu-toggle').getAttribute('aria-expanded')"), 'true'); await evaluate("document.querySelector('.main-nav a[href=\"#/analytics\"]').click()"); await wait("location.hash==='#/analytics' && !!document.querySelector('.project-directory a[href=\"#/projects/5/analytics\"]')"); assert.equal(await evaluate("document.querySelector('.menu-toggle').getAttribute('aria-expanded')"), 'false'); await noOverflow('mobile analytics discovery');
 await go('#/projects/5'); await wait("document.body.innerText.includes('Synthetic supporter')"); await noOverflow('project-390-dark'); await capture('project-dark-390');
 await click('Open accountability chat'); await wait("!!document.querySelector('.project-chat')"); await noOverflow('chat-390-dark'); await capture('chat-dark-390', '.project-chat');
 await evaluate("document.querySelector('.chat-suggestions button').click()"); await evaluate("document.querySelector('.chat-composer').requestSubmit()"); await wait("document.body.innerText.includes('Returned mode: Deterministic')"); await noOverflow('chat-response-390-dark');
 await click('Timeline'); await wait("!!document.querySelector('.b-gantt-task')"); await noOverflow('gantt-390-dark'); await capture('gantt-dark-390', '.opendev-gantt');
 const ganttDark = await evaluate("getComputedStyle(document.querySelector('.b-grid-cell')).backgroundColor");
 await toggle(); await call('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }] }); assert.equal(await evaluate('getComputedStyle(document.documentElement).colorScheme'), 'light');
 const ganttLight = await evaluate("getComputedStyle(document.querySelector('.b-grid-cell')).backgroundColor"); assert.notEqual(ganttDark, ganttLight, 'Bryntum follows manual theme'); await capture('gantt-light-390', '.opendev-gantt'); checks.push('Bryntum live manual theme follows opposite OS preference');
 await viewport(1440); await go('#/projects/5/analytics'); await wait("document.querySelectorAll('.analytics-chart canvas').length>=1 && !!document.querySelector('.ag-root')"); await capture('analytics-light-1440', '.analytics-charts');
 const gridLight = await evaluate("getComputedStyle(document.querySelector('.ag-root')).getPropertyValue('--ag-background-color')"); await toggle(); await new Promise(r => setTimeout(r, 300)); const gridDark = await evaluate("getComputedStyle(document.querySelector('.ag-root')).getPropertyValue('--ag-background-color')"); assert.notEqual(gridLight,gridDark,'AG Grid follows toggle'); await capture('analytics-dark-1440', '.analytics-charts');
 for (const width of [360,390,768,1280,1440]) { await viewport(width); await noOverflow(`analytics-${width}-dark`); }
 await viewport(390); await capture('analytics-dark-390', '.analytics-charts');
 authenticated = true; await go('#/create'); await wait("!!document.querySelector('input[name=repo]')"); await noOverflow('create-390-dark'); await capture('create-dark-390');
 await viewport(1440); await capture('create-dark-1440'); await toggle(); await capture('create-light-1440');
 await go('#/funding-return'); await wait("document.body.innerText.includes('Returned from PayPal Sandbox')"); await capture('payment-return-light-1440'); await viewport(360); await noOverflow('payment-return-360');
 authenticated = false; await go('#/create'); await wait("document.body.innerText.includes('Sign in with GitHub to manage projects')"); assert.equal(await evaluate("!!document.querySelector('input[name=repo]')"),false); checks.push('signed-in create form and anonymous route protection');
 failProjects = true; await go('#/explore'); await wait("document.body.innerText.includes('Synthetic API unavailable')"); failProjects = false; await click('Try again'); await wait("!!document.querySelector('.project-card')"); emptyProjects = true; await go('#/explore'); await wait("document.body.innerText.includes('No projects here yet')"); checks.push('API error retry and empty discovery');
 await evaluate("window.dispatchEvent(new StorageEvent('storage',{key:'opendev-theme',newValue:'dark'}))"); await wait("document.documentElement.dataset.theme==='dark'"); checks.push('cross-tab preference synchronization');
 await call('Page.addScriptToEvaluateOnNewDocument', { source: "Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage blocked')}})" }); await go('#/explore'); assert.equal(await evaluate('document.documentElement.dataset.theme'), 'light'); await toggle(); assert.equal(await evaluate('document.documentElement.dataset.theme'), 'dark'); checks.push('storage-disabled browsing');
 assert.equal(errors.length,0,JSON.stringify(errors));
 await writeFile(join(output,'evidence.json'),JSON.stringify({scope:'Synthetic API fixtures only. No external service calls. Actual Chromium rendering.',checks,runtimeExceptions:errors.length},null,2));
 console.log('PASS: light/dark keyboard toggle, persistence, OS independence, chart/grid/Gantt themes, 5 responsive widths, authenticated forms, protected routes, API retry, empty state and blocked storage. Zero runtime exceptions.');
} finally { ws?.close(); const exit = new Promise(r => browser.once('exit',r)); browser.kill('SIGTERM'); await exit; await server.close(); await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100}); }
