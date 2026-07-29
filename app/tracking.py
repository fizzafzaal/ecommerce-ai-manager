"""Derive an order's delivery/tracking stage from its state and elapsed time.

We don't store a tracking column -- the stage advances by real time since the
order was placed: Processing -> Shipped (after ship_after_hours) -> Delivered
(after deliver_after_hours). So a freshly placed order genuinely progresses.
Refunded/cancelled orders report that terminal state instead.
"""

from datetime import datetime, timedelta

from app.config import settings

# The normal happy-path stages, in order (used to draw the timeline).
TRACKING_STAGES = ["Placed", "Processing", "Shipped", "Delivered"]


def tracking_status(order_status: str, order_date: datetime) -> str:
    """Return the current tracking stage for an order."""
    if order_status == "refunded":
        return "Refunded"
    if order_status == "cancelled":
        return "Cancelled"

    hours = (datetime.utcnow() - order_date).total_seconds() / 3600
    if hours < settings.ship_after_hours:
        return "Processing"
    if hours < settings.deliver_after_hours:
        return "Shipped"
    return "Delivered"


def estimated_delivery(order_status: str, order_date: datetime) -> datetime | None:
    """When the order is expected to arrive -- None once it's delivered or
    is in a terminal (refunded/cancelled) state."""
    if order_status in ("refunded", "cancelled"):
        return None
    eta = order_date + timedelta(hours=settings.deliver_after_hours)
    return eta if eta > datetime.utcnow() else None
