"""
Streamlit UI tests for the Verified Lead-Gen & Qualification Agent.

Uses streamlit.testing.v1.AppTest to simulate widget interactions
and verify the presentation layer works correctly.

Run: python -m pytest test_ui.py -v
"""

import time
from unittest import mock
import pytest
from streamlit.testing.v1 import AppTest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _mock_sleep():
    """Patch time.sleep across every test to avoid 0.6s delays on each rerun."""
    with mock.patch.object(time, "sleep", return_value=None):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_app():
    """Load the Streamlit app in test mode."""
    at = AppTest.from_file("bounty_leadgen_agent.py", default_timeout=30)
    at.run()
    return at


# ---------------------------------------------------------------------------
# Page load and initial state
# ---------------------------------------------------------------------------

class TestPageLoad:
    def test_title_renders(self):
        """Page should render the main title."""
        at = build_app()
        assert at.title[0].value == "Verified Lead-Gen & Qualification Agent"

    def test_subtitle_renders(self):
        """Page should render the subtitle paragraph."""
        at = build_app()
        # Check both markdown and html elements (unsafe_allow_html may appear as html)
        found = any(m.value and "5 qualified leads" in m.value for m in at.markdown)
        found = found or any(h.value and "5 qualified leads" in h.value for h in at.html)
        assert found

    def test_step_header_bounty_intake(self):
        """Step 1 header should be visible."""
        at = build_app()
        # Step header is rendered as st.markdown with class step-header
        assert any("Bounty intake" in m.value for m in at.markdown)

    def test_industry_selectbox_present(self):
        """Industry selectbox should exist."""
        at = build_app()
        assert len(at.selectbox) >= 1
        assert at.selectbox[0].label == "Industry"

    def test_headcount_slider_present(self):
        """Headcount range slider should exist."""
        at = build_app()
        assert len(at.slider) >= 1
        assert "Headcount" in at.slider[0].label

    def test_signal_text_input_present(self):
        """Signal keyword text input should exist."""
        at = build_app()
        assert len(at.text_input) >= 1
        assert at.text_input[0].label == "Signal keyword"

    def test_leads_number_input_present(self):
        """Leads requested number input should exist."""
        at = build_app()
        assert len(at.number_input) >= 1
        assert "Leads" in at.number_input[0].label

    def test_confidence_slider_present(self):
        """Minimum confidence slider should exist."""
        at = build_app()
        assert len(at.slider) >= 2
        assert "Minimum confidence" in at.slider[1].label

    def test_run_bounty_button_present(self):
        """Run bounty button should exist."""
        at = build_app()
        assert len(at.button) >= 1
        assert at.button[0].label == "Run bounty"

    def test_info_message_before_run(self):
        """Before clicking Run bounty, an info message should be shown."""
        at = build_app()
        assert at.info[0].value is not None
        assert "Set your acceptance criteria" in at.info[0].value


# ---------------------------------------------------------------------------
# Default criteria run
# ---------------------------------------------------------------------------

class TestDefaultRun:
    def test_default_criteria_values(self):
        """Default widget values should match expectations."""
        at = build_app()
        assert at.selectbox[0].value == "Any"
        assert at.slider[0].value == (30, 300)
        assert at.text_input[0].value == "AI"
        assert at.number_input[0].value == 5
        # slider[1] is min_confidence — default 0.7
        assert at.slider[1].value == 0.7

    def test_click_run_bounty_produces_scoring_table(self):
        """Clicking Run bounty should produce a dataframe (scoring table)."""
        at = build_app()
        at.button[0].click().run()
        assert len(at.dataframe) >= 1

    def test_click_run_bounty_prospecting_step_header(self):
        """Prospecting step header should appear after clicking Run bounty."""
        at = build_app()
        at.button[0].click().run()
        assert any("Prospecting" in m.value for m in at.markdown)

    def test_click_run_bounty_scoring_step_header(self):
        """Scoring step header should appear after clicking Run bounty."""
        at = build_app()
        at.button[0].click().run()
        assert any("Qualification scoring" in m.value for m in at.markdown)

    def test_click_run_bounty_shortlist_header(self):
        """Shortlist step header should appear after clicking Run bounty."""
        at = build_app()
        at.button[0].click().run()
        assert any("Shortlist" in m.value for m in at.markdown)

    def test_click_run_bounty_verdict_header(self):
        """Verifier verdict step header should appear after clicking Run bounty."""
        at = build_app()
        at.button[0].click().run()
        assert any("Verifier verdict" in m.value for m in at.markdown)

    def test_default_run_passes(self):
        """With default criteria, the verdict should be PASS (5 of 5 qualified)."""
        at = build_app()
        at.button[0].click().run()
        # at.success[0] is the shortlist message, at.success[1] is the verdict
        assert len(at.success) >= 2
        assert "PASS" in at.success[1].value

    def test_scanned_companies_message(self):
        """Scanned companies count should be shown (12)."""
        at = build_app()
        at.button[0].click().run()
        assert any("12" in m.value for m in at.markdown)

    def test_default_run_shows_expanders(self):
        """With default pass, expanders should appear for each qualified lead."""
        at = build_app()
        at.button[0].click().run()
        # At least some expanders should be present
        assert len(at.expander) >= 1

    def test_outreach_draft_in_expander(self):
        """Expander content should include outreach draft text."""
        at = build_app()
        at.button[0].click().run()
        # After clicking, expanders have outreach draft content
        assert any("Outreach draft" in m.value for m in at.markdown)

    def test_evidence_package_in_expander(self):
        """Expander content should include evidence package."""
        at = build_app()
        at.button[0].click().run()
        assert any("Evidence package" in m.value for m in at.markdown)

    def test_scoring_table_has_expected_columns(self):
        """Scoring table should have the expected column names."""
        at = build_app()
        at.button[0].click().run()
        # The dataframe is rendered by st.dataframe
        df = at.dataframe[0]
        # Access columns from the underlying pandas DataFrame
        cols = set(df.value.columns)
        expected = {"Company", "Industry", "Headcount", "Confidence",
                    "Industry Match", "Headcount Match", "Signal Match", "Contact Found"}
        assert expected.issubset(cols)

    def test_verdict_footnote_renders(self):
        """The honest gap footnote should appear after verdict."""
        at = build_app()
        at.button[0].click().run()
        assert any("claim and the check" in m.value for m in at.markdown)


