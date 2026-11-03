"""PDFium text/raster adapter, used only in the resource-limited worker."""
import ctypes
import math
from contextlib import closing
import pypdfium2 as pdfium


def digital_lines(page, number):
    width, height = page.get_size()
    if not all(math.isfinite(v) and 0 < v <= 50000 for v in (width, height)):
        raise ValueError('Invalid page dimensions')
    with closing(page.get_textpage()) as text:
        count = text.count_chars()
        if count > 100000:
            raise ValueError('Text limit')
        lines, chars, boxes = [], [], []

        def flush():
            if chars and ''.join(chars).strip():
                lines.append(dict(text=''.join(chars).strip(), page=number, quality=100,
                    coordinates='pdf_points', bbox=[min(b[0] for b in boxes), min(b[1] for b in boxes),
                    max(b[2] for b in boxes), max(b[3] for b in boxes)]))
            chars.clear(); boxes.clear()

        for index in range(count):
            code = pdfium.raw.FPDFText_GetUnicode(text, index)
            if not code:
                continue
            char = chr(code)
            if char in '\r\n':
                flush()
                continue
            left, bottom, right, top = text.get_charbox(index)
            points = []
            for x, y in ((left, bottom), (right, top), (left, top), (right, bottom)):
                dx, dy = ctypes.c_int(), ctypes.c_int()
                if not pdfium.raw.FPDF_PageToDevice(page, 0, 0, round(width*100), round(height*100),
                        0, x, y, ctypes.byref(dx), ctypes.byref(dy)):
                    raise ValueError('Invalid text position')
                points.append((dx.value/100, dy.value/100))
            chars.append(char)
            boxes.append((min(p[0] for p in points), min(p[1] for p in points),
                          max(p[0] for p in points), max(p[1] for p in points)))
        flush()
        return lines


def raster(page):
    width, height = page.get_size()
    if not all(math.isfinite(v) and 0 < v <= 50000 for v in (width, height)):
        raise ValueError('Invalid page dimensions')
    # Convert/detach before native bitmap closes; no forms or JavaScript.
    with closing(page.render(scale=min(2, 2000/max(width, height)), may_draw_forms=False)) as bitmap:
        image = bitmap.to_pil().convert('RGB')
        if image.width * image.height > 4000000:
            raise ValueError('Raster limit')
        return image
