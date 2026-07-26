from fastapi import APIRouter, HTTPException

from app.schemas.order import Order
from app.services.customer_service import get_customer
from app.services.order_service import (
    get_all_orders,
    get_order,
    get_orders_by_customer,
)

router = APIRouter(tags=["orders"])


@router.get("/orders", response_model=list[Order])
def list_orders() -> list[dict]:
    return get_all_orders()


@router.get("/orders/{order_id}", response_model=Order)
def read_order(order_id: str) -> dict:
    order = get_order(order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Commande introuvable.",
        )

    return order


@router.get(
    "/customers/{customer_id}/orders",
    response_model=list[Order],
)
def list_customer_orders(customer_id: str) -> list[dict]:
    if get_customer(customer_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Client introuvable.",
        )

    return get_orders_by_customer(customer_id)