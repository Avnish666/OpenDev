"""Optional provider boundary. Only the free local provider is enabled."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from typing import Protocol
from app.schemas.extraction import ExtractedReceipt

EXTRACTION_VERSION = 'local-rules-v1'


class ExtractionError(Exception):
    def __init__(self, code): self.code=code


class ExtractionProvider(Protocol):
    def extract(self, path: Path, mime: str) -> ExtractedReceipt: ...


class LocalProvider:
    def extract(self, path, mime):
        worker=Path(__file__).with_name('worker.py')
        process=subprocess.Popen([sys.executable,'-I',str(worker),str(path),mime],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env={},start_new_session=True)
        try:
            output,_=process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            try: os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            process.communicate()
            raise ExtractionError('PROCESSING_TIMEOUT') from None
        if process.returncode:
            raise ExtractionError('RESOURCE_LIMIT')
        if len(output)>250000:
            raise ExtractionError('OUTPUT_LIMIT')
        try:
            body=json.loads(output)
            if 'error' in body: raise ExtractionError(body['error'])
            return ExtractedReceipt.model_validate(body['result'])
        except (ValueError,KeyError,TypeError): raise ExtractionError('INVALID_OUTPUT') from None


provider: ExtractionProvider = LocalProvider()
