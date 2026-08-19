# PII Fix Summary — What Changed and Why

Summary of the fixes applied across `pii_injected_v1.json`, `pii_realistic_v1.json`, and `pii_injected_hard_v1.json`, produced by `fix_pii_injected_v1.py`, `fix_pii_realistic_v1.py`, and `fix_pii_injected_hard_v1.py` respectively. Each script writes a `.fixed.json` output alongside the original (originals are untouched).

Full per-file rationale and category breakdowns are in the companion docs:
- [pii-injected-v1-uncommon-spans.md](pii-injected-v1-uncommon-spans.md)
- [pii-realistic-v1-uncommon-spans.md](pii-realistic-v1-uncommon-spans.md)
- [pii-injected-hard-v1-uncommon-spans.md](pii-injected-hard-v1-uncommon-spans.md)

For how the four entity-level PII models actually score against these refined
datasets (with and without the regex supplement), see:
- [pii-results-refined-with-regex.md](pii-results-refined-with-regex.md)
- [pii-results-refined-no-regex.md](pii-results-refined-no-regex.md)

## What changed vs. what didn't

**Formats/structure were never changed.** Separators, punctuation, grouping, defanging notation (`[.]`, spaces, `dot`/`at` word-substitution), and overall string length were preserved exactly as in the original in every case.

**Only underlying values were resampled, and only for specific rule violations:**

| Category | What was fixed |
|---|---|
| Credit cards | Digits rewritten so the number starts with a real network BIN (Visa `4`, Mastercard `51`–`55`, Amex `34`/`37`, Discover `6011`/`65`) and passes the Luhn checksum. |
| Phone numbers | The specific leading digit of an area code or exchange group changed from `0`/`1` to `2`–`9` (NANP compliance) — regardless of separator style (dash, dot, `+1 (XXX)`, or dashless). |
| IP addresses | First octet changed to move it out of a reserved/unroutable range (`10`, `127`, `224`–`255`). |
| Duplicate names | Each repeated NAME value (beyond its first occurrence) resampled to a unique name not used elsewhere in the file. |

**Deliberately left untouched:**
- SSN formatting variety (dash/space/dot/dashless variants) — underlying digit ranges were already valid.
- Defanged email/IP notation itself (`sven.larsson[at]example.com`, `230[.]61[.]201[.]79`) — intentional adversarial hard-case coverage, not a generation flaw. (Note: two defanged IPs also happened to sit in a reserved octet range — that reserved-range violation *was* fixed, independently of the defanging style, which was kept.)
- Address templates and reserved/placeholder email domains (`example.com`, `mail.test`, `corp.example`) — accepted tradeoffs, documented in the per-file docs.

## Entity-change counts per file

Compared against the original file, using `text[start:end]` per entity before vs. after:

| File | Entities changed | Total entities | Breakdown by type |
|---|---|---|---|
| `pii_injected_v1.json` | 46 | 237 | CREDIT_CARD 30, PHONE 12, NAME 3, IP_ADDRESS 1 |
| `pii_realistic_v1.json` | 29 | 173 | NAME 12, PHONE 8, CREDIT_CARD 8, IP_ADDRESS 1 |
| `pii_injected_hard_v1.json` | 24 | 101 | PHONE 10, CREDIT_CARD 7, IP_ADDRESS 4, NAME 3 |

All other entity types (EMAIL, USERNAME, ADDRESS, SSN) were 0 changes across all three files.
