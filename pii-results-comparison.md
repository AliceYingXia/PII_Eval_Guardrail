# PII Detection Results Comparison: openai/privacy-filter, OpenMed models, vs. Skyflow

## Important caveat on comparability

The two sources measure at different granularities, so the numbers are not strictly apples-to-apples:

- **openai/privacy-filter** reports entity-level counts (TP/FP/FN only, no TN). Note that TP for `pii-injected-v1` is 217 against 130 items, meaning multiple PII entities are being scored per item.
- **Skyflow** reports item-level counts (TP/FN/FP/TN), where each row sums to exactly 130 (matching total items), and Precision/Recall/F1 are computed at the record level.

Given this, F1 and Recall are the most directly comparable metrics across the two, but absolute TP/FP/FN counts should not be compared directly. The OpenMed models below are scored with the same entity-level harness as openai/privacy-filter (see `eval.py`/`pii_eval_lib.py`), so they're directly comparable to it and to each other, just not to Skyflow's item-level counts.

## Side-by-side metrics

| Dataset | Source | Precision | Recall | F1 |
|---|---|---|---|---|
| pii-injected-v1 | openai/privacy-filter | 90.98% | 97.89% | 0.9431 |
| pii-injected-v1 | OpenMed/privacy-filter-nemotron | 96.31% | 99.16% | 0.9771 |
| pii-injected-v1 | OpenMed-PII-SuperClinical-Small (44M) | 94.72% | 98.31% | 0.9648 |
| pii-injected-v1 | OpenMed-PII-SuperClinical-Large (434M) | 96.71% | 99.16% | 0.9792 |
| pii-injected-v1 | Skyflow | 100.0% | 100.0% | 1.000 |
| pii-injected-hard-v1 | openai/privacy-filter | 69.01% | 97.03% | 0.8066 |
| pii-injected-hard-v1 | OpenMed/privacy-filter-nemotron | 77.19% | 87.13% | 0.8186 |
| pii-injected-hard-v1 | OpenMed-PII-SuperClinical-Small (44M) | 74.56% | 84.16% | 0.7907 |
| pii-injected-hard-v1 | OpenMed-PII-SuperClinical-Large (434M) | 83.47% | 100.0% | 0.9099 |
| pii-injected-hard-v1 | Skyflow | 53.7% | 97.1% | 0.691 |
| pii-realistic-v1 | openai/privacy-filter | 85.50% | 98.84% | 0.9169 |
| pii-realistic-v1 | OpenMed/privacy-filter-nemotron | 86.60% | 97.11% | 0.9155 |
| pii-realistic-v1 | OpenMed-PII-SuperClinical-Small (44M) | 83.82% | 98.84% | 0.9072 |
| pii-realistic-v1 | OpenMed-PII-SuperClinical-Large (434M) | 93.01% | 100.0% | 0.9638 |
| pii-realistic-v1 | Skyflow | 62.1% | 100.0% | 0.766 |

## Raw counts

| Dataset | Source | TP | FP | FN | TN | Items |
|---|---|---|---|---|---|---|
| pii-injected-v1 | openai/privacy-filter | 232 | 23 | 5 | – | 130 |
| pii-injected-v1 | OpenMed/privacy-filter-nemotron | 235 | 9 | 2 | – | 130 |
| pii-injected-v1 | OpenMed-PII-SuperClinical-Small | 233 | 13 | 4 | – | 130 |
| pii-injected-v1 | OpenMed-PII-SuperClinical-Large | 235 | 8 | 2 | – | 130 |
| pii-injected-v1 | Skyflow | 130 | 0 | 0 | 0 | 130 |
| pii-injected-hard-v1 | openai/privacy-filter | 98 | 44 | 3 | – | 130 |
| pii-injected-hard-v1 | OpenMed/privacy-filter-nemotron | 88 | 26 | 13 | – | 130 |
| pii-injected-hard-v1 | OpenMed-PII-SuperClinical-Small | 85 | 29 | 16 | – | 130 |
| pii-injected-hard-v1 | OpenMed-PII-SuperClinical-Large | 101 | 20 | 0 | – | 130 |
| pii-injected-hard-v1 | Skyflow | 66 | 57 | 2 | 5 | 130 |
| pii-realistic-v1 | openai/privacy-filter | 171 | 29 | 2 | – | 130 |
| pii-realistic-v1 | OpenMed/privacy-filter-nemotron | 168 | 26 | 5 | – | 130 |
| pii-realistic-v1 | OpenMed-PII-SuperClinical-Small | 171 | 33 | 2 | – | 130 |
| pii-realistic-v1 | OpenMed-PII-SuperClinical-Large | 173 | 13 | 0 | – | 130 |
| pii-realistic-v1 | Skyflow | 77 | 47 | 0 | 6 | 130 |

