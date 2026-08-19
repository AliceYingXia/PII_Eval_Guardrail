"""
One-off regeneration script for pii_realistic_v1.json.

Fixes flagged in pii-realistic-v1-uncommon-spans.md:
  1. Phone numbers with impossible NANP area/exchange codes (leading 0/1)
  2. Credit card numbers with no valid network prefix and failing Luhn
  3. IP address in the reserved 224.0.0.0/4 block (225.161.4.57)
  6. Duplicate NAME values reused across unrelated records

Each fix rewrites only the digits/characters needed to satisfy the
constraint, preserving original formatting/punctuation/length wherever
possible so entity offsets don't shift. Where a fix changes length, offsets
for all later entities in the same item are recomputed.

Deliberately NOT changed:
  - SSNs formatted with spaces instead of dashes (2 of 7) -- left as-is
    per explicit instruction.
  - Defanged emails ("priya dot khan at corp dot example") and defanged IPs
    (136[.]41[.]26[.]35) -- these are intentional obfuscation hard cases,
    not generation artifacts; see section 5 of the companion .md doc.
  - The Evergreen Terrace / Springfield address template reuse -- addresses
    are already literally unique strings (see section 7 of the doc).

Usage: python3 fix_pii_realistic_v1.py
Writes pii_realistic_v1.fixed.json for review before it replaces the original.
"""
import json
import random

random.seed(42)  # deterministic output for reviewable diffs

SRC = "../pii_realistic_v1.json"
DST = "pii_realistic_v1.fixed.json"

RESERVED_IP = "225.161.4.57"

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
    """Resample the first octet of the one flagged reserved-range IP,
    preferring a same-digit-count replacement to avoid offset shifts."""
    parts = text.split(".")
    orig_len = len(parts[0])
    candidates = [
        o for o in range(1, 224)
        if o not in ({10, 127} | set(range(224, 256))) and o != 169 and o != 172
        and len(str(o)) == orig_len
    ]
    if not candidates:
        candidates = [o for o in range(1, 224) if o not in ({10, 127} | set(range(224, 256)))]
    parts[0] = str(random.choice(candidates))
    return ".".join(parts)


def make_replacement(entity, used_names):
    t = entity["type"]
    old = entity["text"]
    if t == "PHONE":
        return fix_phone(old)
    if t == "CREDIT_CARD":
        return fix_credit_card(old)
    if t == "IP_ADDRESS":
        if old == RESERVED_IP:
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
