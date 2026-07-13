"""
Verified Lead-Gen & Qualification Agent — Bounty demo
-------------------------------------------------------
Simulates how an outcome-based bounty for "5 qualified leads" would run on
Bounty's marketplace model: task posted as acceptance criteria -> agent
prospects and scores candidates -> every claimed match ships with an
evidence trail -> an independent verifier checks the evidence against the
criteria before payout is recommended.

Mock data only (no live web calls) so this runs offline, deterministically,
on a call. Swap `MOCK_COMPANIES` for a real search/enrichment call later —
the scoring, evidence, and verification layers don't change.

Run: streamlit run bounty_leadgen_agent.py
"""

import time
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bounty — Verified Lead-Gen Agent", layout="wide")

# ---------------------------------------------------------------------------
# Neumorphism CSS — soft UI with embossed elements, multi-layer shadows,
# monochromatic palette, and tactile press effects.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700&display=swap');

    :root {
        --neu-bg: #e4e9f2;
        --neu-card: #e4e9f2;
        --neu-shadow-dark: #c8ced8;
        --neu-shadow-light: #ffffff;
        --neu-text: #1a1a2e;
        --neu-text-muted: #5a5a7a;
        --neu-primary: #5b6abf;
        --neu-primary-hover: #4c5aad;
        --neu-primary-text: #ffffff;
        --neu-success: #3d8b5f;
        --neu-warning: #c78c3a;
        --neu-error: #c45050;
        --neu-radius: 16px;
        --neu-radius-sm: 12px;
        --neu-radius-xs: 8px;
        --neu-radius-pill: 50px;
        --neu-font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Global Reset ── */
    #root, .stApp, .main > div {
        background: var(--neu-bg);
        font-family: var(--neu-font);
        color: var(--neu-text);
    }
    .stApp {
        background: var(--neu-bg);
    }

    /* ── Section containers (neumorphic card effect) ── */
    .stApp section[data-testid="stVerticalBlock"] > div {
        border-radius: var(--neu-radius-sm);
        padding: 0.25rem 0;
        transition: box-shadow 0.2s ease;
    }

    /* ── Typography ── */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stText,
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: var(--neu-font) !important;
        color: var(--neu-text);
        line-height: 1.6;
    }
    h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em;
        color: var(--neu-text) !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 1px 2px rgba(255,255,255,0.8);
    }
    h2, .stSubheader {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
        color: var(--neu-text) !important;
        margin-top: 0.5rem !important;
    }
    p {
        font-size: 0.95rem !important;
        line-height: 1.7 !important;
        color: var(--neu-text) !important;
    }

    /* Step section headers (1 · Bounty intake, 2 · Prospecting, etc.) */
    .step-header {
        background: var(--neu-card);
        border-radius: var(--neu-radius-sm);
        padding: 0.75rem 1rem;
        margin: 1.5rem 0 1rem 0;
        box-shadow:
            6px 6px 14px var(--neu-shadow-dark),
            -6px -6px 14px var(--neu-shadow-light);
        font-family: var(--neu-font) !important;
        font-weight: 600 !important;
        font-size: 1.15rem !important;
        color: var(--neu-text) !important;
        border-left: 4px solid var(--neu-primary);
    }

    /* ── Dividers ── */
    hr, .stDivider {
        border: none !important;
        height: 2px !important;
        background: transparent !important;
        box-shadow: 0 2px 4px var(--neu-shadow-dark), 0 -1px 2px var(--neu-shadow-light) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Neumorphic Card ── */
    .neu-card {
        background: var(--neu-card);
        border-radius: var(--neu-radius);
        padding: 1.5rem;
        box-shadow:
            8px 8px 16px var(--neu-shadow-dark),
            -8px -8px 16px var(--neu-shadow-light);
        margin-bottom: 1.5rem;
        border: none;
    }
    .neu-card-emboss {
        background: var(--neu-card);
        border-radius: var(--neu-radius);
        padding: 1.5rem;
        box-shadow:
            inset 3px 3px 8px var(--neu-shadow-dark),
            inset -3px -3px 8px var(--neu-shadow-light);
        margin-bottom: 1.5rem;
        border: none;
    }

    /* ── Columns containers ── */
    div[data-testid="column"] {
        border-radius: var(--neu-radius-sm);
        padding: 0.25rem;
    }

    /* ── Widget Labels ── */
    .stSelectbox label, .stSlider label, .stTextInput label,
    .stNumberInput label, p, .stMarkdown p {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: var(--neu-text) !important;
        letter-spacing: 0.02em;
        margin-bottom: 0.4rem !important;
    }

    /* ── Buttons ── */
    div.stButton > button {
        font-family: var(--neu-font) !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.02em;
        background: var(--neu-card) !important;
        color: var(--neu-primary) !important;
        border: none !important;
        border-radius: var(--neu-radius-pill) !important;
        padding: 0.75rem 2.5rem !important;
        box-shadow:
            6px 6px 12px var(--neu-shadow-dark),
            -6px -6px 12px var(--neu-shadow-light) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        min-height: 3.2rem;
        min-width: 10rem;
    }
    div.stButton > button:hover {
        box-shadow:
            4px 4px 8px var(--neu-shadow-dark),
            -4px -4px 8px var(--neu-shadow-light) !important;
        transform: translateY(-1px);
        color: var(--neu-primary-hover) !important;
    }
    div.stButton > button:active {
        box-shadow:
            inset 4px 4px 8px var(--neu-shadow-dark),
            inset -4px -4px 8px var(--neu-shadow-light) !important;
        transform: translateY(1px);
        color: var(--neu-primary-hover) !important;
    }
    /* Primary button variant */
    div.stButton > button[kind="primary"],
    div.stButton > button[kind="primaryFormSubmit"] {
        background: var(--neu-primary) !important;
        color: var(--neu-primary-text) !important;
        box-shadow:
            6px 6px 12px var(--neu-shadow-dark),
            -6px -6px 12px var(--neu-shadow-light) !important;
    }
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button[kind="primaryFormSubmit"]:hover {
        background: var(--neu-primary-hover) !important;
        box-shadow:
            4px 4px 8px var(--neu-shadow-dark),
            -4px -4px 8px var(--neu-shadow-light) !important;
    }
    div.stButton > button[kind="primary"]:active,
    div.stButton > button[kind="primaryFormSubmit"]:active {
        box-shadow:
            inset 4px 4px 8px rgba(0,0,0,0.25),
            inset -4px -4px 8px rgba(255,255,255,0.1) !important;
        background: var(--neu-primary-hover) !important;
    }

    /* ── Selectbox ── */
    div[data-testid="stSelectbox"] > div > div {
        background: var(--neu-card) !important;
        border: none !important;
        border-radius: var(--neu-radius-sm) !important;
        box-shadow:
            inset 3px 3px 7px var(--neu-shadow-dark),
            inset -3px -3px 7px var(--neu-shadow-light) !important;
        padding: 0.25rem 0.5rem !important;
        transition: box-shadow 0.15s ease !important;
    }
    div[data-testid="stSelectbox"] > div > div:focus-within {
        box-shadow:
            inset 4px 4px 10px var(--neu-shadow-dark),
            inset -4px -4px 10px var(--neu-shadow-light) !important;
    }
    div[data-testid="stSelectbox"] select {
        background: transparent !important;
        color: var(--neu-text) !important;
        font-family: var(--neu-font) !important;
        font-size: 0.9rem !important;
    }

    /* ── Text Input ── */
    div[data-testid="stTextInput"] > div > div {
        background: var(--neu-card) !important;
        border: none !important;
        border-radius: var(--neu-radius-sm) !important;
        box-shadow:
            inset 3px 3px 7px var(--neu-shadow-dark),
            inset -3px -3px 7px var(--neu-shadow-light) !important;
        transition: box-shadow 0.15s ease !important;
    }
    div[data-testid="stTextInput"] > div > div:focus-within {
        box-shadow:
            inset 4px 4px 10px var(--neu-shadow-dark),
            inset -4px -4px 10px var(--neu-shadow-light) !important;
    }
    div[data-testid="stTextInput"] input {
        background: transparent !important;
        color: var(--neu-text) !important;
        font-family: var(--neu-font) !important;
        font-size: 0.9rem !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* ── Number Input ── */
    div[data-testid="stNumberInput"] > div > div {
        background: var(--neu-card) !important;
        border: none !important;
        border-radius: var(--neu-radius-sm) !important;
        box-shadow:
            inset 3px 3px 7px var(--neu-shadow-dark),
            inset -3px -3px 7px var(--neu-shadow-light) !important;
        transition: box-shadow 0.15s ease !important;
    }
    div[data-testid="stNumberInput"] input {
        background: transparent !important;
        color: var(--neu-text) !important;
        font-family: var(--neu-font) !important;
        font-size: 0.9rem !important;
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stNumberInput"] button {
        background: var(--neu-card) !important;
        border: none !important;
        border-radius: 50% !important;
        box-shadow:
            2px 2px 5px var(--neu-shadow-dark),
            -2px -2px 5px var(--neu-shadow-light) !important;
        color: var(--neu-text) !important;
        min-width: 2rem !important;
        min-height: 2rem !important;
        transition: all 0.12s ease !important;
    }
    div[data-testid="stNumberInput"] button:active {
        box-shadow:
            inset 2px 2px 5px var(--neu-shadow-dark),
            inset -2px -2px 5px var(--neu-shadow-light) !important;
    }

    /* ── Slider ── */
    div[data-testid="stSlider"] {
        padding: 0.75rem 0.25rem !important;
    }
    div[data-testid="stSlider"] > div {
        background: var(--neu-card) !important;
        border-radius: var(--neu-radius-sm) !important;
        padding: 0.75rem 0.75rem 0.25rem !important;
        box-shadow:
            inset 2px 2px 6px var(--neu-shadow-dark),
            inset -2px -2px 6px var(--neu-shadow-light) !important;
    }
    div[data-testid="stSlider"] div[data-baseweb="slider"] {
        background: transparent !important;
    }
    /* Slider thumb */
    div[data-testid="stSlider"] div[role="slider"] {
        background: var(--neu-primary) !important;
        border: 3px solid var(--neu-card) !important;
        box-shadow:
            2px 2px 6px var(--neu-shadow-dark),
            -2px -2px 6px var(--neu-shadow-light) !important;
        transition: all 0.12s ease !important;
    }
    div[data-testid="stSlider"] div[role="slider"]:active {
        box-shadow:
            inset 2px 2px 4px rgba(0,0,0,0.2),
            inset -2px -2px 4px rgba(255,255,255,0.1) !important;
        transform: scale(0.95);
    }

    /* ── Dataframe / Table ── */
    div[data-testid="stDataFrame"] {
        border-radius: var(--neu-radius-sm) !important;
        overflow: hidden !important;
        box-shadow:
            6px 6px 14px var(--neu-shadow-dark),
            -6px -6px 14px var(--neu-shadow-light) !important;
        background: var(--neu-card) !important;
        padding: 0.25rem !important;
    }
    div[data-testid="stDataFrame"] table {
        font-family: var(--neu-font) !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }
    div[data-testid="stDataFrame"] thead tr th {
        background: var(--neu-card) !important;
        color: var(--neu-text) !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        padding: 0.75rem 0.6rem !important;
        border: none !important;
        box-shadow:
            inset 0 -2px 4px var(--neu-shadow-dark),
            inset 0 1px 2px var(--neu-shadow-light) !important;
    }
    div[data-testid="stDataFrame"] tbody tr td {
        background: var(--neu-card) !important;
        color: var(--neu-text) !important;
        font-size: 0.85rem !important;
        padding: 0.6rem !important;
        border: none !important;
        border-bottom: 1px solid transparent !important;
        box-shadow: 0 1px 2px var(--neu-shadow-dark) !important;
    }
    div[data-testid="stDataFrame"] tbody tr:last-child td {
        box-shadow: none !important;
    }
    div[data-testid="stDataFrame"] tbody tr:hover td {
        filter: brightness(0.97) !important;
        cursor: default !important;
    }

    /* ── Expander ── */
    div[data-testid="stExpander"] {
        border: none !important;
        border-radius: var(--neu-radius-sm) !important;
        background: var(--neu-card) !important;
        box-shadow:
            4px 4px 10px var(--neu-shadow-dark),
            -4px -4px 10px var(--neu-shadow-light) !important;
        margin-bottom: 1rem !important;
        overflow: hidden !important;
        transition: box-shadow 0.2s ease !important;
    }
    div[data-testid="stExpander"]:hover {
        box-shadow:
            5px 5px 12px var(--neu-shadow-dark),
            -5px -5px 12px var(--neu-shadow-light) !important;
    }
    div[data-testid="stExpander"] summary {
        font-family: var(--neu-font) !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        color: var(--neu-text) !important;
        padding: 0.75rem 1rem !important;
        border-radius: var(--neu-radius-sm) !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        user-select: none !important;
    }
    div[data-testid="stExpander"] summary:hover {
        filter: brightness(0.97) !important;
    }
    div[data-testid="stExpander"] div[data-testid="stExpanderContent"] {
        background: var(--neu-card) !important;
        border-radius: 0 0 var(--neu-radius-sm) var(--neu-radius-sm) !important;
        padding: 0.5rem 1rem 1rem !important;
        box-shadow:
            inset 0 3px 6px var(--neu-shadow-dark),
            inset 0 -2px 4px var(--neu-shadow-light) !important;
    }

    /* ── Alerts / Messages ── */
    div[data-testid="stAlertContainer"] {
        border: none !important;
        border-radius: var(--neu-radius-sm) !important;
        padding: 0 !important;
        font-family: var(--neu-font) !important;
        margin-bottom: 1rem !important;
    }
    div[data-testid="stAlertContainer"] > div {
        border: none !important;
        border-radius: var(--neu-radius-sm) !important;
        padding: 1rem 1.25rem !important;
        font-family: var(--neu-font) !important;
        font-size: 0.9rem !important;
        background: var(--neu-card) !important;
    }
    /* Success alert */
    div[data-testid="stAlertContainer"] .stAlert {
        background: var(--neu-card) !important;
        border-left: 4px solid var(--neu-success) !important;
        box-shadow:
            inset 2px 2px 6px rgba(76, 175, 125, 0.15),
            inset -2px -2px 6px rgba(255,255,255,0.5) !important;
        border-radius: var(--neu-radius-sm) !important;
    }
    div[data-testid="stAlertContainer"] .stAlert > div {
        background: transparent !important;
    }
    /* Error alert */
    div[data-testid="stAlertContainer"] .st-bd {
        background: var(--neu-card) !important;
        border-left: 4px solid var(--neu-error) !important;
        box-shadow:
            inset 2px 2px 6px rgba(224, 112, 112, 0.15),
            inset -2px -2px 6px rgba(255,255,255,0.5) !important;
        border-radius: var(--neu-radius-sm) !important;
    }
    /* Warning alert */
    div[data-testid="stAlertContainer"] .st-cb {
        background: var(--neu-card) !important;
        border-left: 4px solid var(--neu-warning) !important;
        box-shadow:
            inset 2px 2px 6px rgba(232, 168, 76, 0.15),
            inset -2px -2px 6px rgba(255,255,255,0.5) !important;
        border-radius: var(--neu-radius-sm) !important;
    }
    /* Info alert */
    div[data-testid="stAlertContainer"] .st-cs {
        background: var(--neu-card) !important;
        border-left: 4px solid var(--neu-primary) !important;
        box-shadow:
            inset 2px 2px 6px rgba(91, 106, 191, 0.15),
            inset -2px -2px 6px rgba(255,255,255,0.5) !important;
        border-radius: var(--neu-radius-sm) !important;
    }
    /* Alert text */
    div[data-testid="stAlertContainer"] .stMarkdown p {
        color: var(--neu-text) !important;
        font-weight: 500 !important;
    }

    /* ── Spinner ── */
    div.stSpinner {
        border-radius: var(--neu-radius-sm) !important;
        padding: 1rem !important;
        background: var(--neu-card) !important;
        box-shadow:
            inset 3px 3px 8px var(--neu-shadow-dark),
            inset -3px -3px 8px var(--neu-shadow-light) !important;
    }
    div.stSpinner > div {
        border-top-color: var(--neu-primary) !important;
    }

    /* ── Caption / small text ── */
    .stCaption, .stMarkdown small, .stMarkdown .caption {
        color: var(--neu-text-muted) !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
    }

    /* ── Scrollbar styling ── */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--neu-bg);
        border-radius: 4px;
        box-shadow: inset 2px 2px 4px var(--neu-shadow-dark);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--neu-shadow-dark);
        border-radius: 4px;
        box-shadow: inset 1px 1px 2px var(--neu-shadow-light);
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--neu-text-muted);
    }

    /* ── Code blocks ── */
    .stCodeBlock {
        border-radius: var(--neu-radius-sm) !important;
        background: var(--neu-card) !important;
        box-shadow:
            inset 3px 3px 8px var(--neu-shadow-dark),
            inset -3px -3px 8px var(--neu-shadow-light) !important;
        padding: 0.25rem !important;
    }
    .stCodeBlock code {
        background: transparent !important;
        color: var(--neu-text) !important;
        font-size: 0.85rem !important;
    }

    /* ── Tooltip / Help text ── */
    div[data-testid="stTooltipIcon"] {
        color: var(--neu-text-muted) !important;
        opacity: 0.7;
    }

    /* ── Info callout (before run) ── */
    .stAlertContainer .stAlert {
        background: var(--neu-card) !important;
        box-shadow:
            inset 3px 3px 8px var(--neu-shadow-dark),
            inset -3px -3px 8px var(--neu-shadow-light) !important;
        border-left: 4px solid var(--neu-primary) !important;
        border-radius: var(--neu-radius-sm) !important;
    }
