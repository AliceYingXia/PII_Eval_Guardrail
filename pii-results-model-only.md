# PII Detection Results: Model-Only Performance (No Regex Supplement)

This is a companion to [pii-results-comparison.md](pii-results-comparison.md), which layers a
regex supplement (`regex_pii.py`) on top of all four entity-level models to catch
clean-format SSN/CREDIT_CARD/IP_ADDRESS/PHONE/EMAIL spans the models miss. This document
strips that regex layer out entirely (`USE_REGEX_SPANS` effectively `False`) to show what
each model detects on its own, with no help from pattern matching.

Numbers were produced by rescoring the same cached raw model predictions in `raw_results/`
(see `rescore_no_regex.py`), so they're directly comparable to the regex-assisted numbers in
`pii-results-comparison.md` -- same predictions, same expected entities, only the regex
supplement step is skipped. Skyflow doesn't use a regex layer in this comparison, so its
numbers are unchanged from the other document and included here only for reference.

## Side-by-side metrics (model-only)

| Dataset | Source | Precision | Recall | F1 |
|---|---|---|---|---|
| pii-injected-v1 | openai/privacy-filter | 88.94% | 78.06% | 0.8315 |
| pii-injected-v1 | OpenMed/privacy-filter-nemotron | 96.17% | 95.36% | 0.9576 |
| pii-injected-v1 | OpenMed-PII-SuperClinical-Small (44M) | 94.42% | 92.83% | 0.9362 |
| pii-injected-v1 | OpenMed-PII-SuperClinical-Large (434M) | 96.58% | 95.36% | 0.9597 |
| pii-injected-v1 | Skyflow (reference, no regex layer) | 100.0% | 100.0% | 1.000 |
| pii-injected-hard-v1 | openai/privacy-filter | 59.63% | 64.36% | 0.6190 |
| pii-injected-hard-v1 | OpenMed/privacy-filter-nemotron | 61.76% | 41.58% | 0.4970 |
| pii-injected-hard-v1 | OpenMed-PII-SuperClinical-Small (44M) | 59.72% | 42.57% | 0.4971 |
| pii-injected-hard-v1 | OpenMed-PII-SuperClinical-Large (434M) | 75.90% | 62.38% | 0.6848 |
| pii-injected-hard-v1 | Skyflow (reference, no regex layer) | 53.7% | 97.1% | 0.691 |
| pii-realistic-v1 | openai/privacy-filter | 84.07% | 88.44% | 0.8620 |
| pii-realistic-v1 | OpenMed/privacy-filter-nemotron | 83.75% | 77.46% | 0.8048 |
| pii-realistic-v1 | OpenMed-PII-SuperClinical-Small (44M) | 81.56% | 84.39% | 0.8295 |
| pii-realistic-v1 | OpenMed-PII-SuperClinical-Large (434M) | 92.53% | 93.06% | 0.9280 |
| pii-realistic-v1 | Skyflow (reference, no regex layer) | 62.1% | 100.0% | 0.766 |

## Raw counts (model-only)

| Dataset | Source | TP | FP | FN | Items |
|---|---|---|---|---|---|
| pii-injected-v1 | openai/privacy-filter | 185 | 23 | 52 | 130 |
| pii-injected-v1 | OpenMed/privacy-filter-nemotron | 226 | 9 | 11 | 130 |
| pii-injected-v1 | OpenMed-PII-SuperClinical-Small | 220 | 13 | 17 | 130 |
| pii-injected-v1 | OpenMed-PII-SuperClinical-Large | 226 | 8 | 11 | 130 |
| pii-injected-hard-v1 | openai/privacy-filter | 65 | 44 | 36 | 130 |
| pii-injected-hard-v1 | OpenMed/privacy-filter-nemotron | 42 | 26 | 59 | 130 |
| pii-injected-hard-v1 | OpenMed-PII-SuperClinical-Small | 43 | 29 | 58 | 130 |
| pii-injected-hard-v1 | OpenMed-PII-SuperClinical-Large | 63 | 20 | 38 | 130 |
| pii-realistic-v1 | openai/privacy-filter | 153 | 29 | 20 | 130 |
| pii-realistic-v1 | OpenMed/privacy-filter-nemotron | 134 | 26 | 39 | 130 |
| pii-realistic-v1 | OpenMed-PII-SuperClinical-Small | 146 | 33 | 27 | 130 |
| pii-realistic-v1 | OpenMed-PII-SuperClinical-Large | 161 | 13 | 12 | 130 |

## Observations

