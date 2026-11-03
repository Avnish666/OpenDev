import json
import asyncio
from threading import Event
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from app.core.database import get_db
from app.routers.expenses import RecordID
from app.agent.contracts import AgentQuestion, AgentAnswer
from app.agent.tools import EvidenceTools
from app.agent.orchestration import orchestrate, AgentConfig, database_budget, insufficient
from app.agent import limits
from app.services.accountability import read_snapshot

router=APIRouter(prefix='/api/projects',tags=['Public accountability baseline'])


def query(db,question,cancelled=None):
    cancelled = cancelled or Event()
    if not limits.slots.acquire(blocking=False):raise HTTPException(429,'Evidence queries busy',headers={'Retry-After':'5'})
    try:
        with read_snapshot(db) as reader:
            config = AgentConfig.load()
            with database_budget(reader, config, cancelled):
                return asyncio.run(orchestrate(EvidenceTools(reader),question,config=config,cancelled=cancelled))
    except (TimeoutError, SQLAlchemyError):
        # Snapshot setup and fallback reads can fail outside the model loop. The
        # context managers have rolled back/closed before constructing this reply.
        # Do not expose driver details or retry on an aborted transaction.
        return insufficient('Public evidence unavailable or database execution budget exceeded.', mode='deterministic')
    finally:limits.slots.release()


@router.post('/{project_id}/agent/query',response_model=AgentAnswer,
    openapi_extra={'requestBody':{'required':True,'content':{'application/json':{'schema':AgentQuestion.model_json_schema()}}}})
async def ask(project_id: RecordID,request: Request,db: Session=Depends(get_db)):
    limits.limiter.check(request.client.host if request.client else 'unknown')
    if request.headers.get('content-type','').split(';')[0].strip().lower()!='application/json':raise HTTPException(415,'JSON required')
    data=bytearray()
    async for chunk in request.stream():
        if len(data)+len(chunk)>4096:raise HTTPException(413,'Question body exceeds 4096 bytes')
        data.extend(chunk)
    try:question=AgentQuestion.model_validate(json.loads(data))
    except (ValueError,ValidationError,RecursionError):raise HTTPException(422,'Invalid question; provide project_id and 3..1000 character question') from None
    if question.project_id!=project_id:raise HTTPException(422,'Project identifier mismatch')
    cancelled = Event()
    async def watch_disconnect():
        while not cancelled.is_set():
            if await request.is_disconnected():
                cancelled.set()
                return
            await asyncio.sleep(.25)
    watcher = asyncio.create_task(watch_disconnect())
    try:
        return await run_in_threadpool(query,db,question,cancelled)
    finally:
        cancelled.set()
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
