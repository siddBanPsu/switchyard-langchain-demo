# Lightning + GPT Sol 6.1: the same visual checkout example

Fresh matched comparison on 17 October 2026: GPT-only and routed completed **3/3** each. Routing used **85.7% less estimated model spend** with reported caching, and **72.3% less** when all input is repriced at the ordinary input rate. Lightning-only completed 0/3 because it cannot accept the screenshot.

[Open the recorded walkthrough](preview.html). No inference is needed for replay. The original all-NVIDIA walkthrough and synthetic backup are retained.

| Approach | Accepted | Mean USD/workflow | Cost/accepted, including failures | Median seconds |
|---|---:|---:|---:|---:|
| GPT Sol 6.1 only | 3/3 | $0.005893 | $0.005893 | 9.15 |
| Lightning only | 0/3 | $0.000202 | No accepted results | 1.23 |
| Lightning + GPT via Switchyard | 3/3 | $0.000845 | $0.000845 | 7.68 |

Lightning-only costs are for failed partial workflows, not a cheaper completed solution. All three reached the image stage, which was blocked locally before sending unsupported input. No failed image inference was observed.

| Repeat | GPT only USD | Routed USD | Reduction |
|---|---:|---:|---:|
| 1 | $0.0092405 | $0.0008462 | 90.8% |
| 2 | $0.0041337 | $0.0008448 | 79.6% |
| 3 | $0.0043037 | $0.0008448 | 80.4% |

## What ran

The exact same synthetic checkout screenshot, logs, authoritative payment record, runbook, prompts and validators as the all-NVIDIA comparison. Three fixed stages: extract backend facts, read the actual PNG, reconcile a structured support decision. The app renders the customer reply from validated integer cents. No payment, refund or repair is performed.

Both GPT-only and routed decisions correctly identify one SGD 118.70 capture, a paid order, misleading failed-payment UI, and the need to avoid Pay again and reconcile the displayed status. All recorded summaries and source IDs were reviewed against the fixture.

Application policy tags an actual image or a validator-rejected retry as strong; other text is weak. Native Switchyard HeaderRoutingConfig performs dispatch. This is authored capability routing in a fixed workflow, with no paid judge or learned difficulty classifier. The same two-attempt cap applies to every stage and baseline. Validators use labelled fixture facts; this is not a general production verifier for arbitrary screenshots.

All three routed attempts took Lightning → GPT Sol 6.1 → Lightning, with no retries. GPT-only took three GPT calls. There were 9 calls per successful arm and 3 partial Lightning-only calls. Exact capable alias: `openai/openai/gpt-6.1-sol`; efficient alias: `nvidia/nvidia/nemotron-3.5-lightning`. Both use the existing TOML NVIDIA gateway endpoint and credentials. GPT uses provider defaults; Lightning uses temperature 0 and disabled thinking. Settings are identical for each model wherever that model appears.

## Prices and caching

| USD per 1M tokens | Input | Output | Cache read | Cache write |
|---|---:|---:|---:|---:|
| GPT Sol 6.1 | $2.00 | $10.00 | $0.10 | $2.50 |
| Lightning | $0.07 | $0.20 | $0.04 | $0.07 assumed |

Fetched the paid-model entries from the [OpenRouter catalog](https://openrouter.ai/api/v1/models) on 17 October 2026. [GPT listing](https://openrouter.ai/openai/gpt-6.1-sol). [Lightning listing](https://openrouter.ai/nvidia/nemotron-3.5-lightning). Exact raw model entries, modalities and rates are saved beside this file. These are reference-price estimates applied to reported gateway usage, not actual gateway invoices. Lightning has no published cache-write rate; ordinary input is assumed (no Lightning cache writes were reported).

Reported cache reads and writes are included in the primary table, with cached tokens removed from ordinary input to avoid double counting. The separate successful vision probe warmed the shared image prompt before this run. Repeats can share caches and ran in shuffled order (seed 41); they are not independent cold-start trials. The first GPT-only backend call reported cache creation, and later GPT backend calls reported reads.

| Ordinary input repricing, cache discounts and write premiums removed | Mean USD/workflow |
|---|---:|
| GPT Sol 6.1 only | $0.010223 |
| Lightning only | $0.000202 |
| Lightning + GPT via Switchyard | $0.002831 |

This is a price sensitivity calculation on the same observed token counts, not another live run. At those counts the saving remains 72.3%. One synthetic case repeated three times cannot establish general accuracy or future savings.

## Workshop recommendation

For the developer/architect audience, use this walkthrough to explain per-step capability routing: cheap text processing plus a model that can read the image. The measured estimate is 85.7% below GPT everywhere. Show the cache-neutral 72.3% sensitivity alongside it. Explain that this comparison demonstrates workflow routing, not autonomous agent planning or a hard reasoning win.

The all-NVIDIA version remains the lower absolute-cost option in its separate recording; the bigger percentage here comes from comparing against a more expensive GPT-only baseline. These were separate runs, not a fresh head-to-head four-model benchmark.

## Reproduce or inspect

- [Raw comparison](../../../recordings/checkout-support/lightning-gpt-sol-final-2026-10-17-20261017T025833913064Z.json): all nine attempts, prompts, usage, exact IDs, routing decisions and source hashes.
- [Review and development spend](review.json), [summary CSV](summary.csv), [model TOML](models.toml), [rates](prices.json), [price snapshot](openrouter-prices-2026-10-17.json), [separate vision probe](vision-probe.json).
- [Shared workflow](../workflow.py) and [native engine](../demo.py). Existing NVIDIA results retain their exact prior source copies in `../versions/combined_guarded_demo.py` and `../versions/combined_guarded_workflow.py`.
- Validation: 75 existing tests passed. All original synthetic core files remain unchanged; documentation links were updated.

From the workspace root (makes paid calls):

```sh
.venv/bin/python examples/checkout-support/workflow.py --profile-dir examples/checkout-support/lightning-gpt-sol --repeats 3 --phase lightning-gpt-sol --allow-paid-calls
```

Rebuild this report and replay without model calls: `.venv/bin/python examples/checkout-support/lightning-gpt-sol/analyze.py`. The raw recorder retains the historical arm name `super_only`; this run uses GPT Sol for that capable-only arm. The report and walkthrough label it correctly.
