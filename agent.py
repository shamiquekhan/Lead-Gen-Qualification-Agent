"""
Core agent logic — scoring, outreach, and mock data.

Extracted from bounty_leadgen_agent.py so the pure functions can be
imported and tested independently of the Streamlit UI layer.
"""

# ---------------------------------------------------------------------------
# Mock candidate pool. In production this comes from a prospecting agent
# (web search / Apollo / Crunchbase / LinkedIn). Each record already carries
# the "evidence" a verifier would need — source + the raw signal text —
# because evidence has to be collected at discovery time, not invented later.
# ---------------------------------------------------------------------------
MOCK_COMPANIES = [
    dict(name="Northwind Analytics", industry="SaaS", headcount=85,
         signal="Posted 3 AI/ML engineering roles in the last 30 days",
         contact="Priya Menon, Head of Growth",
         source="northwindanalytics.com/careers", raised=None),
    dict(name="Cascade Fintech", industry="Fintech", headcount=140,
         signal="Closed $12M Series C round, expanding into three new markets",
         contact="Tom Reyes, VP Sales",
         source="techcrunch.com/cascade-fintech-series-c", raised="Series C"),
    dict(name="Loomis Robotics", industry="Industrial Automation", headcount=42,
         signal="Hiring a Director of Enterprise Sales",
         contact="Anika Shah, Founder/CEO",
         source="linkedin.com/company/loomis-robotics/jobs", raised="Seed"),
    dict(name="Verdant Health", industry="Healthtech", headcount=310,
         signal="Migrated infra to AWS, blog post on scaling data pipeline",
         contact="Marcus Webb, VP Engineering",
         source="verdanthealth.io/blog/scaling-data", raised="Series B"),
    dict(name="Rally Commerce", industry="SaaS", headcount=63,
         signal="Job post mentions 'implementing outbound AI agents'",
         contact="Devon Choi, Head of RevOps",
         source="rallycommerce.com/careers/revops-lead", raised="Seed"),
    dict(name="Solstice Legal Tech", industry="Legal Tech", headcount=28,
         signal="Recently launched a contract-review product",
         contact="Elena Voss, Co-founder",
         source="solsticelegal.com/product-launch", raised="Pre-seed"),
    dict(name="Ferro Materials Co", industry="Manufacturing", headcount=510,
         signal="RFP posted for supply chain software vendors",
         contact="Hassan Ali, Procurement Director",
         source="ferromaterials.com/vendor-rfp", raised=None),
    dict(name="Ember Analytics", industry="SaaS", headcount=97,
         signal="Hiring for 'AI Sales Development Rep' — 2 open reqs",
         contact="Grace Lin, CRO",
         source="ember.io/careers/sdr-ai", raised="Series A"),
    dict(name="Pinecrest Insurance", industry="Insurtech", headcount=225,
         signal="Announced partnership to automate claims triage",
         contact="Robert Kane, VP Operations",
         source="pinecrestinsurance.com/news/claims-automation", raised="Series B"),
    dict(name="Voxa Media", industry="Media/AdTech", headcount=18,
         signal="Small team, no recent hiring or funding signal",
         contact="Sam Torres, Founder",
         source="voxamedia.com/about", raised=None),
    dict(name="Marlowe Consulting", industry="Professional Services", headcount=12,
         signal="No digital signals found in last 90 days",
         contact="unknown",
         source="n/a", raised=None),
    dict(name="Atlas SaaS Group", industry="SaaS", headcount=72,
         signal="Job post: 'Own our AI-driven outbound motion end to end'",
         contact="Nina Park, Head of Sales",
         source="atlassaas.com/careers/outbound-lead", raised="Series A"),
]

# ---------------------------------------------------------------------------
# Scoring — each acceptance-criteria field is checked independently and
# contributes to confidence. This is what makes the score auditable: a
# verifier can look at any lead and see exactly which field passed and why,
# instead of trusting a single opaque "relevance" number.
# ---------------------------------------------------------------------------
def score_lead(company, criteria):
    checks = {}

    industry_match = criteria["industry"] == "Any" or company["industry"] == criteria["industry"]
    checks["industry"] = (industry_match, company["industry"])

    lo, hi = criteria["headcount_range"]
    hc_match = lo <= company["headcount"] <= hi
    checks["headcount"] = (hc_match, f"{company['headcount']} employees")

    signal_kw = criteria["signal_keyword"].lower()
    signal_match = signal_kw in company["signal"].lower() if signal_kw else True
    checks["signal"] = (signal_match, company["signal"])

    has_contact = company["contact"] != "unknown"
    checks["contact"] = (has_contact, company["contact"])

    weights = {"industry": 0.3, "headcount": 0.2, "signal": 0.4, "contact": 0.1}
    confidence = sum(weights[k] for k, (ok, _) in checks.items() if ok)
    return round(confidence, 2), checks


def draft_outreach(company):
    first_name = company["contact"].split()[0] if company["contact"] != "unknown" else "there"
    return (
        f"Subject: {company['signal'][:40]}...\n\n"
        f"Hi {first_name},\n\n"
        f"Noticed {company['name']} {company['signal'].lower()}. "
        f"Wanted to flag something relevant to that — worth a quick call this week?\n\n"
        f"Best,\n[Your name]"
    )
