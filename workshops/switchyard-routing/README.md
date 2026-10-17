# Switchyard routing workshop

Start with [Checkout support: Lightning + GPT Sol 6.1](examples/checkout-support/lightning-gpt-sol/preview.html). A customer sees “Payment failed” although the backend has charged their card. Should they press Pay again?

| Named example | Open | Role |
|---|---|---|
| Checkout support — Lightning + GPT Sol 6.1 | [Walkthrough](examples/checkout-support/lightning-gpt-sol/preview.html) · [Findings](examples/checkout-support/lightning-gpt-sol/README.md) | Selected workshop presentation |
| Checkout support — Lightning + Super VL | [Walkthrough](examples/checkout-support/lightning-super-vl/preview.html) · [Findings](examples/checkout-support/lightning-super-vl/README.md) | All-NVIDIA comparison |
| Checkout support — Super VL + GPT Sol 6.1 | [Findings](examples/checkout-support/super-vl-gpt-sol/README.md) | Shows Super VL alone is enough for this fixture |
| Synthetic incident | [Notebook](examples/synthetic-incident/demo.ipynb) · [Preview](examples/synthetic-incident/preview.html) | Original fallback; defaults to offline rehearsal |
| Ubuntu support handover | [Notebook](examples/ubuntu-support-handover/demo.ipynb) · [Preview](examples/ubuntu-support-handover/preview.html) · [Findings](examples/ubuntu-support-handover/README.md) | Real 79-message conversation; defaults to recorded replay |

## Selected demo results

| Approach | Accepted | Mean estimated USD/workflow | Median seconds |
|---|---:|---:|---:|
| GPT Sol 6.1 only | 3/3 | $0.005893 | 9.15 |
| Lightning only | 0/3 | $0.000202, partial workflow | 1.23 |
| Lightning + GPT via Switchyard | 3/3 | $0.000845 | 7.68 |

Routing used **85.7% less estimated spend** versus GPT everywhere with reported caching, or **72.3% less** when all input is repriced at ordinary rates. These estimates use the pinned OpenRouter snapshot and gateway token usage, not invoices or a current-price quote. The image prompt was warmed by a separate probe. Repricing uses the same token counts and is not another live run.

This is a fixed three-stage workflow. Application policy tags actual images or validator-rejected retries as capable, and routine text as efficient; native Switchyard header routing dispatches requests. There is no paid judge or learned difficulty classifier. All routed attempts followed Lightning → GPT → Lightning without retries. Lightning-only was blocked before image dispatch because it supports text input only; its partial cost is not a completed solution. Three repeats of one labelled synthetic case do not establish general reliability.

## Five-minute presentation

1. Show the failed-payment screenshot and ask whether the customer should pay again.
2. Show one settled SGD 118.70 capture, a paid order, a duplicate webhook and the HTTP 504 confirmation request.
3. Inspect the recorded route: Lightning extracts backend facts, GPT reads the image, Lightning reconciles the structured decision. Select another repeat to inspect the full recording.
4. Compare all three baselines and show both cost calculations, including cache effects.
5. Explain the decision: do not pay again; reconcile displayed order status with the existing payment. The demo proposes a report and performs no payment, refund or repair. The app renders the reply from validated integer cents.

## Run

Open the selected HTML directly for offline presentation. Keep the repository together so images and evidence links resolve.

For notebook rehearsal, after installing `requirements.txt` from this folder:

```sh
python -m jupyterlab examples/synthetic-incident/demo.ipynb
# Or the recorded real-data alternative:
python -m jupyterlab examples/ubuntu-support-handover/demo.ipynb
```

For fresh paid calls, copy `.env.example` to `.env` and configure your own compatible gateway. It must serve the exact aliases in the selected TOML, or you must adapt the model IDs and price/modality metadata. Then, from this workshop folder:

```sh
python examples/checkout-support/workflow.py --profile-dir examples/checkout-support/lightning-gpt-sol --repeats 3 --phase lightning-gpt-sol --allow-paid-calls
```

Fresh calls write new ignored `runs/checkout-support/` results and do not overwrite the workshop's pinned `recordings/`. Notebook defaults disable paid calls and tracing; published outputs are cleared.

`shared/` contains implementation modules, `examples/` contains named entry points, and `recordings/` contains historical evidence. Original recorded source paths are retained inside recordings; [the source map](evidence/source-map.json) resolves measured hashes to immutable snapshots. Use the current entry points for execution; the snapshots are historical evidence.

[Data attribution](ATTRIBUTION.md) · [Publication manifest](publication-manifest.json)
