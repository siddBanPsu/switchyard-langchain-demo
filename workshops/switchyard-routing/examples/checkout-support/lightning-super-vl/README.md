# Combined Lightning + Super VL: visual checkout support

**A useful combined-model example has been measured:** a fixed three-stage support workflow using Lightning for routine text, Super VL for a screenshot, and Super VL for a text retry if validation fails. The combined workflow and Super-VL-only both completed **3/3** attempts. Combined estimated model spend was **22.7% lower** than Super-VL-only, including the failed Lightning extraction and its Super VL retry.

This is **one purpose-built synthetic case**, not an autonomous-agent benchmark or a production savings guarantee. The earlier autonomous-agent prototypes were unreliable or expensive and remain recorded separately. The working result belongs to the bounded workflow described here.

Start with the [recorded walkthrough](preview.html). It makes no API calls. For your developer/architect audience, the customer story and distinct visual/text responsibilities are clearer than the Ubuntu kernel handover. The original workshop demos remain intact.

## The story

“Checkout says payment failed, but my card was charged. Should I press Pay again?”

The [synthetic screenshot](../checkout.png) shows “Payment failed”, “Your card was not charged”, a “Pay again” button and SGD 118.70. Backend records show one successful capture, a paid order, a repeated webhook for the same capture and a 504 from the frontend confirmation request. The correct response is to avoid another payment, reconcile the displayed order status against the capture and inspect the confirmation endpoint. There is no proof of every underlying network cause and no real payment, refund or fix is executed.

## What routes where

1. **Backend text:** Lightning reads the checkout logs and authoritative payment state, extracts the relevant order and counts unique captures. Other orders and webhook retries are in the supplied log.
2. **Visual evidence:** an actual PNG is sent to Super VL. Lightning's advertised input modality is text; Super VL accepts images. No OCR transcript is supplied as a side channel to the Lightning-only baseline.
3. **Reconciliation:** Lightning combines the extracted backend facts, visual observation and runbook into a structured support decision. The application renders the customer reply from validated fields, including integer cents; it does not trust free-form LLM currency conversion.

If a stage's first output fails validation, its one permitted retry uses Super VL in the combined arm. Each single-model baseline retries with its own model. All arms have the same two-attempt limit, prompts, input sources, validators and token limits.

**Actual Switchyard integration:** native `HeaderRoutingConfig` performs the dispatch. Application code tags an image request or failed-validation retry as `strong`; routine text is `weak`. These are explicit authored rules, not a learned capability score. There is **no LLM judge call**. This uses Switchyard's native OpenAI request path because the installed LangChain adapter's content mapper rejects image blocks. It does not compare Switchyard against another router or prove a routing library is uniquely necessary.

## Fresh matched comparison

| Approach | Complete decisions accepted | Mean estimated USD/task | Median time |
|---|---:|---:|---:|
| Super VL only | 3/3 | $0.000770 | 3.51 s |
| Lightning only | 0/3 | $0.000272 (partial failed workflows) | 1.37 s |
| Combined via Switchyard | 3/3 | $0.000595 | 5.16 s |

All nine final attempts are included. Complete usage was returned for every actual API call. Lightning-only did not complete: two attempts passed the backend stage and were blocked before image dispatch by the advertised text-only capability; one failed backend source-ID extraction twice before reaching the image. These are not three observed failed vision inferences or proof of general reasoning inability.

The successful combined paths were:

- Repeat 1: **Lightning text → Super VL correction → Super VL image → Lightning reconciliation**. Lightning returned event types instead of record IDs; the deterministic validator rejected those references. Super VL corrected them using the same original records and field-name feedback.
- Repeats 2 and 3: **Lightning text → Super VL image → Lightning reconciliation**.

Combined used **6 Lightning calls and 4 Super VL calls**, versus **9 Super VL calls** in the capable-only baseline. It made one extra model call overall because of the validation retry. Provider-returned model IDs confirm the configured target on every call.

