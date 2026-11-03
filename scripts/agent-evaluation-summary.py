"""Summarize synthetic pytest evaluations without answers, prompts, IDs or source text."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
data=json.loads(a.input.read_text());groups={}
for case in data['cases']:
 result=case['actual_result'];provider=result.get('provider')
 if provider not in ('deterministic','mocked'):provider='unclassified'
 group=groups.setdefault(provider,{'n':0,'passed':0,'failed':0,'cases':[]});group['n']+=1;group['passed']+=case['outcome']=='passed';group['failed']+=case['outcome']!='passed'
 group['cases'].append({'case':case['case'],'outcome':case['outcome'],'actual_mode':result.get('actual_mode'),'status':result.get('actual_status'),'citation_count':len(result.get('citations',[])),'tool_count':len(result.get('diagnostics',{}).get('tool_names',[]))})
out={'scope':'Existing synthetic deterministic datasets and mocked policy cases; application mode llm is not proof of real inference','pytest_exit_status':data['pytest_exit_status'],'groups':groups,'actual_ollama':{'n':0,'status':'NOT RUN; no runtime/model available'}}
a.output.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{x:v for x,v in g.items() if x!='cases'} for k,g in groups.items()}))
