"""Config for OpenMed/privacy-filter-nemotron.

This model's label set is far broader than the dataset's taxonomy (NAME,
EMAIL, PHONE, ADDRESS, SSN, CREDIT_CARD, USERNAME, IP_ADDRESS) -- it also
tags things like age, blood_type, occupation, political_view, device
identifiers, secrets (api_key/password/pin/cvv), and various date/time
variants. Labels with a real counterpart in the dataset map to that type's
set; every other label is out of scope for this comparison entirely and
goes in EXCLUDED_LABELS -- the model correctly recognizing e.g. a date or
city isn't a false positive against a taxonomy that doesn't include dates
or cities, so those predictions are dropped before scoring rather than
counted.
"""

MODEL_NAME = "OpenMed/privacy-filter-nemotron"

SHORT_NAME = "privacy_filter_nemotron"

# Model entity labels -> set of dataset entity types accepted as a correct match.
LABEL_MAP = {
    "first_name": {"NAME"},
    "last_name": {"NAME"},
    "email": {"EMAIL"},
    "phone_number": {"PHONE"},
    "street_address": {"ADDRESS"},
    "ssn": {"SSN"},
    "credit_debit_card": {"CREDIT_CARD"},
    "user_name": {"USERNAME"},
    "ipv4": {"IP_ADDRESS"},
    "ipv6": {"IP_ADDRESS"},
    # regex_pii spans are already tagged with dataset type names.
    "SSN": {"SSN"},
    "CREDIT_CARD": {"CREDIT_CARD"},
    "IP_ADDRESS": {"IP_ADDRESS"},
    "PHONE": {"PHONE"},
    "EMAIL": {"EMAIL"},
}

# Every model label with no dataset-taxonomy counterpart -- excluded entirely
# from scoring (never counted as tp/fp/fn), same rationale as privacy_filter's
# private_date/private_url/secret exclusions.
EXCLUDED_LABELS = {
    "account_number",
    "age",
    "api_key",
    "bank_routing_number",
    "biometric_identifier",
    "blood_type",
    "certificate_license_number",
    "city",
    "company_name",
    "coordinate",
    "country",
    "county",
    "customer_id",
    "cvv",
    "date",
    "date_of_birth",
    "date_time",
    "device_identifier",
    "education_level",
    "employee_id",
    "employment_status",
    "fax_number",
    "gender",
    "health_plan_beneficiary_number",
    "http_cookie",
    "language",
    "license_plate",
    "mac_address",
    "medical_record_number",
    "national_id",
    "occupation",
    "password",
    "pin",
    "political_view",
    "postcode",
    "race_ethnicity",
    "religious_belief",
    "sexuality",
    "state",
    "swift_bic",
    "tax_id",
    "time",
    "unique_id",
    "url",
    "vehicle_identifier",
}

# Minimum span confidence (min score across the span's constituent tokens) to
# keep a predicted span. Spans below this are dropped before scoring, as if
# the model never predicted them. Set to 0.0 to disable thresholding.
SCORE_THRESHOLD = 0.0

# Supplement this model's predictions with regex_pii spans -- its own
# SSN/CREDIT_CARD/IP_ADDRESS detection has a systematic blind spot on
# clean/unbroken-digit-run formats (see pii-results-comparison.md's
# false-negative analysis) that the regex layer catches.
USE_REGEX_SPANS = True
