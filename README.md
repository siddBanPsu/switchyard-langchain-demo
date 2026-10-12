# One incident. Two models. A router.

A short LangChain + NVIDIA NeMo Switchyard notebook demo. An agent investigates a
synthetic checkout incident using a ticket, logs, metrics, and troubleshooting guides.
Compare **efficient-only**, **capable-only**, and **automatic routing** on the same task.

Start with [the audience notebook](incident_routing_demo.ipynb).
[Presenter notes](PRESENTER_NOTES.md) provide a one-minute story and reveal.

## Run locally

Requires Python 3.12 and Git. From this repository:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab incident_routing_demo.ipynb
```

The notebook defaults to **scripted rehearsal**, with paid calls and tracing off.
Run all cells to practise the workflow without an API key. Rehearsal uses the answer
key: it does not measure model quality, speed, or savings.

## Configure a live comparison

1. Copy `.env.example` to `.env` and provide your endpoint and API key.
2. In `configs/model-profiles/demo-models.toml`, replace both placeholder model IDs
   with IDs available on your endpoint. Executors need tool calling; the judge needs
   structured JSON output. The client requires OpenAI Chat Completions compatibility.
3. Check generation options against your provider. Remove the example
   `chat_template_kwargs` table if your judge does not support it. The classifier
   can use a separate model; its role is independent of the efficient executor.
4. Set `MODE = "live"` and `ALLOW_PAID_CALLS = True` in setup. Run one incident first.
5. Edit `DEMO_PRICES` to model your intended USD-per-million-token price scenario.
   Input, output, cache-read, and cache-write rates are distinct. Include a third
   price if the judge uses a third model.

The three-approach comparison is enabled and defaults to one incident, one repeat.
Every live execution makes fresh calls. `REPEATS` and `COMPARISON_CASES` expand the
comparison; `ORDER_SEED` controls task order, not model generation.
See [configuration details](configs/README.md) for thresholds and limits.

## Read the results

- **Reports passed:** reports satisfying all seven deterministic checks: cause,
  corrective action, decisive evidence, retrieved citations, the appropriate runbook,
  investigation tools, and a complete report with verification steps.
- **Model steps:** executor calls; a call can request multiple tools.
- **Router checks / issues:** separate judge calls / failed or unusable judgments.
  An unusable judgment falls back to the capable model.
- **Illustrative USD:** returned token usage priced at the notebook's editable rates,
  including judge calls and failed calls with usage. Missing usage or applicable
  rates makes the total unavailable. These estimates are not an API invoice.
- **Savings:** spend reduction versus capable-only on matched cases and repeats.
  Compare pass rates and latency before treating lower spending as an improvement.

The checker does not certify every sentence or execute the proposed fix. Review
report wording. The dataset has 36 variants of six templates; it is a demonstration,
not independent validation of production reliability or savings.

## Tracing and recorded results

LangSmith tracing is optional. Add `LANGSMITH_API_KEY` to `.env`, select the appropriate
endpoint/region/workspace, and set `ENABLE_LANGSMITH = True`. This uploads model prompts,
responses, and tool data to your configured tracing service. Trace links appear in results.
The notebook's price scenario is separate from LangSmith's price catalog.

Results are saved under ignored `runs/`. Set `REPLAY_PATH` in the comparison cell to
one of your saved JSON files to show a labelled recording without new model calls.
That setting applies to the comparison cell; skip the earlier live investigation cell
when presenting only recorded results. Repricing stored usage makes no new calls.

## Development and publication

```sh
python -m pytest tests/test_demo.py -q
```

Tests use scripted models and local mock HTTP endpoints; no provider credentials are needed.
Dependencies are pinned: this integration uses Switchyard 0.2.0 and the matching
LangChain NVIDIA adapter commit. Keep the pair compatible when upgrading.

Only synthetic fixtures and source files are included. Credentials, local run logs,
HTML exports, trace links, and executed notebook outputs are excluded. After using the
notebook, clear outputs before committing and inspect staged changes. `.gitignore`
does not remove output embedded in an already tracked notebook.

- [NVIDIA NeMo Switchyard](https://github.com/NVIDIA-NeMo/Switchyard)
- [LangChain Switchyard integration](https://github.com/langchain-ai/langchain-nvidia/tree/48b296bd37211ff750e95066ef23210b58f55500/libs/switchyard)
