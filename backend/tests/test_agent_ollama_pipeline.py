"""Ollama protocol regressions: synthetic model replies, real read-only evidence."""
import asyncio
import json
import logging
import os

import httpx
import pytest

from app.agent.orchestration import definitions
from app.agent.providers import OllamaProvider, GenerationSettings, ModelMessage, ProviderError
from app.core.config import settings
from app.agent import limits
from app.agent.contracts import AgentAnswer
from test_accountability import ac, contribution
from test_agent_orchestration import Replay, calls, final, run


@pytest.fixture(autouse=True)
def development(monkeypatch):
    monkeypatch.setattr(settings, 'APP_ENV', 'development')
    monkeypatch.setattr(settings, 'LLM_ENABLED', True)
    monkeypatch.setattr(limits, 'limiter', limits.RateLimiter())


def test_funding_native_call_then_constrained_answer(ac, monkeypatch):
    contribution(ac)
    requests = []
    def handle(request):
        data = json.loads(request.content)
        requests.append((request.url.path, data))
        if request.url.path == '/api/show':
            return httpx.Response(200, json={'capabilities': ['completion', 'tools', 'thinking']})
        if len(requests) == 2:
            assert 'format' not in data and data['tools']
            assert f'project_id={ac.p.id}' in data['messages'][0]['content']
            return httpx.Response(200, json={'done': True, 'message': {
                'role': 'assistant', 'content': '', 'tool_calls': calls('get_project_finances', project_id=ac.p.id).tool_calls}})
        assert 'format' in data and 'tools' not in data
        assert 'response_schema' not in data['options'] and data['think'] is False
        evidence = json.loads(data['messages'][-1]['content'])
        reference = evidence['citation']['reference']
        assert data['format']['$defs']['FinancialClaim']['properties']['references']['items']['enum'] == [reference]
        return httpx.Response(200, json={'done': True, 'message': {'role': 'assistant', 'content': json.dumps({
            'financial_claims': [{'kind': 'funding_reconciliation', 'references': [reference]}]})}})
    provider = OllamaProvider('http://127.0.0.1:11434', 'qwen3:4b', httpx.MockTransport(handle))
    monkeypatch.setattr('app.agent.orchestration.OllamaProvider', lambda *args: provider)
    response = ac.client.post(f'/api/projects/{ac.p.id}/agent/query', json={
        'project_id': ac.p.id, 'question': 'How much funding has this project received?', 'mode': 'llm'})
    assert response.status_code == 200
    result = AgentAnswer.model_validate(response.json())
    assert result.execution_mode == 'llm' and result.answer_status == 'answered'
    assert result.diagnostics['tool_names'] == ['get_project_finances']
    assert result.diagnostics['turn_count'] == 2
    assert result.citations and result.citations[0] == result.evidence_used[0].citation
    assert result.evidence_used[0].claim == 'finances'
    assert '2000 USD minor units' in result.answer
    assert 'llm_failures' not in result.diagnostics
    assert not any('fallback' in note.lower() for note in result.limitations)


def test_missing_first_call_retries_once_without_echoing_untrusted_content(ac):
    contribution(ac)
    provider = Replay([ModelMessage(content='PRIVATE_MODEL_OUTPUT funding is 999999'),
                       calls('get_project_finances', project_id=ac.p.id), final])
    result = run(ac, provider, question='How much funding has this project received?')
    assert result.execution_mode == 'llm' and result.answer_status == 'answered'
    assert result.diagnostics['tool_names'] == ['get_project_finances']
    assert result.diagnostics['turn_count'] == 3
    assert result.diagnostics['llm_failures'] == [{'stage': 'tool_selection', 'category': 'missing_tool_calls', 'turn': 1}]
    assert 'PRIVATE_MODEL_OUTPUT' not in json.dumps(provider.messages)
    assert '999999' not in result.answer and result.citations
    assert not any('fallback' in note.lower() for note in result.limitations)


