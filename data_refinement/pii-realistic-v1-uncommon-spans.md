# Uncommon PII Spans in `pii_realistic_v1.json`

Review of all 130 items (173 expected PII entities: 77 `realistic_positive`, 53 `hard_negative`) in `pii_realistic_v1.json`, flagging spans that follow synthetic-generation or obfuscation patterns rather than plain real-world PII conventions.

## 1. Phone numbers with impossible NANP codes

Same issue as `pii_injected_v1.json`: a US phone number's area code or exchange (each 3-digit group) can't start with 0 or 1, but 6 of 19 unique numbers do:

- `+1 (067) 899-5122`, `+1 (378) 013-2400`, `+1 (459) 104-5298`, `+1 (591) 164-6300`, `+1 (633) 013-9258` — area code or exchange starts with 0 or 1
- `011.220.4539`, `143.140.2915`, `688.053.5697` — dot-separated numbers with a leading-0/1 group

## 2. Credit card numbers failing Luhn / lacking a valid network prefix

All 8 unique credit card numbers fail the Luhn checksum — none are algorithmically valid card numbers:

- `1815 5045 7244 4558`, `1844419180131938`, `2582 1336 7434 7486`, `8406 3424 5249 4041`, `8658 8202 3341 2113`, `9558 8914 9541 2732` — also start with a digit no card network uses (`1`, `2` outside Mastercard's `2221`–`2720` range, `8`, `9`)
- `4410 2862 8916 5355`, `5136342438056753` — have a real network prefix (Visa `4`, Mastercard `51`–`55`) but still fail Luhn

## 3. IP address in a reserved/unroutable block

`225.161.4.57` falls in `224.0.0.0/4`, the multicast/reserved range — not a real host address.

## 4. SSNs formatted with spaces instead of dashes

`645 70 2836` and `853 66 2898` use space separators where every other SSN in the file (and in real-world usage) uses dashes (`AAA-GG-SSSS`). Not invalid on its own, but an inconsistent/uncommon formatting choice mixed into an otherwise dash-formatted set.

## 5. Deliberately obfuscated ("defanged") emails and IPs

19 of 43 emails are written in defanged word form — `"priya dot khan at corp dot example"` instead of `priya.khan@corp.example` — and 3 of 13 IP addresses use bracket-defanging — `136[.]41[.]26[.]35` instead of `136.41.26.35`. This is a real, common technique (security analysts defang IOCs in reports to stop them auto-linking/executing, and spammers/scrapers-evaders use word-substitution to dodge regex filters), so it's realistic as an *adversarial* pattern — but it means a naive regex-based PII filter would miss these entirely unless it explicitly normalizes defanged text first. Worth confirming this is intentional "hard case" coverage rather than an accidental formatting artifact.

## 6. Repeated identical names across unrelated records

10 names recur 2–3 times each across otherwise-unrelated records (`Nina Rossi` ×3, `Lena Khan` ×3, `Diego Rossi` ×2, `Sven Silva` ×2, `Alex Tanaka` ×2, `Theo Patel` ×2, `Theo Gonzalez` ×2, `Omar Khan` ×2, `Nina Patel` ×2, `Sara Rossi` ×2) — 62 total NAME entities but only 50 unique values. Same templated-generation fingerprint noted in `pii_injected_v1.json`.

## 7. Fictional address reused from *The Simpsons*

Two addresses use `Evergreen Terrace` — `1970 Evergreen Terrace, Portland OR 97201` and `3028 Evergreen Terrace, Austin TX 78701` — which is Homer Simpson's iconic address (742 Evergreen Terrace) with the house number changed. Combined with the reused `Springfield, IL` city already seen in `pii_injected_v1.json`, this confirms the same synthetic template/generator (or a shared pop-culture joke) underlies both files. Addresses themselves are otherwise unique strings (no literal duplicates), same as the other file.

## Why this matters

Most of these (1–4, 6, 7) are the same class of synthetic-generation artifacts already documented for `pii_injected_v1.json` — expected for a fixture built from fake data, but worth flagging if cited as "realistic" coverage for validators doing real-world checks (Luhn, NANP, reserved IP ranges).

Category 5 (defanging) is different: it's a genuine, common real-world obfuscation pattern, not a generation artifact. It's a legitimate hard-negative/hard-positive test case, but the doc calls it out because it directly stresses the PII filter's ability to normalize obfuscated text — a design consideration worth confirming with whoever built this fixture, not something to "fix" by de-obfuscating it.

## Fixes applied

[fix_pii_realistic_v1.py](fix_pii_realistic_v1.py) regenerates the flagged spans and writes the result to `pii_realistic_v1.fixed.json`, staged alongside the original for review rather than overwriting it. Run with `python3 fix_pii_realistic_v1.py` (seeded, so output is reproducible/diffable). It reuses the same offset-safe splice-and-shift approach validated on `pii_injected_v1.json` (see [pii-injected-v1-uncommon-spans.md](pii-injected-v1-uncommon-spans.md)).

**What was changed:**

| Category | Fix |
|---|---|
| 1. Phone numbers | Leading `0`/`1` digit in any 3-digit area/exchange group (regardless of separator style — dash, dot, or `+1 (XXX)`) redrawn to `2`–`9`. Length/formatting unchanged. |
| 2. Credit cards | Prefix rewritten to a real BIN (Visa `4`, Mastercard `51`–`55`, Amex `34`/`37`, Discover `6011`/`65`) matching the existing digit count, middle digits redrawn, final digit recomputed via Luhn. Separator style and length preserved. |
| 3. Reserved IP (`225.161.4.57`) | First octet resampled away from reserved/unroutable ranges. |
| 6. Duplicate names | Each repeat beyond the first occurrence resampled to a unique `first last` combination not used elsewhere in the file. |
| 4. SSN space formatting | **Not changed** — the 2 of 7 SSNs using space separators (`645 70 2836`, `853 66 2898`) are kept as-is, per explicit instruction. |
| 5. Defanged emails/IPs | **Not changed** — kept as intentional obfuscation hard cases (see section 5 above). |
| 7. Evergreen Terrace / address reuse | **Not changed** — addresses are already literally unique strings; nothing to dedupe. |

**Verification performed on `pii_realistic_v1.fixed.json`:**
- `text[start:end] == entity_text` holds for every entity in every item (0 offset mismatches).
- No `PHONE` entity has an area/exchange code starting with `0` or `1`.
- Every `CREDIT_CARD` entity passes the Luhn checksum.
- No `NAME` value appears more than once across the dataset.
- `225.161.4.57` no longer appears; no other `IP_ADDRESS` value falls in a reserved block.
- SSN space-formatted entries: still exactly 2 (unchanged).
- Defanged email count: still exactly 20 occurrences (unchanged).
