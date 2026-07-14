"""
Unit tests for the Places API lead qualification agent (dual backend).

Tests both Google Places and SerpAPI backends, plus normalize_place,
score_lead, draft_outreach. No live network calls.

Run: python -m pytest test_lqa_agent.py -v
"""

import pytest
from unittest import mock
from lqa_agent import (
    search_places,
    normalize_place,
    score_lead,
    draft_outreach,
    _parse_reviews,
    _map_serp_to_google,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fully_populated_place():
    return {
        "displayName": {"text": "Acme Packaging Co"},
        "formattedAddress": "123 Industrial Area, Bhopal, MP",
        "types": ["packaging_supplier", "manufacturing", "point_of_interest"],
        "primaryType": "packaging_supplier",
        "rating": 4.3,
        "userRatingCount": 27,
        "internationalPhoneNumber": "+91-755-1234567",
        "websiteUri": "https://acmepackaging.example.com",
        "googleMapsUri": "https://maps.google.com/?cid=12345",
        "id": "ChIJ1234567890",
    }


@pytest.fixture
def sparse_place():
    return {
        "displayName": {"text": "Obscure Workshop"},
        "formattedAddress": "456 Unknown Lane",
        "types": ["general_contractor"],
        "primaryType": None,
        "rating": None,
        "userRatingCount": None,
        "internationalPhoneNumber": None,
        "websiteUri": None,
        "googleMapsUri": None,
        "id": "ChIJ0000000000",
    }


@pytest.fixture
def no_primary_type_place():
    return {
        "displayName": {"text": "Global Logistics Ltd"},
        "formattedAddress": "789 Transport Nagar",
        "types": ["logistics", "courier_service", "point_of_interest"],
        "primaryType": None,
        "rating": 3.8,
        "userRatingCount": 12,
        "internationalPhoneNumber": "+91-22-9876543",
        "websiteUri": "https://globallogistics.example.com",
        "googleMapsUri": "https://maps.google.com/?cid=67890",
        "id": "ChIJ0987654321",
    }


@pytest.fixture
def default_criteria():
    return {"keyword": "packaging", "min_reviews": 5}


# ---------------------------------------------------------------------------
# _parse_reviews
# ---------------------------------------------------------------------------

class TestParseReviews:
    def test_integer(self):
        assert _parse_reviews(34) == 34

    def test_string_with_reviews(self):
        assert _parse_reviews("34 reviews") == 34

    def test_string_with_k(self):
        assert _parse_reviews("3.4K reviews") == 3400

    def test_parenthesized(self):
        assert _parse_reviews("(862)") == 862

    def test_zero(self):
        assert _parse_reviews(0) == 0
        assert _parse_reviews("") == 0
        assert _parse_reviews(None) == 0


# ---------------------------------------------------------------------------
# _map_serp_to_google
# ---------------------------------------------------------------------------

class TestMapSerpToGoogle:
    def test_basic_mapping(self):
        serp = {
            "title": "Test Business",
            "address": "123 Main St",
            "type": "Coffee shop",
            "rating": 4.5,
            "reviews": 100,
            "phone": "+1-555-1234",
            "website": "https://test.com",
            "place_id": "98765",
            "gps_coordinates": {"latitude": 12.34, "longitude": 56.78},
        }
        g = _map_serp_to_google(serp)
        assert g["displayName"]["text"] == "Test Business"
        assert g["formattedAddress"] == "123 Main St"
        assert g["types"] == ["Coffee shop"]
        assert g["primaryType"] == "coffee_shop"
        assert g["rating"] == 4.5
        assert g["userRatingCount"] == 100
        assert g["internationalPhoneNumber"] == "+1-555-1234"
        assert g["websiteUri"] == "https://test.com"
        assert "98765" in g["googleMapsUri"]
        assert "serp_98765" in g["id"]

    def test_type_as_list(self):
        serp = {
            "title": "Multi Type",
            "address": "456 Oak Ave",
            "type": ["Coffee shop", "Cafe", "Restaurant"],
            "reviews": 50,
        }
        g = _map_serp_to_google(serp)
        assert g["types"] == ["Coffee shop", "Cafe", "Restaurant"]
        assert g["primaryType"] == "coffee_shop"

    def test_phone_in_links(self):
        serp = {
            "title": "Link Phone",
            "address": "789 Pine",
            "type": "Shop",
            "reviews": 10,
            "links": {"phone": "+1-555-9999", "website": "https://shop.com"},
        }
        g = _map_serp_to_google(serp)
        assert g["internationalPhoneNumber"] == "+1-555-9999"
        assert g["websiteUri"] == "https://shop.com"

    def test_no_place_id(self):
        serp = {"title": "No ID", "address": "X", "type": "Other", "reviews": 0}
        g = _map_serp_to_google(serp)
        assert g["googleMapsUri"] == ""
        assert g["id"] == ""

    def test_missing_fields(self):
        g = _map_serp_to_google({})
        assert g["displayName"]["text"] == "Unknown business"
        assert g["formattedAddress"] == "Address not listed"
        assert g["types"] == []
        assert g["primaryType"] is None
        assert g["userRatingCount"] == 0
        assert g["id"] == ""


# ---------------------------------------------------------------------------
# normalize_place
# ---------------------------------------------------------------------------

class TestNormalizePlace:
    def test_fully_populated(self, fully_populated_place):
        n = normalize_place(fully_populated_place)
        assert n["name"] == "Acme Packaging Co"
        assert n["primary_type"] == "packaging supplier"
        assert n["rating"] == 4.3
        assert n["rating_count"] == 27
        assert n["phone"] == "+91-755-1234567"
        assert n["website"] == "https://acmepackaging.example.com"

    def test_sparse(self, sparse_place):
        n = normalize_place(sparse_place)
        assert n["name"] == "Obscure Workshop"
        assert n["primary_type"] == ""
        assert n["rating"] is None
        assert n["rating_count"] is None
        assert n["phone"] is None
        assert n["website"] is None
        assert n["maps_url"] is None

    def test_missing_display_name(self):
        n = normalize_place({"id": "X", "types": ["foo"]})
        assert n["name"] == "Unknown business"

    def test_serp_mapped_result(self):
        serp = {
            "title": "Serp Biz",
            "address": "Serp Address",
            "type": "Packaging company",
            "rating": 4.0,
            "reviews": 15,
            "phone": "+1-555-0000",
            "website": "https://serpbiz.com",
            "place_id": "111111",
        }
        g = _map_serp_to_google(serp)
        n = normalize_place(g)
        assert n["name"] == "Serp Biz"
        assert n["primary_type"] == "packaging company"
        assert n["rating"] == 4.0
        assert n["rating_count"] == 15
        assert n["phone"] == "+1-555-0000"


# ---------------------------------------------------------------------------
# score_lead
# ---------------------------------------------------------------------------

class TestScoreLead:
    def test_full_match(self, fully_populated_place, default_criteria):
        n = normalize_place(fully_populated_place)
        confidence, checks = score_lead(n, default_criteria)
        assert confidence == 1.0
        for k, (ok, _) in checks.items():
            assert ok

    def test_no_match(self, sparse_place):
        criteria = {"keyword": "packaging", "min_reviews": 5}
        n = normalize_place(sparse_place)
        confidence, checks = score_lead(n, criteria)
        assert confidence == 0.0
        for k, (ok, _) in checks.items():
            assert ok is False

    def test_category_match_via_types(self, no_primary_type_place):
        criteria = {"keyword": "logistics", "min_reviews": 5}
        n = normalize_place(no_primary_type_place)
        confidence, checks = score_lead(n, criteria)
        assert checks["category_relevance"][0] is True
        assert confidence > 0

    def test_confidence_weighted_correctly(self, fully_populated_place, default_criteria):
        n = normalize_place(fully_populated_place)
        confidence, _ = score_lead(n, default_criteria)
        assert confidence == 1.0

    def test_partial_match(self, fully_populated_place):
        n = normalize_place(fully_populated_place)
        n["phone"] = None
        criteria = {"keyword": "packaging", "min_reviews": 5}
        confidence, _ = score_lead(n, criteria)
        assert confidence == 0.75


# ---------------------------------------------------------------------------
# draft_outreach
# ---------------------------------------------------------------------------

class TestDraftOutreach:
    def test_basic_structure(self, fully_populated_place):
        n = normalize_place(fully_populated_place)
        email = draft_outreach(n, "packaging materials")
        assert email.startswith("Subject:")
        assert "Bulk supply inquiry" in email
        assert "[Your name]" in email
        assert n["name"] in email

    def test_returns_string(self, sparse_place):
        n = normalize_place(sparse_place)
        assert isinstance(draft_outreach(n, "test"), str)


# ---------------------------------------------------------------------------
# search_places — mocked HTTP
# ---------------------------------------------------------------------------

class TestSearchPlacesGoogle:
    @mock.patch("lqa_agent.requests.post")
    def test_success(self, mock_post):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"places": [{"id": "1", "displayName": {"text": "Test Co"}}]}
        mock_post.return_value = mock_resp

        places, _ = search_places("test query", api_key="key")
        assert len(places) == 1

    @mock.patch("lqa_agent.requests.post")
    def test_empty(self, mock_post):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_post.return_value = mock_resp

        places, _ = search_places("nothing", api_key="key")
        assert places == []

    @mock.patch("lqa_agent.requests.post")
    def test_401_raises(self, mock_post):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"error": {"message": "API key invalid."}}
        mock_post.return_value = mock_resp

        with pytest.raises(RuntimeError) as exc:
            search_places("q", api_key="bad")
        assert "401" in str(exc.value)

    def test_no_key_raises(self):
        with pytest.raises(RuntimeError) as exc:
            search_places("q")
        assert "No API key" in str(exc.value)


