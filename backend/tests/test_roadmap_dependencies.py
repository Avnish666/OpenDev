from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select
from app.models.roadmap import ProjectRoadmapMilestone as Milestone
from test_roadmap import create, ok, REASON
from test_accountability import ac


def edge(ac,source,target,version=1):
    return ac.client.post(f'/api/projects/{ac.p.id}/roadmap/dependencies',json={'from_id':source['id'],'to_id':target['id'],'expected_version':version,'reason':REASON})


def test_dependencies_no_scheduling_and_audited_delete(ac):
    a,b=create(ac),create(ac)
    link=ok(edge(ac,a,b),201)
    for mid in (a['id'],b['id']):
        row=ac.db.get(Milestone,mid);assert row.status=='planned' and row.planned_start_date.isoformat()=='2026-11-01'
    history=ok(ac.client.get(f"/api/roadmap/{a['id']}/history"))
    assert history[0]['action']=='dependency_linked'
    result=ac.client.request('DELETE',f"/api/projects/{ac.p.id}/roadmap/dependencies/{link['id']}",json={'expected_version':2,'reason':REASON})
    assert result.status_code==204,result.text
    assert ok(ac.client.get(f'/api/projects/{ac.p.id}/roadmap/dependencies'))['total']==0
    assert ok(ac.client.get(f"/api/roadmap/{a['id']}/history"))[0]['action']=='dependency_removed'


def test_dependency_cycles_duplicates_and_foreign_project(ac):
    a,b,c=create(ac),create(ac),create(ac)
    ok(edge(ac,a,b),201);ok(edge(ac,b,c),201)
    assert edge(ac,c,a).status_code==422
    assert edge(ac,c,c).status_code==422
    assert edge(ac,a,b,version=2).status_code==409
    other=Milestone(project_id=ac.other.id,created_by=ac.users[3].id,title='Other',description='Other',deliverable_description='Other deliverable',planned_start_date=ac.e.expense_date,planned_end_date=ac.e.expense_date,status='planned',version=1,display_order=0)
    ac.db.add(other);ac.db.commit()
    assert edge(ac,a,{'id':other.id},version=2).status_code==422


def test_dependency_authorization_visibility_csrf(ac):
    a,b=create(ac),create(ac)
    ac.identity[0]=ac.users[2];assert edge(ac,a,b).status_code==403
    ac.identity[0]=ac.users[0]
    assert ac.client.post(f'/api/projects/{ac.p.id}/roadmap/dependencies',json={'from_id':a['id'],'to_id':b['id'],'expected_version':1,'reason':REASON},headers={'Origin':'https://evil.invalid'}).status_code==403
    ok(edge(ac,a,b),201);ac.identity[0]=None
    assert ok(ac.client.get(f'/api/projects/{ac.p.id}/roadmap/dependencies'))['total']==1
    ac.p.status='draft';ac.db.commit()
    assert ac.client.get(f'/api/projects/{ac.p.id}/roadmap/dependencies').status_code==404


def test_concurrent_dependency_cycle_cannot_commit(ac):
    a,b=create(ac),create(ac)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(edge,ac,a,b);second=pool.submit(edge,ac,b,a)
        assert sorted([first.result().status_code,second.result().status_code])==[201,422]
