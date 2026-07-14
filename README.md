# Verified Lead-Gen & Qualification Agent

**A reference implementation of an outcome-based AI marketplace agent**, built to demonstrate [Bounty](https://trybounty.ai)'s "pay for verified outcomes, not AI outputs" model.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-124%20passing-brightgreen)](test_agent.py)

---

## The Core Idea

Most lead-gen agents **self-grade** — the agent that finds the leads is also the agent that decides whether they qualify. "5 qualified leads delivered" is just a sentence the model generated, with nothing behind it a buyer could check.

This project demonstrates an alternative: **every lead carries an auditable evidence record** — which criterion matched, what the matching value was, and where it came from — **before** any pass/fail verdict is rendered. The verdict step doesn't trust the scoring step; it re-derives the same checks and reports honestly when the shortlist falls short, instead of padding it to hit a quota.

The scoring table is shown **before** filtering (rejects included), and the verdict is willing to report **partial pass** rather than silently inflating results.

## Two Demos

| Demo | File | Data source | Requires API key |
|------|------|-------------|-----------------|
| **Mock pool** | `bounty_leadgen_agent.py` | 12 in-memory companies | No — works offline |
| **Live Places** | `lead_qualification_agent.py` | Google Places API + SerpAPI fallback | Google optional, SerpAPI prefilled |

### Mock demo (no setup, works offline)

```bash
pip install -r requirements.txt
streamlit run bounty_leadgen_agent.py
```

### Live Places demo (dual backend)

The app tries **Google Places API** first. If it fails or no Google key is given, it falls back to **SerpAPI** (prefilled with a demo key).

1. Google Cloud Console → enable **Places API (New)** → create an API key (optional)
2. Paste the Google key into the app, or leave blank to use SerpAPI
   ```bash
   streamlit run lead_qualification_agent.py
   ```

### Run the tests

```bash
python -m pytest test_agent.py test_ui.py test_lqa_agent.py test_lqa_ui.py -v
```

All tests should pass.

## Project Structure

| File | Purpose |
|------|---------|
| `agent.py` | Core logic for mock demo — `score_lead`, `draft_outreach`, `MOCK_COMPANIES` |
| `bounty_leadgen_agent.py` | Streamlit UI for mock demo (3D Hyperrealism CSS) |
| `lqa_agent.py` | Core logic for Places API demo — dual-backend `search_places` (Google + SerpAPI), `normalize_place`, `score_lead`, `draft_outreach` |
| `lead_qualification_agent.py` | Streamlit UI for Places API demo (both API key inputs, backend label) |
| `test_agent.py` | 35 unit tests for `agent.py` |
| `test_ui.py` | 31 UI tests for `bounty_leadgen_agent.py` |
| `test_lqa_agent.py` | 30 unit tests for `lqa_agent.py` |
| `test_lqa_ui.py` | 24 UI tests for `lead_qualification_agent.py` |
| `requirements.txt` | Dependencies |
| `documentation.md` | Full documentation (27 sections) |

## How It Works

### Pipeline

1. **Bounty intake** — Buyer sets acceptance criteria (industry, headcount range, signal keyword, quantity, minimum confidence)
2. **Prospecting** — Agent scans the candidate pool (mock companies or live search via Google Places API + SerpAPI fallback)
3. **Qualification scoring** — Each company is scored against the criteria using 4 weighted checks
4. **Shortlist** — Companies above the confidence threshold are presented with outreach drafts
5. **Verifier verdict** — PASS if the requested number of leads qualified; PARTIAL if fewer met the bar

### The evidence package

Every qualified lead ships with a per-field evidence record that an independent verifier could re-check. This is what makes the outcome auditable — a buyer can confirm each claim without trusting the agent's self-report.

### Honest gap

The current "verifier" re-uses the same `qualified` list that scoring produced, rather than re-deriving from raw evidence independently. A real production oracle would run as a **separate service** with its own data access path. See the [Documentation](documentation.md) for the full discussion (Section 15).

## Author

**Shamique Khan**

---

*Built to demonstrate that outcome-based AI marketplaces need verifiable, auditable evidence — not self-reported claims.*
