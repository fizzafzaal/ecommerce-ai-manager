"""FastAPI entry point -- exposes the system over HTTP.

Two endpoints: a health check, and /chat which hands the message to the
orchestrator and returns its reply. The orchestrator (and the agents it
holds) is created once at startup and reused across requests.

Run with:
    uvicorn app.main:app --reload
Interactive docs are then at http://localhost:8000/docs
"""

from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import or_

from app.agent_orchestrator import AgentOrchestrator
from app.agents.marketing_agent import MarketingAgent
from app.agents.product_agent import LOW_STOCK_THRESHOLD
from app.config import settings
from app.database import SessionLocal
from app.models import CartItem, Customer, Order, OrderItem, Product
from app.orchestrator import Orchestrator
from app.schemas import (
    CartItemAdd,
    CartOut,
    ChatRequest,
    ChatResponse,
    CustomerSummary,
    HealthResponse,
    LoginRequest,
    MarketingResponse,
    OrderCreate,
    OrderItemOut,
    OrderOut,
    ProductOut,
    SignupRequest,
)

app = FastAPI(
    title="E-Commerce AI Manager",
    description="A multi-agent AI system for e-commerce support, refunds, and product search.",
    version="1.0.0",
)

# Allow the React dev server (Vite) to call this API from its own origin.
# The storefront runs on a different port during development, so without
# this the browser blocks its requests. Restricted to local dev origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Built once and reused -- agents hold model/DB handles we don't want to
# reconstruct on every request. When a Groq key is configured, the smart
# agentic orchestrator handles chat (delegating to the same specialist
# agents as tools) and falls back to the local one if Groq is unreachable.
marketing_agent = MarketingAgent()  # also exposed via POST /products/{id}/marketing
_local_orchestrator = Orchestrator()
if settings.groq_enabled:
    orchestrator = AgentOrchestrator(
        product_agent=_local_orchestrator.product_agent,
        refund_agent=_local_orchestrator.refund_agent,
        marketing_agent=marketing_agent,
        fallback=_local_orchestrator,
    )
    logger.info(f"Chat: using Groq agentic orchestrator ({settings.groq_model}); phi is the fallback.")
else:
    orchestrator = _local_orchestrator
    logger.info("Chat: Groq not configured; using the local phi orchestrator.")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness check -- confirms the API process is up."""
    return HealthResponse(status="ok")


@app.get("/customers", response_model=list[CustomerSummary])
def list_customers() -> list[CustomerSummary]:
    """Return all customers, so the UI can offer a real customer picker."""
    db = SessionLocal()
    try:
        customers = db.query(Customer).order_by(Customer.id).all()
        return [CustomerSummary(id=c.id, name=c.name) for c in customers]
    finally:
        db.close()


@app.post("/signup", response_model=CustomerSummary, status_code=201)
def signup(req: SignupRequest) -> CustomerSummary:
    """Register a new customer. Actually creates a customer row; the
    password is ignored (login is intentionally fake -- see EXTENSION.md).
    Rejects an email that's already registered."""
    db = SessionLocal()
    try:
        email = req.email.strip().lower()
        existing = db.query(Customer).filter(Customer.email == email).first()
        if existing:
            raise HTTPException(status_code=409, detail="That email is already registered.")
        customer = Customer(name=req.name.strip(), email=email)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return CustomerSummary(id=customer.id, name=customer.name)
    finally:
        db.close()


@app.post("/login", response_model=CustomerSummary)
def login(req: LoginRequest) -> CustomerSummary:
    """Log in by email only (no password check). Returns the matching
    customer, or 404 if no account has that email."""
    db = SessionLocal()
    try:
        email = req.email.strip().lower()
        customer = db.query(Customer).filter(Customer.email == email).first()
        if customer is None:
            raise HTTPException(status_code=404, detail="No account found with that email.")
        return CustomerSummary(id=customer.id, name=customer.name)
    finally:
        db.close()


