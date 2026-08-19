"""Rescore cached raw_results/ predictions with regex supplementing disabled,
to isolate each model's own performance from the regex_pii layer.

Usage: python3 rescore_no_regex.py
"""

import json
import os

import pii_eval_lib as lib

CONFIGS = [
    "privacy_filter",
    "privacy_filter_nemotron",
    "pii_superclinical_small",
    "pii_superclinical_large",
]


def main():
    summary = {}
    for config_name in CONFIGS:
        config = lib.load_config(config_name)
        summary[config_name] = {}
        for dataset in lib.DATASETS:
            path = os.path.join("raw_results", config.SHORT_NAME, dataset)
            raw_dump = json.load(open(path))
            tp = fp = fn = 0
            for item in raw_dump:
                predicted = lib.merge_spans(item["raw_predictions"], config)
                predicted = lib.coalesce_adjacent_spans(predicted, item["text"], config)
                # USE_REGEX_SPANS intentionally NOT applied here.
                item_tp, item_fp, item_fn = lib.score_predictions(
                    predicted, item["expected_entities"], config
                )
                tp += item_tp
                fp += item_fp
                fn += item_fn

            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
            dataset_name = dataset.replace(".json", "").replace("_", "-")
            summary[config_name][dataset_name] = {
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "items": len(raw_dump),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
            }

    os.makedirs("results", exist_ok=True)
    out_path = os.path.join("results", "summary_no_regex.json")
    json.dump(summary, open(out_path, "w"), indent=2)
    print(f"wrote {out_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
