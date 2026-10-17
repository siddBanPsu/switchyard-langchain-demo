"""Analyze one pinned Super VL/GPT recording without inference calls."""
import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
parser=argparse.ArgumentParser();parser.add_argument('recording',type=Path);args=parser.parse_args()
source=args.recording.resolve();data=json.loads(source.read_text());results=data['results']
assert len(results)==9 and all(r['cost_complete'] for r in results)
for name,h in data['metadata']['source_hashes'].items():
    source_map=json.loads((ROOT/'evidence/source-map.json').read_text())
    measured=ROOT/source_map[name][h]
    assert hashlib.sha256(measured.read_bytes()).hexdigest()==h,name
rates=data['metadata']['rates']['rates']
def ordinary(r):
    return sum((c['usage']['input_tokens']*rates[c['model']]['input_per_million']+c['usage']['output_tokens']*rates[c['model']]['output_per_million'])/1e6 for c in r['calls'])
summary=[]
for arm,label in data['metadata']['arm_labels'].items():
    rows=[r for r in results if r['arm']==arm];assert len(rows)==3
    n=sum(r['passed'] for r in rows);total=sum(r['cost_usd'] for r in rows)
    summary.append(dict(arm=arm,approach=label,accepted=n,attempts=3,mean_cost_usd=total/3,cost_per_accepted=total/n if n else None,
        ordinary_input_mean_usd=sum(ordinary(r) for r in rows)/3,median_seconds=statistics.median(r['elapsed_seconds'] for r in rows),
        calls=sum(len(r['calls']) for r in rows),retries=sum(c['decision_reason']=='validation_retry' for r in rows for c in r['calls'])))
