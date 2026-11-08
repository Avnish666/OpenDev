import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { githubSource, onTimeLabel, type ProgressSummary } from '../api/progress';
import { displayMoney } from '../api/transparency';
import Roadmap from './Roadmap';
import GitHubProgress from './GitHubProgress';
import Transparency from './Transparency';

const timestamp = (value: string | null) => value ? new Date(value).toLocaleString() : 'Not recorded';
const message = (e: unknown) => e instanceof Error ? e.message : 'Unable to load project progress';

export function ProgressOverview({ data }: { data: ProgressSummary }) {
  const c = data.counts; const f = data.financial;
  return <><div className="grid progress-cards"><article><h4>Maintainer-reported delivery</h4><p>{c.delivered} asserted delivered / {c.total} roadmap commitments</p><p>{c.in_progress} in progress · {c.submitted_for_review} submitted for review · {c.planned} planned</p><p>{onTimeLabel(c)}</p><p>{c.late} late · {c.unknown_delivery_timing} delivered with unknown timing</p></article>
    <article><h4>Commitments needing context</h4><p>{c.overdue_unfinished} overdue unfinished commitments</p><p>{c.cancelled} cancelled · {c.reopened} distinct milestones reopened after delivery</p><p>Overdue means unfinished and past the current deadline (UTC). It is separate from original-deadline delivery timing.</p></article>
    <article><h4>Linked development signals</h4><p>{data.linked_issues ?? 'Unavailable'} unique linked issues · {data.linked_merged_pull_requests ?? 'Unavailable'} unique linked merged PRs</p><p>Activity is not independent proof of deliverable fulfillment.</p></article>
    <article><h4>Recorded financial accountability</h4><p>Net Sandbox funding: {displayMoney(f.net_recorded_funding_cents, f.currency)}</p><p>Published reported spending: {displayMoney(f.published_reported_spending_cents, f.currency)}</p><p>Calculated difference: {displayMoney(f.funding_minus_reported_expenditure_cents, f.currency)} (not available cash or a verified balance)</p><p>{f.expenses_with_documents_count} / {f.published_expense_count} expenses with approved public document support; {displayMoney(f.expenses_with_documents_cents, f.currency)}</p><p>{f.public_unresolved_discrepancy_count} public budget findings; private receipt findings are withheld.</p><ul>{f.notes.map(note => <li key={note}>{note}</li>)}</ul></article></div>
    <h4>Freshness of observations</h4><p>Last successful GitHub sync: {timestamp(data.sync.last_successful_sync_at)}</p><p>Last attempted GitHub sync: {timestamp(data.sync.latest?.started_at ?? null)} · {data.sync.latest?.status ?? 'No attempt recorded'}</p><p>Attempt finished: {timestamp(data.sync.latest?.completed_at ?? null)}{data.sync.latest?.error_code && ` · ${data.sync.latest.error_code}`}</p><p>Internal roadmap update: {timestamp(data.roadmap_updated_at)}</p><p>Snapshot age at calculation: {data.snapshot_age_seconds === null ? 'Unknown' : `${data.snapshot_age_seconds} seconds`} · calculated {timestamp(data.calculated_at)}</p>
    <p>Linked source freshness: {data.linked_evidence_stale === null ? 'No available linked observations to assess' : data.linked_evidence_stale ? 'Stale linked observations exist; inspect the roadmap evidence' : 'No stale linked observations detected at calculation; retained/deleted-item limits still apply'}</p>
    {data.sync.stale && <p role="status">Stale or missing GitHub data. A failed synchronization preserves previous observations; these are not live updates.</p>}
    <h4>Owner history</h4><p><a href={`#/maintainers/${data.owner.identity.user_id}`}>{data.owner.identity.username}: public maintainer profile</a></p><p>{data.owner.public_projects} owned public projects · {data.owner.delivery.delivered} / {data.owner.delivery.total} commitments currently asserted delivered</p><p>{onTimeLabel(data.owner.delivery)}</p><p>{data.owner.scope}</p>
  </>;
}

