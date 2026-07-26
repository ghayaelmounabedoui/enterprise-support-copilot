from datetime import date, datetime
from typing import Any

from app.services.order_service import get_order


REFUND_PERIOD_DAYS = 30

REFUNDABLE_STATUSES = {
    "delivered",
    "delayed",
    "cancelled",
}


def check_refund_eligibility(order_id: str) -> dict[str, Any]:
    order = get_order(order_id)

    if order is None:
        return {
            "found": False,
            "eligible": False,
            "order_id": order_id,
            "reason": f"Order {order_id} was not found.",
        }

    status = str(order.get("status", "")).strip().lower()

    order_date_value = order.get("order_date")

    if not order_date_value:
        return {
            "found": True,
            "eligible": False,
            "order_id": order_id,
            "reason": "The order date is missing.",
        }

    try:
        order_date = datetime.strptime(
            order_date_value,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        return {
            "found": True,
            "eligible": False,
            "order_id": order_id,
            "reason": "The order date has an invalid format.",
        }

    days_since_order = (date.today() - order_date).days

    if status == "refunded":
        return {
            "found": True,
            "eligible": False,
            "order_id": order_id,
            "status": status,
            "days_since_order": days_since_order,
            "reason": "The order has already been refunded.",
        }

    if status not in REFUNDABLE_STATUSES:
        return {
            "found": True,
            "eligible": False,
            "order_id": order_id,
            "status": status,
            "days_since_order": days_since_order,
            "reason": (
                f"Orders with status '{status}' "
                "are not eligible for a refund."
            ),
        }

    if days_since_order > REFUND_PERIOD_DAYS:
        return {
            "found": True,
            "eligible": False,
            "order_id": order_id,
            "status": status,
            "days_since_order": days_since_order,
            "refund_period_days": REFUND_PERIOD_DAYS,
            "reason": (
                f"The {REFUND_PERIOD_DAYS}-day refund period "
                "has expired."
            ),
        }

    return {
        "found": True,
        "eligible": True,
        "order_id": order_id,
        "status": status,
        "days_since_order": days_since_order,
        "refund_period_days": REFUND_PERIOD_DAYS,
        "reason": (
            f"The order is eligible for a refund within "
            f"the {REFUND_PERIOD_DAYS}-day refund period."
        ),
    }