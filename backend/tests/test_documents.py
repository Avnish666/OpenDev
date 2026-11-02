import hashlib
import io
from urllib.parse import quote
from uuid import uuid4

import httpx
import pytest
from PIL import Image
from pypdf import PdfWriter
from sqlalchemy import event, select, func
from sqlalchemy.exc import IntegrityError

from app.core.auth import get_current_user
from app.main import app
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.services import documents
from app.services.storage import Storage
from test_projects import ctx
from test_expenses import expense_ctx, create


def image_bytes(fmt='PNG', color='white'):
    output=io.BytesIO(); Image.new('RGB',(5,5),color).save(output,format=fmt); return output.getvalue()


def pdf_bytes(active=False):
    writer=PdfWriter();writer.add_blank_page(width=100,height=100)
    if active: writer.add_js('app.alert("test")')
    output=io.BytesIO();writer.write(output);return output.getvalue()


@pytest.fixture
def document_ctx(expense_ctx,monkeypatch):
    client,db,p,users,identity=expense_ctx
    expense=create(expense_ctx).json()
    state={'objects':{},'calls':[],'public':False,'upload_status':200,'delete_fail':False}
    for name,value in [('SUPABASE_URL','https://receipt-test.supabase.co'),('SUPABASE_STORAGE_BUCKET','private-evidence'),('SUPABASE_SERVICE_ROLE_KEY','test-storage-secret')]:monkeypatch.setenv(name,value)
    def handle(request):
        state['calls'].append(request)
        assert request.url.host=='receipt-test.supabase.co'
        assert request.headers['authorization']=='Bearer test-storage-secret'
        assert request.headers['apikey']=='test-storage-secret'
        path=request.url.path
        if path=='/storage/v1/bucket/private-evidence':return httpx.Response(200,json={'public':state['public']})
        if '/object/sign/' in path:
            import json
            assert json.loads(request.content)=={'expiresIn':60}
            return httpx.Response(200,json={'signedURL':path.replace('/storage/v1','')+'?token=test-signature'})
        if request.method=='POST':
            assert request.headers['x-upsert']=='false'
            if state['upload_status']!=200:return httpx.Response(state['upload_status'],json={'message':'provider-private-diagnostic'})
            assert path not in state['objects']
            state['objects'][path]=request.read()
            return httpx.Response(200,json={'Key':path})
        if request.method=='DELETE':
            if state['delete_fail']:return httpx.Response(500,json={})
            import json
            for key in json.loads(request.content)['prefixes']:state['objects'].pop('/storage/v1/object/private-evidence/'+key,None)
            return httpx.Response(200,json=[])
        raise AssertionError(path)
    monkeypatch.setattr(documents,'storage',Storage(httpx.MockTransport(handle)))
    return client,db,p,users,identity,expense,state


def upload(context,data=None,filename='receipt.png',source=None,expense_id=None):
    client,db,p,users,identity,expense,state=context
    url=f"/api/expenses/{expense_id or expense['id']}/documents"
    if source:url+='?redacted_from_id='+source
    return client.post(url,content=image_bytes() if data is None else data,headers={'X-Filename':quote(filename),'Content-Type':'application/octet-stream'})


@pytest.mark.parametrize('mime,data,filename',[('image/png',image_bytes(),'receipt.png'),('image/jpeg',image_bytes('JPEG'),'receipt.jpg'),('application/pdf',pdf_bytes(),'invoice.pdf')])
def test_actual_content_and_private_metadata(document_ctx,mime,data,filename):
    client,db,p,users,identity,expense,state=document_ctx
    result=upload(document_ctx,data,filename)
    assert result.status_code==201,result.text
    metadata=result.json();assert metadata['detected_mime_type']==mime
    assert metadata['publication_status']=='private'
    assert 'storage_key' not in metadata and 'sha256_hash' not in metadata
    assert 'test-storage-secret' not in result.text
    doc=db.get(ExpenseDocument,metadata['id'])
    assert doc.sha256_hash==hashlib.sha256(data).hexdigest()
    assert doc.original_filename==filename and doc.uploaded_by==users[0].id
    assert doc.file_size_bytes==len(data)
    assert state['objects']['/storage/v1/object/private-evidence/'+doc.storage_key]==data
    assert db.get(Expense,expense['id']).evidence_status=='unverified'
    assert metadata['duplicate_in_project'] is False


