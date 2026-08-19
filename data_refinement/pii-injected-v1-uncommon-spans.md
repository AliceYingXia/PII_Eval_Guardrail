# Uncommon PII Spans in `pii_injected_v1.json`

Review of all 130 items (237 expected PII entities) in `pii_injected_v1.json`, flagging spans that follow synthetic-generation patterns rather than real-world PII conventions.

## 1. Phone numbers with impossible NANP codes

US phone numbers can't have an area code or exchange (the first digit of either 3-digit group) start with 0 or 1, but several entries do:

- Exchange starts with 0: `(988) 075-1802`, `(408) 084-4533`, `(798) 036-0802`
- Area code starts with 0: `055-553-1229`, `+1 077 188 7280`, `+1 006 937 5279`, `+1 065 743 8304`, `054-567-7833`, `263-033-0233`, `+1 979 078 0958`
- Area code starts with 1: `(105) 880-0424`, `121-576-9689`

## 2. Credit card numbers with no valid network prefix

Real cards start with a recognized BIN: `4` (Visa), `51`–`55`/`2221`–`2720` (Mastercard), `34`/`37` (Amex), `6011`/`65` (Discover). These entries start with digits no issuer uses:

- `9042485748614186` — starts with 9, not a real BIN range at all
- `7140952532444893`, `7132149174298726` — start with 7, unassigned
- `3411 4689 4069 3133`, `3069 1236 5519 3403` — start with 3 but not `34`/`37` (Amex prefixes)

Beyond the prefix issue, the numbers also aren't algorithmically valid: of the 30 unique credit card values in the file, 28 fail the Luhn checksum (the mod-10 check digit algorithm every real card number satisfies). Only `1117-7006-4122-5662` and `8860-2196-8673-1603` happen to pass — almost certainly by chance rather than by construction. This confirms the numbers are randomly generated digit strings rather than realistic (if fake) card numbers.

## 3. IP address in a reserved/unroutable block

`242.41.28.168` falls in `240.0.0.0/4`, the block reserved for future use — never seen in real traffic, not even in private or multicast ranges.

## 4. Email domains that are reserved placeholder domains (RFC 2606)

Nearly all emails use non-resolving test/reserved domains rather than domains real leaked PII would use:

- `example.com` (e.g. `priya_khan@example.com`)
- `corp.example` (e.g. `alex.berg@corp.example`)
- `mail.test` (e.g. `sven_larsson@mail.test`)
- `acme.io` (repeated across many entries as a fictitious company domain)

## 5. Repeated identical names/addresses across unrelated records

Several names recur across otherwise-unrelated records — e.g. `Priya Tanaka` appears 3 times, `Theo Novak` twice — and addresses follow a small fixed template:

`"<house number> <Oak Rd|Maple Ave|Elm St|Birch Ln|Park Blvd>, Springfield, IL 62704"`

(also `Austin, TX 78701` and `Denver, CO 80203` variants), with only the house number changing. `Springfield` is a nod to the fictional city from *The Simpsons*. Real PII wouldn't cluster like this — it's the fingerprint of templated data generation.

## Why this matters

These patterns are expected and appropriate for a synthetic eval fixture (it avoids embedding real PII). They're worth flagging if this file is ever cited as "realistic" test coverage for validators that apply real-world checks (Luhn, NANP, BIN ranges) — a stricter validator could reject some of these spans as malformed before PII-masking logic even runs.

## Fixes applied

[fix_pii_injected_v1.py](fix_pii_injected_v1.py) regenerates the flagged spans and writes the result to `pii_injected_v1.fixed.json`, staged alongside the original for review rather than overwriting it. Run with `python3 fix_pii_injected_v1.py` (seeded, so output is reproducible/diffable).

For each entity in every item, the script rewrites the value in place inside `input.text` and recomputes that entity's `start`/`end` offsets (shifting all later entities in the same item if the replacement changes length), then mirrors the updated entity list into `must_be_masked`.

**What was changed:**

| Category | Fix |
|---|---|
| 1. Phone numbers | Any 3-digit area code or exchange group with a leading `0`/`1` gets that leading digit redrawn to `2`–`9`. Only the invalid digit is touched, so length and formatting are unchanged and no offset shift is needed. |
| 2. Credit cards | Prefix rewritten to a real BIN (`4` Visa, `51`–`55` Mastercard, `34`/`37` Amex, `6011`/`65` Discover) matching the existing digit count, middle digits redrawn randomly, and the final digit recomputed via the Luhn checksum. Separator style (space/dash/none) and length are preserved. |
| 3. Reserved IP (`242.41.28.168`) | First octet resampled away from reserved/unroutable ranges (`0`, `10`, `127`, `169`, `172`, `224`–`255`), preferring a same-digit-count replacement to avoid offset shifts. |
| 4. Reserved email domains | **Not changed** — kept as documented tradeoff above (RFC 2606 domains are intentionally safe for test fixtures; swapping to a fictitious-but-real-TLD domain risks colliding with an actually-registered domain). |
| 5. Duplicate names (`Priya Tanaka` ×3, `Theo Novak` ×2) | Each repeat resampled to a unique `first last` combination from an expanded name pool, guaranteed not to collide with any name already used elsewhere in the file. |
| 5. Address templates | **Not changed** — verified all 28 address strings are already literally unique (only the street/city template itself repeats, with different house numbers each time), so there was no actual duplicate to fix. |

**Bug found and fixed during implementation:** the first version of the offset-recompute logic skipped updating an entity's `start`/`end` whenever its *own* value was unchanged (`if new_val == e["text"]: continue`), even though an earlier entity in the same text had already shifted the string by changing length. This caused offset drift for any unchanged entity following a changed one (e.g. an `ADDRESS` after a resampled `NAME` earlier in the same text). Fixed by always updating `start`/`end` from the accumulated shift, and only skipping the text-splice step when the value is unchanged.

**Verification performed on `pii_injected_v1.fixed.json`:**
- `text[start:end] == entity_text` holds for every entity in every item (0 offset mismatches).
- No `PHONE` entity has an area/exchange code starting with `0` or `1`.
- Every `CREDIT_CARD` entity passes the Luhn checksum.
- No `NAME` value appears more than once across the dataset.
- No `IP_ADDRESS` entity remains in the `240.0.0.0/4` reserved block.