export function GitHubActivity({ data }: { data: ProgressSummary }) {
  const a = data.activity;
  if (!a || !data.github_available) return <p>Public GitHub activity is missing or unavailable. No conclusion about abandonment is implied.</p>;
  const name = a.repository.full_name;
  return <><p>{name} · retained synchronized observations, not a complete live activity feed.</p>
    <div className="grid"><article><h4>Recent observed issues</h4>{!a.issues.length && <p>No issue observations yet.</p>}<ul>{a.issues.map(item => <li key={item.github_id}><a href={githubSource(name, 'issues', item.number)} target="_blank" rel="noreferrer">#{item.number} {item.title}</a> · {item.state}<p>Updated on GitHub: {timestamp(item.updated_at)}</p></li>)}</ul></article>
      <article><h4>Pull requests and merge status</h4>{!a.pull_requests.length && <p>No pull request observations yet.</p>}<ul>{a.pull_requests.map(item => <li key={item.github_id}><a href={githubSource(name, 'pull', item.number)} target="_blank" rel="noreferrer">#{item.number} {item.title}</a> · {item.state} · {item.merged_at ? 'Merged' : 'No merge recorded'}<p>Updated on GitHub: {timestamp(item.updated_at)}</p></li>)}</ul></article>
      <article><h4>GitHub milestones</h4>{!data.github_milestones.length && <p>No milestone observations yet.</p>}<ul>{data.github_milestones.map(item => <li key={item.github_id}><a href={githubSource(name, 'milestone', item.number)} target="_blank" rel="noreferrer">{item.title}</a> · {item.state}<p>{item.open_issues} open / {item.closed_issues} closed issue/PR associations</p><p>Last observed: {timestamp(item.last_synced_at)}</p></li>)}</ul></article>
    </div><h4>Recent default-branch commit sample</h4>{!a.recent_commits.length && <p>No commits in the current sample.</p>}<ul>{a.recent_commits.map(item => <li key={item.sha}><a href={githubSource(name, 'commit', item.sha)} target="_blank" rel="noreferrer">{item.sha.slice(0, 12)}</a> · {timestamp(item.committed_at)}</li>)}</ul><p>Preview: up to 10 issues, PRs and milestones, plus the existing recent commit sample. These are team/repository signals, not personal productivity scores.</p>
  </>;
}

export default function ProjectProgress({ projectId, canManage }: { projectId: number; canManage: boolean }) {
  const [data, setData] = useState<ProgressSummary>(); const [error, setError] = useState(''); const [version, setVersion] = useState(0);
  const [ledger, setLedger] = useState(false); const [controls, setControls] = useState(false);
  useEffect(() => { let live = true; api<ProgressSummary>(`/api/projects/${projectId}/progress-summary`).then(v => { if (live) { setData(v); setError(''); } }).catch(e => { if (live) setError(message(e)); }); return () => { live = false; }; }, [projectId, version]);
  useEffect(() => {
    const navigateToRoadmap = () => {if(window.location.hash===`#/projects/${projectId}/roadmap`){const target=document.getElementById(`progress-${projectId}-roadmap`);target?.scrollIntoView();target?.focus();}};
    navigateToRoadmap();window.addEventListener('hashchange',navigateToRoadmap);
    return()=>window.removeEventListener('hashchange',navigateToRoadmap);
  },[projectId]);
  const section = (name: string) => `progress-${projectId}-${name}`;
  function navigate(name: string) { const element = document.getElementById(section(name)); element?.scrollIntoView(); element?.focus(); }
  return <section aria-label="Public project progress"><h3>Project Progress</h3><p><a href={`#/projects/${projectId}/analytics`}>Open project analytics</a></p><p>Public evidence and maintainer assertions, with separate financial and development records. No inferred completion percentage or independent delivery certification.</p>
    <nav aria-label="Project progress sections"><button onClick={() => navigate('overview')}>Overview</button><button onClick={() => navigate('roadmap')}>Roadmap / timeline</button><button onClick={() => navigate('github')}>GitHub activity</button><button onClick={() => navigate('history')}>Delivery history</button><button onClick={() => { setLedger(true); requestAnimationFrame(() => navigate('financial')); }}>Open financial transparency ledger</button></nav>
    <button onClick={() => { setData(undefined); setVersion(v => v + 1); }}>Refresh progress summary</button>
    {error && <p role="alert">{error}</p>}{!data && !error && <p role="status">Loading public progress summary…</p>}
    <section id={section('overview')} tabIndex={-1} aria-label="Progress overview">{data && <ProgressOverview data={data} />}</section>
    <section id={section('roadmap')} tabIndex={-1} aria-label="Roadmap and timeline"><Roadmap projectId={projectId} canManage={canManage} /></section>
    <section id={section('github')} tabIndex={-1} aria-label="GitHub development activity"><h3>GitHub development activity</h3>{data && <GitHubActivity data={data} />}
      {canManage && <><button onClick={() => setControls(!controls)}>Maintainer GitHub sync controls</button>{controls && <GitHubProgress projectId={projectId} canManage active />}</>}
    </section>
    <section id={section('history')} tabIndex={-1} aria-label="Public delivery and commitment history"><h3>Delivery and commitment history</h3>{data && <>{!data.delivery_history_preview.length && <p>No published roadmap commitments yet.</p>}{data.delivery_history_preview.map(row => <article key={row.milestone_id}><h4>{row.title} · {row.status}</h4><p>Original recorded deadline: {row.original_deadline ?? 'Unknown'} · current deadline: {row.current_deadline}</p><p>Maintainer-asserted delivery date: {row.actual_completion_date ?? 'Not currently established'}</p><p>{row.timing.replaceAll('_', ' ')} · reopened after delivery: {row.reopened_after_delivery ? 'Yes' : 'No'}</p></article>)}
      <h4>Recent public roadmap changes</h4>{!data.recent_changes.length && <p>No recorded changes yet.</p>}<ol>{data.recent_changes.map(change => <li key={change.id}><p>{change.title} · {change.action} · {timestamp(change.created_at)} · {change.previous_status ?? 'New'} → {change.new_status}</p><p>{change.reason}</p><details><summary>Recorded commitment change</summary><pre className="description">{JSON.stringify({ before: change.before, after: change.after }, null, 2)}</pre></details></li>)}</ol><p>Up to 10 recent commitments/changes. Full immutable history is available in each roadmap milestone.</p>
    </>}</section>
    {ledger && <section id={section('financial')} tabIndex={-1} aria-label="Detailed public financial ledger"><button onClick={() => setLedger(false)}>Close detailed ledger</button><Transparency projectId={projectId} /></section>}
    {data && <aside><h4>Interpretation limits</h4><ul>{data.limitations.map(note => <li key={note}>{note}</li>)}</ul></aside>}
  </section>;
}