def _to_product_out(product: Product) -> ProductOut:
    """Build the API view of a product, joining in its live stock level."""
    stock = product.inventory.stock_quantity if product.inventory else 0
    return ProductOut(
        id=product.id,
        name=product.name,
        description=product.description,
        category=product.category,
        price=product.price,
        stock=stock,
        low_stock=stock < LOW_STOCK_THRESHOLD,
        image_url=product.image_url,
    )


@app.get("/products", response_model=list[ProductOut])
def list_products(category: str | None = None, search: str | None = None) -> list[ProductOut]:
    """List products, optionally filtered by category and/or a text search
    over name and description (a plain storefront search, not the AI's
    semantic search)."""
    db = SessionLocal()
    try:
        query = db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        if search:
            like = f"%{search}%"
            query = query.filter(or_(Product.name.ilike(like), Product.description.ilike(like)))
        products = query.order_by(Product.id).all()
        return [_to_product_out(p) for p in products]
    finally:
        db.close()


@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int) -> ProductOut:
    """Return one product's full details, including live stock."""
    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found.")
        return _to_product_out(product)
    finally:
        db.close()


@app.post("/products/{product_id}/marketing", response_model=MarketingResponse)
def generate_marketing(product_id: int, style: str | None = None) -> MarketingResponse:
    """Generate marketing copy for a product via the Marketing Agent."""
    result = marketing_agent.run(product_id=product_id, style=style)
    if "marketing_copy" not in result:
        raise HTTPException(status_code=404, detail="Product not found.")
    return MarketingResponse(product=result["product"], marketing_copy=result["marketing_copy"])


@app.get("/categories", response_model=list[str])
def list_categories() -> list[str]:
    """Return the distinct product categories, for nav and filtering."""
    db = SessionLocal()
    try:
        rows = db.query(Product.category).distinct().order_by(Product.category).all()
        return [row[0] for row in rows]
    finally:
        db.close()


def _build_cart_out(db, customer_id: int) -> CartOut:
    """Assemble a customer's current cart with per-line and grand totals."""
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.customer_id == customer_id)
        .order_by(CartItem.id)
        .all()
    )
    items = []
    total = 0.0
    for ci in cart_items:
        line_total = round(ci.product.price * ci.quantity, 2)
        total += line_total
        items.append(
            {
                "id": ci.id,
                "product_id": ci.product_id,
                "name": ci.product.name,
                "price": ci.product.price,
                "quantity": ci.quantity,
                "line_total": line_total,
            }
        )
    return CartOut(items=items, total=round(total, 2))


@app.post("/cart", response_model=CartOut)
def add_to_cart(item: CartItemAdd) -> CartOut:
    """Add a product to a customer's cart. Adding a product already in the
    cart increases its quantity rather than creating a duplicate row."""
    db = SessionLocal()
    try:
        if db.get(Product, item.product_id) is None:
            raise HTTPException(status_code=404, detail="Product not found.")

        existing = (
            db.query(CartItem)
            .filter(
                CartItem.customer_id == item.customer_id,
                CartItem.product_id == item.product_id,
            )
            .first()
        )
        if existing:
            existing.quantity += item.quantity
        else:
            db.add(
                CartItem(
                    customer_id=item.customer_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                )
            )
        db.commit()
        return _build_cart_out(db, item.customer_id)
    finally:
        db.close()


@app.get("/cart", response_model=CartOut)
def get_cart(customer_id: int) -> CartOut:
    """Return a customer's current cart."""
    db = SessionLocal()
    try:
        return _build_cart_out(db, customer_id)
    finally:
        db.close()


@app.delete("/cart/{item_id}", response_model=CartOut)
def remove_from_cart(item_id: int) -> CartOut:
    """Remove one line from the cart and return the updated cart."""
    db = SessionLocal()
    try:
        cart_item = db.get(CartItem, item_id)
        if cart_item is None:
            raise HTTPException(status_code=404, detail="Cart item not found.")
        customer_id = cart_item.customer_id
        db.delete(cart_item)
        db.commit()
        return _build_cart_out(db, customer_id)
    finally:
        db.close()


