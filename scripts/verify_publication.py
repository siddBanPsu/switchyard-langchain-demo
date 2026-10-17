"""Check the publication tree without credentials, inference or external services."""
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'workshops/switchyard-routing'
PATTERNS=[re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(rb'\b(?:ghp_|gho_|github_pat_|nvapi-)[A-Za-z0-9_\-]{20,}'),
    re.compile(rb'\bsk-(?:proj-|ant-)?[A-Za-z0-9_\-]{24,}'),
    re.compile(rb'\bAKIA[0-9A-Z]{16}\b')]
errors=[];count=0
for p in ROOT.rglob('*'):
    if not p.is_file() or any(x in p.parts for x in ['.git','.venv','__pycache__','.pytest_cache']):continue
    rel=p.relative_to(ROOT);data=p.read_bytes();count+=1
    if (p.name=='.env' or p.name.startswith('.env.')) and p.name!='.env.example':errors.append(f'Credential file: {rel}')
    if p.suffix in ['.pem','.key','.p12','.pfx']:errors.append(f'Key file: {rel}')
    if any(pattern.search(data) for pattern in PATTERNS):errors.append(f'Possible credential: {rel}')
    if re.search(rb'/Users/[A-Za-z0-9_.-]+/',data):errors.append(f'Local home path: {rel}')
    if p.suffix=='.ipynb':
        nb=json.loads(data)
        for c in nb['cells']:
            if c['cell_type']!='code':continue
            if c.get('outputs') or c.get('execution_count') is not None:errors.append(f'Saved notebook output: {rel}')
            source=''.join(c['source'])
            if re.search(r'^(?:ALLOW_PAID_CALLS|ENABLE_LANGSMITH)\s*=\s*True',source,re.M):errors.append(f'Online default: {rel}')
# Keep all recorded walkthrough assets available without the research workspace.
for name in ['archive/visual-support/gpt-sol/preview.html','archive/visual-support/checkout.png','incident_routing_demo.ipynb','incident_routing_l200_preview.html','ubuntu_handover_super_vl.ipynb']:
    if not (PACKAGE/name).is_file():errors.append(f'Missing workshop asset: {name}')
manifest=PACKAGE/'publication-manifest.json'
if manifest.exists():
    for name,digest in json.loads(manifest.read_text())['files_sha256'].items():
        p=ROOT/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:errors.append(f'Manifest mismatch: {name}')
if errors:raise SystemExit('\n'.join(errors))
print(f'Publication checks passed for {count} files: no recognized secret patterns or credential files; notebooks default offline; pinned assets and manifest verified.')
