# Uncommon PII Spans in `pii_injected_hard_v1.json`

Review of all 130 items (101 expected PII entities: 68 `hard_positive`, 62 `hard_negative`) in `pii_injected_hard_v1.json`. This file's `metadata.obfuscated: true` / `metadata.no_cue: true` flags mark it as an intentionally adversarial "hard" fixture — obfuscated formatting (defanged emails/IPs, unusual separators) is expected by design here, not a flaw. The findings below separate that intentional obfuscation from actual generation-artifact issues that also show up in the easier `pii_injected_v1.json` / `pii_realistic_v1.json` fixtures.

## 1. Phone numbers with impossible NANP codes

9 of 21 unique phone numbers have an area code or exchange (first digit of the 3-digit group) starting with 0 or 1, which NANP prohibits:

- `+1 070 557 6071`, `+1 132 347 2769`, `+1 156 940 6012` — area code starts 0/1
- `018.048.4784` — both area (`018`) and exchange (`048`) invalid
- `051.640.9057`, `1172582948`, `179.278.7941`, `188.603.0011` — area code invalid
- `176.125.2733` — area *and* exchange invalid
- `482.156.4276` — exchange invalid

## 2. Credit card numbers with no valid network prefix (and mostly failing Luhn)

All 7 unique credit card numbers start with a digit no real card network uses (`2421...`, `6309...`, `7486...`, `7738...`, `8777...`, `8998...`, or `5342...` which is close to Mastercard but not `51`–`55`... actually `5342` *is* a valid Mastercard prefix range, yet still fails Luhn):

- `2421.9361.6633.7437`, `6309899273947035`, `8777215926793126`, `8998 3424 9920 3168` — bad prefix, fail Luhn
- `7486171758202185`, `7738.3277.4188.7823` — bad prefix (start with 7), but happen to pass Luhn by chance
- `5342 3692 1644 3156` — valid Mastercard-range prefix, but fails Luhn

So 0 of 7 are both correctly-prefixed *and* Luhn-valid — none of these would pass a real-world card validator.

## 3. IP addresses in reserved/unroutable blocks

4 of 10 unique IPs have a first octet in a reserved/unroutable block (`10`, `127`, or `224`–`255`) — more than the 2 caught in an initial manual pass, since the `224`–`239` multicast sub-range is easy to miss by eye:

- `127 . 34 . 27 . 130` — `127.0.0.0/8` is the loopback range; never a real external host.
- `251 . 124 . 140 . 69` — `240.0.0.0/4` is reserved for future use; never seen in real traffic.
- `230[.]61[.]201[.]79` — `224.0.0.0/4` is the multicast range; not a real unicast host address.
- `231 . 114 . 34 . 249` — also in the `224.0.0.0/4` multicast range.

## 4. Repeated identical names across unrelated records

`Sven Gonzalez`, `Lena Larsson`, and `Maria Rossi` each appear twice across otherwise-unrelated records (19 total NAME entities, only 16 unique) — the same templated-generation fingerprint seen in the other two files.

## 5. SSNs: formatting is inconsistent but numeric ranges are fine

15 unique SSNs use four different separator styles (dashless `132986777`, dot `357.79.6506`, space `151 34 2461`) — inconsistent, but not individually invalid. Checked all against the actual invalid SSN ranges (area `000`/`666`/`900`–`999`, group `00`, serial `0000`): **none** hit an invalid range. So despite odd formatting, the underlying numbers are plausible SSNs — no fix needed here beyond what's already noted as a formatting-diversity/obfuscation choice.

## 6. Deliberately obfuscated ("defanged") emails and IPs — intentional, not a flaw

