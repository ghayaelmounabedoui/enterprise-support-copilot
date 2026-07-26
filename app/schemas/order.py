from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Order(BaseModel):
    order_id: str
    customer_id: str
    product: str
    status: Literal[
        "processing",
        "shipped",
        "delivered",
        "delayed",
        "cancelled",
    ]
    order_date: date
    expected_delivery: date
    amount: float = Field(ge=0)
    currency: str