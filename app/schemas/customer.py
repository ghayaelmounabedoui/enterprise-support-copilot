from pydantic import BaseModel, EmailStr


class Customer(BaseModel):
    customer_id: str
    name: str
    email: EmailStr
    tier: str
    country: str


import json
from pathlib import Path
from typing import Any


CUSTOMERS_FILE = Path("data/customers.json")


def load_customers() -> list[dict[str, Any]]:
    with CUSTOMERS_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def get_all_customers() -> list[dict[str, Any]]:
    return load_customers()


def get_customer(customer_id: str) -> dict[str, Any] | None:
    customers = load_customers()

    return next(
        (
            customer
            for customer in customers
            if customer["customer_id"] == customer_id
        ),
        None,
    )


def search_customers(name: str) -> list[dict[str, Any]]:
    normalized_name = name.strip().lower()

    return [
        customer
        for customer in load_customers()
        if normalized_name in customer["name"].lower()
    ]