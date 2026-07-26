from fastapi import APIRouter, HTTPException, status

from app.schemas.ticket import (
    Ticket,
    TicketCreate,
    TicketUpdate,
)
from app.services.order_service import get_order
from app.services.ticket_service import (
    create_ticket,
    get_all_tickets,
    get_ticket,
    update_ticket_status,
)

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
)


@router.get("", response_model=list[Ticket])
def list_tickets() -> list[dict]:
    return get_all_tickets()


@router.get("/{ticket_id}", response_model=Ticket)
def read_ticket(ticket_id: str) -> dict:
    ticket = get_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket introuvable.",
        )

    return ticket


@router.post(
    "",
    response_model=Ticket,
    status_code=status.HTTP_201_CREATED,
)
def create_support_ticket(
    payload: TicketCreate,
) -> dict:
    if get_order(payload.order_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Commande introuvable.",
        )

    return create_ticket(
        order_id=payload.order_id,
        reason=payload.reason,
        priority=payload.priority,
    )


@router.patch("/{ticket_id}", response_model=Ticket)
def update_support_ticket(
    ticket_id: str,
    payload: TicketUpdate,
) -> dict:
    ticket = update_ticket_status(
        ticket_id=ticket_id,
        status=payload.status,
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket introuvable.",
        )

    return ticket
