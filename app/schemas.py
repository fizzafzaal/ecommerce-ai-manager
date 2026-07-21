"""Request/response shapes for the API (Pydantic).

Keeping these separate from the ORM models means the API contract and
the database schema can evolve independently.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The customer's message.")
    customer_id: int = Field(..., ge=1, description="ID of the customer sending the message.")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="The assistant's reply to show the customer.")
    intent: str = Field(..., description="The intent the router detected.")
    llm_formatted: bool = Field(
        ..., description="True if the LLM added a friendly opening line to the reply."
    )


class HealthResponse(BaseModel):
    status: str