class TestSearchPlacesSerp:
    @mock.patch("lqa_agent.requests.get")
    def test_success(self, mock_get):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "local_results": [
                {"title": "Serp Co", "address": "Addr", "type": "Shop", "reviews": 10}
            ]
        }
        mock_get.return_value = mock_resp

        places, backend = search_places("test", serp_key="serp-key")
        assert len(places) == 1
        assert places[0]["displayName"]["text"] == "Serp Co"
        assert backend == "SerpAPI (Google Local)"

    @mock.patch("lqa_agent.requests.get")
    def test_empty(self, mock_get):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_get.return_value = mock_resp

        places, _ = search_places("nothing", serp_key="serp-key")
        assert places == []

    @mock.patch("lqa_agent.requests.get")
    def test_api_error(self, mock_get):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"error": "Invalid key"}
        mock_get.return_value = mock_resp

        with pytest.raises(RuntimeError) as exc:
            search_places("q", serp_key="bad")
        assert "SerpAPI" in str(exc.value)

    @mock.patch("lqa_agent.requests.get")
    def test_error_in_response_body(self, mock_get):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"error": "Invalid query"}
        mock_get.return_value = mock_resp

        with pytest.raises(RuntimeError) as exc:
            search_places("q", serp_key="bad")
        assert "SerpAPI" in str(exc.value)


