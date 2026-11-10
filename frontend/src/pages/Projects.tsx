import Icon from '../components/Icon';
import HeroVisual from '../components/HeroVisual';
import { PageHeading, StatusBadge, FormSection } from '../components/UI';
import Roadmap from '../components/Roadmap';
import GitHubProgress from '../components/GitHubProgress';
import ProjectProgress from '../components/ProjectProgress';
import { CheckoutButton, FundingHistory } from './Funding';
import { lazy, Suspense, useEffect, useState, type FormEvent } from 'react';
import { api, type Project, type ProjectDetail, type Reward } from '../api/client';
import { useAuth } from '../context/AuthContext';
const ProjectAnalytics = lazy(() => import('../components/ProjectAnalytics'));
const ProjectAIChat = lazy(() => import('../components/ProjectAIChat'));
const Expenses = lazy(() => import('./Expenses'));

const money = (cents: number, currency = 'USD') => new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(cents / 100);
const errorMessage = (e: unknown) => e instanceof Error ? e.message : 'Request failed';

function ExploreHero() {
  return <><section className="hero"><div className="hero-copy"><p className="eyebrow hero-eyebrow"><span />OPEN SOURCE. A SHARED WAY FORWARD.</p><h1>Fund open source.<br /><span>Track every<br className="hero-line-break" /> milestone.</span></h1><p>Back the ideas you believe in. Give maintainers the support to build, with a clear view of the funding, spending, and progress behind every project.</p><div className="actions"><a className="button" href="#/explore" onClick={event => { event.preventDefault(); document.getElementById('discover-projects')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); }}>Explore Projects <Icon name="arrow" size={18} /></a><a className="button button-secondary" href="#/create">Create a project <span aria-hidden="true">+</span></a></div><p className="hero-note"><Icon name="shield" size={16} />Built for maintainers. Made clear for backers.</p></div><HeroVisual /></section><section className="value-strip" aria-label="Why OpenDev">{([{ icon: 'code', title: 'Code you can follow', text: 'Projects connected to the repositories behind the work.' }, { icon: 'shield', title: 'Funding with visibility', text: 'Reported spending and public evidence, in one place.' }, { icon: 'spark', title: 'Answers with a source', text: 'Accountability questions grounded in project records.' }] as const).map((item, index) => <div className="value-item" key={item.title}><span className="value-icon"><Icon name={item.icon} size={21} /></span><div><small className="value-index">0{index + 1}</small><strong>{item.title}</strong><p>{item.text}</p></div></div>)}</section></>;
}

