import type { BudgetVariance } from './transparency';
import type { Counts } from './progress';
import type { DeliveryRow, Indicator, Profile } from './credibility';
export interface AnalyticsExpense { id:number; category:string; amount_cents:number; currency:string; expense_date:string; approved_public_support:boolean; public_category_finding_count:number }
export interface AnalyticsOverview {
 schema_version:'1'; project_id:number; currency:string; as_of:string; visibility:'public_active_project'; funding_goal_cents:number;
 financial:{ project_id:number; currency:string; audience:'public_evidence_only'; gross_completed_funding_cents:number; refund_excluded_cents:number; reversal_excluded_cents:number; exact_refund_total_cents:null; net_recorded_funding_cents:number; published_reported_spending_cents:number; funding_minus_reported_expenditure_cents:number; published_expense_count:number; expenses_with_documents_count:number; expenses_with_documents_cents:number; expenses_without_documents_count:number; expenses_without_documents_cents:number; unresolved_expenses_count:null; unresolved_discrepancy_count:null; independently_payment_matched_cents:0; evidence_coverage:{classification:string;expense_count:number;amount_cents:number}[];budget_variance:BudgetVariance[];calculated_at:string;notes:string[] };
 budget:BudgetVariance[];expenses:AnalyticsExpense[];expense_total:number;expense_limit:number;expense_offset:number;
 development:{counts:Counts;milestones:DeliveryRow[];total:number;limit:number;offset:number;github_counts:Record<string,number>|null;last_successful_sync_at:string|null;github_stale:boolean};
 maintainer:{owner_id:number;participation:Record<string,number>;delivery:Indicator[];rewards:Indicator[];financial:Profile['financial'];scope:string;attribution:string};limitations:string[];
}
export async function loadAnalytics(projectId:number,offset:number,signal:AbortSignal):Promise<AnalyticsOverview>{
 const response=await fetch(`${import.meta.env.VITE_API_URL??''}/api/projects/${projectId}/analytics/overview?limit=50&offset=${offset}`,{credentials:'include',cache:'no-store',signal});
 if(!response.ok)throw new Error(response.status===404?'Public project unavailable.':response.status===413?'This public dataset exceeds the bounded analytics capacity.':'Unable to load analytics. Please retry.');
 const data:AnalyticsOverview=await response.json();
 if(data.schema_version!=='1'||data.project_id!==projectId||data.visibility!=='public_active_project'||data.financial.audience!=='public_evidence_only'||data.currency!==data.financial.currency||!Array.isArray(data.budget)||!Array.isArray(data.expenses))throw new Error('Invalid public analytics response.');
 return data;
}
export function studioData(data:AnalyticsOverview){
 const f=data.financial;
 const money=[data.funding_goal_cents,f.gross_completed_funding_cents,f.refund_excluded_cents,f.reversal_excluded_cents,f.net_recorded_funding_cents,f.published_reported_spending_cents,f.funding_minus_reported_expenditure_cents,...data.budget.flatMap(r=>[r.allocated_cents,r.reported_spending_cents,r.remaining_cents,r.overspend_cents]),...data.expenses.map(r=>r.amount_cents)];
 if(money.some(v=>!Number.isSafeInteger(v)))throw new Error('Amounts exceed safe browser analytics range; inspect exact API integers.');
 return {sources:[
  {id:'financial',data:[{currency:data.currency,funding_goal_cents:data.funding_goal_cents,gross_completed_funding_cents:f.gross_completed_funding_cents,refund_excluded_cents:f.refund_excluded_cents,reversal_excluded_cents:f.reversal_excluded_cents,net_recorded_funding_cents:f.net_recorded_funding_cents,published_reported_spending_cents:f.published_reported_spending_cents,funding_minus_reported_expenditure_cents:f.funding_minus_reported_expenditure_cents}]},
  {id:'budget',data:data.budget.map(r=>({category:r.category,allocated_cents:r.allocated_cents,reported_spending_cents:r.reported_spending_cents,remaining_cents:r.remaining_cents,overspend_cents:r.overspend_cents,currency:data.currency}))},
  {id:'expenses',data:data.expenses.map(r=>({id:r.id,category:r.category,amount_cents:r.amount_cents,currency:r.currency,expense_date:r.expense_date,approved_public_support:r.approved_public_support,public_category_finding_count:r.public_category_finding_count}))},
  {id:'development',data:data.development.milestones.map(r=>({milestone_id:r.milestone_id,status:r.status,original_deadline:r.original_deadline,current_deadline:r.current_deadline,actual_completion_date:r.actual_completion_date,timing:r.timing}))},
  {id:'maintainer_delivery',data:data.maintainer.delivery.map(r=>({key:r.key,numerator:r.numerator,denominator:r.denominator,sample_size:r.sample_size,state:r.state}))},
  {id:'reward_fulfillment',data:data.maintainer.rewards.map(r=>({key:r.key,numerator:r.numerator,denominator:r.denominator,sample_size:r.sample_size,state:r.state}))},
  {id:'github_counts',data:Object.entries(data.development.github_counts??{}).map(([key,count])=>({key,count,last_successful_sync_at:data.development.last_successful_sync_at,stale:data.development.github_stale}))},
  {id:'reporting_coverage',data:data.maintainer.financial.flatMap(p=>p.metrics.map(m=>({project_id:p.project_id,currency:p.currency,key:m.key,numerator:m.numerator,denominator:m.denominator,sample_size:m.sample_size,state:m.state})))},
 ]};
}
export const safeBudget=(data:AnalyticsOverview)=>data.budget.filter(r=>[r.allocated_cents,r.reported_spending_cents].every(Number.isSafeInteger));
export function rendererAllowed(renderer:string,installed:boolean,licensed:boolean,evaluation:boolean,hostname:string){return renderer==='studio'&&installed&&(licensed||(evaluation&&['localhost','127.0.0.1','[::1]'].includes(hostname)));}
