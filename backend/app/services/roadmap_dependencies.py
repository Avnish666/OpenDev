from fastapi import HTTPException
from sqlalchemy import select
from app.models.roadmap_dependency import RoadmapDependency as Edge
from app.models.roadmap import ProjectRoadmapMilestone as Milestone
from app.services import roadmap
from app.services.project_management import commit


def create(db,project_id,user,data):
    roadmap.authorize_project(db,project_id,user,True)
    source=db.scalar(select(Milestone).where(Milestone.id==data.from_id,Milestone.project_id==project_id).with_for_update().execution_options(populate_existing=True))
    target=db.get(Milestone,data.to_id)
    if not source or not target or target.project_id!=project_id:raise HTTPException(422,'Dependency milestones must belong to this project')
    roadmap.check_version(source,data)
    edges=db.scalars(select(Edge).where(Edge.project_id==project_id)).all()
    if any(e.from_id==data.from_id and e.to_id==data.to_id for e in edges):raise HTTPException(409,'Dependency already exists')
    graph={}
    for e in edges:graph.setdefault(e.from_id,[]).append(e.to_id)
    pending=[data.to_id];seen=set()
    while pending:
        node=pending.pop()
        if node==data.from_id:raise HTTPException(422,'Circular dependencies are not allowed')
        if node not in seen:seen.add(node);pending.extend(graph.get(node,[]))
    edge=Edge(project_id=project_id,from_id=data.from_id,to_id=data.to_id)
    db.add(edge);source.version+=1
    roadmap.audit(db,source,user,'dependency_linked',data.reason,{'status':source.status},{'status':source.status,'dependency':{'from_id':data.from_id,'to_id':data.to_id}})
    commit(db);db.refresh(edge);return edge


def remove(db,project_id,dependency_id,user,data):
    roadmap.authorize_project(db,project_id,user,True)
    edge=db.scalar(select(Edge).where(Edge.id==dependency_id,Edge.project_id==project_id))
    if not edge:raise HTTPException(404,'Dependency not found')
    source=roadmap.get(db,edge.from_id,user,True);roadmap.check_version(source,data)
    source.version+=1
    roadmap.audit(db,source,user,'dependency_removed',data.reason,{'status':source.status,'dependency':{'from_id':edge.from_id,'to_id':edge.to_id}},{'status':source.status})
    db.delete(edge);commit(db)
