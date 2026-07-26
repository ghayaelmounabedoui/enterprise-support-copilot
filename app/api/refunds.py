from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.refund_service import check_refund_eligibility


router = APIRouter(
    prefix="/refunds",
    tags=["refunds"],
)


@router.get("/{order_id}/eligibility")
def read_refund_eligibility(order_id: str) -> dict[str, Any]:
    result = check_refund_eligibility(order_id)

    if not result["found"]:
        raise HTTPException(
            status_code=404,
            detail=result["reason"],
        )

    return result