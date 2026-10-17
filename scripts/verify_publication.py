"""Check the publication tree without credentials, inference or external services."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'workshops/switchyard-routing'
PATTERNS=[re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(rb'\b(?:ghp_|gho_|github_pat_|nvapi-)[A-Za-z0-9_\-]{20,}'),
    re.compile(rb'\bsk-(?:proj-|ant-)?[A-Za-z0-9_\-]{24,}'),
    re.compile(rb'\bAKIA[0-9A-Z]{16}\b')]
errors=[];count=0
names=subprocess.check_output(['git','-C',str(ROOT),'ls-files','--cached','--others','--exclude-standard','-z']).decode().split('\0')
for name in sorted(set(filter(None,names))):
    p=ROOT/name
    if not p.is_file():continue
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
for name in ['examples/checkout-support/lightning-gpt-sol/demo.ipynb','examples/checkout-support/lightning-gpt-sol/preview.html','examples/checkout-support/checkout.png','examples/synthetic-incident/demo.ipynb','examples/synthetic-incident/preview.html','examples/ubuntu-support-handover/demo.ipynb']:
    if not (PACKAGE/name).is_file():errors.append(f'Missing workshop asset: {name}')
manifest=PACKAGE/'publication-manifest.json'
if manifest.exists():
    for name,digest in json.loads(manifest.read_text())['files_sha256'].items():
        p=ROOT/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:errors.append(f'Manifest mismatch: {name}')
if errors:raise SystemExit('\n'.join(errors))
print(f'Publication checks passed for {count} files: no recognized secret patterns or credential files; notebooks default offline; pinned assets and manifest verified.')
