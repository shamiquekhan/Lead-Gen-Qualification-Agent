"""
Streamlit UI tests for the Lead Qualification Agent (dual backend).

Uses streamlit.testing.v1.AppTest with mocked HTTP to simulate API responses
without network calls. Tests both the Google Places and SerpAPI paths.

Run: python -m pytest test_lqa_ui.py -v
"""

from unittest import mock
import os
import pytest
from streamlit.testing.v1 import AppTest

import lqa_agent


MOCK_PLACES_RESPONSE = [
    {
        "displayName": {"text": "Bhopal Packaging House"},
        "formattedAddress": "12 Industrial Area, Bhopal, MP 462001",
        "types": ["packaging_supplier", "manufacturing", "point_of_interest"],
        "primaryType": "packaging_supplier",
        "rating": 4.2,
        "userRatingCount": 34,
        "internationalPhoneNumber": "+91-755-1234567",
        "websiteUri": "https://bhopalpackaging.example.com",
        "googleMapsUri": "https://maps.google.com/?cid=111",
        "id": "ChIJ1111111111",
    },
    {
        "displayName": {"text": "MP Corrugated Solutions"},
        "formattedAddress": "45 Transport Nagar, Bhopal, MP 462010",
        "types": ["packaging_company", "manufacturing"],
        "primaryType": "packaging_company",
        "rating": 3.9,
        "userRatingCount": 8,
        "internationalPhoneNumber": "+91-755-9876543",
        "websiteUri": "https://mpcorrugated.example.com",
        "googleMapsUri": "https://maps.google.com/?cid=222",
        "id": "ChIJ2222222222",
    },
    {
        "displayName": {"text": "City Hardware Store"},
        "formattedAddress": "78 Market Road, Bhopal, MP 462002",
        "types": ["hardware_store", "store", "point_of_interest"],
        "primaryType": "hardware_store",
        "rating": 4.0,
        "userRatingCount": 56,
        "internationalPhoneNumber": "+91-755-5555555",
        "websiteUri": None,
        "googleMapsUri": "https://maps.google.com/?cid=333",
        "id": "ChIJ3333333333",
    },
    {
        "displayName": {"text": "No-Contact Services"},
        "formattedAddress": "99 Somewhere, Bhopal",
        "types": ["general_business"],
        "primaryType": None,
        "rating": None,
        "userRatingCount": 0,
        "internationalPhoneNumber": None,
        "websiteUri": None,
        "googleMapsUri": None,
        "id": "ChIJ4444444444",
    },
]

MOCK_EMPTY_RESPONSE = []


def _mock_http_response(data: list[dict], status: int = 200):
    resp = mock.MagicMock()
    resp.status_code = status
    resp.json.return_value = {"places": data}
    return resp


@pytest.fixture
def mock_google():
    """Mock the Google Places backend (requests.post)."""
    patcher = mock.patch("requests.post")
    m = patcher.start()
    m.return_value = _mock_http_response(MOCK_PLACES_RESPONSE)
    yield m
    patcher.stop()


@pytest.fixture
def mock_google_empty():
    patcher = mock.patch("requests.post")
    m = patcher.start()
    m.return_value = _mock_http_response(MOCK_EMPTY_RESPONSE)
    yield m
    patcher.stop()


@pytest.fixture
def mock_google_fails_then_serp():
    """Google fails, SerpAPI succeeds (patches module functions directly)."""
    google_patcher = mock.patch.object(lqa_agent, "_search_google")
    serp_patcher = mock.patch.object(lqa_agent, "_search_serp")

    mock_google = google_patcher.start()
    mock_google.side_effect = RuntimeError("Google Places API error (403): API not enabled")

    mock_serp = serp_patcher.start()
    mock_serp.return_value = [
        {
            "displayName": {"text": "Serp Packaging Co"},
            "formattedAddress": "Serp Rd",
            "types": ["packaging_supplier"],
            "primaryType": "packaging_supplier",
            "rating": 4.0,
            "userRatingCount": 20,
            "internationalPhoneNumber": "+1-555-0000",
            "websiteUri": "https://serppack.example.com",
            "googleMapsUri": "https://maps.google.com/?cid=999",
            "id": "ChIJ9999999999",
        }
    ]

    yield
    google_patcher.stop()
    serp_patcher.stop()


def build_app():
    at = AppTest.from_file("lead_qualification_agent.py", default_timeout=60)
    at.run()
    return at


# ---------------------------------------------------------------------------
# Page load
# ---------------------------------------------------------------------------

class TestPageLoad:
    def test_title_renders(self):
        at = build_app()
        all_text = " ".join(t.value for t in at.title) + " ".join(m.value for m in at.markdown)
        assert "Lead Qualification Agent" in all_text

    def test_google_api_key_input_present(self):
        at = build_app()
        assert any("Google Places" in t.label for t in at.text_input)

    def test_serp_api_key_input_present(self):
        at = build_app()
        assert any("SerpAPI" in t.label for t in at.text_input)

    def test_serp_key_input_present(self):
        at = build_app()
        assert any("SerpAPI" in t.label for t in at.text_input)

    def test_run_button_present(self):
        at = build_app()
        assert any("Run live search" in b.label for b in at.button)

    def test_info_message_before_run(self):
        at = build_app()
        assert any("Set your search criteria" in i.value for i in at.info)


