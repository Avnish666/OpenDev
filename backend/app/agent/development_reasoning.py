"""Read-only development claims; dates/counts are calculated in application code."""
from datetime import datetime, timezone
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.agent.contracts import AgentAnswer
from app.agent.financial_reasoning import FinancialClaim, FinancialPlan, render_financial

Kind = Literal['progress', 'overdue', 'on_time', 'deadlines', 'roadmap_changes',
               'github_activity', 'linked_evidence', 'activity_trend', 'delivery_support',
               'schedule_explanation', 'missing_delivery_evidence', 'maintainer_history',
               'reward_history', 'owner_comparison', 'funding_schedule', 'spending_trend', 'after_funding']
INTENTS = {
 'progress': ('What progress has this project made?',),
 'on_time': ('Which milestones were delivered on time?',),
 'deadlines': ('Which commitments were delayed or rescheduled?',),
 'roadmap_changes': ('What changed in the project roadmap?',),
 'github_activity': ('What GitHub activity is available?',),
 'linked_evidence': ('Which GitHub issues and pull requests relate to a milestone?',),
 'activity_trend': ('Has development activity increased or decreased?',),
 'delivery_support': ('Does the available GitHub evidence support a delivery assertion?',),
 'schedule_explanation': ('Why is the project behind schedule?',),
 'missing_delivery_evidence': ('What evidence is missing to assess delivery?',),
 'owner_history': ("What is this maintainer's delivery history?", 'How many public projects have they owned?',
                   'How many milestones were asserted delivered?', 'How many commitments were delivered on time?',
                   'How many were delivered late?', 'Were commitments reopened?',
                   'Does the maintainer have enough history for a meaningful assessment?'),
 'reward_history': ('What proportion of eligible reward entitlements were fulfilled?', 'Has the maintainer fulfilled rewards on previous projects?'),
 'owner_comparison': ("How does the maintainer's current project compare with their recorded previous outcomes?",),
 'funding_schedule': ('How much funding has this project received, and which commitments are overdue?',),
 'spending_trend': ('Are the reported expenses increasing while delivery is delayed?',),
 'after_funding': ('Is there evidence that project development continued after funding?',),
}


def deadline_analysis(delivery, events, evaluation_at):
    if evaluation_at.tzinfo is None:
        raise ValueError('Evaluation timestamp must be timezone-aware')
    today = evaluation_at.astimezone(timezone.utc).date()
    original = delivery['original_deadline']
    current = delivery['current_deadline']
    actual = delivery['actual_completion_date']
    # Use the earliest immutable deadline, not the current revised date.
    revisions, previous = 0, None
    for event in events:
        end = event.after_json.get('planned_end_date')
        if end is not None:
            if previous is not None and end != previous:
                revisions += 1
            previous = end
    unfinished = delivery['status'] not in ('delivered', 'cancelled')
    return dict(evaluated_at=evaluation_at, days_overdue_current=max(0, (today-current).days) if unfinished else 0,
                days_overdue_original=max(0, (today-original).days) if unfinished and original else None,
                days_late=(actual-original).days if delivery['timing']=='late' and actual and original else 0 if delivery['timing']=='on_time' else None,
                deadline_revisions=revisions, original_deadline_available=original is not None)


