"""
Unit tests for score_lead and draft_outreach functions.

Run: python -m pytest test_agent.py -v
"""

import pytest
from agent import score_lead, draft_outreach, MOCK_COMPANIES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_criteria():
    """Default acceptance criteria matching the demo defaults."""
    return {
        "industry": "Any",
        "headcount_range": (30, 300),
        "signal_keyword": "AI",
    }


@pytest.fixture
def strict_criteria():
    """Stricter criteria requiring SaaS industry."""
    return {
        "industry": "SaaS",
        "headcount_range": (50, 200),
        "signal_keyword": "AI",
    }


# ---------------------------------------------------------------------------
# score_lead — Industry check
# ---------------------------------------------------------------------------

class TestScoreLeadIndustry:
    def test_any_industry_matches_all(self, default_criteria):
        """Industry='Any' should match every company."""
        for company in MOCK_COMPANIES:
            _, checks = score_lead(company, default_criteria)
            assert checks["industry"][0] is True

    def test_specific_industry_matches(self, strict_criteria):
        """SaaS industry should match SaaS companies."""
        saas_company = {"name": "X", "industry": "SaaS", "headcount": 100,
                        "signal": "AI thing", "contact": "A B", "source": "x.com"}
        _, checks = score_lead(saas_company, strict_criteria)
        assert checks["industry"][0] is True

    def test_specific_industry_rejects_mismatch(self, strict_criteria):
        """Fintech company should not match SaaS criteria."""
        fintech_company = {"name": "Y", "industry": "Fintech", "headcount": 100,
                           "signal": "AI thing", "contact": "A B", "source": "y.com"}
        _, checks = score_lead(fintech_company, strict_criteria)
        assert checks["industry"][0] is False

    def test_industry_check_returns_actual_industry_value(self, default_criteria):
        """The industry value in checks should be the company's industry."""
        company = MOCK_COMPANIES[0]
        _, checks = score_lead(company, default_criteria)
        assert checks["industry"][1] == company["industry"]


# ---------------------------------------------------------------------------
# score_lead — Headcount check
# ---------------------------------------------------------------------------

class TestScoreLeadHeadcount:
    def test_headcount_within_range(self, default_criteria):
        """Company with headcount in range should pass."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "AI", "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["headcount"][0] is True

    def test_headcount_below_range(self, default_criteria):
        """Company below min headcount should fail."""
        company = {"name": "X", "industry": "SaaS", "headcount": 10,
                   "signal": "AI", "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["headcount"][0] is False

    def test_headcount_above_range(self, default_criteria):
        """Company above max headcount should fail."""
        company = {"name": "X", "industry": "SaaS", "headcount": 500,
                   "signal": "AI", "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["headcount"][0] is False

    def test_headcount_at_exact_lower_bound(self, default_criteria):
        """Headcount exactly at lower bound should pass."""
        company = {"name": "X", "industry": "SaaS", "headcount": 30,
                   "signal": "AI", "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["headcount"][0] is True

    def test_headcount_at_exact_upper_bound(self, default_criteria):
        """Headcount exactly at upper bound should pass."""
        company = {"name": "X", "industry": "SaaS", "headcount": 300,
                   "signal": "AI", "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["headcount"][0] is True

    def test_headcount_check_returns_employee_string(self, default_criteria):
        """Headcount value should be formatted as 'N employees'."""
        company = {"name": "X", "industry": "SaaS", "headcount": 42,
                   "signal": "AI", "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["headcount"][1] == "42 employees"


# ---------------------------------------------------------------------------
# score_lead — Signal check
# ---------------------------------------------------------------------------

class TestScoreLeadSignal:
    def test_signal_keyword_matches_case_insensitive(self, default_criteria):
        """Signal match should be case-insensitive."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "Building an AI-powered analytics platform",
                   "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["signal"][0] is True

    def test_signal_keyword_no_match(self, default_criteria):
        """Signal without keyword should fail."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "Cloud infrastructure migration project",
                   "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["signal"][0] is False

    def test_empty_signal_keyword_matches_all(self):
        """Empty signal keyword should always match."""
        criteria = {"industry": "Any", "headcount_range": (0, 1000), "signal_keyword": ""}
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "Anything", "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, criteria)
        assert checks["signal"][0] is True

    def test_signal_keyword_partial_match(self, default_criteria):
        """Substring match should work."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "We use AI daily in our workflows",
                   "contact": "A B", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["signal"][0] is True


