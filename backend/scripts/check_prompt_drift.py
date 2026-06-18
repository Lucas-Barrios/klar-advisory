#!/usr/bin/env python3
"""
CI gate: fail loudly if SYSTEM_PROMPT changed but DIAGNOSTIC_PROMPT_VERSION wasn't bumped.

How it works:
1. Hash the current SYSTEM_PROMPT from germany_diagnostic.py.
2. Read the last recorded hash from .prompt_hashes (committed to repo).
3. If the hash changed AND the version string hasn't changed → exit(1) with a clear message.
4. If the hash changed AND the version was bumped → update .prompt_hashes, remind to commit.

Run this in CI before any deploy step.

Usage:
    python scripts/check_prompt_drift.py          # check mode (default)
    python scripts/check_prompt_drift.py --update  # record current hashes as baseline
"""
import argparse
import hashlib
import json
import os
import sys

HASH_FILE = os.path.join(os.path.dirname(__file__), ".prompt_hashes")

# Paths relative to repo root (when run from backend/)
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)

sys.path.insert(0, _BACKEND)


def _hash_string(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _load_stored() -> dict:
    if not os.path.exists(HASH_FILE):
        return {}
    with open(HASH_FILE) as f:
        return json.load(f)


def _save_stored(data: dict) -> None:
    with open(HASH_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _get_current_state() -> dict[str, str]:
    from agents.germany_diagnostic import SYSTEM_PROMPT
    from agents.ausbildung_matcher import MATCH_PROMPT
    from agents.document_factory import DOCUMENT_PROMPT
    # Import *_DEFAULT constants so env overrides can't produce false pass/fail.
    # A stray DIAGNOSTIC_PROMPT_VERSION env var would mask a real drift if we
    # imported the env-resolved constant here.
    from services.diagnostic_versions import (
        DIAGNOSTIC_PROMPT_VERSION_DEFAULT,
        MATCH_PROMPT_VERSION_DEFAULT,
        DOCUMENT_PROMPT_VERSION_DEFAULT,
    )

    return {
        "diagnostic": {
            "prompt_hash": _hash_string(SYSTEM_PROMPT),
            "version": DIAGNOSTIC_PROMPT_VERSION_DEFAULT,
        },
        "match": {
            "prompt_hash": _hash_string(MATCH_PROMPT),
            "version": MATCH_PROMPT_VERSION_DEFAULT,
        },
        "document": {
            "prompt_hash": _hash_string(DOCUMENT_PROMPT),
            "version": DOCUMENT_PROMPT_VERSION_DEFAULT,
        },
    }


def check() -> bool:
    stored = _load_stored()
    current = _get_current_state()
    failed = False

    for key, state in current.items():
        prev = stored.get(key, {})
        prev_hash = prev.get("prompt_hash")
        prev_version = prev.get("version")

        if prev_hash is None:
            print(f"[INFO] {key}: no baseline recorded yet — run with --update to set one.")
            continue

        hash_changed = state["prompt_hash"] != prev_hash
        version_changed = state["version"] != prev_version

        if hash_changed and not version_changed:
            print(
                f"\n[FAIL] Prompt drift detected for '{key}':\n"
                f"  Stored hash:    {prev_hash}\n"
                f"  Current hash:   {state['prompt_hash']}\n"
                f"  Version:        {state['version']} (unchanged)\n"
                f"\n  The {key} prompt changed but the version string was not bumped.\n"
                f"  Edit services/diagnostic_versions.py and bump the version, then re-run\n"
                f"  `python scripts/check_prompt_drift.py --update` to record the new baseline.\n"
            )
            failed = True
        elif hash_changed and version_changed:
            print(
                f"[OK] {key}: prompt changed and version bumped "
                f"({prev_version} → {state['version']}). "
                f"Run --update to record new baseline."
            )
        else:
            print(f"[OK] {key}: prompt unchanged (hash={state['prompt_hash']}, version={state['version']}).")

    return not failed


def update() -> None:
    current = _get_current_state()
    _save_stored(current)
    print(f"Recorded prompt hashes to {HASH_FILE}.")
    print("Commit this file alongside any prompt changes.")
    for key, state in current.items():
        print(f"  {key}: hash={state['prompt_hash']} version={state['version']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check for prompt drift without version bump.")
    parser.add_argument("--update", action="store_true", help="Record current hashes as new baseline.")
    args = parser.parse_args()

    if args.update:
        update()
        return

    ok = check()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
