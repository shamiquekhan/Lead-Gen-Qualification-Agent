# Lead Qualification Agent

**A reference implementation of an outcome-based AI marketplace agent**, built to demonstrate [Bounty](https://trybounty.ai)'s "pay for verified outcomes, not AI outputs" model.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)

---

## The Core Idea

Most lead-gen agents **self-grade** — the agent that finds the leads is also the agent that decides whether they qualify. "5 qualified leads delivered" is just a sentence the model generated, with nothing behind it a buyer could check.

This project demonstrates an alternative: **every lead carries an auditable evidence record** — which criterion matched, what the matching value was, and where it came from — **before** any pass/fail verdict is rendered. The verdict step doesn't trust the scoring step; it re-derives the same checks and reports honestly when the shortlist falls short, instead of padding it to hit a quota.

The scoring table is shown **before** filtering (rejects included), and the verdict is willing to report **partial pass** rather than silently inflating results.

## Live Places demo (dual backend)

The app tries **Google Places API** first. If it fails or no Google key is given, it falls back to **SerpAPI** (set via `SERPAPI_API_KEY` env var).

```bash
pip install -r requirements.txt
streamlit run lead_qualification_agent.py
```

Set API keys via environment variables or the UI inputs:
- `GOOGLE_PLACES_API_KEY` — optional, enables Google Places API
- `SERPAPI_API_KEY` — fallback backend

### Run the tests

```bash
python -m pytest test_lqa_agent.py test_lqa_ui.py -v
```

## Project Structure

| File | Purpose |
|------|---------|
| `lqa_agent.py` | Core logic — dual-backend `search_places` (Google + SerpAPI), `normalize_place`, `score_lead`, `draft_outreach` |
| `lead_qualification_agent.py` | Streamlit UI (both API key inputs, backend label) |
| `test_lqa_agent.py` | 30 unit tests for `lqa_agent.py` |
| `test_lqa_ui.py` | 24 UI tests for `lead_qualification_agent.py` |
| `requirements.txt` | Dependencies |
| `documentation.md` | Full documentation |

## How It Works

### Pipeline

1. **Bounty intake** — Buyer sets acceptance criteria (good/service, location, minimum confidence, quantity)
2. **Prospecting** — Agent searches live via Google Places API + SerpAPI fallback
3. **Qualification scoring** — Each business is scored against the criteria using 4 weighted checks
4. **Shortlist** — Businesses above the confidence threshold are presented with outreach drafts
5. **Verifier verdict** — PASS if the requested number of leads qualified; PARTIAL if fewer met the bar

### The evidence package

Every qualified lead ships with a per-field evidence record that an independent verifier could re-check. This is what makes the outcome auditable — a buyer can confirm each claim without trusting the agent's self-report.

### Honest gap

The current "verifier" re-uses the same `qualified` list that scoring produced, rather than re-deriving from raw evidence independently. A real production oracle would run as a **separate service** with its own data access path. See the [Documentation](documentation.md) for the full discussion.

## Author

**Shamique Khan**

---

*Built to demonstrate that outcome-based AI marketplaces need verifiable, auditable evidence — not self-reported claims.*
