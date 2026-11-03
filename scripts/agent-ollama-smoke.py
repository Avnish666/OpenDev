"""Explicit local-only smoke: never install Ollama or download a model.

From backend/: python ../scripts/agent-ollama-smoke.py --project-id ID
Requires an existing active synthetic project in a local opendev_test_* database.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))

import httpx
from sqlalchemy.engine import make_url
from app.agent.providers import OllamaProvider
from app.agent.contracts import AgentQuestion
from app.core.database import SessionLocal
from app.routers.agent import query


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-id', type=int, required=True)
    parser.add_argument('--question', default='How much funding has the project received?')
    args = parser.parse_args()
    target = make_url(os.environ['DATABASE_URL'])
    if target.host not in ('localhost', '127.0.0.1') or not (target.database or '').startswith('opendev_test_'):
        parser.error('Use an isolated local opendev_test_* database only')
    base = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
    provider = OllamaProvider(base, os.getenv('OLLAMA_MODEL', 'qwen3:4b'))
    if not asyncio.run(provider.available(5)):
        raise SystemExit('Installed model does not advertise tool capability')
    with httpx.Client(trust_env=False, timeout=5) as client:
        version = client.get(base + '/api/version')
        version.raise_for_status()
        print('Ollama version:', version.json()['version'])
    with SessionLocal() as db:
        result = query(db, AgentQuestion(project_id=args.project_id, question=args.question, mode='llm'))
    print(json.dumps({'mode': result.execution_mode, 'status': result.answer_status,
                      'diagnostics': result.diagnostics, 'citation_count': len(result.citations)}))
    if result.execution_mode != 'llm' or result.answer_status != 'answered' or not result.citations:
        raise SystemExit('Smoke failed: no validated LLM tool-calling answer')


if __name__ == '__main__':
    main()
