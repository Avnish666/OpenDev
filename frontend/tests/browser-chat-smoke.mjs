/** Explicit local Chromium check. Mock agent API; no model, auth, or external sources. */
import {agentFixture} from './agent-fixture.mjs';
import {createServer} from 'vite';
import {spawn} from 'node:child_process';
import {mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
const requests=[],held=[];
const server=await createServer({envDir:'/tmp/opendev-empty-env',server:{host:'127.0.0.1',port:0},appType:'custom'});
server.middlewares.use(async(req,res,next)=>{
 if(req.url==='/chat-smoke'){
  res.setHeader('Content-Type','text/html');res.end(await server.transformIndexHtml('/chat-smoke',`<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><main><div id="root"></div></main><script type="module">import React from 'react';import {createRoot} from 'react-dom/client';import Chat from '/src/components/ProjectAIChat.tsx';import '/src/App.css';window.chatRoot=createRoot(document.getElementById('root'));window.showChat=(id)=>window.chatRoot.render(React.createElement(Chat,{projectId:id,ownerId:7}));window.showChat(5);</script></body></html>`));return;
 }
 if(req.url!=='/api/projects/5/agent/query'){next();return;}
 let body='';for await(const chunk of req)body+=chunk;
 const data=JSON.parse(body);requests.push(data);res.setHeader('Content-Type','application/json');
 if(data.question==='hold'){held.push(res);return;}
 if(data.question==='rate'){res.statusCode=429;res.setHeader('Retry-After','1');res.end('{}');return;}
 if(data.question==='failure'){res.statusCode=500;res.end('{"detail":"PRIVATE_TRACE"}');return;}
 if(data.question==='hidden'){res.statusCode=404;res.end('{}');return;}
 const a=agentFixture(data.mode==='llm'?'llm':'deterministic');
 if(data.mode==='auto')a.limitations.push('LLM fallback: Provider unavailable.');
 if(data.question==='stale')a.evidence_used[0].freshness='stale';
 if(data.question==='unsupported')a.answer_status='unsupported_question';
 if(data.question==='limited')a.answer_status='insufficient_evidence';
 if(data.question==='provider')a.answer_status='provider_unavailable';
 if(data.question==='unsafe')a.citations[0].api_path='javascript:alert(1)';
 if(data.question==='missing')a.citations=[];
 if(data.question==='attack')a.answer='<img src=x onerror="window.chatPwned=true">';
 res.end(JSON.stringify(a));
});
await server.listen();const port=server.httpServer.address().port;
const profile=await mkdtemp(join(tmpdir(),'opendev-chat-'));
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
 const ask=async(text,mode)=>{if(mode)await evaluate(`(()=>{const s=document.querySelector('select');s.value=${JSON.stringify(mode)};s.dispatchEvent(new Event('change',{bubbles:true}));})()`);await input(text);await click('Ask question');await wait("!document.querySelector('button[type=submit]').textContent.includes('Answering')");};
 await call('Runtime.enable');await call('Page.enable');await call('Page.navigate',{url:`http://127.0.0.1:${port}/chat-smoke`});
 await wait("document.body.innerText.includes('Start with the evidence')");assert.equal(requests.length,0);
 assert.equal(await evaluate("document.querySelector('select').value"),'deterministic');
 await click('How much funding has the project received?');assert.equal(await evaluate("document.activeElement.tagName"),'TEXTAREA');
 await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13});
 await wait("document.body.innerText.includes('Net recorded funding')");assert.equal(requests.length,1);
 assert.deepEqual(Object.keys(requests[0]).sort(),['mode','project_id','question']);
 await evaluate("document.querySelector('.chat-sources summary').click()");await wait("document.querySelector('.chat-sources').open");
 assert.equal(await evaluate("document.querySelector('.chat-sources a').getAttribute('href')"),'/api/projects/5/transparency');
 await input('line one');await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,modifiers:8,text:'\r'});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,modifiers:8});
 assert.equal(requests.length,1);assert.ok((await evaluate("document.querySelector('textarea').value")).includes('\n'));
 console.log('PASS: public visitor, supported suggestion, Enter submission, Shift+Enter, citation expansion and safe source');
 await ask('funding','llm');assert.ok(await evaluate("document.body.innerText.includes('Returned mode: LLM')"));
 await ask('funding','auto');assert.ok(await evaluate("[...document.querySelectorAll('.chat-meta')].at(-1).textContent.includes('Deterministic')"));
 for(const [question,expected] of [['stale','uses stale evidence'],['limited','cannot fully establish'],['unsupported','Unsupported question'],['provider','No live model answer'],['missing','No citations were returned']]){await ask(question);assert.ok(await evaluate(`document.body.innerText.includes(${JSON.stringify(expected)})`));}
 await ask('unsafe');assert.equal(await evaluate("[...document.querySelectorAll('.chat-sources')].at(-1).querySelectorAll('a').length"),0);
 await ask('attack');assert.equal(await evaluate('!!window.chatPwned'),false);assert.equal(await evaluate("document.querySelectorAll('.chat-answer img').length"),0);
 console.log('PASS: actual execution modes, auto fallback, stale/missing citations, limited statuses and malicious text');
 await input('hold');await click('Ask question');await wait("document.body.innerText.includes('Cancel request')");
 const before=requests.length;await evaluate("document.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))");await new Promise(r=>setTimeout(r,100));assert.equal(requests.length,before);
 await click('Cancel request');await wait("document.body.innerText.includes('Request cancelled. No answer')");assert.ok(await evaluate("document.body.innerText.includes('may not stop inference immediately')"));
 await input('hold');await click('Ask question');await wait("document.body.innerText.includes('Cancel request')");await click('Clear conversation');await wait("document.body.innerText.includes('Start with the evidence')");
 for(const res of held)if(!res.destroyed)res.end(JSON.stringify(agentFixture()));
 await new Promise(r=>setTimeout(r,150));assert.equal(await evaluate("document.querySelectorAll('.chat-exchange').length"),0);
 console.log('PASS: duplicate prevention, abort cancellation, clear during inference and ignored late responses');
 await ask('failure');assert.ok(await evaluate("document.body.innerText.includes('could not answer')"));assert.ok(!(await evaluate('document.body.innerText')).includes('PRIVATE_TRACE'));
 await click('Retry question');await wait("!document.querySelector('button[type=submit]').textContent.includes('Answering')");
 await ask('rate');assert.equal(await evaluate("[...document.querySelectorAll('button')].find(b=>b.textContent==='Retry question'&&!b.disabled)===undefined"),true);
 await new Promise(r=>setTimeout(r,1100));await wait("[...document.querySelectorAll('button')].some(b=>b.textContent==='Retry question'&&!b.disabled)");
 await ask('funding');await ask('hidden');assert.equal(await evaluate("document.querySelectorAll('.chat-exchange').length"),1);assert.ok(await evaluate("document.body.innerText.includes('no longer publicly available')"));
 await click('Clear conversation');
 await call('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 await ask('funding');await evaluate("document.querySelector('.chat-sources summary').click()");
 assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth'));
 await writeFile('/tmp/opendev-chat-mobile.png',Buffer.from((await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true})).data,'base64'));
 assert.ok(await evaluate("!!document.querySelector('label[for=chat-question-5]') && !!document.querySelector('[aria-live=polite]')"));
 await evaluate("localStorage.setItem('chat-test-marker','safe')");await call('Page.reload');await wait("document.body.innerText.includes('Start with the evidence')");assert.equal(await evaluate("document.querySelectorAll('.chat-exchange').length"),0);assert.equal(await evaluate('localStorage.length'),1);
 assert.equal(errors.length,0);
 await input('hold');await click('Ask question');await wait("document.body.innerText.includes('Cancel request')");
 await evaluate('window.showChat(6)');await wait("!!document.getElementById('chat-question-6')");
 assert.equal(await evaluate("document.querySelectorAll('.chat-exchange').length"),0);
 console.log('PASS: safe retry/rate limit, revoked visibility clears old answers, mobile no overflow, accessibility hooks, no persisted transcript and project-navigation cleanup');
}finally{for(const res of held)res.destroy();ws?.close();const exited=new Promise(r=>browser.once('exit',r));browser.kill('SIGTERM');await server.close();await exited;await rm(profile,{recursive:true,force:true});}
