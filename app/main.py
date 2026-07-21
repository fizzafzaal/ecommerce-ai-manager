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

from app.database import SessionLocal
from app.models import Customer
from app.orchestrator import Orchestrator
from app.schemas import ChatRequest, ChatResponse, CustomerSummary, HealthResponse

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
