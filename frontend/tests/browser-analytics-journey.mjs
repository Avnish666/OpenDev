/** Real React app -> local FastAPI -> isolated PostgreSQL; external providers mocked in pytest. */
import {createServer} from 'vite';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
process.env.VITE_API_URL='';
const targetAPI=process.env.PHASE6_TEST_API, project=process.env.PHASE6_TEST_PROJECT;
assert.match(targetAPI,/^http:\/\/127\.0\.0\.1:[0-9]+$/);assert.match(project,/^[0-9]+$/);
if(process.env.TEST_STUDIO==='1')process.env.ANALYTICS_STUDIO_EVALUATION='true';
const server=await createServer({envDir:'/tmp/opendev-empty-env',server:{host:'127.0.0.1',port:0,proxy:{'/api':{target:targetAPI}}}});
await server.listen();const port=server.httpServer.address().port;
const profile=await mkdtemp(join(tmpdir(),'opendev-agent-e2e-'));
const browser=spawn('/usr/bin/chromium',['--headless','--no-sandbox','--disable-dev-shm-usage','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore'});
const downloads=await mkdtemp(join(tmpdir(),'opendev-audit-csv-'));
let ws;
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
 await call('Runtime.enable');await call('Page.enable');await call('Page.setDownloadBehavior',{behavior:'allow',downloadPath:downloads});
 await call('Page.navigate',{url:`http://127.0.0.1:${port}/#/projects/${project}`});await wait("document.body.innerText.includes('Open project analytics')");
 await evaluate(`document.querySelector('a[href="#/projects/${project}/analytics"]').click()`);
 await wait("document.querySelectorAll('.project-analytics canvas').length>=4 && document.querySelectorAll('.project-analytics .ag-row').length>0");
 assert.ok(await evaluate("document.querySelector('.project-analytics').innerText.includes('60.00 USD')"));
 const select=async(name,value)=>evaluate(`(()=>{const s=document.querySelector('[name="${name}"]');s.value=${JSON.stringify(value)};s.dispatchEvent(new Event('change',{bubbles:true}));})()`);
 await select('analytics_view','spending');await wait("document.querySelector('.project-analytics').innerText.includes('Spending & Evidence')");
 await select('analytics_view','development');await wait("document.body.innerText.includes('Milestones 1–3 of 3')");
 assert.ok(await evaluate("document.querySelector('.project-analytics').innerText.includes('2026-10-31') && document.querySelector('.project-analytics').innerText.includes('2026-12-01')"));
 await select('analytics_view','maintainer');await wait("document.querySelector('.project-analytics').innerText.includes('Maintainer analytics')");
 await select('analytics_view','financial');await wait("!!document.querySelector('.project-analytics .financial-cards')");
 await evaluate("(()=>{const input=document.querySelector('input[name=category]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,'Development');input.dispatchEvent(new Event('input',{bubbles:true}));})()");
 await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Apply dashboard filters').focus()");
 await call('Input.dispatchKeyEvent',{type:'keyDown',key:' ',code:'Space',windowsVirtualKeyCode:32});await call('Input.dispatchKeyEvent',{type:'keyUp',key:' ',code:'Space',windowsVirtualKeyCode:32});
 await wait("document.body.innerText.includes('of 1 matching published expenses') && document.querySelectorAll('.project-analytics .ag-row').length>0");
 await click('Download CSV');await wait("document.body.innerText.includes('CSV download started')");
 let csv;for(let i=0;i<100;i++){try{csv=await readFile(join(downloads,`opendev-project-${project}-expenses.csv`),'utf8');break;}catch{await new Promise(r=>setTimeout(r,50));}}
 assert.ok(csv.includes('Development')&&csv.includes('1000'));assert.ok(!csv.includes('Hosting,1500'));assert.ok(!csv.includes('PRIVATE_'));
 const proof=await evaluate(`fetch('/api/projects/${project}/analytics/overview?category=Development').then(r=>r.json())`);
 const parsed=[];let row=[],field='',quoted=false;for(let i=0;i<csv.length;i++){const c=csv[i];if(c==='"'){if(quoted&&csv[i+1]==='"'){field+='"';i++;}else quoted=!quoted;}else if(c===','&&!quoted){row.push(field);field='';}else if(c==='\n'&&!quoted){row.push(field.replace(/\r$/,''));parsed.push(row);row=[];field='';}else field+=c;}
 const header=parsed[0].map(v=>v.replace(/^\ufeff/,''));assert.equal(parsed.length,2);assert.equal(parsed[1][header.indexOf('amount_cents')],'1000');assert.equal(parsed[1][header.indexOf('category')],'Development');assert.equal(Number(parsed[1][header.indexOf('id')]),proof.expenses[0].id);
 assert.equal(proof.expense_total,1);assert.equal(proof.expenses[0].amount_cents,1000);assert.equal(proof.financial.published_reported_spending_cents,2500);assert.equal(proof.financial.expenses_with_documents_count,1);
 assert.equal(await evaluate(`fetch('/api/projects/${process.env.PHASE6_PRIVATE_PROJECT}/analytics/export/expenses').then(r=>r.status)`),404);
 if(process.env.TEST_STUDIO==='1'){
  for(let i=0;i<3;i++){
   await evaluate("(()=>{const s=document.querySelector('.project-analytics select');s.value='studio';s.dispatchEvent(new Event('change',{bubbles:true}));})()");
   await wait("document.querySelectorAll('[studio-id=opendev-analytics] canvas').length>=4");assert.equal(await evaluate("document.querySelectorAll('[studio-id=opendev-analytics]').length"),1);
   assert.ok(await evaluate("document.querySelector('.project-analytics').innerText.includes('60.00 USD')"));
   await evaluate("(()=>{const s=document.querySelector('.project-analytics select');s.value='community';s.dispatchEvent(new Event('change',{bubbles:true}));})()");await wait("!document.querySelector('[studio-id=opendev-analytics]')");
  }
 }
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'));
 for(let i=0;i<2;i++){await call('Page.navigate',{url:`http://127.0.0.1:${port}/#/analytics`});await wait("document.body.innerText.includes('Public project analytics')");await wait(`!!document.querySelector('a[href="#/projects/${project}/analytics"]')`);await evaluate(`document.querySelector('a[href="#/projects/${project}/analytics"]').click()`);await wait("document.querySelectorAll('.project-analytics canvas').length>=4");}
 assert.equal(errors.length,0);console.log('PASS: real signed-out PostgreSQL analytics journey, four presets, keyboard apply, financial/source parity, full filtered CSV, private 404, mobile and repeated renderer/navigation cleanup');
}finally{ws?.close();const exited=new Promise(r=>browser.once('exit',r));browser.kill('SIGTERM');await server.close();await exited;await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100});await rm(downloads,{recursive:true,force:true});}
