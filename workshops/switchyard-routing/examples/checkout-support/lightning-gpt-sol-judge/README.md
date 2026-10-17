# Checkout support: Lightning as judge and efficient executor

**Lightning now decides the model through Switchyard’s built-in `llm_task_classifier`.** It forecasts success on the next stage; Switchyard selects Lightning at `p_solve >= 0.75`, otherwise GPT Sol 6.1. The same fixed three-stage task is retained.

**68.8% lower estimated model cost**, excluding cache discounts and write premiums, including every judge call.

[Workshop notebook](demo.ipynb). It defaults to replaying the final saved comparison, with no API calls. The earlier [rule-based notebook](../lightning-gpt-sol/demo.ipynb) is retained as a separate backup.

| Approach | Accepted | Mean USD/workflow, no cache effects | USD/accepted including failures | Median seconds | Judge / executor calls |
|---|---:|---:|---:|---:|---:|
| GPT Sol 6.1 only | 3/3 | $0.010419 | $0.010419 | 10.34 | 0 / 9 |
| Lightning only | 0/3 | $0.000207 | No accepted results | 1.17 | 0 / 3 |
| Lightning judge + routed executors | 3/3 | $0.003246 | $0.003246 | 8.11 | 9 / 9 |

## Who does what

- Lightning judge sees the actual task text, declared model capabilities, attachment metadata and any rejection feedback. It does not see image pixels or fixture answers. The attachment metadata is not OCR.
- The built-in Switchyard task classifier applies the threshold to the returned forecast and invokes the selected executor adapter.
- That executor receives the original request. Images are sent unchanged through native Switchyard dispatch, bypassing the installed LangChain adapter’s text-only content mapper.
- Python validators still check labelled-fixture outputs. They are evaluators, not routing judges. A retry is judged again by Lightning; application code does not force a different model after rejection.
- A wrong choice of text-only Lightning for an image is blocked and counted as a failed task. Invalid classifier output follows Switchyard’s capable fallback; it is not a successful judge decision.
- All judge and executor requests share one cost ledger, including failed calls. No paid model judge is used by either single-model baseline.

## Actual judge decisions

| Repeat | Stage | Forecast p_solve | Target | Crux |
|---|---|---:|---|---|
| 1 | backend_text | 0.99 | Lightning | Identify the log record with event payment.capture.succeeded and the log record with event frontend.confirmation.fetch, then extract their id fields. |
| 1 | vision | 0.0 | GPT Sol | Cannot process image attachments; text-only model cannot transcribe screenshot content. |
| 1 | reconcile_text | 0.95 | Lightning | UI shows failed payment with 'Pay again' button while backend confirms one capture and paid status. |
| 2 | backend_text | 0.99 | Lightning | Identify the log record with event payment.capture.succeeded and the log record with event frontend.confirmation.fetch, then extract their id fields. |
| 2 | vision | 0.0 | GPT Sol | Cannot process image attachments; text-only model cannot read screenshot evidence. |
| 2 | reconcile_text | 0.95 | Lightning | UI shows failed payment with 'Pay again' button while backend confirms one capture and paid status. |
| 3 | backend_text | 0.99 | Lightning | Identify the log record with event payment.capture.succeeded and the log record with event frontend.confirmation.fetch, then extract their id fields. |
| 3 | vision | 0.0 | GPT Sol | Cannot process image attachments; no vision or OCR tools available. |
| 3 | reconcile_text | 0.95 | Lightning | UI shows failed payment with 'Pay again' button while backend confirms one capture and paid status. |

## Pricing and scope

The primary estimate reprices observed input/output tokens at the pinned reference prices: Lightning $0.07/$0.20 per million, GPT Sol $2/$10 per million. Cache read discounts and cache write premiums are removed from both sides. These are model-cost estimates, not invoices or a new cold-cache run. Judge tokens are included.

<details><summary>Technical detail: reported cache-adjusted estimates</summary>

| Approach | Mean estimated USD/workflow |
|---|---:|
| GPT Sol 6.1 only | $0.006003 |
| Lightning only | $0.000207 |
| Lightning judge + routed executors | $0.001261 |

These secondary estimates apply the saved cache read/write rates to reported gateway usage. Cache state carries across repeats and earlier experiments; use the no-cache-effects estimate for the workshop headline.

</details>

One synthetic fixture repeated three times does not establish general judge calibration, reliability or future savings. This is LLM-based routing within a fixed workflow, not autonomous agent planning. App-rendered customer replies use validated cents and perform no payment, refund or repair.

## Earlier attempts retained

The first comparison accepted 2/3 routed tasks: Lightning was overconfident after a source-ID rejection and selected itself again. A first clarification of record IDs versus event names still confused log record IDs with payment capture object IDs and accepted 0/3 routed tasks. The final contract explicitly identifies `logs.records[].id`; it is applied equally to all fresh baselines. Judge prompt and threshold are unchanged. Earlier runs are separate comparisons and are not pooled into final results.

[Final raw recording](../../../recordings/checkout-support/lightning-gpt-sol-judge-v3-2026-10-17-20261017T081627323689Z.json) · [Summary](summary.csv) · [Model profile](models.toml) · [Judge implementation](judge.py) · [Shared workflow](../workflow.py).

From the workshop folder, to run a fresh paid comparison:

```sh
python examples/checkout-support/lightning-gpt-sol-judge/run.py --allow-paid-calls
```

Final and exploratory reference-price spend, including reported cache effects and every judge call:

| Recording | Attempts | Estimated USD |
|---|---:|---:|
| lightning-gpt-sol-judge-2026-10-17-20261017T081356787014Z.json | 9 | $0.016762 |
| lightning-gpt-sol-judge-v2-2026-10-17-20261017T081517719071Z.json | 9 | $0.021676 |
| lightning-gpt-sol-judge-v3-2026-10-17-20261017T081627323689Z.json | 9 | $0.022413 |

These are separate development comparisons, not pooled evidence for the final savings headline.