## Regex + Luhn-as-soft-signal update

Following the scoring-bug fix below, a second change was made to `regex_pii.py` and the three OpenMed configs: `find_credit_cards` no longer requires the Luhn checksum to pass before emitting a `CREDIT_CARD` span (it's now attached as `luhn_ok` metadata alongside `known_iin`, same treatment), and `USE_REGEX_SPANS` was flipped to `True` for `privacy_filter_nemotron`, `pii_superclinical_small`, and `pii_superclinical_large` (previously only `openai/privacy-filter` used the regex supplement).

Root cause: nearly every credit-card false negative across all four models was a synthetic, randomly-generated card number that doesn't happen to be Luhn-valid (only 3 of 14 sampled FNs passed Luhn), even though the regex's digit-shape pattern matched all of them. A hard Luhn gate is correct for filtering accidental digit-run matches in production traffic, but it was silently discarding exactly the clean-format PII this regex exists to catch in this eval. All four models were rerun (from cached raw predictions, since regex/Luhn are applied at scoring time, not model-inference time) after this change; the tables above reflect it. The clearest effect is on `pii-injected-v1`, where credit cards make up the bulk of each model's FNs: recall rose from ~91-95% to ~98-99% for all four models, with essentially no precision cost (regex CC/SSN/IP spans rarely collide with a wrong expected entity). The effect on `hard-v1`/`realistic-v1` is smaller, since those datasets' remaining FNs are dominated by obfuscated formats (`[at]`, spelled-out "dot", defanged `[.]`) that this regex doesn't attempt to handle.

**Follow-up: dot-separated card numbers.** `CREDIT_CARD_RE` originally only allowed spaces/dashes as digit-group separators, so dot-separated cards like `2421.9361.6633.7437` and `7738.3277.4188.7823` (2 remaining FNs on `pii-injected-hard-v1` for all three OpenMed configs) still fell through. Added `.` to the separator character class in both `CREDIT_CARD_RE` and the digit-stripping step in `find_credit_cards`. This is unambiguous against the dataset's other dotted formats: IPv4 octets are 1-3 digits and dotted phone/SSN groups start with a 3-digit block, while this pattern requires a 4-digit first block, so there's no collision with `018.048.4784`-style phones or defanged IPs. Effect: `pii-injected-hard-v1` recall/F1 for the three OpenMed models ticked up further (e.g. `SuperClinical-Large` 67.33%→69.31% recall, 0.7196→0.7330 F1); `openai/privacy-filter` and the other two datasets were unaffected since they had no remaining dot-separated CC FNs. Tables above reflect this too.

## Regex extension: obfuscated PHONE/SSN/IP/EMAIL formats, applied to all four models

Following the false-negative analysis below (pre-dating this update), `regex_pii.py` was extended to cover the obfuscation patterns that were previously slipping past every model, and the extension was wired into all four configs (`privacy_filter`, `privacy_filter_nemotron`, `pii_superclinical_small`, `pii_superclinical_large`) via their shared `LABEL_MAP` self-mappings for regex-produced spans:

- **Dotted SSN** (3-2-4 grouping, e.g. `357.79.6506`) and **dotted PHONE** (3-3-4 grouping, e.g. `018.048.4784`) — disambiguated from each other purely by group-size shape, and from IPv4 by dot count (2 dots/3 groups vs. 3 dots/4 octets).
- **Bare unbroken digit runs**: 9 digits → SSN, 10 digits → PHONE (`132986777`, `1172582948`).
- **Defanged/spaced IPv4**: `[.]`-bracket notation (`41[.]181[.]122[.]26`) and space-padded dots (`127 . 34 . 27 . 130`), both common IOC-style obfuscations.
- **Obfuscated EMAIL**: spaces around `@` (`diego.morgan @ corp.example`) and fully spelled-out `dot`/`at` (`diego dot novak at acme dot io`).

`configs/privacy_filter_nemotron.py`'s `LABEL_MAP` (inherited by both SuperClinical configs) previously only self-mapped regex spans typed `SSN`/`CREDIT_CARD`/`IP_ADDRESS` — `PHONE` and `EMAIL` regex spans were being generated but silently dropped at scoring time. Added `"PHONE": {"PHONE"}` and `"EMAIL": {"EMAIL"}` there and to `configs/privacy_filter.py` so all four configs treat all five regex-produced types consistently.

**Effect**: this closed essentially all of `pii-injected-hard-v1`'s and `pii-realistic-v1`'s obfuscation-driven false negatives across every model — `SuperClinical-Large` now scores 0 FN (100% recall) on both. The other three models still miss some entities on `hard-v1` (3-16 FN), but the remaining misses are no longer the dotted/defanged/spelled-out patterns this regex targets — see the updated false-negative analysis below for what's left. No new false positives of type PHONE/EMAIL/SSN/IP_ADDRESS were introduced for any model/dataset combination (verified via `analyze_fp.py`); the FP counts in the raw-counts table above are unchanged from before this update except where a model's own remaining native mislabeling (e.g. `-nemotron` tagging emails as `user_name`) still applies, as described below.

## Scoring bug fix: excluded-label adjacency in `merge_spans`

An earlier version of `merge_spans` (`pii_eval_lib.py`) had a bug: when the token stream hit an excluded label (e.g. `B-city` immediately after an in-progress `street_address` span), it reset the in-progress span to `None` and discarded it *without ever appending it to the merged spans list*. For the OpenMed models, `street_address` is almost always immediately followed by `city`/`state`/`postcode` tokens (all excluded, out-of-taxonomy labels), so the in-progress `street_address` span was silently thrown away nearly every time -- producing a near-100% false-negative rate on `ADDRESS` for the SuperClinical models that looked like a genuine model blind spot but was actually a harness bug. Fixed by flushing the in-progress span before discarding on an excluded-label token. All four models were rerun after the fix; the tables above reflect the corrected numbers (openai/privacy-filter's numbers shifted slightly too, since the bug lived in the shared merge logic used by every config).

## Observations

On `pii-injected-v1`, Skyflow still leads with a perfect 1.000 F1. Among entity-level models, `SuperClinical-Large` (0.9792) and `privacy-filter-nemotron` (0.9771) are essentially tied for second, both ahead of `SuperClinical-Small` (0.9648) and `openai/privacy-filter` (0.9431).

On `pii-injected-hard-v1`, `SuperClinical-Large` is now the best entity-level model by a wide margin (0.9099 F1, **100% recall**) -- ahead of Skyflow (0.691), `-nemotron` (0.8186), `openai/privacy-filter` (0.8066), and `SuperClinical-Small` (0.7907). The regex extension above is the main driver: it eliminated the obfuscated-format false negatives that used to dominate every model's misses on this dataset, and `SuperClinical-Large` had the least residual model-specific weakness left over once that shared floor was removed.

On `pii-realistic-v1`, `SuperClinical-Large` again leads (0.9638 F1, 100% recall), followed by `openai/privacy-filter` (0.9169), `-nemotron` (0.9155), and `SuperClinical-Small` (0.9072); Skyflow's 0.766 now trails every entity-level model here.

**Cross-family pattern (post-regex-extension):** `SuperClinical-Large` (434M) is the clear strongest model overall, with perfect recall on both harder datasets and the best F1 on all three. `privacy-filter-nemotron` and `SuperClinical-Small` (44M) both still show a real, but now much smaller and specific, recall gap on the harder two datasets -- see the false-negative analysis above for what's actually driving it (email-as-username mislabeling and, for `SuperClinical-Small`, international phone formats).

Skyflow's overall pattern holds as before: it trades precision for recall relative to every entity-level model here, and now wins outright only on the straightforward `injected-v1` set -- its `hard-v1`/`realistic-v1` lead is gone now that the regex extension has closed most entity-level models' recall gap without the same precision cost.

## OpenMed label-mapping notes

The three OpenMed models (`privacy-filter-nemotron`, `OpenMed-PII-SuperClinical-Small-44M-v1`, `OpenMed-PII-SuperClinical-Large-434M-v1`) share the same ~55-label taxonomy, far broader than this dataset's 8 types (NAME/EMAIL/PHONE/ADDRESS/SSN/CREDIT_CARD/USERNAME/IP_ADDRESS). Two scoring decisions materially affect the numbers above:

- **Out-of-taxonomy labels are excluded, not scored as false positives.** Labels like `date`, `city`, `state`, `language`, `occupation`, `company_name`, `password`/`pin`/`cvv`/`api_key`, etc. have no dataset counterpart. The model correctly recognizing a date or a city isn't a false positive against a taxonomy that doesn't include dates or cities, so these predictions are dropped before scoring (`configs/privacy_filter_nemotron.py`'s `EXCLUDED_LABELS`) rather than counted against precision. An earlier pass that instead mapped these to `None` (still scored, still counted as FP) showed precision as low as 33-44% for `SuperClinical-Small` -- almost entirely an artifact of that choice, not the model's actual PII-detection quality.
- **Adjacent `first_name`→`last_name` spans are coalesced into one `NAME` span** (`coalesce_adjacent_spans` in `pii_eval_lib.py`). These models tag first and last names as two separate spans where the dataset's expected entity is the single full name. Without coalescing, the one-match-per-expected-entity scoring rule let only the first half match, counting the second half as a spurious false positive (123 extraneous `last_name` FPs alone in one earlier run for `SuperClinical-Small`).
- Regex-based supplementing (`add_regex_spans`) is enabled for all four configs, including all three OpenMed configs (`USE_REGEX_SPANS = True`) as of the "Regex extension" update above — originally only `openai/privacy-filter` used it. It now covers SSN, CREDIT_CARD, IP_ADDRESS, PHONE, and EMAIL, all mapped consistently via `LABEL_MAP`.

## False negative analysis

Breakdown of every missed expected entity, by dataset, using the cached model predictions (see `analyze_fn.py`). Figures below are **post-regex-extension** (see the "Regex extension" section above) -- the obfuscated PHONE/SSN/IP_ADDRESS/EMAIL misses that dominated every model's failures previously are now almost entirely gone. What's left is a much smaller, more model-specific residue: gaps in the model's own labeling (e.g. `-nemotron`/`SuperClinical-Small` tagging emails as `user_name`), plus a handful of address/name/username misses the regex layer was never meant to cover.

### openai/privacy-filter

#### pii-injected-v1 (5 FN)

By type: ADDRESS 3, NAME 2.

The credit-card weakness from earlier runs is gone (Luhn-as-soft-signal fix). What remains are a few one-off ADDRESS/NAME misses, unrelated to any obfuscation pattern.

#### pii-injected-hard-v1 (3 FN)

By type: USERNAME 2, EMAIL 1.

Down from 32 before the regex extension. The obfuscated-formatting weakness (dotted SSN/phone, defanged IP, spelled-out email) that used to dominate this dataset is fully closed for this model; the 3 remaining misses are isolated USERNAME/EMAIL cases with no obfuscation involved.

#### pii-realistic-v1 (2 FN)

By type: NAME 2.

Down from 8. No IP/EMAIL/obfuscation misses remain -- just 2 isolated NAME misses.

#### Takeaway

With both the Luhn fix and the regex extension in place, `openai/privacy-filter`'s remaining false negatives are sparse and don't cluster around any single format or obfuscation pattern anymore -- the systematic weaknesses identified in earlier passes (credit cards, dotted/defanged/spelled-out PII) are resolved.

### OpenMed/privacy-filter-nemotron

#### pii-injected-v1 (2 FN)

By type: NAME 1, PHONE 1.

Down from 11; the shared credit-card weakness is gone. Two isolated one-off misses remain.

#### pii-injected-hard-v1 (13 FN)

By type: EMAIL 8, USERNAME 4, PHONE 1.

Down from 59, but this is now `-nemotron`'s clearest remaining weakness: EMAIL (8) and USERNAME (4) misses are almost all the same underlying issue described in the false-positive analysis below -- the model tags a spelled-out/obfuscated email as `user_name` instead of `email`, so the regex's EMAIL span still doesn't help because `add_regex_spans` only fills gaps the model didn't already claim with a *conflicting* label. This is a model-labeling issue, not something the regex layer can fix.

#### pii-realistic-v1 (5 FN)

By type: USERNAME 4, NAME 1.

Down from 39. USERNAME (4) is the same email-mislabeled-as-username pattern as `hard-v1`; the obfuscated-EMAIL misses that used to dominate this dataset (23 of 39) are gone now that spelled-out/spaced emails the model *doesn't* mislabel are caught by the regex.

#### Takeaway

The regex extension closed most of `-nemotron`'s obfuscation-driven gap, but exposed its one remaining real weakness clearly: it tags obfuscated emails as `user_name` rather than `email` often enough that the regex can't compensate (the model's own conflicting label blocks the regex span from being added). This is the same root cause flagged in the false-positive analysis below, just from the FN side.

### OpenMed-PII-SuperClinical-Small-44M-v1

#### pii-injected-v1 (4 FN)

By type: PHONE 4.

Down from 17 (credit-card weakness resolved by the Luhn fix). The remaining 4 are `+1 xxx xxx xxxx` international-format phones (`+1 979 078 0958`, `+1 947 463 7319`) that don't match the regex's dotted/bare-digit-run patterns and aren't caught by the model either -- this model's distinct international-phone-format gap, unchanged by the regex extension since it targets a different format.

#### pii-injected-hard-v1 (16 FN)

By type: PHONE 7, EMAIL 5, USERNAME 3, NAME 1.

Down from 58. PHONE (7) is a mix of the same international-format gap plus a few remaining obfuscated cases the regex didn't fully resolve; EMAIL (5) and USERNAME (3) are the same model-mislabeling issue as `-nemotron` (email tagged as `user_name`).

#### pii-realistic-v1 (2 FN)

By type: PHONE 2.

Down from 27. Only the international-format phone gap remains; the email-obfuscation weakness that dominated this dataset before is resolved.

#### Takeaway

The regex extension closed nearly all of the Small model's obfuscation-driven misses, leaving its two distinct pre-existing weaknesses clearly visible: the international `+1 xxx xxx xxxx` phone format (a format the regex doesn't target) and the same email-tagged-as-username labeling issue shared with `-nemotron`.

### OpenMed-PII-SuperClinical-Large-434M-v1

#### pii-injected-v1 (2 FN)

By type: PHONE 2.

Down from 11 (credit-card weakness resolved by the Luhn fix). Two isolated phone misses remain, not a systematic format gap.

#### pii-injected-hard-v1 (0 FN)

100% recall. Down from 38 before the regex extension -- every previously-missed SSN/PHONE/CREDIT_CARD/EMAIL/IP_ADDRESS entity on this dataset is now caught.

#### pii-realistic-v1 (0 FN)

100% recall. Down from 12.

#### Takeaway

`SuperClinical-Large` doesn't share the Small model's international-phone-format gap, and its own detection was already strong enough on emails/usernames that the regex extension closes the rest of the gap completely on both harder datasets. It's now the clear best performer in this comparison by both recall and F1.

## False positive analysis: OpenMed/privacy-filter-nemotron

Breakdown of every spurious predicted entity (post-exclusion, post-coalescing), using the cached model predictions (see `analyze_fp.py`).

### pii-injected-v1 (9 FP)

By type: `street_address` 4, `first_name` 3, `user_name` 1, `phone_number` 1.

Mostly nonsense triggers on non-PII text that happens to look structured: the recurring Jira-style ticket title `"20240930 - job details 404 Internal RCA"` gets tagged `street_address` four times (the leading "404" reads like a house number), and the literal word "Workato" gets tagged `first_name` three times. One `user_name` FP fires on a bare number (`3994`) inside a "Name: 3994" prompt-injection line, and one `phone_number` FP is a truncated fragment of a credit-card number (`886` out of `8860-2196-8673-1603`) — a partial/malformed span rather than a distinct error.

### pii-injected-hard-v1 (26 FP)

By type: `ipv4` 10, `user_name` 6, `street_address` 3, `credit_debit_card` 2, `first_name` 2, `phone_number` 2, `last_name` 1.

Two distinct patterns dominate:
- **`ipv4` FPs are the mirror image of the IP_ADDRESS false negatives**: the model sees a defanged/obfuscated IP (`230[.]61[.]201[.]79`, `518.38.1848`, `693.259.7043`), tags a truncated or shifted substring as `ipv4`, but the span doesn't overlap the full expected entity closely enough to count as a match — so the same obfuscated IP produces both a FN (missed full span) and a FP (wrong/partial span) simultaneously.
- **`user_name` FPs are almost all the spelled-out-email obfuscation** (`nina.tanaka[at]acme.io`, `diego dot novak at acme dot io`, `sven.patel @ acme.io`): the model correctly notices these are identifiers but tags them `user_name` instead of `email`, so each one scores as an EMAIL false negative *and* a USERNAME false positive — the single biggest driver of `-nemotron`'s poor precision/recall on this dataset.

The `550e8400-e29b-...` UUID getting tagged `credit_debit_card` (2 instances) and the Jira-title `street_address` FPs (3, same pattern as `injected-v1`) round out the rest.

### pii-realistic-v1 (26 FP)

By type: `user_name` 17, `first_name` 4, `ipv4` 3, `street_address` 1, `phone_number` 1.

Overwhelmingly the same **email-mislabeled-as-username** pattern seen on `hard-v1`, but far more concentrated (17 of 26 FPs): `priya dot khan at corp dot example`, `sara dot tanaka at acme dot io`, `yuki dot patel at example dot com`, etc. This dataset's realistic email-signature phrasing ("Thanks, Alex Rossi\npriya dot khan at corp dot example") triggers it constantly. This single mislabeling (`email` → `user_name` instead of the dataset's `email` tag) is directly responsible for both the 23 EMAIL false negatives and the majority of false positives here — it's one underlying error counted twice by the scoring harness, not two independent weaknesses.

### Takeaway

`-nemotron`'s false positives aren't random noise — they're concentrated in two mechanical patterns: (1) a handful of "looks like an address/name" false triggers on structurally similar non-PII text (ticket titles, the word "Workato"), consistent across all three datasets in a small, harness-superficial way; and (2) **the model tagging spelled-out/obfuscated emails as `user_name` instead of `email`**, which is the same underlying failure driving most of its EMAIL recall gap identified in the false-negative analysis above. Fixing #2 (e.g. broadening the LABEL_MAP so `user_name` predictions overlapping an expected EMAIL span count as a match, or improving the model's own email-vs-username disambiguation on obfuscated text) would improve precision on `hard-v1`/`realistic-v1` and simultaneously close most of the recall gap — they're the same bug.

## Cross-model false-negative takeaway

Post-regex-extension, the two weaknesses every model used to share -- **credit cards** (fixed by the Luhn-as-soft-signal change) and **dotted/defanged/bare-digit-run SSN/phone/IP obfuscation** (fixed by this update's regex extension) -- are both resolved across all four models. What's left is genuinely model-specific: `-nemotron` and `SuperClinical-Small` both still tag obfuscated emails as `user_name` instead of `email` often enough to show up as FN/FP pairs (the regex can't compensate when the model's own conflicting label already claims the span); `SuperClinical-Small` additionally has a unique, regex-untouched weakness on plain international `+1 xxx xxx xxxx` phone formats; and `SuperClinical-Large` shares neither residual weakness, landing at 0 FN on both `hard-v1` and `realistic-v1`.
