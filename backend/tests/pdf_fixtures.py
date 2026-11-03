"""Synthetic PDFs using the already-required BSD pypdf writer."""
import io
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject


def text_pdf(text, pages=1, rotation=0):
    writer = PdfWriter()
    for _ in range(pages):
        page = writer.add_blank_page(width=595, height=842)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
            NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
            DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject()
        commands = ['BT /F1 14 Tf 18 TL 40 782 Td']
        for line in text.splitlines():
            safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            commands.append(f'({safe}) Tj T*')
        stream.set_data(('\n'.join(commands)+'\nET').encode('latin1'))
        page[NameObject('/Contents')] = writer._add_object(stream)
        if rotation:page.rotate(rotation)
    result = io.BytesIO(); writer.write(result)
    return result.getvalue()
