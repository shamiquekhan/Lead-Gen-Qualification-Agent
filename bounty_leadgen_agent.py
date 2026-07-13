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

from agent import MOCK_COMPANIES, score_lead, draft_outreach

st.set_page_config(page_title="Bounty — Verified Lead-Gen Agent", layout="wide")

# ---------------------------------------------------------------------------
# Organic / Biomorphic CSS — fluid blob shapes, nature-inspired palette,
# wavy dividers, breathing motion, gooey effects.
# Living Earth palette: Sage Green, Clay, Sand, Moss.
# ---------------------------------------------------------------------------
st.markdown("""
<svg style="position:absolute;width:0;height:0;" aria-hidden="true">
  <defs>
    <filter id="goo">
      <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="blur" />
      <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9" result="goo" />
      <feBlend in="SourceGraphic" in2="goo" />
    </filter>
  </defs>
</svg>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&display=swap');

    @keyframes blob-float {
        0%, 100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; transform: translate(0, 0) scale(1); }
        33% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; transform: translate(30px, -20px) scale(1.05); }
        66% { border-radius: 70% 30% 50% 50% / 30% 50% 70% 40%; transform: translate(-20px, 10px) scale(0.95); }
    }
    @keyframes blob-float-slow {
        0%, 100% { border-radius: 50% 50% 40% 60% / 60% 40% 60% 40%; transform: translate(0, 0) scale(1); }
        33% { border-radius: 40% 60% 60% 40% / 50% 60% 40% 50%; transform: translate(-25px, 15px) scale(1.03); }
        66% { border-radius: 60% 40% 50% 50% / 40% 50% 60% 50%; transform: translate(20px, -15px) scale(0.97); }
    }
    @keyframes wave-scroll {
        0% { background-position-x: 0; }
        100% { background-position-x: 200px; }
    }
    @keyframes breathe {
        0%, 100% { transform: scale(1); opacity: 0.4; }
        50% { transform: scale(1.03); opacity: 0.6; }
    }

    :root {
        --sage: #8FAB7A;
        --sage-light: #B5CDA3;
        --sage-dark: #6A8060;
        --clay: #C17A4E;
        --clay-light: #D49A6A;
        --clay-dark: #A05E38;
        --sand: #E8D5B7;
        --sand-light: #F5EDDC;
        --sand-dark: #D4BFA0;
        --moss: #5C7A3E;
        --moss-dark: #3D5228;
        --bg-warm: #F2EBE1;
        --text-primary: #2C2A1E;
        --text-muted: #7A7568;
        --text-on-dark: #F5F0E8;
        --success: #6A9F6A;
        --warning: #C9A04A;
        --error: #C46060;
        --radius-blob-1: 45% 55% 60% 40% / 55% 45% 55% 45%;
        --radius-blob-2: 55% 45% 40% 60% / 45% 55% 45% 55%;
        --radius-blob-3: 60% 40% 45% 55% / 40% 55% 60% 50%;
        --shadow-organic: 0 8px 32px rgba(92, 122, 62, 0.12), 0 2px 8px rgba(92, 122, 62, 0.06);
        --shadow-float: 0 12px 40px rgba(92, 122, 62, 0.15), 0 4px 12px rgba(92, 122, 62, 0.08);
        --glow-sage: 0 0 0 0 rgba(143, 171, 122, 0);
    }

    html, body, #root, .stApp, .main > div {
        background: var(--bg-warm) !important;
        font-family: 'Quicksand', sans-serif !important;
        color: var(--text-primary);
    }
    .stApp { background: var(--bg-warm) !important; }

    /* ── Background blobs with gooey SVG filter ── */
    .main::before {
        content: '';
        position: fixed;
        width: 400px;
        height: 400px;
        top: -80px;
        right: -100px;
        background: radial-gradient(circle, var(--sage-light) 0%, transparent 70%);
        opacity: 0.35;
        animation: blob-float 18s ease-in-out infinite, breathe 5s ease-in-out infinite;
        filter: url(#goo);
        pointer-events: none;
        z-index: 0;
    }
    .main::after {
        content: '';
        position: fixed;
        width: 350px;
        height: 350px;
        bottom: -60px;
        left: -80px;
        background: radial-gradient(circle, var(--clay-light) 0%, transparent 70%);
        opacity: 0.25;
        animation: blob-float-slow 22s ease-in-out infinite, breathe 6s ease-in-out infinite;
        filter: url(#goo);
        pointer-events: none;
        z-index: 0;
    }
    .stApp::before {
        content: '';
        position: fixed;
        width: 250px;
        height: 250px;
        top: 40%;
        left: -60px;
        background: radial-gradient(circle, var(--sand) 0%, transparent 65%);
        opacity: 0.3;
        animation: blob-float 25s ease-in-out infinite, breathe 7s ease-in-out infinite;
        filter: url(#goo);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Typography ── */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stText,
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Quicksand', sans-serif !important;
        color: var(--text-primary);
        line-height: 1.6;
    }
    h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        color: var(--moss-dark) !important;
        margin-bottom: 0.25rem !important;
        position: relative;
        z-index: 1;
    }
    h2, .stSubheader { font-size: 1.2rem !important; font-weight: 600 !important; color: var(--text-primary) !important; margin-top: 0.5rem !important; }
    p, .stMarkdown p { font-size: 0.95rem !important; line-height: 1.7 !important; color: var(--text-primary) !important; }

    /* ── Step headers ── */
    .step-header {
        display: inline-block;
        background: linear-gradient(135deg, var(--sage) 0%, var(--sage-dark) 100%);
        border-radius: var(--radius-blob-2);
        padding: 0.7rem 1.4rem;
        margin: 1.5rem 0 1rem 0;
        font-family: 'Quicksand', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        color: var(--text-on-dark) !important;
        box-shadow: var(--shadow-organic);
        transition: border-radius 0.5s ease, transform 0.3s ease;
        position: relative;
        z-index: 1;
    }
    .step-header:hover {
        border-radius: var(--radius-blob-3);
        transform: scale(1.02);
        box-shadow: var(--shadow-float);
    }

    /* ── Wavy dividers (no straight lines) ── */
    hr, .stDivider {
        border: none !important;
        height: 24px !important;
        background: transparent !important;
        position: relative;
        margin: 1.5rem 0 !important;
        overflow: visible !important;
    }
    hr::before, .stDivider::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 24px;
        background: url("data:image/svg+xml,%3Csvg width='200' height='24' viewBox='0 0 200 24' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0,12 Q25,0 50,12 T100,12 T150,12 T200,12' stroke='%238FAB7A' stroke-width='2' fill='none' opacity='0.5'/%3E%3C/svg%3E") repeat-x;
        background-size: 200px 24px;
        animation: wave-scroll 8s linear infinite;
    }

    /* ── Organic card (no straight-line borders) ── */
    .bio-card {
        background: rgba(245, 237, 220, 0.7);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border-radius: var(--radius-blob-1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-organic), 0 0 0 1px rgba(143, 171, 122, 0.12);
        transition: all 0.4s ease;
        position: relative;
        z-index: 1;
    }
    .bio-card:hover {
        box-shadow: var(--shadow-float), 0 0 0 1px rgba(143, 171, 122, 0.2);
        border-radius: var(--radius-blob-2);
    }

    /* ── Widget Labels ── */
    .stSelectbox label, .stSlider label, .stTextInput label,
    .stNumberInput label, p, .stMarkdown p {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        margin-bottom: 0.4rem !important;
    }

    /* ── Buttons (shadow edge, not border) ── */
    div.stButton > button {
        font-family: 'Quicksand', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        background: linear-gradient(135deg, var(--sand-light) 0%, var(--sand) 100%) !important;
        color: var(--moss-dark) !important;
        border: none !important;
        border-radius: var(--radius-blob-1) !important;
        padding: 0.75rem 2.5rem !important;
        box-shadow: var(--shadow-organic), 0 0 0 1px rgba(143, 171, 122, 0.15) !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        min-height: 3.2rem;
        min-width: 10rem;
        position: relative;
        z-index: 1;
    }
    div.stButton > button:hover {
        border-radius: var(--radius-blob-2) !important;
        transform: translateY(-2px);
        box-shadow: var(--shadow-float), 0 0 0 1px rgba(143, 171, 122, 0.25) !important;
    }
    div.stButton > button:active {
        transform: translateY(1px) scale(0.98);
        border-radius: var(--radius-blob-3) !important;
    }
    div.stButton > button[kind="primary"],
    div.stButton > button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, var(--moss) 0%, var(--sage-dark) 100%) !important;
        color: var(--text-on-dark) !important;
        box-shadow: var(--shadow-organic) !important;
    }
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button[kind="primaryFormSubmit"]:hover {
        background: linear-gradient(135deg, var(--sage) 0%, var(--moss) 100%) !important;
    }
    div.stButton > button[kind="primary"]:active,
    div.stButton > button[kind="primaryFormSubmit"]:active {
        background: linear-gradient(135deg, var(--moss-dark) 0%, var(--sage-dark) 100%) !important;
    }

    /* ── Inputs (organic edges via shadows, not border lines) ── */
    div[data-testid="stSelectbox"] > div > div,
    div[data-testid="stTextInput"] > div > div,
    div[data-testid="stNumberInput"] > div > div {
        background: rgba(245, 237, 220, 0.7) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        border: none !important;
        border-radius: var(--radius-blob-2) !important;
        padding: 0.25rem 0.75rem !important;
        transition: all 0.3s ease !important;
        box-shadow: inset 0 2px 6px rgba(92, 122, 62, 0.06), 0 0 0 1px rgba(143, 171, 122, 0.15) !important;
    }
    div[data-testid="stSelectbox"] > div > div:focus-within,
    div[data-testid="stTextInput"] > div > div:focus-within,
    div[data-testid="stNumberInput"] > div > div:focus-within {
        box-shadow: 0 0 0 3px rgba(143, 171, 122, 0.15), 0 0 0 1px var(--sage) !important;
        border-radius: var(--radius-blob-3) !important;
    }
    div[data-testid="stSelectbox"] select,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input {
        background: transparent !important;
        color: var(--text-primary) !important;
        font-family: 'Quicksand', sans-serif !important;
        font-size: 0.9rem !important;
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stNumberInput"] button {
        background: rgba(245, 237, 220, 0.7) !important;
        border: none !important;
        border-radius: 50% !important;
        color: var(--moss) !important;
        min-width: 2rem !important;
        min-height: 2rem !important;
        transition: all 0.15s ease !important;
        box-shadow: var(--shadow-organic) !important;
    }
    div[data-testid="stNumberInput"] button:active {
        transform: scale(0.9);
        background: var(--sand) !important;
    }

    /* ── Slider ── */
    div[data-testid="stSlider"] { padding: 0.75rem 0.25rem !important; }
    div[data-testid="stSlider"] > div {
        background: rgba(245, 237, 220, 0.7) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        border: none !important;
        border-radius: var(--radius-blob-2) !important;
        padding: 0.75rem 1rem 0.25rem !important;
        box-shadow: inset 0 2px 6px rgba(92, 122, 62, 0.06), 0 0 0 1px rgba(143, 171, 122, 0.12) !important;
    }
    div[data-testid="stSlider"] div[role="slider"] {
        background: var(--sage) !important;
        border: 3px solid var(--sand-light) !important;
        box-shadow: var(--shadow-organic) !important;
        transition: all 0.2s ease !important;
        width: 22px !important; height: 22px !important;
    }
    div[data-testid="stSlider"] div[role="slider"]:active {
        transform: scale(0.9);
        box-shadow: var(--shadow-float) !important;
        background: var(--sage-dark) !important;
    }

    /* ── Dataframe (organic edges) ── */
    div[data-testid="stDataFrame"] {
        border-radius: var(--radius-blob-2) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-organic), 0 0 0 1px rgba(143, 171, 122, 0.12) !important;
        background: rgba(245, 237, 220, 0.6) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        padding: 0.25rem !important;
    }
    div[data-testid="stDataFrame"] table {
        font-family: 'Quicksand', sans-serif !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }
    div[data-testid="stDataFrame"] thead tr th {
        background: var(--sage) !important;
        color: var(--text-on-dark) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        padding: 0.75rem 0.6rem !important;
        border: none !important;
    }
    div[data-testid="stDataFrame"] thead tr th:first-child { border-radius: 20px 0 0 0; }
    div[data-testid="stDataFrame"] thead tr th:last-child { border-radius: 0 20px 0 0; }
    div[data-testid="stDataFrame"] tbody tr td {
        background: rgba(245, 237, 220, 0.3) !important;
        color: var(--text-primary) !important;
        font-size: 0.85rem !important;
        padding: 0.6rem !important;
        box-shadow: inset 0 -1px 0 rgba(143, 171, 122, 0.08) !important;
        border: none !important;
    }
    div[data-testid="stDataFrame"] tbody tr:last-child td:first-child { border-radius: 0 0 0 20px; }
    div[data-testid="stDataFrame"] tbody tr:last-child td:last-child { border-radius: 0 0 20px 0; }
    div[data-testid="stDataFrame"] tbody tr:hover td {
        background: rgba(143, 171, 122, 0.08) !important;
        cursor: default !important;
    }

    /* ── Expander (organic edges) ── */
    div[data-testid="stExpander"] {
        border: none !important;
        border-radius: var(--radius-blob-1) !important;
        background: rgba(245, 237, 220, 0.7) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        box-shadow: var(--shadow-organic), 0 0 0 1px rgba(143, 171, 122, 0.12) !important;
        margin-bottom: 1rem !important;
        overflow: hidden !important;
        transition: all 0.4s ease !important;
        position: relative;
        z-index: 1;
    }
    div[data-testid="stExpander"]:hover {
        box-shadow: var(--shadow-float) !important;
        border-radius: var(--radius-blob-2) !important;
    }
    div[data-testid="stExpander"] summary {
        font-family: 'Quicksand', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        color: var(--moss-dark) !important;
        padding: 0.85rem 1.2rem !important;
        border-radius: var(--radius-blob-1) !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        user-select: none !important;
    }
    div[data-testid="stExpander"] summary:hover { background: rgba(143, 171, 122, 0.06) !important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderContent"] {
        background: rgba(245, 237, 220, 0.4) !important;
        border-radius: 0 0 var(--radius-blob-1) var(--radius-blob-1) !important;
        padding: 0.5rem 1.25rem 1.25rem !important;
        box-shadow: inset 0 4px 12px rgba(92, 122, 62, 0.04) !important;
    }

    /* ── Alerts (organic, no borders) ── */
    div[data-testid="stAlertContainer"] {
        border: none !important;
        padding: 0 !important;
        font-family: 'Quicksand', sans-serif !important;
        margin-bottom: 1rem !important;
    }
    div[data-testid="stAlertContainer"] > div {
        border: none !important;
        border-radius: var(--radius-blob-2) !important;
        padding: 1rem 1.25rem !important;
        font-family: 'Quicksand', sans-serif !important;
        font-size: 0.9rem !important;
        background: rgba(245, 237, 220, 0.7) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
    }
    div[data-testid="stAlertContainer"] .stAlert {
        background: rgba(106, 159, 106, 0.12) !important;
        box-shadow: 0 0 0 1px rgba(106, 159, 106, 0.2) !important;
        border-radius: var(--radius-blob-2) !important;
    }
    div[data-testid="stAlertContainer"] .st-bd {
        background: rgba(196, 96, 96, 0.12) !important;
        box-shadow: 0 0 0 1px rgba(196, 96, 96, 0.2) !important;
        border-radius: var(--radius-blob-2) !important;
    }
    div[data-testid="stAlertContainer"] .st-cb {
        background: rgba(201, 160, 74, 0.12) !important;
        box-shadow: 0 0 0 1px rgba(201, 160, 74, 0.2) !important;
        border-radius: var(--radius-blob-2) !important;
    }
    div[data-testid="stAlertContainer"] .st-cs {
        background: rgba(143, 171, 122, 0.12) !important;
        box-shadow: 0 0 0 1px rgba(143, 171, 122, 0.2) !important;
        border-radius: var(--radius-blob-2) !important;
    }
    div[data-testid="stAlertContainer"] .stMarkdown p { color: var(--text-primary) !important; font-weight: 500 !important; }

    /* ── Spinner ── */
    div.stSpinner {
        border-radius: var(--radius-blob-2) !important;
        padding: 1.5rem !important;
        background: rgba(245, 237, 220, 0.7) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        box-shadow: var(--shadow-organic), 0 0 0 1px rgba(143, 171, 122, 0.08) !important;
    }
    div.stSpinner > div { border-top-color: var(--sage) !important; border-width: 3px !important; }

    /* ── Caption ── */
    .stCaption, .stMarkdown small, .stMarkdown .caption {
        color: var(--text-muted) !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-warm); border-radius: 8px; }
    ::-webkit-scrollbar-thumb {
        background: var(--sage-light);
        border-radius: 8px;
        border: 2px solid var(--bg-warm);
    }
    ::-webkit-scrollbar-thumb:hover { background: var(--sage); }

    /* ── Code blocks ── */
    .stCodeBlock {
        border-radius: var(--radius-blob-2) !important;
        background: rgba(44, 42, 30, 0.04) !important;
        box-shadow: inset 0 2px 8px rgba(92, 122, 62, 0.06), 0 0 0 1px rgba(143, 171, 122, 0.08) !important;
        padding: 0.25rem !important;
    }
    .stCodeBlock code { background: transparent !important; color: var(--moss-dark) !important; font-size: 0.85rem !important; }

    /* ── Tooltip ── */
    div[data-testid="stTooltipIcon"] { color: var(--text-muted) !important; opacity: 0.6; transition: opacity 0.2s ease; }
    div[data-testid="stTooltipIcon"]:hover { opacity: 0.9; }

    /* ── Info callout ── */
    .stAlertContainer .stAlert {
        background: rgba(245, 237, 220, 0.7) !important;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        box-shadow: 0 0 0 1px rgba(143, 171, 122, 0.15) !important;
        border-radius: var(--radius-blob-2) !important;
    }
</style>
""", unsafe_allow_html=True)


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
    # Honest gap: the verdict re-uses the same `qualified` list scoring produced,
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
