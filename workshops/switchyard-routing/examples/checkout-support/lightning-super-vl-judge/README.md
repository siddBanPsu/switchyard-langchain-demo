# Checkout support: Lightning as judge and efficient executor

**Lightning now decides the model through Switchyard’s built-in `llm_task_classifier`.** It forecasts success on the next stage; Switchyard selects Lightning at `p_solve >= 0.75`, otherwise the capable model. The same fixed three-stage task is retained.

**Routing did not complete all attempts. Do not present partial-workflow spending as a successful savings result.**

[Workshop notebook](demo.ipynb). Recorded comparison: **1 attempt per approach**. No API calls in replay. The earlier [rule-based version](../lightning-super-vl/preview.html) remains separate.

| Approach | Accepted | Mean USD/workflow, no cache effects | USD/accepted including failures | Median seconds | Judge / executor calls |
|---|---:|---:|---:|---:|---:|
| Super VL only | 1/1 | $0.000782 | $0.000782 | 3.56 | 0 / 3 |
| Lightning only | 0/1 | $0.000207 | No accepted results | 1.19 | 0 / 1 |
| Lightning judge + routed executors | 0/1 | $0.000491 | No accepted results | 3.12 | 2 / 1 |

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
| 1 | backend_text | 0.99 | Lightning | Identify the single log record with event payment.capture.succeeded and the single log record with event frontend.confirmation.fetch, then extract their id fields. |
| 1 | vision | 0.95 | Lightning | Extracting order_id, amount_cents, ui_status, ui_claim_no_charge, button_label, and error_reference from a synthetic checkout screenshot. |

## Recorded routing failures

Routed attempt 1 stopped with LibsyError.
- vision: nvidia/nvidia/nemotron-3.5-lightning: Image input unsupported per provider model metadata; no API request sent.
The blocked request is a model-choice failure, not an observed image inference failure. This run was not repeated. No savings claim is made for the partial workflow.

## Pricing and scope

The primary estimate reprices every observed input/output token at the saved rates in prices.json, including judge tokens. Capable model: Super VL. Cache discounts and write premiums are removed from both sides. These are reference estimates, not invoices or a new cold-cache run.

<details><summary>Technical detail: reported cache-adjusted estimates</summary>

| Approach | Mean estimated USD/workflow |
|---|---:|
| Super VL only | $0.000782 |
| Lightning only | $0.000207 |
| Lightning judge + routed executors | $0.000491 |

These secondary estimates apply the saved cache read/write rates to reported gateway usage. Cache state carries across repeats and earlier experiments; use the no-cache-effects estimate for the workshop headline.

</details>

A single synthetic fixture with a small number of attempts does not establish general judge calibration, reliability or future savings. This is LLM-based routing within a fixed workflow, not autonomous agent planning. App-rendered customer replies use validated cents and perform no payment, refund or repair.

## Earlier attempts retained

The earlier GPT judge development comparisons exposed overconfidence and source-ID confusion; those recordings remain separate. The current contract explicitly identifies logs.records[].id equally for every baseline. This single-run comparison is not a reliability benchmark, and no extra model repetitions were made for it.

[Final raw recording](../../../recordings/checkout-support/lightning-super-vl-judge-single-2026-10-17-20261017T083301823486Z.json) · [Summary](summary.csv) · [Model profile](models.toml) · [Judge implementation](../lightning-gpt-sol-judge/judge.py) · [Shared workflow](../workflow.py).

From the workshop folder, to run a fresh paid comparison:

```sh
python examples/checkout-support/lightning-super-vl-judge/run.py --repeats 1 --allow-paid-calls
```


## Development spend

| Recording | Attempts | Estimated USD with reported caches |
|---|---:|---:|
| lightning-super-vl-judge-single-2026-10-17-20261017T083301823486Z.json | 3 | $0.001480 |

Development comparisons are retained separately, not pooled into the final savings headline.
