# Checkout support

Shared synthetic incident: the checkout screen says payment failed, while the backend shows one captured payment and a paid order.

- [Lightning judge + Lightning/GPT executors](lightning-gpt-sol-judge/README.md): selected workshop example; [notebook](lightning-gpt-sol-judge/demo.ipynb).
- [Lightning judge + Lightning/Super VL executors](lightning-super-vl-judge/README.md): [single-run notebook](lightning-super-vl-judge/demo.ipynb), including the observed routing failure.
- [Lightning + GPT Sol 6.1](lightning-gpt-sol/README.md): earlier rule-based backup; [recorded walkthrough](lightning-gpt-sol/preview.html).
- [Lightning + Super VL](lightning-super-vl/README.md): all-NVIDIA comparison; [recorded walkthrough](lightning-super-vl/preview.html).
- [Super VL + GPT Sol 6.1](super-vl-gpt-sol/README.md): both models handle the image; Super alone was cheaper with the same observed acceptance.

`workflow.py` runs the fixed three-stage comparison. `demo.py` provides native Switchyard dispatch and validation. `case.json` and `checkout.png` are shared evidence. Each named variant has its own TOML, prices and recorded findings. Historical agent prototypes remain in `versions/`; they are not the workshop entry point.

[Workshop guide](../../README.md)
