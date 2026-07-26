import json
from pathlib import Path
from typing import Any


ORDERS_FILE = Path("data/orders.json")


def load_orders() -> list[dict[str, Any]]:
    with ORDERS_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def get_all_orders() -> list[dict[str, Any]]:
    return load_orders()


def get_order(order_id: str) -> dict[str, Any] | None:
    return next(
        (
            order
            for order in load_orders()
            if order["order_id"] == order_id
        ),
        None,
    )


def get_orders_by_customer(
    customer_id: str,
) -> list[dict[str, Any]]:
    return [
        order
        for order in load_orders()
        if order["customer_id"] == customer_id
    ]