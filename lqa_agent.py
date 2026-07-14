"""
Core agent logic for the Places API lead qualification agent.

Supports two backends:
1. Google Places API (New) — preferred, needs a Google Cloud API key
2. SerpAPI Google Local — fallback, needs a SerpAPI key

Both return the same normalized shape so the rest of the pipeline is
backend-agnostic.
"""

import re
import requests

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
SERPAPI_BASE = "https://serpapi.com/search"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.types",
    "places.primaryType",
    "places.rating",
    "places.userRatingCount",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.googleMapsUri",
])

MAX_RESULTS_PER_CALL = 20


# ---------------------------------------------------------------------------
# Backend: Google Places API (New)
# ---------------------------------------------------------------------------

def _search_google(query: str, api_key: str, max_results: int = 20) -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {"textQuery": query, "maxResultCount": min(max_results, MAX_RESULTS_PER_CALL)}
    resp = requests.post(PLACES_SEARCH_URL, headers=headers, json=body, timeout=15)
    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except ValueError:
            detail = resp.text
        raise RuntimeError(f"Google Places API error ({resp.status_code}): {detail}")
    return resp.json().get("places", [])


# ---------------------------------------------------------------------------
# Backend: SerpAPI Google Local
# ---------------------------------------------------------------------------

def _parse_reviews(raw) -> int:
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        raw = raw.replace(",", "")
        m = re.search(r"([\d.]+)", raw)
        if m:
            val = float(m.group(1))
            if "k" in raw.lower():
                val *= 1000
            return int(val)
        return 0
    return 0


def _map_serp_to_google(r: dict) -> dict:
    """Map a SerpAPI local result to the Google Places API response shape,
    so normalize_place works unchanged for both backends."""
    raw_type = r.get("type", "")
    if isinstance(raw_type, list):
        types_list = raw_type
        primary = raw_type[0] if raw_type else ""
    else:
        types_list = [raw_type] if raw_type else []
        primary = raw_type

    reviews = _parse_reviews(r.get("reviews", 0))
    phone = r.get("phone") or r.get("links", {}).get("phone")
    website = r.get("website") or r.get("links", {}).get("website")
    place_id = r.get("place_id", "")

    return {
        "displayName": {"text": r.get("title", "Unknown business")},
        "formattedAddress": r.get("address", "Address not listed"),
        "types": types_list,
        "primaryType": primary.replace(" ", "_").lower() if primary else None,
        "rating": r.get("rating"),
        "userRatingCount": reviews,
        "internationalPhoneNumber": phone,
        "websiteUri": website,
        "googleMapsUri": f"https://www.google.com/maps?cid={place_id}" if place_id else "",
        "id": f"serp_{place_id}" if place_id else "",
    }


def _search_serp(query: str, serp_key: str, max_results: int = 20) -> list[dict]:
    params = {
        "engine": "google_local",
        "q": query,
        "api_key": serp_key,
        "num": min(max_results, MAX_RESULTS_PER_CALL),
    }
    resp = requests.get(SERPAPI_BASE, params=params, timeout=15)
    if resp.status_code != 200:
        try:
            detail = resp.json().get("error", resp.text)
        except ValueError:
            detail = resp.text
        raise RuntimeError(f"SerpAPI error ({resp.status_code}): {detail}")

    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"SerpAPI error: {data['error']}")

    raw = data.get("local_results", [])
    return [_map_serp_to_google(r) for r in raw]


# ---------------------------------------------------------------------------
# Dispatcher — try Google first, fall back to SerpAPI
# ---------------------------------------------------------------------------

def search_places(
    query: str,
    api_key: str = "",
    serp_key: str = "",
    max_results: int = 20,
) -> tuple[list[dict], str]:
    """Search for places. Tries Google Places API first if api_key given,
    then falls back to SerpAPI if serp_key given. Raises RuntimeError if
    neither key is provided or both fail.

    Returns (places_list, backend_name)."""
    errors = []
    if api_key:
        try:
            return _search_google(query, api_key, max_results), "Google Places API"
        except Exception as e:
            errors.append(f"Google: {e}")
            if not serp_key:
                raise
    if serp_key:
        try:
            return _search_serp(query, serp_key, max_results), "SerpAPI (Google Local)"
        except Exception as e:
            errors.append(f"SerpAPI: {e}")
            raise RuntimeError("; ".join(errors)) from e
    raise RuntimeError("No API key provided — set a Google Places or SerpAPI key.")


# ---------------------------------------------------------------------------
# Normalization — converts raw API response (Google-shaped) to internal shape
# ---------------------------------------------------------------------------

def normalize_place(place: dict) -> dict:
    return {
        "name": place.get("displayName", {}).get("text", "Unknown business"),
        "address": place.get("formattedAddress", "Address not listed"),
        "types": place.get("types", []),
        "primary_type": (place.get("primaryType") or "").replace("_", " "),
        "rating": place.get("rating"),
        "rating_count": place.get("userRatingCount", 0),
        "phone": place.get("internationalPhoneNumber"),
        "website": place.get("websiteUri"),
        "maps_url": place.get("googleMapsUri", ""),
        "place_id": place.get("id", ""),
    }


# ---------------------------------------------------------------------------
# Scoring — each check independently auditable
# ---------------------------------------------------------------------------

def score_lead(place: dict, criteria: dict) -> tuple[float, dict]:
    checks = {}

    kw = criteria["keyword"].lower()
    name_l = place["name"].lower()
    types_l = " ".join(place["types"]).lower()
    primary_l = place["primary_type"].lower()
    category_match = kw in name_l or kw in types_l or kw in primary_l
    checks["category_relevance"] = (
        category_match,
        place["primary_type"] or (", ".join(place["types"][:3]) if place["types"] else "no category listed"),
    )

    has_phone = bool(place.get("phone"))
    checks["phone_available"] = (has_phone, place.get("phone") or "not listed")

    has_website = bool(place.get("website"))
    checks["website_available"] = (has_website, place.get("website") or "not listed")

    rating_count = place.get("rating_count") or 0
    established = rating_count >= criteria.get("min_reviews", 5)
    rating_str = f"{place.get('rating', 'n/a')} stars, {rating_count} reviews"
    checks["established_presence"] = (established, rating_str)

    weights = {
        "category_relevance": 0.35,
        "phone_available": 0.25,
        "website_available": 0.20,
        "established_presence": 0.20,
    }
    confidence = round(sum(weights[k] for k, (ok, _) in checks.items() if ok), 2)
    return confidence, checks


# ---------------------------------------------------------------------------
# Outreach
# ---------------------------------------------------------------------------

def draft_outreach(place: dict, good_or_service: str) -> str:
    first_line = place["primary_type"] or "your business"
    return (
        f"Subject: Bulk supply inquiry — {good_or_service}\n\n"
        f"Hi {place['name']} team,\n\n"
        f"Came across your listing as a {first_line} in {place['address']}. "
        f"We supply {good_or_service} and wanted to check if a bulk/wholesale "
        f"arrangement would be useful for your operations.\n\n"
        f"Happy to share pricing and volume options — worth a quick call?\n\n"
        f"Best,\n[Your name]"
    )
