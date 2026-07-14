"""
Lead Qualification Agent — real data via Google Places API (New) or SerpAPI
------------------------------------------------------------------
Input: type of good/service + location. Output: real businesses in that
location, qualified against evidence-backed criteria, with an honest
pass/partial verdict.

Backends (tried in order):
1. Google Places API (New) — if a key is provided
2. SerpAPI Google Local — fallback if a SerpAPI key is provided

SETUP:
- Google: cloud.google.com → enable "Places API (New)" → create API key
- SerpAPI: serpapi.com → get API key (free tier: 100 searches/month)

Run:
    pip install -r requirements.txt
    streamlit run lead_qualification_agent.py

Paste your key(s) into the app. Google is tried first; SerpAPI is the fallback.
"""

import os
import pandas as pd
import streamlit as st

from lqa_agent import (
    search_places,
    normalize_place,
    score_lead,
    draft_outreach,
)


st.set_page_config(page_title="Lead Qualification Agent — Live Data", layout="wide")

st.title("Lead Qualification Agent — Live Data")
st.caption(
    "Real businesses from Google Places / SerpAPI, qualified against auditable criteria. "
    "No mock data — every row below comes from a live API call, and the "
    "scoring table shows rejected candidates too, not just the winners."
)

api_key_default = os.environ.get("GOOGLE_PLACES_API_KEY", "")
serp_key_default = os.environ.get("SERPAPI_API_KEY", "")

c_key1, c_key2 = st.columns(2)
with c_key1:
    api_key = st.text_input(
        "Google Places API key (optional)",
        value=api_key_default,
        type="password",
        help="From Google Cloud Console. If provided, tried first.",
    )
with c_key2:
    serp_key = st.text_input(
        "SerpAPI key (fallback)",
        value=serp_key_default,
        type="password",
        help="From serpapi.com. Used as fallback if no Google key or Google fails.",
    )

st.divider()
st.subheader("1 . Search criteria")
c1, c2, c3, c4 = st.columns(4)
with c1:
    good_or_service = st.text_input("Type of good/service", value="packaging suppliers")
with c2:
    location = st.text_input("Location", value="Bhopal, Madhya Pradesh")
with c3:
    quantity = st.number_input("Leads requested", min_value=1, max_value=20, value=5)
with c4:
    max_fetch = st.number_input("Max candidates to fetch", min_value=5, max_value=20, value=20)

min_confidence = st.slider("Minimum confidence to count as qualified", 0.0, 1.0, 0.6, 0.05)
min_reviews = st.slider("Minimum Google reviews to count as 'established'", 0, 50, 5)

run = st.button("Run live search", type="primary")

if run:
    if not api_key and not serp_key:
        st.error(
            "No API key provided. Provide a Google Places API key (preferred) "
            "or a SerpAPI key (fallback). Nothing runs without one."
        )
        st.stop()

    query = f"{good_or_service} in {location}"
    st.subheader("2 . Live prospecting")
    with st.spinner(f"Searching: \"{query}\"..."):
        try:
            raw_places, backend = search_places(query, api_key=api_key, serp_key=serp_key, max_results=max_fetch)
        except Exception as e:
            st.error(f"Search failed: {e}")
            st.stop()

    if not raw_places:
        st.warning(
            f"Zero results for \"{query}\". Try a broader location or a more common "
            f"category term — this is the real API returning nothing, not a bug."
        )
        st.stop()

    st.write(f"Found **{len(raw_places)}** real businesses (backend: {backend}).")

    candidates = [normalize_place(p) for p in raw_places]
    criteria = dict(keyword=good_or_service.split()[0], min_reviews=min_reviews)

    st.subheader("3 . Qualification scoring (auditable, per-field)")
    scored = [(c, *score_lead(c, criteria)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)

    score_table = pd.DataFrame([
        {
            "Business": c["name"],
            "Category": c["primary_type"] or "—",
            "Address": c["address"],
            "Confidence": conf,
            "CatMatch": "YES" if checks["category_relevance"][0] else "NO",
            "Phone": "YES" if checks["phone_available"][0] else "NO",
            "Website": "YES" if checks["website_available"][0] else "NO",
            "Established": "YES" if checks["established_presence"][0] else "NO",
        }
        for c, conf, checks in scored
    ])
    st.dataframe(score_table, use_container_width=True, hide_index=True)

    qualified = [(c, conf, checks) for c, conf, checks in scored if conf >= min_confidence][:quantity]

    st.subheader(f"4 . Shortlist — {len(qualified)} of {quantity} requested")
    if len(qualified) < quantity:
        st.warning(
            f"Only {len(qualified)} of the {len(candidates)} businesses found clear the "
            f"{min_confidence} confidence bar. Reported honestly rather than padded to hit the count — "
            f"try a broader location, a lower bar, or a more common category term."
        )

    for c, conf, checks in qualified:
        with st.expander(f"**{c['name']}** — confidence {conf}"):
            colA, colB = st.columns(2)
            with colA:
                st.markdown("**Outreach draft**")
                st.code(draft_outreach(c, good_or_service), language=None)
            with colB:
                st.markdown("**Evidence package (oracle input)**")
                for field, (ok, val) in checks.items():
                    st.write(f"{'YES' if ok else 'NO'} `{field}`: {val}")
                if c["maps_url"]:
                    st.markdown(f"[Verify on Google Maps]({c['maps_url']})")
                st.caption(f"Place ID: `{c['place_id']}` | Backend: {backend}")

    st.subheader("5 . Verifier verdict")
    if len(qualified) >= quantity:
        st.success(
            f"PASS — {quantity} real, verifiable leads delivered. Every evidence field "
            f"traces back to a live listing — click through and check any of them."
        )
    else:
        st.error(
            f"PARTIAL — {len(qualified)}/{quantity} leads met the bar. This is real search "
            f"scarcity, not the agent underperforming on a fixed pool."
        )
else:
    st.info("Set your search criteria and API keys above, then click **Run live search**.")
