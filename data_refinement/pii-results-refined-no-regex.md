# PII Detection Results on Refined Datasets (Model-Only, No Regex Supplement)

Companion to [pii-results-refined-with-regex.md](pii-results-refined-with-regex.md),
same relationship as [pii-results-model-only.md](../pii-results-model-only.md) is to
[pii-results-comparison.md](../pii-results-comparison.md): this strips the
`regex_pii.py` supplement out entirely (`USE_REGEX_SPANS` effectively `False`)
to show what each of the four models detects **on its own**, against the
refined datasets in `data_refinement/*.fixed.json`.

Produced by the same `eval_refined.py` run as the with-regex doc — both sets
of metrics come from a single classifier pass per model/dataset (regex is a
scoring-time step, not an inference-time step), so the model predictions
underlying both docs are identical; only whether the regex supplement is
layered on top differs.

## Side-by-side metrics (model-only)

| Dataset | Source | Precision | Recall | F1 |
|---|---|---|---|---|
| pii-injected-v1 (refined) | openai/privacy-filter | 88.94% | 78.06% | 0.8315 |
| pii-injected-v1 (refined) | OpenMed/privacy-filter-nemotron | 96.14% | 94.51% | 0.9532 |
| pii-injected-v1 (refined) | OpenMed-PII-SuperClinical-Small (44M) | 93.99% | 92.41% | 0.9319 |
| pii-injected-v1 (refined) | OpenMed-PII-SuperClinical-Large (434M) | 96.60% | 95.78% | 0.9619 |
| pii-injected-hard-v1 (refined) | openai/privacy-filter | 59.26% | 63.37% | 0.6124 |
| pii-injected-hard-v1 (refined) | OpenMed/privacy-filter-nemotron | 65.22% | 44.55% | 0.5294 |
| pii-injected-hard-v1 (refined) | OpenMed-PII-SuperClinical-Small (44M) | 63.38% | 44.55% | 0.5233 |
| pii-injected-hard-v1 (refined) | OpenMed-PII-SuperClinical-Large (434M) | 74.70% | 61.39% | 0.6739 |
| pii-realistic-v1 (refined) | openai/privacy-filter | 85.08% | 89.02% | 0.8701 |
| pii-realistic-v1 (refined) | OpenMed/privacy-filter-nemotron | 82.50% | 76.30% | 0.7928 |
| pii-realistic-v1 (refined) | OpenMed-PII-SuperClinical-Small (44M) | 81.67% | 84.97% | 0.8329 |
| pii-realistic-v1 (refined) | OpenMed-PII-SuperClinical-Large (434M) | 93.06% | 93.06% | 0.9306 |

## Raw counts (model-only)

| Dataset | Source | TP | FP | FN | Items |
|---|---|---|---|---|---|
| pii-injected-v1 (refined) | openai/privacy-filter | 185 | 23 | 52 | 130 |
| pii-injected-v1 (refined) | OpenMed/privacy-filter-nemotron | 224 | 9 | 13 | 130 |
| pii-injected-v1 (refined) | OpenMed-PII-SuperClinical-Small | 219 | 14 | 18 | 130 |
| pii-injected-v1 (refined) | OpenMed-PII-SuperClinical-Large | 227 | 8 | 10 | 130 |
| pii-injected-hard-v1 (refined) | openai/privacy-filter | 64 | 44 | 37 | 130 |
| pii-injected-hard-v1 (refined) | OpenMed/privacy-filter-nemotron | 45 | 24 | 56 | 130 |
| pii-injected-hard-v1 (refined) | OpenMed-PII-SuperClinical-Small | 45 | 26 | 56 | 130 |
| pii-injected-hard-v1 (refined) | OpenMed-PII-SuperClinical-Large | 62 | 21 | 39 | 130 |
| pii-realistic-v1 (refined) | openai/privacy-filter | 154 | 27 | 19 | 130 |
| pii-realistic-v1 (refined) | OpenMed/privacy-filter-nemotron | 132 | 28 | 41 | 130 |
| pii-realistic-v1 (refined) | OpenMed-PII-SuperClinical-Small | 147 | 33 | 26 | 130 |
| pii-realistic-v1 (refined) | OpenMed-PII-SuperClinical-Large | 161 | 12 | 12 | 130 |

