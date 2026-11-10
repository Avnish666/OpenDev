import { useEffect, useState } from 'react';
import { api } from '../api/client';

interface Run { status: string; error_code: string | null; started_at: string; retry_at: string | null }
interface Status { latest: Run | null; last_successful_sync_at: string | null; stale: boolean; notice: string }
interface Activity { sync: Status; repository: { full_name: string; default_branch: string } | null; counts: Record<string, number>; recent_commits: { sha: string; committed_at: string }[] }
interface Milestones { total: number; items: { github_id: number; number: number; title: string; description: string | null; state: string; due_date: string | null; open_issues: number; closed_issues: number; last_synced_at: string }[] }
const message = (error: unknown) => error instanceof Error ? error.message : 'GitHub synchronization failed';

export default function GitHubProgress({ projectId, canManage, active }: { projectId: number; canManage: boolean; active: boolean }) {
  const [status, setStatus] = useState<Status>(); const [activity, setActivity] = useState<Activity>();
  const [milestones, setMilestones] = useState<Milestones>(); const [page, setPage] = useState(0);
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [version, setVersion] = useState(0);
  useEffect(() => {
    let live = true; const root = `/api/projects/${projectId}/github`;
    Promise.all([api<Status>(`${root}/sync-status`), active ? api<Activity>(`${root}/activity`) : Promise.resolve(undefined), active ? api<Milestones>(`${root}/milestones?limit=20&offset=${page * 20}`) : Promise.resolve(undefined)])
      .then(([s, a, m]) => { if (live) { setStatus(s); setActivity(a); setMilestones(m); setError(''); } })
      .catch(e => { if (live) setError(message(e)); });
    return () => { live = false; };
  }, [projectId, active, page, version]);
  async function sync() {
    setBusy(true); setError('');
    try { await api<Run>(`/api/projects/${projectId}/github/sync`, 'POST'); setVersion(v => v + 1); }
    catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <section className="github-controls"><p className="eyebrow">CONNECTED TO THE CODE</p><h3>GitHub development signals</h3><p>Observed repository activity does not prove funded deliverables are complete. Counts include retained observations; deleted GitHub records may remain.</p>
    <div className="actions">{canManage && <button disabled={busy} onClick={() => void sync()}>{busy ? 'Synchronizing GitHub…' : 'Sync GitHub'}</button>}
    <button disabled={busy} onClick={() => { setStatus(undefined); setVersion(v => v + 1); }}>Refresh sync status</button></div>
    {error && <p role="alert">{error}</p>}{!status && !error && <p role="status">Loading repository progress…</p>}
    {status && <><p>Latest attempt: {status.latest?.status ?? 'Not synchronized'}</p>
      <p>Last successful sync: {status.last_successful_sync_at ? new Date(status.last_successful_sync_at).toLocaleString() : 'Never'}</p>
      {status.stale && <p role="status">Stale or incomplete observations. Deleted records may remain in snapshot counts.</p>}
      {status.latest?.error_code && <p role="alert">Sync issue: {status.latest.error_code}. Previous observations are retained. {status.latest.retry_at && `Retry after ${new Date(status.latest.retry_at).toLocaleString()}.`}</p>}
      {status.latest?.status === 'running' && <p>A previous attempt is running or was interrupted. Refresh, or retry if it is no longer active.</p>}
    </>}
    {activity && <><h4>{activity.repository?.full_name ?? 'No repository snapshot yet'}</h4>
      <div className="grid"><article><h5>Observed issues (excluding PRs)</h5><p>{activity.counts.issues_open} open · {activity.counts.issues_closed} closed</p></article><article><h5>Observed pull requests</h5><p>{activity.counts.pull_requests_open} open · {activity.counts.pull_requests_closed} closed · {activity.counts.pull_requests_merged} merged</p></article><article><h5>Recent commit sample</h5><p>{activity.recent_commits.length} commits from the default branch, up to 30.</p></article></div>
    </>}
    {milestones && <><h4>GitHub milestones</h4>{!milestones.total && <p>No milestones observed yet.</p>}
      {milestones.items.map(item => <article key={item.github_id}><h5>{item.title} · {item.state}</h5><p className="description">{item.description}</p><p>{item.open_issues} open · {item.closed_issues} closed GitHub issue/PR associations</p><p>Due: {item.due_date ? new Date(item.due_date).toLocaleDateString() : 'Unscheduled'}</p><p>Last observed: {new Date(item.last_synced_at).toLocaleString()}</p></article>)}
      <div className="actions"><button disabled={!page} onClick={() => { setMilestones(undefined); setPage(p => p - 1); }}>Previous milestones</button><button disabled={(page + 1) * 20 >= milestones.total} onClick={() => { setMilestones(undefined); setPage(p => p + 1); }}>Next milestones</button></div>
    </>}
    {!active && <p>Activity lists become visible when the project is active.</p>}
  </section>;
}