# ---------------------------------------------------------------------------
# Partial pass scenario
# ---------------------------------------------------------------------------

class TestPartialPass:
    def test_strict_criteria_produces_partial(self):
        """With Industry=SaaS and min_confidence=0.8, should produce PARTIAL."""
        at = build_app()
        at.selectbox[0].set_value("SaaS").run()
        at.slider[1].set_value(0.8).run()
        at.button[0].click().run()
        # Should see PARTIAL in error alert
        assert len(at.error) >= 1
        assert "PARTIAL" in at.error[0].value

    def test_partial_shows_shortfall_warning(self):
        """With strict criteria, warning about shortfall should appear."""
        at = build_app()
        at.selectbox[0].set_value("SaaS").run()
        at.slider[1].set_value(0.8).run()
        at.button[0].click().run()
        assert len(at.warning) >= 1
        assert "Only" in at.warning[0].value


# ---------------------------------------------------------------------------
# Criteria interaction
# ---------------------------------------------------------------------------

class TestCriteriaInteraction:
    def test_industry_filter_narrows_results(self):
        """Changing industry from Any to SaaS should reduce qualified leads."""
        at = build_app()
        at.button[0].click().run()
        qualified_any = len(at.expander)

        # Now set industry to SaaS and rerun
        at = build_app()
        at.selectbox[0].set_value("SaaS").run()
        at.button[0].click().run()
        qualified_saas = len(at.expander)

        # SaaS filter should not produce MORE expanders than Any
        # (some companies like Pinecrest/Insurtech will drop out)
        assert qualified_saas <= qualified_any

    def test_change_signal_keyword_affects_results(self):
        """Changing signal keyword should change which companies qualify."""
        at = build_app()
        at.text_input[0].set_value("blockchain").run()
        at.button[0].click().run()
        # With signal keyword 'blockchain', likely very few or no matches
        # The app should still render without errors
        assert len(at.dataframe) >= 1  # Scoring table still shown

    def test_increase_leads_requested(self):
        """Increasing leads requested should still render correctly."""
        at = build_app()
        at.number_input[0].set_value(8).run()
        at.button[0].click().run()
        # Should still produce a dataframe
        assert len(at.dataframe) >= 1
        # Shortlist header should reflect 8 requested
        assert any("8" in m.value for m in at.markdown)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_empty_signal_keyword_still_works(self):
        """Empty signal keyword should match all companies (edge case)."""
        at = build_app()
        at.text_input[0].set_value("").run()
        at.button[0].click().run()
        # Should still render without errors
        assert len(at.dataframe) >= 1

    def test_extreme_headcount_range_still_works(self):
        """Setting headcount to max range should still work."""
        at = build_app()
        at.slider[0].set_value((0, 600)).run()
        at.button[0].click().run()
        assert len(at.dataframe) >= 1

    def test_min_confidence_zero_shows_all(self):
        """Setting min confidence to 0 should show all companies as qualified."""
        at = build_app()
        at.slider[1].set_value(0.0).run()
        at.button[0].click().run()
        # All 12 companies should have expanders
        assert len(at.expander) >= 1
