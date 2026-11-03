"""Local image smoke only: synthetic config, no database/provider connections."""
import json
import subprocess
import time
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--image',default='opendev-release-test')
args=parser.parse_args()

base = ['docker','--host=unix:///var/run/docker.sock']
started = time.monotonic()
cid = subprocess.check_output(base + ['run','-d','--memory=512m','--cpus=1','--pids-limit=32',
    '--read-only','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=64m','--cap-drop=ALL',
    '--security-opt','no-new-privileges','--network=none','-e','APP_ENV=production',
    '-e','DATABASE_URL=postgresql+psycopg://test:test@localhost/opendev_test_smoke',
    '-e','FRONTEND_URL=https://frontend.invalid','-e','PORT=10031',args.image],text=True).strip()
try:
    for attempt in range(40):
        result = subprocess.run(base + ['exec',cid,'python','-c',
            "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:10031/api/health',timeout=1).read().decode())"],capture_output=True,text=True)
        if result.returncode == 0: break
        time.sleep(.25)
    if result.returncode:
        print(subprocess.check_output(base + ['logs',cid],stderr=subprocess.STDOUT,text=True))
        print(result.stderr)
        raise RuntimeError('Container health check failed')
    assert json.loads(result.stdout) == {'status':'ok'}
    print(json.dumps({'health':json.loads(result.stdout),'startup_seconds':round(time.monotonic()-started,2)}), flush=True)
    code = '''import json, os, tempfile, pathlib, resource, time
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from PIL import Image, ImageDraw
from app.services.receipt.provider import LocalProvider
started=time.monotonic()
with tempfile.TemporaryDirectory() as folder:
 p=pathlib.Path(folder)/'receipt.pdf'
 writer=PdfWriter();page=writer.add_blank_page(width=595,height=842)
 font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
 page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
 stream=DecodedStreamObject();stream.set_data(b'BT /F1 14 Tf 40 780 Td (Vendor: Synthetic Hosting) Tj 0 -20 Td (Currency: USD) Tj 0 -20 Td (Grand Total: USD 12.34) Tj ET')
 page[NameObject('/Contents')]=writer._add_object(stream);writer.write(str(p))
 pdf_result=LocalProvider().extract(p,'application/pdf')
 image=Image.new('RGB',(1200,400),'white');ImageDraw.Draw(image).text((30,30),'Vendor: Synthetic Hosting\\nGrand Total: USD 12.34',fill='black',font_size=40)
 p=pathlib.Path(folder)/'receipt.png';image.save(p)
 image_result=LocalProvider().extract(p,'image/png')
 assert os.getuid()==10001 and pdf_result.total_cents.value==1234
 assert image_result.extraction_method=='tesseract'
 assert image_result.total_cents.value==1234
 p=pathlib.Path(folder)/'scan.pdf';image.save(p,format='PDF')
 scan_result=LocalProvider().extract(p,'application/pdf')
 assert scan_result.total_cents.value==1234 and scan_result.extraction_method=='tesseract'
 from importlib.metadata import distribution,PackageNotFoundError
 try:distribution('PyMuPDF');raise AssertionError('Replaced engine remains installed')
 except PackageNotFoundError:pass
 assert pathlib.Path('/app/app/main.py').stat().st_uid==0
 print(json.dumps({'uid':os.getuid(),'pdf_total_cents':pdf_result.total_cents.value,'ocr_method':image_result.extraction_method,'processing_seconds':round(time.monotonic()-started,2),'child_peak_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}))
'''
    subprocess.run(base + ['exec',cid,'python','-c',code],check=True)
    print(subprocess.check_output(base + ['stats','--no-stream','--format','{{.MemUsage}}',cid],text=True).strip())
finally:
    subprocess.run(base + ['stop','-t','3',cid],stdout=subprocess.DEVNULL,check=True)
    subprocess.run(base + ['rm',cid],stdout=subprocess.DEVNULL,check=True)