a,b,c=summary
saving=1-c['mean_cost_usd']/a['mean_cost_usd'];neutral=1-c['ordinary_input_mean_usd']/a['ordinary_input_mean_usd']
extra=c['mean_cost_usd']/b['mean_cost_usd']-1
with (HERE/'summary.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(a));w.writeheader();w.writerows(summary)
print(json.dumps(dict(summary=summary,routed_saving_vs_gpt=saving,ordinary_input_saving=neutral,routed_extra_vs_super=extra),indent=2))
lines=['# Super VL + GPT Sol 6.1 on the same visual checkout example','',
    'Fresh matched comparison on 17 October 2026, using the existing TOML gateway endpoint. Same screenshot, source records, prompts, validation and retry limits as the Lightning/GPT experiment. All nine attempts are included.','',
    '| Approach | Accepted | Mean estimated USD/workflow | Cost per accepted report | Median seconds | Calls / retries |',
    '|---|---:|---:|---:|---:|---:|']
for s in summary:
    per=f"${s['cost_per_accepted']:.6f}" if s['cost_per_accepted'] is not None else 'No accepted results'
    lines.append(f"| {s['approach']} | {s['accepted']}/3 | ${s['mean_cost_usd']:.6f} | {per} | {s['median_seconds']:.2f} | {s['calls']} / {s['retries']} |")
lines+=['',f'Routing reduced estimated spend by **{saving:.1%} versus GPT everywhere** using reported caching. At ordinary input rates with cache discounts and write premiums removed, the saving was **{neutral:.1%}** on the same observed token counts. This repricing is a sensitivity calculation, not a separate live trial.', '',
    f'The routed workflow cost **{extra:.1%} more than Super VL alone**. All three arms passed 3/3 without retries. GPT escalation has no demonstrated quality benefit on this fixture. Prefer Super VL alone for the lowest observed spend on this particular case; prefer the previous [Lightning/GPT walkthrough](../lightning-gpt-sol/preview.html) when explaining complementary text and image capabilities.','',
    '| Ordinary input repricing | Mean USD/workflow |','|---|---:|']
for s in summary:lines.append(f"| {s['approach']} | ${s['ordinary_input_mean_usd']:.6f} |")
lines+=['','The authored routing policy is unchanged: actual image or failed-validation retry → GPT, other text → Super VL. Both models support the image. This intentionally holds policy fixed for comparison; it does not establish that GPT is required for this screenshot. Native Switchyard HeaderRoutingConfig dispatches requests. There is no paid judge or learned difficulty classifier.','',
    'Each routed attempt followed Super VL → GPT screenshot reading → Super VL. All nine task attempts completed without retries. Each stage gets at most two attempts. Super VL uses temperature 0 with thinking disabled; GPT uses provider defaults. Each model has the same settings wherever used. The application renders the customer reply from validated integer cents. Nothing is paid, refunded or repaired. Fixture-based validators are evaluation checks, not a general production verifier.','',
    '| Repeat | GPT only USD | Super VL only USD | Routed USD | Accepted (GPT / Super / routed) |','|---|---:|---:|---:|---|']
for n in range(1,4):
    rows=[next(r for r in results if r['repeat']==n and r['arm']==arm) for arm in ['super_only','lightning_only','routed']]
    lines.append(f"| {n} | ${rows[0]['cost_usd']:.7f} | ${rows[1]['cost_usd']:.7f} | ${rows[2]['cost_usd']:.7f} | {' / '.join(str(r['passed']) for r in rows)} |")
lines+=['','## Price basis and limits','',
    '| USD per 1M tokens | Input | Output | Cache read | Cache write |','|---|---:|---:|---:|---:|']
for model in [data['metadata']['models']['efficient'],data['metadata']['models']['capable']]:
    r=rates[model];lines.append(f"| {model.rsplit('/',1)[-1]} | ${r['input_per_million']:.2f} | ${r['output_per_million']:.2f} | ${r['cached_input_per_million']:.2f} | ${r['cache_write_per_million']:.2f} |")
lines+=['',
    'Rates were freshly fetched from the paid-model [OpenRouter catalog](https://openrouter.ai/api/v1/models). [Super VL provider prices](https://openrouter.ai/nvidia/nemotron-3.5-super-vl) now include $0.10 input / $0.40 output / $0.08 cache-read offers; older recordings used a separate $0.15 / $0.50 / $0.02 snapshot. Those historical estimates remain unchanged. [GPT Sol listing](https://openrouter.ai/openai/gpt-6.1-sol). Super VL cache-write price is assumed equal to ordinary input if unpublished.','',
    'Reference prices are applied to reported gateway usage, not actual invoices. Prompt tokens include cached tokens: cache reads and writes are removed from ordinary input to prevent double counting. Runs are shuffled (seed 41), share repeated prompts and may reuse caches warmed by previous experiments. These are three samples of one synthetic case, not independent cold-start trials or a general reliability benchmark.','',
    f'Comparison model spend across all nine attempts: ${sum(r["cost_usd"] for r in results):.7f}. No separate probe or pilot was run for this pair.','',
    '## Inspect and reproduce','',
    f'- [Raw recording](../../../{source.relative_to(ROOT)}): prompts, exact model IDs, usage, messages, source hashes and routing reasons.',
    '- [Model TOML](models.toml), [rates](prices.json), [price snapshot](openrouter-prices-2026-10-17.json), [summary CSV](summary.csv).',
    '- Historical raw arm names are retained: `super_only` means capable GPT-only; `lightning_only` means efficient Super-VL-only. Display labels above use the actual models.',
    '- Validation: 10 existing visual workflow checks passed. All nine reports, evidence IDs, support summaries, model IDs and token ledgers were reviewed; all source hashes matched.',
    '- Shared [workflow](../workflow.py) and [engine](../demo.py) are unchanged by this experiment. All earlier demos and synthetic backups remain available.','',
    'From the workspace root, to make a fresh set of paid calls:','',
    '```sh','.venv/bin/python examples/checkout-support/super-vl-gpt-sol/run.py --allow-paid-calls','```','',
    'To rebuild this report without inference:','', '```sh',f'.venv/bin/python examples/checkout-support/super-vl-gpt-sol/analyze.py {source.relative_to(ROOT)}','```','']
(HERE/'README.md').write_text('\n'.join(lines))
