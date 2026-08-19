"""Config for OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1.

Same label vocabulary and BIO tagging convention as privacy_filter_nemotron
(see that config's docstring for the taxonomy-mismatch rationale) -- this
model just omits the E/I-final and S-single-token tags, using plain B/I.
merge_spans handles that fine since it only special-cases S.
"""

from configs.privacy_filter_nemotron import EXCLUDED_LABELS, LABEL_MAP

MODEL_NAME = "OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1"

SHORT_NAME = "pii_superclinical_small"

SCORE_THRESHOLD = 0.0

# Supplement this model's predictions with regex_pii spans -- the model's
# own SSN/CREDIT_CARD/IP_ADDRESS detection has a systematic blind spot on
# clean/unbroken-digit-run formats (see pii-results-comparison.md's
# false-negative analysis) that the regex layer catches.
USE_REGEX_SPANS = True
