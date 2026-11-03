import { Component, lazy, Suspense, useEffect, useState, type ReactNode } from 'react';
import { loadAnalytics, rendererAllowed, defaultExpenseFilters, type AnalyticsView, type ExpenseFilters, type AnalyticsOverview } from '../api/analytics';
import { displayMoney } from '../api/transparency';
import './ProjectAnalytics.css';
const Community=lazy(()=>import('./ProjectAnalyticsCommunity'));
const Studio=lazy(()=>import('@opendev/studio-renderer'));
class RendererBoundary extends Component<{children:ReactNode;fallback:()=>void},{failed:boolean}>{
 state={failed:false};static getDerivedStateFromError(){return {failed:true};}
 render(){return this.state.failed?<div role="alert"><p>Analytics renderer could not initialize.</p><button onClick={this.props.fallback}>Return to Community view</button></div>:this.props.children;}
}
export default function ProjectAnalytics(props:{projectId:number}){return <AnalyticsSession key={props.projectId} {...props}/>;}
function AnalyticsSession({projectId}:{projectId:number}){
 const [data,setData]=useState<AnalyticsOverview>();const [error,setError]=useState('');const [offset,setOffset]=useState(0);const [version,setVersion]=useState(0);
 const [filters,setFilters]=useState<ExpenseFilters>(defaultExpenseFilters);const [draft,setDraft]=useState<ExpenseFilters>(defaultExpenseFilters);const [filterError,setFilterError]=useState('');
 const [view,setView]=useState<AnalyticsView>('financial');const [milestoneOffset,setMilestoneOffset]=useState(0);
 const [renderer,setRenderer]=useState(import.meta.env.VITE_ANALYTICS_RENDERER==='studio'?'studio':'community');
 useEffect(()=>{const abort=new AbortController();loadAnalytics(projectId,offset,abort.signal,filters,milestoneOffset).then(v=>{if(!abort.signal.aborted){setData(v);setError('');}}).catch(()=>{if(!abort.signal.aborted){setData(undefined);setError('Unable to load this public analytics dataset. Refresh or return to the project.');}});return()=>abort.abort();},[projectId,offset,version,filters,milestoneOffset]);
 const studio=rendererAllowed(renderer,__STUDIO_INSTALLED__,__STUDIO_LICENSED__,__STUDIO_EVALUATION__,typeof location==='undefined'?'':location.hostname);
 return <section className="project-analytics" aria-label="Public project analytics"><h3>Project analytics</h3><p>Financial and development analytics from current public records. Delivery is a maintainer assertion. Funding minus reported expenditure is a calculated difference, not a verified bank balance.</p>
 <div className="actions"><label>Renderer<select value={renderer} onChange={e=>setRenderer(e.target.value)}><option value="community">Community</option><option value="studio">AG Studio (requires authorization)</option></select></label><button onClick={()=>{setData(undefined);setError('');setVersion(v=>v+1);}}>Refresh analytics</button></div>
 <label>Analytics dashboard<select name="analytics_view" value={view} onChange={e=>setView(e.target.value as AnalyticsView)}><option value="financial">Financial analytics</option><option value="development">Development analytics</option></select></label>
 {view==='financial'&&<form className="analytics-filters" onSubmit={e=>{e.preventDefault();if(draft.date_from&&draft.date_to&&draft.date_from>draft.date_to){setFilterError('Start date must be on or before end date.');return;}setFilterError('');setError('');setData(undefined);setOffset(0);setFilters({...draft});}}>
 <p>Expense filters affect the grid and expense breakdowns. Funding, budget and coverage remain full-project totals.</p>
 <label>Expense category<input name="category" maxLength={100} list={`expense-categories-${projectId}`} value={draft.category} onChange={e=>setDraft({...draft,category:e.target.value})}/><datalist id={`expense-categories-${projectId}`}>{data?.budget.map(r=><option key={r.category} value={r.category}/>)}</datalist></label>
 <label>From expense date<input name="date_from" type="date" value={draft.date_from} onChange={e=>setDraft({...draft,date_from:e.target.value})}/></label>
 <label>Through expense date<input name="date_to" type="date" value={draft.date_to} onChange={e=>setDraft({...draft,date_to:e.target.value})}/></label>
 <label>Public evidence<select name="evidence" value={draft.evidence} onChange={e=>setDraft({...draft,evidence:e.target.value as ExpenseFilters['evidence']})}><option value="all">All expenses</option><option value="supported">With approved public documents</option><option value="unsupported">Without public documents</option></select></label>
 <label>Expense order<select name="sort" value={draft.sort} onChange={e=>setDraft({...draft,sort:e.target.value as ExpenseFilters['sort']})}><option value="date_desc">Newest expense first</option><option value="date_asc">Oldest expense first</option></select></label>
 <button>Apply expense filters</button><button type="button" onClick={()=>{setDraft(defaultExpenseFilters);setFilters({...defaultExpenseFilters});setOffset(0);setData(undefined);setError('');setFilterError('');}}>Reset expense filters</button>
 </form>}{filterError&&<p role="alert">{filterError}</p>}
 {error&&<p role="alert">{error}</p>}{!data&&!error&&<p role="status">Loading public analytics…</p>}
 {renderer==='studio'&&!studio?<div role="alert"><p>AG Studio is unavailable or not authorized in this build. Evaluation is local-only; public use requires appropriate licensing.</p><button onClick={()=>setRenderer('community')}>Return to Community view</button></div>:data&&<RendererBoundary key={`${renderer}-${data.as_of}`} fallback={()=>setRenderer('community')}><Suspense fallback={<p role="status">Loading analytics renderer…</p>}>{studio?<Studio data={data} view={view}/>:<Community data={data} view={view}/>}</Suspense></RendererBoundary>}
 {data&&<><p>Snapshot: {data.as_of} · {data.currency} · public scope only. GitHub last success: {data.development.last_successful_sync_at??'Unknown'} ({data.development.github_stale?'stale or missing':'retained observations'}).</p><p>Expense rows {data.expenses.length?data.expense_offset+1:0}–{data.expense_offset+data.expenses.length} of {data.expense_total} matching published expenses. Filtered reported spending: {displayMoney(data.expense_analysis.reported_spending_cents,data.currency)}.</p>
 {view==='development'?<><p>Milestones {data.development.milestones.length?data.development.offset+1:0}–{data.development.offset+data.development.milestones.length} of {data.development.total}.</p><div className="actions"><button disabled={!milestoneOffset} onClick={()=>{setData(undefined);setMilestoneOffset(Math.max(0,milestoneOffset-50));}}>Previous milestone page</button><button disabled={milestoneOffset+50>=data.development.total||milestoneOffset>=10000} onClick={()=>{setData(undefined);setMilestoneOffset(milestoneOffset+50);}}>Next milestone page</button></div></>:<div className="actions"><button disabled={!offset} onClick={()=>{setData(undefined);setOffset(Math.max(0,offset-50));}}>Previous expense page</button><button disabled={offset+50>=data.expense_total||offset>=10000} onClick={()=>{setData(undefined);setOffset(offset+50);}}>Next expense page</button></div>}
 <details><summary>Dataset scope and limitations</summary><ul>{data.limitations.map((s,i)=><li key={i}>{s}</li>)}</ul><p>{data.maintainer.scope} {data.maintainer.attribution}</p><p>AG Studio AI, report persistence and private datasets are not configured.</p></details></>}
 </section>;
}
