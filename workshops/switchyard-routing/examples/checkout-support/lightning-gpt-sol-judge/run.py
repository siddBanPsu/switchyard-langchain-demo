"""Matched Lightning-judge comparison; all judge calls counted."""
import argparse
import asyncio
import hashlib
import json
import random
import sys
from datetime import datetime,timezone
from pathlib import Path
from dotenv import load_dotenv

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import workflow
import demo
from judge import JudgeEngine,JUDGE_PROMPT

BACKEND_PROMPT=workflow.BACKEND_PROMPT+'\nFor capture_event_id and confirmation_event_id, copy the id field of the corresponding entry in logs.records. These are LOG RECORD IDs, not capture object IDs in payment.settled_captures and not event type names. The capture_event_id belongs to the log record whose event is payment.capture.succeeded; confirmation_event_id belongs to the log record whose event is frontend.confirmation.fetch.'

async def compare():
    config=demo.core.tomllib.loads((HERE/'models.toml').read_text())
    jobs=[(a,r) for r in range(1,4) for a in demo.ARMS];random.Random(41).shuffle(jobs)
    folder=demo.ROOT/'runs/checkout-support';folder.mkdir(parents=True,exist_ok=True)
    path=folder/f'lightning-gpt-sol-judge-v3-2026-10-17-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}.json'
    files=[Path(__file__),HERE/'judge.py',Path(workflow.__file__),Path(demo.__file__),HERE/'models.toml',HERE/'prices.json',HERE/'openrouter-prices-2026-10-17.json',demo.HERE/'case.json',demo.HERE/'checkout.png']
    metadata=dict(synthetic_data=True,workflow_type='Same fixed three-stage workflow, not an autonomous agent',
        task=demo.load_case()['ticket'],backend_prompt=BACKEND_PROMPT,vision_prompt=demo.VISION,reconcile_prompt=workflow.RECONCILE_PROMPT,
        models={role:config['roles'][role]['model_id'] for role in ['efficient','capable']},
        arm_labels=dict(super_only='GPT Sol 6.1 only',lightning_only='Lightning only',routed='Lightning judge + routed executors'),
        routing='Switchyard built-in llm_task_classifier: Lightning forecasts efficient-stage success; threshold 0.75. Selected executor receives original payload via native dispatch. No image-to-GPT rule. Deterministic fixture validators still grade and permit one retry.',
        judge_prompt=JUDGE_PROMPT,
        rates=json.loads((HERE/'prices.json').read_text()),
        source_hashes={str(p.relative_to(demo.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        settings=dict(shuffle_seed=41,max_attempts_per_stage=2,max_backend_tokens=700,max_vision_tokens=700,max_reconcile_tokens=900,generation='NVIDIA temperature 0, disabled thinking; GPT provider defaults. Same per-model settings in every arm.'),
        limitations='One synthetic case repeated three times. Fixed stage workflow, LLM routing, not autonomous planning. Judge sees text and attachment metadata, not pixels or fixture answers. App renders customer reply. Cache state can carry across repeats and previous experiments. Existing pinned reference prices retained to compare routing methods; not current prices or invoices.',
        versions={n:demo.core.importlib.metadata.version(n) for n in ['nemo-switchyard','openai']})
    results=[]
    for arm,repeat in jobs:
        print(f'{len(results)+1}/9 {metadata["arm_labels"][arm]} repeat {repeat}',flush=True)
        r=await workflow.run(arm,profile_dir=HERE,engine_factory=JudgeEngine,backend_prompt=BACKEND_PROMPT);r.update(repeat=repeat,order=len(results)+1)
        results.append(r);path.write_text(json.dumps(dict(metadata=metadata,results=results),indent=2)+'\n')
        print(json.dumps(dict(arm=arm,repeat=repeat,passed=r['passed'],cost=r['cost_usd'],error=r['error_type'],saved=str(path))),flush=True)
    return path

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--allow-paid-calls',action='store_true');args=parser.parse_args()
    if not args.allow_paid_calls:parser.error('Use --allow-paid-calls to enable inference')
    load_dotenv(demo.ROOT/'.env',override=True)
    asyncio.run(compare())
