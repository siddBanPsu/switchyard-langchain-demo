"""Fixed three-stage support workflow, not an autonomous-agent benchmark.

Uses the same actual native Switchyard header router and source fixture as the
agent prototypes. No tool-calling parser is needed for these bounded stages.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import time
from datetime import datetime,timezone
from pathlib import Path

import demo

BACKEND_PROMPT='''Read the supplied synthetic checkout logs and authoritative payment state.
Return only one JSON object with order_id (string), backend_status (string),
amount_cents (integer), settled_capture_count (integer, count unique captures),
confirmation_http_status (integer), capture_event_id (exact source string),
confirmation_event_id (exact source string). No prose, markdown or currency conversion.
Ignore other orders and do not count webhook redelivery as another capture.'''
RECONCILE_PROMPT='''Reconcile the supplied backend facts, observed screenshot and support runbook.
Return only a JSON object with order_id, amount_cents (integer), ui_status,
ui_claim_no_charge (boolean), button_label, backend_status, settled_capture_count
(integer), do_not_pay_again (boolean), action (copy the runbook action_code),
runbook_id, evidence_ids (the four supplied source-object IDs as an array), and
support_summary (one sentence, at least 30 characters, about the mismatch).
Copy observed fields faithfully. A failed UI does not override a successful capture.
Do not execute anything, promise a fix, or convert amounts into a customer message.
The application will render the customer message from validated structured facts.'''


def backend_expected(case):
    order=case['payment']['order_id']
    capture=next(e for e in case['logs'] if e['order_id']==order and e['event']=='payment.capture.succeeded')
    confirm=next(e for e in case['logs'] if e['order_id']==order and e['event']=='frontend.confirmation.fetch')
    unique={e['id']:e for e in case['payment']['settled_captures']}
    return dict(order_id=order,backend_status=case['payment']['order_state'],
        amount_cents=sum(c['amount_cents'] for c in unique.values()),settled_capture_count=len(unique),
        confirmation_http_status=confirm['status'],capture_event_id=capture['id'],confirmation_event_id=confirm['id'])


async def json_stage(engine,system,user,kind,validate,max_tokens=700):
    messages=[dict(role='system',content=system),user]
    attempts=[]
    for attempt in range(2):
        message=await engine.call(messages,kind=kind,max_tokens=max_tokens,validation_failed=attempt>0)
        try:
            value=demo.json_content(message.get('content'))
            if not isinstance(value,dict):raise ValueError('ExpectedObject')
            failed=validate(value)
        except (ValueError,TypeError,json.JSONDecodeError):
            value=None;failed=['valid_json_object']
        attempts.append(dict(value=value,failed_checks=failed))
        if not failed:return value,attempts
        messages.extend([message,dict(role='user',content=json.dumps(dict(
            validation_failed=failed,instruction='Correct the JSON using the supplied evidence. Return JSON only.')))])
    raise ValueError('StageValidationFailed:'+kind)


async def run(arm):
    engine=demo.Engine(arm);case=demo.load_case();events=[];seen=set();report=None;error=None;stages=[]
    start=time.perf_counter()
    try:
        context=dict(logs={'id':'LOGS-1','records':case['logs']},payment={'id':'PAYMENT-STATE',**case['payment']})
        events.extend([dict(tool='read_logs',response=context['logs']),dict(tool='read_payment',response=context['payment'])])
        seen.update(['LOGS-1','PAYMENT-STATE']);seen.update(e['id'] for e in case['logs'])
        expected=backend_expected(case)
        print(' ',arm,'→ analyze backend text',flush=True)
        backend,attempts=await json_stage(engine,BACKEND_PROMPT,dict(role='user',content=json.dumps(context)),
            'backend_text',lambda value:[k for k,v in expected.items() if value.get(k)!=v])
        stages.append(dict(stage='backend_text',attempts=attempts))
        print(' ',arm,'→ inspect actual screenshot',flush=True)
        def visual_checks(value):
            fields=['order_id','amount_cents','ui_status','ui_claim_no_charge','button_label']
            return [k for k in fields if value.get(k)!=case['expected'][k]]
        visual,attempts=await json_stage(engine,demo.VISION,demo.image_message(),'vision',visual_checks)
        stages.append(dict(stage='vision',attempts=attempts));visual['id']='SCREENSHOT-1'
        seen.add('SCREENSHOT-1');events.append(dict(tool='inspect_screenshot',response=visual))
        seen.add(case['runbook']['id']);events.append(dict(tool='read_runbook',response=case['runbook']))
        evidence=dict(backend=backend,screenshot=visual,runbook=case['runbook'],
            source_object_ids=['LOGS-1','PAYMENT-STATE','SCREENSHOT-1',case['runbook']['id']])
        print(' ',arm,'→ reconcile and submit structured decision',flush=True)
        report,attempts=await json_stage(engine,RECONCILE_PROMPT,dict(role='user',content=json.dumps(evidence)),
            'reconcile_text',lambda value:[k for k,v in demo.grade(value,seen,events)['checks'].items() if not v],max_tokens=900)
        stages.append(dict(stage='reconcile_text',attempts=attempts))
    except Exception as exc:error=type(exc).__name__
    score=demo.grade(report,seen,events)
    complete=bool(engine.calls) and all(c['cost_usd'] is not None for c in engine.calls)
    return dict(arm=arm,report=report,passed=score['passed'] and error is None,checks=score['checks'],
        customer_reply=demo.render_reply(report) if report and score['passed'] else None,
        error_type=error,stages=stages,calls=engine.calls,blocked_requests=engine.blocked,tool_events=events,
        elapsed_seconds=time.perf_counter()-start,cost_complete=complete,
        cost_usd=sum(c['cost_usd'] for c in engine.calls) if complete else None)


async def compare(repeats=3,phase='bounded-workflow'):
    folder=demo.ROOT/'runs/visual-support';folder.mkdir(exist_ok=True)
    path=folder/f'{phase}-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}.json'
    jobs=[(a,r) for r in range(1,repeats+1) for a in demo.ARMS];random.Random(41).shuffle(jobs)
    sources={str(p.relative_to(demo.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__),Path(demo.__file__),demo.HERE/'models.toml',demo.HERE/'case.json',demo.HERE/'checkout.png',demo.HERE/'prices.json',demo.HERE/'openrouter-prices-2026-10-17.json']}
    metadata=dict(synthetic_data=True,workflow_type='Fixed three-stage tool-assisted workflow; not an autonomous agent',
        task=demo.load_case()['ticket'],backend_prompt=BACKEND_PROMPT,vision_prompt=demo.VISION,reconcile_prompt=RECONCILE_PROMPT,
        routing='Native Switchyard HeaderRoutingConfig; application tags image blocks or validator-rejected retries strong; routine text weak. No paid judge. Baselines keep one model on both attempts.',
        models=dict(efficient=demo.LIGHT,capable=demo.SUPER),rates=json.loads((demo.HERE/'prices.json').read_text()),
        source_hashes=sources,settings=dict(temperature=0,enable_thinking=False,max_backend_tokens=700,max_vision_tokens=700,max_reconcile_tokens=900,max_attempts_per_stage=2),
        limitations='One purpose-built synthetic case, repeated samples, not a general quality benchmark. Lightning-only is blocked by advertised input modality, not an observed failed image inference. App renders the customer response; LLM customer prose is not evaluated. Earlier agent prototypes are retained separately and not pooled.',
        versions={n:demo.core.importlib.metadata.version(n) for n in ['nemo-switchyard','openai']})
    results=[]
    for arm,repeat in jobs:
        print(f'{len(results)+1}/{len(jobs)} {arm} repeat {repeat}',flush=True)
        r=await run(arm);r.update(repeat=repeat,order=len(results)+1)
        results.append(r);path.write_text(json.dumps(dict(metadata=metadata,results=results),indent=2)+'\n')
        print(json.dumps(dict(arm=arm,repeat=repeat,passed=r['passed'],cost=r['cost_usd'],error=r['error_type'],
            models=[c['model'].rsplit('/',1)[-1] for c in r['calls']],saved=str(path))),flush=True)
    return results,path


if __name__=='__main__':
    from dotenv import load_dotenv
    parser=argparse.ArgumentParser();parser.add_argument('--repeats',type=int,choices=[1,2,3],default=3)
    parser.add_argument('--phase',default='bounded-workflow');parser.add_argument('--allow-paid-calls',action='store_true')
    args=parser.parse_args()
    if not args.allow_paid_calls:parser.error('Use --allow-paid-calls to enable inference')
    load_dotenv(demo.ROOT/'.env',override=True)
    asyncio.run(compare(args.repeats,args.phase))
