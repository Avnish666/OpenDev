import csv,io,json,os,time,tracemalloc
from pathlib import Path
import pytest
from sqlalchemy import event
from app.services import analytics_exports as service
from test_accountability import ac,contribution,receipt
from test_credibility import milestone
from test_transparency import extra_expense

@pytest.fixture(autouse=True)
def quota():
    service._peers.clear()
    yield
    service._peers.clear()
def export(ac,kind='expenses',**params):return ac.client.get(f'/api/projects/{ac.p.id}/analytics/export/{kind}',params=params)
def rows(response):
    assert response.status_code==200,response.text
    assert response.headers['content-type'].startswith('text/csv')
    assert response.headers['cache-control']=='no-store'
    return list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))

@pytest.mark.parametrize('kind',['expenses','financial','budget','roadmap','github','maintainer-delivery'])
def test_public_exports(ac,kind):
    contribution(ac);milestone(ac,completed='2026-11-01',status='delivered')
    ac.identity[0]=None;data=rows(export(ac,kind))
    assert data[0]['as_of'] and data[0]['request_project_id']==str(ac.p.id)
    assert data[0]['currency']=='USD' and data[0]['limitations']

def test_complete_filtered_expenses_and_fields(ac):
    for _ in range(54):extra_expense(ac,amount_cents=123)
    extra_expense(ac,category='Other',amount_cents=100)
    data=rows(export(ac,category='development',limit=1,offset=999))
    assert len(data)==55 and data[0]['expense_date']=='2026-10-31'
    assert sum(int(r['amount_cents']) for r in data)==1000+54*123
    assert {'vendor','description','approved_public_support'}<=data[0].keys()

def test_financial_and_budget_parity(ac):
    contribution(ac,'completed',10000);contribution(ac,'refunded',2000)
    d=rows(export(ac,'financial',category='no-match'))[0]
    assert d['net_recorded_funding_cents']=='10000' and d['filtered_expense_total']=='0'
    assert d['published_reported_spending_cents']=='1000'
    b=rows(export(ac,'budget'))[0];assert b['remaining_cents']=='9000'

def test_roadmap_filters_and_owner_scope(ac):
    milestone(ac,status='planned');milestone(ac,completed='2026-11-01',status='delivered')
    for kind in ['roadmap','maintainer-delivery']:
        d=rows(export(ac,kind,milestone_status='delivered'))
        assert len(d)==1 and d[0]['timing']=='late' and d[0]['original_deadline']=='2026-10-31'

@pytest.mark.parametrize('text',['=SUM(A1:A3)','+cmd','-cmd','@SUM(1)',' \t=1','\r\n@cmd','\u200b=1','＝1'])
def test_formula_cells_after_csv_parsing(text):
    value=service.encode([{'text':text}],['text']).decode('utf-8-sig')
    parsed=list(csv.DictReader(io.StringIO(value)))[0]['text']
    assert parsed=="'"+text

def test_quotes_unicode_newlines_numeric_minor_units():
    source={'text':'Café, "quoted"\nnext line','amount':-123}
    assert list(csv.DictReader(io.StringIO(service.encode([source],list(source)).decode('utf-8-sig'))))[0]=={'text':source['text'],'amount':'-123'}

@pytest.mark.parametrize('params',[{'date_from':'bad'},{'date_from':'2026-12-01','date_to':'2026-01-01'},{'scope':'private'},{'milestone_status':'secret'}])
def test_invalid_filter(ac,params):assert export(ac,**params).status_code==422

@pytest.mark.parametrize('state',['draft','paused','completed'])
def test_visibility(ac,state):
    ac.p.status=state;ac.db.commit();assert export(ac).status_code==404

def test_privacy_isolation_and_filename(ac):
    original,ocr=receipt(ac);extra_expense(ac,publication_status='draft',description='PRIVATE_DRAFT');extra_expense(ac,project_id=ac.other.id,description='OTHER_PROJECT')
    ac.p.title='bad\r\nInjected: header';ac.db.commit()
    r=export(ac)
    for value in [original.id,ocr.id,original.storage_key,'PRIVATE_DRAFT','OTHER_PROJECT','capture_id','email']:
        assert value not in r.content.decode('utf-8-sig')
    assert r.headers['content-disposition']==f'attachment; filename="opendev-project-{ac.p.id}-expenses.csv"'

def test_caps_rate_and_source_immutability(ac,monkeypatch):
    before=ac.e.amount_cents
    monkeypatch.setattr(service,'MAX_ROWS',0);assert export(ac).status_code==413
    monkeypatch.setattr(service,'MAX_ROWS',1000);monkeypatch.setattr(service,'MAX_BYTES',10);assert export(ac).status_code==413
    monkeypatch.setattr(service,'MAX_BYTES',2*1024*1024)
    service._peers.clear()
    for _ in range(10):assert export(ac).status_code==200
    assert export(ac).status_code==429
    ac.db.refresh(ac.e);assert ac.e.amount_cents==before

def test_export_performance(ac):
    for _ in range(199):extra_expense(ac,amount_cents=100)
    sql=[]
    def capture(*args):sql.append(1)
    event.listen(ac.engine,'before_cursor_execute',capture);tracemalloc.start();start=time.perf_counter()
    try:r=export(ac);elapsed=(time.perf_counter()-start)*1000;_,peak=tracemalloc.get_traced_memory()
    finally:tracemalloc.stop();event.remove(ac.engine,'before_cursor_execute',capture)
    assert len(rows(r))==200
    target=os.getenv('EXPORT_PERFORMANCE_FILE')
    if target:Path(target).write_text(json.dumps(dict(rows=200,elapsed_ms=round(elapsed,3),sql=len(sql),bytes=len(r.content),tracemalloc_peak_bytes=peak),indent=2))

def test_row_boundary_and_deadline():
    assert len(list(csv.DictReader(io.StringIO(service.encode([{'value':1}]*1000,['value']).decode('utf-8-sig')))))==1000
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:service.encode([{'value':1}]*1001,['value'])
    assert exc.value.status_code==413
    with pytest.raises(TimeoutError):service.encode([{'value':1}],['value'],time.monotonic()-1)

def test_internal_page_limits_only_materialize_requested_records(ac,monkeypatch):
    real=service.analytics.overview;calls=[]
    def observed(*args,**kwargs):calls.append(kwargs);return real(*args,**kwargs)
    monkeypatch.setattr(service.analytics,'overview',observed)
    rows(export(ac,'expenses'));assert calls[-1]['expense_limit']==1001 and calls[-1]['milestone_limit']==1
    rows(export(ac,'roadmap'));assert calls[-1]['expense_limit']==1 and calls[-1]['milestone_limit']==1001
