# Three small configuration files

For the separate Lightning handover comparison, use
`model-profiles/nemotron-lightning-gpt-sol.toml` with `pricing-handover.toml`.
Lightning is both efficient executor and classifier; the capable model remains GPT Sol.
Reference rates retrieved from the [OpenRouter paid-model catalog](https://openrouter.ai/api/v1/models)
on 16 October 2026 are $0.07/M input, $0.20/M output and $0.04/M cache reads.
Cache writes are assumed to cost ordinary input at $0.07/M. These are not verified
gateway billing rates. The original Lightning/Ultra and Super VL profiles are preserved.

For the Super VL handover experiment, use
`model-profiles/nemotron-super-vl-gpt-sol.toml` with `pricing-handover.toml`.
Both efficient execution and classification use the exact gateway ID
`nvidia/nvidia/nemotron-3.5-super-vl`; capable execution stays on the existing GPT Sol model.
The earlier Nano-judge variant is preserved as `nemotron-super-vl-gpt-sol-nano-judge.toml`.

Super VL input/output rates are $0.25/$0.65 per million tokens, requested from
[Artificial Analysis](https://artificialanalysis.ai/models/nemotron-3-5-super-vl).
Cache reads retain the user's $0.10/M assumption; cache writes are assumed to cost ordinary
input at $0.25/M. These are comparison assumptions, not a verified invoice from the gateway.
The Intelligence Index's average $0.30 per task is not a fee for this handover task.
Nano and capable-model prices remain separate entries with their previous scenario values.

```sh
.venv/bin/python shared/ubuntu_handover_demo.py \
  --profile configs/model-profiles/nemotron-super-vl-gpt-sol.toml \
  --repeats 3 --phase super-vl-comparison --allow-paid-calls
```

Each comparison snapshots settings and prices before its first model call. Results include
all judge usage and failed attempts. The original synthetic and storage notebooks keep
their existing model selection; this experiment has a separate profile.

| File | What it configures |
|---|---|
| `model-profiles/*.toml` | Shared clients and efficient/capable/classifier model roles |
| `routing/*.toml` | Switchyard algorithm, parameters, and run limits |
| `pricing.toml` | Optional cost estimates, once per client/model pair |

The model profiles use the format from the [reference learning labs](https://github.com/siddBanPsu/nvidia-ai-learning-labs/tree/main/configs/model-profiles).
They have been adapted to the selected gateway. Endpoint/key values live in `.env`; the profile stores their
environment-variable names. Models, roles, routing, and prices no longer live in `.env`.
Each role may reference the same client or different clients.
Each role can also define an optional `extra_body` table for provider request options.
The selected Nano profile sends `chat_template_kwargs.enable_thinking=false` only for
the classifier, as documented in [NVIDIA's Nano model guide](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-nano-30b-a3b).
This aims to leave the output budget available for the JSON verdict; support by the
internal gateway is not verified. If the gateway rejects this option, remove that table
and use a compatible non-reasoning judge. Executor requests do not receive the option.
Roles also accept optional `temperature` and `seed` fields. The Nano executor and classifier
request temperature zero; seeds are left unset until gateway support is established.
The comparison's `ORDER_SEED` affects only task order. It is independent of any model seed.
Changing generation settings requires new measurements; results collected under different
settings should not be combined as a single controlled comparison.

The NVIDIA profile uses Lightning as efficient executor and classifier and Ultra as capable
executor. The selected `nemotron-nano-gpt-sol.toml` profile currently uses Nemotron 3 Nano
as efficient executor and routing judge, and GPT-6.1 Sol as capable executor, through the same NVIDIA gateway. This compares against the **chosen capable model**.
Check provider/account availability before a live demo; prices must match the configured IDs exactly.
The notebook's role table is derived from actual model IDs. Routing judgments are separate API calls;
the final incident checks are deterministic Python rules and do not use an LLM grader.

```python
PROFILE = ROOT / "configs/model-profiles/nemotron-lightning-ultra.toml"
STRATEGY = ROOT / "configs/routing/task-classifier.toml"
settings = load_settings(PROFILE, STRATEGY, ROOT / "configs/pricing.toml", mode=MODE,
                         allow_paid_calls=ALLOW_PAID_CALLS)
```

`[routing] type="llm_classifier", mode="capability"` maps to the real
`algorithms.llm_task_classifier(...)` constructor. `type="stage_router"` maps to
`algorithms.stage_router(...)`. Unknown fields and unsupported modes are rejected.
The notebook prints the strategy and shows the adapter's routing function.

These routing files configure **this notebook's adapter**, not the standalone server.
Do not pass them directly to `switchyard-server --config`. The reference repo's renderer produces
native server TOML; this notebook constructs embedded library objects instead.
The client supports `format="openai_chat"` only. Native Anthropic Messages or Responses profiles
need a compatible gateway or another adapter; unsupported formats fail clearly.

Rehearsal always uses real stage routing with scripted models, even if the selected live strategy
is the task classifier. The notebook displays the effective mode. Rehearsal proves no savings.
