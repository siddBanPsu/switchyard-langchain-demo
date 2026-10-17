"""Rebuild judge-inclusive results without inference."""
import argparse,csv,hashlib,json,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
p=argparse.ArgumentParser();p.add_argument('recording',type=Path);args=p.parse_args()
source=args.recording.resolve();d=json.loads(source.read_text());results=d['results'];assert len(results)==9
rates=d['metadata']['rates']['rates']
def ordinary(r):return sum((c['usage']['input_tokens']*rates[c['model']]['input_per_million']+c['usage']['output_tokens']*rates[c['model']]['output_per_million'])/1e6 for c in r['calls'])
rows=[]
for arm,label in d['metadata']['arm_labels'].items():
 group=[r for r in results if r['arm']==arm];assert len(group)==3 and all(r['cost_complete'] for r in group)
 accepted=sum(r['passed'] for r in group);total=sum(ordinary(r) for r in group)
 rows.append(dict(arm=arm,approach=label,accepted=accepted,attempts=3,mean_usd_no_cache=total/3,
    per_accepted_usd_no_cache=total/accepted if accepted else None,median_seconds=statistics.median(r['elapsed_seconds'] for r in group),
    judge_calls=sum(c['kind']=='routing_judge' for r in group for c in r['calls']),
    executor_calls=sum(c['kind']!='routing_judge' for r in group for c in r['calls']),
    mean_usd_reported_cache=sum(r['cost_usd'] for r in group)/3))
with (HERE/'summary.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
a,b,c=rows;saving=1-c['mean_usd_no_cache']/a['mean_usd_no_cache']
complete=a['accepted']==c['accepted']==3
lines=['# Checkout support: Lightning as judge and efficient executor','',
    '**Lightning now decides the model through Switchyard’s built-in `llm_task_classifier`.** It forecasts success on the next stage; Switchyard selects Lightning at `p_solve >= 0.75`, otherwise GPT Sol 6.1. The same fixed three-stage task is retained.','',
    f'**{saving:.1%} lower estimated model cost**, excluding cache discounts and write premiums, including every judge call.' if complete else '**Routing did not complete all attempts. Do not present partial-workflow spending as a successful savings result.**','',
    '[Workshop notebook](demo.ipynb). It defaults to replaying the final saved comparison, with no API calls. The earlier [rule-based notebook](../lightning-gpt-sol/demo.ipynb) is retained as a separate backup.','',
    '| Approach | Accepted | Mean USD/workflow, no cache effects | USD/accepted including failures | Median seconds | Judge / executor calls |','|---|---:|---:|---:|---:|---:|']
for r in rows:
 per=f"${r['per_accepted_usd_no_cache']:.6f}" if r['per_accepted_usd_no_cache'] is not None else 'No accepted results'
 lines.append(f"| {r['approach']} | {r['accepted']}/3 | ${r['mean_usd_no_cache']:.6f} | {per} | {r['median_seconds']:.2f} | {r['judge_calls']} / {r['executor_calls']} |")
lines+=['','## Who does what','',
    '- Lightning judge sees the actual task text, declared model capabilities, attachment metadata and any rejection feedback. It does not see image pixels or fixture answers. The attachment metadata is not OCR.',
    '- The built-in Switchyard task classifier applies the threshold to the returned forecast and invokes the selected executor adapter.',
    '- That executor receives the original request. Images are sent unchanged through native Switchyard dispatch, bypassing the installed LangChain adapter’s text-only content mapper.',
    '- Python validators still check labelled-fixture outputs. They are evaluators, not routing judges. A retry is judged again by Lightning; application code does not force a different model after rejection.',
    '- A wrong choice of text-only Lightning for an image is blocked and counted as a failed task. Invalid classifier output follows Switchyard’s capable fallback; it is not a successful judge decision.',
    '- All judge and executor requests share one cost ledger, including failed calls. No paid model judge is used by either single-model baseline.','',
    '## Actual judge decisions','', '| Repeat | Stage | Forecast p_solve | Target | Crux |','|---|---|---:|---|---|']
for r in sorted([r for r in results if r['arm']=='routed'],key=lambda r:r['repeat']):
 for j in r['judge_decisions']:
  v=j.get('verdict') or {};crux=str(v.get('crux','Invalid verdict')).replace('|','/')
  lines.append(f"| {r['repeat']} | {j['stage']} | {v.get('p_solve','unknown')} | {'Lightning' if j['selected_tier']=='weak' else 'GPT Sol'} | {crux} |")
lines+=['','## Pricing and scope','',
    'The primary estimate reprices observed input/output tokens at the pinned reference prices: Lightning $0.07/$0.20 per million, GPT Sol $2/$10 per million. Cache read discounts and cache write premiums are removed from both sides. These are model-cost estimates, not invoices or a new cold-cache run. Judge tokens are included.','',
    '<details><summary>Technical detail: reported cache-adjusted estimates</summary>','',
    '| Approach | Mean estimated USD/workflow |','|---|---:|']
for r in rows:lines.append(f"| {r['approach']} | ${r['mean_usd_reported_cache']:.6f} |")
lines+=['','These secondary estimates apply the saved cache read/write rates to reported gateway usage. Cache state carries across repeats and earlier experiments; use the no-cache-effects estimate for the workshop headline.','', '</details>','',
    'One synthetic fixture repeated three times does not establish general judge calibration, reliability or future savings. This is LLM-based routing within a fixed workflow, not autonomous agent planning. App-rendered customer replies use validated cents and perform no payment, refund or repair.','',
    '## Earlier attempts retained','',
    'The first comparison accepted 2/3 routed tasks: Lightning was overconfident after a source-ID rejection and selected itself again. A first clarification of record IDs versus event names still confused log record IDs with payment capture object IDs and accepted 0/3 routed tasks. The final contract explicitly identifies `logs.records[].id`; it is applied equally to all fresh baselines. Judge prompt and threshold are unchanged. Earlier runs are separate comparisons and are not pooled into final results.','',
    f'[Final raw recording](../../../{source.relative_to(ROOT)}) · [Summary](summary.csv) · [Model profile](models.toml) · [Judge implementation](judge.py) · [Shared workflow](../workflow.py).','',
    'From the workshop folder, to run a fresh paid comparison:','', '```sh','python examples/checkout-support/lightning-gpt-sol-judge/run.py --allow-paid-calls','```','']
development=sorted((ROOT/'recordings/checkout-support').glob('lightning-gpt-sol-judge-*.json'))
lines+=['','## Development spend','', '| Recording | Attempts | Estimated USD with reported caches |','|---|---:|---:|']
for path in development:
    trial=json.loads(path.read_text());lines.append(f"| {path.name} | {len(trial['results'])} | ${sum(r['cost_usd'] for r in trial['results']):.6f} |")
lines+=['','Development comparisons are retained separately, not pooled into the final savings headline.','']
(HERE/'README.md').write_text('\n'.join(lines));print(json.dumps(dict(rows=rows,saving=saving,all_comparable_complete=complete),indent=2))
