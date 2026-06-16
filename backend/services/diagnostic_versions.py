import os


DIAGNOSTIC_PROMPT_VERSION = os.getenv(
    "DIAGNOSTIC_PROMPT_VERSION",
    "germany_diagnostic_prompt_v1",
)
DIAGNOSTIC_RUBRIC_VERSION = os.getenv(
    "DIAGNOSTIC_RUBRIC_VERSION",
    "germany_readiness_rubric_v1",
)
