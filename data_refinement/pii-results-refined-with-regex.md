# PII Detection Results on Refined Datasets (With Regex Supplement)

This evaluates the same four entity-level models used in
[pii-results-comparison.md](../pii-results-comparison.md) —
`openai/privacy-filter`, `OpenMed/privacy-filter-nemotron`,
`OpenMed-PII-SuperClinical-Small (44M)`, `OpenMed-PII-SuperClinical-Large (434M)` —
against the **refined** datasets in `data_refinement/*.fixed.json` instead of the
original `pii_*.json` files. The refined datasets fix the unrealistic PII values
documented in `data_refinement/pii-*-uncommon-spans.md` (invalid-NANP phone
numbers, non-Luhn/bad-prefix credit cards, reserved-block IP addresses, and
duplicate names) while leaving formatting, SSN separator variety, defanged
emails/IPs, and address templates untouched — see
[pii-fix-summary.md](pii-fix-summary.md) for
exactly what changed.

Regex supplementing (`regex_pii.py`, `USE_REGEX_SPANS=True` for all four configs)
is active here, same as the main comparison doc. Produced by `eval_refined.py`,
which reruns each of the four models against the three refined datasets (a
fresh classifier pass, since the input text differs from the original files)
and writes `results/summary_refined_with_regex.json`.

## Side-by-side metrics

| Dataset | Source | Precision | Recall | F1 |
|---|---|---|---|---|
| pii-injected-v1 (refined) | openai/privacy-filter | 90.98% | 97.89% | 0.9431 |
| pii-injected-v1 (refined) | OpenMed/privacy-filter-nemotron | 96.31% | 99.16% | 0.9771 |
| pii-injected-v1 (refined) | OpenMed-PII-SuperClinical-Small (44M) | 94.31% | 97.89% | 0.9607 |
| pii-injected-v1 (refined) | OpenMed-PII-SuperClinical-Large (434M) | 96.71% | 99.16% | 0.9792 |
| pii-injected-hard-v1 (refined) | openai/privacy-filter | 69.01% | 97.03% | 0.8066 |
| pii-injected-hard-v1 (refined) | OpenMed/privacy-filter-nemotron | 78.38% | 86.14% | 0.8208 |
| pii-injected-hard-v1 (refined) | OpenMed-PII-SuperClinical-Small (44M) | 76.99% | 86.14% | 0.8131 |
| pii-injected-hard-v1 (refined) | OpenMed-PII-SuperClinical-Large (434M) | 82.64% | 99.01% | 0.9009 |
| pii-realistic-v1 (refined) | openai/privacy-filter | 86.36% | 98.84% | 0.9218 |
| pii-realistic-v1 (refined) | OpenMed/privacy-filter-nemotron | 85.71% | 97.11% | 0.9106 |
| pii-realistic-v1 (refined) | OpenMed-PII-SuperClinical-Small (44M) | 83.82% | 98.84% | 0.9072 |
| pii-realistic-v1 (refined) | OpenMed-PII-SuperClinical-Large (434M) | 93.51% | 100.0% | 0.9665 |

## Raw counts

| Dataset | Source | TP | FP | FN | Items |
|---|---|---|---|---|---|
| pii-injected-v1 (refined) | openai/privacy-filter | 232 | 23 | 5 | 130 |
| pii-injected-v1 (refined) | OpenMed/privacy-filter-nemotron | 235 | 9 | 2 | 130 |
| pii-injected-v1 (refined) | OpenMed-PII-SuperClinical-Small | 232 | 14 | 5 | 130 |
| pii-injected-v1 (refined) | OpenMed-PII-SuperClinical-Large | 235 | 8 | 2 | 130 |
| pii-injected-hard-v1 (refined) | openai/privacy-filter | 98 | 44 | 3 | 130 |
| pii-injected-hard-v1 (refined) | OpenMed/privacy-filter-nemotron | 87 | 24 | 14 | 130 |
| pii-injected-hard-v1 (refined) | OpenMed-PII-SuperClinical-Small | 87 | 26 | 14 | 130 |
| pii-injected-hard-v1 (refined) | OpenMed-PII-SuperClinical-Large | 100 | 21 | 1 | 130 |
| pii-realistic-v1 (refined) | openai/privacy-filter | 171 | 27 | 2 | 130 |
| pii-realistic-v1 (refined) | OpenMed/privacy-filter-nemotron | 168 | 28 | 5 | 130 |
| pii-realistic-v1 (refined) | OpenMed-PII-SuperClinical-Small | 171 | 33 | 2 | 130 |
| pii-realistic-v1 (refined) | OpenMed-PII-SuperClinical-Large | 173 | 12 | 0 | 130 |