The spending calculation is `1 - total combined spend / total Super-only spend`, on the same case/repeat set. The aggregate reduction is **22.7%**, not the best single-run result:

| Repeat | Super VL only | Combined | Spend reduction | Validation retry |
|---|---:|---:|---:|---:|
| 1 | $0.000772 | $0.000901 | -16.8% | 1 |
| 2 | $0.000768 | $0.000442 | 42.4% | 0 |
| 3 | $0.000770 | $0.000442 | 42.5% | 0 |

The correction made the first combined attempt more expensive than Super-only. Both ordinary combined paths saved about 42%. Combined was slower at the median; this is a measured spend tradeoff, not a latency win. Per-accepted-workflow cost equals mean cost for both successful arms because both accepted all three attempts.

## OpenRouter prices, retrieved 17 October 2026

Paid model entries from the [OpenRouter model catalog](https://openrouter.ai/api/v1/models), USD per million tokens:

| Model | Input | Output | Cache read | Cache write |
|---|---:|---:|---:|---:|
| Nemotron 3.5 Lightning | $0.07 | $0.20 | $0.04 | $0.07 assumed |
| Nemotron 3.5 Super VL | $0.15 | $0.50 | $0.02 | $0.15 assumed |

The raw metadata, input-modality declarations and retrieval timestamp are saved in `openrouter-prices-2026-10-17.json`. `prices.json` maps those public model entries to the user's exact gateway IDs. Free-tier entries are excluded. Cache-write prices were not supplied, so ordinary input rates are an explicit assumption. No cache reads/writes were reported in the final comparison, so that write assumption did not affect the headline.

**Inference ran through the configured NVIDIA gateway; costs are OpenRouter reference-price estimates applied to its returned token usage, not OpenRouter invoices or verified gateway billing.** Image input is included in reported prompt tokens; there is no additional invented image fee. Reasoning output is not double-counted. Failed outputs and retries count; an unsupported image request blocked before dispatch has no model-call charge, while its preceding text calls still count.

These prices differ from the earlier Artificial Analysis scenario, and this baseline is Super VL rather than GPT Sol. Do not compare the previous 56% handover headline and this 22.7% result as if they were one controlled benchmark.

## Validation and review

The backend validator checks fields against the supplied payment records and log IDs. Retry feedback lists rejected fields without supplying the correct answers. Visual and final checks use the labelled synthetic fixture for evaluation; this demonstration does not provide a general verifier for arbitrary screenshots. In the final measurement, only a backend source-ID correction was needed; all image observations and final reconciliations passed on their first attempts.

The final report is linked to four retrieved source objects: logs, payment state, screenshot and runbook. Source data and rendered image hashes are frozen with the recording. Final structured fields and support summaries were manually reviewed against the actual screenshot and records. Customer-facing money is rendered by application code, equally for all approaches. This is a deliberate application design choice, not evidence that the LLMs always write correct financial prose.

Model calls request temperature zero and thinking disabled for both targets. Backend and vision calls allow 700 output tokens each; reconciliation allows 900; each stage permits at most two attempts. Sampling and gateway/provider behavior can still vary. Three repeats of one authored case do not establish general production reliability or workload-wide savings.

## Five-minute workshop script

1. Show the screenshot and ask: “Would you press Pay again?”
2. Reveal the backend capture, duplicate webhook and failed confirmation request. Explain why the screen's payment claim is insufficient.
3. Show the route: cheap text extraction, visual evidence on Super VL, cheap reconciliation. Select repeat 1 in the walkthrough to inspect a real validation-triggered escalation.
4. Show all three rows of the comparison: successful Super-only and combined workflows; text-only Lightning cannot complete the visual task. State the modality limitation explicitly.
5. State the bounded claim: “On this synthetic support workflow, combining Lightning and Super VL through Switchyard cut estimated model spend by 22.7% versus Super VL everywhere, with 3/3 completed decisions in both.” Also show that one retry cost more and the combined median was slower.

## Run or inspect

- [Recorded walkthrough](preview.html), [fixture](../case.json), [screenshot](../checkout.png), [model profile](models.toml).
- Entry point: `workflow.py`. Native routing implementation: `demo.py`.
- Final recording: `recordings/checkout-support/guarded-final-2026-10-17-20261016T170620764284Z.json`.
- Summary: `recordings/checkout-support/guarded-summary-2026-10-17.csv`.
- [Review notes](review.json). All prompts, exact model IDs, reported usage, routing reasons, price snapshots and source hashes are retained.

From the workspace root:

```sh
.venv/bin/python examples/checkout-support/workflow.py --repeats 3 --phase my-combined-comparison --allow-paid-calls
```

The command explicitly enables paid model calls. Open the HTML preview for replay without Python or inference. Preserve the workspace so the shared source modules and local `.env` remain available. Never copy `.env` into a publication package.

## Prototype history, kept separate

The first tool-using agent produced invented citation IDs or a prose answer without submission. A required-tool variant then showed repeated submissions and inconsistent monetary prose. A staged agent completed but repeatedly called the same screenshot tool, making it expensive. A fixed modality-only workflow reduced spend but failed one extraction in the repeated run. The final guarded workflow adds validation-triggered escalation. These are different workflows/contracts and are not pooled into the final comparison.

| Recording | Attempts | Super only | Lightning only | Combined | Estimated USD |
|---|---:|---:|---:|---:|---:|
| `bounded-final-2026-10-17-20261016T170404105627Z.json` | 9 | 3/3 | 0/3 | 2/3 | $0.003919 |
| `bounded-pilot-2026-10-17-20261016T170310928210Z.json` | 3 | 1/1 | 0/1 | 1/1 | $0.001625 |
| `guarded-final-2026-10-17-20261016T170620764284Z.json` | 9 | 3/3 | 0/3 | 3/3 | $0.004909 |
| `lightning-super-visual-2026-10-17-20261016T165332375668Z.json` | 9 | 0/3 | 0/3 | 0/3 | $0.009669 |
| `lightning-super-visual-v2-2026-10-17-20261016T165543914270Z.json` | 9 | 3/3 | 0/3 | 2/3 | $0.024960 |
| `lightning-super-visual-v3-pilot-2026-10-17-20261016T165954220646Z.json` | 3 | 1/1 | 0/1 | 1/1 | $0.010984 |

Across all **42 recorded exploratory task attempts**, estimated development model spend was **$0.056067**, plus **$0.000170** for the separate vision probe. This development spend is disclosed separately from the recurring cost of the final workflow. All responses had usable price/usage data. The raw recordings and matching source versions remain available; no unfavorable trial was deleted.

The original synthetic backup and earlier workshop notebooks remain intact. Final verification: **75 tests passed**. The recorded walkthrough was checked in Chrome on desktop and at 480px width; trial selection updated the routing steps and cost, and the narrow page had no horizontal overflow.

## Same example with GPT Sol 6.1

The separate [Lightning + GPT Sol comparison](../lightning-gpt-sol/README.md) uses the same case, prompts, checks and retry cap. GPT-only and routed both completed 3/3; estimated routed spend was 85.7% lower with reported caching, or 72.3% lower with ordinary input repricing. [Recorded walkthrough](../lightning-gpt-sol/preview.html). This all-NVIDIA recording remains unchanged; its exact measured source files are retained in `versions/combined_guarded_demo.py` and `versions/combined_guarded_workflow.py`.

## Same example with Super VL and GPT Sol 6.1

The [fresh Super VL/GPT comparison](../super-vl-gpt-sol/README.md) passed 3/3 in every arm. Routing cost 84.2% less than GPT everywhere with reported caching (69.8% less at ordinary input rates), but 105.0% more than Super VL alone. Super VL handled both modalities without retries; this pair shows no quality advantage from GPT on this fixture. New OpenRouter rates and previous recordings are retained separately.
