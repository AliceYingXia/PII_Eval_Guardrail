"""List every false-negative (missed) expected entity for a given model,
using its cached raw_results/<config_name>/*.json predictions rather than
re-running the model.

Usage: python3 analyze_fn.py <config_name>
Example: python3 analyze_fn.py privacy_filter
"""

import json
import os
import sys

import pii_eval_lib as lib


def analyze(path, config):
    items = json.load(open(path))
    misses = []
    for item in items:
        text = item["text"]
        expected = item["expected_entities"]
        predicted = lib.merge_spans(item["raw_predictions"], config)
        predicted = lib.coalesce_adjacent_spans(predicted, text, config)
        if getattr(config, "USE_REGEX_SPANS", True):
            predicted = lib.add_regex_spans(predicted, text, config)

        _, matched_expected = lib.match(predicted, expected, config)

        for ei, e in enumerate(expected):
            if ei in matched_expected:
                continue
            snippet_start = max(0, e["start"] - 25)
            snippet_end = min(len(text), e["end"] + 25)
            misses.append(
                {
                    "index": item["index"],
                    "type": e["type"],
                    "text": e["text"],
                    "context": text[snippet_start:snippet_end],
                }
            )
    return misses


def main():
    config_name = sys.argv[1] if len(sys.argv) > 1 else "privacy_filter"
    config = lib.load_config(config_name)
    raw_dir = os.path.join("raw_results", config.SHORT_NAME)

    for dataset_path in lib.DATASETS:
        raw_path = os.path.join(raw_dir, dataset_path)
        misses = analyze(raw_path, config)
        print(f"\n=== {dataset_path}: {len(misses)} false negatives ===")
        by_type = {}
        for m in misses:
            by_type.setdefault(m["type"], []).append(m)
        for t, ms in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
            print(f"  {t}: {len(ms)}")
        for m in misses:
            print(f"  [{m['index']}] {m['type']!r} {m['text']!r}  ...{m['context']}...")


if __name__ == "__main__":
    main()
