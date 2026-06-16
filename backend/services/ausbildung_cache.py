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
API_KEY = "jobboerse-jobsuche"


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