export function ProjectList({ mine = false, analytics = false }: { mine?: boolean; analytics?: boolean }) {
  const [items, setItems] = useState<Project[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [query, setQuery] = useState('');
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let live = true;
    api<Project[]>(`${mine ? '/api/me/projects' : '/api/projects'}?limit=20&offset=${page * 20}`).then(data => { if (live) { setItems(data); setError(''); } }).catch(e => { if (live) setError(errorMessage(e)); }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [mine, page, version]);
  const filtered = items.filter(p => `${p.title} ${p.description} ${p.github_repo_url}`.toLowerCase().includes(query.toLowerCase()));
  return <>{!mine && !analytics && <ExploreHero />}<section id="discover-projects"><div className="section-heading"><div><p className="eyebrow">{mine ? 'YOUR WORK, MOVING FORWARD' : analytics ? 'PUBLIC PROJECT RECORDS' : 'DISCOVER WHAT COMES NEXT'}</p><h2>{mine ? 'My Projects' : 'Explore Projects'}</h2><p>{mine ? 'Manage your campaigns, milestones, and backer rewards.' : 'Small contributions. Meaningful possibilities.'}</p></div><div className="discovery-search"><span className="field-caption">Search this page</span><div className="search-input"><Icon name="search" size={18} /><label htmlFor="project-search">Search this page of projects</label><input id="project-search" type="search" placeholder="Search projects on this page…" value={query} onChange={e => setQuery(e.target.value)} /></div></div></div>
    {loading ? <div className="grid" role="status" aria-label="Loading projects"><div className="skeleton" /><div className="skeleton" /><div className="skeleton" /><span className="muted">Loading projects…</span></div> : error ? <div className="empty-state"><Icon name="code" size={32} /><h3>Projects couldn't be loaded.</h3><p role="alert">{error}</p><button onClick={() => { setLoading(true); setVersion(v => v + 1); }}>Try again</button></div> : <><div className="grid project-grid">{filtered.map(p => <article className="project-card" key={p.id}><div className="project-card-top"><span className="project-monogram" aria-hidden="true">{p.title.slice(0,1).toUpperCase()}</span><StatusBadge status={p.status} /></div><h3><a href={`#/projects/${p.id}${analytics ? '/analytics' : ''}`}>{p.title}</a></h3><p className="card-description">{p.description}</p>{p.github_repo_url ? <a className="repo-link" href={p.github_repo_url} target="_blank" rel="noreferrer"><Icon name="github" size={15} />{p.github_repo_url.replace('https://github.com/', '')}</a> : <span className="muted">Repository unavailable</span>}<div className="project-card-bottom"><div className="goal-line"><span>Funding goal</span><strong>{money(p.funding_goal_cents, p.currency)}</strong></div><a className="card-action" href={`#/projects/${p.id}${analytics ? '/analytics' : ''}`}>{analytics ? 'View analytics' : 'Explore project'}<Icon name="arrow" size={17} /></a></div></article>)}</div>{!filtered.length && <div className="empty-state"><Icon name={query ? 'search' : 'code'} size={32} /><h3>{query ? 'No matches on this page.' : mine ? 'Your next idea starts here.' : 'The next great idea could be yours.'}</h3><p>{query ? 'Try another search, or browse another page.' : mine ? 'Create a project to start building in the open.' : 'No projects here yet. Start a campaign and give your work a way forward.'}</p>{!query && <a className="button" href="#/create">Create a project <Icon name="arrow" size={17} /></a>}</div>}<div className="actions pagination"><button className="secondary" disabled={!page} onClick={() => { setLoading(true); setQuery(''); setPage(page - 1); }}>Previous</button><span>Page {page + 1} · Search applies to this page</span><button className="secondary" disabled={items.length < 20} onClick={() => { setLoading(true); setQuery(''); setPage(page + 1); }}>Next</button></div></>}
  </section></>;
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
  return <section className="project-form-page"><PageHeading eyebrow="THE NEXT THING STARTS WITH YOU" title={project ? 'Edit Draft' : 'Create Project'} description="Connect your repository. Set a clear goal. Build with your backers in the picture." /><div className="form-layout"><form className="project-editor" onSubmit={submit}>
    <FormSection number="01" title="The project" description="Tell backers what you’re building and why it matters.">
      {!project && <label>Public GitHub repository (owner/name)<input name="repo" required pattern="[A-Za-z0-9-]+/[A-Za-z0-9_.-]+" placeholder="your-username/your-project" /><span className="field-hint">Use a public repository you own on GitHub.</span></label>}
      <label>Title<input name="title" required minLength={3} maxLength={150} defaultValue={project?.title} placeholder="A clear, memorable project name" /></label>
      <label>Description<textarea name="description" required minLength={20} maxLength={20000} defaultValue={project?.description} placeholder="What are you building, who is it for, and what will this funding help deliver?" /></label>
    </FormSection>
    <FormSection number="02" title="Funding & budget" description="Enter integer cents: 10,000 cents = $100. Your budget categories must total your funding goal.">
      <label>Funding goal (USD cents)<input name="goal" type="number" min="1" step="1" required defaultValue={project?.funding_goal_cents} /></label>
      <label>Planned budget (one category:integer cents per line)<textarea name="budget" required placeholder={'Development:8000\nHosting:2000'} defaultValue={project?.budget.map(b => `${b.category}:${b.allocated_cents}`).join('\n')} /><span className="field-hint">Use unique category names and allocate the full goal.</span></label>
    </FormSection>
    {error && <p role="alert">{error}</p>}<div className="form-footer"><span>Your project is saved as a draft.</span><button disabled={busy}>{busy ? 'Saving…' : 'Save Draft'}</button></div>
  </form><aside className="form-guide"><span className="feature-icon"><Icon name="code" size={27} /></span><p className="eyebrow">START WITH A CLEAR PLAN</p><h3>Good projects make the next step clear.</h3><ol className="guide-checklist"><li><strong>Connect the code</strong><p>Give backers a public repository they can follow.</p></li><li><strong>Make the goal tangible</strong><p>Explain what the work is and how the budget supports it.</p></li><li><strong>Publish when you’re ready</strong><p>Review your draft before making your campaign active.</p></li></ol><div className="disclosure"><Icon name="shield" size={17} /><span>PayPal Sandbox only. No real funds are collected.</span></div></aside></div></section>;

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
  return <form className="reward-editor" onSubmit={submit}><h3>{tier ? 'Edit Reward Tier' : 'Create Reward Tier'}</h3>
    <p className="muted">Define a clear benefit for the people supporting your work.</p><FormSection number="01" title="The reward"><label>Name<input name="name" required maxLength={100} defaultValue={tier?.name} /></label>
    <label>Description<textarea name="description" required maxLength={5000} defaultValue={tier?.description} /></label>
    </FormSection><FormSection number="02" title="Price & availability" description="Amounts are entered in integer USD cents. Checkout remains Sandbox-only."><label>Price (USD cents)<input name="price" type="number" required min="1" step="1" defaultValue={tier?.price_cents} /></label>
    <label>Benefits (one title | description per line)<textarea name="benefits" required defaultValue={tier?.benefits.map(b => `${b.title} | ${b.description}`).join('\n')} /></label>
    <label>Quantity limit (blank means unlimited)<input name="quantity" type="number" min="1" step="1" defaultValue={tier?.quantity_limit ?? ''} /></label>
    <label className="checkbox"><input name="active" type="checkbox" defaultChecked={tier?.active ?? true} />Active</label></FormSection>
    {error && <p role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Saving…' : 'Save Reward'}</button>
  </form>;
}

export function ProjectPage({ id }: { id: number }) {
  const [chatOpen, setChatOpen] = useState(false);
  const [analyticsOpen,setAnalyticsOpen]=useState(()=>window.location.hash.split('?')[0].endsWith('/analytics'));
  useEffect(()=>{const open=()=>{if(window.location.hash.split('?')[0]===`#/projects/${id}/analytics`)setAnalyticsOpen(true);};window.addEventListener('hashchange',open);return()=>window.removeEventListener('hashchange',open);},[id]);
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
  function jumpTo(section: string) { document.getElementById(`project-${id}-${section}`)?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }); }
  return <section className="project-page"><div className="breadcrumb"><a href="#/explore">Explore projects</a><span>/</span><span>{project.title}</span></div><div className="project-hero"><StatusBadge status={project.status} /><h1>{project.title}</h1>{error && <p role="alert">{error}</p>}<p className="description">{project.description}</p><div className="project-meta"><a className="repo-link" href={project.github_repo_url} target="_blank" rel="noreferrer"><Icon name="github" size={17} />{project.github_repo_url.replace('https://github.com/', '')} ↗</a><span className="muted">Maintained by {project.maintainers.map((m, i) => <span key={m.id}>{i > 0 && ', '}<a href={`#/maintainers/${m.id}`}>{m.username}</a></span>)}</span></div></div>
    <nav className="project-subnav" aria-label="Project sections"><a href={`#/projects/${id}`} onClick={e => { e.preventDefault(); jumpTo('funding'); }}>Funding &amp; rewards</a><a href={`#/projects/${id}/roadmap`}>Development progress</a><a href={`#/projects/${id}/analytics`}>Analytics</a>{project.status === 'active' && <a href={`#/projects/${id}`} onClick={e => { e.preventDefault(); jumpTo('assistant'); }}>AI accountability</a>}</nav>
    <div className="funding-layout" id={`project-${id}-funding`}><article><p className="eyebrow">GIVE THE BUILD A BOOST</p><h3>Funding Goal</h3><p className="funding-goal">{money(project.funding_goal_cents, project.currency)}</p><p className="funding-label">Campaign target · {project.currency}</p><p className="muted">Recorded funding and reported spending are available in the public progress and financial records below.</p><p className="disclosure">PayPal Sandbox only. No real funds are collected.</p></article><article><p className="eyebrow">A PLAN YOU CAN SEE</p><h3>Planned Budget</h3><ul className="budget-list">{project.budget.map(b => <li key={b.category}><span>{b.category}</span><strong>{money(b.allocated_cents, project.currency)}</strong></li>)}</ul></article></div>
    {project.can_manage && project.status === 'draft' && <div className="actions"><button onClick={() => setEditing(!editing)}>Edit Draft</button><button disabled={busy} onClick={() => void publish()}>{busy ? 'Publishing…' : 'Publish Project'}</button></div>}
    {editing && <ProjectForm project={project} done={refresh} />}
    <section className="reward-section"><div className="section-heading"><div><p className="eyebrow">SUPPORT THE PEOPLE BEHIND THE CODE</p><h3>Backer Rewards</h3><p>Sandbox demo only. No real funds are collected.</p></div></div><div className="grid reward-grid">{rewards.map(r => <article className="reward-card" key={r.id}><div className="reward-card-heading"><h4>{r.name}</h4><StatusBadge status={r.active ? 'active' : 'inactive'} /></div><span className="reward-price">{money(r.price_cents, r.currency)}</span><p>{r.description}</p><ul>{r.benefits.map((b, i) => <li key={i}>{b.title}{b.description && ` — ${b.description}`}</li>)}</ul><p>{r.quantity_limit === null ? 'Unlimited quantity' : `Quantity limit: ${r.quantity_limit}`} · {r.active ? 'Active' : 'Inactive'}</p>{r.active && <CheckoutButton tierId={r.id} />}{project.can_manage && <button onClick={() => setEditor(r)}>Edit Tier</button>}</article>)}</div>{!rewards.length && <div className="empty-state">No reward tiers yet.</div>}</section>
    {project.can_manage && project.status !== 'active' && <GitHubProgress key={`github-${id}-${project.status}`} projectId={id} canManage={project.can_manage} active={project.status === 'active'} />}
    {project.can_manage && project.status !== 'active' && <Roadmap key={`roadmap-${id}`} projectId={id} canManage={project.can_manage} />}
    {project.status === 'active' && <ProjectProgress key={id} projectId={id} canManage={project.can_manage} fundingGoalCents={project.funding_goal_cents} currency={project.currency} />}
    <div id={`project-${id}-assistant`}>{project.status === 'active' && (chatOpen ? <Suspense fallback={<p role="status">Loading accountability chat…</p>}><ProjectAIChat key={id} projectId={id} ownerId={project.owner_id} /></Suspense> : <section className="feature-panel"><Icon name="spark" size={38} /><div><p className="eyebrow">YOUR QUESTIONS. PUBLIC EVIDENCE.</p><h3>AI Accountability Assistant</h3><p>Explore recorded funding, delivery assertions and their limitations. Ask public questions without signing in.</p></div><button type="button" onClick={() => setChatOpen(true)}>Open accountability chat</button></section>)}</div>
    {project.status==='active'&&(analyticsOpen?<Suspense fallback={<p role="status">Loading project analytics…</p>}><ProjectAnalytics key={id} projectId={id}/></Suspense>:<section className="feature-panel analytics-entry"><Icon name="chart" size={34} /><div><p className="eyebrow">FOLLOW THE NUMBERS</p><h3>Project analytics</h3><p>Inspect recorded funding, reported expenses, and development indicators in one dashboard.</p></div><button onClick={()=>setAnalyticsOpen(true)}>Open project analytics</button></section>)}
    {project.can_manage && project.status !== 'draft' && <Suspense fallback={<p role="status">Loading expense reporting…</p>}><Expenses projectId={id} canManage={project.can_manage} /></Suspense>}
    {project.can_manage && <FundingHistory projectId={id} />}
    {project.can_manage && <><button onClick={() => setEditor('new')}>Create Reward Tier</button>{editor && <><RewardForm key={editor === 'new' ? 'new' : editor.id} projectId={id} tier={editor === 'new' ? undefined : editor} done={refresh} /><button onClick={() => setEditor(null)}>Cancel</button></>}</>}
  </section>;
}