Removing the regex supplement drops recall substantially for every model on every dataset,
confirming how much of the regex-assisted numbers in `pii-results-comparison.md` were driven
by pattern-matchable formats (credit cards, SSNs, IPs, phones, emails) rather than the models'
own detection:

- **pii-injected-v1** (dominated by clean-format credit card numbers): `openai/privacy-filter`
  drops the most, from 0.9431 to 0.8315 F1 (its FN count jumps from 5 to 52 -- almost entirely
  the credit-card numbers the regex layer used to catch). The three OpenMed models hold up
  better here (0.94-0.96 F1) since their own token-classification heads already catch most
  injected PII without the regex assist.
- **pii-injected-hard-v1** (dominated by obfuscated/defanged formats): every model falls
  sharply once the regex layer -- which specifically targets dotted/defanged/spelled-out
  SSN/phone/IP/email patterns -- is removed. `SuperClinical-Large` goes from a perfect 0 FN
  (100% recall, 0.9099 F1) to 38 FN (62.38% recall, 0.6848 F1), and is still the best of the
  four models on their own. `-nemotron` and `SuperClinical-Small` are both worse than
  `openai/privacy-filter` here without the regex assist (0.497 F1 vs. 0.619).
- **pii-realistic-v1**: same pattern, smaller magnitude. `SuperClinical-Large` still leads
  (0.928 F1), followed by `openai/privacy-filter` (0.862), `SuperClinical-Small` (0.8295), and
  `-nemotron` (0.8048).

**Ranking of the models' own detection (no regex), by average F1 across the three datasets:**
`SuperClinical-Large` (0.857) > `openai/privacy-filter` (0.771) > `SuperClinical-Small`
(0.754) > `-nemotron` (0.753). Note `-nemotron` and `SuperClinical-Small` are essentially tied,
and both trail `openai/privacy-filter` once the regex assist is removed -- the opposite of
their ranking in the regex-assisted comparison, where the regex supplement (applied to all
three OpenMed configs but originally only `openai/privacy-filter`) closes most of that gap.
`SuperClinical-Large` is the only model that stays clearly ahead of `openai/privacy-filter`
with or without the regex layer.

Skyflow is included only for reference -- it isn't a token-classification model scored by
this harness, so "model-only" isn't a meaningful distinction for it; its numbers are
unchanged from `pii-results-comparison.md`.

## False negative deep dive: SuperClinical-Large (434M) on pii-injected-v1, model-only

11 FN total, by type: CREDIT_CARD 9, PHONE 2.

- **CREDIT_CARD (9 of 11)** -- the model produces *zero* overlapping prediction at all for
  any of these, whether the card number is a bare 16-digit run (`9042485748614186`,
  `7140952532444893`, `5213318730533923`, `2459284931062096`, `5116943715961853`,
  `4015717598713633`, `7132149174298726`) or dash-separated (`8908-8813-5472-2326`,
  `1335-1984-6894-8140`). This isn't a boundary/format issue -- the model's own
  `credit_debit_card` head simply never fires on these spans in this dataset. It's exactly
  the gap the regex supplement in `pii-results-comparison.md` is designed to fill (and does:
  this same model scores 2 CREDIT_CARD-related FN, not 9, once the regex layer is restored).
- **PHONE (2 of 11)**:
  - Item 44: expected `(738) 498-9092`, but the model predicted one `phone_number` span
    covering `start:183, end:228`, which swallows *both* `+1 634 470 1773` and
    `(738) 498-9092` into a single merged span. Because `spans_overlap` only allows one match
    per expected entity and the earlier phone number in the pair presumably already consumed
    it, this second number's own boundaries are never predicted distinctly -- an
    adjacent-span-merging artifact rather than a missed detection outright.
  - Item 112: expected `+1 419 789 8906` -- no overlapping prediction at all. Same
    international `+1 xxx xxx xxxx` format gap noted for `SuperClinical-Small` in
    `pii-results-comparison.md`, so `SuperClinical-Large` isn't fully immune to it either,
    just less prone to it (1 instance here vs. several for the Small model).

**Takeaway:** essentially all of `SuperClinical-Large`'s model-only weakness on this dataset
is the same single root cause -- it doesn't reliably tag standalone credit-card-shaped digit
runs as `credit_debit_card` -- with two much smaller, distinct PHONE issues (a multi-number
span-merging artifact and the international-format gap) rounding out the rest. None of these
are NAME/ADDRESS/EMAIL/USERNAME/SSN/IP_ADDRESS misses, so the model's non-financial PII
detection is already at 100% recall on this dataset without any regex help.
