# Switchyard workshop examples

Start with the [self-contained workshop package](workshops/switchyard-routing/README.md).

**Selected demo:** [Lightning + GPT Sol 6.1 checkout support](workshops/switchyard-routing/archive/visual-support/gpt-sol/preview.html). Download/clone the repository and open the HTML locally for recorded replay. GitHub's file viewer shows HTML source.

The package includes the original synthetic fallback, a real Ubuntu support-handover alternative, model comparisons, source evidence, price snapshots, notebooks, pinned dependencies and tests. Replay requires no API key. Live runs require your own compatible gateway and explicit paid-call opt-in.

```sh
git clone https://github.com/siddBanPsu/switchyard-langchain-demo.git
cd switchyard-langchain-demo/workshops/switchyard-routing
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest tests -q
```

For a browser-only presentation, no Python installation is needed. From the repository root, `python3 -m http.server 8000 --bind 127.0.0.1` also serves the walkthrough and evidence links locally.

No credentials or private gateway URL are supplied. Use the workshop's `.env.example` as a template; keep your `.env` local. Configured model IDs are gateway aliases and may need adjustment for your provider. Reference token prices are historical estimates, not billing guarantees.

[Data attribution](workshops/switchyard-routing/ATTRIBUTION.md) · [Publication verification](scripts/verify_publication.py)
