/** Real React app -> local FastAPI -> isolated PostgreSQL; external providers mocked in pytest. */
import {createServer} from 'vite';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
process.env.VITE_API_URL='';
const targetAPI=process.env.PHASE5_TEST_API, project=process.env.PHASE5_TEST_PROJECT;
assert.match(targetAPI,/^http:\/\/127\.0\.0\.1:[0-9]+$/);assert.match(project,/^[0-9]+$/);
const server=await createServer({envDir:'/tmp/opendev-empty-env',server:{host:'127.0.0.1',port:0,proxy:{'/api':{target:targetAPI}}}});
await server.listen();const port=server.httpServer.address().port;
const profile=await mkdtemp(join(tmpdir(),'opendev-agent-e2e-'));
const browser=spawn('/usr/bin/chromium',['--headless','--no-sandbox','--disable-dev-shm-usage','--remote-debugging-port=0',`--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore'});
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
 const input=async text=>evaluate(`(()=>{const e=document.querySelector('textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,${JSON.stringify(text)});e.dispatchEvent(new Event('input',{bubbles:true}));e.focus();})()`);
 const ask=async(text,mode)=>{if(mode)await evaluate(`(()=>{const s=document.querySelector('select');s.value=${JSON.stringify(mode)};s.dispatchEvent(new Event('change',{bubbles:true}));})()`);await input(text);const n=await evaluate("document.querySelectorAll('.chat-exchange').length");await click('Ask question');await wait("document.querySelectorAll('.chat-exchange').length>"+n);await wait("![...document.querySelectorAll('.chat-assistant')].at(-1).textContent.includes('Retrieving bounded public evidence')");};
 await call('Runtime.enable');await call('Page.enable');await call('Page.navigate',{url:`http://127.0.0.1:${port}/#/projects/${project}`});
 await wait("document.body.innerText.includes('Open accountability chat')");
 await click('Open accountability chat');await wait("document.body.innerText.includes('Start with the evidence')");
 await click('How much funding has the project received?');await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});await wait("document.body.innerText.includes('2000 USD minor units')");
 assert.ok(await evaluate("document.body.innerText.includes('2000 USD minor units')"),await evaluate("document.body.innerText.slice(-2400)"));
 await evaluate("document.querySelector('.chat-sources summary').click()");
 const href=await evaluate("document.querySelector('.chat-sources a').getAttribute('href')");assert.equal(href,`/api/projects/${project}/transparency`);
 assert.equal(await evaluate(`fetch(${JSON.stringify(href)}).then(r=>r.json()).then(v=>v.financial_summary.net_recorded_funding_cents)`),2000);
 await evaluate("document.querySelector('.chat-sources a').click()");
 const targets=await call('Target.getTargets');assert.ok(targets.targetInfos.some(t=>t.url.includes('/transparency')));
 await ask('What progress has this project made?','llm');
 assert.ok(await evaluate("document.body.innerText.includes('Returned mode: LLM')"));
 assert.ok(await evaluate("document.body.innerText.includes('Retained GitHub snapshot counts')"));
 await evaluate("[...document.querySelectorAll('.chat-sources')].at(-1).querySelector('summary').click()");
 assert.ok(await evaluate("[...document.querySelectorAll('.chat-sources')].at(-1).querySelectorAll('li').length>=2"));
 await ask('Unsupported private proof question','deterministic');assert.ok(await evaluate("document.body.innerText.includes('Unsupported question')"));
 await ask('How much has been reported as spent?','deterministic');await click('Retry question');
 await wait("document.body.innerText.includes('1000 USD minor units')");
 await ask('Auto fallback check','auto');assert.ok(await evaluate("[...document.querySelectorAll('.chat-meta')].at(-1).textContent.includes('Deterministic')"));
 await input('hold');await click('Ask question');
 await wait("document.body.innerText.includes('Cancel request')");await new Promise(r=>setTimeout(r,700));await click('Cancel request');await wait("document.body.innerText.includes('Request cancelled. No answer')");
 await click('Clear conversation');assert.equal(await evaluate("document.querySelectorAll('.chat-exchange').length"),0);
 assert.equal(await evaluate("document.body.innerText.includes('PRIVATE_RECEIPT')"),false);
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'));
 assert.ok(await evaluate("!!document.querySelector('[aria-live=polite]')"));
 for(let i=0;i<3;i++){await call('Page.navigate',{url:`http://127.0.0.1:${port}/#/explore`});await wait("document.body.innerText.includes('Explore Projects')");await call('Page.navigate',{url:`http://127.0.0.1:${port}/#/projects/${project}`});await wait("document.body.innerText.includes('Open accountability chat')");}
 assert.equal(errors.length,0);
 console.log('PASS: real visitor project/chat, financial retrieval/citation navigation, mocked LLM roadmap+GitHub, unsupported status, retry, fallback, cancellation, mobile, announcements and repeated navigation');
}finally{ws?.close();const exited=new Promise(r=>browser.once('exit',r));browser.kill('SIGTERM');await server.close();await exited;await rm(profile,{recursive:true,force:true});}
