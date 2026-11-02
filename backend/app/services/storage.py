"""Private Supabase Storage REST adapter. No public object endpoints or upserts."""
import os
import re
from urllib.parse import urlparse, urlencode
import httpx
from fastapi import HTTPException


class UploadFailure(HTTPException):
    def __init__(self, cleanup_safe: bool):
        super().__init__(502, 'Private storage upload failed')
        self.cleanup_safe = cleanup_safe


class Storage:
    def __init__(self, transport=None):
        self.transport = transport

    def configuration(self):
        base = os.getenv('SUPABASE_URL', '').rstrip('/')
        bucket = os.getenv('SUPABASE_STORAGE_BUCKET', '')
        secret = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
        url = urlparse(base)
        if (url.scheme != 'https' or not url.hostname or not re.fullmatch(r'[a-z0-9-]+\.supabase\.co', url.hostname) or
            url.netloc != url.hostname or url.path or url.query or url.fragment or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}', bucket) or not secret):
            raise HTTPException(503, 'Private storage configuration is incomplete')
        return base, bucket, {'Authorization': f'Bearer {secret}', 'apikey': secret}

    def request(self, method, path, **kwargs):
        base, bucket, headers = self.configuration()
        headers.update(kwargs.pop('headers', {}))
        try:
            with httpx.Client(base_url=base + '/storage/v1/', headers=headers, timeout=15, follow_redirects=False, transport=self.transport) as client:
                result = client.request(method, path, **kwargs)
                result.raise_for_status()
                return result
        except (httpx.HTTPError, ValueError, TypeError):
            raise HTTPException(502, 'Private storage request failed') from None

    def require_private(self):
        _, bucket, _ = self.configuration()
        try:
            info = self.request('GET', f'bucket/{bucket}').json()
            if not isinstance(info, dict) or info.get('public') is not False:
                raise HTTPException(503, 'Storage bucket must be private')
        except ValueError:
            raise HTTPException(502, 'Invalid storage bucket response') from None

    def upload(self, key, path, mime):
        self.require_private()
        _, bucket, _ = self.configuration()
        # Keep provider status private but distinguish collisions from uncertain uploads.
        base, _, headers = self.configuration()
        headers.update({'Content-Type': mime, 'x-upsert': 'false'})
        try:
            with httpx.Client(timeout=15, follow_redirects=False, transport=self.transport) as client, open(path, 'rb') as source:
                response = client.post(f'{base}/storage/v1/object/{bucket}/{key}', headers=headers, content=source)
                if response.status_code in (400, 409):
                    raise UploadFailure(cleanup_safe=False)
                response.raise_for_status()
        except UploadFailure:
            raise
        except (httpx.HTTPError, OSError):
            raise UploadFailure(cleanup_safe=True) from None

    def delete(self, key):
        _, bucket, _ = self.configuration()
        self.request('DELETE', f'object/{bucket}', json={'prefixes': [key]})

    def signed_url(self, key, mime):
        self.require_private()
        base, bucket, _ = self.configuration()
        try:
            result = self.request('POST', f'object/sign/{bucket}/{key}', json={'expiresIn': 60}).json()
            relative = result['signedURL']
            if not isinstance(relative, str) or not relative.startswith(f'/object/sign/{bucket}/{key}?'):
                raise ValueError()
            ext = {'application/pdf':'pdf', 'image/png':'png', 'image/jpeg':'jpg'}[mime]
            # Attachment filename is generated, never derived from untrusted document text.
            return base + '/storage/v1' + relative + '&' + urlencode({'download': 'evidence.' + ext})
        except (ValueError, TypeError, KeyError):
            raise HTTPException(502, 'Invalid storage signing response') from None


storage = Storage()
