"""Bounded official REST reads and atomic observational snapshots. No OAuth storage."""
import json
import os
import time
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select, text, func
from sqlalchemy.dialects.postgresql import insert
from app.models.github_progress import (GitHubSyncRun as Run, GitHubRepositorySnapshot as Repo,
    GitHubMilestoneSnapshot as Milestone, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull)
from app.schemas.github_progress import RepositoryData, MilestoneData, IssueData, PullData
from app.services.project_management import project_for, can_manage

NOW = lambda: datetime.now(timezone.utc)


class SyncError(Exception):
    def __init__(self, code, retry_at=None): self.code, self.retry_at = code, retry_at


class GitHubClient:
    def __init__(self, transport=None): self.transport = transport

    def get(self, client, path, params=None, etag=None):
        if time.monotonic() > client.sync_deadline: raise SyncError('TIME_LIMIT')
        headers = {'If-None-Match':etag} if etag else {}
        try:
            with client.stream('GET', path, params=params, headers=headers) as response:
                if response.status_code in (403,429):
                    try:
                        delay = max(60, int(response.headers.get('retry-after','60')))
                        reset = int(response.headers.get('x-ratelimit-reset','0'))
                        delay = max(delay, reset-int(time.time()))
                        if delay > 86400: raise ValueError()
                    except ValueError: delay = 86400
                    raise SyncError('RATE_LIMITED', NOW()+timedelta(seconds=delay))
                if response.status_code == 404: raise SyncError('REPOSITORY_UNAVAILABLE')
                if response.status_code == 409 and path.endswith('/commits'): return [], None, False
                if response.status_code == 304: return None, response.headers.get('etag',etag), False
                if response.status_code >= 500: raise SyncError('GITHUB_UNAVAILABLE')
                if response.status_code != 200: raise SyncError('GITHUB_REJECTED')
                body = bytearray()
                for chunk in response.iter_bytes(65536):
                    body.extend(chunk)
                    if len(body)>2_000_000: raise SyncError('RESPONSE_LIMIT')
                    if time.monotonic()>client.sync_deadline: raise SyncError('TIME_LIMIT')
                return json.loads(body), response.headers.get('etag'), bool(response.links.get('next'))
        except (httpx.HTTPError, ValueError): raise SyncError('INVALID_OR_UNAVAILABLE_RESPONSE') from None

    def pages(self, client, path, params, cutoff=None):
        rows=[]
        for page in range(1,6):
            data,_,more=self.get(client,path,{**params,'per_page':100,'page':page})
            if not isinstance(data,list): raise SyncError('MALFORMED_RESPONSE')
            if len(data)>100: raise SyncError('MALFORMED_RESPONSE')
            rows.extend(data)
            if cutoff and data:
                try:
                    if datetime.fromisoformat(data[-1]['updated_at'].replace('Z','+00:00')) < cutoff: return rows
                except (ValueError, KeyError, TypeError): raise SyncError('MALFORMED_RESPONSE') from None
            if not more: return rows
        raise SyncError('PAGE_LIMIT')

    def collect(self, project, cached, since):
        headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'OpenDev-Progress'}
        token=os.getenv('GITHUB_SYNC_TOKEN')
        if token: headers['Authorization']='Bearer '+token
        with httpx.Client(base_url='https://api.github.com',headers=headers,timeout=10,follow_redirects=False,transport=self.transport) as client:
            client.sync_deadline=time.monotonic()+80
            data,etag,_=self.get(client,f'/repositories/{project.github_repo_id}',etag=cached.etag if cached else None)
            if data is None:
                if cached is None: raise SyncError('MALFORMED_RESPONSE')
                data=cached.metadata_json
            if data.get('private') is not False: raise SyncError('REPOSITORY_NOT_PUBLIC')
            repo=RepositoryData.model_validate(data)
            if repo.id!=project.github_repo_id: raise SyncError('REPOSITORY_IDENTITY_CHANGED')
            base='/repos/'+repo.full_name
            milestones=self.pages(client,base+'/milestones',{'state':'all'})
            params={'state':'all','sort':'updated','direction':'desc'}
            issues=self.pages(client,base+'/issues',{**params,**({'since':since.isoformat()} if since else {})})
            pulls=self.pages(client,base+'/pulls',params,cutoff=since)
            commits,_,_=self.get(client,base+'/commits',{'per_page':30})
            if not isinstance(commits,list): raise SyncError('MALFORMED_RESPONSE')
            observed=[]
            for commit in commits[:30]:
                sha=commit['sha']
                if not isinstance(sha,str) or len(sha)!=40 or any(c not in '0123456789abcdef' for c in sha):raise SyncError('MALFORMED_RESPONSE')
                date=datetime.fromisoformat(commit['commit']['committer']['date'].replace('Z','+00:00'))
                observed.append({'sha':sha,'committed_at':date.isoformat()})
            return (repo,etag,[MilestoneData.model_validate(row) for row in milestones],
                    [IssueData.model_validate(row) for row in issues if 'pull_request' not in row],
                    [PullData.model_validate(row) for row in pulls],observed)


