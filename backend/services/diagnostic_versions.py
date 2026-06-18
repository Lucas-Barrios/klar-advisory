import os

# ---------------------------------------------------------------------------
# Source-controlled defaults — these are the canonical version strings.
# check_prompt_drift.py reads the *_DEFAULT constants directly so that a
# stray environment variable cannot produce a false "unchanged" or false
# "changed" result during CI. The application-visible constants (without
# _DEFAULT) still honour env overrides for deployment flexibility.
# ---------------------------------------------------------------------------

# Bump when SYSTEM_PROMPT in germany_diagnostic.py changes.
# The check_prompt_drift.py CI gate will fail if the hash changes without a bump.
DIAGNOSTIC_PROMPT_VERSION_DEFAULT = "germany_diagnostic_prompt_v3"
DIAGNOSTIC_PROMPT_VERSION = os.getenv(
    "DIAGNOSTIC_PROMPT_VERSION",
    DIAGNOSTIC_PROMPT_VERSION_DEFAULT,
)

DIAGNOSTIC_RUBRIC_VERSION_DEFAULT = "germany_readiness_rubric_v1"
DIAGNOSTIC_RUBRIC_VERSION = os.getenv(
    "DIAGNOSTIC_RUBRIC_VERSION",
    DIAGNOSTIC_RUBRIC_VERSION_DEFAULT,
)

# Bump when MATCH_PROMPT in ausbildung_matcher.py changes.
MATCH_PROMPT_VERSION_DEFAULT = "ausbildung_match_prompt_v1"
MATCH_PROMPT_VERSION = os.getenv(
    "MATCH_PROMPT_VERSION",
    MATCH_PROMPT_VERSION_DEFAULT,
)

# Bump when DOCUMENT_PROMPT in document_factory.py changes.
DOCUMENT_PROMPT_VERSION_DEFAULT = "document_factory_prompt_v2"
DOCUMENT_PROMPT_VERSION = os.getenv(
    "DOCUMENT_PROMPT_VERSION",
    DOCUMENT_PROMPT_VERSION_DEFAULT,
)
