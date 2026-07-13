# Verified Lead-Gen & Qualification Agent

**A reference implementation of an outcome-based AI marketplace agent**, built to demonstrate [Bounty](https://trybounty.ai)'s "pay for verified outcomes, not AI outputs" model.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.59.2-red)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/tests-35%20passing-brightgreen)](test_agent.py)

---

## The Core Idea

Most lead-gen agents **self-grade** — the agent that finds the leads is also the agent that decides whether they qualify. "5 qualified leads delivered" is just a sentence the model generated, with nothing behind it a buyer could check.

This project demonstrates an alternative: **every lead carries an auditable evidence record** — which criterion matched, what the matching value was, and where it came from — **before** any pass/fail verdict is rendered. The verdict step doesn't trust the scoring step; it re-derives the same checks and reports honestly when the shortlist falls short, instead of padding it to hit a quota.

The scoring table is shown **before** filtering (rejects included), and the verdict is willing to report **partial pass** rather than silently inflating results.

## Quick Start

```bash
# Clone and enter
git clone https://github.com/shamiquekhan/Lead-Gen-Qualification-Agent.git
cd Lead-Gen-Qualification-Agent

# Set up environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install streamlit pandas

# Run the app
streamlit run bounty_leadgen_agent.py
```

Then open **http://localhost:8501** in your browser. Set your acceptance criteria and click **Run bounty**.

### Run the tests

```bash
python -m pytest test_agent.py -v
```

All 35 tests should pass.

## Project Structure

```
agent.py                  # Core logic — scoring, outreach, mock data (101 lines)
bounty_leadgen_agent.py   # Streamlit entrypoint — UI, neumorphism CSS, orchestration (760 lines)
test_agent.py             # 35 unit & integration tests (347 lines)
requirements.txt          # Pinned dependencies (streamlit==1.59.2, pandas==3.0.3)
BUILD_GUIDE.md            # Full build documentation (this is the primary reference)
README.md                 # This file
```

**Why two files?** `agent.py` contains only pure functions (`score_lead`, `draft_outreach`) and the mock data (`MOCK_COMPANIES`) — no Streamlit or IO dependencies. This makes it importable and testable in a standard `pytest` run without a Streamlit runtime. The UI layer lives in `bounty_leadgen_agent.py`, which adds ~500 lines of inlined neumorphism CSS for the visual design.

## How It Works

### Pipeline

1. **Bounty intake** — Buyer sets acceptance criteria (industry, headcount range, signal keyword, quantity, minimum confidence)
2. **Prospecting** — Agent scans the candidate pool (currently 12 mock companies; replace with a real API in production)
3. **Qualification scoring** — Each company is scored against the criteria using 4 weighted checks:

   | Check | Weight | Logic |
   |---|---|---|
   | Industry | 0.3 | Exact match, or always pass if "Any" |
   | Headcount | 0.2 | Within selected range |
   | Signal | 0.4 | Case-insensitive keyword match in recent activity |
   | Contact | 0.1 | Contact info found (not "unknown") |

4. **Shortlist** — Companies above the confidence threshold are presented with outreach drafts
5. **Verifier verdict** — PASS if the requested number of leads qualified; PARTIAL if fewer met the bar

### The evidence package

Every qualified lead ships with a per-field evidence record that an independent verifier could re-check:

```
PASS  industry:  SaaS
PASS  headcount: 85 employees
PASS  signal:    Posted 3 AI/ML engineering roles in the last 30 days
PASS  contact:   Priya Menon, Head of Growth
```

**Source:** northwindanalytics.com/careers

This is what makes the outcome auditable — a buyer can confirm each claim without trusting the agent's self-report.

### Honest gap

The current "verifier" re-uses the same `qualified` list that scoring produced, rather than re-deriving from raw evidence independently. A real production oracle would run as a **separate service** with its own data access path. See the [BUILD_GUIDE](BUILD_GUIDE.md) for the full discussion (Section 15).

## Technology Stack

| Technology | Why |
|---|---|
| **Python** | Fastest path to a working demo; ecosystem fit for future ML scoring |
| **Streamlit** + 500 lines of neumorphism CSS | Zero front-end setup, polished visual design (embossed cards, inset inputs, pill buttons) |
| **Pandas** | Clean tabular rendering of the scoring table |
| **Mock data** (12 dicts) | Deterministic, offline, zero API keys needed — swap for a real prospecting API later |

## Build Guide

The **[BUILD_GUIDE.md](BUILD_GUIDE.md)** is the primary documentation — 27 sections covering everything from product philosophy to production upgrade paths, security, testing strategy, and a full FAQ. This README is just the entry point.

## Author

**Shamique Khan**

---

*Built to demonstrate that outcome-based AI marketplaces need verifiable, auditable evidence — not self-reported claims.*
