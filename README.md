# Switchyard workshop

The selected demo is **Checkout support: Lightning + GPT Sol 6.1**.

[Open the workshop guide](workshops/switchyard-routing/README.md) · [Open the recorded walkthrough](workshops/switchyard-routing/examples/checkout-support/lightning-gpt-sol/preview.html)

Clone/download the repository and open the HTML locally; GitHub displays its source. Replay requires no API key or Python environment.

```text
workshops/switchyard-routing/
  examples/
    checkout-support/
      lightning-gpt-sol/          selected workshop example
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
scripts/                         publication checks
```

From the workshop folder, install pinned dependencies with Python 3.12:

```sh
cd workshops/switchyard-routing
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

Live inference requires your own compatible gateway and explicit paid-call opt-in. Copy the workshop's `.env.example` to `.env`; keys and private endpoint values are excluded from Git. Configured model IDs are gateway aliases and may need adjustment for your provider.

The local-only `local-research/` directory retains previous experiments and the original synthetic backup. It is ignored by Git and is not required by any workshop example. Generated live results go to ignored `runs/` folders; committed `recordings/` hold the pinned evidence.

[Data attribution](workshops/switchyard-routing/ATTRIBUTION.md) · [Publication verification](scripts/verify_publication.py)
