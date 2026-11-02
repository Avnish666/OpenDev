import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { BryntumGantt, type BryntumGanttProps } from '@bryntum/gantt-react-community';
import { loadTimeline, mapRoadmap, proposal, saveSchedule, calendarDate, shiftDate, type DateProposal } from '../api/gantt';
import '@bryntum/core-community/fontawesome/css/fontawesome.css';
import '@bryntum/core-community/fontawesome/css/solid.css';
import '@bryntum/gantt-community/gantt.css';
import '@bryntum/gantt-community/svalbard.css';
import './RoadmapTimeline.css';

const message = (e: unknown) => e instanceof Error ? e.message : 'Timeline failed';

export default function RoadmapTimeline({ projectId, canManage }: { projectId: number; canManage: boolean }) {
  const [data, setData] = useState<Awaited<ReturnType<typeof loadTimeline>>>(); const [error, setError] = useState('');
  const [version, setVersion] = useState(0); const [generation, setGeneration] = useState(0); const [zoom, setZoom] = useState('weekAndDayLetter');
  const [selected, setSelected] = useState<number>(); const [pending, setPending] = useState<DateProposal>(); const [busy, setBusy] = useState(false);
  const drag = useRef<DateProposal | undefined>(undefined);
  useEffect(() => {
    let live = true;
    loadTimeline(projectId).then(value => { if (live) { setData(value); setError(''); } }).catch(e => { if (live) setError(message(e)); });
    return () => { live = false; };
  }, [projectId, version]);
  const mapped = useMemo(() => { try { return data ? { value: mapRoadmap(data.rows, data.edges, projectId, canManage), error: '' } : undefined; } catch (e) { return { value: undefined, error: message(e) }; } }, [data, projectId, canManage]);
  function refresh() { setPending(undefined); setData(undefined); setVersion(v => v + 1); }
  function propose(dates: DateProposal | undefined) {
    setGeneration(g => g + 1); // Discard widget mutations: React/backend dates stay authoritative.
    if (dates && canManage && data?.rows.some(r => r.id === dates.milestoneId && r.status === 'planned')) { setPending(dates); setSelected(dates.milestoneId); }
  }
  const props: BryntumGanttProps = {
    height: 480, snap: true, timeResolution: { unit: 'day', increment: 1 }, readOnly: !canManage || busy || !!pending, viewPreset: zoom,
    columns: [{ type: 'name', width: 220, htmlEncode: true }],
    project: { ...mapped?.value, autoLoad: false, autoSync: false },
    basicTaskEditFeature: false, cellEditFeature: false, taskMenuFeature: false, taskDragCreateFeature: false,
    taskTooltipFeature: false, scheduleTooltipFeature: false, cellMenuFeature: false,
    taskDragFeature: canManage, taskResizeFeature: canManage ? { leftHandle: false, rightHandle: true } : false,
    dependenciesFeature: { allowCreate: false },
    taskRenderer: ({ taskRecord }) => ({ tag: 'span', text: `${taskRecord.name} · ${data?.rows.find(r => r.id === taskRecord.id)?.status.replaceAll('_', ' ') ?? ''}` }),
    onTaskClick: ({ taskRecord }) => setSelected(Number(taskRecord.id)),
    onBeforeTaskDrag: ({ taskRecord }) => { drag.current = undefined; return !pending && !busy && canManage && data?.rows.find(r => r.id === taskRecord.id)?.status === 'planned'; },
    onTaskDrag: ({ taskRecords, startDate, endDate }) => { if (taskRecords.length === 1) drag.current = proposal(Number(taskRecords[0].id), startDate, endDate); },
    onBeforeTaskDropFinalize: ({ context }) => { const dates = context.valid ? drag.current : undefined; context.valid = false; context.async = true; void Promise.resolve(context.finalize(false)).then(() => propose(dates)); },
    onBeforeTaskResize: ({ taskRecord }) => !pending && !busy && canManage && data?.rows.find(r => r.id === taskRecord.id)?.status === 'planned',
    onBeforeTaskResizeFinalize: ({ context, taskRecord }) => {
      const row = data?.rows.find(r => r.id === taskRecord.id);
      const dates = row ? proposal(row.id, calendarDate(row.planned_start_date), context.endDate) : undefined;
      context.async = true; void Promise.resolve(context.finalize(false)).then(() => propose(dates));
    },
  };
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const row = data?.rows.find(r => r.id === pending?.milestoneId);
    if (!row || !pending) return;
    const reason = String(new FormData(event.currentTarget).get('reason')); setBusy(true); setError('');
    try { await saveSchedule(row, pending, reason, canManage); refresh(); }
    catch (e) { setError(`${message(e)}. Original dates remain visible. Refresh before retrying a version conflict.`); setPending(undefined); setGeneration(g => g + 1); }
    finally { setBusy(false); }
  }
  const row = data?.rows.find(r => r.id === selected);
  const dates = mapped?.value?.tasks;
  const start = dates?.length ? new Date(Math.min(...dates.map(t => (t.startDate as Date).getTime()))) : undefined;
  const end = dates?.length ? shiftDate(new Date(Math.max(...dates.map(t => (t.endDate as Date).getTime()))), 3) : undefined;
  return <section aria-label="Roadmap timeline"><div className="actions"><button disabled={busy} onClick={refresh}>Reload timeline</button><label>Timeline scale<select value={zoom} onChange={e => setZoom(e.target.value)}><option value="dayAndWeek">Day</option><option value="weekAndDayLetter">Week</option><option value="monthAndYear">Month</option></select></label></div>
    <p>Dependency arrows are read-only finish-to-start relationships. They never reschedule commitments. No delivery completion percentage is inferred.</p>
    {error && <p role="alert">{error}</p>}{mapped?.error && <p role="alert">{mapped.error}</p>}{!data && !error && <p role="status">Loading timeline…</p>}
    {data?.sync.stale && <p role="status">GitHub observations are stale or unavailable.</p>}
    {data && <p>Last successful GitHub synchronization: {data.sync.last_successful_sync_at ? new Date(data.sync.last_successful_sync_at).toLocaleString() : 'Never'}</p>}
    {mapped?.value && !mapped.value.tasks.length && <p>No roadmap milestones to display.</p>}
    {!!mapped?.value?.tasks.length && <div className="opendev-gantt"><BryntumGantt key={`${generation}-${version}`} {...props} startDate={start} endDate={end} /></div>}
    {data && <label>Select milestone (also available without dragging)<select value={selected ?? ''} onChange={e => setSelected(e.target.value ? Number(e.target.value) : undefined)}><option value="">Choose a milestone</option>{data.rows.map(r => <option key={r.id} value={r.id}>{r.title} · {r.status}</option>)}</select></label>}
    {row && <article><h4>{row.title} · {row.status.replaceAll('_', ' ')}</h4><p>{row.deliverable_description}</p><p>{row.planned_start_date} → {row.planned_end_date}</p><p>{row.notice}</p><ul>{Object.entries(row.development_signals).map(([key, value]) => <li key={key}>{key.replaceAll('_', ' ')}: {value}</li>)}</ul><ul>{row.evidence.map(e => <li key={e.id}>{e.url ? <a href={e.url} target="_blank" rel="noreferrer">{e.evidence_type} · {e.canonical_id}</a> : `${e.evidence_type}: unavailable`} · {e.state ?? 'commit / unknown'} {e.evidence_type === 'pull_request' && `· merged: ${e.merged === true ? 'Yes' : e.merged === false ? 'No' : 'Unknown'}`} {e.stale && '· stale observation'}</li>)}</ul>
      {canManage && row.status === 'planned' && !pending && <form onSubmit={e => { e.preventDefault(); const f = new FormData(e.currentTarget); propose({ milestoneId: row.id, start: String(f.get('start')), end: String(f.get('end')) }); }}><h5>Propose planned dates</h5><label>Start<input name="start" type="date" required defaultValue={row.planned_start_date} /></label><label>End (inclusive)<input name="end" type="date" required defaultValue={row.planned_end_date} /></label><button disabled={busy}>Review proposed dates</button></form>}
    </article>}
    {pending && <form onSubmit={e => void save(e)} aria-label="Confirm schedule change"><h4>Confirm commitment date change</h4><p>Proposed: {pending.start} → {pending.end}. Only these dates will change.</p><label>Public reason (required)<textarea name="reason" required minLength={10} maxLength={2000} /></label><p>This change is recorded in immutable milestone history. Status and other milestone dates remain unchanged.</p><button disabled={busy}>{busy ? 'Saving…' : 'Confirm and save dates'}</button><button type="button" disabled={busy} onClick={() => setPending(undefined)}>Cancel date change</button></form>}
  </section>;
}
