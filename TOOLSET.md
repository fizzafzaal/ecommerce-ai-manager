# TOOLSET.md — Tech Stack & Memory Budget

Every tool here is free, open-source, CPU-friendly, and chosen to fit an 8GB laptop with no GPU. Do not swap anything for a heavier alternative without telling me why and getting a "yes."

---

## THE STACK

| Layer | Tool | Why this one |
|---|---|---|
| Language | Python 3.11+ | Standard for AI, everything below supports it |
| Backend/API | FastAPI + Uvicorn | Lightweight, async, auto Swagger docs at `/docs` |
| Database | **SQLite** (via SQLAlchemy) | Zero setup, one file, no server to install/run. Replaces PostgreSQL to save hours and RAM on a 3-day build. |
| ORM | SQLAlchemy 2.x | Safe parameterized queries (no SQL injection), clean models |
| Vector DB | ChromaDB | In-process, no server, tiny footprint |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | 80MB, CPU-fast, good enough for product search |
| LLM runtime | Ollama | Simplest way to run local models; one command to pull/run |
| LLM model | **phi-2** (2.7B, quantized) | ~2GB RAM, fastest usable option on your hardware |
| Frontend | Streamlit | Pure Python UI, no JavaScript/Node, fast to build |
| Data faking | Faker | Generates realistic mock customers/orders |
| Config | python-dotenv | Loads settings from `.env` |
| Logging | loguru | One-line nicer logging |
| Tests | pytest | Standard, lightweight |
| Version control | Git + GitHub | Checkpoints and submission |

**Deliberately NOT used** (and why): PostgreSQL (server overhead — SQLite is enough here), CrewAI (heavier RAM than a plain router), React/Node (build step + RAM — Streamlit is enough), Docker (RAM overhead we can't spare), Redis/Celery (unnecessary for this scale), mistral-7b (too big — see below), any paid API.

---

## MEMORY BUDGET (the number that keeps this project alive)

You have **7.78GB usable**. Aim to stay under **7GB** to leave the OS breathing room.

| What's running | Approx RAM |
|---|---|
| Windows + background | ~1.5 GB |
| SQLite (in-process) | ~50 MB |
| ChromaDB | ~200 MB |
| FastAPI app | ~300 MB |
| Embedding model (MiniLM) | ~150 MB |
| **phi-2 loaded** | **~2 GB** |
| **Running total** | **~4.2 GB** ✅ leaves ~3.5GB headroom |

Compare with the model we are NOT using:

| With mistral-7b instead | Approx RAM |
|---|---|
| Everything above minus phi-2 | ~2.2 GB |
| **mistral-7b-q4 loaded** | **~4.2 GB** |
| **Running total** | **~6.4 GB** ⚠️ almost no headroom → crash risk |

**Rules that come from this table:**
- Only **one** LLM loaded at a time. Never run two models.
- `MAX_TOKENS = 256`. Longer replies use more memory and take much longer.
- Close Chrome/other apps while developing and demoing.
- If RAM approaches ~7GB, stop and tell me before continuing.

---

## PERFORMANCE EXPECTATIONS (so we're not surprised)

- Intent detection / short reply: a few seconds.
- Full formatted response through the LLM: **10–20 seconds** on CPU. This is normal for phi-2 on your laptop — it is not a bug.
- Always show a spinner/"thinking..." in the UI so it never looks frozen.
- Embedding all 40 products: one-time, ~30 seconds.
- Product search after that: well under a second.

---

## SETTINGS TEMPLATE (`.env.example`)

```
# Database (SQLite file, no server needed)
DATABASE_URL=sqlite:///./ecommerce.db

# Ollama / LLM
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=phi-2
MAX_TOKENS=256
LLM_TIMEOUT_SECONDS=45

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# App
ENVIRONMENT=development
```

---

## INSTALL ORDER (Day 1)

1. Python 3.11+ — confirm with `python --version`.
2. Ollama — download from ollama.com, then `ollama pull phi-2`.
3. Project deps — `pip install -r requirements.txt` inside `venv`.

**`requirements.txt` starting point** (Claude Code should pin versions when it creates the file):
```
fastapi
uvicorn
sqlalchemy
pydantic
pydantic-settings
python-dotenv
chromadb
sentence-transformers
ollama
faker
loguru
streamlit
pytest
```

---

## FALLBACK PLAN (if phi-2 is too slow or unstable)

In order, try:
1. Shorten prompts and drop `MAX_TOKENS` to 128.
2. Use the LLM **only** for intent detection and final wording; do everything else with rules and DB queries (this is already the design).
3. Last resort: replace intent detection with pure keyword matching and skip the LLM entirely — the product search + refund rules still work without it, so the app stays demoable.

The architecture is intentionally built so that if the LLM has to be switched off, the system still runs.
