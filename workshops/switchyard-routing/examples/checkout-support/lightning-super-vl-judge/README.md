# Checkout support: Lightning judge + Super VL

**The strengthened prompt completed the routed workflow in one new comparison. Estimated cost was 7.9% higher than Super VL alone, including all judge calls.**

[Workshop notebook](demo.ipynb) replays this new recording without API calls. Exactly one attempt per approach was run after the prompt change; no extra repeats were made.

## What changed

The shared [Lightning judge prompt](../lightning-gpt-sol-judge/judge.py) now checks access to required evidence before reasoning difficulty. When image reading is required without a sufficient text transcription, it instructs Lightning to return `LIM-1`, `unsupported`, and `p_solve = 0`. Metadata and hashes are explicitly not substitutes for the image contents. Tasks with sufficient text and no required visual verification remain eligible for Lightning.

Lightning still makes the routing judgment; there is no application override that assigns images to Super VL. Switchyard applies the unchanged 0.75 threshold. The existing modality guard blocks an invalid selection rather than rerouting it. Both future GPT and Super comparisons use this shared prompt; the existing GPT recording was not rerun or relabelled as using the new prompt.

## New single-run results

| Approach | Accepted | Estimated USD/workflow, cache effects excluded | Seconds | Judge / executor calls |
|---|---:|---:|---:|---:|
| Super VL only | 1/1 | $0.00078385 | 4.83 | 0 / 3 |
| Lightning only | 0/1 | $0.00020739 (partial) | 1.16 | 0 / 1 |
| Lightning judge + routed executors | 1/1 | $0.00084578 | 7.37 | 3 / 3 |

The cheaper Super-only baseline completed the task. Routing added three judge calls, so this comparison demonstrates correct delegation but no cost saving. Lightning-only stopped before image inference and its partial spend is not a completed-solution cost.

## Actual judge decisions

| Stage | Forecast p_solve | Selected executor | Explanation |
|---|---:|---|---|
| backend_text | 0.99 | Lightning | Extract 7 fields from the single order QF-1042 across logs.records and payment.settled_captures. |
| vision | 0.00 | Super VL | Required image evidence unavailable; Lightning cannot read pixels or OCR the screenshot. |
| reconcile_text | 0.96 | Lightning | Reconcile backend capture state against UI failure screenshot; count captures, compare statuses. |

## Earlier failure retained

The [earlier recording](../../../recordings/checkout-support/lightning-super-vl-judge-single-2026-10-17-20261017T083301823486Z.json) used the original prompt: Super-only passed 1/1; routed failed 0/1 because Lightning predicted 0.95 for screenshot reading and selected itself. The application blocked that image request before inference. Its partial routed estimate was $0.00049050. That run remains separate from the new successful attempt; the results are not pooled.

## Scope and pricing

This is LLM routing within a fixed three-stage synthetic workflow, not autonomous planning. The judge sees task text and attachment metadata, not image pixels or fixture answers. The chosen executor receives the original payload. Python fixture validators evaluate outputs and permit the unchanged two-attempt limit per stage. All three successful routed stages completed without a validation retry. Customer replies are rendered from validated data; no payment, refund or repair is performed.

Primary estimates apply the saved ordinary input/output prices in [prices.json](prices.json) to all observed judge and executor tokens, excluding cache discounts and write premiums. They are pinned reference estimates, not invoices. In this comparison the cache-adjusted and ordinary estimates are equal. One synthetic case and one attempt per approach cannot establish general reliability, calibrated probabilities or future savings.

[New recording](../../../recordings/checkout-support/lightning-super-vl-judge-single-2026-10-17-20261017T090853642257Z.json) · [Summary](summary.csv) · [Model profile](models.toml) · [Shared workflow](../workflow.py)

To run a fresh paid comparison from the workshop folder:

```sh
python examples/checkout-support/lightning-super-vl-judge/run.py --repeats 1 --allow-paid-calls
```

## Development spend

| Recording | Attempts | Estimated USD with reported caches |
|---|---:|---:|
| lightning-super-vl-judge-single-2026-10-17-20261017T083301823486Z.json | 3 | $0.00148024 |
| lightning-super-vl-judge-single-2026-10-17-20261017T090853642257Z.json | 3 | $0.00183702 |

Development runs are retained separately; they are not pooled into a savings headline.