@pytest.mark.parametrize('actor',[0,1])
def test_authorized_upload_and_download(document_ctx,actor):
    client,db,p,users,identity,expense,state=document_ctx;identity[0]=users[actor]
    result=upload(document_ctx);assert result.status_code==201
    signed=client.get(f"/api/documents/{result.json()['id']}/download")
    assert signed.status_code==200 and signed.json()['expires_in']==60
    assert signed.headers['cache-control']=='no-store'
    assert 'download=evidence.png' in signed.json()['url']
    assert len(client.get(f"/api/expenses/{expense['id']}/documents").json())==1


@pytest.mark.parametrize('actor',[2,3])
def test_idor_no_storage_call(document_ctx,actor):
    client,db,p,users,identity,expense,state=document_ctx
    doc=upload(document_ctx).json();client.post(f"/api/expenses/{expense['id']}/publish")
    identity[0]=users[actor];before=len(state['calls'])
    assert upload(document_ctx).status_code==403
    assert client.get(f"/api/documents/{doc['id']}/download").status_code==404
    assert client.get(f"/api/expenses/{expense['id']}/documents").json()==[]
    assert client.post(f"/api/documents/{doc['id']}/publish",json={'redaction_reviewed':True}).status_code==403
    assert len(state['calls'])==before


def test_csrf_and_anonymous_upload(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    for origin in ['', 'https://evil.example']:
        assert client.post(f"/api/expenses/{expense['id']}/documents",content=image_bytes(),headers={'Origin':origin,'X-Filename':'receipt.png'}).status_code==403
    app.dependency_overrides.pop(get_current_user)
    assert upload(document_ctx).status_code==401
    assert not state['calls']


@pytest.mark.parametrize('data',[b'',b'fake png',b'\x89PNG\r\n\x1a\ntruncated',b'%PDF-1.7\nfake\n%%EOF',image_bytes()+b'<script>bad</script>',pdf_bytes(active=True)])
def test_invalid_content(document_ctx,data):
    result=upload(document_ctx,data)
    assert result.status_code in (415,422),result.text
    assert not document_ctx[-1]['objects']
    assert not document_ctx[-1]['calls']


def test_size_and_missing_expense(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    assert upload(document_ctx,b'a'*(documents.MAX_BYTES+1)).status_code==413
    assert upload(document_ctx,expense_id=9223372036854775807).status_code==404
    assert not state['calls']


def test_duplicate_project_and_uuid_objects(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    first=upload(document_ctx).json()
    second=upload(document_ctx).json()
    assert second['duplicate_in_project'] is True
    other_expense=create((client,db,p,users,identity)).json()
    third=upload(document_ctx,expense_id=other_expense['id']).json()
    assert third['duplicate_in_project'] is True
    assert len(state['objects'])==3
    keys=[d.storage_key for d in db.scalars(select(ExpenseDocument))]
    assert len(set(keys))==3 and all(key.startswith('receipts/') for key in keys)
    assert first['id']!=second['id']


def test_reviewed_redaction_and_public_visibility(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    original=upload(document_ctx).json()
    assert client.post(f"/api/documents/{original['id']}/publish",json={'redaction_reviewed':True}).status_code==409
    assert upload(document_ctx,source=original['id']).status_code==422
    redacted=upload(document_ctx,image_bytes(color='black'),source=original['id']).json()
    assert client.post(f"/api/documents/{redacted['id']}/publish",json={'redaction_reviewed':True}).status_code==409
    client.post(f"/api/expenses/{expense['id']}/publish")
    assert client.post(f"/api/documents/{redacted['id']}/publish",json={'redaction_reviewed':False}).status_code==422
    assert client.post(f"/api/documents/{redacted['id']}/publish",json={'redaction_reviewed':True}).status_code==200
    identity[0]=None
    docs=client.get(f"/api/expenses/{expense['id']}/documents").json()
    assert [d['id'] for d in docs]==[redacted['id']]
    assert docs[0]['duplicate_in_project'] is None
    before=len(state['calls'])
    assert client.get(f"/api/documents/{original['id']}/download").status_code==404
    assert len(state['calls'])==before
    assert client.get(f"/api/documents/{redacted['id']}/download").status_code==200
    p.status='draft';db.commit()
    assert client.get(f"/api/documents/{redacted['id']}/download").status_code==404
    p.status='active';db.commit();identity[0]=users[0]
    assert client.post(f"/api/documents/{redacted['id']}/unpublish").status_code==200
    identity[0]=None
    assert client.get(f"/api/documents/{redacted['id']}/download").status_code==404
    assert db.get(Expense,expense['id']).evidence_status=='unverified'


def test_cross_expense_redaction_rejected(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    original=upload(document_ctx).json()
    other=create((client,db,p,users,identity)).json()
    assert upload(document_ctx,image_bytes(color='black'),source=original['id'],expense_id=other['id']).status_code==404


def test_database_failure_cleans_storage(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    def failed_commit(session):raise RuntimeError('simulated failure')
    event.listen(db,'before_commit',failed_commit)
    try:assert upload(document_ctx).status_code==503
    finally:event.remove(db,'before_commit',failed_commit)
    assert not state['objects']
    assert db.scalar(select(func.count()).select_from(ExpenseDocument))==0


def test_cleanup_failure_is_reported(document_ctx,caplog):
    client,db,p,users,identity,expense,state=document_ctx;state['delete_fail']=True
    def failed_commit(session):raise RuntimeError('test')
    event.listen(db,'before_commit',failed_commit)
    try:result=upload(document_ctx)
    finally:event.remove(db,'before_commit',failed_commit)
    assert result.status_code==503 and 'reconciliation' in result.text
    assert 'test-storage-secret' not in caplog.text+result.text
    assert len(state['objects'])==1


def test_public_bucket_fails_closed_and_collision_not_deleted(document_ctx):
    state=document_ctx[-1];state['public']=True
    assert upload(document_ctx).status_code==503
    state['public']=False;state['upload_status']=409
    assert upload(document_ctx).status_code==502
    assert not any(request.method=='DELETE' for request in state['calls'])


def test_stream_size_without_content_length(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    chunks=(b'x'*65536 for _ in range(81))
    response=client.post(f"/api/expenses/{expense['id']}/documents",content=chunks,headers={'X-Filename':'receipt.png'})
    assert response.status_code==413
    assert not state['calls']


def test_approval_csrf_and_strict_attestation(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    original=upload(document_ctx).json()
    redacted=upload(document_ctx,image_bytes(color='black'),source=original['id']).json()
    client.post(f"/api/expenses/{expense['id']}/publish")
    for action in ['publish','unpublish']:
        assert client.post(f"/api/documents/{redacted['id']}/{action}",json={'redaction_reviewed':True},headers={'Origin':'https://evil.example'}).status_code==403
    assert client.post(f"/api/documents/{redacted['id']}/publish",json={'redaction_reviewed':1}).status_code==422
    assert client.post(f"/api/documents/{redacted['id']}/publish",json={'redaction_reviewed':True,'payment_verified':True}).status_code==422
    identity[0]=None
    assert client.get(f"/api/documents/{redacted['id']}/download").status_code==404
    assert client.get(f"/api/expenses/{expense['id']}/documents").json()==[]


def test_unknown_upload_outcome_attempts_cleanup(document_ctx,monkeypatch):
    client,db,p,users,identity,expense,state=document_ctx
    original_storage=documents.storage
    # Preserve the original bound method rather than recursing through the patched object.
    original_upload=original_storage.upload
    def ambiguous(key,path,mime):
        original_upload(key,path,mime)
        from app.services.storage import UploadFailure
        raise UploadFailure(cleanup_safe=True)
    monkeypatch.setattr(original_storage,'upload',ambiguous)
    assert upload(document_ctx).status_code==502
    assert not state['objects']
    assert db.scalar(select(func.count()).select_from(ExpenseDocument))==0


def test_storage_signing_blocked_if_bucket_becomes_public(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    doc=upload(document_ctx).json();state['public']=True
    assert client.get(f"/api/documents/{doc['id']}/download").status_code==503
    assert not any('/object/sign/' in str(request.url) for request in state['calls'])


def test_schema_prevents_publishing_original_and_filename_is_bounded(document_ctx):
    client,db,p,users,identity,expense,state=document_ctx
    assert upload(document_ctx,filename='bad\nname.png').status_code==422
    assert upload(document_ctx,filename='x'*256).status_code==422
    doc=upload(document_ctx,filename='../../receipt.png').json()
    assert doc['original_filename']=='receipt.png'
    stored=db.get(ExpenseDocument,doc['id'])
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            stored.publication_status='published';db.flush()
