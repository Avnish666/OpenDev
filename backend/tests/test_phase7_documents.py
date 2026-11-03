"""Native PDF adapter and actual kernel resource-limit regressions."""
import json
import signal
import struct
import subprocess
import sys
import zlib
from pathlib import Path
import pytest
from fastapi import HTTPException
from pypdf import PdfWriter
from app.services import documents
from app.services.decoder_limits import decoder_slot
from app.services.receipt.provider import LocalProvider,ExtractionError
from pdf_fixtures import text_pdf


@pytest.mark.parametrize('rotation',[0,90,180,270])
def test_pdfium_preserves_text_and_displayed_point_coordinates(tmp_path,rotation):
    path=tmp_path/'receipt.pdf'
    path.write_bytes(text_pdf('Vendor: Acme Hosting\nCurrency: USD\nGrand Total: USD 12.34',rotation=rotation))
    result=LocalProvider().extract(path,'application/pdf')
    assert result.total_cents.value==1234 and result.extraction_method=='pdf_text'
    evidence=result.total_cents.evidence[0]
    width,height=(842,595) if rotation in (90,270) else (595,842)
    x0,y0,x1,y1=evidence.bbox
    assert evidence.coordinates=='pdf_points' and evidence.page==1
    assert 0<=x0<x1<=width and 0<=y0<y1<=height
    assert list(tmp_path.iterdir())==[path]


def test_page_limit_malformed_and_extreme_dimensions_fail_closed(tmp_path):
    path=tmp_path/'receipt.pdf'
    for content,code in [(text_pdf('Synthetic text',pages=6),'PAGE_LIMIT'),(b'%PDF-1.7 corrupt\n%%EOF','INVALID_DOCUMENT')]:
        path.write_bytes(content)
        with pytest.raises(ExtractionError) as error:LocalProvider().extract(path,'application/pdf')
        assert error.value.code==code
    writer=PdfWriter();writer.add_blank_page(width=1e9,height=100);writer.write(path)
    with pytest.raises(ExtractionError):LocalProvider().extract(path,'application/pdf')
    assert list(tmp_path.iterdir())==[path]


def test_shared_admission_prevents_validation_plus_extraction(tmp_path):
    decoder_slot.acquire()
    try:
        with pytest.raises(ExtractionError) as error:LocalProvider().extract(tmp_path/'unused','application/pdf')
        assert error.value.code=='PROCESSING_BUSY'
        with pytest.raises(HTTPException) as error:documents.validate(tmp_path/'unused')
        assert error.value.status_code==429
    finally:decoder_slot.release()


def test_png_decompression_bomb_rejected_without_allocation(tmp_path):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    body=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',200000,200000,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'))+chunk(b'IEND',b'')
    path=tmp_path/'bomb.png';path.write_bytes(body)
    with pytest.raises(HTTPException) as error:documents.validate(path)
    assert error.value.status_code==415


def test_kernel_memory_file_descriptor_core_and_privilege_limits(tmp_path):
    code='''from app.services.decoder_limits import worker_limits
import resource,json
worker_limits(64,2,4096)
try:
 bytearray(128*1024*1024)
 raise AssertionError('memory bound absent')
except MemoryError:pass
assert resource.getrlimit(resource.RLIMIT_CORE)==(0,0)
assert resource.getrlimit(resource.RLIMIT_NOFILE)==(64,64)
assert 'NoNewPrivs:\\t1' in open('/proc/self/status').read()
print('bounded')
'''
    r=subprocess.run([sys.executable,'-c',code],env={},capture_output=True,text=True,timeout=5)
    assert r.returncode==0,r.stderr
    assert r.stdout.strip()=='bounded'
    target=tmp_path/'output'
    code="from app.services.decoder_limits import worker_limits; worker_limits(64,2,4096); open(__import__('sys').argv[1],'wb').write(b'x'*8192)"
    r=subprocess.run([sys.executable,'-c',code,str(target)],env={},capture_output=True,timeout=5)
    # A regular-file write may be short instead of terminating the process.
    assert 0 < target.stat().st_size<=4096


def test_kernel_cpu_limit_kills_worker():
    code='from app.services.decoder_limits import worker_limits\nworker_limits(64,1,4096)\nwhile True:pass'
    r=subprocess.run([sys.executable,'-c',code],env={},capture_output=True,timeout=5)
    assert r.returncode in (-signal.SIGKILL,-signal.SIGXCPU)
