"""Explicit baseline intents; no semantic guessing, model execution or source instructions."""
from fastapi import HTTPException
from app.agent.contracts import AgentAnswer

INTENTS={
 'funding':('How much funding has the project received?',),
 'spending':('How much has been reported as spent?',),
 'categories':('What is the reported spending by category?',),
 'overdue':('Which milestones are overdue?',),
 'delivered':('What has been asserted delivered?',),
 'github_sync':('When was GitHub last synchronized?',),
 'maintainer_history':("What is the maintainer's recorded delivery history?",),
 'reward_fulfillment':('What is the reward fulfillment history?',),
}


def intent_for(question):
    normalized=' '.join(question.lower().strip().rstrip('?').split())
    for intent,phrases in INTENTS.items():
        if normalized==intent or any(normalized==p.lower().rstrip('?') for p in phrases):return intent
    return None


def answer(tools,question):
    p=tools.project(question.project_id)  # Visibility checked even for unsupported questions.
    intent=intent_for(question.question)
    if not intent:return AgentAnswer(answer='Unsupported question. Use one of: '+', '.join(INTENTS),limitations=['Only explicit baseline intents are supported; no LLM reasoning.'],confidence='not_applicable',answer_status='unsupported_question')
    try:
        if intent in ('funding','spending','categories'):
            e=tools.get_project_finances(p.id);s=e.value['financial_summary']
            if intent=='funding':text=f"Net recorded Sandbox funding: {s['net_recorded_funding_cents']} {s['currency']} minor units. This is not an available bank balance."
            elif intent=='spending':text=f"Published reported spending: {s['published_reported_spending_cents']} {s['currency']} minor units. Reports do not verify vendor payment."
            else:text='Reported spending by category (integer minor units): '+str(s['budget_variance'])
        elif intent in ('overdue','delivered'):
            e=tools.get_project_roadmap(p.id);rows=e.value['items']
            selected=[r for r in rows if (r['commitment']['status']=='delivered' if intent=='delivered' else r['commitment']['status'] not in ('delivered','cancelled') and r['commitment']['planned_end_date']<tools.now.date().isoformat())]
            text=('Maintainer-asserted delivery' if intent=='delivered' else 'Overdue unfinished commitments')+': '+str([dict(id=r['commitment']['id'],title=r['commitment']['title']) for r in selected])+'. First page only; not independent certification.'
            if not selected:
                return result(e,'No matching commitments in the retrieved page.','insufficient_evidence')
        elif intent=='github_sync':
            e=tools.get_github_activity(p.id);timestamp=e.value['activity']['sync']['last_successful_sync_at']
            if not timestamp:return result(e,'No successful GitHub synchronization recorded.','unavailable_source')
            text='Last successful GitHub synchronization: '+timestamp+'. Bounded observations, not exhaustive coverage.'
        elif intent=='maintainer_history':
            e=tools.get_maintainer_history(p.owner_id)
            if next(m for m in e.value['delivery'] if m['key']=='published_milestones')['sample_size']==0:return result(e,'Insufficient public delivery history.','insufficient_evidence')
            text='Recorded owner delivery history: '+str([{k:m[k] for k in ('key','numerator','denominator','sample_size','state')} for m in e.value['delivery']])+'. Maintainer assertions, not a trust score.'
        else:
            e=tools.get_reward_fulfillment(p.id);text='Recorded project reward fulfillment: '+str(e.value)
        return result(e,text)
    except HTTPException as exc:
        if exc.status_code not in (404,413):raise
        return AgentAnswer(answer='Public source unavailable.',limitations=['Source missing, not publicly accessible, or above bounded retrieval capacity; no inference of misconduct.'],confidence='limited_evidence',answer_status='unavailable_source')


def result(e,text,status='answered'):
    return AgentAnswer(answer=text,citations=[e.citation],evidence_used=[e],limitations=e.limitations,
        confidence='limited_evidence' if status!='answered' or e.freshness!='current_database_snapshot' else 'deterministic_records',answer_status=status)
