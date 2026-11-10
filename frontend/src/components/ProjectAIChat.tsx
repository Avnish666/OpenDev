import { useEffect, useRef, useState, type FormEvent } from 'react';
import { AgentRequestError, citationPresentation, queryAgent, type AgentAnswer, type AgentMode } from '../api/agent';
import './ProjectAIChat.css';

const SUGGESTIONS = ['How much funding has the project received?', 'How much has been reported as spent?', 'Which budget categories are over budget?', 'Which milestones are overdue?', 'What progress has this project made?', "What is this maintainer's delivery history?", 'What financial information is missing?'];
const MODES: Record<AgentMode, string> = { deterministic: 'Deterministic', auto: 'Auto', llm: 'LLM' };
const STATUS: Record<AgentAnswer['answer_status'], string> = { answered: 'Answered from records', insufficient_evidence: 'Insufficient evidence', unsupported_question: 'Unsupported question', unavailable_source: 'Source unavailable', provider_unavailable: 'Model provider unavailable' };
const stamp = (date: string | null) => date && Number.isFinite(Date.parse(date)) ? new Date(date).toISOString() : 'Unknown';

export function CitationList({ answer, projectId, ownerId }: { answer: AgentAnswer; projectId: number; ownerId?: number }) {
  if (!answer.citations.length) return <p className="chat-notice">No citations were returned. This answer has no linked supporting evidence.</p>;
  return <details className="chat-sources"><summary>Evidence citations ({answer.citations.length})</summary>
    <p>Hashes identify retrieved public projections, not independent proof. Sources may change or lose public access; opening a source rechecks its current visibility.</p>
    <ol>{answer.citations.map((c, index) => {
      const e = answer.evidence_used.find(e => e.citation.reference === c.reference);
      const source = citationPresentation(c, e, projectId, ownerId);
      const freshness = e?.freshness === 'stale' ? 'Stale evidence' : e?.freshness === 'current_database_snapshot' ? 'Current database snapshot · not live verification' : 'Freshness unknown';
      return <li className="citation-card" key={`${c.reference}-${index}`}><div className="citation-heading"><span className="citation-number" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span><strong>{source.title}</strong><span className="chat-tag">{source.category}</span></div>
        <p>{source.explanation}</p><p className={e?.freshness === 'stale' ? 'chat-notice' : ''}>{freshness}</p>
        <dl><dt>Retrieved</dt><dd>{stamp(c.retrieved_at)}</dd><dt>Last source update</dt><dd>{stamp(e?.last_updated_at ?? null)}</dd></dl>
        {source.verifiedReference && <details><summary>Reference and projection hash</summary><code>{source.verifiedReference}</code></details>}
        {source.href ? <a href={source.href} target="_blank" rel="noopener noreferrer">Open current public source</a> : <p>No safe public link is available.</p>}
      </li>;
    })}</ol></details>;
}
export function AgentResponse({ answer, projectId, ownerId }: { answer: AgentAnswer; projectId: number; ownerId?: number }) {
  const unavailable = answer.answer_status === 'provider_unavailable';
  return <><div className="chat-meta"><strong>{STATUS[answer.answer_status]}</strong><span className="chat-tag chat-execution-tag" data-mode={answer.execution_mode} data-unavailable={unavailable}>Returned mode: {MODES[answer.execution_mode]}{unavailable ? ' · unavailable' : ''}</span></div>
    {unavailable && <p className="chat-notice">No live model answer is available. Try Deterministic mode.</p>}
    {answer.answer_status === 'insufficient_evidence' && <p className="chat-notice">The available records cannot fully establish the requested conclusion.</p>}
    <div className="chat-answer">{answer.answer}</div>
    {answer.evidence_used.some(e => e.freshness === 'stale') && <p className="chat-notice">This answer uses stale evidence. Review the source timestamps.</p>}
    <CitationList answer={answer} projectId={projectId} ownerId={ownerId} />
    <details className="chat-limitations"><summary>Limitations and uncertainty ({answer.limitations.length})</summary><ul>{answer.limitations.map((s, i) => <li key={i}>{s}</li>)}</ul><p>Confidence category: {answer.confidence.replaceAll('_', ' ')}. This is not a calibrated probability.</p></details>
  </>;
}
interface Exchange { id: number; question: string; mode: AgentMode; answer?: AgentAnswer; error?: string; cancelled?: boolean; retryAt?: number }
export default function ProjectAIChat(props: { projectId: number; ownerId?: number }) {
  return <ChatSession key={props.projectId} {...props} />;
}
function ChatSession({ projectId, ownerId }: { projectId: number; ownerId?: number }) {
  const [question, setQuestion] = useState(''); const [mode, setMode] = useState<AgentMode>('deterministic');
  const [messages, setMessages] = useState<Exchange[]>([]); const [busy, setBusy] = useState(false); const [notice, setNotice] = useState(''); const [cooldown, setCooldown] = useState(false);
  const active = useRef<AbortController | null>(null); const serial = useRef(0); const input = useRef<HTMLTextAreaElement>(null); const result = useRef<HTMLHeadingElement>(null);
  const mounted = useRef(true);
  const retryUntil = useRef(0);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; active.current?.abort(); active.current = null; }; }, [projectId]);
  useEffect(() => { const field = input.current; if (field) { field.style.height = 'auto'; field.style.height = `${Math.min(field.scrollHeight, 200)}px`; } }, [question]);
  useEffect(() => { if (!cooldown) return; const timer = setTimeout(() => setCooldown(false), Math.max(0, retryUntil.current - Date.now())); return () => clearTimeout(timer); }, [cooldown]);
  const valid = Array.from(question.trim()).length >= 3 && Array.from(question.trim()).length <= 1000;
  async function send(text: string, selectedMode: AgentMode) {
    if (active.current || cooldown || Array.from(text.trim()).length < 3 || Array.from(text.trim()).length > 1000) return;
    const controller = new AbortController(); active.current = controller;
    const id = ++serial.current;
    setBusy(true); setNotice(''); setQuestion('');
    setMessages(previous => [...previous, { id, question: text.trim(), mode: selectedMode }].slice(-12));
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 45000);
    try {
      const answer = await queryAgent(projectId, text, selectedMode, controller.signal);
      if (mounted.current && active.current === controller && !controller.signal.aborted) setMessages(previous => previous.map(m => m.id === id ? { ...m, answer } : m));
    } catch (e) {
      if (mounted.current && active.current === controller) {
        const cancelled = controller.signal.aborted && !timedOut;
        const retryAt = e instanceof AgentRequestError ? e.retryAt : undefined;
        const error = cancelled ? undefined : timedOut ? 'The browser request timed out. Backend work may still be completing.' : e instanceof Error ? e.message : 'Request failed.';
        setMessages(previous => (e instanceof AgentRequestError && [403, 404].includes(e.status) ? previous.filter(m => m.id === id) : previous).map(m => m.id === id ? { ...m, error, cancelled, retryAt } : m));
        if (retryAt) { retryUntil.current = retryAt; setCooldown(true); }
      }
    } finally {
      clearTimeout(timeout);
      if (mounted.current && active.current === controller) { active.current = null; setBusy(false); setTimeout(() => result.current?.focus(), 0); }
    }
  }
  function submit(event: FormEvent) { event.preventDefault(); if (valid) void send(question, mode); }
  function cancel() { active.current?.abort(); setNotice('Browser request cancelled. Backend cancellation is cooperative and may not stop inference immediately.'); }
  function clear() { active.current?.abort(); active.current = null; setBusy(false); setMessages([]); setQuestion(''); setNotice('Conversation cleared from this page.'); input.current?.focus(); }
  return <section className="project-chat" aria-labelledby={`chat-title-${projectId}`}>
    <div className="chat-heading"><div><span className="chat-eyebrow">Evidence desk / Public records · read only</span><h3 id={`chat-title-${projectId}`}>AI Accountability Assistant</h3></div><button type="button" className="chat-secondary" onClick={clear} disabled={!messages.length && !question}>Clear conversation</button></div>
    <p>Ask about funding, reported spending, commitments and public evidence. Reports and citations do not independently verify delivery or payment.</p>
    <p className="chat-caption">Each question is independent; earlier messages are not sent to the agent. History stays on this page only (up to 12 exchanges) and clears on refresh.</p>
    <div className="chat-workbench">
    <form className="chat-composer" onSubmit={submit}>
      <label htmlFor={`chat-question-${projectId}`}>Your question<textarea placeholder="Ask about this project’s funding or progress…" id={`chat-question-${projectId}`} ref={input} value={question} maxLength={1000} rows={2} aria-describedby={`chat-help-${projectId}`} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); if (valid) void send(question, mode); } }} /></label>
      <p id={`chat-help-${projectId}`} className="chat-caption">3–1,000 characters. Enter to ask; Shift+Enter for a new line. {Array.from(question).length}/1,000</p>
      <div className="chat-controls"><label>Execution mode<select value={mode} onChange={e => setMode(e.target.value as AgentMode)} disabled={busy}><option value="deterministic">Deterministic</option><option value="auto">Auto</option><option value="llm">LLM</option></select></label><span className="chat-requested-mode">Requested mode: <strong>{MODES[mode]}</strong></span><button type="submit" disabled={!valid || busy || cooldown}>{busy ? 'Answering…' : 'Ask question'}</button>{busy && <button type="button" className="chat-secondary" onClick={cancel}>Cancel request</button>}</div>
      <p className="chat-caption">Deterministic uses verified backend rules. LLM requests model-assisted tool selection and requires a configured provider. Auto may fall back to deterministic rules. Select LLM only when a model provider is available. Deterministic works without one.</p>
    </form>
    {!messages.length && <div className="chat-empty"><div className="chat-empty-intro"><h4>Start with the evidence</h4><p>Choose a supported question or write your own. No sign-in is required.</p></div><div className="chat-suggestions">{SUGGESTIONS.map(s => <button type="button" className="chat-secondary" key={s} onClick={() => { setQuestion(s); input.current?.focus(); }}>{s}</button>)}</div></div>}
    </div>
    <div className="chat-history" role="region" aria-label="Conversation history" aria-busy={busy}>{messages.map((m, index) => <div className="chat-exchange" key={m.id}>
      <div className="chat-user"><div className="chat-user-label"><strong>Question</strong></div><p>{m.question}</p><small>Requested: {MODES[m.mode]}</small></div>
      <article className="chat-assistant"><h4 className="assistant-answer-heading" tabIndex={-1} ref={index === messages.length - 1 ? result : undefined}>Accountability answer</h4>
        {m.answer ? <AgentResponse answer={m.answer} projectId={projectId} ownerId={ownerId} /> : m.cancelled ? <p>Request cancelled. No answer was accepted.</p> : m.error ? <><p role="alert">{m.error}</p>{m.retryAt && <p>Retry after {new Date(m.retryAt).toLocaleTimeString()}.</p>}<button type="button" disabled={busy || cooldown} onClick={() => void send(m.question, m.mode)}>Retry question</button></> : <p className="chat-loading"><span className="loading-dot" aria-hidden="true" />Retrieving bounded public evidence…</p>}
      </article></div>)}</div>
    <p role="status" aria-live="polite">{busy ? 'Preparing an evidence-backed answer…' : notice}</p>

  </section>;
}
