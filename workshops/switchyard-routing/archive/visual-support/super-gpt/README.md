# Super VL + GPT Sol 6.1 on the same visual checkout example

Fresh matched comparison on 17 October 2026, using the existing TOML gateway endpoint. Same screenshot, source records, prompts, validation and retry limits as the Lightning/GPT experiment. All nine attempts are included.

| Approach | Accepted | Mean estimated USD/workflow | Cost per accepted report | Median seconds | Calls / retries |
|---|---:|---:|---:|---:|---:|
| GPT Sol 6.1 only | 3/3 | $0.006739 | $0.006739 | 10.42 | 9 / 0 |
| Super VL only | 3/3 | $0.000519 | $0.000519 | 6.36 | 9 / 0 |
| Super VL + GPT via Switchyard | 3/3 | $0.001063 | $0.001063 | 5.52 | 9 / 0 |

Routing reduced estimated spend by **84.2% versus GPT everywhere** using reported caching. At ordinary input rates with cache discounts and write premiums removed, the saving was **69.8%** on the same observed token counts. This repricing is a sensitivity calculation, not a separate live trial.

The routed workflow cost **105.0% more than Super VL alone**. All three arms passed 3/3 without retries. GPT escalation has no demonstrated quality benefit on this fixture. Prefer Super VL alone for the lowest observed spend on this particular case; prefer the previous [Lightning/GPT walkthrough](../gpt-sol/preview.html) when explaining complementary text and image capabilities.

| Ordinary input repricing | Mean USD/workflow |
|---|---:|
| GPT Sol 6.1 only | $0.010233 |
| Super VL only | $0.000533 |
| Super VL + GPT via Switchyard | $0.003093 |

The authored routing policy is unchanged: actual image or failed-validation retry → GPT, other text → Super VL. Both models support the image. This intentionally holds policy fixed for comparison; it does not establish that GPT is required for this screenshot. Native Switchyard HeaderRoutingConfig dispatches requests. There is no paid judge or learned difficulty classifier.

Each routed attempt followed Super VL → GPT screenshot reading → Super VL. All nine task attempts completed without retries. Each stage gets at most two attempts. Super VL uses temperature 0 with thinking disabled; GPT uses provider defaults. Each model has the same settings wherever used. The application renders the customer reply from validated integer cents. Nothing is paid, refunded or repaired. Fixture-based validators are evaluation checks, not a general production verifier.

| Repeat | GPT only USD | Super VL only USD | Routed USD | Accepted (GPT / Super / routed) |
|---|---:|---:|---:|---|
| 1 | $0.0119185 | $0.0004887 | $0.0009427 | True / True / True |
| 2 | $0.0041437 | $0.0005335 | $0.0011231 | True / True / True |
| 3 | $0.0041537 | $0.0005335 | $0.0011227 | True / True / True |

## Price basis and limits

| USD per 1M tokens | Input | Output | Cache read | Cache write |
|---|---:|---:|---:|---:|
| nemotron-3.5-super-vl | $0.10 | $0.40 | $0.08 | $0.10 |
| gpt-6.1-sol | $2.00 | $10.00 | $0.10 | $2.50 |

Rates were freshly fetched from the paid-model [OpenRouter catalog](https://openrouter.ai/api/v1/models). [Super VL provider prices](https://openrouter.ai/nvidia/nemotron-3.5-super-vl) now include $0.10 input / $0.40 output / $0.08 cache-read offers; older recordings used a separate $0.15 / $0.50 / $0.02 snapshot. Those historical estimates remain unchanged. [GPT Sol listing](https://openrouter.ai/openai/gpt-6.1-sol). Super VL cache-write price is assumed equal to ordinary input if unpublished.

Reference prices are applied to reported gateway usage, not actual invoices. Prompt tokens include cached tokens: cache reads and writes are removed from ordinary input to prevent double counting. Runs are shuffled (seed 41), share repeated prompts and may reuse caches warmed by previous experiments. These are three samples of one synthetic case, not independent cold-start trials or a general reliability benchmark.

Comparison model spend across all nine attempts: $0.0249601. No separate probe or pilot was run for this pair.

## Inspect and reproduce

- [Raw recording](../../../runs/visual-support/super-vl-gpt-sol-final-2026-10-17-20261017T033850366904Z.json): prompts, exact model IDs, usage, messages, source hashes and routing reasons.
- [Model TOML](models.toml), [rates](prices.json), [price snapshot](openrouter-prices-2026-10-17.json), [summary CSV](summary.csv).
- Historical raw arm names are retained: `super_only` means capable GPT-only; `lightning_only` means efficient Super-VL-only. Display labels above use the actual models.
- Validation: 10 existing visual workflow checks passed. All nine reports, evidence IDs, support summaries, model IDs and token ledgers were reviewed; all source hashes matched.
- Shared [workflow](../workflow.py) and [engine](../demo.py) are unchanged by this experiment. All earlier demos and synthetic backups remain available.

From the workspace root, to make a fresh set of paid calls:

```sh
.venv/bin/python archive/visual-support/super-gpt/run.py --allow-paid-calls
```

To rebuild this report without inference:

```sh
.venv/bin/python archive/visual-support/super-gpt/analyze.py runs/visual-support/super-vl-gpt-sol-final-2026-10-17-20261017T033850366904Z.json
```
