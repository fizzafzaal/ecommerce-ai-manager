"""FastAPI entry point -- exposes the system over HTTP.

Two endpoints: a health check, and /chat which hands the message to the
orchestrator and returns its reply. The orchestrator (and the agents it
holds) is created once at startup and reused across requests.

Run with:
    uvicorn app.main:app --reload
Interactive docs are then at http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from loguru import logger
from sqlalchemy import or_

from app.agents.product_agent import LOW_STOCK_THRESHOLD
from app.database import SessionLocal
from app.models import Customer, Product
from app.orchestrator import Orchestrator
from app.schemas import (
    ChatRequest,
    ChatResponse,
    CustomerSummary,
    HealthResponse,
    ProductOut,
)

app = FastAPI(
    title="E-Commerce AI Manager",
    description="A multi-agent AI system for e-commerce support, refunds, and product search.",
    version="1.0.0",
)

# Built once and reused -- agents hold model/DB handles we don't want to
# reconstruct on every request.
orchestrator = Orchestrator()


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


@app.get("/categories", response_model=list[str])
def list_categories() -> list[str]:
    """Return the distinct product categories, for nav and filtering."""
    db = SessionLocal()
    try:
        rows = db.query(Product.category).distinct().order_by(Product.category).all()
        return [row[0] for row in rows]
    finally:
        db.close()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Route a customer message through the orchestrator and return the reply."""
    try:
        result = orchestrator.handle_message(
            message=request.message, customer_id=request.customer_id
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