def test_missing_calls_are_bounded_and_fallback_is_truthful(ac):
    result = run(ac, Replay([ModelMessage(content='PRIVATE_PROSE'), ModelMessage(content='{}')]))
    assert result.execution_mode == 'deterministic'
    assert result.diagnostics['tool_names'] == [] and result.diagnostics['turn_count'] == 2
    assert all(f['category'] == 'missing_tool_calls' for f in result.diagnostics['llm_failures'])
    assert 'PRIVATE_PROSE' not in json.dumps(result.diagnostics)


@pytest.mark.parametrize('kind,stage,category', [
    ('args', 'tool_validation', 'invalid_tool_arguments'),
    ('scope', 'tool_validation', 'invalid_tool_arguments'),
    ('unknown', 'tool_validation', 'unknown_tool'),
    ('json', 'answer_validation', 'malformed_structured_output'),
    ('schema', 'answer_validation', 'invalid_answer_schema'),
    ('citation', 'answer_validation', 'invalid_citation_or_fact'),
])
def test_exact_failure_stage_and_no_sensitive_diagnostics(ac, caplog, kind, stage, category):
    steps = [calls('get_project_finances', project_id=ac.p.id)]
    if kind == 'args': steps = [calls('get_project_finances', project_id=str(ac.p.id), secret='PRIVATE_ARGS')]
    elif kind == 'scope': steps = [calls('get_project_finances', project_id=ac.other.id)]
    elif kind == 'unknown': steps = [calls('PRIVATE_UNKNOWN_TOOL', project_id=ac.p.id)]
    elif kind == 'json': steps += [ModelMessage(content='PRIVATE_RAW_OUTPUT')]
    elif kind == 'schema': steps += [ModelMessage(content='{"facts":[],"secret":"PRIVATE_OUTPUT"}')]
    else: steps += [ModelMessage(content='{"facts":[{"reference":"PRIVATE_CITATION","pointer":"/title"}]}')]
    with caplog.at_level(logging.INFO, logger='app.agent.diagnostics'):
        result = run(ac, Replay(steps), question='PRIVATE_QUESTION funding')
    assert result.execution_mode == 'deterministic'
    assert result.diagnostics['llm_failures'][-1] == {'stage': stage, 'category': category, 'turn': 1 if kind in ('args','scope','unknown') else 2}
    assert 'PRIVATE_' not in json.dumps(result.diagnostics) and 'PRIVATE_' not in caplog.text
    assert 'stage=' in caplog.text and 'category=' in caplog.text


@pytest.mark.parametrize('environment', ['production', 'testing', 'staging'])
def test_detailed_failures_never_exposed_outside_development(ac, monkeypatch, caplog, environment):
    monkeypatch.setattr(settings, 'APP_ENV', environment)
    with caplog.at_level(logging.INFO, logger='app.agent.diagnostics'):
        result = run(ac, Replay([calls('get_project_finances', project_id='PRIVATE_ARGS')]))
    assert 'llm_failures' not in result.diagnostics and not caplog.records


def test_model_timeout_distinguished_from_invalid_output(ac):
    class Slow(Replay):
        async def chat(self, *args): await asyncio.sleep(10)
    result = run(ac, Slow(), model_timeout=.02)
    assert result.diagnostics['llm_failures'][-1]['stage'] == 'model_request'
    assert result.diagnostics['llm_failures'][-1]['category'] == 'model_timeout'
    assert result.execution_mode == 'deterministic'


def test_structured_additional_tools_still_use_scope_validation(ac):
    def more(messages):
        return ModelMessage(content=json.dumps({'tool_requests': [{'name': 'get_project_overview', 'arguments': {'project_id': ac.p.id}}]}))
    result = run(ac, Replay([calls('get_project_finances', project_id=ac.p.id), more, final]))
    assert result.execution_mode == 'llm' and len(result.citations) == 2
    assert result.diagnostics['tool_names'] == ['get_project_finances', 'get_project_overview']
    for args in ({'project_id': ac.other.id}, {'project_id': True}, {'project_id': ac.p.id, 'url': 'PRIVATE_URL'}):
        result = run(ac, Replay([calls('get_project_finances', project_id=ac.p.id),
            ModelMessage(content=json.dumps({'tool_requests': [{'name': 'get_project_overview', 'arguments': args}]}))]))
        assert result.execution_mode == 'deterministic'
        assert result.diagnostics['tool_names'] == ['get_project_finances']
        assert result.diagnostics['llm_failures'][-1]['category'] == 'invalid_tool_arguments'


