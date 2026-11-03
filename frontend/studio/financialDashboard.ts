import type { AgDataSourcesDefinition, AgFieldDefinition, AgReportState, AgWidgetState, AgDefaultRegistry } from 'ag-studio';
import { studioData, type AnalyticsOverview } from '../src/api/analytics';

// 3.0.0 initialState -> pages -> widgets/dataMapping, with source.field references.
// No joins, expressions or financial sums; conversion to major units is display only.
export function financialDashboard(data:AnalyticsOverview, mobile=false):{sources:AgDataSourcesDefinition;state:AgReportState} {
 const allowed=new Set(['financial','budget','expenses','expense_categories','expense_months','evidence']);
 const sources:AgDataSourcesDefinition={sources:studioData(data).sources.filter(s=>allowed.has(s.id)&&s.data.length>0).map(source=>({
  ...source,
  fields:Object.keys(source.data[0]).map((id):AgFieldDefinition=>{
   const sample=(source.data[0] as Record<string,unknown>)[id];
   const monetary=id.endsWith('_cents');
   return {id,name:id.replaceAll('_cents','').replaceAll('_',' '),editable:false,
    format:monetary?'decimalFormat':typeof sample==='number'?'integerFormat':typeof sample==='boolean'?'booleanFormat':'textFormat',
    ...(monetary?{accessor:(row:Record<string,unknown>)=>Number(row[id])/100,createValueFormatter:()=>value=>new Intl.NumberFormat('en-US',{style:'currency',currency:data.currency}).format(Number(value))}:{})};
  }),
 }))};
 const widgets:Record<string,AgWidgetState<AgDefaultRegistry>>={};const widgetLayout:NonNullable<AgReportState['pages'][number]['widgetLayout']>={};
 let y=0;
 const add=(id:string,widget:AgWidgetState<AgDefaultRegistry>,height=3)=>{widgets[id]=widget;widgetLayout[id]={xTrack:0,yTrack:y,xSpan:mobile?1:2,ySpan:height};y+=height;};
 const title=(text:string)=>({title:{text,enabled:true}});
 const ref=(id:string)=>({id});
 const measure=(id:string)=>({id,aggregation:'first' as const});
 for(const [field,label] of [['net_recorded_funding_cents','Net recorded funding'],['published_reported_spending_cents','Published reported spending'],['funding_minus_reported_expenditure_cents','Calculated difference · not a verified bank balance']] as const){
  add(field,{type:'value',format:title(`${label} (${data.currency})`),dataMapping:{value:[ref(`financial.${field}`)]}},2);
 }
 if(data.budget.length)add('budget',{type:'bar-chart-grouped',format:title(`Budget comparison (${data.currency})`),dataMapping:{categoryKey:[ref('budget.category')],valueKey:['allocated_cents','reported_spending_cents','remaining_cents'].map(f=>measure(`budget.${f}`))}},5);
 if(data.expense_analysis.categories.length)add('categories',{type:'pie-chart',format:title(`Filtered expense categories (${data.currency})`),dataMapping:{categoryKey:[ref('expense_categories.category')],valueKey:[measure('expense_categories.amount_cents')]}},5);
 if(data.expense_analysis.months.length)add('months',{type:'bar-chart-grouped',format:title(`Filtered expense months (${data.currency})`),dataMapping:{categoryKey:[ref('expense_months.month')],valueKey:[measure('expense_months.amount_cents')]}},5);
 if(data.financial.published_expense_count)add('coverage',{type:'pie-chart',format:title(`Public document coverage (${data.currency})`),dataMapping:{categoryKey:[ref('evidence.support')],valueKey:[measure('evidence.amount_cents')]}},5);
 if(data.expenses.length)add('expenses',{type:'grid',format:title(`Published expense page (${data.currency})`),dataMapping:{cols:['id','category','amount_cents','expense_date','approved_public_support'].map(f=>ref(`expenses.${f}`))}},5);
 return {sources,state:{version:'3.0.0',selectedPageId:'financial',pages:[{id:'financial',widgets,widgetLayout,layout:{columns:mobile?1:2,minWidth:280,rowHeight:65,pagePadding:12}}]}};
}
