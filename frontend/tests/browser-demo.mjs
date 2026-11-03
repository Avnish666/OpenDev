/** Actual loopback React/API/PostgreSQL demo acceptance and unaltered Chromium captures. */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile,mkdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
const manifestPath=process.argv[2];
assert.ok(manifestPath,'Pass the private local demo manifest path');
const manifest=JSON.parse(await readFile(manifestPath,'utf8'));
assert.equal(manifest.scope,'LOCAL SYNTHETIC DEMO; no live-provider verification');
const pid=manifest.project_id,eid=manifest.expense_id,owner=manifest.owner_id;
for(const id of [pid,eid,owner,manifest.private_project_id])assert.ok(Number.isSafeInteger(id)&&id>0);
const output=fileURLToPath(new URL('../../docs/submission/screenshots/',import.meta.url));
await mkdir(output,{recursive:true});
const profile=await mkdtemp(join(tmpdir(),'opendev-demo-chromium-'));
const browser=spawn('/usr/bin/chromium',['--headless','--no-sandbox','--disable-dev-shm-usage','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore'});
let ws;
const screenshots=[];
try{
 let port;for(let n=0;n<100;n++){try{port=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break;}catch{await new Promise(r=>setTimeout(r,100));}}
 assert.ok(port,'Chromium ready');
 const page=await(await fetch(`http://127.0.0.1:${port}/json/new?about:blank`,{method:'PUT'})).json();
 ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));
 let seq=0;const pending=new Map(),errors=[];
 ws.addEventListener('message',({data})=>{const m=JSON.parse(data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(m.error)p.reject(m.error);else p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);});
 const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 const wait=async expression=>{for(let n=0;n<200;n++){if(await evaluate('!!document.body && ('+expression+')'))return;assert.equal(errors.length,0,JSON.stringify(errors));await new Promise(r=>setTimeout(r,75));}throw new Error('Timeout: '+expression+'\n'+await evaluate('document.body.innerText'));};
 const go=async path=>{await call('Page.navigate',{url:'http://127.0.0.1:5173/'+path});await wait("document.body.innerText.includes('Open Source Funding')&&!document.body.innerText.includes('Checking session')");};
 const click=async text=>evaluate(`[...document.querySelectorAll('button')].find(e=>e.textContent===${JSON.stringify(text)}).click()`);
 async function capture(name,caption,selector){
  if(selector)await evaluate(`document.querySelector(${JSON.stringify(selector)}).scrollIntoView({block:'start'})`);
  await new Promise(r=>setTimeout(r,300));
  assert.ok(!(await evaluate('document.body.innerText')).includes('DEMO_PRIVATE_'));
  const r=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  const bytes=Buffer.from(r.data,'base64');await writeFile(join(output,name+'.png'),bytes);
  screenshots.push({file:name+'.png',caption:'LOCAL SYNTHETIC DEMO — '+caption,sha256:createHash('sha256').update(bytes).digest('hex')});
 }
 await call('Runtime.enable');await call('Page.enable');await call('Network.enable');
 await call('Network.setBlockedURLs',{urls:['*github.com*','*paypal.com*','*supabase.co*']});
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await go('#/explore');await wait("document.body.innerText.includes('[LOCAL DEMO] OpenDev Observatory')");await capture('01-public-campaigns','Two fixture campaigns; no provider claims');
 await go(`#/projects/${pid}`);await wait("document.body.innerText.includes('Open accountability chat')");await capture('02-project-overview','Campaign, budget and fixture reward tier');
 await click('Open financial transparency ledger');await wait("!!document.querySelector('.transparency .financial-value')");await capture('03-financial-transparency','Recorded funding, spending and public findings','.transparency');
 await go(`#/projects/${pid}/expenses/${eid}`);await wait("document.body.innerText.includes('Synthetic Demo Vendor')");await capture('04-expense-evidence','Published report and approved fixture metadata; no storage objects');
 await go(`#/projects/${pid}`);await wait("document.body.innerText.includes('Timeline')");
 await click('Timeline');await wait("document.querySelectorAll('.b-gantt-task').length>=3");await evaluate("(()=>{const s=document.querySelector('[aria-label=\"Roadmap timeline\"] select');s.value='monthAndYear';s.dispatchEvent(new Event('change',{bubbles:true}));})()");await capture('05-bryntum-roadmap','Real Bryntum Community rendering of synthetic commitments','[aria-label="Roadmap timeline"]');
 await go(`#/projects/${pid}/analytics`);await wait("document.querySelectorAll('.project-analytics canvas').length>=4");await capture('06-community-financial-analytics','Real Community charts and public data','.project-analytics .analytics-charts');
 await evaluate("(()=>{const s=document.querySelector('[name=analytics_view]');s.value='development';s.dispatchEvent(new Event('change',{bubbles:true}));})()");
 await wait("document.body.innerText.includes('Milestones 1–3 of 3')");await capture('07-development-analytics','Deadline and development record analytics','.project-analytics .analytics-charts');
 const csv=await evaluate(`fetch('/api/projects/${pid}/analytics/export/expenses').then(async r=>({status:r.status,text:await r.text()}))`);
 assert.equal(csv.status,200);assert.ok(csv.text.includes('35000')&&!csv.text.includes('DEMO_PRIVATE_'));
 await go(`#/maintainers/${owner}`);await wait("document.body.innerText.includes('opendev-demo-maintainer')&&document.body.innerText.includes('Delivery')");await capture('08-maintainer-history','Current-owner outcome aggregates; not a trust score');
 await go(`#/projects/${pid}`);await wait("document.body.innerText.includes('Open accountability chat')");await click('Open accountability chat');
 await wait("!!document.querySelector('.project-chat')");
 await evaluate("(()=>{const t=document.querySelector('.project-chat textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(t,'How much funding has the project received?');t.dispatchEvent(new Event('input',{bubbles:true}));})()");
 await evaluate("document.querySelector('.project-chat form').requestSubmit()");
 await wait("document.querySelector('.project-chat').innerText.includes('95000')&&document.querySelector('.project-chat').innerText.includes('Deterministic')");
 await evaluate("document.querySelector('.chat-sources').open=true");await capture('09-deterministic-chat','Backend-rendered answer with actual-mode label and public citations','.project-chat');
 assert.equal(await evaluate(`fetch('/api/projects/${manifest.private_project_id}').then(r=>r.status)`),404);
 assert.equal(await evaluate("fetch('/api/auth/me').then(r=>r.status)"),401);
 await go('#/create');await wait("document.body.innerText.includes('Sign in with GitHub to manage projects')");
 assert.equal(errors.length,0);
 await writeFile(join(output,'evidence.json'),JSON.stringify({scope:manifest.scope,viewport:{width:1440,height:1000},provider_status:'No external provider calls; seeded fixtures; no model inference',screenshots,checks:{public_pages:true,community_analytics:true,development_analytics:true,gantt:true,csv:true,deterministic_chat:true,private_project_404:true,unauthenticated_create_denied:true},runtime_exceptions:0},null,2)+'\n');
 console.log(`PASS: local synthetic demo, ${screenshots.length} real Chromium screenshots, charts/Gantt/chat/CSV and anonymous privacy boundaries`);
}finally{
 ws?.close();const exited=new Promise(resolve=>browser.once('exit',resolve));browser.kill('SIGTERM');await exited;await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100});
}
