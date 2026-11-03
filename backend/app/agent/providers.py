"""Provider boundary: serialized public messages only; no application tools or DB."""
import asyncio
import json
from typing import Protocol
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field


class ProviderError(Exception):
    """Safe error: provider payloads and endpoint details must never reach clients."""


class FunctionCall(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: str = Field(max_length=100)
    arguments: dict
    index: int = 0  # Ollama's wire response includes a function index.


class ModelMessage(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    role: str = 'assistant'
    content: str = Field(default='', max_length=8000)
    tool_calls: list[dict] = Field(default_factory=list, max_length=6)


class GenerationSettings(BaseModel):
    temperature: float = 0
    num_predict: int = 512
    num_ctx: int = 8192


class ModelProvider(Protocol):
    async def available(self, timeout: float) -> bool: ...
    async def chat(self, messages: list[dict], tools: list[dict],
                   settings: GenerationSettings, timeout: float) -> ModelMessage: ...


class DeterministicProvider:
    """Step 1 is intentionally independent of model generation and external services."""
    async def available(self, timeout=0):
        return True

    def answer(self, tools, question):
        from app.agent.answers import answer
        return answer(tools, question)


class OllamaProvider:
    def __init__(self, base_url: str, model: str, transport=None):
        url = urlsplit(base_url)
        if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ('', '/'):
            raise ProviderError('Invalid provider configuration')
        if not model or len(model) > 200:
            raise ProviderError('Invalid provider configuration')
        self.base_url, self.model, self.transport = base_url.rstrip('/'), model, transport

    async def _request(self, path, payload, timeout):
        try:
            # Endpoint is operator configuration, never model/user input. No redirects,
            # ambient proxy credentials or cookies; intended for a private local service.
            async with httpx.AsyncClient(transport=self.transport, trust_env=False,
                                        follow_redirects=False, timeout=timeout) as client:
                async with asyncio.timeout(timeout):
                    async with client.stream('POST', self.base_url + path, json=payload) as response:
                        response.raise_for_status()
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > 32768:
                                raise ProviderError('Provider response too large')
                        return json.loads(body)
        except (httpx.HTTPError, TimeoutError, ValueError, RecursionError) as exc:
            raise ProviderError('Provider unavailable or invalid response') from exc

    async def available(self, timeout):
        result = await self._request('/api/show', {'model': self.model}, timeout)
        return isinstance(result, dict) and isinstance(result.get('capabilities'), list) and 'tools' in result['capabilities']

    async def chat(self, messages, tools, settings, timeout):
        result = await self._request('/api/chat', {
            'model': self.model, 'messages': messages, 'tools': tools, 'stream': False,
            'think': False, 'options': settings.model_dump(), 'keep_alive': '5m',
        }, timeout)
        try:
            if result.get('done') is not True:
                raise ValueError('Incomplete response')
            raw = result['message']
            # Ollama may include thinking and timing fields; never forward them.
            message = ModelMessage.model_validate({k: raw[k] for k in ('role', 'content', 'tool_calls') if k in raw})
            if message.role != 'assistant':
                raise ValueError('Invalid role')
            return message
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise ProviderError('Invalid provider response') from exc
