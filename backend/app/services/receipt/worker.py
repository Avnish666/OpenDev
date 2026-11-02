"""Bounded local extraction subprocess; no environment secrets or text-derived commands."""
import csv
import io
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

def set_limits():
    sys.dont_write_bytecode = True
    resource.setrlimit(resource.RLIMIT_AS, (320 * 1024 * 1024, 320 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (50, 50))
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.services.receipt.parser import parse


class ProcessingError(Exception):
    pass


def ocr(image, page, folder):
    from PIL import Image
    if image.width * image.height > 8_000_000:
        image.thumbnail((2000,2000))
    path = Path(folder)/'ocr.png'; image.convert('RGB').save(path)
    output = Path(folder)/'ocr.tsv'
    try:
        with output.open('wb') as target:
            subprocess.run(['/usr/bin/tesseract',str(path),'stdout','-l','eng','--psm','6','tsv'],
                           stdout=target,stderr=subprocess.DEVNULL,timeout=12,check=True,
                           env={'OMP_THREAD_LIMIT':'1','PATH':'/usr/bin:/bin'})
    except FileNotFoundError: raise ProcessingError('OCR_UNAVAILABLE')
    except subprocess.TimeoutExpired: raise ProcessingError('OCR_TIMEOUT')
    except subprocess.CalledProcessError: raise ProcessingError('OCR_FAILED')
    if output.stat().st_size > 2_000_000: raise ProcessingError('TEXT_LIMIT')
    groups = {}
    for row in csv.DictReader(io.StringIO(output.read_text()),delimiter='\t'):
        if not row.get('text','').strip(): continue
        key = (row['block_num'],row['par_num'],row['line_num'])
        entry = groups.setdefault(key,[]); entry.append(row)
    lines = []
    for words in groups.values():
        x=min(int(w['left']) for w in words);y=min(int(w['top']) for w in words)
        right=max(int(w['left'])+int(w['width']) for w in words);bottom=max(int(w['top'])+int(w['height']) for w in words)
        lines.append({'text':' '.join(w['text'] for w in words),'page':page,'quality':sum(float(w['conf']) for w in words)/len(words),'bbox':[x,y,right,bottom],'coordinates':'image_pixels'})
    return lines


def extract(path, mime):
    import pymupdf
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = 20_000_000
    lines=[];methods=set();pages=1
    with tempfile.TemporaryDirectory(prefix='ocr-', dir=str(Path(path).parent)) as folder:
        if mime == 'application/pdf':
            with pymupdf.open(path) as pdf:
                if pdf.is_encrypted: raise ProcessingError('ENCRYPTED_PDF')
                pages=len(pdf)
                if not 1 <= pages <= 5: raise ProcessingError('PAGE_LIMIT')
                for number,page in enumerate(pdf,1):
                    grouped={}
                    for x0,y0,x1,y1,word,block,line,_ in page.get_text('words'):
                        entry=grouped.setdefault((block,line),{'words':[],'bbox':[x0,y0,x1,y1]})
                        entry['words'].append(word);box=entry['bbox'];box[:]=[min(box[0],x0),min(box[1],y0),max(box[2],x1),max(box[3],y1)]
                    digital=[{'text':' '.join(v['words']),'bbox':v['bbox'],'coordinates':'pdf_points','page':number,'quality':100} for v in grouped.values()]
                    if sum(len(v['text']) for v in digital) >= 30:
                        methods.add('pdf_text');lines.extend(digital)
                    else:
                        zoom=min(2,2000/max(page.rect.width,page.rect.height))
                        pix=page.get_pixmap(matrix=pymupdf.Matrix(zoom,zoom),alpha=False)
                        image=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                        lines.extend(ocr(image,number,folder));methods.add('tesseract')
        else:
            with Image.open(path) as original:
                if original.width*original.height > 20_000_000: raise ProcessingError('IMAGE_LIMIT')
                image=ImageOps.exif_transpose(original)
                lines=ocr(image,1,folder);methods.add('tesseract')
        if len(lines)>3000 or sum(len(line['text']) for line in lines)>100000: raise ProcessingError('TEXT_LIMIT')
        method='mixed' if len(methods)>1 else next(iter(methods),'no_text')
        return parse(lines,method,pages).model_dump(mode='json')


if __name__ == '__main__':
    set_limits()
    try: print(json.dumps({'result':extract(sys.argv[1],sys.argv[2])}))
    except ProcessingError as error: print(json.dumps({'error':str(error)}))
    except Exception: print(json.dumps({'error':'INVALID_DOCUMENT'}))
