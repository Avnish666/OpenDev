/** Local analytics SDK acceptance; no live accounts, paid service or private data. */
import {analyticsFixture} from './analytics-fixture.mjs';
import {createServer} from 'vite';import {spawn} from 'node:child_process';import {mkdtemp,readFile,rm} from 'node:fs/promises';import {tmpdir} from 'node:os';import {join} from 'node:path';import assert from 'node:assert/strict';
if(process.env.TEST_STUDIO==='1')process.env.ANALYTICS_STUDIO_EVALUATION='true';
let fail=false,empty=false;
const server=await createServer({envDir:'/tmp/opendev-empty-env',server:{host:'127.0.0.1',port:0},appType:'custom'});
server.middlewares.use(async(req,res,next)=>{
 if(req.url==='/analytics-smoke'){res.setHeader('Content-Type','text/html');res.end(await server.transformIndexHtml('/analytics-smoke',`<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><main><div id="root"></div></main><script type="module">import React from 'react';import {createRoot} from 'react-dom/client';import View from '/src/components/ProjectAnalytics.tsx';import '/src/App.css';createRoot(document.getElementById('root')).render(React.createElement(View,{projectId:5}));</script></body></html>`));return;}
 if(req.url.startsWith('/api/projects/5/analytics/overview')){res.setHeader('Content-Type','application/json');if(fail){res.statusCode=503;res.end('{}');return;}const d=analyticsFixture();d.expenses[0].category='<img src=x onerror=window.analyticsPwned=true>';if(empty){d.budget=[];d.expenses=[];d.expense_total=0;}res.end(JSON.stringify(d));return;}next();
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
 await call('Page.navigate',{url:`http://127.0.0.1:${port}/analytics-smoke`});await wait("document.querySelectorAll('.ag-row').length>0 && document.querySelectorAll('canvas').length>=2");
 assert.ok(await evaluate("document.body.innerText.includes('40.00 USD')"));assert.equal(requests.some(u=>u.includes('/studio/node_modules/')),false);
 assert.ok(await evaluate("document.body.innerText.includes('AG Charts Community')"));
 await evaluate("document.querySelector('select').value='studio';document.querySelector('select').dispatchEvent(new Event('change',{bubbles:true}))");
 if(process.env.TEST_STUDIO==='1'){
  await wait("!!document.querySelector('[studio-id=opendev-analytics]') || document.body.innerText.includes('could not initialize')");
  assert.ok(await evaluate("!!document.querySelector('[studio-id=opendev-analytics]')"),await evaluate('document.body.innerText'));
  assert.ok(requests.some(u=>u.includes('/studio/')));
  console.log('PASS: official AG Studio 3.0.0 initialized from isolated packages for local evaluation only');
  await evaluate("document.querySelector('select').value='community';document.querySelector('select').dispatchEvent(new Event('change',{bubbles:true}))");
 }else{await wait("document.body.innerText.includes('unavailable or not authorized')");await click('Return to Community view');}
 await wait("document.querySelectorAll('.ag-row').length>0");
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'));
 empty=true;await click('Refresh analytics');await wait("document.body.innerText.includes('No public budget')");
 fail=true;await click('Refresh analytics');await wait("document.body.innerText.includes('Unable to load this public')");
 fail=false;empty=false;await click('Refresh analytics');await wait("document.querySelectorAll('.ag-row').length>0");
 assert.equal(await evaluate('!!window.analyticsPwned'),false);assert.equal(await evaluate("document.querySelectorAll('.ag-cell img').length"),0);assert.equal(errors.length,0);
 console.log('PASS: actual Community charts/grid, safe default, license gate/switching, empty/error recovery, 390px layout and clean unmount');
}finally{ws?.close();const exit=new Promise(r=>browser.once('exit',r));browser.kill('SIGTERM');await server.close();await exit;await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100});}
