"""Allowlisted public projections; callers must use accountability.read_snapshot."""
from sqlalchemy import select, func, text
from fastapi import HTTPException
from app.models.project import Project
from app.models.roadmap import ProjectRoadmapMilestone as Milestone
from app.models.github_progress import GitHubMilestoneSnapshot as GHMilestone
from app.schemas.project import ProjectResponse
from app.schemas.transparency import PublicTransparency, LedgerPage
from app.schemas.roadmap import MilestoneResponse, HistoryResponse
from app.schemas.github_progress import ActivityResponse, MilestoneResponse as GHResponse
from app.schemas.credibility import CredibilityProfile, DeliveryRow
from app.services import transparency, credibility, roadmap, github_progress
from app.agent.citations import evidence
from app.agent.contracts import ToolCall, AgentEvidence

PAGE=50


class EvidenceTools:
    def __init__(self,db):
        if db.scalar(text('SHOW transaction_read_only'))!='on':
            raise ValueError('Evidence tools require a read-only snapshot')
        self.db=db
        self.now=db.scalar(select(func.transaction_timestamp()))

    def project(self,pid):return transparency.public_project(self.db,pid)

    def get_project_overview(self,project_id:int) -> AgentEvidence:
        p=self.project(project_id)
        return evidence('project',p.id,p.id,'overview',ProjectResponse.model_validate(p).model_dump(),f'/api/projects/{p.id}',self.now,p.updated_at,False)

    def get_project_finances(self,project_id:int) -> AgentEvidence:
        p=self.project(project_id);data=PublicTransparency.model_validate(transparency.overview(self.db,p))
        return evidence('project',p.id,p.id,'finances',data.model_dump(),f'/api/projects/{p.id}/transparency',self.now,limitations=data.financial_summary.notes)

    def get_project_expenses(self,project_id:int,offset:int=0) -> AgentEvidence:
        self.page(offset);p=self.project(project_id)
        data=LedgerPage.model_validate(transparency.ledger(self.db,p,PAGE,offset,'date_desc','','','all'))
        return evidence('project',p.id,p.id,f'expenses:offset:{offset}',data.model_dump(),f'/api/projects/{p.id}/ledger?limit={PAGE}&offset={offset}',self.now,
            limitations=['Page of published reports; approved redaction metadata only. Receipts do not prove vendor payment.'])

    def get_project_roadmap(self,project_id:int,offset:int=0) -> AgentEvidence:
        self.page(offset);p=self.project(project_id)
        rows=self.db.scalars(select(Milestone).where(Milestone.project_id==p.id).order_by(Milestone.display_order,Milestone.id).limit(PAGE).offset(offset)).all()
        derived=credibility.delivery_rows(self.db,rows)
        items=[]
        for row,delivery in zip(rows,derived):
            history=roadmap.history(self.db,row,None,PAGE,0)
            items.append(dict(commitment=MilestoneResponse.model_validate(roadmap.view(self.db,row,None)).model_dump(),
                delivery=DeliveryRow.model_validate(delivery).model_dump(),history=[HistoryResponse.model_validate(h).model_dump() for h in history]))
        total=self.db.scalar(select(func.count()).select_from(Milestone).where(Milestone.project_id==p.id))
        return evidence('project',p.id,p.id,f'roadmap:offset:{offset}',dict(items=items,total=total,limit=PAGE,offset=offset),f'/api/projects/{p.id}/roadmap?limit={PAGE}&offset={offset}',self.now,
            limitations=[credibility.DELIVERY_LIMIT,'History preview at most 50 events per milestone; use cited milestone IDs with /api/roadmap/{id}/history pagination. Delivery is self-reported.'])

    def get_github_activity(self,project_id:int,offset:int=0) -> AgentEvidence:
        self.page(offset);p=self.project(project_id)
        github_progress.read_project(self.db,p.id,None)
        activity=ActivityResponse.model_validate(github_progress.public_activity(self.db,p.id,PAGE,offset))
        milestones=self.db.scalars(select(GHMilestone).where(GHMilestone.project_id==p.id).order_by(GHMilestone.number,GHMilestone.github_id).limit(PAGE).offset(offset)).all()
        return evidence('github_repository',p.github_repo_id,p.id,f'activity:offset:{offset}',dict(activity=activity.model_dump(),milestones=[GHResponse.model_validate(m).model_dump() for m in milestones]),
            f'/api/projects/{p.id}/github/activity?limit={PAGE}&offset={offset}',self.now,activity.sync.last_successful_sync_at,activity.sync.stale,
            ['Bounded retained snapshots and at most 30 commits, not exhaustive live GitHub activity. Absence does not prove inactivity. Milestone page uses /github/milestones.'])

    def get_maintainer_history(self,maintainer_id:int) -> AgentEvidence:
        ids=credibility.owned_ids(maintainer_id)
        if self.db.scalar(select(func.count()).select_from(Project).where(Project.id.in_(ids)))>20:
            raise HTTPException(413,'Public history exceeds baseline capacity')
        from app.models.roadmap import MilestoneStatusHistory as History
        mids=select(Milestone.id).where(Milestone.project_id.in_(ids))
        if self.db.scalar(select(func.count()).select_from(History).where(History.milestone_id.in_(mids)))>10000:
            raise HTTPException(413,'Public history exceeds baseline capacity')
        data=CredibilityProfile.model_validate(credibility.profile(self.db,maintainer_id,self.now))
        return evidence('maintainer',maintainer_id,None,'history',data.model_dump(),f'/api/maintainers/{maintainer_id}/credibility',self.now,limitations=data.limitations)

    def get_reward_fulfillment(self,project_id:int) -> AgentEvidence:
        p=self.project(project_id)
        from app.schemas.credibility import Indicator
        stats=[Indicator.model_validate(r).model_dump() for r in credibility.reward_statistics(self.db,[p],self.now)]
        result=evidence('project',p.id,p.id,'reward_fulfillment',stats,f'/api/projects/{p.id}/agent/query',self.now,
            limitations=['Project-scoped Sandbox aggregates; fulfillment is a maintainer mark. No deadlines/status-change timestamps; refunds/reversals excluded by existing eligibility rules. Citation retrieval uses the reward_fulfillment intent, not GET.'])
        result.citation.method='POST'
        result.citation.request_body={'project_id':p.id,'question':'reward_fulfillment'}
        return result

    @staticmethod
    def page(offset):
        if type(offset) is not int or not 0<=offset<=10000:raise HTTPException(422,'Offset must be 0..10000')


TOOL_NAMES=('get_project_overview','get_project_finances','get_project_expenses','get_project_roadmap','get_github_activity','get_maintainer_history','get_reward_fulfillment')


def invoke(tools:EvidenceTools,name:str,identifier:int,offset:int=0) -> AgentEvidence:
    if name not in TOOL_NAMES:raise HTTPException(422,'Unsupported evidence tool')
    if type(identifier) is not int or not 0<identifier<=9223372036854775807:raise HTTPException(422,'Invalid source identifier')
    ToolCall(name=name,identifier=identifier,offset=offset)
    method=getattr(tools,name)
    return method(identifier,offset) if name in ('get_project_expenses','get_project_roadmap','get_github_activity') else method(identifier)
