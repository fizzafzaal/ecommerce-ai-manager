"""Derive an order's delivery/tracking stage from its state and age.

We don't store a separate tracking column -- for this project the stage is
derived from how long ago the order was placed (recent orders are still on
their way, older ones have arrived). Refunded/cancelled orders report that
terminal state instead.
"""

from datetime import datetime

# The normal happy-path stages, in order (used to draw the timeline).
TRACKING_STAGES = ["Placed", "Processing", "Shipped", "Delivered"]


def tracking_status(order_status: str, order_date: datetime) -> str:
    """Return the current tracking stage for an order."""
    if order_status == "refunded":
        return "Refunded"
    if order_status == "cancelled":
        return "Cancelled"

    age_days = (datetime.utcnow() - order_date).days
    if age_days <= 1:
        return "Processing"
    if age_days <= 3:
        return "Shipped"
    return "Delivered"
