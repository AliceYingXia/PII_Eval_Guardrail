"""
One-off regeneration script for pii_injected_hard_v1.json.

Fixes flagged in pii-injected-hard-v1-uncommon-spans.md:
  1. Phone numbers with impossible NANP area/exchange codes (leading 0/1)
  2. Credit card numbers with no valid network prefix / failing Luhn
  3. IP addresses in reserved/unroutable blocks (127.0.0.0/8, 240.0.0.0/4)
  4. Duplicate NAME values reused across unrelated records

Each fix rewrites only the digits/characters needed to satisfy the
constraint, preserving original formatting/punctuation/length wherever
possible so entity offsets don't shift. Where a fix changes length, offsets
for all later entities in the same item are recomputed.

Deliberately NOT changed:
  - SSN formatting (space/dot/dashless variants) -- these are an
    intentional part of this "hard" fixture's obfuscation coverage, and
    the underlying digit values are already in valid ranges.
  - Defanged emails ("sven.larsson[at]example.com") and defanged/padded
    IPs ("251 . 124 . 140 . 69") -- intentional adversarial hard-positive
    cases per metadata.obfuscated=true, not generation artifacts.

Usage: python3 fix_pii_injected_hard_v1.py
Writes pii_injected_hard_v1.fixed.json for review before it replaces the original.
"""
import json
import random

random.seed(42)  # deterministic output for reviewable diffs

SRC = "../pii_injected_hard_v1.json"
DST = "pii_injected_hard_v1.fixed.json"

# IPs are only "fixed" if their first octet falls in a reserved block AND
# the value isn't already defanged/padded obfuscation we want to preserve
# as-is content-wise. We only resample the numeric octet, keeping whatever
# separator style (plain dots, spaces around dots, bracket-defanged) as-is.
RESERVED_FIRST_OCTETS = {10, 127} | set(range(224, 256))

FIRST_NAMES = [
    "Ravi", "Priya", "Alex", "Diego", "Nina", "Sven", "Sara", "Theo",
    "Omar", "Maria", "Lena", "Yuki", "Sofia", "Elena", "Marcus", "Aisha",
    "Kenji", "Camila", "Noah", "Ines",
]
LAST_NAMES = [
    "Patel", "Rossi", "Silva", "Berg", "Gonzalez", "Tanaka", "Khan",
    "Larsson", "Morgan", "Novak", "Reyes", "Dubois", "Osei", "Haddad",
    "Lindgren", "Petrova", "Nakamura", "Alvarez", "Kowalski", "Fischer",
]


def luhn_checksum(digits_no_check):
    total = 0
    for i, d in enumerate(reversed(digits_no_check)):
        d = int(d)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - (total % 10)) % 10


def fix_phone(text):
    """Replace any leading 0/1 in a 3-digit digit-run (area code / exchange,
    regardless of separator style) with a digit 2-9, in place."""
    out = list(text)
    run_start = None
    for i, ch in enumerate(out + [" "]):
        is_digit = i < len(out) and ch.isdigit()
        if is_digit and run_start is None:
            run_start = i
        elif not is_digit and run_start is not None:
            run_len = i - run_start
            if run_len == 3 and out[run_start] in ("0", "1"):
                out[run_start] = str(random.randint(2, 9))
            run_start = None
    # 10-digit unseparated numbers (e.g. "1172582948") have no punctuation
    # boundary between area code and exchange, so the run-based scan above
    # sees one 10-digit run and never fires. Handle that case explicitly.
    digits_only = "".join(c for c in text if c.isdigit())
    if len(digits_only) == 10 and text.strip() == digits_only:
        chars = list(text)
        for pos in (0, 3):
            if chars[pos] in ("0", "1"):
                chars[pos] = str(random.randint(2, 9))
        return "".join(chars)
    return "".join(out)


VALID_PREFIXES = [
    ("4", 16),          # Visa
    ("51", 16), ("52", 16), ("53", 16), ("54", 16), ("55", 16),  # Mastercard
    ("34", 15), ("37", 15),  # Amex
    ("6011", 16), ("65", 16),  # Discover
]


def fix_credit_card(text):
    """Rewrite prefix to a real network BIN and recompute the Luhn check
    digit, keeping punctuation/grouping and overall length unchanged."""
    digit_positions = [i for i, ch in enumerate(text) if ch.isdigit()]
    n = len(digit_positions)
    prefix, _ = random.choice([p for p in VALID_PREFIXES if p[1] == n] or [("4", n)])
    digits = list(prefix) + [str(random.randint(0, 9)) for _ in range(n - len(prefix) - 1)]
    check = luhn_checksum(digits)
    digits.append(str(check))
    out = list(text)
    for pos, d in zip(digit_positions, digits):
        out[pos] = d
    return "".join(out)


def fix_ip(text):
    """Resample the first octet away from reserved/unroutable ranges,
    preserving whatever separator/defanging style surrounds it."""
    # locate the first run of digits in the string (the first octet)
    start = None
    for i, ch in enumerate(text):
        if ch.isdigit():
            start = i
            break
    end = start
    while end < len(text) and text[end].isdigit():
        end += 1
    orig_len = end - start
    candidates = [
        o for o in range(1, 224)
        if o not in RESERVED_FIRST_OCTETS and o != 169
        and len(str(o)) == orig_len
    ]
    if not candidates:
        candidates = [o for o in range(1, 224) if o not in RESERVED_FIRST_OCTETS]
    return text[:start] + str(random.choice(candidates)) + text[end:]


def octet_is_reserved(text):
    start = None
    for i, ch in enumerate(text):
        if ch.isdigit():
            start = i
            break
    end = start
    while end < len(text) and text[end].isdigit():
        end += 1
    first_octet = int(text[start:end])
    return first_octet in RESERVED_FIRST_OCTETS


def make_replacement(entity, used_names):
    t = entity["type"]
    old = entity["text"]
    if t == "PHONE":
        return fix_phone(old)
    if t == "CREDIT_CARD":
        return fix_credit_card(old)
    if t == "IP_ADDRESS":
        if octet_is_reserved(old):
            return fix_ip(old)
        return old
    if t == "NAME":
        if used_names[old] > 1:
            used_names[old] -= 1
            while True:
                candidate = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                if candidate not in used_names:
                    return candidate
        return old
    return old


def apply_fix(item, used_names):
    text = item["input"]["text"]
    entities = item["expected_output"]["entities"]
    ordered = sorted(range(len(entities)), key=lambda i: entities[i]["start"])
    delta = 0
    for idx in ordered:
        e = entities[idx]
        start, end = e["start"] + delta, e["end"] + delta
        assert text[start:end] == e["text"], f"offset drift: {text[start:end]!r} != {e['text']!r}"
        new_val = make_replacement(e, used_names)
        if new_val != e["text"]:
            text = text[:start] + new_val + text[end:]
            e["text"] = new_val
            delta += len(new_val) - (end - start)
        e["start"] = start
        e["end"] = start + len(new_val)
    item["input"]["text"] = text
    item["expected_output"]["must_be_masked"] = entities


def main():
    with open(SRC) as f:
        data = json.load(f)

    name_counts = {}
    for it in data["items"]:
        for e in it["expected_output"]["entities"]:
            if e["type"] == "NAME":
                name_counts[e["text"]] = name_counts.get(e["text"], 0) + 1

    for item in data["items"]:
        apply_fix(item, name_counts)

    with open(DST, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {DST}")


if __name__ == "__main__":
    main()
