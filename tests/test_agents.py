"""Sanity tests for the agents.

Deliberately avoids the LLM: intent detection is tested through the
deterministic keyword/entity paths, not the model, so the suite is fast
and repeatable. The refund approval test creates and deletes its own
throwaway rows so it never touches the seeded demo data.

Run from the project root:
    pytest -q
"""

import uuid
from datetime import datetime, timedelta

import pytest

from app.agents.product_agent import ProductAgent
from app.agents.refund_agent import RefundAgent
from app.agents.support_agent import SupportAgent
from app.database import SessionLocal
from app.models import Customer, Inventory, Order, OrderItem, Product, Refund


# --- Support Agent: deterministic intent + entity extraction ---


@pytest.fixture(scope="module")
def support_agent():
    return SupportAgent()


def test_keyword_intent_detects_refund(support_agent):
    assert support_agent._detect_intent_via_keywords("I want a refund please") == "refund"


def test_keyword_intent_detects_product_search(support_agent):
    assert support_agent._detect_intent_via_keywords("I'm looking for headphones") == "product_search"


def test_keyword_intent_unknown_for_gibberish(support_agent):
    assert support_agent._detect_intent_via_keywords("asdkjh qwe zxc") == "unknown"


def test_faq_matching_returns_answer(support_agent):
    answer = support_agent._match_faq("what is your return policy?")
    assert answer is not None and "30 days" in answer


def test_order_id_extraction(support_agent):
    entities = support_agent._extract_entities("please refund order #42")
    assert entities["order_id"] == 42


# --- Refund Agent: rules only ---


@pytest.fixture(scope="module")
def refund_agent():
    return RefundAgent()


def test_refund_rejects_nonexistent_order(refund_agent):
    result = refund_agent.run(order_id=999999, customer_id=1)
    assert result["approved"] is False
    assert result["reason"] == "order_not_found"


def test_refund_rejects_wrong_customer(refund_agent):
    """An existing order requested by the wrong customer is rejected."""
    db = SessionLocal()
    order = db.query(Order).first()
    order_id, real_owner = order.id, order.customer_id
    db.close()

    result = refund_agent.run(order_id=order_id, customer_id=real_owner + 10000)
    assert result["approved"] is False
    assert result["reason"] == "order_not_owned_by_customer"


def test_refund_approved_for_eligible_order(refund_agent):
    """Create a throwaway recent order, refund it, then delete everything
    so the seeded demo data is left untouched and the test can re-run."""
    db = SessionLocal()
    customer = Customer(name="Test User", email=f"test_{uuid.uuid4().hex}@example.com")
    product = Product(name="Test Product", description="A test item.", category="Test", price=20.0)
    db.add_all([customer, product])
    db.flush()
    order = Order(
        customer_id=customer.id,
        total_amount=20.0,
        status="completed",
        order_date=datetime.utcnow() - timedelta(days=5),  # inside the 30-day window
        items=[OrderItem(product_id=product.id, quantity=1, unit_price=20.0)],
    )
    db.add(order)
    db.commit()
    order_id, customer_id, product_id = order.id, customer.id, product.id
    db.close()

    try:
        result = refund_agent.run(order_id=order_id, customer_id=customer_id)
        assert result["approved"] is True
        assert result["refund_amount"] == 20.0
    finally:
        db = SessionLocal()
        db.query(Refund).filter(Refund.order_id == order_id).delete()
        db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
        db.query(Order).filter(Order.id == order_id).delete()
        db.query(Product).filter(Product.id == product_id).delete()
        db.query(Customer).filter(Customer.id == customer_id).delete()
        db.commit()
        db.close()


def test_refund_rejects_out_of_window_order(refund_agent):
    """A throwaway order older than 30 days is rejected as out-of-window."""
    db = SessionLocal()
    customer = Customer(name="Old Order User", email=f"old_{uuid.uuid4().hex}@example.com")
    product = Product(name="Old Product", description="An old item.", category="Test", price=15.0)
    db.add_all([customer, product])
    db.flush()
    order = Order(
        customer_id=customer.id,
        total_amount=15.0,
        status="completed",
        order_date=datetime.utcnow() - timedelta(days=45),  # outside the window
        items=[OrderItem(product_id=product.id, quantity=1, unit_price=15.0)],
    )
    db.add(order)
    db.commit()
    order_id, customer_id, product_id = order.id, customer.id, product.id
    db.close()

    try:
        result = refund_agent.run(order_id=order_id, customer_id=customer_id)
        assert result["approved"] is False
        assert result["reason"] == "outside_refund_window"
    finally:
        db = SessionLocal()
        db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
        db.query(Order).filter(Order.id == order_id).delete()
        db.query(Product).filter(Product.id == product_id).delete()
        db.query(Customer).filter(Customer.id == customer_id).delete()
        db.commit()
        db.close()


# --- Product Agent: semantic search sanity check ---


def test_product_search_returns_structured_results():
    result = ProductAgent().run(query="warm winter jacket")
    assert "results" in result
    assert isinstance(result["results"], list)
    if result["results"]:
        top = result["results"][0]
        assert {"id", "name", "price", "stock", "low_stock"}.issubset(top.keys())
        assert isinstance(top["low_stock"], bool)
