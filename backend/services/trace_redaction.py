from __future__ import annotations

import copy
import re

# Label-value patterns that appear in our prompt templates.
# Each pattern captures (label_prefix, pii_value) so we can replace just the value.
# re.MULTILINE makes ^ / $ match per-line, so .+ stops at the newline boundary.
_PII_PATTERNS: list[re.Pattern[str]] = [
    # Diagnostic + document user messages
    re.compile(r"^(Name: )(.+)$", re.MULTILINE),
    re.compile(r"^(Financial Situation: )(.+)$", re.MULTILINE),
    # germany_diagnostic uses "Current Location:" (capital L), ausbildung_matcher uses lowercase
    re.compile(r"^(Current [Ll]ocation: )(.+)$", re.MULTILINE),
    # document_factory facts block (from _build_facts_block)
    re.compile(r"^(- Employer name: )(.+)$", re.MULTILINE),
    re.compile(r"^(- Street address: )(.+)$", re.MULTILINE),
    re.compile(r"^(- Phone number: )(.+)$", re.MULTILINE),
    re.compile(r"^(- Full address: )(.+)$", re.MULTILINE),
]


def _redact_text(text: str) -> str:
    for pattern in _PII_PATTERNS:
        text = pattern.sub(lambda m: m.group(1) + "[REDACTED]", text)
    return text


def _redact_content(content: object) -> object:
    if isinstance(content, str):
        return _redact_text(content)
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                block["text"] = _redact_text(block["text"])
    return content


def redact_trace_inputs(inputs: dict) -> dict:
    """Redact known PII fields before they reach LangSmith.
    Only operates on the LangSmith trace copy — never modifies what's
    actually sent to Anthropic for inference."""
    inputs = copy.deepcopy(inputs)
    messages = inputs.get("messages")
    if not isinstance(messages, list):
        return inputs
    for msg in messages:
        if isinstance(msg, dict) and "content" in msg:
            msg["content"] = _redact_content(msg["content"])
    return inputs
