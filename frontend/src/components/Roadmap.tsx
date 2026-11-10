import { Component, lazy, Suspense, useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { api } from '../api/client';
import type { RoadmapPage, RoadmapMilestone, RoadmapStatus, RoadmapHistory } from '../api/roadmap';

class TimelineBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? <p role="alert">Unable to render the timeline. Use the milestone list or refresh the page.</p> : this.props.children; }
}

const Timeline = lazy(() => import('./RoadmapTimeline'));

const message = (error: unknown) => error instanceof Error ? error.message : 'Roadmap request failed';
const transitions: Record<RoadmapStatus, RoadmapStatus[]> = {
  planned: ['in_progress', 'cancelled'], in_progress: ['planned', 'submitted_for_review', 'cancelled'],
  submitted_for_review: ['in_progress', 'delivered', 'cancelled'], delivered: ['in_progress'], cancelled: ['planned'],
};

function CommitmentForm({ projectId, row, done }: { projectId: number; row?: RoadmapMilestone; done: () => void }) {
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const commitment = !row || row.status === 'planned';
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    const body: Record<string, unknown> = { display_order: Number(form.get('display_order')) };
    if (commitment) for (const key of ['title', 'description', 'deliverable_description', 'planned_start_date', 'planned_end_date']) body[key] = String(form.get(key));
    if (commitment && String(body.planned_start_date) > String(body.planned_end_date)) { setError('Start date must precede end date.'); return; }
    if (row) { body.expected_version = row.version; body.reason = String(form.get('reason')); }
    setBusy(true); setError('');
    try { await api(row ? `/api/roadmap/${row.id}` : `/api/projects/${projectId}/roadmap`, row ? 'PATCH' : 'POST', body); done(); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <form className="roadmap-editor" onSubmit={event => void submit(event)}><h4>{row ? 'Edit commitment / order' : 'Create roadmap commitment'}</h4>
    {commitment && <><label>Title<input name="title" required minLength={3} maxLength={200} defaultValue={row?.title} /></label>
      <label>Description<textarea name="description" required maxLength={10000} defaultValue={row?.description} /></label>
      <label>Specific deliverable<textarea name="deliverable_description" required minLength={10} maxLength={10000} defaultValue={row?.deliverable_description} /></label>
      <label>Planned start<input name="planned_start_date" type="date" required defaultValue={row?.planned_start_date} /></label>
      <label>Planned end<input name="planned_end_date" type="date" required defaultValue={row?.planned_end_date} /></label></>}
    <label>Display order (ties sort by milestone ID)<input name="display_order" type="number" required min={0} max={2147483647} step={1} defaultValue={row?.display_order ?? 0} /></label>
    {row && <label>Public reason for change<textarea name="reason" required minLength={10} maxLength={2000} /></label>}
    <p>Commitments and their change history are public on active projects. Never include private notes or credentials.</p>
    {error && <p role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Saving…' : 'Save commitment'}</button>
  </form>;
}

function MilestoneCard({ row, canManage, done }: { row: RoadmapMilestone; canManage: boolean; done: () => void }) {
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(false); const [history, setHistory] = useState<RoadmapHistory[]>(); const [historyPage, setHistoryPage] = useState(0);
  async function mutate(path: string, method: string, body: Record<string, unknown>) {
    setBusy(true); setError('');
    try { await api(path, method, { ...body, expected_version: row.version }); done(); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  function update(event: FormEvent<HTMLFormElement>, kind: 'status' | 'evidence') {
    event.preventDefault(); const form = new FormData(event.currentTarget); const body: Record<string, unknown> = { reason: String(form.get('reason')) };
    if (kind === 'status') body.status = form.get('status');
    else { body.evidence_type = form.get('evidence_type'); body.canonical_id = String(form.get('canonical_id')).trim(); }
    void mutate(`/api/roadmap/${row.id}/${kind}`, 'POST', body);
  }
  async function loadHistory(page: number) {
    setBusy(true); setError('');
    try { setHistory(await api<RoadmapHistory[]>(`/api/roadmap/${row.id}/history?limit=10&offset=${page * 10}`)); setHistoryPage(page); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <article className="milestone-card"><h4>{row.title} · {row.status.replaceAll('_', ' ')}</h4><p className="description">{row.description}</p>
    <h5>Deliverable commitment</h5><p className="description">{row.deliverable_description}</p>
    <p>Planned: {row.planned_start_date} → {row.planned_end_date}</p><p>Maintainer-reported delivery date: {row.actual_completion_date ?? 'Not delivered'}</p><p>{row.notice}</p>
    <h5>Development signals (not delivery certification)</h5><ul>{Object.entries(row.development_signals).map(([key, value]) => <li key={key}>{key.replaceAll('_', ' ')}: {value}</li>)}</ul>
    <h5>Linked GitHub evidence</h5>{!row.evidence.length && <p>No supporting links yet.</p>}
    <ul>{row.evidence.map(item => <li key={item.id}>{item.url ? <a href={item.url} target="_blank" rel="noreferrer">{item.evidence_type} · {item.canonical_id}</a> : `${item.evidence_type}: source unavailable`}
      <p>Observed state: {item.state ?? 'Unknown / commit observation'}{item.evidence_type === 'pull_request' && ` · merged: ${item.merged === null ? 'Unknown' : item.merged ? 'Yes' : 'No'}`}</p>
      {item.stale && <p>Stale or retained observation; refresh GitHub sync. Deleted items may remain.</p>}
      {canManage && <form onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); void mutate(`/api/roadmap/${row.id}/evidence/${item.id}`, 'DELETE', { reason: String(form.get('reason')) }); }}><label>Public removal reason<input name="reason" required minLength={10} maxLength={2000} /></label><button disabled={busy}>Unlink evidence (history retained)</button></form>}
    </li>)}</ul>
    {canManage && <><button disabled={busy} onClick={() => setEditing(!editing)}>Edit / reorder milestone</button>{editing && <CommitmentForm projectId={row.project_id} row={row} done={done} />}
      <form onSubmit={event => update(event, 'evidence')}><h5>Link synchronized GitHub evidence</h5>
        <label>Evidence type<select name="evidence_type"><option value="issue">Issue</option><option value="pull_request">Pull request</option><option value="github_milestone">GitHub milestone</option><option value="commit">Commit</option></select></label>
        <label>Canonical GitHub ID (not issue number or URL), or full commit SHA<input name="canonical_id" required maxLength={40} /></label>
        <label>Public link reason<textarea name="reason" required minLength={10} maxLength={2000} /></label><button disabled={busy}>Link evidence</button>
      </form>
      <form onSubmit={event => update(event, 'status')}><h5>Record a delivery-status assertion</h5><label>Next status<select name="status">{transitions[row.status].map(state => <option key={state} value={state}>{state.replaceAll('_', ' ')}</option>)}</select></label>
        <label>Public reason<textarea name="reason" required minLength={10} maxLength={2000} /></label><p>Submission and delivery require a supporting link. Delivery is an explicit maintainer assertion, not independent verification.</p><button disabled={busy}>Record status change</button></form>
    </>}
    {error && <p role="alert">{error}</p>}<button disabled={busy} onClick={() => void loadHistory(0)}>Read milestone history</button>
    {history && <section aria-label="Public milestone history">{!history.length && <p>No further entries.</p>}<ol>{history.map(entry => <li key={entry.id}><p>Version {entry.version} · {entry.action} · actor {entry.actor_id} · {new Date(entry.created_at).toLocaleString()}</p><p>{entry.previous_status ?? 'New'} → {entry.new_status}</p><p>{entry.reason}</p><details><summary>Recorded commitment changes</summary><pre className="description">{JSON.stringify({ before: entry.before, after: entry.after }, null, 2)}</pre></details></li>)}</ol><div className="actions"><button disabled={busy || !historyPage} onClick={() => void loadHistory(historyPage - 1)}>Newer history</button><button disabled={busy || history.length < 10} onClick={() => void loadHistory(historyPage + 1)}>Older history</button></div></section>}
  </article>;
}

export default function Roadmap({ projectId, canManage }: { projectId: number; canManage: boolean }) {
  const [view, setView] = useState<'list' | 'timeline'>('list');
  const [data, setData] = useState<RoadmapPage>(); const [error, setError] = useState('');
  const [page, setPage] = useState(0); const [version, setVersion] = useState(0); const [creating, setCreating] = useState(false);
  useEffect(() => {
    let live = true;
    api<RoadmapPage>(`/api/projects/${projectId}/roadmap?limit=10&offset=${page * 10}`).then(value => { if (live) { setData(value); setError(''); } }).catch(e => { if (live) setError(message(e)); });
    return () => { live = false; };
  }, [projectId, page, version]);
  function refresh() { setData(undefined); setVersion(v => v + 1); setCreating(false); }
  return <section className="roadmap-section"><p className="eyebrow">A PUBLIC PLAN FOR WHAT COMES NEXT</p><h3>Project roadmap and funding deliverables</h3><p>Maintainer commitments are separate from synchronized GitHub milestones. Issue closure and PR merges never automatically mark delivery.</p>
    <div className="actions roadmap-view-toggle"><button aria-pressed={view === 'list'} onClick={() => { setView('list'); refresh(); }}>Milestone list</button><button aria-pressed={view === 'timeline'} onClick={() => setView('timeline')}>Timeline</button></div>
    {view === 'timeline' && <TimelineBoundary><Suspense fallback={<p role="status">Loading timeline module…</p>}><Timeline projectId={projectId} canManage={canManage} /></Suspense></TimelineBoundary>}
    <div hidden={view !== 'list'}><button onClick={refresh}>Refresh roadmap</button>{canManage && <button onClick={() => setCreating(!creating)}>Create milestone</button>}
    {creating && <CommitmentForm projectId={projectId} done={refresh} />}
    {error && <p role="alert">{error}</p>}{!data && !error && <p role="status">Loading roadmap…</p>}
    {data && <>{!data.total && <p>No roadmap commitments have been published yet.</p>}{data.items.map(row => <MilestoneCard key={`${row.id}-${row.version}`} row={row} canManage={canManage} done={refresh} />)}
      <div className="actions"><button disabled={!page} onClick={() => { setData(undefined); setPage(p => p - 1); }}>Previous roadmap milestones</button><span>Page {page + 1}</span><button disabled={(page + 1) * 10 >= data.total} onClick={() => { setData(undefined); setPage(p => p + 1); }}>Next roadmap milestones</button></div></>}
    </div>
  </section>;
}
