# ShopSphere — E-Commerce AI Manager

A full e-commerce web app with an **agentic AI assistant** built in. Customers
can sign up, browse a product catalogue with images, add to cart, place orders,
track deliveries, download invoices, and chat with an AI that can search
products, look up their orders, process refunds, and write marketing copy.

The AI is **agentic**: a large language model orchestrates specialist agents
(product, refund, marketing) as *tools*, but every **business decision**
(refund eligibility, stock, prices, invoice authenticity) is made by **Python
rules on real database data** — so the AI can't hallucinate an approval or
invent a number. It also **degrades gracefully**: online it uses a fast cloud
model (Groq); offline it falls back to a local model (phi via Ollama).

Built as a university Final Year Project.

---

## Features

**Storefront (React)**
- Sign up / log in (creates a real customer record; no password security — demo only)
- Browse products by category, with real photos and live stock
- Product detail pages, with an AI **"Generate description"** button
- Server-side cart, checkout (decrements stock transactionally), order history
- **Order tracking** — Placed → Processing → Shipped → Delivered, advancing by real elapsed time, with an estimated delivery
- **Order detail page** with a visual tracking timeline
- **Downloadable invoices** (generated as images)
- **Invoice verification** — upload an invoice image; it's verified against the database

**AI Assistant (chat)**
- Understands free-form messages ("do you have warm jackets under $70?", "where's my order #5?", "refund my kettle", "write a fun ad for the puffer jacket")
- Remembers the conversation (multi-turn: "yes, refund it")
- Uses the specialist agents as tools; renders replies as rich markdown

---

## Architecture

```
                      React storefront (Vite)         Streamlit (backup chat UI)
                              │  HTTP                         │
                              ▼                               ▼
                    ┌──────────────────────────  FastAPI  ──────────────────────────┐
                    │  /products /cart /orders /orders/{id}/invoice /verify-invoice  │
                    │  /signup /login /chat ...                                       │
                    └───────────────────────────────┬───────────────────────────────┘
                                                     │ POST /chat
                                          ┌──────────▼───────────┐
                                          │  Agent Orchestrator  │   ← Groq LLM (the brain)
                                          │  (LLM + tool-calling)│      decides which tool to call
                                          └───┬────────┬─────────┘
                        search_products │ get_my_orders │ request_refund │ write_marketing_copy
                                        ▼        ▼        ▼        ▼
                              ┌─────────┐ ┌─────────┐ ┌──────────┐
                              │ Product │ │ Refund  │ │Marketing │   ← specialist agents (tools)
                              │  Agent  │ │  Agent  │ │  Agent   │
                              └────┬────┘ └────┬────┘ └────┬─────┘
                                   ▼           ▼           ▼
                              ChromaDB      SQLite       Groq/phi
                            (semantic     (rules +      (copywriting)
                             search)      decisions)

  Offline fallback: if Groq is unreachable, /chat uses a local deterministic
  router (app/orchestrator.py) with the Support Agent + phi (via Ollama).

  Invoice verification: Tesseract OCR reads the uploaded image; Python checks
  the extracted order number + total against the database.
```

**Key principle — AI reads/orchestrates, rules decide.** The LLM chooses tools
and phrases replies; refund eligibility, stock, prices, and invoice
authenticity are computed in Python against the database. The customer id is
injected server-side, never by the model, so the AI can't reach another
customer's data.

---

## Tech stack

| Layer | Tool |
|---|---|
| Storefront | **React** (Vite), React Router, react-markdown |
| Backup chat UI | **Streamlit** |
| Backend / API | **FastAPI** + Uvicorn |
| Database | **SQLite** via SQLAlchemy 2.x |
| Product search | **ChromaDB** + `all-MiniLM-L6-v2` embeddings (sentence-transformers) |
| Cloud AI (chat brain) | **Groq** (`openai/gpt-oss-20b`) with tool-calling |
| Local AI (offline fallback) | **phi** via **Ollama** |
| Invoice OCR | **Tesseract** (pytesseract) |
| Invoice / image rendering | **Pillow** |
| Mock data | Faker |
| Tests | pytest |

Languages: Python (backend), JavaScript (frontend), SQL (via ORM), HTML/CSS.

