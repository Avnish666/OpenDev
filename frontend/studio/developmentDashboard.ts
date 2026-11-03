import type { AgDataSourcesDefinition, AgFieldDefinition, AgReportState, AgWidgetState, AgDefaultRegistry } from 'ag-studio';
import { studioData, rewardSlices, type AnalyticsOverview } from '../src/api/analytics';
export function developmentDashboard(data:AnalyticsOverview,mobile=false):{sources:AgDataSourcesDefinition;state:AgReportState}{
 const allowed=new Set(['development','development_kpis','roadmap_states','maintainer_delivery','participation','project_rewards','github_counts','github_commits','reporting_coverage']);
 const inputs=[...studioData(data).sources.filter(s=>allowed.has(s.id)),{id:'reward_status',data:rewardSlices(data.maintainer.project_rewards)}];
 const numbers=new Set(['numerator','denominator','sample_size','deadline_shift_days','delivery_delay_days']);
 const sources:AgDataSourcesDefinition={sources:inputs.filter(s=>s.data.length>0).map(s=>({...s,fields:Object.keys(s.data[0]).map((id):AgFieldDefinition=>({id,name:id.replaceAll('_',' '),editable:false,format:numbers.has(id)||typeof (s.data[0] as Record<string,unknown>)[id]==='number'?'integerFormat':typeof (s.data[0] as Record<string,unknown>)[id]==='boolean'?'booleanFormat':'textFormat'}))}))};
 const widgets:Record<string,AgWidgetState<AgDefaultRegistry>>={},widgetLayout:NonNullable<AgReportState['pages'][number]['widgetLayout']>={};let y=0;
 const add=(id:string,widget:AgWidgetState<AgDefaultRegistry>,height=4)=>{widgets[id]=widget;widgetLayout[id]={xTrack:0,yTrack:y,xSpan:mobile?1:2,ySpan:height};y+=height;};
 const title=(text:string)=>({title:{text,enabled:true}}),ref=(id:string)=>({id}),measure=(id:string)=>({id,aggregation:'first' as const});
 for(const [field,label] of [['total','Published roadmap commitments'],['delivered','Maintainer-asserted delivered'],['overdue_unfinished','Overdue unfinished (overlapping indicator)']] as const)add(field,{type:'value',format:title(label),dataMapping:{value:[ref('development_kpis.'+field)]}},2);
 if(data.development.total)add('states',{type:'bar-chart-grouped',format:title('Roadmap states · exclusive'),dataMapping:{categoryKey:[ref('roadmap_states.state')],valueKey:[measure('roadmap_states.count')]}});
 if(data.development.milestones.some(r=>r.original_deadline))add('deadlines',{type:'bar-chart-grouped',format:title('Days relative to original deadline · page'),dataMapping:{categoryKey:[ref('development.commitment_label')],valueKey:[measure('development.deadline_shift_days'),measure('development.delivery_delay_days')]}});
 if(data.development.milestones.length)add('history',{type:'grid',format:title('Milestone delivery history · page'),dataMapping:{cols:['milestone_id','title','status','original_deadline','current_deadline','actual_completion_date','timing','revision_count','deadline_revision_count','overdue'].map(k=>ref('development.'+k))}},5);
 if(data.development.github.available)add('github',{type:'bar-chart-grouped',format:title('Retained GitHub counts · merged subset overlaps closed'),dataMapping:{categoryKey:[ref('github_counts.key')],valueKey:[measure('github_counts.count')]}});
 if(data.development.github.recent_commits.length)add('commits',{type:'grid',format:title('Recent synchronized commit sample'),dataMapping:{cols:[ref('github_commits.sha'),ref('github_commits.committed_at')]}});
 add('maintainer',{type:'grid',format:title('Owner delivery metrics · explicit denominators'),dataMapping:{cols:['key','numerator','denominator','sample_size','state'].map(k=>ref('maintainer_delivery.'+k))}},5);
 add('roles',{type:'bar-chart-grouped',format:title('Owner versus team participation'),dataMapping:{categoryKey:[ref('participation.role')],valueKey:[measure('participation.count')]}});
 if(rewardSlices(data.maintainer.project_rewards).length)add('rewards',{type:'pie-chart',format:title('Project rewards · eligible only'),dataMapping:{categoryKey:[ref('reward_status.state')],valueKey:[measure('reward_status.count')]}});
 if(data.maintainer.project_rewards.length)add('reward_metrics',{type:'grid',format:title('Project reward eligibility and exclusions'),dataMapping:{cols:['label','numerator','denominator','sample_size','state'].map(k=>ref('project_rewards.'+k))}},5);
 return {sources,state:{version:'3.0.0',selectedPageId:'development',pages:[{id:'development',widgets,widgetLayout,layout:{columns:mobile?1:2,minWidth:280,rowHeight:65,pagePadding:12}}]}};
}
