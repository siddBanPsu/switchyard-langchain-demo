# Super VL handover comparison — 16 October 2026

With **`nvidia/nvidia/nemotron-3.5-super-vl` as both efficient executor and routing judge**, automatic routing passed the automated report checks in all three fresh attempts and used **56.0% less estimated spend** than capable-only. The capable executor remains the existing GPT Sol model. This is one selected historical support-handover task, not a general reliability benchmark.

| Approach | Automated checks passed | Mean USD per attempt | USD per accepted report, including failures | Median elapsed |
|---|---:|---:|---:|---:|
| Capable only | 3/3 | $0.012931 | $0.012931 | 15.0 s |
| Super VL only | 2/3 | $0.003513 | $0.005270 | 22.8 s |
| Automatic routing | 3/3 | $0.005687 | $0.005687 | 28.4 s |

The savings calculation is `1 - total routing spend / total capable-only spend`, using matched case/repeat sets. All nine attempts are included. Routing was slower in this sample. Super-VL-only was cheaper, including on cost per accepted report; its one failed check was an omitted `U59` in the structured evidence-ID list, even though the admission was mentioned in its prose. This does not establish that routing is more reliable than Super VL alone.

## Prices and accounting

| Model | Input / M | Output / M | Cache read / M | Cache write / M |
|---|---:|---:|---:|---:|
| Super VL, for both executor and judge calls | $0.25 | $0.65 | $0.10 | $0.25 |
| Existing capable model | $2.00 | $10.00 | $0.10 | $2.50 |
| Preserved Nano entry, unused in the final comparison | $0.05 | $0.20 | $0.03 | $0.05 |

The Super VL input/output rates are the user-requested rates reported by [Artificial Analysis](https://artificialanalysis.ai/models/nemotron-3-5-super-vl), verified on its [localized model page](https://artificialanalysis.ai/es/models/nemotron-3-5-super-vl). They are cross-provider reference prices, not proof of the internal gateway's billing. Cache reads retain the user's earlier $0.10/M assumption. No cache-write rate was supplied, so writes are assumed to cost ordinary input at $0.25/M. Capable and Nano rates retain the previous workshop scenario assumptions.

Artificial Analysis's average **$0.30 per Intelligence Index task** is not used as a flat fee. This comparison prices actual returned input/output/cache counts. Reasoning tokens are included within output tokens, not charged twice. Missing required usage or rates would leave cost unavailable. Settings and the model-price catalog are frozen at the start of the comparison; all judge calls and failed attempts are included.

Mean routing cost breaks down as:

| Role | Mean USD per task |
|---|---:|
| Super VL executor | $0.003065 |
| Capable executor | $0.000335 |
| Super VL routing judge | $0.002287 |
| **Total** | **$0.005687** |

Judge calls account for about 40% of routing spend. Two routed attempts used Super VL for every executor step. One used the capable model to read the opening ticket, then Super VL for evidence retrieval and reporting. No routing choices were forced. The routing thresholds remain base 0.6, step 0.1, recent window 3, with the existing 4,000-token call limit.

Provider-controlled cache treatment varied. Capable-only attempt 1 cost $0.021472; attempts 2 and 3 cost $0.008630 and $0.008690. Matched-repeat savings ranged from 22.4% to 75.5%; the 56.0% headline is the aggregate spend reduction. As a sensitivity calculation, pricing every observed input token at the ordinary input rate, without cache discounts or surcharges for any model, gives **69.7% lower routing spend**. That is a repricing exercise, not another live measurement. The primary result uses actual reported cache categories.

## Interface correction and quality review

The earlier Super VL attempts exposed a report-submission mismatch: some text fields were emitted as prose while the tool required lists. With a terminal submission tool, that validation failure ended the task before the model could repair it. These rejected attempts are retained; they are not silently counted as successful reports.

The final comparison uses the **same revised interface for all three approaches**. `contradictions`, `attempted_actions` and `unknowns` accept prose or lists and are stored as lists without rewriting their content. Evidence IDs still require a list and must reference retrieved material. The evaluator also accepts acknowledgement of missing post-reboot verification in either `outcome` or `unknowns`; this changes field-location handling, not the required fact. Metadata records both revisions. Earlier strict-interface results are not pooled into this comparison, and the new outcome cannot be attributed solely to the model change.

The three routed reports captured the admitted interrupted `do-release-upgrade -d`, identified the historically reported `linux-generic` remedy, and distinguished the helper's predicted kernel 3.13 from an observed post-reboot version. The source contains no post-reboot `uname` output. Some contextual wording repeats historical helper interpretations; preserve attribution and review wording before presenting the report as verified technical fact. Automated passes are not a semantic proof.

The task compiles a handover from a **complete 79-message historical conversation**, including its remedy and reported success. It is not a hidden-outcome diagnosis task or a live repair. Tools are read-only. Missing paste contents were never reconstructed. Public-source memorization is possible.

## Artifacts and reproduction

- Notebook: `examples/ubuntu-support-handover/demo.ipynb`, defaulting to recorded mode with the full matched comparison pinned.
- Browser preview: `examples/ubuntu-support-handover/preview.html`.
- Exact model profile: `configs/model-profiles/nemotron-super-vl-gpt-sol.toml`.
- Separate model-price entries: `configs/pricing-handover.toml`.
- Raw final results: `recordings/ubuntu-handover/super-vl-both-v2-2026-10-16-20261016T042519610347Z.json`.
- Summary: `recordings/ubuntu-handover/super-vl-v2-summary-2026-10-16.csv`.
- Role-cost breakdown and no-cache sensitivity CSVs are in the same folder.

```sh
.venv/bin/python shared/ubuntu_handover_demo.py \
  --profile configs/model-profiles/nemotron-super-vl-gpt-sol.toml \
  --repeats 3 --phase super-vl-repeat --allow-paid-calls
```

The old Nano-judge variant is preserved separately. Preliminary runs were stopped when the judge configuration and report interface changed; completed attempts and their repriced copies remain available. An interrupted request may have incurred unreported usage; these preliminary runs are not included in the final matched comparison or its savings claim.

All **53 regression tests passed**. The final notebook is executed in recorded mode for delivery. Original synthetic notebooks, code, data, routing settings and requirements still match their backup hashes; the prior storage notebook and its recordings remain intact.

Data: [Ubuntu Chat Logs Corpus](https://www.convokit.cornell.edu/documentation/chatlogs.html), conversation 79.2; Sarkar et al. (2025), ConvoKit formatting by Axel Bax, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Original source messages and the grouped adaptation are retained in `data/ubuntu/handover/`.