---

## Setup

**Prerequisites**
- Python 3.10+
- Node.js 18+ (for the React storefront)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) — `winget install UB-Mannheim.TesseractOCR` (for invoice verification)
- A free **Groq API key** — https://console.groq.com (for the smart assistant)
- *(Optional)* [Ollama](https://ollama.com) + `ollama pull phi` — only for the offline fallback

**Steps**
```bash
# 1. Python environment
python -m venv venv
venv\Scripts\activate                 # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

# 2. Settings — copy the template and add your key
copy .env.example .env                # then set GROQ_API_KEY=... in .env

# 3. Seed the database (customers, products, orders)
python -m app.seed

# 4. Build the product search index (embeds the 40 products, once)
python -m app.vector_store

# 5. Install the storefront's dependencies
cd storefront
npm install
cd ..
```

---

## Running it

Two processes: the **backend** and the **storefront**.

```bash
# Terminal 1 — backend API (http://localhost:8000, docs at /docs)
uvicorn app.main:app

# Terminal 2 — React storefront (http://localhost:5173)
cd storefront
npm run dev
```

Open **http://localhost:5173**, sign up, and explore.

**Backup Streamlit chat UI** (optional, simpler): `streamlit run frontend/chat_app.py`

### Things to try
- Sign up as yourself → browse → add to cart → checkout → **My Orders** → open an order (tracking timeline) → **Download invoice**.
- **Verify Invoice** page → upload that invoice → *verified*; edit its total and re-upload → *not verified*; upload any other photo → *not recognized*.
- **AI Assistant** → "what have I ordered?", "where's my order #5?", "show me warm jackets under $70", "write a playful ad for the air fryer".

---

## Configuration (.env)

| Setting | Purpose |
|---|---|
| `GROQ_API_KEY` | Enables the smart cloud assistant (falls back to phi if unset) |
| `GROQ_MODEL` | Groq model (default `openai/gpt-oss-20b`) |
| `USE_LLM` | `false` = safe mode: no local model, keyword routing only |
| `SHIP_AFTER_HOURS` / `DELIVER_AFTER_HOURS` | When an order becomes Shipped / Delivered (default 3h / 5h; lower to demo tracking live) |

---

## Tests

```bash
pytest -q
```
Tests avoid the LLM (fast, repeatable) and clean up their own data, so they
never disturb the seeded demo data.

---

## Project structure

```
ecommerce-ai-manager/
├── app/                          # backend (FastAPI)
│   ├── main.py                   # API endpoints
│   ├── config.py                 # settings (.env)
│   ├── database.py  models.py  schemas.py
│   ├── agent_orchestrator.py     # Groq LLM + tool-calling (primary brain)
│   ├── orchestrator.py           # deterministic router (offline fallback)
│   ├── llm.py                    # Ollama/phi + Groq text helpers
│   ├── vector_store.py           # ChromaDB semantic search
│   ├── invoice.py                # invoice image generation (Pillow)
│   ├── invoice_verifier.py       # OCR + DB verification
│   ├── tracking.py               # order tracking stages
│   ├── seed.py                   # mock data
│   └── agents/
│       ├── base_agent.py         # shared parent (timeout, logging, fallback)
│       ├── support_agent.py      # intent / FAQ / small-talk (fallback path)
│       ├── refund_agent.py       # refund rules + order lookup
│       ├── product_agent.py      # semantic search + stock
│       └── marketing_agent.py    # product marketing copy
├── storefront/                   # React app (Vite)
│   └── src/  (pages/, components/, context/, api.js)
├── frontend/
│   └── chat_app.py               # Streamlit backup chat UI
├── tests/test_agents.py
├── requirements.txt   .env.example   run_demo.bat   stop_demo.bat
```

---

## Notes & limitations

- **The AI assistant needs internet** (Groq). Offline, it falls back to the local phi model automatically.
- **Invoice verification needs Tesseract installed.** It reads clean generated invoices very accurately; heavily blurred phone photos may read less reliably.
- **Login is visual only** — no real authentication/passwords; signup just creates a customer record.
- **Order tracking is time-derived** (not a real courier) and progresses on a configurable timer.
- **No real payments or shipping integrations** — out of scope.
```
