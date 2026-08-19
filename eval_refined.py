"""Evaluate all four configured PII models against the refined datasets in
data_refinement/*.fixed.json, computing both with-regex and without-regex
metrics from a single classifier pass per model/dataset (regex/Luhn are
scoring-time steps, not model-inference-time steps, so both can be derived
from the same raw predictions without re-running the model).

Usage: python3 eval_refined.py
Writes results/summary_refined_with_regex.json and
results/summary_refined_no_regex.json.
"""
import json
import os

from transformers import pipeline

import pii_eval_lib as lib

CONFIGS = [
    "privacy_filter",
    "privacy_filter_nemotron",
    "pii_superclinical_small",
    "pii_superclinical_large",
]

REFINED_DATASETS = [
    ("pii-injected-v1", "data_refinement/pii_injected_v1.fixed.json"),
    ("pii-injected-hard-v1", "data_refinement/pii_injected_hard_v1.fixed.json"),
    ("pii-realistic-v1", "data_refinement/pii_realistic_v1.fixed.json"),
]


def _metrics(tp, fp, fn, items):
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "items": items,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def score_refined_dataset(classifier, path, config):
    data = json.load(open(path))
    tp_r = fp_r = fn_r = 0
    tp_n = fp_n = fn_n = 0
    for item in data["items"]:
        text = item["input"]["text"]
        expected = item["expected_output"]["entities"]
        raw = classifier(text)
        raw_clean = [
            {
                "entity": r["entity"],
                "word": r["word"],
                "start": int(r["start"]),
                "end": int(r["end"]),
                "score": float(r["score"]),
            }
            for r in raw
        ]
        predicted = lib.merge_spans(raw_clean, config)
        predicted = lib.coalesce_adjacent_spans(predicted, text, config)

        # without regex
        item_tp, item_fp, item_fn = lib.score_predictions(predicted, expected, config)
        tp_n += item_tp
        fp_n += item_fp
        fn_n += item_fn

        # with regex (only if this config enables it, mirroring score_dataset)
        predicted_r = predicted
        if getattr(config, "USE_REGEX_SPANS", True):
            predicted_r = lib.add_regex_spans(predicted, text, config)
        item_tp, item_fp, item_fn = lib.score_predictions(predicted_r, expected, config)
        tp_r += item_tp
        fp_r += item_fp
        fn_r += item_fn

    n = len(data["items"])
    return _metrics(tp_r, fp_r, fn_r, n), _metrics(tp_n, fp_n, fn_n, n)


def main():
    with_regex_summary = {}
    no_regex_summary = {}

    for config_name in CONFIGS:
        config = lib.load_config(config_name)
        classifier = pipeline("token-classification", model=config.MODEL_NAME)
        with_regex_summary[config_name] = {}
        no_regex_summary[config_name] = {}

        for dataset_name, path in REFINED_DATASETS:
            with_r, no_r = score_refined_dataset(classifier, path, config)
            with_regex_summary[config_name][dataset_name] = with_r
            no_regex_summary[config_name][dataset_name] = no_r
            print(f"{config_name} / {dataset_name}: with_regex={with_r} no_regex={no_r}")

    os.makedirs("results", exist_ok=True)
    with open("results/summary_refined_with_regex.json", "w") as f:
        json.dump(with_regex_summary, f, indent=2)
    with open("results/summary_refined_no_regex.json", "w") as f:
        json.dump(no_regex_summary, f, indent=2)
    print("wrote results/summary_refined_with_regex.json and results/summary_refined_no_regex.json")


if __name__ == "__main__":
    main()
