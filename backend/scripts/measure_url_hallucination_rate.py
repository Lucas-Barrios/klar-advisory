#!/usr/bin/env python3
"""
Measure the URL hallucination rate from approved diagnostics in the production DB.

For each approved diagnostic, inspect the recommendations[].url field. A URL is
classified as:
  OK       — passes urllib.parse validation AND the domain is on the pre-approved
             safe-domain list derived from the SYSTEM_PROMPT's URL grounding rule.
  NULL     — url field is None or empty string (model correctly withheld a URL
             it wasn't sure about — the intended behaviour from germany_diagnostic_prompt_v3+).
  INVENTED — url present but either not parseable, on an unrecognised domain,
             or fails the safe-domain check.

Outputs a plain-text report with counts and rate, and optionally a JSON file.

Usage:
    # Report to stdout (read-only, safe to run anytime)
    python scripts/measure_url_hallucination_rate.py

    # Also write a JSON report
    python scripts/measure_url_hallucination_rate.py --output url_hallucination_report.json

    # Limit to the most recent N diagnostics
    python scripts/measure_url_hallucination_rate.py --limit 50
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.parse import urlparse

SAFE_DOMAINS: set[str] = {
    # Explicitly named in SYSTEM_PROMPT URL grounding rule
    "daad.de",
    "www.daad.de",
    "goethe.de",
    "www.goethe.de",
    "bamf.de",
    "www.bamf.de",
    "anabin.kmk.org",
    "make-it-in-germany.com",
    "www.make-it-in-germany.com",
    # Well-known German institutions the model reliably links correctly
    "arbeitsagentur.de",
    "www.arbeitsagentur.de",
    "auswaertiges-amt.de",
    "www.auswaertiges-amt.de",
    "kmk.org",
    "www.kmk.org",
    "destatis.de",
    "www.destatis.de",
    "bmbf.de",
    "www.bmbf.de",
    "uni-assist.de",
    "www.uni-assist.de",
    "hochschulstart.de",
    "www.hochschulstart.de",
    "studienkollegs.de",
    "www.studienkollegs.de",
    "iq-netzwerk.de",
    "www.iq-netzwerk.de",
    # Additional well-known institutions observed in production data
    "bibb.de",                          # Bundesinstitut für Berufsbildung
    "www.bibb.de",
    "anerkennung-in-deutschland.de",    # German gov. recognition portal (hosted by BIBB)
    "www.anerkennung-in-deutschland.de",
    "dw.com",                           # Deutsche Welle
    "www.dw.com",
    "learngerman.dw.com",
    "deutschakademie.de",               # DeutschAkademie language school
    "www.deutschakademie.de",
    "ausbildung.de",                    # Ausbildung.de job board
    "www.ausbildung.de",
    "zdh.de",                           # Zentralverband des Deutschen Handwerks
    "www.zdh.de",
    "giz.de",                           # Deutsche Gesellschaft für Internationale Zusammenarbeit
    "www.giz.de",
    "tu.berlin",                        # TU Berlin
    "www.tu.berlin",
    "ahk.de",                           # AHK umbrella (Auslandshandelskammern)
    "www.ahk.de",
    "ahkbrasil.com",                    # AHK Brazil
    "www.ahkbrasil.com",
    "brasilien.ahk.de",
    "ahkargentina.com.ar",              # AHK Argentina
    "www.ahkargentina.com.ar",
    "argentina.ahk.de",
    "zab.de",
    "www.zab.de",
    "studying-in-germany.org",
    "www.studying-in-germany.org",
    "bundesregierung.de",
    "www.bundesregierung.de",
    "euraxess.de",
    "www.euraxess.de",
    "uni-heidelberg.de",
    "www.uni-heidelberg.de",
    "lmu.de",
    "www.lmu.de",
    "tum.de",
    "www.tum.de",
    "rwth-aachen.de",
    "www.rwth-aachen.de",
}


def classify_url(url: str | None) -> str:
    if url is None or url.strip() == "":
        return "NULL"
    try:
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            return "INVENTED"
        domain = parsed.netloc.lower().lstrip("www.")
        fqdn = parsed.netloc.lower()
        if fqdn in SAFE_DOMAINS or f"www.{domain}" in SAFE_DOMAINS or domain in {
            d.lstrip("www.") for d in SAFE_DOMAINS
        }:
            return "OK"
        return "INVENTED"
    except Exception:
        return "INVENTED"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure URL hallucination rate from approved diagnostics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--output", metavar="FILE", help="Write JSON report to this file.")
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Max number of diagnostics to inspect (default: 200).",
    )
    parser.add_argument(
        "--include-pending",
        action="store_true",
        help="Include diagnostics with status='pending' (default: approved only).",
    )
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))

    from dotenv import load_dotenv
    load_dotenv()

    from database import get_supabase
    supabase = get_supabase()

    statuses = ["approved"]
    if args.include_pending:
        statuses.append("pending")

    # Discover which column holds recommendations — try ai_output first, fall back to raw_output
    sample = (
        supabase.table("diagnostics")
        .select("id")
        .in_("status", statuses)
        .limit(1)
        .execute()
    )
    if not (sample.data or []):
        print(f"[measure] No diagnostics found with status in {statuses}.")
        sys.exit(0)

    # Try the column name used by the DB schema
    try:
        supabase.table("diagnostics").select("ai_output").limit(1).execute()
        output_col = "ai_output"
    except Exception:
        output_col = "raw_output"

    query = (
        supabase.table("diagnostics")
        .select(f"id, status, created_at, {output_col}")
        .in_("status", statuses)
        .order("created_at", desc=True)
        .limit(args.limit)
    )
    result = query.execute()
    diagnostics = result.data or []

    total_urls = 0
    null_count = 0
    ok_count = 0
    invented_count = 0
    invented_examples: list[dict] = []

    for diag in diagnostics:
        raw = diag.get(output_col) or {}
        # raw_output may be a JSON string, possibly with a ```json markdown wrapper
        if isinstance(raw, str):
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                # Strip ``` json\n ... ``` wrapper (legacy format before schema gate fix)
                import re as _re
                cleaned = _re.sub(r'^```json?\s*', '', cleaned).strip()
                cleaned = _re.sub(r'\s*```$', '', cleaned).strip()
            try:
                raw = json.loads(cleaned)
            except Exception:
                raw = {}
        recommendations = raw.get("recommendations") or []
        for rec in recommendations:
            url = rec.get("url")
            total_urls += 1
            classification = classify_url(url)
            if classification == "NULL":
                null_count += 1
            elif classification == "OK":
                ok_count += 1
            else:
                invented_count += 1
                if len(invented_examples) < 20:
                    invented_examples.append({
                        "diagnostic_id": diag["id"],
                        "url": url,
                        "rec_name": rec.get("name"),
                    })

    hallucination_rate = round(invented_count / total_urls, 4) if total_urls else None
    null_rate = round(null_count / total_urls, 4) if total_urls else None

    print("\n" + "=" * 60)
    print("URL HALLUCINATION RATE MEASUREMENT")
    print("=" * 60)
    print(f"Diagnostics inspected : {len(diagnostics)}")
    print(f"Total URLs seen       : {total_urls}")
    print(f"  NULL (withheld)     : {null_count}  ({null_rate*100:.1f}% of total)" if null_rate is not None else "  NULL (withheld)     : 0")
    print(f"  OK (safe domain)    : {ok_count}")
    print(f"  INVENTED            : {invented_count}")
    print(f"\nHallucination rate    : {hallucination_rate*100:.1f}%" if hallucination_rate is not None else "\nHallucination rate    : n/a (no URLs seen)")
    print("=" * 60)

    if invented_examples:
        print(f"\nSample invented URLs (up to 20):")
        for ex in invented_examples:
            print(f"  [{ex['diagnostic_id'][:8]}] {ex['rec_name']} → {ex['url']}")

    report = {
        "diagnostics_inspected": len(diagnostics),
        "total_recommendation_urls": total_urls,
        "null_count": null_count,
        "ok_count": ok_count,
        "invented_count": invented_count,
        "hallucination_rate": hallucination_rate,
        "null_rate": null_rate,
        "invented_examples": invented_examples,
        "safe_domain_list": sorted(SAFE_DOMAINS),
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[measure] Report written to {args.output}")

    return report


if __name__ == "__main__":
    main()
