"""Build this single-run report using the common judge-results analyzer."""
from pathlib import Path
import runpy,sys
HERE=Path(__file__).resolve().parent
sys.argv.extend(['--profile-dir',str(HERE)])
runpy.run_path(str(HERE.parent/'lightning-gpt-sol-judge/analyze.py'),run_name='__main__')
