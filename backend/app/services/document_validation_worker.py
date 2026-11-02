"""Untrusted parser worker: no credentials, strict CPU/memory/time limits, no extraction."""
import json
import resource
import sys
import warnings

sys.dont_write_bytecode = True

resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))


def validate(path):
    with open(path, 'rb') as source:
        header = source.read(12)
    if header.startswith(b'\x89PNG\r\n\x1a\n') or header.startswith(b'\xff\xd8\xff'):
        with open(path, 'rb') as source:
            source.seek(0, 2)
            length = source.tell()
            source.seek(max(0, length - 12))
            trailer = source.read()
        if header.startswith(b'\x89PNG') and trailer != b'\x00\x00\x00\x00IEND\xaeB`\x82':
            raise ValueError()
        if header.startswith(b'\xff\xd8') and not trailer.endswith(b'\xff\xd9'):
            raise ValueError()
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 20_000_000
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as image:
            fmt = image.format
            if fmt not in ('PNG', 'JPEG') or image.width * image.height > 20_000_000:
                raise ValueError()
            image.verify()
        with Image.open(path) as image:
            image.load()
        return 'image/png' if fmt == 'PNG' else 'image/jpeg'
    if header.startswith(b'%PDF-'):
        from pypdf import PdfReader
        from pypdf.generic import DictionaryObject, ArrayObject, IndirectObject
        with open(path, 'rb') as source:
            source.seek(0, 2)
            source.seek(max(0, source.tell() - 1024))
            if not source.read().rstrip().endswith(b'%%EOF'):
                raise ValueError()
        reader = PdfReader(path, strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 100:
            raise ValueError()
        forbidden = {'/JS', '/JavaScript', '/OpenAction', '/AA', '/Launch', '/RichMedia', '/EmbeddedFiles', '/EF', '/AcroForm', '/XFA'}
        todo = [reader.trailer]; seen = set(); count = 0
        while todo:
            item = todo.pop(); count += 1
            if count > 50_000:
                raise ValueError()
            if isinstance(item, IndirectObject):
                marker = (item.idnum, item.generation)
                if marker in seen:
                    continue
                seen.add(marker); item = item.get_object()
            if isinstance(item, DictionaryObject):
                if forbidden.intersection(item.keys()):
                    raise ValueError()
                todo.extend(item.values())
            elif isinstance(item, ArrayObject):
                todo.extend(item)
        return 'application/pdf'
    raise ValueError()


if __name__ == '__main__':
    try:
        print(json.dumps({'mime': validate(sys.argv[1])}))
    except Exception:
        # No filenames, parser diagnostics, document content or metadata in output.
        sys.exit(1)
