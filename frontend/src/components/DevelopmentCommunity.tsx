import { useMemo } from 'react';
import { AgCharts } from 'ag-charts-react';
import type { AgChartOptions } from 'ag-charts-community';
import { AgGridReact } from 'ag-grid-react';
import type { ColDef } from 'ag-grid-community';
import { roadmapStates, rewardSlices, type AnalyticsOverview, type AnalyticsMilestone } from '../api/analytics';
import { DevelopmentOverview, DevelopmentTables } from './DevelopmentFacts';
export default function DevelopmentCommunity({data}:{data:AnalyticsOverview}){
 const options=useMemo<AgChartOptions[]>(()=>{
  const result:AgChartOptions[]=[];
  if(data.development.total)result.push({data:roadmapStates(data),title:{text:'Roadmap states · exclusive current states'},series:[{type:'bar',xKey:'state',yKey:'count',tooltip:{enabled:false}}]});
  const dates=data.development.milestones.filter(r=>r.deadline_shift_days!==null).map(r=>({...r,label:`${r.milestone_id}: ${r.title}`}));
  if(dates.length)result.push({data:dates,title:{text:'Days relative to original deadline · current page'},series:[{type:'bar',xKey:'label',yKey:'deadline_shift_days',yName:'Revised deadline shift',tooltip:{enabled:false}},{type:'bar',xKey:'label',yKey:'delivery_delay_days',yName:'Asserted delivery delay',tooltip:{enabled:false}}]});
  const github=data.development.github;
  if(github.available)result.push({data:Object.entries(github.counts??{}).map(([key,count])=>({key,count})),title:{text:'Retained GitHub snapshot counts · overlapping PR merge subset'},series:[{type:'bar',xKey:'key',yKey:'count',tooltip:{enabled:false}}]});
  const rewards=rewardSlices(data.maintainer.project_rewards);
  if(rewards.length)result.push({data:rewards,title:{text:'Project rewards · eligible entitlements only'},series:[{type:'pie',angleKey:'count',legendItemKey:'state',tooltip:{enabled:false}}]});
  return result;
 },[data]);
 const columns=useMemo<ColDef<AnalyticsMilestone>[]>(()=>[{field:'title',minWidth:180},{field:'status',minWidth:155},{field:'original_deadline',headerName:'Original deadline',valueFormatter:p=>p.value??'Unknown',minWidth:160},{field:'current_deadline',headerName:'Revised deadline',minWidth:160},{field:'actual_completion_date',headerName:'Asserted delivery',valueFormatter:p=>p.value??'Unknown / not currently delivered',minWidth:230},{field:'timing',minWidth:170},{field:'revision_count',headerName:'Recorded revisions',minWidth:170},{field:'deadline_revision_count',headerName:'Deadline revisions',minWidth:170},{field:'overdue',minWidth:110},{field:'reopened_after_delivery',headerName:'Reopened',minWidth:130}],[]);
 return <section aria-label="Community development dashboard"><p className="badge">AG Charts Community + AG Grid Community · development view</p><DevelopmentOverview data={data}/>{!data.development.total&&<p>No published roadmap commitments yet.</p>}
 <div className="analytics-charts">{options.map((option,i)=><div key={i} className="analytics-chart" role="region" aria-label={String(option.title?.text)}><AgCharts options={option}/></div>)}</div>
 <p>Deadline bars use calendar-day differences calculated by the backend. Negative delay means earlier than the original deadline. Missing dates are not plotted. Exact dates and every chart count are available below.</p>
 {!!data.development.milestones.length&&<div className="analytics-grid" aria-label="Milestone delivery history grid"><AgGridReact<AnalyticsMilestone> rowData={data.development.milestones} columnDefs={columns} defaultColDef={{sortable:true,resizable:true,editable:false}} getRowId={p=>String(p.data.milestone_id)}/></div>}
 <p>Grid column sorting applies to the current milestone page. Global order is stable milestone ID ascending.</p><DevelopmentTables data={data}/></section>;
}
