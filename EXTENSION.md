# EXTENSION.md — Storefront Phase

This file extends the completed MVP. Read it alongside CLAUDE.md, WORKFLOW.md, and TOOLSET.md. Those files still apply — this one adds the next phase. Where this file and the older ones agree (hardware limits, "ask before you execute", one-step-at-a-time, commit often), the rules stay exactly the same.

---

## 1. WHAT WE'RE BUILDING (and what already exists)

The MVP is **done and working**: a FastAPI + SQLite backend with 3 agents (Support, Refund, Product), a deterministic router, semantic product search (ChromaDB), a seeded database, and endpoints `GET /health`, `POST /chat`, `GET /customers`. There is also a working Streamlit chat app.

This phase turns that backend into a **real-looking retail website**: a customer can "log in" (visuals only — see §4), browse products by category, view a product, add items to a cart, and place an order. The existing AI chat becomes **one page** inside this new site (the "AI Assistant" page).

**The backend logic is finished and must not be rewritten.** We are adding a few new endpoints and a new frontend. The agents, router, refund rules, and search stay as they are.

---

## 2. THE GOLDEN RULE OF THIS PHASE

**The backend is safe. The frontend is new.** Everything valuable already built (agents, router, rules, search, database, existing endpoints) is backend and runs independently of any UI. The new React frontend talks to the backend over HTTP only — exactly like the Streamlit app does. It **cannot** damage the backend logic. The worst case for any frontend mistake is a broken page, never broken agents.

Two consequences:
- **Do NOT delete or break the Streamlit app.** It is our fallback for the demo. Keep it running. Build React alongside it, not on top of it.
- New backend endpoints must be **added**, never rewrites of existing ones. If an existing endpoint seems to need changing, stop and explain why before touching it.

---

## 3. FRONTEND DECISION: REACT

The new storefront is built in **React**, not Streamlit. Reason: a shopping site (product grids, a live cart, page navigation, a login screen, a polished look) is what React is designed for, and it's the current Streamlit UI's ceiling that we're trying to break past.

Guardrails, because the laptop is still 8GB with no GPU:
- Keep it a **single-page React app** (e.g. Vite + React). No Next.js, no server-side rendering, no heavy meta-framework — that's RAM and complexity we don't need.
- Styling: **Tailwind CSS** or plain CSS. No large component libraries unless there's a clear reason.
- The React app is **static frontend only**. It holds no business logic and no database access. It calls the FastAPI backend for everything. All decisions (prices, stock, orders, refunds) stay in the backend.
- The dev server (Vite) and the Python backend run as two separate processes. That's normal and fine on 8GB — just don't also run a second LLM at the same time.
- I'm new to React. Add short comments and tell me how to run and check each page.

**Appearance:** I want it to look like a clean modern store, not a data app. When building UI, aim for a tidy product grid, clear category navigation, a visible cart, and a simple login screen. I'll describe the look or share a reference; ask me if the style is unclear rather than guessing.

---

## 4. LOGIN IS VISUALS ONLY

No real authentication. No password checking, no sessions, no security layer. The login **page** has email/password fields and a "Sign in" button purely for appearance. On submit, it just picks which existing customer we're shopping as (reuse `GET /customers`) and enters the store.

Do not build password hashing, JWT, OAuth, or any auth infrastructure. If real auth ever comes, it's a separate future phase. Keeping this fake avoids a security rabbit hole and saves time.

---

## 5. NEW BACKEND ENDPOINTS TO ADD

Add these to the existing FastAPI app. Each one: validate input, validate output with a Pydantic schema, meaningful status codes, error handling, and it reads/writes the **existing** SQLite tables. No new database engine — still SQLite.

**Products & browsing**
- `GET /products` — list products; support optional `?category=` and `?search=` query params.
- `GET /products/{id}` — one product's full details, including live stock.
- `GET /categories` — the list of distinct categories (for the nav/filter).

