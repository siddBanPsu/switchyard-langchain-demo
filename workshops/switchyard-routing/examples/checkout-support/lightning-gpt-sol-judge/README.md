# Checkout support: Lightning as judge and efficient executor

**Lightning now decides the model through Switchyard’s built-in `llm_task_classifier`.** It forecasts success on the next stage; Switchyard selects Lightning at `p_solve >= 0.75`, otherwise the capable model. The same fixed three-stage task is retained.

**67.3% lower estimated model cost**, excluding cache discounts and write premiums, including every judge call.

[Workshop notebook](demo.ipynb). Recorded comparison: **1 attempt per approach**. No API calls in replay. The earlier [rule-based version](../lightning-gpt-sol/preview.html) remains separate.

| Approach | Accepted | Mean USD/workflow, no cache effects | USD/accepted including failures | Median seconds | Judge / executor calls |
|---|---:|---:|---:|---:|---:|
| GPT Sol 6.1 only | 1/1 | $0.010306 | $0.010306 | 10.05 | 0 / 3 |
| Lightning only | 0/1 | $0.000207 | No accepted results | 1.19 | 0 / 1 |
| Lightning judge + routed executors | 1/1 | $0.003366 | $0.003366 | 8.98 | 3 / 3 |

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
| 1 | vision | 0.0 | GPT Sol | Cannot process image input; no vision tools available. |
| 1 | reconcile_text | 0.95 | Lightning | UI shows failed payment with 'Pay again' button while backend records one capture and paid status. |

## Recorded routing failures

No routing failure in this recorded comparison. One attempt does not establish general reliability.

## Pricing and scope

The primary estimate reprices every observed input/output token at the saved rates in prices.json, including judge tokens. Capable model: GPT Sol 6.1. Cache discounts and write premiums are removed from both sides. These are reference estimates, not invoices or a new cold-cache run.

<details><summary>Technical detail: reported cache-adjusted estimates</summary>

| Approach | Mean estimated USD/workflow |
|---|---:|
| GPT Sol 6.1 only | $0.004122 |
| Lightning only | $0.000207 |
| Lightning judge + routed executors | $0.001380 |

These secondary estimates apply the saved cache read/write rates to reported gateway usage. Cache state carries across repeats and earlier experiments; use the no-cache-effects estimate for the workshop headline.

</details>

A single synthetic fixture with a small number of attempts does not establish general judge calibration, reliability or future savings. This is LLM-based routing within a fixed workflow, not autonomous agent planning. App-rendered customer replies use validated cents and perform no payment, refund or repair.

## Earlier attempts retained

The earlier GPT judge development comparisons exposed overconfidence and source-ID confusion; those recordings remain separate. The current contract explicitly identifies logs.records[].id equally for every baseline. This single-run comparison is not a reliability benchmark, and no extra model repetitions were made for it.

[Final raw recording](../../../recordings/checkout-support/lightning-gpt-sol-judge-single-2026-10-17-20261017T083259388267Z.json) · [Summary](summary.csv) · [Model profile](models.toml) · [Judge implementation](judge.py) · [Shared workflow](../workflow.py).

From the workshop folder, to run a fresh paid comparison:

```sh
python examples/checkout-support/lightning-gpt-sol-judge/run.py --repeats 1 --allow-paid-calls
```


## Development spend

| Recording | Attempts | Estimated USD with reported caches |
|---|---:|---:|
| lightning-gpt-sol-judge-2026-10-17-20261017T081356787014Z.json | 9 | $0.016762 |
| lightning-gpt-sol-judge-single-2026-10-17-20261017T083259388267Z.json | 3 | $0.005709 |
| lightning-gpt-sol-judge-v2-2026-10-17-20261017T081517719071Z.json | 9 | $0.021676 |
| lightning-gpt-sol-judge-v3-2026-10-17-20261017T081627323689Z.json | 9 | $0.022413 |

Development comparisons are retained separately, not pooled into the final savings headline.
