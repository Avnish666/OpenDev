"""Full HTTP journey with real cookie auth, real PostgreSQL and local PDF extraction.
Only GitHub, PayPal and private object storage are mocked; no live claims.
"""
import json
from pathlib import Path
from uuid import uuid4
import httpx
import pymupdf
from sqlalchemy import select, func
from app.main import app
from app.core.auth import get_current_user, get_optional_user
from app.models.funding import Contribution, Entitlement
from app.models.session import UserSession
from app.routers import auth, projects
from app.services import project_management, funding, documents
from app.services.paypal import PayPal
from app.services.receipt import pipeline
from test_accountability import ac
from test_funding import headers


def ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def login(client, monkeypatch, user):
    async def token(code):
        assert code == 'synthetic-code'
        return 'synthetic-private-github-token'
    async def profile(token):
        return {'id': user.github_id, 'login': user.username, 'avatar_url': None}
    monkeypatch.setattr(auth, 'exchange_code_for_token', token)
    monkeypatch.setattr(auth, 'get_github_user', profile)
    client.get('/api/auth/github/login', follow_redirects=False)
    state = client.cookies.get(auth.STATE_COOKIE)
    assert client.get('/api/auth/github/callback?code=synthetic-code&state=wrong', follow_redirects=False).status_code == 400
    result = client.get('/api/auth/github/callback', params={'code':'synthetic-code','state':state}, follow_redirects=False)
    assert result.status_code == 303
    assert 'httponly' in result.headers['set-cookie'].lower()
    assert client.get('/api/auth/me').json()['id'] == user.id


def test_full_cookie_authenticated_release_journey(ac, monkeypatch):
    app.dependency_overrides.pop(get_current_user)
    app.dependency_overrides.pop(get_optional_user)
    client = ac.client
    login(client, monkeypatch, ac.users[0])
    session = ac.db.scalar(select(UserSession))
    assert session.token_hash != client.cookies.get('app_session')
    async def repo(repo_name, github_user_id):
        assert repo_name == 'owner/release' and github_user_id == ac.users[0].github_id
        return {'id':9000,'url':'https://github.com/owner/release'}
    monkeypatch.setattr(projects, 'verify_repository_ownership', repo)
    monkeypatch.setattr(project_management, 'verify_repository_ownership', repo)
    project = ok(client.post('/api/projects', json={'github_repo':'owner/release','title':'Release journey',
        'description':'Synthetic project for release verification','funding_goal_cents':10000,
        'budget':[{'category':'Hosting','allocated_cents':10000}]}),201)
    pid = project['id']
    tier = ok(client.post(f'/api/projects/{pid}/rewards', json={'name':'Beta','description':'Beta access',
        'price_cents':500,'benefits':[{'title':'Beta access'}]}),201)
    ok(client.post(f'/api/projects/{pid}/publish'))
    ok(client.post('/api/auth/logout'))
    assert client.get('/api/auth/me').status_code == 401
    login(client, monkeypatch, ac.users[3])
    for name in ['PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','PAYPAL_WEBHOOK_ID','PAYPAL_MERCHANT_ID']:
        monkeypatch.setenv(name,'synthetic-sandbox')
    captured = [False]
    requests = []
    def paypal(request):
        requests.append(request)
        assert request.url.host == 'api-m.sandbox.paypal.com'
        if request.url.path == '/v1/oauth2/token':
            return httpx.Response(200,json={'access_token':'synthetic-paypal-token'})
        if request.url.path.endswith('verify-webhook-signature'):
            body = json.loads(request.content)
            assert body['webhook_id'] == 'synthetic-sandbox'
            return httpx.Response(200,json={'verification_status':'SUCCESS'})
        c = ac.db.scalar(select(Contribution).where(Contribution.project_id == pid))
        unit = {'custom_id':c.id,'payee':{'merchant_id':'synthetic-sandbox'},'amount':{'currency_code':'USD','value':'5.00'},
                'payments':{'captures':[{'id':'CAP-RELEASE'}] if captured[0] else []}}
        if request.url.path == '/v2/checkout/orders' and request.method == 'POST':
            assert json.loads(request.content)['purchase_units'][0]['amount']['value'] == '5.00'
            return httpx.Response(201,json={'id':'ORDER-RELEASE','links':[{'rel':'payer-action','href':'https://www.sandbox.paypal.com/checkoutnow?token=ORDER-RELEASE'}]})
        if request.url.path.endswith('/capture'):
            captured[0] = True; unit['payments']['captures'] = [{'id':'CAP-RELEASE'}]
        if request.url.path == '/v2/payments/captures/CAP-RELEASE':
            return httpx.Response(200,json={'id':'CAP-RELEASE','status':'COMPLETED','amount':unit['amount']})
        return httpx.Response(200,json={'id':'ORDER-RELEASE','intent':'CAPTURE','status':'COMPLETED' if captured[0] else 'APPROVED','purchase_units':[unit]})
    monkeypatch.setattr(funding,'paypal',PayPal(httpx.MockTransport(paypal)))
    contribution = ok(client.post('/api/funding/orders',json={'tier_id':tier['id'],'checkout_key':str(uuid4())}))
    cid = contribution['id']
    assert ok(client.post(f'/api/funding/{cid}/capture'))['status'] == 'completed'
    event = {'id':'RELEASE-EVENT','event_type':'PAYMENT.CAPTURE.COMPLETED',
             'resource':{'id':'CAP-RELEASE','supplementary_data':{'related_ids':{'order_id':'ORDER-RELEASE'}}}}
    assert ok(client.post('/api/paypal/webhook',json=event,headers=headers))['status'] == 'processed'
    assert ok(client.post('/api/paypal/webhook',json=event,headers=headers))['status'] == 'duplicate'
    assert ac.db.scalar(select(func.count()).select_from(Entitlement)) == 1
    assert ok(client.get('/api/me/contributions'))[0]['entitlement']['status'] == 'granted'
    ok(client.post('/api/auth/logout')); login(client,monkeypatch,ac.users[0])
    expense = ok(client.post(f'/api/projects/{pid}/expenses',json={'category':'Hosting','amount_cents':1000,
        'currency':'USD','vendor':'Acme Hosting','description':'Synthetic reported hosting','expense_date':'2026-10-31'}),201)
    eid = expense['id']
    objects = {}
    def upload(key, path, mime): objects[key] = Path(path).read_bytes()
    def download(storage, key, target, max_bytes):
        assert len(objects[key]) <= max_bytes
        Path(target).write_bytes(objects[key]); return len(objects[key])
    monkeypatch.setattr(documents.storage,'upload',upload)
    monkeypatch.setattr(pipeline,'download_private',download)
    with pymupdf.open() as pdf:
        page = pdf.new_page(); page.insert_text((60,60),'Vendor: Acme Hosting\nDate: 2026-10-31\nCurrency: USD\nGrand Total: USD 12.34')
        content = pdf.tobytes()
    doc = ok(client.post(f'/api/expenses/{eid}/documents',content=content,
        headers={'X-Filename':'private.pdf','Content-Type':'application/pdf'}),201)
    extraction = ok(client.post(f"/api/documents/{doc['id']}/extract",json={}))
    assert extraction['extraction_status'] == 'completed'
    findings = ok(client.get(f'/api/expenses/{eid}/verification'))['findings']
    mismatch = next(f for f in findings if f['finding_code'] == 'AMOUNT_MISMATCH')
    ok(client.post('/api/extraction-findings/'+mismatch['id']+'/review',json={
        'request_key':str(uuid4()),'action':'mark_reviewed','reason':'Private explanation for synthetic mismatch.'}))
    assert ok(client.get(f'/api/expenses/{eid}/review-history'))[0]['outcome'] == 'unresolved'
    ok(client.post(f'/api/expenses/{eid}/publish'))
    # Distinct, valid redacted PDF; publication never exposes the original.
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((60,60),'Approved redacted supporting evidence')
        redaction = pdf.tobytes()
    redacted = ok(client.post(f"/api/expenses/{eid}/documents?redacted_from_id={doc['id']}",content=redaction,
        headers={'X-Filename':'redacted.pdf','Content-Type':'application/pdf'}),201)
    ok(client.post(f"/api/documents/{redacted['id']}/publish",json={'redaction_reviewed':True}))
    private = ok(client.get(f'/api/projects/{pid}/accountability'))
    ok(client.post('/api/auth/logout')); client.cookies.clear()
    public = ok(client.get(f'/api/projects/{pid}/transparency'))
    assert public['financial_summary']['net_recorded_funding_cents'] == private['net_recorded_funding_cents'] == 500
    assert public['financial_summary']['published_reported_spending_cents'] == 1000
    ledger = ok(client.get(f'/api/projects/{pid}/ledger'))
    assert ledger['total'] == 1 and ledger['items'][0]['evidence'][0]['id'] == redacted['id']
    assert doc['id'] not in json.dumps(ledger) and 'Private explanation' not in json.dumps(public)
    assert client.get(f"/api/documents/{doc['id']}/download").status_code == 404
    assert client.get(f"/api/documents/{doc['id']}/extraction").status_code == 401


