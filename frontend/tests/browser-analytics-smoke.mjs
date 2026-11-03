/** Local analytics SDK acceptance; no live accounts, paid service or private data. */
import {developmentFixture} from './analytics-fixture.mjs';
import {createServer} from 'vite';import {spawn} from 'node:child_process';import {mkdtemp,readFile,rm} from 'node:fs/promises';import {tmpdir} from 'node:os';import {join} from 'node:path';import assert from 'node:assert/strict';
if(process.env.TEST_STUDIO==='1')process.env.ANALYTICS_STUDIO_EVALUATION='true';
let fail=false,empty=false,delayNext=false;
const server=await createServer({envDir:'/tmp/opendev-empty-env',server:{host:'127.0.0.1',port:0},appType:'custom'});
server.middlewares.use(async(req,res,next)=>{
 if(req.url==='/expense-link-smoke'){res.setHeader('Content-Type','text/html');res.end(await server.transformIndexHtml('/expense-link-smoke',`<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><div id="root"></div><script type="module">import React from 'react';import {createRoot} from 'react-dom/client';import App from '/src/App.tsx';import {AuthProvider} from '/src/context/AuthContext.tsx';createRoot(document.getElementById('root')).render(React.createElement(AuthProvider,null,React.createElement(App)));</script></body></html>`));return;}
 if(req.url==='/api/auth/me'){res.setHeader('Content-Type','application/json');res.statusCode=401;res.end('{}');return;}
 if(req.url==='/api/projects/5/ledger/8'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify({id:8,project_id:5,currency:'USD',category:'Development',vendor:'Synthetic public vendor',description:'Published report only',amount_cents:2500,expense_date:'2026-11-01',updated_at:'2026-11-03T00:00:00Z',evidence:[],findings:[],public_evidence_status:'self_reported',independently_payment_matched:false}));return;}
 if(req.url==='/analytics-smoke'){res.setHeader('Content-Type','text/html');res.end(await server.transformIndexHtml('/analytics-smoke',`<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><main><div id="root"></div></main><script type="module">import React from 'react';import {createRoot} from 'react-dom/client';import View from '/src/components/ProjectAnalytics.tsx';import '/src/App.css';createRoot(document.getElementById('root')).render(React.createElement(View,{projectId:5}));</script></body></html>`));return;}
 if(req.url.startsWith('/api/projects/5/analytics/overview')){
  res.setHeader('Content-Type','application/json');if(fail){res.statusCode=503;res.end('{}');return;}
  const d=developmentFixture(),params=new URL(req.url,'http://localhost').searchParams;
  const templates=d.development.milestones;
  let allMilestones=Array.from({length:102},(_,i)=>({...templates[i%3],milestone_id:100+i,title:i===0?'<img src=x onerror=window.analyticsPwned=true>':`Synthetic milestone ${i}`}));
  if(params.get('milestone_status')&&params.get('milestone_status')!=='all')allMilestones=allMilestones.filter(r=>r.status===params.get('milestone_status'));
  d.development.offset=Number(params.get('milestone_offset')??0);d.development.total=allMilestones.length;
  d.development.milestones=allMilestones.slice(d.development.offset,d.development.offset+50);
  d.development.counts={total:allMilestones.length,...Object.fromEntries(['planned','in_progress','submitted_for_review','delivered','cancelled'].map(key=>[key,allMilestones.filter(r=>r.status===key).length])),overdue_unfinished:allMilestones.filter(r=>r.overdue).length,reopened:allMilestones.filter(r=>r.reopened_after_delivery).length,on_time:0,late:allMilestones.filter(r=>r.status==='delivered').length,unknown_delivery_timing:0};
  // Synthetic server fixture: 1000 reports in two known groups. Browser never sums rows.
  d.financial.published_reported_spending_cents=100000;d.financial.funding_minus_reported_expenditure_cents=-96000;
  d.financial.published_expense_count=1000;d.financial.expenses_with_documents_count=600;d.financial.expenses_with_documents_cents=60000;d.financial.expenses_without_documents_count=400;d.financial.expenses_without_documents_cents=40000;
  d.budget=[{category:'development',allocated_cents:10000,reported_spending_cents:60000,remaining_cents:-50000,overspend_cents:50000},{category:'hosting',allocated_cents:0,reported_spending_cents:40000,remaining_cents:-40000,overspend_cents:40000}];d.public_unresolved_finding_count=2;
  let groups=[{key:'development',month:'2026-10',date:'2026-10-31',expense_count:600,amount_cents:60000,support:true},{key:'hosting',month:'2026-11',date:'2026-11-01',expense_count:400,amount_cents:40000,support:false}];
  if(params.get('category'))groups=groups.filter(g=>g.key===params.get('category').trim().toLowerCase());
  if(params.get('date_from'))groups=groups.filter(g=>g.date>=params.get('date_from'));
  if(params.get('date_to'))groups=groups.filter(g=>g.date<=params.get('date_to'));
  if(params.get('evidence')==='supported')groups=groups.filter(g=>g.support);
  if(params.get('evidence')==='unsupported')groups=groups.filter(g=>!g.support);
  if(empty){groups=[];d.budget=[];}
  const count=groups.reduce((v,g)=>v+g.expense_count,0),amount=groups.reduce((v,g)=>v+g.amount_cents,0);
  d.expense_analysis={categories:groups.map(g=>({key:g.key,expense_count:g.expense_count,amount_cents:g.amount_cents})),months:groups.map(g=>({key:g.month,expense_count:g.expense_count,amount_cents:g.amount_cents})),expense_count:count,reported_spending_cents:amount,date_basis:'maintainer_reported_expense_date'};
  d.expense_filters={category:params.get('category')??'',evidence:params.get('evidence')??'all',date_from:params.get('date_from'),date_to:params.get('date_to'),sort:params.get('sort')??'date_desc'};
  d.expense_total=count;d.expense_offset=Number(params.get('offset')??0);
  const ordered=[...groups].sort((a,b)=>d.expense_filters.sort==='date_asc'?a.date.localeCompare(b.date):b.date.localeCompare(a.date));
  const all=ordered.flatMap((g,i)=>Array.from({length:g.expense_count},(_,j)=>({id:8+i*600+j,category:g.key,amount_cents:100,currency:'USD',expense_date:g.date,approved_public_support:g.support,public_category_finding_count:1})));
  d.expenses=all.slice(d.expense_offset,d.expense_offset+50);if(d.expenses[0])d.expenses[0].category='<img src=x onerror=window.analyticsPwned=true>';
  if(delayNext){delayNext=false;setTimeout(()=>res.end(JSON.stringify(d)),200);}else res.end(JSON.stringify(d));return;}
 next();
});await server.listen();const port=server.httpServer.address().port;
const profile=await mkdtemp(join(tmpdir(),'opendev-analytics-'));const browser=spawn('/usr/bin/chromium',['--headless','--no-sandbox','--disable-dev-shm-usage','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore'});let ws;
try{
 let debugPort;for(let i=0;i<100;i++){try{debugPort=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break;}catch{await new Promise(r=>setTimeout(r,100));}}
 assert.ok(debugPort,'Chromium started');
 const target=await(await fetch(`http://127.0.0.1:${debugPort}/json/new?about:blank`,{method:'PUT'})).json();
 ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));
 let seq=0;const pending=new Map(),errors=[];
 ws.addEventListener('message',({data})=>{const m=JSON.parse(data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(m.error)p.reject(m.error);else p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);});
 const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 const wait=async expression=>{for(let i=0;i<150;i++){if(await evaluate(expression))return;if(errors.length)throw new Error(JSON.stringify(errors));await new Promise(r=>setTimeout(r,50));}throw new Error('Timeout: '+expression+'\n'+await evaluate('document.body.innerText'));};
 const click=async text=>evaluate(`[...document.querySelectorAll('button')].find(b=>b.textContent===${JSON.stringify(text)}).click()`);
 await call('Runtime.enable');await call('Page.enable');await call('Network.enable');const requests=[];ws.addEventListener('message',({data})=>{const m=JSON.parse(data);if(m.method==='Network.requestWillBeSent')requests.push(m.params.request.url);});
 const initialStart=performance.now();
 await call('Page.navigate',{url:`http://127.0.0.1:${port}/analytics-smoke`});await wait("document.querySelectorAll('.ag-row').length>0 && document.querySelectorAll('canvas').length>=2");
 const initialMs=performance.now()-initialStart;console.log('MEASURE initial Community navigation-to-chart ms:',initialMs.toFixed(2));
 assert.ok(await evaluate("document.body.innerText.includes('40.00 USD')"));assert.equal(requests.some(u=>u.includes('/studio/node_modules/')),false);
 assert.ok(await evaluate("document.body.innerText.includes('AG Charts Community')"));
 // Use native input setters so React receives real form changes.
 const input=async(name,value)=>evaluate(`(()=>{const el=document.querySelector('[name="${name}"]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,${JSON.stringify(value)});el.dispatchEvent(new Event('input',{bubbles:true}));})()`);
 const select=async(name,value)=>evaluate(`(()=>{const el=document.querySelector('[name="${name}"]');el.value=${JSON.stringify(value)};el.dispatchEvent(new Event('change',{bubbles:true}));})()`);
 const filterStart=performance.now();await input('category','development');await input('date_from','2026-10-01');await input('date_to','2026-10-31');await select('evidence','supported');await select('sort','date_asc');await click('Apply dashboard filters');
 await wait("document.body.innerText.includes('of 600 matching published expenses') && document.querySelectorAll('canvas').length>=4");
 console.log('MEASURE filtered Community input-to-chart ms:',(performance.now()-filterStart).toFixed(2));
 assert.ok(requests.some(u=>u.includes('date_from=2026-10-01')&&u.includes('evidence=supported')&&u.includes('sort=date_asc')));
 await click('Next expense page');await wait("document.body.innerText.includes('Expense rows 51–100 of 600')");
 await click('Reset all filters');await wait("document.body.innerText.includes('of 1000 matching published expenses')");
 await input('date_from','2026-12-01');await input('date_to','2026-01-01');await click('Apply dashboard filters');await wait("document.body.innerText.includes('Start date must be on or before end date')");
 await click('Reset all filters');await wait("document.body.innerText.includes('of 1000 matching published expenses')");
 const developmentStart=performance.now();await select('analytics_view','development');
 await wait("!!document.querySelector('[aria-label=\"Community development dashboard\"]') && document.querySelectorAll('canvas').length>=4 && document.querySelectorAll('.ag-row').length>0");
 assert.ok(await evaluate("document.body.innerText.includes('Milestones 1–50 of 102') && document.body.innerText.includes('Stale or missing snapshot') && document.body.innerText.includes('2 / 3')"));
 assert.ok(await evaluate("!!document.querySelector('a[href=\"#/projects/5/roadmap\"]')"));
 console.log('MEASURE Community development selection-to-charts ms:',(performance.now()-developmentStart).toFixed(2));
 await click('Next milestone page');await wait("document.body.innerText.includes('Milestones 51–100 of 102')");
 assert.ok(requests.some(u=>u.includes('milestone_offset=50')));
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'));
 await select('analytics_view','financial');await wait("document.body.innerText.includes('Funding goal')");
 await select('milestone_status','in_progress');await click('Apply dashboard filters');await select('analytics_view','development');await wait("document.body.innerText.includes('Milestones 1–34 of 34')");
 assert.ok(await evaluate("location.hash.includes('milestone_status=in_progress') && !location.hash.includes('category=')"));
 delayNext=true;await select('milestone_status','planned');await click('Apply dashboard filters');await wait("document.body.innerText.includes('Loading public analytics')");
 await select('milestone_status','in_progress');await click('Apply dashboard filters');await wait("document.body.innerText.includes('Milestones 1–34 of 34')");await new Promise(r=>setTimeout(r,250));assert.ok(await evaluate("document.body.innerText.includes('Milestones 1–34 of 34')"));
 const callsBefore=requests.filter(u=>u.includes('/analytics/overview')).length;await select('participation','team');await click('Apply dashboard filters');await select('analytics_view','maintainer');await wait("document.body.innerText.includes('Maintainer analytics')");
 assert.equal(requests.filter(u=>u.includes('/analytics/overview')).length,callsBefore);
 await select('analytics_view','spending');await wait("document.body.innerText.includes('Spending & Evidence')");
 await click('Reset all filters');await select('analytics_view','financial');await wait("document.body.innerText.includes('Funding goal')");
 console.log('PASS: four presets, shared server status filter, safe URL, local aggregate selection without refetch and reset');
 const studioStart=performance.now();
 await evaluate("document.querySelector('select').value='studio';document.querySelector('select').dispatchEvent(new Event('change',{bubbles:true}))");
 if(process.env.TEST_STUDIO==='1'){
  await wait("!!document.querySelector('[studio-id=opendev-analytics]') || document.body.innerText.includes('could not initialize')");
  assert.ok(await evaluate("!!document.querySelector('[studio-id=opendev-analytics]')"),await evaluate('document.body.innerText'));
  assert.ok(requests.some(u=>u.includes('/studio/')));
  await wait("document.querySelectorAll('[studio-id=opendev-analytics] canvas').length>=4 && document.querySelectorAll('[studio-id=opendev-analytics] .ag-row').length>0");
  await wait("!document.querySelector('[studio-id=opendev-analytics]').innerText.includes('No data to display')");
  assert.ok(await evaluate("document.querySelector('[studio-id=opendev-analytics]').innerText.includes('$40.00')"));
  console.log('MEASURE lazy Studio select-to-widgets ms:',(performance.now()-studioStart).toFixed(2));
  assert.ok(await evaluate("document.querySelector('[studio-id=opendev-analytics]').innerText.includes('Budget comparison')"));
  assert.equal(await evaluate("document.querySelector('[studio-id=opendev-analytics]').innerText.includes('Build your report')"),false);
  await input('category','hosting');await click('Apply dashboard filters');await wait("document.body.innerText.includes('of 400 matching published expenses') && document.querySelectorAll('[studio-id=opendev-analytics] canvas').length>=4");
  await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await wait("!!document.querySelector('[studio-id=opendev-analytics]')");assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'));
  await click('Reset all filters');await wait("document.body.innerText.includes('of 1000 matching published expenses')");
  const devStudioStart=performance.now();await select('analytics_view','development');
  await wait("document.body.innerText.includes('AG Studio development dashboard') && document.querySelectorAll('[studio-id=opendev-analytics] canvas').length>=5 && document.querySelectorAll('[studio-id=opendev-analytics] .ag-row').length>0");
  await wait("!document.querySelector('[studio-id=opendev-analytics]').innerText.includes('No data to display')");
  assert.ok(await evaluate("document.querySelector('[studio-id=opendev-analytics]').innerText.includes('102') && document.body.innerText.includes('2 / 3')"));
  console.log('MEASURE Studio development selection-to-widgets ms:',(performance.now()-devStudioStart).toFixed(2));
  assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'));
  await select('analytics_view','maintainer');await wait("document.body.innerText.includes('AG Studio maintainer dashboard') && document.querySelectorAll('[studio-id=opendev-analytics] .ag-row').length>0");
  await select('analytics_view','spending');await wait("document.body.innerText.includes('AG Studio spending dashboard') && document.querySelectorAll('[studio-id=opendev-analytics] canvas').length>=3");
  await select('analytics_view','financial');await wait("document.body.innerText.includes('AG Studio financial dashboard')");
  console.log('PASS: official AG Studio 3.0.0 initialized from isolated packages for local evaluation only');
  await evaluate("document.querySelector('select').value='community';document.querySelector('select').dispatchEvent(new Event('change',{bubbles:true}))");
 }else{await wait("document.body.innerText.includes('unavailable or not authorized')");await click('Return to Community view');}
 await wait("document.querySelectorAll('.ag-row').length>0");
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'));
 empty=true;await click('Refresh analytics');await wait("document.body.innerText.includes('No public budget')");
 fail=true;await click('Refresh analytics');await wait("document.body.innerText.includes('Unable to load this public')");
 fail=false;empty=false;await click('Refresh analytics');await wait("document.querySelectorAll('.ag-row').length>0");
 assert.equal(await evaluate('!!window.analyticsPwned'),false);assert.equal(await evaluate("document.querySelectorAll('.ag-cell img').length"),0);assert.equal(errors.length,0);
 await call('Page.navigate',{url:`http://127.0.0.1:${port}/expense-link-smoke#/projects/5/expenses/8`});await wait("document.body.innerText.includes('Synthetic public vendor')");
 assert.ok(await evaluate("document.querySelector('[aria-label=\"Public expense detail\"]').innerText.includes('25.00 USD')"));
 assert.ok(await evaluate("document.querySelector('a[href=\"#/projects/5\"]')!==null"));
 assert.equal(errors.length,0);console.log('PASS: actual App hash route opens existing public expense detail while signed out');
 console.log('PASS: server category/date/evidence filters, reset, reversed dates and pagination');
 console.log('PASS: actual Community charts/grid, safe default, license gate/switching, empty/error recovery, 390px layout and clean unmount');
}finally{ws?.close();const exit=new Promise(r=>browser.once('exit',r));browser.kill('SIGTERM');await server.close();await exit;await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100});}
