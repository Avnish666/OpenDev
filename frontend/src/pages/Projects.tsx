import Expenses from './Expenses';
import Roadmap from '../components/Roadmap';
import GitHubProgress from '../components/GitHubProgress';
import ProjectProgress from '../components/ProjectProgress';
import { CheckoutButton, FundingHistory } from './Funding';
import { lazy, Suspense, useEffect, useState, type FormEvent } from 'react';
import { api, type Project, type ProjectDetail, type Reward } from '../api/client';
import { useAuth } from '../context/AuthContext';
const ProjectAIChat = lazy(() => import('../components/ProjectAIChat'));

const money = (cents: number, currency = 'USD') => new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(cents / 100);
const errorMessage = (e: unknown) => e instanceof Error ? e.message : 'Request failed';

export function ProjectList({ mine = false }: { mine?: boolean }) {
  const [items, setItems] = useState<Project[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  useEffect(() => {
    let live = true;
    api<Project[]>(`${mine ? '/api/me/projects' : '/api/projects'}?limit=20&offset=${page * 20}`).then(data => { if (live) { setItems(data); setError(''); } }).catch(e => { if (live) setError(errorMessage(e)); }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [mine, page]);
  return <section><h2>{mine ? 'My Projects' : 'Explore Projects'}</h2>{loading ? <p role="status">Loading projects…</p> : error ? <p role="alert">{error}</p> : <><div className="grid">{items.map(p => <article key={p.id}><h3><a href={`#/projects/${p.id}`}>{p.title}</a></h3><p>{p.description}</p><p>{money(p.funding_goal_cents, p.currency)} goal · {p.status}</p></article>)}</div>{!items.length && <p>No projects here yet.</p>}<div className="actions"><button disabled={!page} onClick={() => { setLoading(true); setPage(page - 1); }}>Previous</button><button disabled={items.length < 20} onClick={() => { setLoading(true); setPage(page + 1); }}>Next</button></div></>}</section>;
}

export function ProjectForm({ project, done }: { project?: ProjectDetail; done: (id: number) => void }) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const goal = Number(form.get('goal'));
      const budget = String(form.get('budget')).split('\n').filter(v => v.trim()).map(line => {
        const split = line.lastIndexOf(':');
        return { category: line.slice(0, split).trim(), allocated_cents: Number(line.slice(split + 1)) };
      });
      if (!Number.isSafeInteger(goal) || goal <= 0 || budget.some(b => b.category.length < 2 || !Number.isSafeInteger(b.allocated_cents) || b.allocated_cents < 0) || budget.reduce((s, b) => s + b.allocated_cents, 0) !== goal || new Set(budget.map(b => b.category.toLowerCase())).size !== budget.length) throw new Error('Use unique budget categories and integer cents totaling the funding goal.');
      setBusy(true); setError('');
      const body = { title: form.get('title'), description: form.get('description'), funding_goal_cents: goal, budget, ...(!project && { github_repo: form.get('repo'), currency: 'USD' }) };
      const result = await api<Project>(project ? `/api/projects/${project.id}` : '/api/projects', project ? 'PATCH' : 'POST', body);
      done(result.id);
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  return <section><h2>{project ? 'Edit Draft' : 'Create Project'}</h2><form onSubmit={submit}>
    {!project && <label>Public GitHub repository (owner/name)<input name="repo" required pattern="[A-Za-z0-9-]+/[A-Za-z0-9_.-]+" /></label>}
    <label>Title<input name="title" required minLength={3} maxLength={150} defaultValue={project?.title} /></label>
    <label>Description<textarea name="description" required minLength={20} maxLength={20000} defaultValue={project?.description} /></label>
    <label>Funding goal (USD cents)<input name="goal" type="number" min="1" step="1" required defaultValue={project?.funding_goal_cents} /></label>
    <label>Planned budget (one category:integer cents per line)<textarea name="budget" required placeholder={'Development:8000\nHosting:2000'} defaultValue={project?.budget.map(b => `${b.category}:${b.allocated_cents}`).join('\n')} /></label>
    {error && <p role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Saving…' : 'Save Draft'}</button>
  </form></section>;
}

function RewardForm({ projectId, tier, done }: { projectId: number; tier?: Reward; done: () => void }) {
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    try {
      const price = Number(form.get('price')); const quantity = form.get('quantity') ? Number(form.get('quantity')) : null;
      const benefits = String(form.get('benefits')).split('\n').filter(b => b.trim()).map(line => { const [title, ...rest] = line.split('|'); return { title: title.trim(), description: rest.join('|').trim() }; });
      if (!Number.isSafeInteger(price) || price <= 0 || (quantity !== null && (!Number.isSafeInteger(quantity) || quantity <= 0)) || !benefits.length) throw new Error('Enter positive integer cents, a valid quantity, and at least one benefit.');
      setBusy(true); setError('');
      await api(`/api/projects/${projectId}/rewards${tier ? `/${tier.id}` : ''}`, tier ? 'PATCH' : 'POST', { name: form.get('name'), description: form.get('description'), price_cents: price, currency: 'USD', benefits, quantity_limit: quantity, active: form.get('active') === 'on' }); done();
    } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  return <form onSubmit={submit}><h3>{tier ? 'Edit Reward Tier' : 'Create Reward Tier'}</h3>
    <label>Name<input name="name" required maxLength={100} defaultValue={tier?.name} /></label>
    <label>Description<textarea name="description" required maxLength={5000} defaultValue={tier?.description} /></label>
    <label>Price (USD cents)<input name="price" type="number" required min="1" step="1" defaultValue={tier?.price_cents} /></label>
    <label>Benefits (one title | description per line)<textarea name="benefits" required defaultValue={tier?.benefits.map(b => `${b.title} | ${b.description}`).join('\n')} /></label>
    <label>Quantity limit (blank means unlimited)<input name="quantity" type="number" min="1" step="1" defaultValue={tier?.quantity_limit ?? ''} /></label>
    <label className="checkbox"><input name="active" type="checkbox" defaultChecked={tier?.active ?? true} />Active</label>
    {error && <p role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Saving…' : 'Save Reward'}</button>
  </form>;
}

export function ProjectPage({ id }: { id: number }) {
  const [chatOpen, setChatOpen] = useState(false);
  const { user } = useAuth();
  const [project, setProject] = useState<ProjectDetail>(); const [rewards, setRewards] = useState<Reward[]>([]);
  const [error, setError] = useState(''); const [version, setVersion] = useState(0); const [busy, setBusy] = useState(false);
  const [editor, setEditor] = useState<Reward | 'new' | null>(null); const [editing, setEditing] = useState(false);
  useEffect(() => {
    let live = true;
    Promise.all([api<ProjectDetail>(`/api/projects/${id}`), api<Reward[]>(`/api/projects/${id}/rewards`)]).then(([p, r]) => { if (live) { setProject(p); setRewards(r); setError(''); } }).catch(e => { if (live) setError(errorMessage(e)); });
    return () => { live = false; };
  }, [id, version, user]);
  const refresh = () => { setEditor(null); setEditing(false); setVersion(v => v + 1); };
  async function publish() { setBusy(true); try { await api(`/api/projects/${id}/publish`, 'POST'); refresh(); } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); } }
  if (!project) return error ? <p role="alert">{error}</p> : <p role="status">Loading project…</p>;
  return <section><h2>{project.title}</h2>{error && <p role="alert">{error}</p>}<p className="badge">{project.status}</p><p className="description">{project.description}</p><a href={project.github_repo_url} target="_blank" rel="noreferrer">GitHub Repository</a><h3>Funding Goal</h3><p>{money(project.funding_goal_cents, project.currency)}</p><h3>Maintainers</h3><ul>{project.maintainers.map(m => <li key={m.id}><a href={`#/maintainers/${m.id}`}>{m.username}</a></li>)}</ul><h3>Planned Budget</h3><ul>{project.budget.map(b => <li key={b.category}>{b.category}: {money(b.allocated_cents, project.currency)}</li>)}</ul>
    {project.can_manage && project.status === 'draft' && <div className="actions"><button onClick={() => setEditing(!editing)}>Edit Draft</button><button disabled={busy} onClick={() => void publish()}>{busy ? 'Publishing…' : 'Publish Project'}</button></div>}
    {editing && <ProjectForm project={project} done={refresh} />}
    <h3>Backer Rewards</h3><p>Sandbox demo only. No real funds are collected.</p><div className="grid">{rewards.map(r => <article key={r.id}><h4>{r.name} · {money(r.price_cents, r.currency)}</h4><p>{r.description}</p><ul>{r.benefits.map((b, i) => <li key={i}>{b.title}{b.description && ` — ${b.description}`}</li>)}</ul><p>{r.quantity_limit === null ? 'Unlimited quantity' : `Quantity limit: ${r.quantity_limit}`} · {r.active ? 'Active' : 'Inactive'}</p>{r.active && <CheckoutButton tierId={r.id} />}{project.can_manage && <button onClick={() => setEditor(r)}>Edit Tier</button>}</article>)}</div>{!rewards.length && <p>No reward tiers yet.</p>}
    {project.can_manage && project.status !== 'active' && <GitHubProgress key={`github-${id}-${project.status}`} projectId={id} canManage={project.can_manage} active={project.status === 'active'} />}
    {project.can_manage && project.status !== 'active' && <Roadmap key={`roadmap-${id}`} projectId={id} canManage={project.can_manage} />}
    {project.status === 'active' && <ProjectProgress key={id} projectId={id} canManage={project.can_manage} />}
    {project.status === 'active' && (chatOpen ? <Suspense fallback={<p role="status">Loading accountability chat…</p>}><ProjectAIChat key={id} projectId={id} ownerId={project.owner_id} /></Suspense> : <section><h3>Ask about public evidence</h3><p>Explore recorded funding, delivery assertions and their limitations.</p><button type="button" onClick={() => setChatOpen(true)}>Open accountability chat</button></section>)}
    {project.can_manage && project.status !== 'draft' && <Expenses projectId={id} canManage={project.can_manage} />}
    {project.can_manage && <FundingHistory projectId={id} />}
    {project.can_manage && <><button onClick={() => setEditor('new')}>Create Reward Tier</button>{editor && <><RewardForm key={editor === 'new' ? 'new' : editor.id} projectId={id} tier={editor === 'new' ? undefined : editor} done={refresh} /><button onClick={() => setEditor(null)}>Cancel</button></>}</>}
  </section>;
}
