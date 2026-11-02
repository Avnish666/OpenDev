"""Sandbox-only REST adapter. Contracts: paypal-plan.md; never log provider bodies."""
import os
import asyncio
import re
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException

BASE_URL = 'https://api-m.sandbox.paypal.com'

class PayPal:
    def __init__(self, transport=None):
        self.transport = transport

    def config(self, name):
        value = os.getenv(name)
        if not value:
            raise HTTPException(503, 'PayPal Sandbox configuration is incomplete')
        return value

    async def request(self, method, path, body=None, key=None):
        try:
            async with asyncio.timeout(35):
                return await self._request(method,path,body,key)
        except TimeoutError:
            raise HTTPException(502, "PayPal Sandbox timed out; retry the same contribution") from None

    async def _request(self, method, path, body=None, key=None):
        # Bounded calls, TLS/proxy defaults retained, redirects and implicit retries disabled.
        try:
            async with httpx.AsyncClient(base_url=BASE_URL, timeout=15, follow_redirects=False, transport=self.transport) as client:
                token = await client.post('/v1/oauth2/token', auth=(self.config('PAYPAL_CLIENT_ID'), self.config('PAYPAL_CLIENT_SECRET')), data={'grant_type':'client_credentials'})
                token.raise_for_status()
                headers = {'Authorization': 'Bearer ' + token.json()['access_token'], 'Prefer':'return=representation'}
                if key: headers['PayPal-Request-Id'] = key
                response = await client.request(method, path, json=body, headers=headers)
                response.raise_for_status()
                value = response.json()
                if not isinstance(value, dict): raise ValueError()
                return value
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise HTTPException(502, 'PayPal Sandbox request failed; retry the same contribution') from None

    def identifier(self, value):
        if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9-]{1,64}', value):
            raise HTTPException(502, 'Invalid PayPal resource identifier')
        return value

    async def order(self, order_id):
        return await self.request('GET', f'/v2/checkout/orders/{self.identifier(order_id)}')

    async def capture_details(self, capture_id):
        return await self.request('GET', f'/v2/payments/captures/{self.identifier(capture_id)}')

    async def verify(self, event, headers):
        names = {'auth_algo':'paypal-auth-algo','cert_url':'paypal-cert-url','transmission_id':'paypal-transmission-id','transmission_sig':'paypal-transmission-sig','transmission_time':'paypal-transmission-time'}
        if any(not headers.get(n) for n in names.values()): raise HTTPException(400,'Missing PayPal signature headers')
        body = {k: headers[v] for k,v in names.items()}
        body.update(webhook_id=self.config('PAYPAL_WEBHOOK_ID'), webhook_event=event)
        result = await self.request('POST','/v1/notifications/verify-webhook-signature',body)
        if result.get('verification_status') != 'SUCCESS': raise HTTPException(400,'Invalid PayPal signature')

    def approval(self, order):
        for link in order.get('links',[]):
            if link.get('rel') in ('approve','payer-action'):
                url = urlparse(link.get('href',''))
                if url.scheme == 'https' and url.hostname == 'www.sandbox.paypal.com' and url.port in (None,443) and not url.username:
                    return link['href']
        raise HTTPException(502,'PayPal did not supply a Sandbox approval URL')

paypal = PayPal()
