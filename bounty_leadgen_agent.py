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
# 3D Hyperrealism CSS — brushed titanium, carbon fiber, optical glass,
# cinematic lighting, physics-based motion, CSS 3D transforms.
# Palette: Gunmetal Grey, Silver, with cyan accent glows.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&display=swap');

    /* ── Physics-based motion: spring overshoot ── */
    @keyframes spring-up {
        0% { transform: translateY(12px) scale(0.96); opacity: 0; }
        50% { transform: translateY(-2px) scale(1.01); opacity: 1; }
        70% { transform: translateY(1px) scale(0.995); }
        100% { transform: translateY(0) scale(1); opacity: 1; }
    }
    @keyframes lens-flare {
        0% { transform: translateX(-100%) rotate(-30deg); opacity: 0; }
        20% { opacity: 0.6; }
        60% { transform: translateX(100%) rotate(-30deg); opacity: 0.3; }
        100% { transform: translateX(200%) rotate(-30deg); opacity: 0; }
    }
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 6px rgba(0, 180, 216, 0.3), 0 0 20px rgba(0, 180, 216, 0.1); }
        50% { box-shadow: 0 0 12px rgba(0, 180, 216, 0.5), 0 0 40px rgba(0, 180, 216, 0.2); }
    }

    :root {
        --gunmetal: #2C2E33;
        --gunmetal-light: #3D4045;
        --gunmetal-dark: #1A1B1E;
        --silver: #C0C2C5;
        --silver-light: #D6D8DB;
        --silver-dark: #8A8D91;
        --titanium: #A0A3A8;
        --carbon: #1E1F22;
        --carbon-light: #2A2B30;
        --cyan: #00B4D8;
        --cyan-glow: #48CAE4;
        --glass: rgba(255, 255, 255, 0.06);
        --glass-edge: rgba(255, 255, 255, 0.1);
        --bg-dark: #141518;
        --text-primary: #E8E9EB;
        --text-muted: #8A8D93;
        --text-dim: #5C5F66;
        --success: #2ECC71;
        --success-bg: rgba(46, 204, 113, 0.1);
        --warning: #F39C12;
        --warning-bg: rgba(243, 156, 18, 0.1);
        --error: #E74C3C;
        --error-bg: rgba(231, 76, 60, 0.1);
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 16px;
        --perspective: 1200px;
    }

    /* ── Background: carbon fiber dark ── */
    html, body, #root, .stApp, .main > div {
        background: var(--bg-dark) !important;
        font-family: 'Chakra Petch', sans-serif !important;
        color: var(--text-primary);
    }
    .stApp {
        background: var(--bg-dark) !important;
    }
    .main {
        perspective: var(--perspective);
    }

    /* ── Subtle carbon fiber texture overlay ── */
    .stApp::after {
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.015) 2px, rgba(255,255,255,0.015) 4px),
            repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(255,255,255,0.012) 2px, rgba(255,255,255,0.012) 4px);
        pointer-events: none;
        z-index: 9999;
    }

    /* ── Cinematic vignette ── */
    .main::before {
        content: '';
        position: fixed;
        inset: 0;
        background: radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.5) 100%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Lens flare highlight (fixed position sweep) ── */
    .stApp::before {
        content: '';
        position: fixed;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: linear-gradient(
            45deg,
            transparent 30%,
            rgba(0, 180, 216, 0.02) 40%,
            rgba(255, 255, 255, 0.04) 45%,
            rgba(0, 180, 216, 0.02) 50%,
            transparent 60%
        );
        animation: lens-flare 12s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }

    /* ── Typography ── */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stText,
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Chakra Petch', sans-serif !important;
        color: var(--text-primary);
        line-height: 1.6;
    }
    h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--silver-light) !important;
        margin-bottom: 0.25rem !important;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5), 0 0 40px rgba(0, 180, 216, 0.08);
    }
    h2, .stSubheader { font-size: 1.15rem !important; font-weight: 600 !important; color: var(--silver) !important; margin-top: 0.5rem !important; letter-spacing: 0.02em; }
    p, .stMarkdown p { font-size: 0.92rem !important; line-height: 1.7 !important; color: var(--text-primary) !important; }

    /* ── Step headers: titanium badge ── */
    .step-header {
        display: inline-block;
        background: linear-gradient(135deg, var(--gunmetal-light) 0%, var(--gunmetal) 100%);
        border-radius: var(--radius-sm);
        padding: 0.6rem 1.3rem;
        margin: 1.5rem 0 1rem 0;
        font-family: 'Chakra Petch', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.03em;
        color: var(--silver-light) !important;
        box-shadow:
            0 2px 4px rgba(0,0,0,0.3),
            0 4px 12px rgba(0,0,0,0.15),
            inset 0 1px 0 rgba(255,255,255,0.08);
        border: 1px solid var(--glass-edge);
        position: relative;
        z-index: 1;
        transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.25s ease;
        animation: spring-up 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    }
    .step-header:hover {
        transform: translateY(-1px) scale(1.02);
        box-shadow:
            0 4px 8px rgba(0,0,0,0.4),
            0 8px 24px rgba(0,0,0,0.2),
            inset 0 1px 0 rgba(255,255,255,0.12),
            0 0 20px rgba(0, 180, 216, 0.06);
        border-color: rgba(0, 180, 216, 0.2);
    }

    /* ── Dividers: etched line ── */
    hr, .stDivider {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, var(--glass-edge), transparent) !important;
        margin: 1.5rem 0 !important;
        position: relative;
    }

    /* ── Glass card ── */
    .glass-card {
        background: var(--glass);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: var(--radius-md);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid var(--glass-edge);
        box-shadow:
            0 4px 16px rgba(0,0,0,0.2),
            0 1px 4px rgba(0,0,0,0.15),
            inset 0 1px 0 rgba(255,255,255,0.06);
        position: relative;
        z-index: 1;
        transform: translateZ(0);
        transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
    }
    .glass-card:hover {
        transform: translateZ(4px);
        box-shadow:
            0 8px 32px rgba(0,0,0,0.3),
            0 2px 8px rgba(0,0,0,0.2),
            inset 0 1px 0 rgba(255,255,255,0.08);
    }

    /* ── Widget Labels ── */
    .stSelectbox label, .stSlider label, .stTextInput label,
    .stNumberInput label, p, .stMarkdown p {
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        color: var(--silver) !important;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.4rem !important;
    }

    /* ── Buttons: brushed titanium ── */
    div.stButton > button {
        font-family: 'Chakra Petch', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        background: linear-gradient(135deg, var(--gunmetal-light) 0%, var(--gunmetal) 100%) !important;
        color: var(--silver-light) !important;
        border: 1px solid var(--glass-edge) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.75rem 2.5rem !important;
        box-shadow:
            0 2px 4px rgba(0,0,0,0.3),
            0 4px 12px rgba(0,0,0,0.15),
            inset 0 1px 0 rgba(255,255,255,0.08) !important;
        transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        cursor: pointer !important;
        min-height: 3rem;
        min-width: 10rem;
        position: relative;
        z-index: 1;
        overflow: hidden;
    }
    div.stButton > button::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
        background-size: 200% 100%;
        animation: shimmer 4s ease-in-out infinite;
        pointer-events: none;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow:
            0 4px 12px rgba(0,0,0,0.4),
            0 8px 24px rgba(0,0,0,0.2),
            inset 0 1px 0 rgba(255,255,255,0.12),
            0 0 16px rgba(0, 180, 216, 0.06) !important;
        border-color: rgba(0, 180, 216, 0.25) !important;
        color: var(--cyan-glow) !important;
    }
    div.stButton > button:active {
        transform: translateY(0) scale(0.98);
        box-shadow:
            0 1px 2px rgba(0,0,0,0.3),
            inset 0 2px 8px rgba(0,0,0,0.2) !important;
    }
    /* Primary button variant: cyan accent */
    div.stButton > button[kind="primary"],
    div.stButton > button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #005A7A 0%, #003D52 100%) !important;
        color: var(--cyan-glow) !important;
        border-color: rgba(0, 180, 216, 0.3) !important;
        box-shadow:
            0 2px 4px rgba(0,0,0,0.3),
            0 4px 12px rgba(0, 180, 216, 0.1),
            inset 0 1px 0 rgba(255,255,255,0.08) !important;
        animation: pulse-glow 3s ease-in-out infinite;
    }
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button[kind="primaryFormSubmit"]:hover {
        background: linear-gradient(135deg, #007096 0%, #005A7A 100%) !important;
        box-shadow:
            0 4px 12px rgba(0,0,0,0.4),
            0 8px 24px rgba(0, 180, 216, 0.15),
            inset 0 1px 0 rgba(255,255,255,0.1) !important;
    }
    div.stButton > button[kind="primary"]:active,
    div.stButton > button[kind="primaryFormSubmit"]:active {
        background: linear-gradient(135deg, #002A3A 0%, #001A26 100%) !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.3) !important;
    }

    /* ── Selectbox: carbon fiber inset ── */
    div[data-testid="stSelectbox"] > div > div {
        background: var(--carbon) !important;
        border: 1px solid var(--glass-edge) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.25rem 0.75rem !important;
        transition: all 0.2s ease !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3), 0 1px 0 rgba(255,255,255,0.04) !important;
    }
    div[data-testid="stSelectbox"] > div > div:focus-within {
        border-color: var(--cyan) !important;
        box-shadow:
            inset 0 2px 4px rgba(0,0,0,0.3),
            0 0 0 2px rgba(0, 180, 216, 0.15) !important;
    }
    div[data-testid="stSelectbox"] select {
        background: transparent !important;
        color: var(--text-primary) !important;
        font-family: 'Chakra Petch', sans-serif !important;
        font-size: 0.85rem !important;
    }

    /* ── Text / Number Input: carbon fiber inset ── */
    div[data-testid="stTextInput"] > div > div,
    div[data-testid="stNumberInput"] > div > div {
        background: var(--carbon) !important;
        border: 1px solid var(--glass-edge) !important;
        border-radius: var(--radius-sm) !important;
        transition: all 0.2s ease !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3), 0 1px 0 rgba(255,255,255,0.04) !important;
    }
    div[data-testid="stTextInput"] > div > div:focus-within,
    div[data-testid="stNumberInput"] > div > div:focus-within {
        border-color: var(--cyan) !important;
        box-shadow:
            inset 0 2px 4px rgba(0,0,0,0.3),
            0 0 0 2px rgba(0, 180, 216, 0.15) !important;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input {
        background: transparent !important;
        color: var(--text-primary) !important;
        font-family: 'Chakra Petch', sans-serif !important;
        font-size: 0.85rem !important;
        border: none !important;
        box-shadow: none !important;
    }
    div[data-testid="stNumberInput"] button {
        background: var(--gunmetal) !important;
        border: 1px solid var(--glass-edge) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--silver) !important;
        min-width: 2rem !important;
        min-height: 2rem !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.06) !important;
    }
    div[data-testid="stNumberInput"] button:active {
        transform: scale(0.92);
        background: var(--gunmetal-dark) !important;
    }

    /* ── Slider ── */
    div[data-testid="stSlider"] { padding: 0.75rem 0.25rem !important; }
    div[data-testid="stSlider"] > div {
        background: var(--carbon) !important;
        border: 1px solid var(--glass-edge) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.75rem 1rem 0.25rem !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="stSlider"] div[role="slider"] {
        background: linear-gradient(135deg, var(--cyan) 0%, #0096B4 100%) !important;
        border: 2px solid var(--bg-dark) !important;
        box-shadow: 0 0 8px rgba(0, 180, 216, 0.3), 0 2px 4px rgba(0,0,0,0.3) !important;
        transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        width: 20px !important; height: 20px !important;
    }
    div[data-testid="stSlider"] div[role="slider"]:active {
        transform: scale(1.2);
        box-shadow: 0 0 16px rgba(0, 180, 216, 0.5), 0 2px 8px rgba(0,0,0,0.3) !important;
    }

    /* ── Dataframe: glass table ── */
    div[data-testid="stDataFrame"] {
        border-radius: var(--radius-md) !important;
        overflow: hidden !important;
        box-shadow:
            0 4px 16px rgba(0,0,0,0.2),
            0 1px 4px rgba(0,0,0,0.15),
            inset 0 1px 0 rgba(255,255,255,0.04) !important;
        background: var(--glass) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid var(--glass-edge) !important;
    }
    div[data-testid="stDataFrame"] table {
        font-family: 'Chakra Petch', sans-serif !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }
    div[data-testid="stDataFrame"] thead tr th {
        background: var(--gunmetal) !important;
        color: var(--silver-light) !important;
        font-weight: 600 !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.7rem 0.6rem !important;
        border-bottom: 1px solid var(--glass-edge) !important;
    }
    div[data-testid="stDataFrame"] tbody tr td {
        background: transparent !important;
        color: var(--text-primary) !important;
        font-size: 0.82rem !important;
        padding: 0.55rem 0.6rem !important;
        border-bottom: 1px solid rgba(255,255,255,0.03) !important;
    }
    div[data-testid="stDataFrame"] tbody tr:hover td {
        background: rgba(0, 180, 216, 0.04) !important;
        cursor: default !important;
    }

    /* ── Expander: glass panel ── */
    div[data-testid="stExpander"] {
        border: 1px solid var(--glass-edge) !important;
        border-radius: var(--radius-md) !important;
        background: var(--glass) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        box-shadow:
            0 4px 16px rgba(0,0,0,0.15),
            0 1px 4px rgba(0,0,0,0.1),
            inset 0 1px 0 rgba(255,255,255,0.04) !important;
        margin-bottom: 1rem !important;
        overflow: hidden !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        position: relative;
        z-index: 1;
    }
    div[data-testid="stExpander"]:hover {
        box-shadow:
            0 8px 32px rgba(0,0,0,0.25),
            0 2px 8px rgba(0,0,0,0.15),
            inset 0 1px 0 rgba(255,255,255,0.06),
            0 0 16px rgba(0, 180, 216, 0.03) !important;
        border-color: rgba(0, 180, 216, 0.15);
    }
    div[data-testid="stExpander"] summary {
        font-family: 'Chakra Petch', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.02em;
        color: var(--silver-light) !important;
        padding: 0.8rem 1.1rem !important;
        border-radius: var(--radius-md) !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        user-select: none !important;
    }
    div[data-testid="stExpander"] summary:hover { background: rgba(255,255,255,0.03) !important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderContent"] {
        background: rgba(0,0,0,0.15) !important;
        border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
        padding: 0.5rem 1.1rem 1.1rem !important;
        box-shadow: inset 0 4px 12px rgba(0,0,0,0.1) !important;
    }

    /* ── Alerts ── */
    div[data-testid="stAlertContainer"] {
        border: none !important;
        padding: 0 !important;
        font-family: 'Chakra Petch', sans-serif !important;
        margin-bottom: 1rem !important;
    }
    div[data-testid="stAlertContainer"] > div {
        border: 1px solid var(--glass-edge) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.9rem 1.1rem !important;
        font-family: 'Chakra Petch', sans-serif !important;
        font-size: 0.85rem !important;
        background: var(--glass) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }
    div[data-testid="stAlertContainer"] .stAlert {
        background: var(--success-bg) !important;
        border-color: rgba(46, 204, 113, 0.25) !important;
        box-shadow: 0 0 12px rgba(46, 204, 113, 0.06) !important;
    }
    div[data-testid="stAlertContainer"] .st-bd {
        background: var(--error-bg) !important;
        border-color: rgba(231, 76, 60, 0.25) !important;
    }
    div[data-testid="stAlertContainer"] .st-cb {
        background: var(--warning-bg) !important;
        border-color: rgba(243, 156, 18, 0.25) !important;
    }
    div[data-testid="stAlertContainer"] .st-cs {
        background: rgba(0, 180, 216, 0.08) !important;
        border-color: rgba(0, 180, 216, 0.2) !important;
    }
    div[data-testid="stAlertContainer"] .stMarkdown p { color: var(--text-primary) !important; font-weight: 500 !important; }

    /* ── Spinner ── */
    div.stSpinner {
        border-radius: var(--radius-md) !important;
        padding: 1.5rem !important;
        background: var(--glass) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid var(--glass-edge) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
    }
    div.stSpinner > div { border-top-color: var(--cyan) !important; border-width: 2px !important; }

    /* ── Code blocks (dark glass) ── */
    .stCodeBlock {
        border-radius: var(--radius-sm) !important;
        background: var(--carbon) !important;
        border: 1px solid var(--glass-edge) !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.2) !important;
        padding: 0.25rem !important;
    }
    .stCodeBlock code { background: transparent !important; color: var(--cyan-glow) !important; font-size: 0.82rem !important; }

    /* ── Caption ── */
    .stCaption, .stMarkdown small, .stMarkdown .caption {
        color: var(--text-dim) !important;
        font-size: 0.78rem !important;
        font-weight: 400 !important;
        letter-spacing: 0.02em;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-dark); }
    ::-webkit-scrollbar-thumb {
        background: var(--gunmetal-light);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: var(--silver-dark); }

    /* ── Tooltip ── */
    div[data-testid="stTooltipIcon"] { color: var(--text-dim) !important; opacity: 0.5; transition: opacity 0.2s ease; }
    div[data-testid="stTooltipIcon"]:hover { opacity: 0.8; }

    /* ── Info callout ── */
    .stAlertContainer .stAlert {
        background: var(--glass) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid var(--glass-edge) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
        border-radius: var(--radius-sm) !important;
    }

    /* ── 3D card hover effect on data containers ── */
    div[data-testid="stVerticalBlock"] > div {
        transform-style: preserve-3d;
        transition: transform 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("Verified Lead-Gen & Qualification Agent")
st.markdown(
    '<p style="color: var(--text-muted); font-size: 0.95rem; margin-top: -0.5rem; '
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
        f'<div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">'
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
        '<div style="font-size: 0.8rem; color: var(--text-muted); text-align: right; '
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
                    'color: var(--text-primary);">Outreach draft</p>',
                    unsafe_allow_html=True,
                )
                st.code(draft_outreach(company), language=None)
            with colB:
                st.markdown(
                    '<p style="font-weight: 600; margin-bottom: 0.5rem; '
                    'color: var(--text-primary);">Evidence package (oracle input)</p>',
                    unsafe_allow_html=True,
                )
                for field, (ok, val) in checks.items():
                    icon = "PASS" if ok else "FAIL"
                    st.markdown(
                        f'<div style="display: flex; align-items: center; gap: 0.5rem; '
                        f'padding: 0.25rem 0;">'
                        f'<span style="font-size: 0.8rem; font-weight: 600; color: {"var(--success)" if ok else "var(--error)"};">{icon}</span>'
                        f'<code style="background: transparent; color: var(--text-primary); font-size: 0.85rem;">'
                        f'{field}: {val}</code>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div style="display: flex; align-items: center; gap: 0.5rem; '
                    f'padding-top: 0.5rem; border-top: 1px solid var(--glass-edge); '
                    f'margin-top: 0.5rem;">'
                    f'<span style="font-size: 0.8rem; font-weight: 600; color: var(--text-muted);">Source:</span>'
                    f'<code style="background: transparent; color: var(--text-primary); font-size: 0.85rem;">'
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
        '<div style="margin-top: 1rem; padding: 1rem; border-radius: var(--radius-sm); '
        'background: var(--glass); backdrop-filter: blur(8px); '
        'border: 1px solid var(--glass-edge); '
        'box-shadow: 0 4px 16px rgba(0,0,0,0.2), 0 1px 4px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.04);">'
        '<p style="color: var(--text-muted); font-size: 0.85rem; margin: 0;">'
        'This is the piece most lead-gen agents skip: the claim and the check are the same step, '
        'so there\'s nothing for a buyer or an oracle to independently verify. Here they\'re separated — '
        'the scoring table and evidence package exist whether or not the shortlist passes.'
        '</p>'
        '<p style="color: var(--text-muted); font-size: 0.8rem; margin: 0.5rem 0 0; '
        'border-top: 1px solid var(--glass-edge); padding-top: 0.5rem;">'
        'Note: In this demo the verifier still relies on the scorer\'s output rather than '
        're-deriving from raw evidence independently. A real production oracle would run as a '
        'separate service with its own data access path — see Section 15 of the documentation.'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )

else:
    st.info("Set your acceptance criteria above and click **Run bounty**.")
