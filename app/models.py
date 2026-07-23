"""Database tables (ORM models), one class per table.

Keep this file to schema only -- no business logic. Refund eligibility,
stock checks, etc. live in the agents.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="customer")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(50))
    price: Mapped[float]

    inventory: Mapped["Inventory"] = relationship(back_populates="product", uselist=False)
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")


class Inventory(Base):
    """Stock level for a product. One row per product."""

    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)
    stock_quantity: Mapped[int]

    product: Mapped["Product"] = relationship(back_populates="inventory")


class Order(Base):
    """An order header. The individual products live in OrderItem rows, so
    one order can contain several different products (a cart checkout)."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    total_amount: Mapped[float]
    status: Mapped[str] = mapped_column(String(20), default="completed")
    order_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    refund: Mapped["Refund"] = relationship(back_populates="order", uselist=False)


class OrderItem(Base):
    """One line of an order: a product, a quantity, and the price paid
    at the time (kept separately so later price changes don't rewrite
    order history)."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]
    unit_price: Mapped[float]

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")


class CartItem(Base):
    """A product a customer has added to their (server-side) cart. One row
    per product per customer -- adding the same product again updates the
    quantity rather than inserting a duplicate."""

    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("customer_id", "product_id", name="uq_cart_customer_product"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]

    customer: Mapped["Customer"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship()


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    reason: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20))  # "approved" or "rejected"
    refund_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    order: Mapped["Order"] = relationship(back_populates="refund")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))  # "user" or "assistant"
    content: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
