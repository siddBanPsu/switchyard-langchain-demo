"""Execute the named offline notebooks in memory, from their own folders."""
import argparse
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]/'workshops/switchyard-routing/examples'
parser=argparse.ArgumentParser();parser.add_argument('names',nargs='*');args=parser.parse_args()
names=args.names or ['synthetic-incident/demo.ipynb','synthetic-incident/advanced.ipynb','ubuntu-support-handover/demo.ipynb']
for name in names:
    path=ROOT/name
    print('Offline notebook replay:',name,flush=True)
    nb=nbformat.read(path,as_version=4)
    NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(path.parent)}}).execute()
    print('PASS:',name,flush=True)
