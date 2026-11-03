"""Synthetic local-only acceptance files; never uploads or reads real receipts."""
import hashlib
import io
import json
import struct
import zlib
from pathlib import Path
from PIL import Image,ImageDraw
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject

TEXT='Vendor: Synthetic Hosting\nInvoice No: ACCEPT-001\nDate: 2026-11-04\nCurrency: USD\nGrand Total: USD 12.34'


def generate(directory):
    root=Path(directory)
    root.mkdir(mode=0o700,exist_ok=False)  # Never overwrite a user's existing directory.
    writer=PdfWriter();page=writer.add_blank_page(width=595,height=842)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject();stream.set_data(('BT /F1 14 Tf 18 TL 40 780 Td\n'+'\n'.join('('+line+') Tj T*' for line in TEXT.splitlines())+'\nET').encode())
    page[NameObject('/Contents')]=writer._add_object(stream)
    writer.write(root/'text.pdf')
    image=Image.new('RGB',(1400,700),'white');ImageDraw.Draw(image).multiline_text((40,40),TEXT,fill='black',font_size=40,spacing=18)
    image.save(root/'receipt.png');image.save(root/'receipt.jpg',quality=95);image.save(root/'scan.pdf',format='PDF',resolution=144)
    (root/'corrupt.pdf').write_bytes(b'%PDF-1.7 broken\n%%EOF')
    pages=PdfWriter()
    for _ in range(6):pages.add_blank_page(width=100,height=100)
    pages.write(root/'six-pages.pdf')
    (root/'invalid.png').write_bytes(b'<html>synthetic invalid signature</html>')
    (root/'oversized.pdf').write_bytes(b'x'*(5*1024*1024+1))
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    (root/'large-image.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',200000,200000,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'))+chunk(b'IEND',b''))
    manifest=[]
    for path in sorted(root.iterdir()):
        body=path.read_bytes();manifest.append(dict(name=path.name,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),expected='valid total 1234 USD minor units' if path.name in ('text.pdf','scan.pdf','receipt.png','receipt.jpg') else 'reject upload or extraction; six-pages PDF exceeds extraction limit'))
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
