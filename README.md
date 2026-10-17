# Switchyard workshop

The selected demo is **Checkout support: Lightning as judge + Lightning/GPT Sol executors**. A [Lightning judge + Super VL notebook](workshops/switchyard-routing/examples/checkout-support/lightning-super-vl-judge/demo.ipynb) is also available.

[Open the main notebook](workshops/switchyard-routing/examples/checkout-support/lightning-gpt-sol-judge/demo.ipynb) · [Workshop guide](workshops/switchyard-routing/README.md) · [Judge-inclusive results](workshops/switchyard-routing/examples/checkout-support/lightning-gpt-sol-judge/README.md)

Lightning forecasts whether it can handle each stage; Switchyard selects the executor. The latest test made **one attempt per approach for each model pair**, with no extra model repeats. Lightning/GPT routing completed 1/1 and estimated **67.3% lower model cost**, including judge calls and excluding cache effects. Lightning/Super routing failed its one attempt because the judge sent an image to text-only Lightning; Super-only completed 1/1. Partial spending is not a savings result.

```text
workshops/switchyard-routing/
  examples/
    checkout-support/
      lightning-gpt-sol-judge/    selected: Lightning decides the executor
      lightning-super-vl-judge/   single-run all-NVIDIA LLM judge comparison
      lightning-gpt-sol/          earlier rule-based version, retained
      lightning-super-vl/         all-NVIDIA comparison
      super-vl-gpt-sol/           alternative comparison
    synthetic-incident/          original fallback
    ubuntu-support-handover/      real conversation alternative
  shared/                        common Python modules
  configs/                       model and pricing settings
  data/                          source fixtures and attribution
  recordings/                    pinned comparison evidence
  evidence/                      immutable measured-source snapshots
  tests/                         offline and mock-endpoint checks
scripts/                         publication and notebook replay checks
```

From the workshop folder, install pinned dependencies with Python 3.12:

```sh
cd workshops/switchyard-routing
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab examples/checkout-support/lightning-gpt-sol-judge/demo.ipynb
```

The notebook defaults to recorded replay with no model calls or key requirement. Live inference requires your own compatible gateway and explicit paid-call opt-in. Copy `.env.example` to `.env`; credentials and private endpoint values are excluded from Git. Configured IDs are gateway aliases.

Local `local-research/` retains earlier experiments and the untouched synthetic backup; it is ignored and is not required by the workshop. New live results go to ignored `runs/`; committed `recordings/` hold pinned evidence. The earlier rule-based [HTML walkthrough](workshops/switchyard-routing/examples/checkout-support/lightning-gpt-sol/preview.html) remains a comparison, not a recording of the new LLM-judge workflow.

[Data attribution](workshops/switchyard-routing/ATTRIBUTION.md) · [Publication verification](scripts/verify_publication.py)
