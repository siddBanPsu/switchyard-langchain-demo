# Switchyard routing workshop

**Show [Lightning as judge + Lightning/GPT executors](examples/checkout-support/lightning-gpt-sol-judge/demo.ipynb).** The customer sees “Payment failed” although the backend has charged their card. Lightning decides which model should handle each stage.

| Named example | Open | Role |
|---|---|---|
| Lightning judge + Lightning/GPT Sol executors | [Notebook](examples/checkout-support/lightning-gpt-sol-judge/demo.ipynb) · [Results](examples/checkout-support/lightning-gpt-sol-judge/README.md) | Selected workshop presentation |
| Lightning judge + Lightning/Super VL executors | [Notebook](examples/checkout-support/lightning-super-vl-judge/demo.ipynb) · [Results](examples/checkout-support/lightning-super-vl-judge/README.md) | One attempt per approach; routed attempt failed |
| Lightning + GPT Sol, earlier rules | [Notebook](examples/checkout-support/lightning-gpt-sol/demo.ipynb) · [HTML](examples/checkout-support/lightning-gpt-sol/preview.html) | Working rule-based backup; different routing method |
| Lightning + Super VL | [HTML](examples/checkout-support/lightning-super-vl/preview.html) · [Results](examples/checkout-support/lightning-super-vl/README.md) | All-NVIDIA comparison |
| Super VL + GPT Sol | [Results](examples/checkout-support/super-vl-gpt-sol/README.md) | Super alone handled this fixture |
| Synthetic incident | [Notebook](examples/synthetic-incident/demo.ipynb) · [HTML](examples/synthetic-incident/preview.html) | Original fallback |
| Ubuntu support handover | [Notebook](examples/ubuntu-support-handover/demo.ipynb) · [Results](examples/ubuntu-support-handover/README.md) | Real conversation alternative |

## Latest single-run results

Exactly one attempt per approach for each pair. All judge calls are included; the main estimates exclude cache discounts and write premiums. These are pinned reference prices applied to observed tokens, not invoices or a cold-cache rerun.

| Model pair / approach | Accepted | Estimated USD/task | Outcome |
|---|---:|---:|---|
| GPT Sol only | 1/1 | $0.010306 | Complete |
| Lightning judge + Lightning/GPT executors | 1/1 | $0.003366 | **67.3% lower estimated model cost** |
| Super VL only | 1/1 | $0.000782 | Complete |
| Lightning judge + Lightning/Super executors | 0/1 | $0.000491, partial | Judge chose Lightning for the image; blocked |

Lightning-only completed 0/1 in each pair because it cannot consume the image. The Super-routed partial cost does not establish savings. No extra live model runs were made to replace that failure. A single attempt does not establish general reliability. Earlier multi-repeat comparisons are retained separately in `recordings/` and the findings pages.

## Presentation

Use the GPT-judge notebook as the selected workshop example. It shows Lightning's forecast and explanation before each executor call, and the single recorded routing path. The Super-judge notebook shows the observed model-choice failure and displays the blocked request without crashing.

The judge sees task text, model capabilities and attachment metadata, not pixels or fixture answers. The selected executor receives the original payload. Python validators evaluate task output; there is no application rule that automatically assigns image requests to the capable model. The Super failure demonstrates that a model judge can choose incorrectly.

This remains LLM routing within a fixed three-stage synthetic workflow, not autonomous planning. The report proposes avoiding another payment and reconciling the paid order; no payment, refund or repair is executed.

## Run

From this workshop folder, after installing `requirements.txt`:

```sh
python -m jupyterlab examples/checkout-support/lightning-gpt-sol-judge/demo.ipynb
```

Run all cells with `DEMO_MODE = "recorded"` and `ALLOW_PAID_CALLS = False`. For fresh paid calls using your own compatible gateway in `.env`:

```sh
python examples/checkout-support/lightning-gpt-sol-judge/run.py --repeats 1 --allow-paid-calls
```

Both runners reject repeat counts other than 1. For the all-NVIDIA pair, use `examples/checkout-support/lightning-super-vl-judge/run.py --repeats 1 --allow-paid-calls`.

Fresh results go to ignored `runs/checkout-support/`, preserving pinned `recordings/`. Shared implementations are under `shared/` and `examples/`; [the source map](evidence/source-map.json) resolves historical recorded hashes to measured-source snapshots.

[Data attribution](ATTRIBUTION.md) · [Publication manifest](publication-manifest.json)