def _to_order_out(order: Order) -> OrderOut:
    """Build the API view of an order from its ORM row and line items."""
    items = [
        OrderItemOut(
            product_id=it.product_id,
            name=it.product.name,
            quantity=it.quantity,
            unit_price=it.unit_price,
            line_total=round(it.unit_price * it.quantity, 2),
        )
        for it in order.items
    ]
    return OrderOut(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        order_date=order.order_date,
        total_amount=order.total_amount,
        items=items,
    )


@app.post("/orders", response_model=OrderOut, status_code=201)
def place_order(order_req: OrderCreate) -> OrderOut:
    """Place an order. Uses the explicit `items` list if given, otherwise
    the customer's cart. Stock is checked for every line first (all-or-
    nothing); on success, inventory is decremented, the order and its
    items are created in one transaction, and the cart is cleared if it
    was the source. Decisions and stock changes are pure Python + SQL --
    no LLM involved."""
    db = SessionLocal()
    try:
        if db.get(Customer, order_req.customer_id) is None:
            raise HTTPException(status_code=404, detail="Customer not found.")

        from_cart = order_req.items is None
        if from_cart:
            cart_items = (
                db.query(CartItem).filter(CartItem.customer_id == order_req.customer_id).all()
            )
            if not cart_items:
                raise HTTPException(status_code=400, detail="Your cart is empty.")
            requested = [(ci.product_id, ci.quantity) for ci in cart_items]
        else:
            if not order_req.items:
                raise HTTPException(status_code=400, detail="No items provided.")
            # Merge duplicate product lines into a single quantity.
            merged: dict[int, int] = {}
            for line in order_req.items:
                merged[line.product_id] = merged.get(line.product_id, 0) + line.quantity
            requested = list(merged.items())

        # Validate stock for every line before changing anything.
        products: dict[int, Product] = {}
        insufficient = []
        for product_id, qty in requested:
            product = db.get(Product, product_id)
            if product is None:
                raise HTTPException(status_code=404, detail=f"Product {product_id} not found.")
            products[product_id] = product
            available = product.inventory.stock_quantity if product.inventory else 0
            if qty > available:
                insufficient.append(
                    {
                        "product_id": product_id,
                        "name": product.name,
                        "requested": qty,
                        "available": available,
                    }
                )
        if insufficient:
            raise HTTPException(
                status_code=409,
                detail={"error": "insufficient_stock", "items": insufficient},
            )

        # All lines are stockable: build the order and decrement inventory.
        order = Order(
            customer_id=order_req.customer_id,
            total_amount=0.0,
            status="completed",
            order_date=datetime.utcnow(),
        )
        total = 0.0
        for product_id, qty in requested:
            product = products[product_id]
            product.inventory.stock_quantity -= qty
            total += product.price * qty
            order.items.append(
                OrderItem(product_id=product_id, quantity=qty, unit_price=product.price)
            )
        order.total_amount = round(total, 2)
        db.add(order)

        if from_cart:
            db.query(CartItem).filter(CartItem.customer_id == order_req.customer_id).delete()

        db.commit()
        db.refresh(order)
        return _to_order_out(order)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to place order: {e}")
        raise HTTPException(status_code=500, detail="Could not place the order.")
    finally:
        db.close()


@app.get("/orders", response_model=list[OrderOut])
def list_orders(customer_id: int) -> list[OrderOut]:
    """Return a customer's order history, most recent first."""
    db = SessionLocal()
    try:
        orders = (
            db.query(Order)
            .filter(Order.customer_id == customer_id)
            .order_by(Order.order_date.desc(), Order.id.desc())
            .all()
        )
        return [_to_order_out(o) for o in orders]
    finally:
        db.close()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Route a customer message through the orchestrator and return the reply."""
    try:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        result = orchestrator.handle_message(
            message=request.message, customer_id=request.customer_id, history=history
        )
        return ChatResponse(
            reply=result["reply"],
            intent=result["intent"],
            llm_formatted=result["llm_formatted"],
        )
    except Exception as e:
        # The orchestrator and agents already degrade gracefully, so
        # reaching here is unexpected -- surface a clean 500 rather than
        # leaking a stack trace to the client.
        logger.exception(f"Unhandled error in /chat: {e}")
        raise HTTPException(status_code=500, detail="Something went wrong processing your message.")
