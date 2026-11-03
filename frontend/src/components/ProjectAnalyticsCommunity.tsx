import { useMemo } from 'react';
import { AgCharts } from 'ag-charts-react';
import { AllCommunityModule as ChartsCommunityModule, ModuleRegistry as ChartsRegistry, type AgChartOptions } from 'ag-charts-community';
import { AgGridReact } from 'ag-grid-react';
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community';
import { safeBudget, type AnalyticsOverview, type AnalyticsExpense } from '../api/analytics';
import { displayMoney } from '../api/transparency';
import DevelopmentCommunity from './DevelopmentCommunity';
import { FinancialOverview, FinancialTables } from './FinancialFacts';
ModuleRegistry.registerModules([AllCommunityModule]);ChartsRegistry.registerModules([ChartsCommunityModule]);
export default function ProjectAnalyticsCommunity({data,view='financial'}:{data:AnalyticsOverview;view?:'financial'|'development'}){return view==='development'?<DevelopmentCommunity data={data}/>:<FinancialCommunity data={data}/>;}
function FinancialCommunity({data}:{data:AnalyticsOverview}){
 const rows=useMemo(()=>safeBudget(data).map(r=>({...r,allocated:r.allocated_cents/100,reported:r.reported_spending_cents/100,remaining:r.remaining_cents/100})),[data]);
 const options=useMemo<AgChartOptions[]>(()=>{
  const categories=data.expense_analysis.categories.filter(r=>Number.isSafeInteger(r.amount_cents)).map(r=>({...r,amount:r.amount_cents/100}));
  const months=data.expense_analysis.months.filter(r=>Number.isSafeInteger(r.amount_cents)).map(r=>({...r,amount:r.amount_cents/100}));
  const coverage=[{support:'With public documents',amount:data.financial.expenses_with_documents_cents/100},{support:'Without public documents',amount:data.financial.expenses_without_documents_cents/100}];
  const charts:AgChartOptions[]=[];
  if(rows.length)charts.push({data:rows,title:{text:`Budget comparison (${data.currency})`},series:[{type:'bar',xKey:'category',yKey:'allocated',yName:'Planned allocation',tooltip:{enabled:false}},{type:'bar',xKey:'category',yKey:'reported',yName:'Reported spending',tooltip:{enabled:false}},{type:'bar',xKey:'category',yKey:'remaining',yName:'Remaining (negative = overrun)',tooltip:{enabled:false}}]});
  if(categories.length)charts.push({data:categories,title:{text:`Filtered spending by category (${data.currency})`},series:[{type:'pie',angleKey:'amount',legendItemKey:'key',tooltip:{enabled:false}}]});
  if(months.length)charts.push({data:months,title:{text:`Filtered expenses by month (${data.currency})`},series:[{type:'bar',xKey:'key',yKey:'amount',yName:'Reported expense amount',tooltip:{enabled:false}}]});
  if([data.financial.expenses_with_documents_cents,data.financial.expenses_without_documents_cents].every(Number.isSafeInteger)&&data.financial.published_expense_count>0)charts.push({data:coverage,title:{text:`Public document coverage (${data.currency})`},series:[{type:'pie',angleKey:'amount',legendItemKey:'support',tooltip:{enabled:false}}]});
  return charts;
 },[rows,data]);
 const columns=useMemo<ColDef<AnalyticsExpense>[]>(()=>[{field:'id',headerName:'Public detail',minWidth:155,cellRenderer:(p:{value:number})=><a href={`#/projects/${data.project_id}/expenses/${p.value}`}>Expense {p.value}</a>},{field:'category',headerName:'Published category',flex:1,minWidth:160},{field:'amount_cents',headerName:'Reported amount',valueFormatter:p=>displayMoney(p.value,data.currency),minWidth:170},{field:'expense_date',headerName:'Expense date',minWidth:145},{field:'approved_public_support',headerName:'Public document support',valueFormatter:p=>p.value?'Approved redacted support':'No public documents',minWidth:210},{field:'public_category_finding_count',headerName:'Category findings',minWidth:155}], [data.currency,data.project_id]);
 return <div><p className="badge">AG Charts Community + AG Grid Community · not AG Studio</p><FinancialOverview data={data}/>
  {(rows.length!==data.budget.length||[...data.expense_analysis.categories,...data.expense_analysis.months].some(r=>!Number.isSafeInteger(r.amount_cents))||![data.financial.expenses_with_documents_cents,data.financial.expenses_without_documents_cents].every(Number.isSafeInteger))&&<p role="status">Some amounts exceed safe browser chart range. Inspect exact API values; unsafe amounts are not charted.</p>}
  <div className="analytics-charts">{options.map((option,i)=><div key={i} className="analytics-chart" role="region" aria-label={String(option.title?.text)}><AgCharts options={option}/></div>)}</div>
  <FinancialTables data={data}/>
  <h4>Published expense analytics · current page</h4><p>Expense charts use all matching records. Months are maintainer-reported expense dates, not receipt uploads or PayPal capture dates. Months with no observations are omitted.</p>
  {!data.expenses.length?<p>No published expense rows match these filters.</p>:<div className="analytics-grid" aria-label="Published expense detail grid"><AgGridReact<AnalyticsExpense> rowData={data.expenses} columnDefs={columns} defaultColDef={{sortable:true,resizable:true,editable:false}} getRowId={p=>String(p.data.id)} /></div>}
  <p>Column sorting applies to the current page. Use expense order above for server-side date sorting across all pages. Category findings describe full-project categories, not individual payment allegations.</p>
 </div>;
}