@pytest.mark.parametrize('body,category', [
    ({'done': True, 'done_reason': 'length', 'message': {'role': 'assistant', 'content': 'PRIVATE_TRUNCATED'}}, 'model_output_truncated'),
    ({'done': False}, 'provider_incomplete_response'),
    ({'done': True, 'message': {'role': 'user', 'content': 'PRIVATE_OUTPUT'}}, 'provider_invalid_message'),
    ([], 'provider_invalid_message'),
])
def test_provider_exact_categories_hide_raw_responses(body, category):
    provider = OllamaProvider('http://127.0.0.1:11434', 'qwen3:4b', httpx.MockTransport(lambda r: httpx.Response(200, json=body)))
    with pytest.raises(ProviderError) as error: asyncio.run(provider.chat([], [], GenerationSettings(), 1))
    assert error.value.category == category and 'PRIVATE_' not in str(error.value)


def test_http_timeout_has_distinct_provider_category():
    def timeout(request): raise httpx.ReadTimeout('PRIVATE_ENDPOINT')
    provider = OllamaProvider('http://127.0.0.1:11434', 'qwen3:4b', httpx.MockTransport(timeout))
    with pytest.raises(ProviderError) as error: asyncio.run(provider.chat([], [], GenerationSettings(), 1))
    assert error.value.category == 'provider_timeout' and 'PRIVATE_' not in str(error.value)


def test_structured_generation_cannot_mix_native_tool_mode():
    provider = OllamaProvider('http://127.0.0.1:11434', 'qwen3:4b')
    with pytest.raises(ProviderError):
        asyncio.run(provider.chat([], definitions(1, 2), GenerationSettings(response_schema={'type': 'object'}), 1))


def test_truncated_first_turn_preserves_honest_deterministic_fallback(ac):
    def handle(request):
        body = {'capabilities': ['tools']} if request.url.path == '/api/show' else {
            'done': True, 'done_reason': 'length', 'message': {'role': 'assistant', 'content': 'PRIVATE_TRUNCATED'}}
        return httpx.Response(200, json=body)
    result = run(ac, OllamaProvider('http://127.0.0.1:11434', 'qwen3:4b', httpx.MockTransport(handle)))
    assert result.execution_mode == 'deterministic' and result.diagnostics['tool_names'] == []
    assert result.diagnostics['llm_failures'] == [{'stage': 'model_request', 'category': 'model_output_truncated', 'turn': 1}]
    assert 'PRIVATE_' not in json.dumps(result.diagnostics)


@pytest.mark.skipif(os.getenv('OPENDEV_TEST_LOCAL_OLLAMA') != '1', reason='Explicit opt-in and installed local Ollama required')
def test_actual_local_ollama_funding_acceptance(ac):
    """Real inference only when requested; fixtures create an isolated public campaign."""
    from app.acceptance.ollama import probe
    base = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    model = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
    status = probe(base, model)
    assert status.get('model_present') and status.get('model_local') and status.get('tool_capability'), status
    contribution(ac)
    result = run(ac, OllamaProvider(base, model), question='How much funding has this project received?',
                 timeout_seconds=120, model_timeout=60)
    safe = {'mode': result.execution_mode, 'status': result.answer_status, 'diagnostics': result.diagnostics}
    assert result.execution_mode == 'llm' and result.answer_status == 'answered', safe
    assert 'get_project_finances' in result.diagnostics['tool_names'], safe
    finances = [e for e in result.evidence_used if e.claim == 'finances']
    assert finances and all(e.citation in result.citations for e in finances), safe
    assert not any('fallback' in note.lower() for note in result.limitations), safe
