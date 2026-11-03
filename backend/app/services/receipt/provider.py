"""Optional provider boundary. Only the free local provider is enabled."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from typing import Protocol
from app.schemas.extraction import ExtractedReceipt
from app.services.decoder_limits import decoder_slot

EXTRACTION_VERSION = 'pdfium-rules-v2'


class ExtractionError(Exception):
    def __init__(self, code): self.code=code


class ExtractionProvider(Protocol):
    def extract(self, path: Path, mime: str) -> ExtractedReceipt: ...


class LocalProvider:
    def extract(self, path, mime):
        if not decoder_slot.acquire(blocking=False):
            raise ExtractionError('PROCESSING_BUSY')
        try:return self._extract(path,mime)
        finally:decoder_slot.release()

    def _extract(self, path, mime):
        worker=Path(__file__).with_name('worker.py')
        # communicate() on a PIPE buffers all output before enforcing OUTPUT_LIMIT.
        # A regular temporary file keeps decoder output off the parent heap; the
        # worker's RLIMIT_FSIZE also applies to this inherited stdout descriptor.
        with tempfile.TemporaryFile() as output_file:
            process=subprocess.Popen([sys.executable,'-I',str(worker),str(path),mime],stdout=output_file,stderr=subprocess.DEVNULL,env={},start_new_session=True)
            try:
                process.communicate(timeout=60)
            except subprocess.TimeoutExpired:
                try: os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                process.communicate()
                raise ExtractionError('PROCESSING_TIMEOUT') from None
            if process.returncode:
                raise ExtractionError('RESOURCE_LIMIT')
            if os.fstat(output_file.fileno()).st_size>250000:
                raise ExtractionError('OUTPUT_LIMIT')
            output_file.seek(0)
            output=output_file.read(250001)
        try:
            body=json.loads(output)
            if 'error' in body: raise ExtractionError(body['error'])
            return ExtractedReceipt.model_validate(body['result'])
        except (ValueError,KeyError,TypeError): raise ExtractionError('INVALID_OUTPUT') from None



provider: ExtractionProvider = LocalProvider()
