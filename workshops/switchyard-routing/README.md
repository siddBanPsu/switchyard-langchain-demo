# Start here: Switchyard workshop

**Show the Lightning + GPT Sol 6.1 checkout-support example.** A customer sees “Payment failed” even though their card was charged. The workflow combines backend logs, payment state, the actual screenshot and a runbook to decide whether they should pay again.

| What to open | Purpose |
|---|---|
| [Main recorded walkthrough](archive/visual-support/gpt-sol/preview.html) | Selected workshop demo; opens in a browser without Python or API calls |
| [Results and run instructions](archive/visual-support/gpt-sol/README.md) | Matched trials, pricing, cache sensitivity and source evidence |
| [Model TOML](archive/visual-support/gpt-sol/models.toml) | Lightning efficient model and GPT Sol 6.1 capable model, using the existing gateway |
| [Synthetic fallback notebook](incident_routing_demo.ipynb) | Original synthetic demo, retained unchanged |
| [Synthetic recorded preview](incident_routing_l200_preview.html) | Offline fallback presentation |
| [Earlier Ubuntu handover notebook](ubuntu_handover_super_vl.ipynb) | Retained alternative with a real 79-message support conversation |
| [Experiment index](archive/README.md) | Earlier model comparisons, recordings and notes |

## Recorded results

Three attempts per approach on the same synthetic checkout case:

| Approach | Accepted | Mean estimated USD/workflow | Median seconds |
|---|---:|---:|---:|
| GPT Sol 6.1 only | 3/3 | $0.005893 | 9.15 |
| Lightning only | 0/3 | $0.000202, partial workflow | 1.23 |
| Lightning + GPT via Switchyard | 3/3 | $0.000845 | 7.68 |

**Workshop claim:** “On this synthetic support workflow, Lightning handled the text and GPT read the screenshot. Routing reduced estimated spend by 85.7% versus GPT everywhere, with both approaches completing all three attempts. Repricing all input at ordinary rates still gives a 72.3% reduction.”

Costs use the pinned OpenRouter price snapshot and reported gateway token usage, including cache reads and writes; they are not invoices or a current-price quote. The image prompt was warmed by a separate probe. The 72.3% sensitivity uses the same observed token counts without cache discounts or write premiums; it is not another live run. Lightning-only was blocked before image dispatch because it supports text input only. Its partial cost is not the price of a completed solution.

This is a **fixed three-stage workflow** using native Switchyard header routing. Application policy tags an actual image or a validator-rejected retry as capable, and other text as efficient. It has no paid LLM judge or learned difficulty classifier. All three routed attempts followed Lightning → GPT → Lightning without retries. Validators use the labelled synthetic fixture; the app renders the customer reply from validated integer cents. Three repeats of one case do not establish general accuracy or future savings.

## Five-minute presentation

1. **Frame the incident:** “Checkout failed, but my card was charged. Should I press Pay again?” Show the screenshot alongside the backend evidence.
2. **Explain the evidence:** the backend has one settled SGD 118.70 capture and a paid order. A repeated webhook is not a second charge; the confirmation request returned HTTP 504.
3. **Show the recorded route:** Lightning extracts backend facts, GPT reads the actual image, and Lightning reconciles the structured decision. Switchyard dispatches each tagged request. Select another repeat to show the complete recording.
4. **Show all three baselines:** GPT-only and routing complete 3/3; Lightning cannot finish the image task. Present both the 85.7% estimate with reported caching and the 72.3% ordinary-input repricing.
5. **Give the decision:** do not pay again; reconcile the displayed order with the existing payment and inspect the confirmation endpoint. The demo records a proposed support report and performs no payment, refund or repair.

## Rehearse or run

Open [the recorded walkthrough](archive/visual-support/gpt-sol/preview.html) directly in a browser. Keep the workspace together so its screenshot and evidence links resolve. Replay makes no inference calls.

For a fresh comparison using the existing TOML gateway configuration, from this workspace:

```sh
.venv/bin/python archive/visual-support/workflow.py --profile-dir archive/visual-support/gpt-sol --repeats 3 --phase lightning-gpt-sol --allow-paid-calls
```

This command makes paid calls and writes a new recording; it does not replace the pinned workshop replay. Fresh results and cache behavior can vary. Local credentials remain in `.env`.

## Retained alternatives

Published copies of the synthetic notebook and advanced notebook have outputs cleared, paid calls disabled and tracing disabled. Their source data and configurations are included. The original byte-for-byte synthetic backup remains in the local research workspace. For an offline synthetic fallback, open the preview above or select rehearsal mode in the original notebook.

The [Ubuntu handover preview](ubuntu_handover_super_vl_preview.html) and [analysis](SUPER_VL_HANDOVER_ANALYSIS_2026-10-16.md) remain available. The [all-NVIDIA visual comparison](archive/visual-support/README.md) is retained with its own price snapshot. The [Super VL + GPT comparison](archive/visual-support/super-gpt/README.md) passed 3/3 in every arm, but Super VL alone was cheaper than the combination; it demonstrated no quality benefit from GPT on this fixture.

Shared Python modules, `configs/`, `data/`, selected `runs/`, tests and pinned `requirements.txt` are included. Create your own `.venv`; no environment or keys are shipped. Historical and unfavorable checkout trials are retained in the experiment index.

## Install and configure

Requires Python 3.12 and Git. From this workshop folder:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest tests -q
python -m jupyterlab incident_routing_demo.ipynb
```

For live calls, copy `.env.example` to `.env` and supply your own compatible gateway URL and key. It must serve the exact model aliases in the selected TOML, or you must edit those IDs to match your provider and update pricing/modality metadata. The placeholder endpoint is intentionally not a live service. For browser replay and notebook rehearsal, leave keys unset.

[Data attribution](ATTRIBUTION.md) · [Publication manifest](publication-manifest.json).