client = GitHubClient()


def upsert(db, model, values):
    stmt=insert(model).values(**values)
    db.execute(stmt.on_conflict_do_update(index_elements=['project_id','github_id'],set_={k:v for k,v in values.items() if k not in ('project_id','github_id')}))


def sync(db, project_id, user):
    project=project_for(db,project_id,user)
    if not can_manage(db,project,user): raise HTTPException(403,'Project owner or maintainer required')
    with db.get_bind().engine.connect() as slot:
        if not slot.scalar(text("SELECT pg_try_advisory_xact_lock(hashtextextended(:key,0))"),{'key':'opendev-github:'+str(project_id)}):
            raise HTTPException(409,'GitHub synchronization already running')
        # Anonymous IP and configured token quotas can be shared across projects.
        cooldown=db.scalar(select(func.max(Run.retry_at)).where(Run.retry_at>NOW()))
        if cooldown: raise HTTPException(429,'GitHub cooldown active',headers={'Retry-After':str(max(1,int((cooldown-NOW()).total_seconds())))})
        for old in db.scalars(select(Run).where(Run.project_id==project_id,Run.status=='running')):
            old.status='failed';old.error_code='INTERRUPTED';old.completed_at=NOW()
        previous=db.scalar(select(Run).where(Run.project_id==project_id,Run.status=='completed').order_by(Run.started_at.desc()).limit(1))
        since=previous.started_at-timedelta(minutes=10) if previous else None
        run=Run(id=str(uuid4()),project_id=project_id,status='running',started_at=NOW(),counters={})
        db.add(run);db.commit()
        try:
            cached=db.get(Repo,project_id)
            repo,etag,milestones,issues,pulls,commits=client.collect(project,cached,since)
            now=NOW()
            for model,rows in [(Milestone,milestones),(Issue,issues),(Pull,pulls)]:
                for row in rows:
                    values=row.model_dump();values['github_id']=values.pop('id')
                    if model is Milestone: values['due_date']=values.pop('due_on')
                    if model is Issue:
                        milestone=values.pop('milestone');values['milestone_github_id']=milestone['id'] if milestone else None
                    upsert(db,model,dict(project_id=project_id,last_synced_at=now,**values))
            values=dict(publicly_accessible=True,github_repo_id=repo.id,metadata_json=repo.model_dump(mode='json'),recent_commits=commits,etag=etag,last_synced_at=now)
            if cached:
                for key,value in values.items():setattr(cached,key,value)
            else:db.add(Repo(project_id=project_id,**values))
            run.status='completed';run.completed_at=now
            run.counters={'milestones':len(milestones),'issues':len(issues),'pull_requests':len(pulls),'sampled_commits':len(commits)}
            db.commit()
        except Exception as exc:
            db.rollback();run=db.get(Run,run.id)
            run.status='failed';run.completed_at=NOW()
            run.error_code=exc.code if isinstance(exc,SyncError) else 'MALFORMED_RESPONSE' if isinstance(exc,(ValidationError,KeyError,TypeError,ValueError,AttributeError)) else 'SYNC_FAILED'
            cached=db.get(Repo,project_id)
            if cached and run.error_code in ('REPOSITORY_UNAVAILABLE','REPOSITORY_NOT_PUBLIC','REPOSITORY_IDENTITY_CHANGED'):cached.publicly_accessible=False
            run.retry_at=exc.retry_at if isinstance(exc,SyncError) else None
            db.commit()
        return run


def read_project(db, project_id, user, status_only=False):
    project=project_for(db,project_id,user)
    manager=can_manage(db,project,user)
    if project.status!='active' and not (status_only and manager):raise HTTPException(404,'Project not found')
    latest=db.scalar(select(Run).where(Run.project_id==project_id).order_by(Run.started_at.desc()).limit(1))
    cached=db.get(Repo,project_id)
    if not manager and cached and not cached.publicly_accessible:raise HTTPException(404,'Repository activity unavailable')
    if not manager and latest and latest.error_code in ('REPOSITORY_UNAVAILABLE','REPOSITORY_NOT_PUBLIC','REPOSITORY_IDENTITY_CHANGED'):
        raise HTTPException(404,'Repository activity unavailable')
    return project


def status(db, project_id):
    latest=db.scalar(select(Run).where(Run.project_id==project_id).order_by(Run.started_at.desc()).limit(1))
    success=db.scalar(select(Run).where(Run.project_id==project_id,Run.status=='completed').order_by(Run.started_at.desc()).limit(1))
    timestamp=success.completed_at if success else None
    return dict(latest=latest,last_successful_sync_at=timestamp,stale=not timestamp or NOW()-timestamp>timedelta(hours=6) or bool(latest and latest.status!='completed'))