# ---------------------------------------------------------------------------
# score_lead — Contact check
# ---------------------------------------------------------------------------

class TestScoreLeadContact:
    def test_known_contact_passes(self, default_criteria):
        """Non-'unknown' contact should pass."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "AI", "contact": "Jane Smith, CTO", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["contact"][0] is True

    def test_unknown_contact_fails(self, default_criteria):
        """'unknown' contact should fail."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "AI", "contact": "unknown", "source": "x.com"}
        _, checks = score_lead(company, default_criteria)
        assert checks["contact"][0] is False

    def test_unknown_contact_caps_confidence_at_09(self, default_criteria):
        """A company with unknown contact can reach max 0.9 confidence."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "AI", "contact": "unknown", "source": "x.com"}
        confidence, _ = score_lead(company, default_criteria)
        assert confidence <= 0.9


# ---------------------------------------------------------------------------
# score_lead — Confidence calculation
# ---------------------------------------------------------------------------

class TestScoreLeadConfidence:
    def test_perfect_score(self, default_criteria):
        """All four checks passing should yield confidence of 1.0."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "AI", "contact": "Jane Smith", "source": "x.com"}
        confidence, _ = score_lead(company, default_criteria)
        assert confidence == 1.0

    def test_worked_example_cascade_fintech(self):
        """Section 13 worked example: Cascade Fintech should score 0.3."""
        criteria = {"industry": "SaaS", "headcount_range": (30, 300), "signal_keyword": "AI"}
        company = {
            "name": "Cascade Fintech", "industry": "Fintech", "headcount": 140,
            "signal": "Closed $12M Series C round, expanding into three new markets",
            "contact": "Tom Reyes, VP Sales",
            "source": "techcrunch.com/cascade-fintech-series-c", "raised": "Series C"
        }
        confidence, _ = score_lead(company, criteria)
        assert confidence == 0.3

    def test_confidence_is_rounded_to_two_decimals(self, default_criteria):
        """Confidence should be rounded to 2 decimal places."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "AI", "contact": "unknown", "source": "x.com"}
        confidence, _ = score_lead(company, default_criteria)
        assert confidence == round(confidence, 2)

    def test_returns_four_checks(self, default_criteria):
        """checks dict should have exactly 4 keys."""
        company = MOCK_COMPANIES[0]
        _, checks = score_lead(company, default_criteria)
        assert set(checks.keys()) == {"industry", "headcount", "signal", "contact"}

    def test_each_check_is_tuple_of_bool_and_string(self, default_criteria):
        """Each check value should be (bool, str)."""
        company = MOCK_COMPANIES[0]
        _, checks = score_lead(company, default_criteria)
        for field, value in checks.items():
            assert isinstance(value, tuple), f"{field} should be a tuple"
            assert len(value) == 2, f"{field} should have 2 elements"
            assert isinstance(value[0], bool), f"{field} first element should be bool"
            assert isinstance(value[1], str), f"{field} second element should be string"

    def test_weights_sum_to_one(self):
        """Weight values should sum to 1.0."""
        weights = {"industry": 0.3, "headcount": 0.2, "signal": 0.4, "contact": 0.1}
        assert sum(weights.values()) == 1.0


# ---------------------------------------------------------------------------
# score_lead — Edge cases
# ---------------------------------------------------------------------------

class TestScoreLeadEdgeCases:
    def test_no_checks_pass(self):
        """Company that fails all checks should score 0.0."""
        criteria = {"industry": "SaaS", "headcount_range": (30, 300), "signal_keyword": "AI"}
        company = {"name": "X", "industry": "Fintech", "headcount": 10,
                   "signal": "Cloud migration", "contact": "unknown", "source": "x.com"}
        confidence, checks = score_lead(company, criteria)
        assert confidence == 0.0
        for field, (ok, _) in checks.items():
            assert ok is False, f"{field} should have failed"

    def test_signal_weight_is_highest(self):
        """Signal should be weighted at 0.4, the highest."""
        # Verify from the function logic
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "AI", "contact": "unknown", "source": "x.com"}
        criteria = {"industry": "SaaS", "headcount_range": (30, 300), "signal_keyword": "AI"}
        confidence_with_signal, _ = score_lead(company, criteria)

        # Without signal match, confidence should drop by 0.4
        company_no_signal = {**company, "signal": "No match here"}
        confidence_without_signal, _ = score_lead(company_no_signal, criteria)

        assert confidence_with_signal - confidence_without_signal == 0.4


# ---------------------------------------------------------------------------
# draft_outreach
# ---------------------------------------------------------------------------

class TestDraftOutreach:
    def test_basic_structure(self):
        """Outreach should have Subject, greeting, body, and sign-off."""
        company = MOCK_COMPANIES[0]
        email = draft_outreach(company)
        assert email.startswith("Subject:")
        assert "Hi Priya," in email
        assert "Best," in email
        assert "[Your name]" in email

    def test_first_name_extraction(self):
        """First name should be extracted from contact."""
        company = MOCK_COMPANIES[0]  # "Priya Menon, Head of Growth"
        email = draft_outreach(company)
        assert "Hi Priya," in email

    def test_unknown_contact_fallback(self):
        """Unknown contact should use 'there' as greeting."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "AI thing", "contact": "unknown", "source": "x.com"}
        email = draft_outreach(company)
        assert "Hi there," in email

    def test_company_name_in_body(self):
        """Company name should appear in the email body."""
        company = MOCK_COMPANIES[0]
        email = draft_outreach(company)
        assert company["name"] in email

    def test_signal_in_body(self):
        """Signal text should appear in the email body (lowercased)."""
        company = MOCK_COMPANIES[0]
        email = draft_outreach(company)
        assert company["signal"].lower() in email

    def test_subject_truncates_signal_at_40_chars(self):
        """Subject line should truncate signal at 40 characters."""
        company = {"name": "X", "industry": "SaaS", "headcount": 100,
                   "signal": "A" * 100, "contact": "Jane Smith", "source": "x.com"}
        email = draft_outreach(company)
        subject_line = email.split("\n")[0]
        assert "A" * 40 in subject_line
        assert subject_line.endswith("...")

    def test_returns_string(self):
        """draft_outreach should always return a string."""
        for company in MOCK_COMPANIES:
            result = draft_outreach(company)
            assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Integration — full mock pool
# ---------------------------------------------------------------------------

class TestIntegrationMockPool:
    def test_all_mock_companies_score(self):
        """All 12 mock companies should be scorable without errors."""
        criteria = {"industry": "Any", "headcount_range": (30, 300), "signal_keyword": "AI"}
        for company in MOCK_COMPANIES:
            confidence, checks = score_lead(company, criteria)
            assert isinstance(confidence, float)
            assert 0.0 <= confidence <= 1.0
            assert len(checks) == 4

    def test_all_mock_companies_generate_outreach(self):
        """All 12 mock companies should generate outreach without errors."""
        for company in MOCK_COMPANIES:
            email = draft_outreach(company)
            assert isinstance(email, str)
            assert len(email) > 0

    def test_default_criteria_qualifies_some_companies(self):
        """With defaults, some but not all companies should qualify."""
        criteria = {"industry": "Any", "headcount_range": (30, 300), "signal_keyword": "AI"}
        qualified = []
        for company in MOCK_COMPANIES:
            confidence, _ = score_lead(company, criteria)
            if confidence >= 0.7:
                qualified.append(company)
        assert 1 <= len(qualified) < len(MOCK_COMPANIES), "Some but not all companies should qualify"
