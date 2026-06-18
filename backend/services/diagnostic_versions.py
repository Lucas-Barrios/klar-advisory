import os


# Bump DIAGNOSTIC_PROMPT_VERSION whenever SYSTEM_PROMPT in germany_diagnostic.py changes.
# The check_prompt_drift.py CI gate will fail if the hash changes without a version bump.
DIAGNOSTIC_PROMPT_VERSION = os.getenv(
    "DIAGNOSTIC_PROMPT_VERSION",
    "germany_diagnostic_prompt_v2",
)
DIAGNOSTIC_RUBRIC_VERSION = os.getenv(
    "DIAGNOSTIC_RUBRIC_VERSION",
    "germany_readiness_rubric_v1",
)

# Bump when MATCH_PROMPT in ausbildung_matcher.py changes.
MATCH_PROMPT_VERSION = os.getenv(
    "MATCH_PROMPT_VERSION",
    "ausbildung_match_prompt_v1",
)

# Bump when DOCUMENT_PROMPT in document_factory.py changes.
DOCUMENT_PROMPT_VERSION = os.getenv(
    "DOCUMENT_PROMPT_VERSION",
    "document_factory_prompt_v1",
)
