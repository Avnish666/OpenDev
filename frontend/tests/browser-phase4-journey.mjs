/** Opt-in bridge to a disposable PostgreSQL/FastAPI fixture, invoked by pytest. */
import { createServer } from 'vite';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';
const origin=process.env.PHASE4_TEST_API, port=Number(process.env.PHASE4_TEST_PORT);
const project=Number(process.env.PHASE4_TEST_PROJECT), milestone=Number(process.env.PHASE4_TEST_MILESTONE), end=process.env.PHASE4_TEST_END;
assert.match(origin??'',/^http:\/\/127\.0\.0\.1:\d+$/);assert.ok(port&&project&&milestone&&end&&process.env.PHASE4_TEST_SESSION);
const server=await createServer({envDir:'/tmp/opendev-empty-env',appType:'custom',server:{host:'127.0.0.1',port,strictPort:true,proxy:{'/api':{target:origin,changeOrigin:false}}}});
server.middlewares.use(async(req,res,next)=>{
  if(req.url!=='/phase4-journey'){next();return;}
  res.setHeader('Content-Type','text/html');
  res.end(await server.transformIndexHtml('/phase4-journey',`<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body><div id="root"></div><script type="module">import React from 'react';import {createRoot} from 'react-dom/client';import Progress from '/src/components/ProjectProgress.tsx';createRoot(document.getElementById('root')).render(React.createElement(Progress,{projectId:${project},canManage:true}));</script></body></html>`));
});
await server.listen();
const profile=await mkdtemp(join(tmpdir(),'opendev-phase4-db-browser-'));
const chrome=spawn('/usr/bin/chromium',['--headless','--no-sandbox','--disable-dev-shm-usage','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore'});
let ws;
try{
  let debugging;
  for(let i=0;i<100;i++){try{debugging=(await readFile(join(profile,'DevToolsActivePort'),'utf8')).split('\n')[0];break;}catch{await new Promise(r=>setTimeout(r,100));}}
  assert.ok(debugging);
  const target=await(await fetch(`http://127.0.0.1:${debugging}/json/new?about:blank`,{method:'PUT'})).json();
  ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));
  let id=0;const pending=new Map(),errors=[];
  ws.addEventListener('message',({data})=>{const m=JSON.parse(data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);if(m.error)p.reject(m.error);else p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);});
  const call=(method,params={})=>new Promise((resolve,reject)=>{pending.set(++id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
  const evaluate=async expression=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
  const wait=async expression=>{for(let i=0;i<300;i++){if(await evaluate(expression))return;assert.equal(errors.length,0,errors.join('\n'));await new Promise(r=>setTimeout(r,100));}throw Error('Timeout: '+expression+'\n'+await evaluate('document.body.innerText'));};
  await call('Runtime.enable');await call('Page.enable');await call('Network.enable');
  assert.ok((await call('Network.setCookie',{name:'app_session',value:process.env.PHASE4_TEST_SESSION,url:`http://127.0.0.1:${port}`,httpOnly:true,sameSite:'Lax'})).success);
  await call('Page.navigate',{url:`http://127.0.0.1:${port}/phase4-journey`});
  await wait("document.querySelector('[aria-label=\"Public project progress\"]') !== null");
  await wait("[...document.querySelectorAll('button')].some(b=>b.textContent==='Timeline')");
  await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Timeline').click()");
  await wait("document.querySelectorAll('.b-gantt-task-wrap').length === 1");
  await evaluate(`(()=>{const s=[...document.querySelectorAll('select')].find(s=>s.textContent.includes('Choose a milestone'));s.value='${milestone}';s.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  await wait("document.body.innerText.includes('Propose planned dates')");
  await evaluate(`(()=>{const f=[...document.querySelectorAll('form')].find(f=>f.textContent.includes('Propose planned dates'));f.querySelector('[name=end]').value='${end}';f.requestSubmit();})()`);
  await wait("document.body.innerText.includes('Confirm commitment date change')");
  await evaluate(`(()=>{const f=document.querySelector('[aria-label="Confirm schedule change"]');f.querySelector('textarea').value='Browser confirmed revised public commitment';f.requestSubmit();})()`);
  await wait(`!document.body.innerText.includes('Confirm commitment date change') && document.body.innerText.includes('${end}')`);
  const rows=await evaluate(`fetch('/api/projects/${project}/roadmap').then(r=>r.json())`);
  assert.equal(rows.items.find(r=>r.id===milestone).planned_end_date,end);
  const history=await evaluate(`fetch('/api/roadmap/${milestone}/history').then(r=>r.json())`);
  assert.ok(history.some(h=>h.action==='edited'&&h.reason==='Browser confirmed revised public commitment'));
  // Reload with the actual session removed; the same project/dashboard stays public.
  await call('Network.deleteCookies',{name:'app_session',url:`http://127.0.0.1:${port}`});
  assert.equal(await evaluate("fetch('/api/auth/me').then(r=>r.status)"),401);
  const visitor=await evaluate(`fetch('/api/projects/${project}/progress-summary').then(r=>r.json())`);
  assert.equal(visitor.project_id,project);assert.equal(visitor.counts.planned,1);
  assert.equal(errors.length,0);
  console.log('PASS: Chromium → Vite proxy → FastAPI → disposable PostgreSQL: authenticated schedule confirmation, immutable history and anonymous dashboard');
}finally{
  ws?.close();const exited=new Promise(r=>chrome.exitCode!==null?r():chrome.once('exit',r));chrome.kill('SIGTERM');await server.close();await exited;await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100});
}