**Cart** (keep it simple — cart can live in the frontend's state, but these help if we want it server-side)
- If we do server-side cart: `POST /cart` / `GET /cart` / `DELETE /cart/{item}`. Decide with me first — a frontend-only cart may be simpler and is fine for an FYP.

**Orders**
- `POST /orders` — place an order: takes a customer id + list of product ids/quantities, checks stock via existing rules, decrements inventory in a transaction, creates an order + order items, returns an order summary.
- `GET /orders?customer_id=` — a customer's order history (nice for an "My Orders" page).

**Reused as-is (do not modify)**
- `GET /customers` — powers the fake login dropdown.
- `POST /chat` — powers the AI Assistant page.
- `GET /health`.

Rules that still hold from the MVP: **rules and DB for decisions, LLM only for language.** Order placement and stock changes are pure Python + SQL in a transaction — never an LLM call. Every write to inventory/orders is transactional so stock can't go negative or double-count.

---

## 6. PAGES IN THE NEW SITE

Build these one at a time, in this order. Each must work and be committed before the next.

1. **Login page** — fake login (§4), lands you in the store.
2. **Home / storefront** — product grid, category navigation, cart icon with count.
3. **Product page** — one product's details, "Add to cart" button, stock shown.
4. **Cart page** — items, quantities, total, "Place order" button → calls `POST /orders`.
5. **Order confirmation / My Orders** — shows the placed order (and optionally history via `GET /orders`).
6. **AI Assistant page** — the existing chat, now a page in the site. Calls `POST /chat`. This is mostly done — it's the same interaction the Streamlit app already does, just rebuilt as a React page.

The AI page is deliberately last-ish because it's the lowest-risk: the endpoint behind it already works and is tested.

---

## 7. BUILD ORDER (stages, not days)

No timelines — just a safe sequence where the project runs at every checkpoint.

**Stage A — Backend endpoints first.** The storefront is useless without data to show. Add the `/products`, `/categories`, `/orders` endpoints. Test each with `/docs` or curl before any UI exists. Commit each.

**Stage B — React skeleton.** Get a bare Vite + React app running that can fetch `/products` and print them as raw text. Ugly is fine — this proves the frontend can reach the backend. Commit.

**Stage C — Pages, one at a time,** in the §6 order. Each page: build it, wire it to its endpoint, test it in the browser, commit. Do not start the next page until the current one works.

**Stage D — Styling pass.** Once the pages function, make it look like a real store (Tailwind/CSS, product-grid polish, consistent header/nav/cart). Function first, looks second — a pretty page that doesn't work helps no one.

**Stage E — Fold in the AI page** and do a full click-through: log in → browse → add to cart → place order → check order → ask the AI something.

**Throughout:** the Streamlit app and all existing endpoints keep working. If anything existing breaks, stop and fix before continuing.

---

## 8. SUCCESS CRITERIA FOR THIS PHASE

**Must be true:**
- [ ] Existing backend still works unchanged (agents, `/chat`, `/customers`, tests still pass).
- [ ] Streamlit fallback still runs.
- [ ] New endpoints (`/products`, `/categories`, `/orders`) work and are tested.
- [ ] React site: fake login → browse by category → open a product → add to cart → place an order → see confirmation.
- [ ] Placing an order decrements stock in the database, transactionally.
- [ ] The AI Assistant page works inside the new site.
- [ ] It looks like a clean modern store, not a data app.
- [ ] RAM stays under ~7GB (don't run a second LLM while both servers are up).

**Nice to have (only if ahead):**
- [ ] Order history page.
- [ ] Cart persists on refresh.
- [ ] Search bar on the storefront (reuses `/products?search=`).

**Still explicitly out of scope:**
- Real authentication/passwords, real payments, shipping, Docker/cloud deploy, admin dashboard. All future phases.

---

## 9. COMMUNICATION (unchanged from CLAUDE.md, restated because it matters)

- **Ask before you execute** anything that installs, deletes, overwrites files, or changes the database.
- **One component at a time**, tested and committed before moving on.
- Before each step: tell me what you'll build, why, which files change, and any risk.
- After each step: tell me what changed, what's left, and commit.
- If React setup or anything else looks like it'll be heavy on the laptop, warn me **before** running it.
- If you spot a cleaner approach than this file describes, stop and explain the trade-off before changing course.