# ---------------------------------------------------------------------------
# Successful run with Google backend
# ---------------------------------------------------------------------------

class TestSuccessfulRunGoogle:
    def _run_with_google_key(self, at):
        google_inputs = [t for t in at.text_input if "Google Places" in t.label]
        google_inputs[0].set_value("fake-google-key").run()
        run_buttons = [b for b in at.button if "Run live search" in b.label]
        run_buttons[0].click().run()

    def test_scoring_table(self, mock_google):
        at = build_app()
        self._run_with_google_key(at)
        assert len(at.dataframe) >= 1

    def test_prospecting_header(self, mock_google):
        at = build_app()
        self._run_with_google_key(at)
        assert any("Live prospecting" in s.value for s in at.subheader)

    def test_scoring_header(self, mock_google):
        at = build_app()
        self._run_with_google_key(at)
        assert any("Qualification scoring" in s.value for s in at.subheader)

    def test_shortlist_header(self, mock_google):
        at = build_app()
        self._run_with_google_key(at)
        assert any("Shortlist" in s.value for s in at.subheader)

    def test_verdict_header(self, mock_google):
        at = build_app()
        self._run_with_google_key(at)
        assert any("Verifier verdict" in s.value for s in at.subheader)

    def test_found_count(self, mock_google):
        at = build_app()
        self._run_with_google_key(at)
        assert any("4" in m.value for m in at.markdown)

    def test_scoring_table_columns(self, mock_google):
        at = build_app()
        self._run_with_google_key(at)
        cols = set(at.dataframe[0].value.columns)
        expected = {"Business", "Category", "Address", "Confidence",
                    "CatMatch", "Phone", "Website", "Established"}
        assert expected.issubset(cols)

    def test_expanders(self, mock_google):
        at = build_app()
        self._run_with_google_key(at)
        assert len(at.expander) >= 1

    def test_pass_verdict(self, mock_google):
        at = build_app()
        google_inputs = [t for t in at.text_input if "Google Places" in t.label]
        google_inputs[0].set_value("fake-google-key").run()
        leads_inputs = [n for n in at.number_input if "Leads" in n.label]
        leads_inputs[0].set_value(3).run()
        conf_sliders = [s for s in at.slider if "Minimum confidence" in s.label]
        conf_sliders[0].set_value(0.0).run()
        run_buttons = [b for b in at.button if "Run live search" in b.label]
        run_buttons[0].click().run()
        assert any("PASS" in s.value for s in at.success)


# ---------------------------------------------------------------------------
# Empty results
# ---------------------------------------------------------------------------

class TestEmptyResults:
    def test_zero_results_shows_warning(self, mock_google_empty):
        at = build_app()
        google_inputs = [t for t in at.text_input if "Google Places" in t.label]
        google_inputs[0].set_value("fake-key").run()
        run_buttons = [b for b in at.button if "Run live search" in b.label]
        run_buttons[0].click().run()
        assert any("Zero results" in w.value for w in at.warning)


# ---------------------------------------------------------------------------
# No API key
# ---------------------------------------------------------------------------

class TestNoApiKey:
    def test_no_key_shows_error(self):
        at = build_app()
        # Clear both keys
        google_inputs = [t for t in at.text_input if "Google Places" in t.label]
        google_inputs[0].set_value("").run()
        serp_inputs = [t for t in at.text_input if "SerpAPI" in t.label]
        serp_inputs[0].set_value("").run()
        run_buttons = [b for b in at.button if "Run live search" in b.label]
        run_buttons[0].click().run()
        assert any("No API key" in e.value for e in at.error)


# ---------------------------------------------------------------------------
# Partial verdict
# ---------------------------------------------------------------------------

class TestPartialVerdict:
    def test_high_bar_produces_partial(self, mock_google):
        at = build_app()
        google_inputs = [t for t in at.text_input if "Google Places" in t.label]
        google_inputs[0].set_value("fake-key").run()
        conf_sliders = [s for s in at.slider if "Minimum confidence" in s.label]
        conf_sliders[0].set_value(0.95).run()
        run_buttons = [b for b in at.button if "Run live search" in b.label]
        run_buttons[0].click().run()
        assert any("PARTIAL" in e.value for e in at.error)

    def test_partial_shows_warning(self, mock_google):
        at = build_app()
        google_inputs = [t for t in at.text_input if "Google Places" in t.label]
        google_inputs[0].set_value("fake-key").run()
        conf_sliders = [s for s in at.slider if "Minimum confidence" in s.label]
        conf_sliders[0].set_value(1.0).run()
        run_buttons = [b for b in at.button if "Run live search" in b.label]
        run_buttons[0].click().run()
        assert any("Only" in w.value for w in at.warning)


