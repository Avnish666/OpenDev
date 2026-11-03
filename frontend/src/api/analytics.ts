import type { BudgetVariance } from './transparency';
import type { ProgressSummary, Counts } from './progress';
import type { DeliveryRow, Indicator, Profile } from './credibility';
export interface AnalyticsExpense { id:number; category:string; amount_cents:number; currency:string; expense_date:string; approved_public_support:boolean; public_category_finding_count:number }
export interface ExpenseGroup {key:string;expense_count:number;amount_cents:number}
export interface ExpenseFilters {category:string;evidence:'all'|'supported'|'unsupported';date_from:string;date_to:string;sort:'date_desc'|'date_asc'}
export const defaultExpenseFilters:ExpenseFilters={category:'',evidence:'all',date_from:'',date_to:'',sort:'date_desc'};
export interface AnalyticsMilestone extends DeliveryRow {revision_count:number;deadline_revision_count:number;overdue:boolean;deadline_shift_days:number|null;delivery_delay_days:number|null}
export interface AnalyticsGithub {available:boolean;repository_name:string|null;counts:Record<string,number>|null;sync:ProgressSummary['sync'];observed_at:string|null;snapshot_age_seconds:number|null;issues:NonNullable<ProgressSummary['activity']>['issues'];pull_requests:NonNullable<ProgressSummary['activity']>['pull_requests'];milestones:ProgressSummary['github_milestones'];recent_commits:{sha:string;committed_at:string}[];exhaustive:false;limitations:string[]}
export type AnalyticsView='financial'|'development'|'spending'|'maintainer';
export interface AnalyticsOverview {
 schema_version:'1'; project_id:number; currency:string; as_of:string; visibility:'public_active_project'; funding_goal_cents:number;
 financial:{ project_id:number; currency:string; audience:'public_evidence_only'; gross_completed_funding_cents:number; refund_excluded_cents:number; reversal_excluded_cents:number; exact_refund_total_cents:null; net_recorded_funding_cents:number; published_reported_spending_cents:number; funding_minus_reported_expenditure_cents:number; published_expense_count:number; expenses_with_documents_count:number; expenses_with_documents_cents:number; expenses_without_documents_count:number; expenses_without_documents_cents:number; unresolved_expenses_count:null; unresolved_discrepancy_count:null; independently_payment_matched_cents:0; evidence_coverage:{classification:string;expense_count:number;amount_cents:number}[];budget_variance:BudgetVariance[];calculated_at:string;notes:string[] };
 expense_analysis:{categories:ExpenseGroup[];months:ExpenseGroup[];expense_count:number;reported_spending_cents:number;date_basis:'maintainer_reported_expense_date'};
 expense_filters:Omit<ExpenseFilters,'date_from'|'date_to'>&{date_from:string|null;date_to:string|null};public_unresolved_finding_count:number;funding_trend:{available:false;reason:string};
 budget:BudgetVariance[];expenses:AnalyticsExpense[];expense_total:number;expense_limit:number;expense_offset:number;
 development:{counts:Counts;milestones:AnalyticsMilestone[];github:AnalyticsGithub;total:number;limit:number;offset:number;github_counts:Record<string,number>|null;last_successful_sync_at:string|null;github_stale:boolean};
 maintainer:{project_rewards:Indicator[];owner_id:number;participation:Record<string,number>;delivery:Indicator[];rewards:Indicator[];financial:Profile['financial'];scope:string;attribution:string};limitations:string[];
}
export async function loadAnalytics(projectId:number,offset:number,signal:AbortSignal,filters:ExpenseFilters=defaultExpenseFilters,milestoneOffset=0,dimensions:object={}):Promise<AnalyticsOverview>{
 const params=new URLSearchParams({limit:'50',offset:String(offset),milestone_offset:String(milestoneOffset)});for(const [key,value] of Object.entries(filters))if(value)params.set(key,value);
 for(const [key,value] of Object.entries(dimensions))if(value&&!['participation','reward'].includes(key))params.set(key,value);
 const response=await fetch(`${import.meta.env.VITE_API_URL??''}/api/projects/${projectId}/analytics/overview?${params}`,{credentials:'include',cache:'no-store',signal});
 if(!response.ok)throw new Error(response.status===404?'Public project unavailable.':response.status===413?'This public dataset exceeds the bounded analytics capacity.':'Unable to load analytics. Please retry.');
 const data:AnalyticsOverview=await response.json();
 if(data.schema_version!=='1'||data.project_id!==projectId||data.visibility!=='public_active_project'||data.financial.audience!=='public_evidence_only'||data.currency!==data.financial.currency||!data.development?.github||!Array.isArray(data.maintainer?.project_rewards)||!Array.isArray(data.budget)||!Array.isArray(data.expenses)||!Array.isArray(data.expense_analysis?.months)||!Array.isArray(data.expense_analysis?.categories)||data.funding_trend?.available!==false)throw new Error('Invalid public analytics response.');
 return data;
}
export function studioData(data:AnalyticsOverview){
 const f=data.financial;
 const money=[data.funding_goal_cents,f.gross_completed_funding_cents,f.refund_excluded_cents,f.reversal_excluded_cents,f.net_recorded_funding_cents,f.published_reported_spending_cents,f.funding_minus_reported_expenditure_cents,...data.budget.flatMap(r=>[r.allocated_cents,r.reported_spending_cents,r.remaining_cents,r.overspend_cents]),...data.expenses.map(r=>r.amount_cents),f.expenses_with_documents_cents,f.expenses_without_documents_cents,data.expense_analysis.reported_spending_cents,...data.expense_analysis.categories.map(r=>r.amount_cents),...data.expense_analysis.months.map(r=>r.amount_cents)];
 if(money.some(v=>!Number.isSafeInteger(v)))throw new Error('Amounts exceed safe browser analytics range; inspect exact API integers.');
 return {sources:[
  {id:'financial',data:[{currency:data.currency,funding_goal_cents:data.funding_goal_cents,gross_completed_funding_cents:f.gross_completed_funding_cents,refund_excluded_cents:f.refund_excluded_cents,reversal_excluded_cents:f.reversal_excluded_cents,net_recorded_funding_cents:f.net_recorded_funding_cents,published_reported_spending_cents:f.published_reported_spending_cents,funding_minus_reported_expenditure_cents:f.funding_minus_reported_expenditure_cents}]},
  {id:'budget',data:data.budget.map(r=>({category:r.category,allocated_cents:r.allocated_cents,reported_spending_cents:r.reported_spending_cents,remaining_cents:r.remaining_cents,overspend_cents:r.overspend_cents,currency:data.currency}))},
  {id:'expenses',data:data.expenses.map(r=>({id:r.id,category:r.category,amount_cents:r.amount_cents,currency:r.currency,expense_date:r.expense_date,approved_public_support:r.approved_public_support,public_category_finding_count:r.public_category_finding_count}))},
  {id:'expense_categories',data:data.expense_analysis.categories.map(r=>({category:r.key,expense_count:r.expense_count,amount_cents:r.amount_cents,currency:data.currency}))},
  {id:'expense_months',data:data.expense_analysis.months.map(r=>({month:r.key,expense_count:r.expense_count,amount_cents:r.amount_cents,currency:data.currency}))},
  {id:'evidence',data:[{support:'With public documents',expense_count:f.expenses_with_documents_count,amount_cents:f.expenses_with_documents_cents,currency:data.currency},{support:'Without public documents',expense_count:f.expenses_without_documents_count,amount_cents:f.expenses_without_documents_cents,currency:data.currency}]},
  {id:'development',data:data.development.milestones.map(r=>({milestone_id:r.milestone_id,commitment_label:`${r.milestone_id}: ${r.title}`,title:r.title,revision_count:r.revision_count,deadline_revision_count:r.deadline_revision_count,overdue:r.overdue,deadline_shift_days:r.deadline_shift_days,delivery_delay_days:r.delivery_delay_days,status:r.status,original_deadline:r.original_deadline,current_deadline:r.current_deadline,actual_completion_date:r.actual_completion_date,timing:r.timing}))},
  {id:'development_kpis',data:[{total:data.development.counts.total,delivered:data.development.counts.delivered,in_progress:data.development.counts.in_progress,overdue_unfinished:data.development.counts.overdue_unfinished,cancelled:data.development.counts.cancelled,reopened:data.development.counts.reopened,on_time:data.development.counts.on_time,late:data.development.counts.late}]},
  {id:'roadmap_states',data:roadmapStates(data)},
  {id:'participation',data:Object.entries(data.maintainer.participation).map(([role,count])=>({role,count}))},
  {id:'project_rewards',data:data.maintainer.project_rewards.map(r=>({key:r.key,label:r.label,numerator:r.numerator,denominator:r.denominator,sample_size:r.sample_size,state:r.state}))},
  {id:'github_commits',data:data.development.github.recent_commits.map(r=>({sha:r.sha,committed_at:r.committed_at}))},
  {id:'maintainer_delivery',data:data.maintainer.delivery.map(r=>({key:r.key,numerator:r.numerator,denominator:r.denominator,sample_size:r.sample_size,state:r.state}))},
  {id:'reward_fulfillment',data:data.maintainer.rewards.map(r=>({key:r.key,numerator:r.numerator,denominator:r.denominator,sample_size:r.sample_size,state:r.state}))},
  {id:'github_counts',data:Object.entries(data.development.github_counts??{}).map(([key,count])=>({key,count,last_successful_sync_at:data.development.last_successful_sync_at,stale:data.development.github_stale}))},
  {id:'reporting_coverage',data:data.maintainer.financial.flatMap(p=>p.metrics.map(m=>({project_id:p.project_id,currency:p.currency,key:m.key,numerator:m.numerator,denominator:m.denominator,sample_size:m.sample_size,state:m.state})))},
 ]};
}
export const safeBudget=(data:AnalyticsOverview)=>data.budget.filter(r=>[r.allocated_cents,r.reported_spending_cents].every(Number.isSafeInteger));
export function rendererAllowed(renderer:string,installed:boolean,licensed:boolean,evaluation:boolean,hostname:string){return renderer==='studio'&&installed&&(licensed||(evaluation&&['localhost','127.0.0.1','[::1]'].includes(hostname)));}

export function roadmapStates(data:AnalyticsOverview){return (['planned','in_progress','submitted_for_review','delivered','cancelled'] as const).map(key=>({state:key==='delivered'?'delivered (asserted)':key,count:data.development.counts[key]}));}
export function rewardSlices(metrics:Indicator[]){return metrics.filter(r=>['fulfilled','pending'].includes(r.key)&&r.state==='recorded'&&r.numerator!==null&&Number.isSafeInteger(r.numerator)&&r.denominator!==null&&r.denominator>0).map(r=>({state:r.key,count:r.numerator!}));}
