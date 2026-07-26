from pydantic import BaseModel


class RefundCheckRequest(BaseModel):
    order_id: str


class RefundCheckResponse(BaseModel):
    order_id: str
    eligible: bool
    reason: str
    eligible_from: str | None = None