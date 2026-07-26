from fastapi import APIRouter, HTTPException, Query

from app.schemas.customer import Customer
from app.services.customer_service import (
    get_all_customers,
    get_customer,
    search_customers,
)

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


@router.get("", response_model=list[Customer])
def list_customers() -> list[dict]:
    return get_all_customers()


@router.get("/search", response_model=list[Customer])
def search_customer_by_name(
    name: str = Query(min_length=1),
) -> list[dict]:
    return search_customers(name)


@router.get("/{customer_id}", response_model=Customer)
def read_customer(customer_id: str) -> dict:
    customer = get_customer(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Client introuvable.",
        )

    return customer