# ---------------------------------------------------------------------------
# SerpAPI fallback path
# ---------------------------------------------------------------------------

class TestSerpFallback:
    def test_serp_results_when_google_fails(self, mock_google_fails_then_serp):
        at = build_app()
        google_inputs = [t for t in at.text_input if "Google Places" in t.label]
        serp_inputs = [t for t in at.text_input if "SerpAPI" in t.label]
        google_inputs[0].set_value("bad-google-key").run()
        serp_inputs[0].set_value("fake-serp-key").run()
        run_buttons = [b for b in at.button if "Run live search" in b.label]
        run_buttons[0].click().run()
        # Should still show results via SerpAPI fallback
        assert len(at.dataframe) >= 1
        assert any("SerpAPI" in m.value for m in at.markdown)


# ---------------------------------------------------------------------------
# SerpAPI direct (no Google key)
# ---------------------------------------------------------------------------

class TestSerpDirect:
    @mock.patch("requests.get")
    def test_serp_only_key(self, mock_get):
        mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "local_results": [
                {"title": "Direct Serp Biz", "address": "Serp St", "type": "Service",
                 "reviews": 5, "rating": 4.0}
            ]
        }
        mock_get.return_value = mock_resp

        at = build_app()
        serp_inputs = [t for t in at.text_input if "SerpAPI" in t.label]
        serp_inputs[0].set_value("fake-serp-key").run()
        # Leave Google key blank, use default Serp key
        run_buttons = [b for b in at.button if "Run live search" in b.label]
        run_buttons[0].click().run()
        assert len(at.dataframe) >= 1
        assert any("SerpAPI" in m.value for m in at.markdown)


# ---------------------------------------------------------------------------
# Mock call verification
# ---------------------------------------------------------------------------

class TestMockCallVerification:
    def test_google_called_when_key_provided(self, mock_google):
        at = build_app()
        google_inputs = [t for t in at.text_input if "Google Places" in t.label]
        google_inputs[0].set_value("real-key").run()
        run_buttons = [b for b in at.button if "Run live search" in b.label]
        run_buttons[0].click().run()
        assert mock_google.call_count >= 1
        call_body = mock_google.call_args[1]["json"]
        assert "textQuery" in call_body


# ---------------------------------------------------------------------------
# Pre-flight SerpAPI key health check
# ---------------------------------------------------------------------------

def _mock_account_response(payload: dict, status: int = 200):
    resp = mock.MagicMock()
    resp.status_code = status
    resp.json.return_value = payload
    return resp


ACCOUNT_OK = {
    "account_id": "abc123",
    "account_email": "demo@serpapi.com",
    "account_status": "Active",
    "plan_name": "Freelancer Plan",
    "total_searches_left": 5958,
}


class TestPreflightCheck:
    def _click_check(self, at):
        check_buttons = [b for b in at.button if "Check SerpAPI key" in b.label]
        check_buttons[0].click().run()

    def test_check_button_present(self):
        at = build_app()
        assert any("Check SerpAPI key" in b.label for b in at.button)

    def test_no_key_warning(self):
        at = build_app()
        serp_inputs = [t for t in at.text_input if "SerpAPI" in t.label]
        serp_inputs[0].set_value("").run()
        self._click_check(at)
        assert any("No SerpAPI key to check" in w.value for w in at.warning)

    @mock.patch("requests.get")
    def test_healthy_key_shows_success(self, mock_get):
        mock_get.return_value = _mock_account_response(ACCOUNT_OK)
        at = build_app()
        serp_inputs = [t for t in at.text_input if "SerpAPI" in t.label]
        serp_inputs[0].set_value("fake-serp-key").run()
        self._click_check(at)
        assert any("searches left" in s.value for s in at.success)

    @mock.patch("requests.get")
    def test_invalid_key_shows_error(self, mock_get):
        mock_get.return_value = _mock_account_response({}, status=401)
        at = build_app()
        serp_inputs = [t for t in at.text_input if "SerpAPI" in t.label]
        serp_inputs[0].set_value("bad-key").run()
        self._click_check(at)
        assert any("Invalid" in e.value for e in at.error)

    @mock.patch("requests.get")
    def test_exhausted_key_shows_warning(self, mock_get):
        payload = dict(ACCOUNT_OK, total_searches_left=0)
        mock_get.return_value = _mock_account_response(payload)
        at = build_app()
        serp_inputs = [t for t in at.text_input if "SerpAPI" in t.label]
        serp_inputs[0].set_value("fake-serp-key").run()
        self._click_check(at)
        assert any("no searches left" in w.value for w in at.warning)

    def test_env_var_prefills_serp_key(self):
        at = AppTest.from_file("lead_qualification_agent.py", default_timeout=60)
        with mock.patch.dict(os.environ, {"SERPAPI_API_KEY": "env-secret-key"}):
            at.run()
        serp_inputs = [t for t in at.text_input if "SerpAPI" in t.label]
        assert serp_inputs[0].value == "env-secret-key"