def test_private_profile_and_errors_not_cacheable(ac):
    for path in ['/api/auth/me','/api/me/contributions','/api/expenses/99999999']:
        response = ac.client.get(path)
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['referrer-policy'] == 'no-referrer'
        assert response.headers['x-content-type-options'] == 'nosniff'


def test_phase1_records_survive_forward_migration_chain(ac):
    import os
    import subprocess
    import sys
    from sqlalchemy.engine import make_url
    from sqlalchemy import create_engine, text
    schema = 'upgrade_preservation_' + uuid4().hex
    with ac.engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA {schema}'))
    url = make_url(os.environ['TEST_DATABASE_URL']).update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    env = dict(os.environ,DATABASE_URL=url,APP_ENV='testing')
    def upgrade(revision):
        subprocess.run([str(Path(sys.executable).with_name('alembic')),'upgrade',revision],cwd=Path(__file__).parents[1],env=env,check=True,capture_output=True)
    upgrade('ec107b8b4763')
    engine = create_engine(url)
    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO users (id,github_id,username,created_at) VALUES (900,9900,'existing',now())"))
            conn.execute(text("INSERT INTO projects (id,owner_id,github_repo_id,github_repo_url,title,description,funding_goal_cents,currency,status) VALUES (900,900,9900,'https://github.com/existing/repo','Existing','Pre-upgrade project',10000,'USD','draft')"))
            conn.execute(text("INSERT INTO budget_allocations (project_id,category,allocated_cents) VALUES (900,'Development',10000)"))
        upgrade('head')
        with engine.connect() as conn:
            assert conn.scalar(text('SELECT funding_goal_cents FROM projects WHERE id=900')) == 10000
            assert conn.scalar(text('SELECT sum(allocated_cents) FROM budget_allocations WHERE project_id=900')) == 10000
            assert conn.scalar(text('SELECT username FROM users WHERE id=900')) == 'existing'
            assert conn.scalar(text('SELECT version_num FROM alembic_version')) == 'a684112224e6'
    finally:
        engine.dispose()
