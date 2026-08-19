"""Shared scoring logic for evaluating any token-classification PII model
against the local datasets. Model-specific label handling lives in
configs/<model>.py; this module is generic over that config.
"""

import importlib
import json

import regex_pii

DATASETS = [
    "pii_injected_v1.json",
    "pii_injected_hard_v1.json",
    "pii_realistic_v1.json",
]


def load_config(name):
    """name is a configs/ module name, e.g. 'privacy_filter'."""
    return importlib.import_module(f"configs.{name}")


def merge_spans(raw_entities, config):
    """Merge B/I/E/S-tagged token spans from the pipeline into full entity spans.

    Merges on the model's raw category regardless of LABEL_MAP membership, so
    every predicted entity (including unmapped ones) shows up in the result and
    is scored as a false positive if unmapped. EXCLUDED_LABELS are dropped
    entirely instead, so they never count toward tp/fp/fn.
    """
    merged = []
    current = None
    for ent in raw_entities:
        tag = ent["entity"]
        bio, _, label = tag.partition("-")
        if label in config.EXCLUDED_LABELS:
            if current:
                merged.append(current)
            current = None
            continue
        if bio in ("B", "S"):
            if current:
                merged.append(current)
            current = {
                "type": label,
                "start": ent["start"],
                "end": ent["end"],
                "score": ent["score"],
            }
            if bio == "S":
                merged.append(current)
                current = None
        elif bio in ("I", "E") and current and current["type"] == label:
            current["end"] = ent["end"]
            current["score"] = min(current["score"], ent["score"])
            if bio == "E":
                merged.append(current)
                current = None
        else:
            current = None
    if current:
        merged.append(current)
    return [span for span in merged if span["score"] >= config.SCORE_THRESHOLD]


def coalesce_adjacent_spans(spans, text, config):
    """Merge adjacent predicted spans that map to the same dataset type but
    carry different raw labels -- e.g. a model tagging "Lena" as first_name
    and "Silva" as last_name as two separate spans, when the dataset's
    expected entity is the single span "Lena Silva".

    Without this, spans_overlap's one-match-per-expected-entity rule lets
    only the first sub-span consume the expected entity; the second is
    counted as a false positive even though it's a correct partial detection
    of the same entity. Two spans are coalesced only if they're adjacent
    (separated by whitespace only, no other characters) and their
    LABEL_MAP-mapped type sets intersect.
    """
    spans = sorted(spans, key=lambda s: s["start"])
    coalesced = []
    for span in spans:
        if coalesced:
            prev = coalesced[-1]
            gap = text[prev["end"] : span["start"]]
            prev_types = config.LABEL_MAP.get(prev["type"]) or set()
            cur_types = config.LABEL_MAP.get(span["type"]) or set()
            if gap.strip() == "" and prev_types & cur_types:
                prev["end"] = span["end"]
                prev["score"] = min(prev["score"], span["score"])
                continue
        coalesced.append(dict(span))
    return coalesced


def spans_overlap(predicted, expected, config):
    """predicted['type'] is a model label; expected['type'] is a dataset type.

    A LABEL_MAP entry of None (rather than a set) means the label is a
    recognized-but-out-of-taxonomy prediction: it stays in the merged spans
    and counts as a false positive if predicted, instead of being dropped
    from scoring entirely like EXCLUDED_LABELS.
    """
    return (
        expected["type"] in (config.LABEL_MAP.get(predicted["type"]) or set())
        and predicted["start"] < expected["end"]
        and expected["start"] < predicted["end"]
    )


def _char_overlap(a, b):
    return a["start"] < b["end"] and b["start"] < a["end"]


def add_regex_spans(predicted, text, config):
    """Supplement model spans with regex-detected SSN/CREDIT_CARD/IP_ADDRESS
    spans. A regex span is dropped if it overlaps a model span whose label
    already maps to the same dataset type, since that would double-count a
    single true entity against spans_overlap's one-match-per-expected rule.
    """
    combined = list(predicted)
    for span in regex_pii.find_all(text):
        if any(
            _char_overlap(span, p) and span["type"] in (config.LABEL_MAP.get(p["type"]) or set())
            for p in combined
        ):
            continue
        combined.append(span)
    return combined


def match(predicted, expected, config):
    """Returns (matched_predicted_indices, matched_expected_indices)."""
    matched_expected = set()
    matched_predicted = set()
    for pi, p in enumerate(predicted):
        for ei, e in enumerate(expected):
            if ei in matched_expected:
                continue
            if spans_overlap(p, e, config):
                matched_expected.add(ei)
                matched_predicted.add(pi)
                break
    return matched_predicted, matched_expected


def score_predictions(predicted, expected, config):
    matched_predicted, matched_expected = match(predicted, expected, config)
    tp = len(matched_expected)
    fp = len(predicted) - len(matched_predicted)
    fn = len(expected) - len(matched_expected)
    return tp, fp, fn


def score_dataset(classifier, path, config):
    data = json.load(open(path))
    tp = fp = fn = 0
    raw_dump = []
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
        predicted = merge_spans(raw_clean, config)
        predicted = coalesce_adjacent_spans(predicted, text, config)
        if getattr(config, "USE_REGEX_SPANS", True):
            predicted = add_regex_spans(predicted, text, config)

        item_tp, item_fp, item_fn = score_predictions(predicted, expected, config)
        tp += item_tp
        fp += item_fp
        fn += item_fn

        raw_dump.append(
            {
                "index": index,
                "text": text,
                "raw_predictions": raw_clean,
                "regex_predictions": regex_pii.find_all(text),
                "expected_entities": expected,
            }
        )

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    metrics = {
        "dataset": data["dataset_name"],
        "items": len(data["items"]),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }
    return metrics, raw_dump