class TestSearchPlacesFallback:
    @mock.patch("lqa_agent._search_google")
    @mock.patch("lqa_agent._search_serp")
    def test_falls_back_to_serp_when_google_fails(self, mock_serp, mock_google):
        mock_google.side_effect = RuntimeError("Google down")
        mock_serp.return_value = [{"displayName": {"text": "Fallback Co"}}]

        places, backend = search_places("q", api_key="gkey", serp_key="skey")
        assert len(places) == 1
        assert places[0]["displayName"]["text"] == "Fallback Co"
        assert backend == "SerpAPI (Google Local)"

    @mock.patch("lqa_agent._search_google")
    @mock.patch("lqa_agent._search_serp")
    def test_raises_when_both_fail(self, mock_serp, mock_google):
        mock_google.side_effect = RuntimeError("Google down")
        mock_serp.side_effect = RuntimeError("Serp down")

        with pytest.raises(RuntimeError) as exc:
            search_places("q", api_key="gkey", serp_key="skey")
        assert "Google" in str(exc.value)

    @mock.patch("lqa_agent._search_google")
    def test_prefers_google(self, mock_google):
        mock_google.return_value = [{"displayName": {"text": "Google Co"}}]

        places, backend = search_places("q", api_key="gkey", serp_key="skey")
        assert places[0]["displayName"]["text"] == "Google Co"
        assert backend == "Google Places API"
