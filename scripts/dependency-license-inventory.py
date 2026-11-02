"""Inventory local installed backend dependency metadata and the frontend lockfile.
Not a legal or vulnerability compliance scanner. Never reads environment files.
"""
import json
from pathlib import Path
from importlib.metadata import distribution
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

root = Path(__file__).resolve().parents[1]
pending = []
for name in ['requirements-app.txt','requirements-payments.txt','requirements-dev.txt']:
    for line in (root/'backend'/name).read_text().splitlines():
        if line.strip() and not line.startswith(('#','-r')):
            pending.append(Requirement(line))
seen = {}; python = []
while pending:
    req = pending.pop(); name = canonicalize_name(req.name)
    extras = set(req.extras) | {''}
    if name in seen and extras <= seen[name]: continue
    first = name not in seen; seen.setdefault(name,set()).update(extras)
    d = distribution(name); m = d.metadata
    if first:
        classifiers = [c for c in m.get_all('Classifier',[]) if c.startswith('License ::')]
        python.append({'name':m['Name'],'version':d.version,'license_expression':m.get('License-Expression'),
            'license_metadata':(m.get('License') or '').splitlines()[0:1], 'license_classifiers':classifiers,
            'source':'installed distribution metadata; inspect bundled and upstream license notices before release'})
    for dependency in m.get_all('Requires-Dist',[]):
        child = Requirement(dependency)
        if child.marker is None or any(child.marker.evaluate({'extra':extra}) for extra in seen[name]):pending.append(child)
lock = json.loads((root/'frontend/package-lock.json').read_text())
node = [{'path':name,'version':item.get('version'),'license':item.get('license','UNDECLARED: inspect package license'),
         'dev':item.get('dev',False)} for name,item in lock['packages'].items() if name]
print(json.dumps({'scope':'Web runtime/test dependency closure and all frontend lockfile entries; legacy scientific requirements are not shipped.',
    'python':sorted(python,key=lambda item:item['name'].lower()),'npm':node},indent=2))
