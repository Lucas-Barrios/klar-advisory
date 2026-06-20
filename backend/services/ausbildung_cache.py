import base64
import logging
from datetime import datetime, timezone

import httpx
from database import get_supabase

SECTORS = {
    "Pflege": "nursing",
    "Mechatroniker": "mechatronics",
    "Informatik": "it",
    "Hotel": "hospitality",
    "Küche": "gastronomy",
}

API_BASE = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
DETAIL_API_BASE = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails"
API_KEY = "jobboerse-jobsuche"

logger = logging.getLogger(__name__)


def fetch_sector_positions(keyword: str, limit: int = 25) -> list[dict]:
    try:
        response = httpx.get(
            API_BASE,
            params={"was": keyword, "angebotsart": "4", "page": "1", "size": str(limit)},
            headers={"X-API-Key": API_KEY},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json().get("stellenangebote", [])
    except Exception as e:
        print(f"Failed to fetch positions for '{keyword}': {e}")
        return []


def fetch_job_description(refnr: str) -> str | None:
    """Return the full posting text for a position, fetching and caching on demand.

    Checks full_description_fetched_at to determine cache freshness.
    On any failure (HTTP error, missing DB columns, timeout), logs a warning
    and returns None so callers degrade gracefully — matches the resilience
    pattern used for target_keywords in diagnostic.py.
    """
    supabase = get_supabase()

    # Cache-hit path: if fetched_at is set (even if description is NULL, we already tried)
    try:
        result = supabase.table("ausbildung_positions").select(
            "full_description, full_description_fetched_at"
        ).eq("refnr", refnr).single().execute()
        row = result.data or {}
        if row.get("full_description_fetched_at") is not None:
            return row.get("full_description")
    except Exception as e:
        logger.warning("fetch_job_description: cache lookup failed for %r: %s", refnr, e)

    # Fetch from the detail endpoint
    try:
        encoded = base64.b64encode(refnr.encode()).decode()
        response = httpx.get(
            f"{DETAIL_API_BASE}/{encoded}",
            headers={"X-API-Key": API_KEY},
            timeout=10.0,
        )
        response.raise_for_status()
        description: str | None = response.json().get("stellenangebotsBeschreibung")
    except Exception as e:
        logger.warning("fetch_job_description: HTTP fetch failed for %r: %s", refnr, e)
        return None

    # Persist to cache (best-effort; degraded without the migration columns)
    try:
        supabase.table("ausbildung_positions").upsert(
            {
                "refnr": refnr,
                "full_description": description,
                "full_description_fetched_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="refnr",
        ).execute()
    except Exception as e:
        logger.warning("fetch_job_description: cache write failed for %r: %s", refnr, e)

    return description


def refresh_all_positions() -> dict:
    supabase = get_supabase()
    results = {}

    for keyword, sector_name in SECTORS.items():
        positions = fetch_sector_positions(keyword)
        results[sector_name] = len(positions)

        for p in positions:
            refnr = p.get("refnr")
            if not refnr:
                continue

            arbeitsort = p.get("arbeitsort", {})
            koordinaten = arbeitsort.get("koordinaten", {})

            row = {
                "refnr": refnr,
                "sector_keyword": sector_name,
                "beruf": p.get("beruf"),
                "titel": p.get("titel"),
                "arbeitgeber": p.get("arbeitgeber"),
                "plz": arbeitsort.get("plz"),
                "ort": arbeitsort.get("ort"),
                "region": arbeitsort.get("region"),
                "lat": koordinaten.get("lat"),
                "lon": koordinaten.get("lon"),
                "eintrittsdatum": p.get("eintrittsdatum"),
                "veroeffentlichungsdatum": p.get("aktuelleVeroeffentlichungsdatum"),
                "application_url": f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}",
            }

            try:
                supabase.table("ausbildung_positions").upsert(
                    row, on_conflict="refnr"
                ).execute()
            except Exception as e:
                print(f"Failed to upsert position {refnr}: {e}")

    return results