Consistent with `metadata.obfuscated: true`, several entities use real-world evasion notations:
- Emails: `diego.morgan @ corp.example`, `sven.larsson[at]example.com`, `theo.novak[at]acme.io`, `lena dot morgan at acme dot io`, `diego.larsson(at)acme dot io`, `diego dot novak at acme dot io` (6 distinct forms, 16 occurrences total)
- IPs: bracket-defanged (`12[.]129[.]185[.]155`, `41[.]181[.]122[.]26`, `211[.]186[.]243[.]5`, `29[.]224[.]108[.]232`) and space-padded (`182 . 11 . 145 . 137`, `213 . 152 . 114 . 41`, etc.) — the defanging notation itself is the intentional part; two of the space-padded and bracket-defanged examples (`251 . 124 . 140 . 69`, `230[.]61[.]201[.]79`) also happen to sit in a reserved octet range, which is the separate, unintentional issue covered in section 3 above.

This matches the same pattern flagged in `pii_realistic_v1.json` — a genuine real-world PII-filter-evasion technique, correctly included here as a hard-positive/no-cue test case. Not something to "fix."

## 7. No ADDRESS entities at all

Unlike the other two files, this fixture has zero `ADDRESS`-type entities (0 of 101). Not a correctness issue, just worth noting if full entity-type coverage is expected of "hard" cases too.

## Verdict

**No** — a meaningful fraction of the PII in this file is not realistic by construction:
- Phone numbers: **9/21 (43%)** violate NANP structure.
- Credit cards: **7/7 (100%)** fail to be both correctly-prefixed and Luhn-valid.
- IP addresses: **4/10 (40%)** fall in reserved/unroutable blocks.
- Names: **3/16 unique values (19%)** are reused across unrelated records.

SSNs are fine despite inconsistent formatting, and the defanged emails/IPs are intentional adversarial test cases rather than defects — those two categories should be left alone. The phone/card/IP/name issues are the same class of synthetic-generation artifacts already fixed in the other two files' `.fixed.json` outputs; the same fix approach (offset-safe in-place regeneration) would apply here too if desired.

## Fixes applied

[fix_pii_injected_hard_v1.py](fix_pii_injected_hard_v1.py) regenerates the flagged spans and writes the result to `pii_injected_hard_v1.fixed.json`, staged alongside the original for review rather than overwriting it. Run with `python3 fix_pii_injected_hard_v1.py` (seeded, so output is reproducible/diffable). Reuses the same offset-safe splice-and-shift approach as the other two files' fix scripts.

**What was changed:**

| Category | Fix |
|---|---|
| 1. Phone numbers | Leading `0`/`1` digit in any 3-digit area/exchange group redrawn to `2`–`9`, regardless of separator style (dash, dot, `+1 (XXX)`, or fully dashless 10-digit strings, which get area/exchange positions 0 and 3 checked explicitly). |
| 2. Credit cards | Prefix rewritten to a real BIN (Visa `4`, Mastercard `51`–`55`, Amex `34`/`37`, Discover `6011`/`65`) matching digit count, middle digits redrawn, final digit recomputed via Luhn. Separator style and length preserved. |
| 3. Reserved IPs (`127.x`, `251.x`, `230.x`, `231.x`) | First octet resampled away from `10`, `127`, and `224`–`255`, preserving whatever separator/defanging style (plain, space-padded, or bracket-defanged) surrounds it. |
| 4. Duplicate names | Each repeat beyond the first occurrence (`Sven Gonzalez`, `Lena Larsson`, `Maria Rossi`) resampled to a unique `first last` combination not used elsewhere in the file. |
| SSN formatting | **Not changed** — space/dot/dashless variants preserved as intentional obfuscation coverage; underlying digit ranges were already valid. |
| Defanged emails/IPs | **Not changed** — kept as intentional adversarial hard-positive cases per `metadata.obfuscated: true`. |

**Verification performed on `pii_injected_hard_v1.fixed.json`:**
- `text[start:end] == entity_text` holds for every entity in every item (0 offset mismatches).
- No `PHONE` entity has an area/exchange code starting with `0` or `1`.
- Every `CREDIT_CARD` entity is both correctly-prefixed and Luhn-valid.
- No `NAME` value appears more than once across the dataset.
- No `IP_ADDRESS` entity has a first octet in `10`, `127`, or `224`–`255`.
- SSN formats: still all 3 original variants (space/dot/dashless), unchanged.
- Defanged email count: still exactly 16 occurrences, unchanged.
