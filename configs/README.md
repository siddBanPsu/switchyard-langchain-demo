# Configuration

`model-profiles/demo-models.toml` contains placeholder efficient, capable, and classifier
roles on a shared compatible endpoint. Replace model IDs before a live run. Endpoint
and key values belong in ignored `.env`; profiles store environment-variable names.
`shared-models.toml` is a second example without provider generation options.

The default profile requests temperature zero for efficient and classifier roles.
Its judge-only `chat_template_kwargs.enable_thinking=false` table is an example for
providers that support that option. Remove it for incompatible models/endpoints.
Optional `seed` values also require provider support. Neither guarantees determinism.

`routing/task-classifier.toml` configures the embedded Switchyard classifier:

- `base_threshold = 0.6`: required predicted solve probability for supported tasks.
- `threshold_step = 0.1`: uncertain/unmatched tasks require 0.7; unsupported tasks 0.8.
- Lower probabilities select the capable model. Invalid judgments use capable fallback.
- `max_output_tokens = 4000`: per-call output cap, including the classifier.
- Other limits cap calls per task, task/request time, and comparison size.

Raising the threshold is more conservative but does not fix malformed JSON or truncation.
Judge calls add overhead, so compare final quality, total spend, and latency.

`routing/stage.toml` selects stage routing using tool activity, with no LLM judge.
Rehearsal always uses stage routing and scripted answers, even when a live classifier
preset is selected. Routing files configure this notebook adapter, not a standalone server.

`pricing.toml` is optional when calling `load_settings` directly. The audience notebook
uses its `DEMO_PRICES` cell instead. Prices match exact model IDs and cover input, output,
and cache usage. Missing required rates remain unavailable; they do not imply zero cost.
