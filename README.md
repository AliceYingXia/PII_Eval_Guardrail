# PII Eval Guardrail

Evaluation harness for benchmarking token-classification PII detection models (e.g. `openai/privacy-filter`, OpenMed PII models) against a set of local PII datasets, with optional regex/Luhn supplementing.

## Datasets

- `pii_injected_v1.json`
- `pii_injected_hard_v1.json`
- `pii_realistic_v1.json`
- `data_refinement/*.fixed.json` — refined/corrected versions of the above (see `data_refinement/pii-fix-summary.md`)

## Models / configs

Each model is configured under `configs/<name>.py`, defining its HF model name, excluded labels, score threshold, and a label map from model entity types to dataset entity types:

- `privacy_filter` (openai/privacy-filter)
- `privacy_filter_nemotron` (OpenMed/privacy-filter-nemotron)
- `pii_superclinical_small` (OpenMed-PII-SuperClinical-Small, 44M)
- `pii_superclinical_large` (OpenMed-PII-SuperClinical-Large, 434M)

## Usage

Run an evaluation for one or more configs:

```
python3 eval.py <config_name> [<config_name> ...]
# e.g. python3 eval.py privacy_filter
```

This writes per-item predictions to `raw_results/<config_name>/` and updates `results/summary.json`.

Rescore cached predictions with regex supplementing disabled, to isolate model-only performance:

```
python3 rescore_no_regex.py
```

Evaluate all configured models against the refined datasets in one pass:

```
python3 eval_refined.py
```

Inspect errors from cached predictions without re-running the model:

```
python3 analyze_fn.py <config_name>   # false negatives (missed entities)
python3 analyze_fp.py <config_name>   # false positives (spurious entities)
```

## Results

- `results/summary.json`, `results/summary_no_regex.json` — aggregated precision/recall/F1 per model/dataset
- `pii-results-comparison.md` — side-by-side comparison across models and Skyflow
- `pii-results-model-only.md` — model-only (no regex) results

## Layout

- `pii_eval_lib.py` — shared scoring logic (span merging, matching, metrics)
- `regex_pii.py` — regex/Luhn-based supplemental PII detection
- `configs/` — per-model configuration
- `raw_results/` — cached per-item model predictions
- `data_refinement/` — dataset cleanup scripts and refined datasets
