# WORKFLOW.md — 3-Day Build Plan

The original plan was 1 month. This is the compressed 3-day version. It only works if we stay disciplined about scope. **Build in the exact order below.** Each block ends with a checkpoint: it must run before we move on. If a checkpoint fails and can't be fixed quickly, we cut the failing feature rather than blowing the schedule.

**Golden rule of these 3 days:** a working small thing at every checkpoint. Commit after each green checkpoint so we always have something to demo.

---

## PRIORITY ORDER (if time runs out, cut from the BOTTOM)

1. Environment + database + seed data  ← without this, nothing works
2. LLM wrapper working (Ollama + phi-2)  ← the core capability
3. Support Agent (intent detection)  ← the entry point
4. Refund Agent (rules)  ← the headline feature
5. Product Agent (search)  ← the second feature
6. Orchestrator wiring it together
7. Streamlit chat UI  ← so it's demoable
8. README + a couple of tests
9. Marketing Agent  ← FIRST thing to cut
10. Conversation memory / polish  ← SECOND thing to cut

If Day 3 evening arrives and you're at step 7, you have a demoable project. Steps 9–10 are bonuses.

---

## DAY 1 — Foundation & Core Capability

**Goal by end of day:** database seeded, and phi-2 answers a test prompt through our own code.

### Block 1.1 — Environment (ask before installing)
- Create `requirements.txt`, `setup_env.sh`, `.gitignore`, `.env.example`.
- Create and activate `venv`, install dependencies.
- Install Ollama, pull `phi-2`, confirm `ollama serve` runs.
- **Checkpoint:** `ollama run phi-2 "say hello"` returns text. `pip list` shows FastAPI, SQLAlchemy, chromadb, streamlit.
- Commit.

### Block 1.2 — Database + seed data
- `app/database.py` (SQLite + SQLAlchemy), `app/models.py` (tables: customers, products, inventory, orders, refunds, conversations, messages).
- `app/seed.py` generates mock data with Faker: ~15 customers, ~40 products, ~25 orders, ~8 refunds.
- **Ask before running the seed** (it writes to the DB).
- **Checkpoint:** open the SQLite file (or a quick query script) and see rows in every table.
- Commit.

### Block 1.3 — LLM wrapper
- `app/llm.py`: one function `ask_llm(prompt, max_tokens=256)` that calls Ollama with a timeout and a fallback string on error.
- `app/config.py` loads model name, token limit, DB path from `.env`.
- **Checkpoint:** a tiny script calls `ask_llm("Reply with the word OK")` and prints the reply. Watch RAM in Task Manager while it runs — confirm we stay under ~7GB.
- Commit.

**End-of-Day-1 state:** data exists, the model talks to us through our code, memory behaves. This is the riskiest day; if it's green, the rest is mostly wiring.

---

## DAY 2 — Agents & Orchestration

**Goal by end of day:** a request can go in as text and come out as a correct, routed response — tested from the command line (no UI yet).

### Block 2.1 — Base agent + Support Agent
- `app/agents/base_agent.py` (parent class: input, output dict, timeout, logging).
- `app/agents/support_agent.py`: detect intent (`refund` / `product_search` / `faq` / `unknown`) + extract entities. LLM first, keyword fallback.
- **Checkpoint:** feed 5 sample sentences, get correct intents.
- Commit.

### Block 2.2 — Refund Agent (rules only)
- `app/agents/refund_agent.py`: eligibility by rules (order exists, belongs to customer, within 30 days, not already refunded). Updates DB in a transaction. No LLM in the decision.
- **Checkpoint:** one eligible order → approved + DB updated; one 40-day-old order → rejected.
- Commit.

### Block 2.3 — Product Agent + vector store
- `app/vector_store.py`: ChromaDB collection, embed the 40 products once with `all-MiniLM-L6-v2`.
- `app/agents/product_agent.py`: semantic search + stock check + low-stock flag.
- **Ask before running** the one-time embedding build.
- **Checkpoint:** search "warm jacket" returns jacket-like products with stock info.
- Commit.

### Block 2.4 — Orchestrator
- `app/orchestrator.py`: intent → which agent(s) → run → merge → one final `ask_llm` call to phrase the reply.
- **Checkpoint:** from a script, send "I want to return order X and see similar items" → refund decision + product list in one combined reply.
- Commit.

**End-of-Day-2 state:** the brain works end to end in the terminal. Day 3 is mostly the face and the paperwork.

---

## DAY 3 — Interface, Docs, Buffer

**Goal by end of day:** something you can open, click, and demo, with a README.

### Block 3.1 — FastAPI endpoints
- `app/main.py`: `GET /health`, `POST /chat` (message in → orchestrator → reply out).
- **Checkpoint:** `/health` returns ok; `/chat` returns a reply via `/docs` or curl.
- Commit.

### Block 3.2 — Streamlit chat UI
- `frontend/chat_app.py`: pick a customer, type a message, see the reply. Calls `POST /chat`. Show a "thinking..." spinner (responses take 10–20s — that's expected).
- **Checkpoint:** full loop in the browser: type → wait → reply.
- Commit. **At this point you have a demoable project. Everything below is bonus.**

### Block 3.3 — Docs + tests
- `README.md`: what it is, how to install, how to run, known limits (slow inference, small model).
- `tests/test_agents.py`: a few sanity tests (intent detection, refund rule).
- Commit.

### Block 3.4 — BUFFER (leave this empty on purpose)
- Bug-fixing, RAM issues, or catch-up from Day 1/2 slippage.
- If genuinely ahead: build the Marketing Agent, or add conversation memory. Not before.

---

## Daily habits
- Start each day by telling me which block we're on.
- Watch RAM (Task Manager) whenever the LLM runs.
- Commit after every green checkpoint.
- If a block runs long, flag it immediately and we cut from the bottom of the priority list — we do not silently fall behind.