</style>
""", unsafe_allow_html=True)

from agent import MOCK_COMPANIES, score_lead, draft_outreach


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("Verified Lead-Gen & Qualification Agent")
st.markdown(
    '<p style="color: var(--neu-text-muted); font-size: 0.95rem; margin-top: -0.5rem; '
    'font-weight: 400;">'
    'A bounty for <strong>5 qualified leads</strong> only pays out on a verified outcome — '
    'not on an agent\'s claim. This demo shows the full loop: '
    'acceptance criteria → prospecting → auditable scoring → evidence → verdict.'
    '</p>',
    unsafe_allow_html=True,
)

st.divider()

# --- Step 1: Bounty intake ---
st.markdown(
    '<div class="step-header">1 · Bounty intake — acceptance criteria</div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    industry = st.selectbox(
        "Industry",
        ["Any", "SaaS", "Fintech", "Healthtech",
         "Legal Tech", "Insurtech", "Industrial Automation",
         "Manufacturing", "Media/AdTech", "Professional Services"],
        help="Select target industry, or 'Any' to accept all industries.",
    )
with c2:
    hc_range = st.slider(
        "Headcount range",
        0, 600, (30, 300),
        help="Target company size range.",
    )
with c3:
    signal_kw = st.text_input(
        "Signal keyword",
        value="AI",
        help="Keyword to match in job posts, news, or funding announcements.",
    )
with c4:
    quantity = st.number_input(
        "Leads requested",
        min_value=1, max_value=10, value=5,
        help="Number of qualified leads the bounty requires.",
    )

min_confidence = st.slider(
    "Minimum confidence to count as 'qualified'",
    0.0, 1.0, 0.7, 0.05,
    help="Leads below this confidence threshold are excluded from the shortlist.",
)

criteria = dict(industry=industry, headcount_range=hc_range, signal_keyword=signal_kw)

col_btn, col_spacer = st.columns([1, 3])
with col_btn:
    run = st.button("Run bounty", type="primary", use_container_width=True)

if run:
    # --- Step 2: Prospecting ---
    st.markdown(
        '<div class="step-header">2 · Prospecting</div>',
        unsafe_allow_html=True,
    )
    with st.spinner("Agent scanning candidate pool..."):
        time.sleep(0.6)
    st.markdown(
        f'Scanned **{len(MOCK_COMPANIES)}** candidate companies.\n\n'
        f'<div style="font-size: 0.85rem; color: var(--neu-text-muted); margin-top: 0.25rem;">'
        f'Source: In-memory mock pool — replace with real prospecting API in production.</div>',
        unsafe_allow_html=True,
    )

    # --- Step 3: Qualification scoring ---
    st.markdown(
        '<div class="step-header">3 · Qualification scoring (auditable, per-field)</div>',
        unsafe_allow_html=True,
    )
    scored = []
    for company in MOCK_COMPANIES:
        confidence, checks = score_lead(company, criteria)
        scored.append((company, confidence, checks))
    scored.sort(key=lambda x: x[1], reverse=True)

    score_table = pd.DataFrame([
        {
            "Company": c["name"],
            "Industry": c["industry"],
            "Headcount": c["headcount"],
            "Confidence": conf,
            "Industry Match": "Yes" if checks["industry"][0] else "No",
            "Headcount Match": "Yes" if checks["headcount"][0] else "No",
            "Signal Match": "Yes" if checks["signal"][0] else "No",
            "Contact Found": "Yes" if checks["contact"][0] else "No",
        }
        for c, conf, checks in scored
    ])
    st.dataframe(score_table, use_container_width=True, hide_index=True)
    st.markdown(
        '<div style="font-size: 0.8rem; color: var(--neu-text-muted); text-align: right; '
        'padding: 0.25rem 0.5rem;">'
        'All 12 candidates shown, sorted by confidence — rejected candidates are visible too.'
        '</div>',
        unsafe_allow_html=True,
    )

    qualified = [(c, conf, checks) for c, conf, checks in scored if conf >= min_confidence][:quantity]

    # --- Step 4: Shortlist ---
    st.markdown(
        f'<div class="step-header">4 · Shortlist — {len(qualified)} of {quantity} requested</div>',
        unsafe_allow_html=True,
    )
    if len(qualified) < quantity:
        st.warning(
            f"Only {len(qualified)} candidates clear the {min_confidence} confidence bar. "
            f"An honest agent reports this gap instead of padding the list to hit the number."
        )
    else:
        st.success(
            f"All {quantity} requested leads cleared the {min_confidence} confidence bar."
        )

    # --- Step 4/5: Outreach + evidence package ---
    for company, conf, checks in qualified:
        with st.expander(f"**{company['name']}** — confidence {conf}"):
            colA, colB = st.columns([1, 1])
            with colA:
                st.markdown(
                    '<p style="font-weight: 600; margin-bottom: 0.5rem; '
                    'color: var(--neu-text);">Outreach draft</p>',
                    unsafe_allow_html=True,
                )
                st.code(draft_outreach(company), language=None)
            with colB:
                st.markdown(
                    '<p style="font-weight: 600; margin-bottom: 0.5rem; '
                    'color: var(--neu-text);">Evidence package (oracle input)</p>',
                    unsafe_allow_html=True,
                )
                for field, (ok, val) in checks.items():
                    icon = "PASS" if ok else "FAIL"
                    st.markdown(
                        f'<div style="display: flex; align-items: center; gap: 0.5rem; '
                        f'padding: 0.25rem 0;">'
                        f'<span style="font-size: 0.8rem; font-weight: 600; color: {"var(--neu-success)" if ok else "var(--neu-error)"};">{icon}</span>'
                        f'<code style="background: transparent; color: var(--neu-text); font-size: 0.85rem;">'
                        f'{field}: {val}</code>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div style="display: flex; align-items: center; gap: 0.5rem; '
                    f'padding-top: 0.5rem; border-top: 1px solid var(--neu-shadow-dark); '
                    f'margin-top: 0.5rem;">'
                    f'<span style="font-size: 0.8rem; font-weight: 600; color: var(--neu-text-muted);">Source:</span>'
                    f'<code style="background: transparent; color: var(--neu-text); font-size: 0.85rem;">'
                    f'{company["source"]}</code>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # --- Step 5: Verifier verdict ---
    # ⚠️  Honest gap: the verdict re-uses the same `qualified` list scoring produced,
    # rather than re-deriving from raw evidence independently. A real oracle would
    # run as a separate service with its own data access path — see Section 15.
    st.markdown(
        '<div class="step-header">5 · Verifier verdict</div>',
        unsafe_allow_html=True,
    )
    if len(qualified) >= quantity:
        st.success(
            f"PASS — {quantity} leads delivered, each with an independently re-checkable "
            f"evidence trail. Escrow release recommended."
        )
    else:
        st.error(
            f"PARTIAL — {len(qualified)}/{quantity} leads met the bar. "
            f"Escrow should release proportionally or the bounty should stay open, "
            f"not silently pay out on an unmet quota."
        )

    # Verdict footnotes
    st.markdown(
        '<div style="margin-top: 1rem; padding: 1rem; border-radius: var(--neu-radius-sm); '
        'background: var(--neu-card); '
        'box-shadow: inset 3px 3px 8px var(--neu-shadow-dark), '
        'inset -3px -3px 8px var(--neu-shadow-light);">'
        '<p style="color: var(--neu-text-muted); font-size: 0.85rem; margin: 0;">'
        'This is the piece most lead-gen agents skip: the claim and the check are the same step, '
        'so there\'s nothing for a buyer or an oracle to independently verify. Here they\'re separated — '
        'the scoring table and evidence package exist whether or not the shortlist passes.'
        '</p>'
        '<p style="color: var(--neu-text-muted); font-size: 0.8rem; margin: 0.5rem 0 0; '
        'border-top: 1px solid var(--neu-shadow-dark); padding-top: 0.5rem;">'
        'Note: In this demo the verifier still relies on the scorer\'s output rather than '
        're-deriving from raw evidence independently. A real production oracle would run as a '
        'separate service with its own data access path — see Section 15 of the build guide.'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )

else:
    st.info("Set your acceptance criteria above and click **Run bounty**.")
