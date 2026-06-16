"""
Exploration script for the Bundesagentur für Arbeit job search API.

Correct endpoint: jobboerse/jobsuche-service/pc/v4/jobs
Filter: angebotsart=4 (Ausbildung / apprenticeship positions only)

NOTE: The infosysbub/absuche endpoint returns training COURSES (Kursnet),
not employer apprenticeship vacancies. Do not use it for position matching.
"""

import requests
import json
from typing import Optional

BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
HEADERS = {"X-API-Key": "jobboerse-jobsuche"}
DIRECT_URL_TEMPLATE = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"

SECTORS = {
    "Pflege": "nursing/care",
    "Mechatroniker": "mechatronics",
    "Informatik": "IT",
    "Hotel": "hospitality",
    "Küche": "kitchen/culinary",
}


def fetch_ausbildung_positions(keyword: str, page: int = 0) -> list[dict]:
    """
    Fetch apprenticeship (Ausbildung) positions from the BA job search API.

    Args:
        keyword: Occupation keyword in German (e.g. "Pflege", "Mechatroniker")
        page: Page number, 1-indexed (API uses page=1 as first page)

    Returns:
        List of position dicts with normalized field names.
        Empty list on any error.
    """
    # API is 1-indexed; allow callers to pass 0 and convert
    api_page = max(1, page + 1) if page == 0 else page

    params = {
        "was": keyword,
        "angebotsart": 4,  # 4 = Ausbildung (apprenticeship) only
        "page": api_page,
        "size": 20,
    }

    try:
        resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection failed for keyword='{keyword}': {e}")
        return []
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timed out for keyword='{keyword}'")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP {resp.status_code} for keyword='{keyword}': {e}")
        return []

    raw_items = resp.json().get("stellenangebote", [])
    positions = []
    for item in raw_items:
        loc = item.get("arbeitsort", {})
        refnr = item.get("refnr", "")
        positions.append({
            "refnr": refnr,
            "direct_url": DIRECT_URL_TEMPLATE.format(refnr=refnr) if refnr else None,
            "beruf": item.get("beruf"),
            "titel": item.get("titel"),
            "arbeitgeber": item.get("arbeitgeber"),
            "city": loc.get("ort"),
            "plz": loc.get("plz"),
            "region": loc.get("region"),
            "lat": loc.get("koordinaten", {}).get("lat"),
            "lon": loc.get("koordinaten", {}).get("lon"),
            "eintrittsdatum": item.get("eintrittsdatum"),
            "veroeffentlicht": item.get("aktuelleVeroeffentlichungsdatum"),
        })
    return positions


def fetch_result_count(keyword: str) -> int:
    """Return total apprenticeship result count for a keyword without fetching all pages."""
    params = {"was": keyword, "angebotsart": 4, "page": 1, "size": 1}
    try:
        resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("maxErgebnisse", 0)
    except Exception:
        return -1


def main():
    print("=" * 70)
    print("Bundesagentur für Arbeit — Ausbildung API Exploration")
    print("Endpoint: jobboerse/jobsuche-service/pc/v4/jobs?angebotsart=4")
    print("=" * 70)
    print()

    # Summary table
    print(f"{'Sector':<18} {'Keyword':<16} {'Count':>8}  {'Sample employer':<35} {'Sample city'}")
    print("-" * 100)

    for keyword, sector_label in SECTORS.items():
        total = fetch_result_count(keyword)
        positions = fetch_ausbildung_positions(keyword, page=0)
        if positions:
            sample = positions[0]
            employer = (sample["arbeitgeber"] or "?")[:34]
            city = sample["city"] or "?"
        else:
            employer = "no results"
            city = "?"
        print(f"{sector_label:<18} {keyword:<16} {total:>8}  {employer:<35} {city}")

    print()
    print("=" * 70)
    print("SAMPLE FULL RECORD (Pflege, page 1, first result)")
    print("=" * 70)
    positions = fetch_ausbildung_positions("Pflege", page=0)
    if positions:
        print(json.dumps(positions[0], indent=2, ensure_ascii=False))

    print()
    print("=" * 70)
    print("PAGINATION CHECK (Pflege, pages 1-3)")
    print("=" * 70)
    seen_refnrs = set()
    for pg in [1, 2, 3]:
        positions = fetch_ausbildung_positions("Pflege", page=pg)
        page_refnrs = {p["refnr"] for p in positions}
        overlap = page_refnrs & seen_refnrs
        print(f"  Page {pg}: {len(positions)} results, overlap with prior pages: {len(overlap)}")
        seen_refnrs |= page_refnrs

    print()
    print("=" * 70)
    print("FIELD INVENTORY")
    print("=" * 70)
    positions = fetch_ausbildung_positions("Pflege", page=0)
    if positions:
        sample = positions[0]
        for field, value in sample.items():
            present = value is not None
            print(f"  {field:<22}: {'✓' if present else '✗ (null)'}  {repr(value) if present else ''}")

    print()
    print("NOTES:")
    print("  - No German language level field exists in the API data.")
    print("    Language assessment must come from Claude reasoning on occupation type.")
    print("  - 'eintrittsdatum' = intended start date (usually Oct 1 for apprenticeships).")
    print("  - 'veroeffentlicht' = listing publication date (use as freshness indicator).")
    print("  - Location is structured: PLZ + city string + lat/lon + region.")
    print("  - Direct application URL = https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}")


if __name__ == "__main__":
    main()
