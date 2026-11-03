import { Component, lazy, Suspense, useEffect, useState, type ReactNode } from 'react';
import { loadAnalytics, rendererAllowed, type AnalyticsOverview } from '../api/analytics';
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
 const [renderer,setRenderer]=useState(import.meta.env.VITE_ANALYTICS_RENDERER==='studio'?'studio':'community');
 useEffect(()=>{const abort=new AbortController();loadAnalytics(projectId,offset,abort.signal).then(v=>{if(!abort.signal.aborted){setData(v);setError('');}}).catch(()=>{if(!abort.signal.aborted){setData(undefined);setError('Unable to load this public analytics dataset. Refresh or return to the project.');}});return()=>abort.abort();},[projectId,offset,version]);
 const studio=rendererAllowed(renderer,__STUDIO_INSTALLED__,__STUDIO_LICENSED__,__STUDIO_EVALUATION__,typeof location==='undefined'?'':location.hostname);
 return <section className="project-analytics" aria-label="Public project analytics"><h3>Project analytics</h3><p>Current public records and maintainer assertions. No inferred funding trends, cash balance, completion percentage or trust score.</p>
 <div className="actions"><label>Renderer<select value={renderer} onChange={e=>setRenderer(e.target.value)}><option value="community">Community</option><option value="studio">AG Studio (requires authorization)</option></select></label><button onClick={()=>{setData(undefined);setVersion(v=>v+1);}}>Refresh analytics</button></div>
 {error&&<p role="alert">{error}</p>}{!data&&!error&&<p role="status">Loading public analytics…</p>}
 {renderer==='studio'&&!studio?<div role="alert"><p>AG Studio is unavailable or not authorized in this build. Evaluation is local-only; public use requires appropriate licensing.</p><button onClick={()=>setRenderer('community')}>Return to Community view</button></div>:data&&<RendererBoundary key={renderer} fallback={()=>setRenderer('community')}><Suspense fallback={<p role="status">Loading analytics renderer…</p>}>{studio?<Studio data={data}/>:<Community data={data}/>}</Suspense></RendererBoundary>}
 {data&&<><p>Snapshot: {data.as_of} · {data.currency} · public scope only. GitHub last success: {data.development.last_successful_sync_at??'Unknown'} ({data.development.github_stale?'stale or missing':'retained observations'}).</p><p>Expense rows {data.expenses.length?data.expense_offset+1:0}–{data.expense_offset+data.expenses.length} of {data.expense_total}. Milestone page: {data.development.milestones.length} of {data.development.total}.</p>
 <div className="actions"><button disabled={!offset} onClick={()=>{setData(undefined);setOffset(Math.max(0,offset-50));}}>Previous analytics page</button><button disabled={offset+50>=Math.max(data.expense_total,data.development.total)||offset>=10000} onClick={()=>{setData(undefined);setOffset(offset+50);}}>Next analytics page</button></div>
 <details><summary>Dataset scope and limitations</summary><ul>{data.limitations.map((s,i)=><li key={i}>{s}</li>)}</ul><p>{data.maintainer.scope} {data.maintainer.attribution}</p><p>AG Studio AI, report persistence and private datasets are not configured.</p></details></>}
 </section>;
}
