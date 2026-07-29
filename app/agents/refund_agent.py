"""Decides refund eligibility using rules only -- no LLM in the decision.

Approves or rejects a refund request against fixed business rules and
updates the database in a transaction. The LLM is only ever used
elsewhere (the orchestrator's final formatting step) to phrase the
outcome in friendly text -- it never sees or influences this decision,
so a hallucinated approval is not possible.
"""

from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.database import SessionLocal
from app.models import Order, Refund
from app.tracking import tracking_status

REFUND_WINDOW_DAYS = 30


class RefundAgent(BaseAgent):
    name = "refund_agent"
    timeout_seconds = 10.0

    def get_customer_orders(self, customer_id: int) -> list[dict]:
        """Read-only: list a customer's orders (newest first) with product
        names and refund eligibility. Used to help a customer who wants a
        refund but didn't give an order number."""
        db = SessionLocal()
        try:
            orders = (
                db.query(Order)
                .filter(Order.customer_id == customer_id)
                .order_by(Order.order_date.desc())
                .all()
            )
            summaries = []
            for order in orders:
                age_days = (datetime.utcnow() - order.order_date).days
                summaries.append(
                    {
                        "id": order.id,
                        "date": order.order_date,
                        "age_days": age_days,
                        "status": order.status,
                        "tracking_status": tracking_status(order.status, order.order_date),
                        "total": order.total_amount,
                        "products": [item.product.name for item in order.items],
                        "eligible": order.status == "completed" and age_days <= REFUND_WINDOW_DAYS,
                    }
                )
            return summaries
        finally:
            db.close()

    def process(self, order_id: int, customer_id: int, reason: str = "") -> dict:
        db = SessionLocal()
        try:
            order = db.get(Order, order_id)

            if order is None:
                return {"approved": False, "reason": "order_not_found"}

            if order.customer_id != customer_id:
                return {"approved": False, "reason": "order_not_owned_by_customer"}

            if order.status == "refunded":
                return {"approved": False, "reason": "already_refunded"}

            age_days = (datetime.utcnow() - order.order_date).days
            if age_days > REFUND_WINDOW_DAYS:
                return {
                    "approved": False,
                    "reason": "outside_refund_window",
                    "order_age_days": age_days,
                }

            refund = Refund(
                order_id=order.id,
                reason=reason or "Customer requested refund",
                status="approved",
                refund_date=datetime.utcnow(),
            )
            order.status = "refunded"
            db.add(refund)
            db.commit()

            return {
                "approved": True,
                "reason": "eligible",
                "refund_amount": order.total_amount,
                "order_id": order.id,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