## Comparison against the original (unrefined) datasets, model-only

Comparing `(tp, fp, fn)` per model/dataset against `results/summary_no_regex.json`
(the original, unrefined-data model-only run behind `pii-results-model-only.md`):

| Config | Dataset | Original (tp, fp, fn) | Refined (tp, fp, fn) | Same? |
|---|---|---|---|---|
| privacy_filter | pii-injected-v1 | (185, 23, 52) | (185, 23, 52) | same |
| privacy_filter | pii-injected-hard-v1 | (65, 44, 36) | (64, 44, 37) | **diff** |
| privacy_filter | pii-realistic-v1 | (153, 29, 20) | (154, 27, 19) | **diff** |
| privacy_filter_nemotron | pii-injected-v1 | (226, 9, 11) | (224, 9, 13) | **diff** |
| privacy_filter_nemotron | pii-injected-hard-v1 | (42, 26, 59) | (45, 24, 56) | **diff** |
| privacy_filter_nemotron | pii-realistic-v1 | (134, 26, 39) | (132, 28, 41) | **diff** |
| pii_superclinical_small | pii-injected-v1 | (220, 13, 17) | (219, 14, 18) | **diff** |
| pii_superclinical_small | pii-injected-hard-v1 | (43, 29, 58) | (45, 26, 56) | **diff** |
| pii_superclinical_small | pii-realistic-v1 | (146, 33, 27) | (147, 33, 26) | **diff** |
| pii_superclinical_large | pii-injected-v1 | (226, 8, 11) | (227, 8, 10) | **diff** |
| pii_superclinical_large | pii-injected-hard-v1 | (63, 20, 38) | (62, 21, 39) | **diff** |
| pii_superclinical_large | pii-realistic-v1 | (161, 13, 12) | (161, 12, 12) | **diff** |

Without the regex safety net, differences show up in 11 of 12 combinations
(vs. 7 of 12 with regex active) — every shift is still small (≤3 entities,
both directions), but a larger fraction of runs move at all. This makes
sense: with the regex supplement present, many entities are caught by the
shape-matching regex regardless of what each model itself does, masking small
model-level differences. With regex removed, every model's own token
classifier is fully exposed to the exact digit content of each span, so the
refined data's changed values (different credit-card/phone/IP digits, plus
resampled duplicate names) more visibly nudge each model's own boundary and
confidence decisions. None of these shifts change the qualitative picture —
model-only recall on `pii-injected-hard-v1` is still catastrophically worse
than with regex for every model (e.g. `privacy_filter_nemotron`: 44.55%
recall model-only vs. 86.14% with regex), same as in the original comparison.

## Observations

- The core finding from `pii-results-model-only.md` holds unchanged on the
  refined data: removing the regex supplement drops recall substantially for
  every model on every dataset, confirming most of the with-regex numbers are
  driven by pattern-matchable formats (credit cards, SSNs, IPs, phones,
  emails), not the models' own NER.
- `pii-injected-hard-v1` is still by far the hardest dataset model-only
  (F1 0.52-0.67 across all four models), since its obfuscated formats
  (`[at]`, spelled-out "dot", defanged `[.]`) require the regex layer's
  specific pattern coverage that a general NER model wasn't trained to expect.
- `SuperClinical-Large` remains the strongest model-only performer on all
  three refined datasets, consistent with both the with-regex refined results
  and the original (unrefined) comparison.
- The refinement's changed values shift some models' own predictions by a
  handful of entities per dataset (see table above), but never enough to
  change which model ranks where, or to alter the top-level conclusion that
  the regex supplement is doing most of the heavy lifting on clean-format PII.
