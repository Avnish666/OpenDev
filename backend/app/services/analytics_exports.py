"""Bounded public CSV projections. No accounting arithmetic or source writes."""
import csv,io,json,threading,time,unicodedata
from collections import OrderedDict
from datetime import date,datetime
from fastapi import HTTPException
from sqlalchemy import select,event
from contextlib import contextmanager
from app.models.expense import Expense
from app.services import analytics,credibility,analytics_development
MAX_ROWS=1000
MAX_BYTES=2*1024*1024
_slots=threading.BoundedSemaphore(2)
_lock=threading.Lock()
_peers=OrderedDict()

def admit(peer):
    now=time.monotonic()
    with _lock:
        while _peers and now-next(iter(_peers.values()))[0]>60:_peers.popitem(last=False)
        start,count=_peers.get(peer,(now,0))
        if count>=10:raise HTTPException(429,'Export rate limit; retry later',headers={'Retry-After':'60'})
        if len(_peers)>=2048 and peer not in _peers:raise HTTPException(429,'Exports busy',headers={'Retry-After':'60'})
        _peers[peer]=(start,count+1)
    if not _slots.acquire(blocking=False):raise HTTPException(429,'Exports busy',headers={'Retry-After':'5'})

@contextmanager
def budget(reader):
    deadline=time.monotonic()+10
    connection=reader.connection()
    def guard(conn,cursor,statement,parameters,context,executemany):
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('Export deadline')
        cursor.execute("SELECT set_config('statement_timeout', %s, true)",(str(max(1,int(min(remaining,5)*1000))),))
    event.listen(connection,'before_cursor_execute',guard)
    try:yield deadline
    finally:event.remove(connection,'before_cursor_execute',guard)

def cell(value):
    if value is None:return ''
    if isinstance(value,(date,datetime)):return value.isoformat()
    if isinstance(value,(int,float,bool)):return str(value)
    text=str(value)
    probe=''.join(c for c in unicodedata.normalize('NFKC',text) if not c.isspace() and unicodedata.category(c) not in ('Cc','Cf'))
    if (probe and probe[0] in '=+-@') or (text and (ord(text[0])<32 or unicodedata.category(text[0])=='Cf')):return "'"+text
    return text

def encode(rows,columns,deadline=None):
    if len(rows)>MAX_ROWS:raise HTTPException(413,'Export exceeds 1000 rows; narrow filters')
    out=io.StringIO(newline='');writer=csv.writer(out,lineterminator='\r\n');writer.writerow(columns)
    for row in rows:
        if deadline and time.monotonic()>deadline:raise TimeoutError('Export deadline')
        writer.writerow([cell(row.get(k)) for k in columns])
        if out.tell()>MAX_BYTES:raise HTTPException(413,'Export exceeds byte capacity; narrow filters')
    result=('\ufeff'+out.getvalue()).encode('utf-8')
    if len(result)>MAX_BYTES:raise HTTPException(413,'Export exceeds byte capacity; narrow filters')
    return result

def generate(db,pid,kind,filters,dimensions,deadline=None):
    # Services retain their own preflight bounds and same readonly transaction.
    data=analytics.overview(db,pid,1,0,filters,0,dimensions,expense_limit=MAX_ROWS+1 if kind=='expenses' else 1,milestone_limit=MAX_ROWS+1 if kind=='roadmap' else 1)
    if kind=='expenses':
        if data.expense_total>MAX_ROWS:raise HTTPException(413,'Export exceeds 1000 rows; narrow filters')
        details={e.id:e for e in db.scalars(select(Expense).where(Expense.project_id==pid,Expense.publication_status=='published',Expense.id.in_([r.id for r in data.expenses])))}
        rows=[dict(**r.model_dump(),vendor=details[r.id].vendor,description=details[r.id].description) for r in data.expenses]
        cols=['id','category','vendor','description','expense_date','amount_cents','approved_public_support','public_category_finding_count']
    elif kind=='budget':
        rows=[r.model_dump() for r in data.budget];cols=['category','allocated_cents','reported_spending_cents','remaining_cents','overspend_cents']
    elif kind=='financial':
        f=data.financial
        keys=['gross_completed_funding_cents','refund_excluded_cents','reversal_excluded_cents','net_recorded_funding_cents','published_reported_spending_cents','funding_minus_reported_expenditure_cents','expenses_with_documents_cents','expenses_without_documents_cents','published_expense_count','expenses_with_documents_count','expenses_without_documents_count']
        rows=[{**{k:getattr(f,k) for k in keys},'funding_goal_cents':data.funding_goal_cents,'public_unresolved_finding_count':data.public_unresolved_finding_count,'filtered_expense_total':data.expense_total,'filtered_expense_spending_cents':data.expense_analysis.reported_spending_cents}];cols=list(rows[0])
    elif kind in ('roadmap','maintainer-delivery'):
        if kind=='roadmap':
            if data.development.total>MAX_ROWS:raise HTTPException(413,'Export exceeds 1000 rows; narrow filters')
            rows=[r.model_dump() for r in data.development.milestones]
        else:
            history=credibility.delivery_history(db,data.maintainer.owner_id,10001,0,data.as_of)
            rows=analytics_development.filter_milestones(history['items'],dimensions)
        cols=['project_id','milestone_id','title','status','original_deadline','current_deadline','actual_completion_date','timing','revision_count','deadline_revision_count','reopened_after_delivery']
    else:
        g=data.development.github
        rows=[dict(metric=k,count=v) for k,v in sorted((g.counts or {}).items())]
        rows.append(dict(metric='sampled_commits' if g.available else 'unavailable',count=len(g.recent_commits) if g.available else None))
        cols=['metric','count','last_successful_sync_at','snapshot_stale']
        for row in rows:row.update(last_successful_sync_at=g.sync.last_successful_sync_at,snapshot_stale=g.sync.stale)
    scope='owner_active_projects' if kind=='maintainer-delivery' else 'project_full_totals' if kind in ('financial','budget') else 'complete_filtered_records' if kind in ('expenses','roadmap') else 'retained_snapshot_summary'
    metadata=dict(exported_record_count=len(rows),request_project_id=pid,currency=data.currency,as_of=data.as_of,scope=scope,filters=json.dumps({**filters.model_dump(mode='json'),**dimensions.model_dump(mode='json')},sort_keys=True),limitations=' | '.join(data.limitations))
    # Even an empty dataset has one explicit metadata row, with blank record fields.
    rows=rows or [{}]
    for index,row in enumerate(rows):row.update({**metadata,'filters':metadata['filters'] if index==0 else '', 'limitations':metadata['limitations'] if index==0 else ''})
    return encode(rows,list(dict.fromkeys(['request_project_id','exported_record_count','currency','as_of','scope',*cols,'filters','limitations'])),deadline)
