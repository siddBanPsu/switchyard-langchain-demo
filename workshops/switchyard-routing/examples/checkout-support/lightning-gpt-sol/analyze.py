"""Rebuild this recorded comparison's report and browser replay; makes no API calls."""
import csv
import hashlib
import json
import statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/'recordings/checkout-support/lightning-gpt-sol-final-2026-10-17-20261017T025833913064Z.json'
data=json.loads(SOURCE.read_text());results=data['results'];rates=data['metadata']['rates']['rates']
assert len(results)==9
for name,digest in data['metadata']['source_hashes'].items():
    source_map=json.loads((ROOT/'evidence/source-map.json').read_text())
    measured=ROOT/source_map[name][digest]
    assert hashlib.sha256(measured.read_bytes()).hexdigest()==digest,name
labels={'super_only':'GPT Sol 6.1 only','lightning_only':'Lightning only','routed':'Lightning + GPT via Switchyard'}
def uncached(r):
    return sum((c['usage']['input_tokens']*rates[c['model']]['input_per_million']+c['usage']['output_tokens']*rates[c['model']]['output_per_million'])/1e6 for c in r['calls'])
summary=[]
for arm,label in labels.items():
    rows=[r for r in results if r['arm']==arm]
    assert len(rows)==3 and all(r['cost_complete'] for r in rows)
    total=sum(r['cost_usd'] for r in rows);accepted=sum(r['passed'] for r in rows)
    summary.append(dict(arm=arm,approach=label,accepted=accepted,attempts=3,mean_cost_usd=total/3,
        cost_per_accepted=total/accepted if accepted else None,median_seconds=statistics.median(r['elapsed_seconds'] for r in rows),
        model_calls=sum(len(r['calls']) for r in rows),uncached_mean_usd=sum(uncached(r) for r in rows)/3))
trials=[]
for n in range(1,4):
    a=next(r for r in results if r['arm']=='super_only' and r['repeat']==n)
    b=next(r for r in results if r['arm']=='routed' and r['repeat']==n)
    trials.append(dict(repeat=n,super_usd=a['cost_usd'],combined_usd=b['cost_usd'],saving=1-b['cost_usd']/a['cost_usd']))