class DevelopmentClaim(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Kind
    references: list[str] = Field(min_length=1, max_length=6)


class DevelopmentPlan(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    development_claims: list[DevelopmentClaim] = Field(min_length=1, max_length=5)


NOTICE = ('Delivery is a maintainer assertion, not independent verification. Closed issues and merged PRs do not certify delivery. '
          'These records do not establish causes of delay, dishonesty or misuse of funding. No completion percentage or trust score is inferred.')


def render_development(plan, evidence, max_chars=6000):
    registry = {e.citation.reference:e for e in evidence}
    used, paragraphs, notes, statuses = {}, [], [NOTICE], []
    for claim in plan.development_claims:
        sources = [registry[r] for r in claim.references]
        if len(set(claim.references)) != len(sources) or any(e.visibility!='public_active_projects' for e in sources):
            raise ValueError('Invalid development citations')
        road = [e for e in sources if e.claim.startswith('roadmap:offset:')]
        finance = [e for e in sources if e.claim=='finances']
        profiles = [e for e in sources if e.claim=='history' and e.source_type=='maintainer']
        github = [e for e in sources if e.claim.startswith('activity:offset:')]
        required = {'github_activity':'github', 'activity_trend':'github', 'maintainer_history':'profile',
                    'reward_history':'profile', 'owner_comparison':'profile'}.get(claim.kind, 'road')
        expected={'github'} if required=='github' else {'profile'} if required=='profile' else {'road'}
        if claim.kind=='owner_comparison':expected.add('road')
        if claim.kind in ('funding_schedule','spending_trend','after_funding'):expected.add('finance')
        actual={name for name,rows in [('road',road),('finance',finance),('profile',profiles),('github',github)] if rows}
        if actual!=expected or len(sources)!=len(road)+len(finance)+len(profiles)+len(github):
            raise ValueError('Unrelated or missing development citation')
        if not {'github':github, 'profile':profiles, 'road':road}[required]:
            raise ValueError('Required source missing')
        if len(road)>1 or len(finance)>1 or len(profiles)>1 or len(github)>1:
            raise ValueError('Use one page per domain in each claim')
        project_ids = {e.project_id for e in sources if e.project_id is not None}
        if len(project_ids)>1:
            raise ValueError('Cross-project source')
        if profiles and project_ids:
            # Owner comparison must match the server-authorized profile, not arbitrary people.
            if any(r.value['owner_id'] != profiles[0].value['identity']['user_id'] for r in road):
                raise ValueError('Unrelated maintainer')
        parts, status = [], 'answered'
        if claim.kind in ('github_activity','activity_trend'):
            e=github[0]; a=e.value['activity']
            parts=[f"Retained GitHub snapshot counts: {json.dumps(a['counts'],sort_keys=True)}. "
                   f"Available sampled commits: {len(a['recent_commits'])}; GitHub milestones in this page: {len(e.value['milestones'])}. "
                   f"Last successful synchronization: {a['sync']['last_successful_sync_at']}; stale: {e.value['stale_at_evaluation']} "
                   f"at evaluation {e.value['evaluated_at']} (None means the available snapshot postdates evaluation).",
                   'Closed PR counts include merged PRs; these are not disjoint quantities. Initial/incremental collections are bounded, commit history is sampled, '
                   'deleted records can remain and unlinked activity need not represent funded commitments.']
            if claim.kind=='activity_trend':
                parts.append('Insufficient comparable complete time windows to establish an increase or decrease in development activity. Missing recent observations do not establish abandonment.')
                status='insufficient_evidence'
        elif claim.kind in ('maintainer_history','reward_history','owner_comparison'):
            p=profiles[0].value
            sections=['rewards'] if claim.kind=='reward_history' else ['delivery','rewards']
            parts=['Owner outcomes cover only currently owned active public projects, not a lifetime or previous-project cohort. '
                   'Team participation is separate: '+json.dumps(p['participation'],sort_keys=True)+'.']
            for section in sections:
                parts.append(section+': '+json.dumps([{k:m[k] for k in ('key','numerator','denominator','sample_size','state')} for m in p[section]],sort_keys=True)+'.')
            parts.append('Financial reporting indicators and GitHub repository signals are separate from owner delivery and team participation. '
                         'No financial amounts are summed across currencies; repository activity is not personal authorship. '
                         'Reward fulfillment fractions use eligible completed captures only; refunded/reversed/revoked entitlements are excluded. '
                         'Fulfillment is a maintainer mark; no reward deadline exists.')
            empty=next(m for m in p['delivery'] if m['key']=='published_milestones')['sample_size']==0
            if empty and claim.kind!='reward_history':
                parts.append('Insufficient history for a meaningful delivery assessment, not zero trust.')
                status='insufficient_evidence'
            if claim.kind=='reward_history' and next(m for m in p['rewards'] if m['key']=='fulfilled')['sample_size']==0:
                parts.append('Insufficient history of eligible reward entitlements.'); status='insufficient_evidence'
            if claim.kind=='owner_comparison':
                if not road: raise ValueError('Current roadmap citation required')
                parts.append('Current project page counts: '+json.dumps(road[0].value['counts'],sort_keys=True)+'. '
                             'The owner aggregate includes this project. It is not an independent previous-outcome comparison; publication and ownership history are unavailable.')
        else:
            r=road[0].value
            parts=[f"Roadmap page scope: offset {r['offset']}, {len(r['items'])} of {r['total']} commitments; "
                   f"evaluated at {r['evaluated_at']}. Current-state counts in this page: {json.dumps(r['counts'],sort_keys=True)}."]
            selected=r['items']
            if claim.kind=='overdue':selected=[i for i in selected if i['analysis']['days_overdue_current']>0]
            if claim.kind=='on_time':selected=[i for i in selected if i['delivery']['timing']=='on_time']
            if claim.kind in ('deadlines','roadmap_changes','overdue','on_time','schedule_explanation','progress','missing_delivery_evidence'):
                parts.append('Commitment facts: '+json.dumps([dict(id=i['commitment']['id'],title=i['commitment']['title'],
                    status=i['delivery']['status'],original_deadline=i['delivery']['original_deadline'],current_deadline=i['delivery']['current_deadline'],
                    asserted_delivery_date=i['delivery']['actual_completion_date'],timing=i['delivery']['timing'],
                    reopened=i['delivery']['reopened_after_delivery'],**i['analysis']) for i in selected],sort_keys=True)+'.')
                if claim.kind=='roadmap_changes':
                    parts.append('Public immutable history previews (not exhaustive): '+json.dumps([
                        dict(milestone_id=i['commitment']['id'],events=[{k:h[k] for k in ('id','version','action','previous_status','new_status','created_at','before','after')} for h in i['history']]) for i in selected])+'.')
            if claim.kind in ('linked_evidence','delivery_support','missing_delivery_evidence'):
                parts.append('Current public linked evidence: '+json.dumps([dict(milestone_id=i['commitment']['id'],
                    status=i['delivery']['status'],links=i['commitment']['evidence']) for i in selected],sort_keys=True)+'. '
                    'Links may support investigation; they do not establish fulfillment of the deliverable or independent review. Stale, missing and unavailable links remain uncertain.')
                if claim.kind in ('delivery_support','missing_delivery_evidence'):status='insufficient_evidence'
            if claim.kind in ('funding_schedule','spending_trend','after_funding'):
                if not finance:raise ValueError('Financial citation required')
                f=finance[0]
                result=render_financial(FinancialPlan(financial_claims=[FinancialClaim(kind='funding_reconciliation',references=[f.citation.reference])]),[f])
                parts.append(result.answer)
                parts.append('Overdue commitment IDs in this page: '+json.dumps([i['commitment']['id'] for i in selected if i['analysis']['days_overdue_current']>0])+'. '
                             'Financial comparisons and development assertions are separate; correlation does not establish causation.')
                if claim.kind!='funding_schedule':
                    parts.append('Insufficient evidence for an expenditure trend or development-after-funding chronology: immutable financial time windows and per-capture funding dates are not exposed by these aggregate tools.')
                    status='insufficient_evidence'
            if not selected or any(not i['analysis']['original_deadline_available'] for i in selected):
                status='insufficient_evidence'
                parts.append('Insufficient evidence: no matching commitments or an original immutable deadline is unavailable; original-deadline timing cannot be inferred.')
            parts.append('Counts and lists cover only this page. Current statuses are evaluated at a UTC date; a supplied earlier timestamp does not replay historical state. '
                         'Deadline revisions never erase the original missed commitment. History previews are bounded to 50 events per milestone.')
        paragraphs.append(' '.join(parts)+' '+' '.join('['+e.citation.reference+']' for e in sources))
        statuses.append(status)
        for e in sources:
            used[e.citation.reference]=e; notes.extend(e.limitations)
    answer='\n'.join(paragraphs)+'\n'+NOTICE
    if len(answer)>max_chars:raise ValueError('Development answer exceeds budget')
    notes.extend(f'{e.source_id}: freshness {e.freshness}, last update {e.last_updated_at}, retrieved {e.observed_at}.' for e in used.values())
    return AgentAnswer(answer=answer,citations=[e.citation for e in used.values()],evidence_used=list(used.values()),
        limitations=list(dict.fromkeys(notes)),confidence='limited_evidence',
        answer_status='insufficient_evidence' if 'insufficient_evidence' in statuses else 'answered')


def deterministic_development(tools, question, kind):
    kind='maintainer_history' if kind=='owner_history' else kind
    p=tools.project(question.project_id)
    sources=[]
    if kind in ('maintainer_history','reward_history','owner_comparison'):
        sources.append(tools.get_maintainer_history(p.owner_id))
    if kind in ('github_activity','activity_trend'):
        sources.append(tools.get_github_activity(p.id))
    elif kind not in ('maintainer_history','reward_history'):
        sources.append(tools.get_project_roadmap(p.id))
    if kind in ('funding_schedule','spending_trend','after_funding'):
        sources.append(tools.get_project_finances(p.id))
    return render_development(DevelopmentPlan(development_claims=[DevelopmentClaim(kind=kind,references=[e.citation.reference for e in sources])]),sources)
