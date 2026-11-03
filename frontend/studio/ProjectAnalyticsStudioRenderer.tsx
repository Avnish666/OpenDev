// Resolved only by an explicitly authorized optional Studio build.
import { useEffect, useMemo, useState } from 'react';
import { AgStudio } from 'ag-studio-react';
import { AgStudioLicenseManager } from 'ag-studio';
import type { AnalyticsOverview } from '../src/api/analytics';
import { MaintainerFacts, DevelopmentOverview, DevelopmentTables } from '../src/components/DevelopmentFacts';
import { developmentDashboard } from './developmentDashboard';
import { FinancialOverview, FinancialTables } from '../src/components/FinancialFacts';
import { financialDashboard } from './financialDashboard';
const key=import.meta.env.VITE_AG_STUDIO_LICENSE_KEY;
if(key)AgStudioLicenseManager.setLicenseKey(key);
export default function ProjectAnalyticsStudioRenderer({data,view='financial'}:{data:AnalyticsOverview;view?:'financial'|'development'|'spending'|'maintainer'}){
 const [mobile,setMobile]=useState(()=>window.matchMedia('(max-width:600px)').matches);
 useEffect(()=>{const media=window.matchMedia('(max-width:600px)');const update=()=>setMobile(media.matches);media.addEventListener('change',update);return()=>media.removeEventListener('change',update);},[]);
 const {sources,state}=useMemo(()=>{const result=['development','maintainer'].includes(view)?developmentDashboard(data,mobile):financialDashboard(data,mobile);const keep=view==='maintainer'?['maintainer','roles','reward_metrics']:view==='spending'?['categories','months','coverage','expenses']:null;if(keep)for(const page of result.state.pages){for(const key of Object.keys(page.widgets??{}))if(!keep.includes(key)){delete page.widgets?.[key];delete page.widgetLayout?.[key];}let y=0;for(const layout of Object.values(page.widgetLayout??{})){if(layout){layout.yTrack=y;y+=layout.ySpan;}}}return result;},[data,mobile,view]);
 return <div><p className="badge">AG Studio {view} dashboard · view mode</p>{view==='maintainer'?<MaintainerFacts data={data}/>:['development','maintainer'].includes(view)?<DevelopmentOverview data={data}/>:<FinancialOverview data={data}/>}
 {['financial','spending'].includes(view)?<p>Use the expense filters above for server-side filtering across all pages. KPI, budget and coverage widgets show full-project totals. Expense widgets show the matching dataset; the table is one bounded page.</p>:<p>Development KPI and snapshot counts use their full current public scope. Milestone widgets use the bounded history page; owner outcomes and project reward obligations are shown separately.</p>}
 <div className="analytics-studio" aria-label={`AG Studio ${view} dashboard`}><AgStudio key={`${view}-${data.as_of}-${data.development.offset}-${data.expense_offset}-${JSON.stringify(data.expense_filters)}-${mobile}`} studioId="opendev-analytics" data={sources} initialState={state} mode="view" panels={{view:{left:[],right:[]},edit:{left:[],right:[]}}} /></div>
 {view==='maintainer'?null:['development','maintainer'].includes(view)?<DevelopmentTables data={data}/>:<FinancialTables data={data}/>} {['financial','spending'].includes(view)&&!data.expenses.length&&<p>No published expense rows match these filters.</p>}</div>;
}