## Comparison against the original (unrefined) datasets

Comparing `(tp, fp, fn)` per model/dataset against `results/summary.json`
(the original, unrefined-data run behind `pii-results-comparison.md`):

| Config | Dataset | Original (tp, fp, fn) | Refined (tp, fp, fn) | Same? |
|---|---|---|---|---|
| privacy_filter | pii-injected-v1 | (232, 23, 5) | (232, 23, 5) | same |
| privacy_filter | pii-injected-hard-v1 | (98, 44, 3) | (98, 44, 3) | same |
| privacy_filter | pii-realistic-v1 | (171, 29, 2) | (171, 27, 2) | **diff** |
| privacy_filter_nemotron | pii-injected-v1 | (235, 9, 2) | (235, 9, 2) | same |
| privacy_filter_nemotron | pii-injected-hard-v1 | (88, 26, 13) | (87, 24, 14) | **diff** |
| privacy_filter_nemotron | pii-realistic-v1 | (168, 26, 5) | (168, 28, 5) | **diff** |
| pii_superclinical_small | pii-injected-v1 | (233, 13, 4) | (232, 14, 5) | **diff** |
| pii_superclinical_small | pii-injected-hard-v1 | (85, 29, 16) | (87, 26, 14) | **diff** |
| pii_superclinical_small | pii-realistic-v1 | (171, 33, 2) | (171, 33, 2) | same |
| pii_superclinical_large | pii-injected-v1 | (235, 8, 2) | (235, 8, 2) | same |
| pii_superclinical_large | pii-injected-hard-v1 | (101, 20, 0) | (100, 21, 1) | **diff** |
| pii_superclinical_large | pii-realistic-v1 | (173, 13, 0) | (173, 12, 0) | **diff** |

7 of 12 model/dataset combinations shift by 1-3 counts. All shifts are small
(≤3 entities) and go in both directions (some FN counts rise, some fall) —
this is **not** the regex layer behaving differently (it's shape-based and
matches the same character spans regardless of digit validity, as established
earlier in this session), it's each model's *own* token-classification output
shifting slightly because the actual digit content at a given span changed
(e.g. a resampled credit card number or a phone number with one digit moved
off `0`/`1`). A model's internal NER decision (span boundaries, confidence
score crossing `SCORE_THRESHOLD`, or whether it labels a span at all) can be
sensitive to the specific digits present, independent of format. `-nemotron`
and `-small` show the most movement (both directions on `hard-v1`); the two
`SuperClinical` configs and `privacy_filter` are otherwise stable on
`pii-injected-v1`, the dataset with the most changed entities (46 of 237).

This means the refined dataset is not perfectly metric-equivalent to the
original — expect low-single-digit-count noise per model/dataset when
switching to it — but the shifts are too small and bidirectional to represent
a systematic quality change. The refinement's purpose isn't to move these
scores; it's to remove PII spans that a real-world validator would reject
outright (see `data_refinement/pii-fix-summary.md`), which is orthogonal to
how well a given model happens to tag them.

## Observations

- **SuperClinical-Large** remains the strongest performer across all three
  refined datasets (0.9792 / 0.9009 / 0.9665 F1), consistent with the original
  comparison.
