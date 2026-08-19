"""Regex-based detectors for SSN, credit card, IP address, phone, and email
spans.

Produces spans shaped like the model/dataset entities (type/start/end/text)
so they can be scored with the same spans_overlap logic used in
eval_privacy_filter.py, or merged in as a fallback/supplement to the model.
"""

import re

# SSN: NNN-NN-NNNN or NNN NN NNNN, excludes obviously invalid area/group of 000
# and the reserved 666/900-999 area numbers.
SSN_RE = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b"
)

# SSN, dotted 3-2-4 grouping (e.g. "357.79.6506") -- adversarial datasets use
# this to camouflage an SSN as IP-address-looking punctuation. Distinguished
# from a dotted PHONE by group sizes (3-2-4, 9 digits total) and from an IPv4
# address by having only 2 dots (3 groups) instead of 3 dots (4 octets).
SSN_DOTTED_RE = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}\.(?!00)\d{2}\.(?!0000)\d{4}\b"
)

# SSN, bare unbroken 9-digit run with no separators at all.
SSN_BARE_RE = re.compile(r"\b(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}\b")

# PHONE: dotted 3-3-4 grouping (e.g. "018.048.4784", 10 digits total) --
# distinguished from SSN_DOTTED_RE by group sizes, not by separator.
PHONE_DOTTED_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{4}\b")

# PHONE: bare unbroken 10-digit run with no separators at all.
PHONE_BARE_RE = re.compile(r"\b\d{10}\b")

# EMAIL: standard local@domain, but tolerant of spaces inserted around the
# "@" (e.g. "diego.morgan @ corp.example") -- a common obfuscation to dodge
# naive email regexes.
EMAIL_RE = re.compile(
    r"\b[\w.+-]+[ \t]*@[ \t]*[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b"
)

# EMAIL, fully spelled out (e.g. "diego dot novak at acme dot io") -- local
# and domain parts are word tokens joined by " dot ", separated from each
# other by " at ". Requires at least one " dot " in the domain half so a TLD
# is present, mirroring how a real domain always has a dot.
EMAIL_SPELLED_RE = re.compile(
    r"\b\w+(?:[ ]dot[ ]\w+)*[ ]at[ ]\w+(?:[ ]dot[ ]\w+)+\b", re.IGNORECASE
)

# Credit card: 13-19 digits, optionally grouped by spaces, dashes, or dots in
# blocks of 4 (with a possibly shorter final/first block), then Luhn-checked.
# Dots are unambiguous here since the first block requires 4 digits -- IPv4
# octets (1-3 digits) and dotted phone/SSN formats (3-digit first block)
# can't match this pattern.
CREDIT_CARD_RE = re.compile(
    r"\b\d{4}[ .-]?\d{4,7}[ .-]?\d{4,7}(?:[ .-]?\d{1,4})?\b"
)

# IPv4: four 0-255 octets, separated by a plain dot, a "[.]"-defanged dot
# (common IOC notation in security contexts), or a dot with surrounding
# spaces (e.g. "127 . 34 . 27 . 130"). IPv6: hex groups separated by colons
# (no attempt at full RFC validation, just a practical match for 8-group or
# "::"-compressed forms).
_IPV4_OCTET = r"(?:25[0-5]|2[0-4]\d|1?\d{1,2})"
_IPV4_SEP = r"(?:\s*\[\.\]\s*|\s*\.\s*)"
IPV4_RE = re.compile(
    rf"\b{_IPV4_OCTET}(?:{_IPV4_SEP}{_IPV4_OCTET}){{3}}\b"
)
IPV6_RE = re.compile(
    r"\b(?:[0-9A-Fa-f]{1,4}:){2,7}(?:[0-9A-Fa-f]{1,4}|:)(?::[0-9A-Fa-f]{1,4})*\b"
)


def _luhn_ok(digits):
    total = 0
    for i, d in enumerate(reversed(digits)):
        d = int(d)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _dedupe_spans(spans):
    """Drop later spans that overlap an already-accepted span of the same
    type -- multiple patterns (e.g. dotted vs bare SSN) can otherwise match
    the same text and double-count one entity."""
    kept = []
    for span in spans:
        if any(
            span["type"] == k["type"] and _char_overlap(span, k) for k in kept
        ):
            continue
        kept.append(span)
    return kept


def _char_overlap(a, b):
    return a["start"] < b["end"] and b["start"] < a["end"]


