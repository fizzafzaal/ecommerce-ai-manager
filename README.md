# E-Commerce AI Manager

A multi-agent AI system for e-commerce operations. Specialized agents handle
customer support, refunds, and product search, coordinated by a **deterministic
(non-LLM) router**. A local language model (phi-2 via Ollama) is used only for
understanding language and writing friendly text — never for business decisions
like approving a refund. Everything runs locally on CPU, with no paid APIs.

Built as a university Final Year Project, designed to run on a modest laptop
(8GB RAM, no GPU).

---

## What it does

- **Customer support** — detects what the customer wants (refund, product
  search, FAQ) and answers common questions directly.
- **Refunds** — decides eligibility with fixed business rules (order exists,
  belongs to the customer, within 30 days, not already refunded) and updates
  the database in a transaction.
- **Product search** — semantic search over the product catalogue ("warm
  jacket" finds coats and jackets), with live stock levels and low-stock flags.

A single request can combine actions, e.g. *"I want a refund for order #1 and
see similar items"* returns a refund decision **and** a product list in one
reply.

---

## Architecture

```
          ┌─────────────┐
User ───► │  Streamlit  │  (chat UI, talks to the API over HTTP)
          └──────┬──────┘
                 │  POST /chat
          ┌──────▼──────┐
          │   FastAPI   │  (/health, /chat, /customers)
          └──────┬──────┘
                 │
          ┌──────▼───────┐
          │ Orchestrator │  ← deterministic router (plain Python, NOT an LLM)
          └──┬───────┬───┘
             │       │
   ┌─────────▼─┐  ┌──▼────────┐  ┌────────────┐
   │  Support  │  │  Refund   │  │  Product   │
   │  Agent    │  │  Agent    │  │  Agent     │
   └─────┬─────┘  └─────┬─────┘  └─────┬──────┘
         │              │              │
      phi (LLM)      SQLite         ChromaDB
   intent + wording  (rules)     (semantic search)
```

**Key design principle:** the LLM detects intent and phrases replies; **rules
and database queries make every decision**. This prevents hallucinated refund
approvals or invented stock numbers — all facts in a reply come straight from
the database.

The system also degrades gracefully: every LLM call has a timeout and a
fallback, and if the model is slow or unavailable, intent detection falls back
to keyword matching and replies fall back to plain (still correct) text.

---

## Tech stack

| Layer | Tool |
|---|---|
| Backend / API | FastAPI + Uvicorn |
| Database | SQLite via SQLAlchemy 2.x |
| Vector search | ChromaDB + `all-MiniLM-L6-v2` embeddings |
| LLM runtime | Ollama running **phi-2** (CPU, ~2GB RAM) |
| Frontend | Streamlit |
| Mock data | Faker |
| Tests | pytest |

Everything is free, open-source, and CPU-only.

---

## Setup

**Prerequisites:** Python 3.10+, and [Ollama](https://ollama.com) installed.

1. **Create the virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   venv\Scripts\activate            # Windows
   # source venv/bin/activate       # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Pull the language model** (once, ~1.6GB download):
   ```bash
   ollama pull phi
   ```

3. **Create your settings file** by copying the template:
   ```bash
   copy .env.example .env           # Windows
   # cp .env.example .env           # macOS/Linux
   ```

4. **Seed the database** with mock data (customers, products, orders, refunds):
   ```bash
   python -m app.seed
   ```

5. **Build the product search index** (embeds the 40 products, ~30s once):
   ```bash
   python -m app.vector_store
   ```

---

## Running it

### Easiest: one-click launcher (Windows)

Double-click **`run_demo.bat`**. It starts Ollama if needed, pre-warms the
model so the first reply is fast, launches the backend and the chat UI, and
opens your browser. To shut everything down, double-click **`stop_demo.bat`**.

### Manual (two terminals)

You need **two terminals** (both with the venv activated), and Ollama running.

**Terminal 1 — the backend API:**
```bash
uvicorn app.main:app
```
Interactive API docs are then at http://localhost:8000/docs

**Terminal 2 — the chat UI:**
```bash
streamlit run frontend/chat_app.py
```
Then open http://localhost:8501, pick a customer, and start chatting.

**Tip:** pre-warm the model first so your first reply isn't a slow cold start:
```bash
python -m app.warmup
```

### Things to try
Pick **customer #1** in the sidebar, then send:
- `what is your return policy?` — instant FAQ answer
- `do you have any warm winter jackets?` — product search
- `I want a refund for order #1` — refund **approved**
- `I want a refund for order #16` — refund **rejected** (outside 30-day window)

---

## Running the tests

```bash
pytest -q
```
The tests avoid the LLM (so they're fast and repeatable) and clean up after
themselves, so they never disturb the seeded demo data.

---

## Safe mode (low-memory fallback)

If you ever need to run with minimal memory — or Ollama isn't available — set
`USE_LLM=false` in `.env`. The system then skips the language model entirely:

- **Unchanged:** refund decisions, product search, stock, and FAQ answers —
  none of these ever used the LLM.
- **Simpler:** intent detection uses keyword matching, and replies use plain
  (still correct) wording instead of the LLM-written friendly opener.

This drops peak memory from ~6.8GB to ~4.5GB. It's a fallback — the default is
full quality (`USE_LLM=true`).

---

## Known limitations

These are deliberate trade-offs for a 3-day build on modest hardware:

- **Replies take ~10–40 seconds.** phi-2 runs on CPU; the first reply after
  startup is slowest because the model loads into memory. This is expected, not
  a bug — the UI shows a "Thinking..." spinner.
- **Small model.** phi-2 sometimes phrases things oddly. Because it never makes
  decisions, this only affects wording, never correctness.
- **Close other heavy apps (e.g. Chrome) while running.** The full stack
  (API + embeddings + phi + UI) uses ~6.8GB RAM. On an 8GB machine, a browser
  with many tabs can push you into swapping.
- **One order = one product.** Orders are single-item to keep the refund/stock
  logic simple. Multi-item orders are future work.
- **No authentication, payments, or real integrations.** Out of scope for the
  MVP.

---

## Project structure

```
ecommerce-ai-manager/
├── app/
│   ├── main.py           # FastAPI entry point (/health, /chat, /customers)
│   ├── config.py         # settings loaded from .env
│   ├── database.py       # SQLite + SQLAlchemy setup
│   ├── models.py         # database tables (ORM)
│   ├── schemas.py        # API request/response shapes (Pydantic)
│   ├── orchestrator.py   # deterministic router (NOT an LLM)
│   ├── llm.py            # single wrapper for all Ollama calls
│   ├── vector_store.py   # ChromaDB semantic search
│   ├── seed.py           # generate + insert mock data
│   └── agents/
│       ├── base_agent.py     # shared parent (timeout, logging, fallback)
│       ├── support_agent.py  # intent detection + FAQ
│       ├── refund_agent.py   # refund rules (deterministic)
│       └── product_agent.py  # semantic search + stock
├── frontend/
│   └── chat_app.py       # Streamlit chat UI
├── tests/
│   └── test_agents.py    # sanity tests
├── requirements.txt
└── .env.example
```
