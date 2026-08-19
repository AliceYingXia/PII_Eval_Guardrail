"""List every false-negative and false-positive for a given model against a
refined dataset (data_refinement/*.fixed.json), running the classifier fresh
since no cached raw_results/ exist for the refined files.

Usage: python3 analyze_refined.py <config_name> <refined_dataset_path>
Example: python3 analyze_refined.py pii_superclinical_large data_refinement/pii_injected_v1.fixed.json
"""
import json
import sys

from transformers import pipeline

import pii_eval_lib as lib


def main():
    config_name = sys.argv[1]
    dataset_path = sys.argv[2]
    config = lib.load_config(config_name)
    classifier = pipeline("token-classification", model=config.MODEL_NAME)

    data = json.load(open(dataset_path))
    misses = []
    extras = []

    for index, item in enumerate(data["items"]):
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
        if getattr(config, "USE_REGEX_SPANS", True):
            predicted = lib.add_regex_spans(predicted, text, config)

        matched_predicted, matched_expected = lib.match(predicted, expected, config)

        for ei, e in enumerate(expected):
            if ei in matched_expected:
                continue
            s, en = max(0, e["start"] - 25), min(len(text), e["end"] + 25)
            misses.append(
                {"index": index, "type": e["type"], "text": e["text"], "context": text[s:en]}
            )
        for pi, p in enumerate(predicted):
            if pi in matched_predicted:
                continue
            s, en = max(0, p["start"] - 25), min(len(text), p["end"] + 25)
            extras.append(
                {
                    "index": index,
                    "type": p["type"],
                    "text": text[p["start"] : p["end"]],
                    "context": text[s:en],
                }
            )

    print(f"\n=== {dataset_path} / {config_name}: {len(misses)} false negatives ===")
    by_type = {}
    for m in misses:
        by_type.setdefault(m["type"], []).append(m)
    for t, ms in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        print(f"  {t}: {len(ms)}")
    for m in misses:
        print(f"  [{m['index']}] {m['type']!r} {m['text']!r}  ...{m['context']}...")

    print(f"\n=== {dataset_path} / {config_name}: {len(extras)} false positives ===")
    by_type = {}
    for m in extras:
        by_type.setdefault(m["type"], []).append(m)
    for t, ms in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        print(f"  {t}: {len(ms)}")
    for m in extras:
        print(f"  [{m['index']}] {m['type']!r} {m['text']!r}  ...{m['context']}...")


if __name__ == "__main__":
    main()