- **pii-injected-hard-v1** is still the hardest dataset for every model, since
  its remaining difficulty (obfuscated `[at]`/`dot`-spelled emails, bracket
  and space-defanged IPs) is untouched by this refinement — those are
  intentional adversarial cases, not generation artifacts, and correctly
  weren't "fixed."
- The refinement's main value isn't a metrics shift here — it's that the
  fixture no longer contains PII spans that a real-world validator (Luhn,
  NANP, IP-reservation check) would reject outright, which matters for anyone
  citing this dataset as "realistic" PII coverage independent of model
  scoring.

## Deep dive: SuperClinical-Large FN/FP on pii-injected-v1 (refined)

`OpenMed-PII-SuperClinical-Large (434M)` scores tp=235, fp=8, fn=2 here — the
exact same counts as on the original unrefined `pii_injected_v1.json` (see the
comparison table above), so nothing about the refinement introduced or
removed a miss/extra for this specific model/dataset pair. Full detail below,
produced by `analyze_refined.py pii_superclinical_large data_refinement/pii_injected_v1.fixed.json`.

**2 false negatives — both PHONE, both `(XXX) XXX-XXXX` format:**

- `(738) 498-9092` — `...4 470 1773. My number is (738) 498-9092. Ship to 6559 Oak Rd, Sp...`
- `+1 419 789 8906` — `...a a a a a a a Call me on +1 419 789 8906. The card is 6540-1640-0...`

Neither is a regex gap in the strict sense — `regex_pii.py`'s `PHONE_DOTTED_RE`
and `PHONE_BARE_RE` only cover dotted 3-3-4 and fully bare 10-digit phone
formats (established earlier in this session); `(XXX) XXX-XXXX` and
`+1 XXX XXX XXXX` aren't in scope for the regex layer at all, so these two
misses are purely the model's own native NER failing to tag a
parenthesized/spaced phone number it apparently handles inconsistently
elsewhere in the same dataset (it does catch other `(XXX) XXX XXXX`-style
numbers correctly, e.g. the with-regex tp=235 includes several). This is a
model-behavior gap, not something the data refinement caused or could fix.

**8 false positives — all `first_name`/`last_name` mislabeling of non-name text:**

- `first_name`: `'Workato RAG'`, `'Squeamish Ossifrage'`, `'Atlassian'`, `' Workato'`
- `last_name`: `'sian'` (×3, a sub-token fragment of "Atlassian"), `'Atlassian'`

All 8 cluster around the same root cause: the model treats capitalized
non-name tokens — product/brand names (`Workato`, `Atlassian`, `RAG`) and a
quoted test phrase (`"Squeamish Ossifrage"`, a well-known cryptographic
canary string) — as person names, including one case where it double-counts
"Atlassian" as both a `first_name` and a `last_name`-tagged fragment (`sian`)
in the same span. None of these are anywhere near a PHONE/CREDIT_CARD/SSN/IP
context, so this isn't a regex interaction either — it's the model's person-
name detector over-firing on capitalized proper nouns generally, independent
of the PII-refinement work in this dataset.

## Deep dive: SuperClinical-Large FN/FP on pii-realistic-v1 (refined)

Same model, `pii-realistic-v1 (refined)`: tp=173, fp=12, fn=0 — one fewer FP
than the original unrefined dataset (13→12), otherwise identical.

**0 false negatives** — perfect recall, same as on the original data.

**12 false positives**, same two root causes as `pii-injected-v1` above, plus
a defanged-email variant:

| Type | Count | Examples |
|---|---|---|
| `user_name` | 4 | `'\nsara'`, `' omar dot novak'`, `' alex dot larsson'`, `' diego dot tanaka'` |
| `first_name` | 3 | `'Workato RAG'`, `'Squeamish Ossifrage'`, `'Atlassian'` |
| `last_name` | 3 | `'ato'`, `'sian'`, `' no'` |
| `ipv4` | 1 | `' 598.271.9803'` |
| `email` | 1 | `' acme dot io'` |

