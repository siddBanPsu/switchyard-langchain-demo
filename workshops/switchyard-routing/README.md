# Switchyard routing workshop

**Show [Lightning as judge + Lightning/GPT executors](examples/checkout-support/lightning-gpt-sol-judge/demo.ipynb).** The customer sees “Payment failed” although the backend has charged their card. Lightning decides which model should handle each stage.

| Named example | Open | Role |
|---|---|---|
| Lightning judge + Lightning/GPT Sol executors | [Notebook](examples/checkout-support/lightning-gpt-sol-judge/demo.ipynb) · [Results](examples/checkout-support/lightning-gpt-sol-judge/README.md) | Selected workshop presentation |
| Lightning + GPT Sol, earlier rules | [Notebook](examples/checkout-support/lightning-gpt-sol/demo.ipynb) · [HTML](examples/checkout-support/lightning-gpt-sol/preview.html) | Working rule-based backup; different routing method |
| Lightning + Super VL | [HTML](examples/checkout-support/lightning-super-vl/preview.html) · [Results](examples/checkout-support/lightning-super-vl/README.md) | All-NVIDIA comparison |
| Super VL + GPT Sol | [Results](examples/checkout-support/super-vl-gpt-sol/README.md) | Super alone handled this fixture |
| Synthetic incident | [Notebook](examples/synthetic-incident/demo.ipynb) · [HTML](examples/synthetic-incident/preview.html) | Original fallback |
| Ubuntu support handover | [Notebook](examples/ubuntu-support-handover/demo.ipynb) · [Results](examples/ubuntu-support-handover/README.md) | Real conversation alternative |

## Lightning-judge results

Same final extraction contract for all fresh baselines. Ordinary input/output prices applied to observed tokens; cache discounts and write premiums excluded. **All judge calls included.**

| Approach | Accepted | Mean estimated USD/workflow | Median seconds | Judge / executor calls, all 3 repeats |
|---|---:|---:|---:|---:|
| GPT Sol only | 3/3 | $0.010419 | 10.34 | 0 / 9 |
| Lightning only | 0/3 | $0.000207, partial | 1.17 | 0 / 3 |
| Lightning judge + routed executors | 3/3 | $0.003246 | 8.11 | 9 / 9 |

**68.8% lower estimated model cost** than GPT everywhere, excluding cache effects. Prices are the pinned reference snapshot, not invoices or current quotes. This repricing is not a cold-cache inference run. Lightning-only cannot read the image and is blocked before dispatch; its partial cost is not a completed solution.

## Five-minute presentation

1. Show the customer screenshot: “Payment failed, but my card was charged. Should I pay again?”
2. Explain the backend evidence: one SGD 118.70 capture, paid order, duplicate webhook and HTTP 504 confirmation request.
3. Show Lightning's actual forecasts: 0.99 for backend text, 0.00 for image reading, and 0.95 for reconciliation. Switchyard's task classifier applies the configured threshold of 0.75 to select the executor.
4. Show the route and ledger: Lightning judge → Lightning text; Lightning judge → GPT image; Lightning judge → Lightning reconciliation. The nine judge calls across three repeats are included in costs.
5. Show acceptance and the 68.8% estimate. Explain the proposed outcome: do not pay again; reconcile displayed status with the existing payment. No payment, refund or repair is performed.

The judge sees task text, capability descriptions, attachment metadata and retry feedback, not image pixels or fixture answers. The executor receives the original payload. Python validators evaluate the result; they are not the routing judge. A retry is judged again. No application rule selects GPT merely because an image or validation rejection is present.

This is LLM routing inside a fixed three-stage workflow, not autonomous planning or a general quality benchmark. Earlier tests exposed overconfidence after source-ID errors; the final contract disambiguates log record IDs from payment object IDs identically for every baseline. [All earlier attempts are retained](examples/checkout-support/lightning-gpt-sol-judge/README.md).

## Run

From this workshop folder, after installing `requirements.txt`:

```sh
python -m jupyterlab examples/checkout-support/lightning-gpt-sol-judge/demo.ipynb
```

Run all cells with `DEMO_MODE = "recorded"` and `ALLOW_PAID_CALLS = False`. For fresh paid calls using your own compatible gateway in `.env`:

```sh
python examples/checkout-support/lightning-gpt-sol-judge/run.py --allow-paid-calls
```

Fresh results go to ignored `runs/checkout-support/`, preserving pinned `recordings/`. Shared implementations are under `shared/` and `examples/`; [the source map](evidence/source-map.json) resolves historical recorded hashes to measured-source snapshots.

[Data attribution](ATTRIBUTION.md) · [Publication manifest](publication-manifest.json)
