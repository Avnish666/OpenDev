import {before,after,test} from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';
import {mkdtemp,mkdir,readFile,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createElement} from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {agentFixture} from './agent-fixture.mjs';
let folder,client,Chat,ResponseView;
before(async()=>{
 folder=await mkdtemp(join(import.meta.dirname,'.compiled-chat-'));
 for(const file of ['api/client.ts','api/agent.ts','components/ProjectAIChat.tsx']){
  const source=(await readFile(new URL('../src/'+file,import.meta.url),'utf8')).replace('import.meta.env',"({VITE_API_URL:'https://api.invalid'})").replace("import './ProjectAIChat.css';",'');
  let {outputText}=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext,jsx:ts.JsxEmit.ReactJSX}});
  outputText=outputText.replace(/from '(\.[^']+)'/g,(_,p)=>`from '${p}.js'`);
  const dest=join(folder,file.replace(/\.tsx?$/,'.js'));await mkdir(join(dest,'..'),{recursive:true});await writeFile(dest,outputText);
 }
 client=await import(pathToFileURL(join(folder,'api/agent.js')));
 ({default:Chat,AgentResponse:ResponseView}=await import(pathToFileURL(join(folder,'components/ProjectAIChat.js'))));
});
after(async()=>{if(folder)await rm(folder,{recursive:true,force:true});});
const render=a=>renderToStaticMarkup(createElement(ResponseView,{answer:a,projectId:5,ownerId:7}));
test('public empty state, independent questions, keyboard hints and safest default',()=>{
 const html=renderToStaticMarkup(createElement(Chat,{projectId:5}));
 for(const s of ['Start with the evidence','No sign-in','Each question is independent','Clear conversation','Shift+Enter','aria-live="polite"'])assert.ok(html.includes(s),s);
 assert.match(html,/value="deterministic" selected=""/);
});
for(const mode of ['deterministic','llm'])test(`actual ${mode} response and public citations`,()=>{
 const html=render(agentFixture(mode));assert.match(html,new RegExp('Returned mode: '+(mode==='llm'?'LLM':'Deterministic')));assert.match(html,/Evidence citations \(1\)/);assert.match(html,/api.invalid\/api\/projects\/5\/transparency/);
});
test('auto fallback never advertises LLM execution',()=>{const a=agentFixture();a.limitations.push('LLM fallback: Provider unavailable.');assert.match(render(a),/Returned mode: Deterministic/);assert.doesNotMatch(render(a),/Returned mode: LLM/);});
for(const status of ['insufficient_evidence','unsupported_question','unavailable_source','provider_unavailable'])test(`limited ${status} result`,()=>{const html=render(agentFixture('llm',status));assert.match(html,/Limitations and uncertainty/);if(status==='provider_unavailable')assert.match(html,/No live model answer/);if(status==='insufficient_evidence')assert.match(html,/cannot fully establish/);});
test('missing citations and stale sources are explicit',()=>{const a=agentFixture();a.citations=[];a.evidence_used[0].freshness='stale';assert.match(render(a),/No citations were returned/);assert.match(render(a),/uses stale evidence/);});
for(const path of ['javascript:alert(1)','data:text/html,evil','//evil.invalid','https://evil.invalid/private','/api/documents/private/download','/api/projects/99/transparency'])test(`unsafe navigation rejected: ${path}`,()=>{const a=agentFixture();a.citations[0].api_path=path;assert.equal(client.citationPresentation(a.citations[0],a.evidence_used[0],5,7).href,undefined);});
test('unrecognized source identifiers and raw evidence are not rendered',()=>{const a=agentFixture();a.evidence_used[0].value={storage_key:'PRIVATE_STORAGE',extracted_json:'PRIVATE_OCR'};a.citations[0].source_id='PRIVATE_SOURCE';assert.match(render(a),/Unrecognized source/);assert.doesNotMatch(render(a),/PRIVATE_|storage_key|extracted_json/);});
test('malicious answer and limitations are escaped plain text',()=>{const a=agentFixture();a.answer='<img src=x onerror=alert(1)> [run](javascript:evil)';a.limitations=['<script>alert(1)</script>'];assert.match(render(a),/&lt;img/);assert.doesNotMatch(render(a),/<img|<script|href="javascript/);});
test('invalid response contracts and private evidence are rejected',()=>{assert.equal(client.parseAgentAnswer(agentFixture()).answer_status,'answered');for(const patch of [{execution_mode:'auto'},{answer_status:'fraud'},{citations:[{}]},{evidence_used:[{visibility:'manager_private'}]},{answer:4}])assert.throws(()=>client.parseAgentAnswer({...agentFixture(),...patch}),/invalid response/);});
test('only a single question is sent, with AbortSignal and no history',async()=>{const original=fetch;let call;globalThis.fetch=async(url,options)=>{call={url,options};return new Response(JSON.stringify(agentFixture()));};try{const c=new AbortController();await client.queryAgent(5,' funding ','auto',c.signal);assert.deepEqual(JSON.parse(call.options.body),{project_id:5,question:'funding',mode:'auto'});assert.equal(call.options.signal,c.signal);assert.equal(call.options.credentials,'include');assert.equal(call.options.cache,'no-store');assert.equal(call.url,'https://api.invalid/api/projects/5/agent/query');await assert.rejects(client.queryAgent(5,'x','auto',c.signal),/3–1,000/);}finally{globalThis.fetch=original;}});
for(const status of [400,422,401,403,404,429,503,504])test(`HTTP ${status} returns safe errors and retry metadata`,async()=>{const original=fetch;globalThis.fetch=async()=>new Response('PRIVATE_TRACE',{status,headers:{'Retry-After':'60'}});try{await assert.rejects(client.queryAgent(5,'funding','deterministic',new AbortController().signal),e=>e.status===status&&!e.message.includes('PRIVATE_TRACE')&&e.retryAfter===60);}finally{globalThis.fetch=original;}});
test('network errors, malformed JSON and cancellation remain distinct',async()=>{const original=fetch;try{globalThis.fetch=async()=>{throw new Error('PRIVATE_NETWORK');};await assert.rejects(client.queryAgent(5,'funding','llm',new AbortController().signal),/Network connection failed/);globalThis.fetch=async()=>new Response('PRIVATE_JSON');await assert.rejects(client.queryAgent(5,'funding','llm',new AbortController().signal),/invalid response/);const c=new AbortController();c.abort();globalThis.fetch=async()=>{throw new DOMException('Cancelled','AbortError');};await assert.rejects(client.queryAgent(5,'funding','llm',c.signal),e=>e.name==='AbortError');}finally{globalThis.fetch=original;}});
test('POST-only reward sources stay non-clickable and maintainer links are owner-scoped',()=>{
 const a=agentFixture();const e=a.evidence_used[0],c=a.citations[0];
 e.claim='reward_fulfillment';e.source_id='opendev:project:5:reward_fulfillment';Object.assign(c,{source_id:e.source_id,reference:e.source_id+'@sha256:'+c.projection_sha256,method:'POST',api_path:'/api/projects/5/agent/query',request_body:{project_id:5,question:'reward_fulfillment'}});
 assert.equal(client.citationPresentation(c,e,5,7).href,undefined);
 e.project_id=null;e.claim='history';e.source_type='maintainer';e.source_id='opendev:maintainer:7:history';Object.assign(c,{source_id:e.source_id,reference:e.source_id+'@sha256:'+c.projection_sha256,method:'GET',api_path:'/api/maintainers/7/credibility'});
 assert.equal(client.citationPresentation(c,e,5,7).href,'https://api.invalid/api/maintainers/7/credibility');
 assert.equal(client.citationPresentation(c,e,5,8).href,undefined);
});