def find_ssns(text):
    spans = (
        [
            {"type": "SSN", "start": m.start(), "end": m.end(), "text": m.group()}
            for m in SSN_RE.finditer(text)
        ]
        + [
            {"type": "SSN", "start": m.start(), "end": m.end(), "text": m.group()}
            for m in SSN_DOTTED_RE.finditer(text)
        ]
        + [
            {"type": "SSN", "start": m.start(), "end": m.end(), "text": m.group()}
            for m in SSN_BARE_RE.finditer(text)
        ]
    )
    return _dedupe_spans(spans)


def find_phones(text):
    spans = [
        {"type": "PHONE", "start": m.start(), "end": m.end(), "text": m.group()}
        for m in PHONE_DOTTED_RE.finditer(text)
    ] + [
        {"type": "PHONE", "start": m.start(), "end": m.end(), "text": m.group()}
        for m in PHONE_BARE_RE.finditer(text)
    ]
    return _dedupe_spans(spans)


def find_emails(text):
    spans = [
        {"type": "EMAIL", "start": m.start(), "end": m.end(), "text": m.group()}
        for m in EMAIL_RE.finditer(text)
    ] + [
        {"type": "EMAIL", "start": m.start(), "end": m.end(), "text": m.group()}
        for m in EMAIL_SPELLED_RE.finditer(text)
    ]
    return _dedupe_spans(spans)


# Known issuer identification number (IIN/BIN) prefixes, checked against the
# full digit string length + leading digits (not just the leading 4-block,
# since input may be grouped differently). Ranges are inclusive prefixes.
_IIN_PREFIXES = (
    # Visa
    (("4",), 13),
    (("4",), 16),
    (("4",), 19),
    # Mastercard: 51-55 and 2221-2720
    (tuple(str(n) for n in range(51, 56)), 16),
    (tuple(str(n) for n in range(2221, 2721)), 16),
    # American Express: 34, 37
    (("34", "37"), 15),
    # Discover: 6011, 644-649, 65
    (("6011",), 16),
    (tuple(str(n) for n in range(644, 650)), 16),
    (("65",), 16),
    # Diners Club: 300-305, 36, 38
    (tuple(str(n) for n in range(300, 306)), 14),
    (("36", "38"), 14),
    # JCB: 3528-3589
    (tuple(str(n) for n in range(3528, 3590)), 16),
)


def _iin_ok(digits):
    length = len(digits)
    for prefixes, expected_len in _IIN_PREFIXES:
        if length != expected_len:
            continue
        if any(digits.startswith(p) for p in prefixes):
            return True
    return False


def find_credit_cards(text):
    """Luhn and IIN match are both confidence signals, not hard filters.
    Real-world card numbers are always Luhn-valid, but this detector is also
    used against synthetic/test data (e.g. randomly generated numbers in
    eval datasets) that share the shape of a card number without passing
    Luhn -- rejecting those would mean systematically missing exactly the
    kind of clean, unbroken-digit-run PII this regex exists to catch. The
    known-prefix list also only covers major networks (Visa, Mastercard,
    Amex, Discover, Diners, JCB), so a hard IIN filter would reject valid
    cards from other schemes (UnionPay, Maestro, RuPay, store cards, etc.).
    """
    spans = []
    for m in CREDIT_CARD_RE.finditer(text):
        digits = re.sub(r"[ .-]", "", m.group())
        if 13 <= len(digits) <= 19:
            spans.append(
                {
                    "type": "CREDIT_CARD",
                    "start": m.start(),
                    "end": m.end(),
                    "text": m.group(),
                    "luhn_ok": _luhn_ok(digits),
                    "known_iin": _iin_ok(digits),
                }
            )
    return spans


def find_ip_addresses(text):
    spans = [
        {"type": "IP_ADDRESS", "start": m.start(), "end": m.end(), "text": m.group()}
        for m in IPV4_RE.finditer(text)
    ]
    for m in IPV6_RE.finditer(text):
        value = m.group()
        # Require compression ("::"), 4+ groups, or a hex letter (a-f) to
        # avoid matching plain HH:MM:SS timestamps, which are also valid
        # colon-separated decimal-digit sequences.
        if "::" in value or value.count(":") >= 3 or re.search(r"[A-Fa-f]", value):
            spans.append(
                {"type": "IP_ADDRESS", "start": m.start(), "end": m.end(), "text": value}
            )
    return spans


def find_all(text):
    spans = (
        find_ssns(text)
        + find_credit_cards(text)
        + find_ip_addresses(text)
        + find_phones(text)
        + find_emails(text)
    )
    return sorted(spans, key=lambda s: s["start"])


if __name__ == "__main__":
    sample = (
        "SSN 539-38-3020, card 4111 1111 1111 1111, "
        "server at 192.168.1.10 and fe80::1ff:fe23:4567:890a"
    )
    for span in find_all(sample):
        print(span)
