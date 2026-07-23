"""Request/response shapes for the API (Pydantic).

Keeping these separate from the ORM models means the API contract and
the database schema can evolve independently.
"""

from datetime import datetime

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


class CustomerSummary(BaseModel):
    id: int
    name: str


class ProductOut(BaseModel):
    """A product as shown in the storefront, with live stock."""

    id: int
    name: str
    description: str
    category: str
    price: float
    stock: int
    low_stock: bool
    image_url: str | None = None


class SignupRequest(BaseModel):
    """Create a new customer. Password is accepted for realism but never
    stored or checked (login is intentionally fake)."""

    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=100)
    password: str | None = None


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=100)
    password: str | None = None


class CartItemAdd(BaseModel):
    """Request body for adding a product to a customer's cart."""

    customer_id: int = Field(..., ge=1)
    product_id: int = Field(..., ge=1)
    quantity: int = Field(1, ge=1, description="How many to add.")


class CartItemOut(BaseModel):
    id: int
    product_id: int
    name: str
    price: float
    quantity: int
    line_total: float


class CartOut(BaseModel):
    """A customer's whole cart: its line items and the grand total."""

    items: list[CartItemOut]
    total: float


class OrderLineIn(BaseModel):
    product_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1)


class OrderCreate(BaseModel):
    """Place an order. If `items` is omitted, the customer's current cart
    is checked out instead."""

    customer_id: int = Field(..., ge=1)
    items: list[OrderLineIn] | None = Field(
        None, description="Explicit lines to order; if omitted, the cart is used."
    )


class OrderItemOut(BaseModel):
    product_id: int
    name: str
    quantity: int
    unit_price: float
    line_total: float


class OrderOut(BaseModel):
    id: int
    customer_id: int
    status: str
    order_date: datetime
    total_amount: float
    items: list[OrderItemOut]

