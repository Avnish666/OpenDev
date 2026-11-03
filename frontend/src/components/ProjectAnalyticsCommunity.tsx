import { useMemo } from 'react';
import { AgCharts } from 'ag-charts-react';
import { AllCommunityModule as ChartsCommunityModule, ModuleRegistry as ChartsRegistry, type AgChartOptions } from 'ag-charts-community';
import { AgGridReact } from 'ag-grid-react';
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community';
import { safeBudget, type AnalyticsOverview, type AnalyticsExpense } from '../api/analytics';
import { displayMoney } from '../api/transparency';
ModuleRegistry.registerModules([AllCommunityModule]);ChartsRegistry.registerModules([ChartsCommunityModule]);
export default function ProjectAnalyticsCommunity({data}:{data:AnalyticsOverview}){
 const rows=useMemo(()=>safeBudget(data),[data]);
 const options=useMemo<AgChartOptions[]>(()=>[
  {data:rows,title:{text:`Budget versus reported spending (${data.currency} minor units)`},series:[{type:'bar',xKey:'category',yKey:'allocated_cents',yName:'Allocated',tooltip:{enabled:false}},{type:'bar',xKey:'category',yKey:'reported_spending_cents',yName:'Reported spending',tooltip:{enabled:false}}]},
  {data:rows.filter(r=>r.reported_spending_cents>0),title:{text:`Published spending by category (${data.currency} minor units)`},series:[{type:'pie',angleKey:'reported_spending_cents',legendItemKey:'category',tooltip:{enabled:false}}]},
 ],[rows,data.currency]);
 const columns=useMemo<ColDef<AnalyticsExpense>[]>(()=>[{field:'category',headerName:'Published category',flex:1,minWidth:160},{field:'amount_cents',headerName:'Reported amount',valueFormatter:p=>displayMoney(p.value,data.currency),minWidth:170},{field:'expense_date',headerName:'Expense date',minWidth:145},{field:'approved_public_support',headerName:'Approved public support',minWidth:190},{field:'public_category_finding_count',headerName:'Category findings',minWidth:155}], [data.currency]);
 const cards=[['Net recorded funding',data.financial.net_recorded_funding_cents],['Published reported spending',data.financial.published_reported_spending_cents],['Calculated difference · not cash balance',data.financial.funding_minus_reported_expenditure_cents],['Funding goal',data.funding_goal_cents]] as const;
 return <div><p className="badge">AG Charts Community + AG Grid Community · not AG Studio</p><div className="grid">{cards.map(([label,value])=><article key={label}><h4>{label}</h4><p>{displayMoney(value,data.currency)}</p></article>)}</div>
  {rows.length!==data.budget.length&&<p role="status">Some amounts exceed safe browser chart range. Inspect exact API values; unsafe amounts are not charted.</p>}
  {!rows.length?<p>No public budget or spending categories yet.</p>:<div className="analytics-charts">{options.map((option,i)=><div key={i} className="analytics-chart"><AgCharts options={option}/></div>)}</div>}
  <details><summary>Exact category values and chart alternative</summary><ul>{data.budget.map(r=><li key={r.category}>{r.category}: allocated {displayMoney(r.allocated_cents,data.currency)}; reported {displayMoney(r.reported_spending_cents,data.currency)}; remaining {displayMoney(r.remaining_cents,data.currency)}; overrun {displayMoney(r.overspend_cents,data.currency)}</li>)}</ul></details>
  <h4>Published expense analytics · current page</h4>{!data.expenses.length?<p>No published expense rows in this page.</p>:<div className="analytics-grid"><AgGridReact<AnalyticsExpense> rowData={data.expenses} columnDefs={columns} defaultColDef={{sortable:true,filter:true,resizable:true,editable:false}} getRowId={p=>String(p.data.id)} /></div>}
  <p>Approved public support is not payment verification. Category findings are not receipt-level allegations. Full totals are separate from paged expense rows.</p>
 </div>;
}