1. **Person-name over-firing on capitalized non-names** — same
   `Workato`/`Atlassian`/`Squeamish Ossifrage` pattern as `pii-injected-v1`.
2. **Defanged-email misparsing**: for spelled-out obfuscated emails like
   `"omar dot novak at acme dot io"`, the model splits the string into
   separate `user_name`/`email`-fragment predictions (`' omar dot novak'`,
   `' acme dot io'`) instead of recognizing one EMAIL span, so each fragment
   mismatches the single expected entity. This is a model limitation on the
   intentionally-obfuscated hard cases discussed earlier — not something the
   refinement touched or could fix.

**The one FP that disappeared vs. the original data**: `143.140.2915` was
mistagged `ipv4` in the original dataset — a dot-separated PHONE number
(`143.140.2915`) that happens to look IP-shaped. The fix script changed this
exact span to `643.740.2915` (correcting its NANP-invalid leading `1`→`6`).
After that change the model no longer tags it `ipv4`, plausibly because `643`
exceeds the valid IP-octet range (max 255) the way `143` didn't, making the
string look less IP-like. This is a side effect worth noting, not the fix's
goal — one data point, not a systematic pattern to generalize from.

## Deep dive: SuperClinical-Large FN/FP on pii-injected-hard-v1 (refined)

Same model, `pii-injected-hard-v1 (refined)`: tp=100, fp=21, fn=1 — the one
case among the three datasets where the refinement measurably shifted this
model's error profile versus the original (unrefined) tp=101, fp=20, fn=0.

**1 false negative (NAME) — a side effect of an adjacent entity's fix:**

- `Maria Gonzalez` — `...Let me know if further assistance is needed! Maria Gonzalez. (110 . 114 . 34 . 249)...`

`Maria Gonzalez` itself wasn't touched by the fix script. The IP address two
tokens later (`231 . 114 . 34 . 249` → `110 . 114 . 34 . 249`, correcting the
reserved-multicast-range octet) was. The model caught this name correctly in
the original data; after only the nearby IP's digits changed, it misses the
name. This is a narrow but real example of a digit-value fix perturbing the
model's context/attention enough to flip an unrelated adjacent prediction —
not something the fix script could reasonably anticipate or avoid, since it
operates purely on the target span's own validity, not on knock-on effects to
neighboring entities.

**21 false positives** — the same `Workato`/`Atlassian`/canary-phrase
name-over-firing pattern as the other two datasets, plus `ipv4` mistags of
dot-separated phone numbers (a `\d{3}.\d{3}.\d{4}`-shaped string reads as
IP-ish to the model). Diffing the FP list against the original line-by-line:

| Change | Item | Before → After |
|---|---|---|
| New FP | 14 | phone `018.048.4784`→`518.548.4784` (NANP fix); not mistagged `ipv4` before, is now |
| New FP | 16 | phone `051.640.9057`→`251.640.9057`; now partially mistagged as `ipv4` (`'251'`) |
| FP removed | 126 | phone `188.603.0011`→`788.603.0011`; was mistagged `ipv4` before, isn't now |
| Unchanged | 47, 125 | same phones, digits changed by the fix, still mistagged `ipv4` either way |

Net: +2 new, −1 removed = +1 FP overall (20→21), matching the observed count.
Despite these mistags, PHONE recall didn't drop: `regex_pii.py`'s
`PHONE_DOTTED_RE` independently catches the correct PHONE span regardless of
what wrong label the model itself guesses, so each of these is a purely
spurious extra FP layered on top of an already-correct TP, not a lost
detection. This is coincidental noise from the model's own IP-vs-phone
heuristic reacting to specific digit values, not a systematic effect of the
refinement — three digits changed, three FPs shuffled, net effect +1.
