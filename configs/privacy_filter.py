"""Config for openai/privacy-filter."""

MODEL_NAME = "openai/privacy-filter"

# Short name used for raw_results/<name>/ and results/summary.json keys.
SHORT_NAME = "privacy_filter"

# Model labels excluded entirely from scoring (never counted as tp/fp/fn).
EXCLUDED_LABELS = {"private_date", "private_url", "secret"}

# Minimum span confidence (min score across the span's constituent tokens) to
# keep a predicted span. Spans below this are dropped before scoring, as if
# the model never predicted them. Set to 0.0 to disable thresholding.
SCORE_THRESHOLD = 0.0

# Model entity labels -> set of dataset entity types accepted as a correct match.
LABEL_MAP = {
    "private_person": {"NAME", "USERNAME"},
    "private_email": {"EMAIL"},
    "private_phone": {"PHONE"},
    "private_address": {"ADDRESS"},
    "account_number": {"SSN", "CREDIT_CARD"},
    # regex_pii spans are already tagged with dataset type names.
    "SSN": {"SSN"},
    "CREDIT_CARD": {"CREDIT_CARD"},
    "IP_ADDRESS": {"IP_ADDRESS"},
    "PHONE": {"PHONE"},
    "EMAIL": {"EMAIL"},
}