saving=1-summary[2]['mean_cost_usd']/summary[0]['mean_cost_usd']
uncached_saving=1-summary[2]['uncached_mean_usd']/summary[0]['uncached_mean_usd']
with (HERE/'summary.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
print(json.dumps(dict(summary=summary,trials=trials,saving=saving,uncached_saving=uncached_saving),indent=2))
lines=['# Lightning + GPT Sol 6.1: the same visual checkout example','',
    f'Fresh matched comparison on 17 October 2026: GPT-only and routed completed **3/3** each. Routing used **{saving:.1%} less estimated model spend** with reported caching, and **{uncached_saving:.1%} less** when all input is repriced at the ordinary input rate. Lightning-only completed 0/3 because it cannot accept the screenshot.','',
    '[Open the workshop notebook](demo.ipynb) or [recorded walkthrough](preview.html). No inference is needed for replay. The original all-NVIDIA walkthrough and synthetic backup are retained.','',
    '| Approach | Accepted | Mean USD/workflow | Cost/accepted, including failures | Median seconds |',
    '|---|---:|---:|---:|---:|']
for s in summary:
    accepted_cost=f"${s['cost_per_accepted']:.6f}" if s['cost_per_accepted'] is not None else 'No accepted results'
    lines.append(f"| {s['approach']} | {s['accepted']}/3 | ${s['mean_cost_usd']:.6f} | {accepted_cost} | {s['median_seconds']:.2f} |")
lines+=['','Lightning-only costs are for failed partial workflows, not a cheaper completed solution. All three reached the image stage, which was blocked locally before sending unsupported input. No failed image inference was observed.','',
    '| Repeat | GPT only USD | Routed USD | Reduction |','|---|---:|---:|---:|']
for t in trials:lines.append(f"| {t['repeat']} | ${t['super_usd']:.7f} | ${t['combined_usd']:.7f} | {t['saving']:.1%} |")
lines+=['','## What ran','',
    'The exact same synthetic checkout screenshot, logs, authoritative payment record, runbook, prompts and validators as the all-NVIDIA comparison. Three fixed stages: extract backend facts, read the actual PNG, reconcile a structured support decision. The app renders the customer reply from validated integer cents. No payment, refund or repair is performed.','',
    'Both GPT-only and routed decisions correctly identify one SGD 118.70 capture, a paid order, misleading failed-payment UI, and the need to avoid Pay again and reconcile the displayed status. All recorded summaries and source IDs were reviewed against the fixture.','',
    'Application policy tags an actual image or a validator-rejected retry as strong; other text is weak. Native Switchyard HeaderRoutingConfig performs dispatch. This is authored capability routing in a fixed workflow, with no paid judge or learned difficulty classifier. The same two-attempt cap applies to every stage and baseline. Validators use labelled fixture facts; this is not a general production verifier for arbitrary screenshots.','',
    'All three routed attempts took Lightning → GPT Sol 6.1 → Lightning, with no retries. GPT-only took three GPT calls. There were 9 calls per successful arm and 3 partial Lightning-only calls. Exact capable alias: `openai/openai/gpt-6.1-sol`; efficient alias: `nvidia/nvidia/nemotron-3.5-lightning`. Both use the existing TOML NVIDIA gateway endpoint and credentials. GPT uses provider defaults; Lightning uses temperature 0 and disabled thinking. Settings are identical for each model wherever that model appears.','',
    '## Prices and caching','',
    '| USD per 1M tokens | Input | Output | Cache read | Cache write |','|---|---:|---:|---:|---:|',
    '| GPT Sol 6.1 | $2.00 | $10.00 | $0.10 | $2.50 |','| Lightning | $0.07 | $0.20 | $0.04 | $0.07 assumed |','',
    'Fetched the paid-model entries from the [OpenRouter catalog](https://openrouter.ai/api/v1/models) on 17 October 2026. [GPT listing](https://openrouter.ai/openai/gpt-6.1-sol). [Lightning listing](https://openrouter.ai/nvidia/nemotron-3.5-lightning). Exact raw model entries, modalities and rates are saved beside this file. These are reference-price estimates applied to reported gateway usage, not actual gateway invoices. Lightning has no published cache-write rate; ordinary input is assumed (no Lightning cache writes were reported).','',
    'Reported cache reads and writes are included in the primary table, with cached tokens removed from ordinary input to avoid double counting. The separate successful vision probe warmed the shared image prompt before this run. Repeats can share caches and ran in shuffled order (seed 41); they are not independent cold-start trials. The first GPT-only backend call reported cache creation, and later GPT backend calls reported reads.','',
    '| Ordinary input repricing, cache discounts and write premiums removed | Mean USD/workflow |','|---|---:|']
for s in summary:lines.append(f"| {s['approach']} | ${s['uncached_mean_usd']:.6f} |")
lines+=['',f'This is a price sensitivity calculation on the same observed token counts, not another live run. At those counts the saving remains {uncached_saving:.1%}. One synthetic case repeated three times cannot establish general accuracy or future savings.','',
    '## Workshop recommendation','',
    f'For the developer/architect audience, use this walkthrough to explain per-step capability routing: cheap text processing plus a model that can read the image. The measured estimate is {saving:.1%} below GPT everywhere. Show the cache-neutral {uncached_saving:.1%} sensitivity alongside it. Explain that this comparison demonstrates workflow routing, not autonomous agent planning or a hard reasoning win.','',
    'The all-NVIDIA version remains the lower absolute-cost option in its separate recording; the bigger percentage here comes from comparing against a more expensive GPT-only baseline. These were separate runs, not a fresh head-to-head four-model benchmark.','',
    '## Reproduce or inspect','',
    f'- [Raw comparison](../../../{SOURCE.relative_to(ROOT)}): all nine attempts, prompts, usage, exact IDs, routing decisions and source hashes.',
    '- [Review and development spend](review.json), [summary CSV](summary.csv), [model TOML](models.toml), [rates](prices.json), [price snapshot](openrouter-prices-2026-10-17.json), [separate vision probe](vision-probe.json).',
    '- [Shared workflow](../workflow.py) and [native engine](../demo.py). Existing NVIDIA results retain their exact prior source copies in `../versions/combined_guarded_demo.py` and `../versions/combined_guarded_workflow.py`.',
    '- Validation: 75 existing tests passed. All original synthetic core files remain unchanged; documentation links were updated.',
    '', 'From the workspace root (makes paid calls):','', '```sh',
    '.venv/bin/python examples/checkout-support/workflow.py --profile-dir examples/checkout-support/lightning-gpt-sol --repeats 3 --phase lightning-gpt-sol --allow-paid-calls',
    '```','',
    'Rebuild this report and replay without model calls: `.venv/bin/python examples/checkout-support/lightning-gpt-sol/analyze.py`. The raw recorder retains the historical arm name `super_only`; this run uses GPT Sol for that capable-only arm. The report and walkthrough label it correctly.','']
(HERE/'README.md').write_text('\n'.join(lines))
# Reuse the already checked layout; replace the pinned data and model-specific claims.
page=(HERE.parent/'lightning-super-vl/preview.html').read_text()
start=page.index('const data=');end=page.index(';\n',start)
payload=dict(summary=summary,trials=trials,results=results,source=str(SOURCE.relative_to(ROOT)))
page=page[:start]+'const data='+json.dumps(payload).replace('</','<\\/')+page[end:]
page=page.replace('Super VL','GPT Sol 6.1').replace('22.7%',f'{saving:.1%}')
page=page.replace('Repeat 1 — validator recovery','Repeat 1 — normal path')
page=page.replace('including the validation retry.','including every call; no validation retries were needed.')
page=page.replace('two requests were blocked before image dispatch because it advertises text input only; one failed a source-record ID check twice before reaching the image.','all three attempts reached the image step and were blocked before dispatch because it advertises text input only.')
page=page.replace('The retry has a cost','Inspect every repeat')
old='Repeat 1 cost more with routing because it needed a GPT Sol 6.1 correction. The combined workflow was slower at the median. The '+f'{saving:.1%}'+' saving is the aggregate—not a promise that every request saves money.'
page=page.replace(old,f'Cache reads and writes affect these estimates. With all input repriced at ordinary rates, the reduction is {uncached_saving:.1%}. These are three repeats of one synthetic case, not a general benchmark.')
page=page.replace('<td>GPT Sol 6.1</td><td>$0.15</td><td>$0.50</td><td>$0.02</td>','<td>GPT Sol 6.1</td><td>$2.00</td><td>$10.00</td><td>$0.10</td>')
page=page.replace('No cache reads/writes were reported in the final comparison.','Reported GPT cache reads/writes are included; cache writes use $2.50/M. A separate vision probe warmed the image cache before the comparison.')
page=page.replace("href='../../'+data.source","href='../../../'+data.source")
page=page.replace('${r.arm} · repeat', '${data.summary.find(s=>s.arm===r.arm).approach} · repeat')
(HERE/'preview.html').write_text(page)
