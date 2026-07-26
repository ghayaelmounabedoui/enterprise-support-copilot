from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    order_id: str
    reason: str = Field(min_length=3, max_length=500)
    priority: Literal["low", "medium", "high", "critical"] = "medium"


class TicketUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved", "closed"]


class Ticket(BaseModel):
    ticket_id: str
    order_id: str
    reason: str
    priority: str
    status: str
    created_at: datetime