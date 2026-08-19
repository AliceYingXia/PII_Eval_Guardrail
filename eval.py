"""Evaluate a token-classification PII model against the three local
datasets, using its configs/<name>.py label mapping.

Usage: python3 eval.py <config_name> [<config_name> ...]
Example: python3 eval.py privacy_filter
"""

import json
import os
import sys

from transformers import pipeline

import pii_eval_lib as lib


def run(config_name):
    config = lib.load_config(config_name)
    classifier = pipeline("token-classification", model=config.MODEL_NAME)

    out_dir = os.path.join("raw_results", config.SHORT_NAME)
    os.makedirs(out_dir, exist_ok=True)

    results = []
    for path in lib.DATASETS:
        metrics, raw_dump = lib.score_dataset(classifier, path, config)
        results.append(metrics)
        out_path = os.path.join(out_dir, path)
        json.dump(raw_dump, open(out_path, "w"), indent=2)
        print(f"wrote {len(raw_dump)} items to {out_path}")

    return results


def update_summary(config_name, results):
    os.makedirs("results", exist_ok=True)
    summary_path = os.path.join("results", "summary.json")
    summary = json.load(open(summary_path)) if os.path.exists(summary_path) else {}
    summary[config_name] = {r["dataset"]: r for r in results}
    json.dump(summary, open(summary_path, "w"), indent=2)
    print(f"updated {summary_path}")


def main():
    config_names = sys.argv[1:] or ["privacy_filter"]
    for config_name in config_names:
        results = run(config_name)
        update_summary(config_name, results)
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
