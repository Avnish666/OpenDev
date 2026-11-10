/** Real app rendering with isolated synthetic API fixtures. No live providers/DB. */
import {createServer} from 'vite';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
import {agentFixture} from './agent-fixture.mjs';
import {project,projects,rewards,milestones,expenses,analytics,progress,transparency,profile,contributions,stamp} from './design-fixture.mjs';
let authenticated=false,emptyAnalytics=false,longAmounts=false;
const writes=[],unhandled=[],analyticsRequests=[];
const server=await createServer({envDir:'/tmp/opendev-empty-env',server:{host:'127.0.0.1',port:0},appType:'custom'});
server.middlewares.use(async(req,res,next)=>{
 const u=new URL(req.url,'http://local'),path=u.pathname;
 if(path==='/design-smoke'){res.setHeader('Content-Type','text/html');res.end(await server.transformIndexHtml(path,await readFile('index.html','utf8')));return;}
 if(!path.startsWith('/api/')){next();return;}
 res.setHeader('Content-Type','application/json');
 const send=value=>res.end(JSON.stringify(value));
 if(req.method!=='GET'){
  let raw='';for await(const chunk of req)raw+=chunk;const body=raw?JSON.parse(raw):undefined;
  writes.push({path,method:req.method,body});
  if(path.endsWith('/agent/query')){const a=agentFixture(body.mode==='llm'?'llm':'deterministic');a.answer='Net recorded funding: 735000 USD minor units. Not a verified bank balance.';a.evidence_used[0].value={financial_summary:analytics().financial};send(a);return;}
  if(path==='/api/projects'){send({...project,id:6,status:'draft',can_manage:true});return;}
  if(path==='/api/projects/6'){send({...project,id:6,status:'draft',can_manage:true});return;}
  if(path==='/api/projects/5/rewards'){send({...rewards[0],id:3});return;}
  if(path==='/api/projects/5/expenses'){send({...expenses[0],id:10,publication_status:'draft'});return;}
  if(path==='/api/projects/5/roadmap'){send({...milestones[0],id:4});return;}
  if(path==='/api/projects/5/github/sync'){send({status:'completed',started_at:stamp,error_code:null,retry_at:null});return;}
  if(path==='/api/funding/orders'){send(contributions[0]);return;}
  if(path==='/api/funding/fixture-pending/capture'){send({...contributions[0],status:'completed',capture_id:'TEST-CAPTURE',entitlement:{status:'granted',fulfillment_note:''}});return;}
  if(path==='/api/auth/logout'){authenticated=false;send({});return;}
  unhandled.push({path,method:req.method});res.statusCode=418;send({detail:'Unexpected synthetic test write'});return;
 }
 if(path==='/api/auth/me'){res.statusCode=authenticated?200:401;send(authenticated?{id:9,github_id:999,username:'synthetic-maintainer',avatar_url:null}:{});return;}
 if(path==='/api/projects'||path==='/api/me/projects'){const offset=Number(u.searchParams.get('offset')||0);send(projects.slice(offset,offset+20));return;}
 if(/^\/api\/projects\/[56]$/.test(path)){const id=Number(path.split('/').at(-1));send({...project,id,status:id===6?'draft':'active',can_manage:authenticated});return;}
 if(path.endsWith('/rewards')){send(rewards);return;}
 if(path.endsWith('/progress-summary')){send(progress());return;}
 if(path.endsWith('/analytics/overview')){analyticsRequests.push(Object.fromEntries(u.searchParams));const data=analytics(emptyAnalytics,u.searchParams);if(longAmounts){data.financial.net_recorded_funding_cents=123456789012345;data.financial.funding_minus_reported_expenditure_cents=123456788797345;}send(data);return;}
 if(path.includes('/analytics/export/')){res.setHeader('Content-Type','text/csv');res.end('id,amount_cents\r\n8,150000\r\n');return;}
 if(path.endsWith('/transparency')){send(transparency());return;}
 if(path.endsWith('/accountability')){send(analytics().financial);return;}
 if(path.endsWith('/ledger/8')){send(expenses[0]);return;}
 if(path.endsWith('/ledger')){send({project_id:5,items:expenses,total:2,limit:10,offset:0,calculated_at:stamp,sort:'date_desc'});return;}
 if(path.endsWith('/roadmap')){send({items:milestones,total:3,limit:50,offset:0});return;}
 if(path.endsWith('/dependencies')){send({items:[{id:1,project_id:5,from_id:1,to_id:2}],total:1});return;}
 if(path.endsWith('/github/sync-status')){send({latest:{status:'completed',started_at:stamp,error_code:null,retry_at:null},last_successful_sync_at:stamp,stale:false,notice:'Synthetic GitHub observations.'});return;}
 if(path.endsWith('/github/activity')){const g=analytics().development.github;send({...g,repository:{full_name:'example/observatory',default_branch:'main'}});return;}
 if(path.endsWith('/github/milestones')){send({items:analytics().development.github.milestones,total:1});return;}
 if(path.endsWith('/expenses')){send(expenses);return;}
 if(path.endsWith('/verification')){send({evidence_states:['self_reported'],classification:'self_reported',unresolved_discrepancy_count:null,audience:'public_evidence_only',independently_payment_matched:false,findings:[],notice:'Synthetic report; not independent payment verification.'});return;}
 if(path.endsWith('/review-history')||path.endsWith('/documents')){send([]);return;}
 if(path.endsWith('/fulfillments')||path.endsWith('/contributions')){send(contributions);return;}
 if(path==='/api/maintainers/9/credibility'){send(profile());return;}
 if(path==='/api/maintainers/9/projects'){send({items:[{...project,role:'owner',project_href:'#/projects/5'}],total:1,limit:10,offset:0,calculated_at:stamp});return;}
 if(path==='/api/maintainers/9/delivery-history'){send({items:analytics().development.milestones,total:3,limit:10,offset:0,calculated_at:stamp});return;}
 unhandled.push({path,method:req.method});res.statusCode=418;send({detail:'Unexpected synthetic test read'});
});
await server.listen();const port=server.httpServer.address().port;
const browserProfile = await mkdtemp(join(tmpdir(), 'opendev-theme-'));
const output = process.env.OPENDEV_SCREENSHOT_DIR || '/workspace/work/design-matrix';
await mkdir(output, { recursive: true });
const browser = spawn('/usr/bin/chromium', ['--headless', '--no-sandbox', '--disable-dev-shm-usage', '--remote-debugging-port=0', `--user-data-dir=${browserProfile}`, 'about:blank'], { stdio: 'ignore' });
let ws;
try {
 let debugPort; for (let i = 0; i < 100; i++) { try { debugPort = (await readFile(join(browserProfile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; break; } catch { await new Promise(r => setTimeout(r, 100)); } }
 assert.ok(debugPort, 'Chromium started');
 const target = await (await fetch(`http://127.0.0.1:${debugPort}/json/new?about:blank`, { method: 'PUT' })).json();
 ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
 let seq = 0, navigation = 0; const pending = new Map(), errors = [], checks = [];
 ws.addEventListener('message', ({ data }) => { const m = JSON.parse(data); if (m.id) { const p = pending.get(m.id); pending.delete(m.id); if (m.error) p.reject(m.error); else p.resolve(m.result); } if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails); if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args); });
 const call = (method, params = {}) => new Promise((resolve, reject) => { const id = ++seq; pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params })); });
 const evaluate = async expression => { const r = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value; };
 const wait = async expression => { for (let i = 0; i < 200; i++) { if (await evaluate(expression)) return; assert.equal(errors.length, 0, JSON.stringify(errors)); await new Promise(r => setTimeout(r, 75)); } throw new Error('Timeout: ' + expression + '\n' + await evaluate('document.body.innerText')); };
 const click = text => evaluate(`[...document.querySelectorAll('button')].find(b=>b.textContent===${JSON.stringify(text)}).click()`);
 const go = async hash => { await call('Page.navigate', { url: `http://127.0.0.1:${port}/design-smoke?run=${++navigation}${hash}` }); await wait("!!document.querySelector('.site-footer') && !document.body.innerText.includes('Checking session')"); };
 const toggle = async () => { await evaluate("document.querySelector('.theme-toggle').click()"); await new Promise(r => setTimeout(r, 100)); };
 const viewport = async width => { await call('Emulation.setDeviceMetricsOverride', { width, height: 1000, deviceScaleFactor: 1, mobile: width < 768 }); };
 const noOverflow = async label => { assert.ok(await evaluate('document.documentElement.scrollWidth <= innerWidth'), label + ' must fit viewport'); checks.push(label); };
 const checkContrast = async () => {
  const ratios = await evaluate(`(() => { const s=getComputedStyle(document.documentElement); const get=k=>s.getPropertyValue(k).trim(); const luminance=hex=>{const rgb=(hex.length===4?[...hex.slice(1)].map(c=>c+c).join(''):hex.slice(1)).match(/.{2}/g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722}; const ratio=(a,b)=>{const x=luminance(get(a)),y=luminance(get(b));return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};return {body:ratio('--text','--bg'),muted:ratio('--muted','--surface'),link:ratio('--link','--surface'),button:ratio('--on-primary','--primary'),field:ratio('--input-border','--surface')}})()`);
  for(const key of ['body','muted','link','button']) assert.ok(ratios[key]>=4.5, `${key} text contrast ${ratios[key]}`);
  assert.ok(ratios.field>=3, `input boundary contrast ${ratios.field}`); checks.push({theme:await evaluate('document.documentElement.dataset.theme'),contrast:ratios});
 };
 const capture = async (name, selector) => { if (selector) await evaluate(`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({block:'start'})`); await new Promise(r => setTimeout(r, 250)); const screenshot = await call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false }); await writeFile(join(output, name + '.png'), Buffer.from(screenshot.data, 'base64')); };
 const choose = (selector,value)=>evaluate(`(()=>{const s=document.querySelector(${JSON.stringify(selector)});s.value=${JSON.stringify(value)};s.dispatchEvent(new Event('change',{bubbles:true}));})()`);
 const input = (selector,value)=>evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});const proto=e.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(proto,'value').set.call(e,${JSON.stringify(value)});e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
 const scene = async(name,selector,width,theme)=>{
  await noOverflow(`${name}-${theme}-${width}`);
  const overlap=await evaluate(`(()=>{for(const grid of document.querySelectorAll('.grid,.analytics-charts')){const rects=[...grid.children].map(e=>e.getBoundingClientRect()).filter(r=>r.width&&r.height);for(let a=0;a<rects.length;a++)for(let b=a+1;b<rects.length;b++){const x=Math.min(rects[a].right,rects[b].right)-Math.max(rects[a].left,rects[b].left),y=Math.min(rects[a].bottom,rects[b].bottom)-Math.max(rects[a].top,rects[b].top);if(x>1&&y>1)return true;}}return false})()`);
  assert.equal(overlap,false,`${name}-${theme}-${width}: grid cards must not overlap`);
  const tiny=await evaluate(`([...document.querySelectorAll('.page-container button:not(.b-bryntum *):not(.ag-root *),.header-actions button')].filter(e=>e.getClientRects().length).filter(e=>e.getBoundingClientRect().height<43.5).map(e=>e.textContent))`);
  assert.deepEqual(tiny,[],`${name}-${theme}-${width}: touch target height`);
  if(width===1440||width===390)await capture(`${name}-${theme}-${width}`,selector);
 };
 const setTheme = async theme=>{if(await evaluate('document.documentElement.dataset.theme')!==theme)await toggle();await checkContrast();};
 await call('Runtime.enable');await call('Page.enable');await call('Network.enable');await call('Page.bringToFront');
 await call('Network.setBlockedURLs',{urls:['*github.com*','*paypal.com*','*supabase.co*']});
 for(const theme of ['light','dark'])for(const width of (process.env.OPENDEV_DESIGN_CONTRACTS_ONLY==='1'?[]:[360,390,768,1280,1440])){
  authenticated=false;await viewport(width);await go('#/explore');await setTheme(theme);await wait("document.querySelectorAll('.project-card').length===20");
  await scene('landing',null,width,theme);await scene('discovery','#discover-projects',width,theme);
  await input('#project-search','No such synthetic project');await wait("document.body.innerText.includes('No matches on this page')");assert.equal(await evaluate("document.querySelectorAll('.project-card').length"),0);await input('#project-search','');await wait("document.querySelectorAll('.project-card').length===20");
  await evaluate("document.querySelector('.pagination button:last-of-type').click()");await wait("document.querySelectorAll('.project-card').length===1");assert.ok(await evaluate("document.querySelector('.pagination').innerText.includes('Page 2')"));
  await go('#/projects/5');await wait("!!document.querySelector('.reward-card')");await scene('project',null,width,theme);await scene('rewards','.reward-section',width,theme);
  assert.ok(await evaluate("document.querySelector('.checkout-button').disabled"),'signed-out back button remains disabled');
  await click('Open accountability chat');await wait("!!document.querySelector('.project-chat')");await scene('chat-empty','.project-chat',width,theme);
  await choose('.chat-controls select','llm');await evaluate("document.querySelector('.chat-suggestions button').click()");await evaluate("document.querySelector('.chat-composer').requestSubmit()");await wait("document.body.innerText.includes('Returned mode: LLM')");await evaluate("document.querySelector('.chat-sources').open=true");await scene('chat-answer','.chat-assistant',width,theme);
  await click('Timeline');await wait("!!document.querySelector('.b-gantt-task')");await scene('timeline','.roadmap-timeline',width,theme);
  await click('Open financial transparency ledger');await wait("!!document.querySelector('.transparency .financial-value')");await scene('transparency','.transparency',width,theme);
  await go('#/projects/5/analytics');await wait("document.querySelectorAll('.analytics-chart canvas').length>=4 && !!document.querySelector('.ag-root')");await scene('analytics','.project-analytics',width,theme);await scene('charts','.analytics-charts',width,theme);
  await go('#/projects/5/expenses/8');await wait("document.body.innerText.includes('Synthetic development vendor')");await scene('expense-evidence','.public-expense-page',width,theme);
  authenticated=true;await go('#/create');await wait("!!document.querySelector('input[name=repo]')");await scene('create-project',null,width,theme);
  await evaluate("document.querySelector('.account-menu summary').click()");await wait("document.querySelector('.account-menu').open");await scene('account-menu',null,width,theme);await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await wait("!document.querySelector('.account-menu').open");assert.ok(await evaluate("document.activeElement.matches('.account-menu summary')"));
  await go('#/my');await wait("document.querySelectorAll('.project-card').length===20");await scene('my-projects',null,width,theme);
  await go('#/maintainers/9');await wait("!!document.querySelector('.maintainer-identity')");await scene('maintainer',null,width,theme);
  await go('#/history');await wait("document.querySelectorAll('.contribution-card').length===2");await scene('funding-history',null,width,theme);
  await call('Page.navigate',{url:`http://127.0.0.1:${port}/design-smoke?run=${++navigation}&contribution=fixture-pending#/funding-return`});await wait("!!document.querySelector('.payment-return button')");await scene('funding-return','.payment-return',width,theme);
  await click('Complete funding');await wait("!!document.querySelector('.receipt-summary')");await scene('receipt','.payment-return',width,theme);
  await go('#/projects/6');await wait("!!document.querySelector('.project-page')");await click('Edit Draft');await wait("!!document.querySelector('.project-editor')");await scene('edit-project','.project-form-page',width,theme);
  await go('#/projects/5');await wait("!!document.querySelector('.expenses-page')");await evaluate("[...document.querySelectorAll('.expenses-page summary')].find(e=>e.textContent==='Create expense').click()");await scene('expense-reporting','.expense-form',width,theme);
  await click('Create Reward Tier');await wait("!!document.querySelector('.reward-editor')");await scene('reward-editor','.reward-editor',width,theme);
  await click('Create milestone');await wait("!!document.querySelector('.roadmap-editor')");await scene('roadmap-management','.roadmap-editor',width,theme);
  await click('Maintainer GitHub sync controls');await wait("!!document.querySelector('.github-controls')");await scene('github-sync','.github-controls',width,theme);
  console.log(`PASS: complete UI matrix ${theme} ${width}px`);
 }
 if(process.env.OPENDEV_DESIGN_CONTRACTS_ONLY!=='1')await writeFile(join(output,'matrix-evidence.json'),JSON.stringify({scope:'Actual app with synthetic API fixtures only',viewports:[360,390,768,1280,1440],themes:['light','dark'],checks,runtimeExceptions:errors.length,unhandled},null,2));
 // Interaction contracts: exact existing payloads, no real external calls.
 authenticated=true;await viewport(1440);await go('#/create');await input('input[name=repo]','example/project');await input('input[name=title]','Synthetic new project');await input('textarea[name=description]','A sufficiently detailed synthetic project description.');await input('input[name=goal]','10000');await input('textarea[name=budget]','Development:8000\nHosting:2000');await evaluate("document.querySelector('.project-editor').requestSubmit()");await wait("location.hash==='#/projects/6'");
 assert.deepEqual(writes.find(w=>w.path==='/api/projects').body,{title:'Synthetic new project',description:'A sufficiently detailed synthetic project description.',funding_goal_cents:10000,budget:[{category:'Development',allocated_cents:8000},{category:'Hosting',allocated_cents:2000}],github_repo:'example/project',currency:'USD'});
 await wait("!!document.querySelector('.project-page')");await click('Edit Draft');await wait("!!document.querySelector('.project-editor')");await evaluate("document.querySelector('.project-editor').requestSubmit()");await wait("!document.querySelector('.project-editor')");assert.deepEqual(Object.keys(writes.find(w=>w.path==='/api/projects/6').body).sort(),['budget','description','funding_goal_cents','title']);
 await go('#/projects/5');await wait("!!document.querySelector('.expenses-page')");await click('Create Reward Tier');await input('.reward-editor input[name=name]','Synthetic reward');await input('.reward-editor textarea[name=description]','A synthetic reward description.');await input('.reward-editor input[name=price]','2500');await input('.reward-editor textarea[name=benefits]','Access | Synthetic beta');await input('.reward-editor input[name=quantity]','10');await evaluate("document.querySelector('.reward-editor').requestSubmit()");await wait("!document.querySelector('.reward-editor')");assert.deepEqual(writes.find(w=>w.path==='/api/projects/5/rewards').body,{name:'Synthetic reward',description:'A synthetic reward description.',price_cents:2500,currency:'USD',benefits:[{title:'Access',description:'Synthetic beta'}],quantity_limit:10,active:true});
 await evaluate("[...document.querySelectorAll('.expenses-page summary')].find(e=>e.textContent==='Create expense').click()");await input('.expense-form input[name=category]','Hosting');await input('.expense-form input[name=amount]','5000');await input('.expense-form input[name=vendor]','Synthetic vendor');await input('.expense-form textarea[name=description]','Synthetic expense description');await input('.expense-form input[name=date]','2026-11-10');await evaluate("document.querySelector('.expense-form').requestSubmit()");await wait("document.querySelector('.expense-form input[name=category]').value===''");assert.deepEqual(writes.find(w=>w.path==='/api/projects/5/expenses').body,{category:'Hosting',amount_cents:5000,currency:'USD',vendor:'Synthetic vendor',description:'Synthetic expense description',expense_date:'2026-11-10'});
 await click('Create milestone');await input('.roadmap-editor input[name=title]','Synthetic milestone');await input('.roadmap-editor textarea[name=description]','Synthetic description');await input('.roadmap-editor textarea[name=deliverable_description]','Publish a documented synthetic release');await input('.roadmap-editor input[name=planned_start_date]','2026-11-10');await input('.roadmap-editor input[name=planned_end_date]','2026-11-15');await evaluate("document.querySelector('.roadmap-editor').requestSubmit()");await wait("!document.querySelector('.roadmap-editor')");assert.deepEqual(writes.find(w=>w.path==='/api/projects/5/roadmap').body,{display_order:0,title:'Synthetic milestone',description:'Synthetic description',deliverable_description:'Publish a documented synthetic release',planned_start_date:'2026-11-10',planned_end_date:'2026-11-15'});
 await click('Maintainer GitHub sync controls');await wait("!!document.querySelector('.github-controls')");await click('Sync GitHub');await wait("[...document.querySelectorAll('button')].some(b=>b.textContent==='Sync GitHub'&&!b.disabled)");assert.equal(writes.find(w=>w.path==='/api/projects/5/github/sync').body,undefined);
 await evaluate("document.querySelector('.checkout-button').click()");await wait("location.hash==='#/history'");const order=writes.find(w=>w.path==='/api/funding/orders');assert.equal(order.body.tier_id,1);assert.match(order.body.checkout_key,/^[0-9a-f-]{36}$/);assert.deepEqual(Object.keys(order.body).sort(),['checkout_key','tier_id']);
 await go('#/projects/5');await wait("!!document.querySelector('.project-page')");await click('Open accountability chat');await wait("!!document.querySelector('.project-chat')");await choose('.chat-controls select','llm');await input('.chat-composer textarea','How much funding has the project received?');await evaluate("document.querySelector('.chat-composer').requestSubmit()");await wait("document.body.innerText.includes('Returned mode: LLM')");assert.deepEqual(writes.filter(w=>w.path.endsWith('/agent/query')).at(-1).body,{project_id:5,question:'How much funding has the project received?',mode:'llm'});
 await go('#/projects/5/analytics');await wait("!!document.querySelector('.ag-root')");await evaluate("document.querySelector('.dashboard-filter-panel').open=true");await input('.analytics-filters input[name=category]','Infrastructure');await evaluate("document.querySelector('.analytics-filters').requestSubmit()");await wait("document.body.innerText.includes('of 1 matching published expenses')");assert.ok(analyticsRequests.some(q=>q.category==='Infrastructure'));await noOverflow('expanded analytics filters');
 emptyAnalytics=true;await click('Reset all filters');await click('Refresh analytics');await wait("document.body.innerText.includes('No published expenses yet.')");await capture('analytics-empty-1440','.project-analytics');emptyAnalytics=false;
 longAmounts=true;await click('Refresh analytics');await wait("document.querySelector('.primary-financial-cards')?.innerText.includes('1234567890123.45 USD')");await viewport(360);await noOverflow('long authoritative financial values at 360px');await capture('analytics-long-values-360','.primary-financial-cards');longAmounts=false;
 await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});await go('#/explore');assert.ok(await evaluate("getComputedStyle(document.querySelector('.theme-glyph')).animationName==='none'"));
 assert.equal(errors.length,0,JSON.stringify(errors));assert.deepEqual(unhandled,[]);
 assert.ok(writes.some(w=>w.path.endsWith('/agent/query')&&w.body.mode==='llm'));
 await writeFile(join(output,'evidence.json'),JSON.stringify({scope:'Actual app in Chromium with explicitly synthetic API responses only. No live providers or financial records.',viewports:process.env.OPENDEV_DESIGN_CONTRACTS_ONLY==='1'?[1440,360]:[360,390,768,1280,1440],themes:process.env.OPENDEV_DESIGN_CONTRACTS_ONLY==='1'?['light']:['light','dark'],checks,requestContracts:['project create/edit','reward tier','expense draft','roadmap commitment','GitHub sync','checkout order','explicit payment capture','LLM mode','analytics filters'],runtimeExceptions:errors.length,unhandled},null,2));
 console.log((process.env.OPENDEV_DESIGN_CONTRACTS_ONLY==='1'?'PASS: contract-only browser run; ':'PASS: all page/theme/viewport combinations; ')+ ' exact form and checkout payloads; requested/returned modes; filters; search/pagination; account Escape; reduced motion. Zero runtime exceptions.');
} finally {ws?.close();const exit=new Promise(r=>browser.once('exit',r));browser.kill('SIGTERM');await exit;await server.close();await rm(browserProfile,{recursive:true,force:true,maxRetries:10,retryDelay:100});}
