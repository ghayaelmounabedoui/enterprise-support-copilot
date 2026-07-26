import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TICKETS_FILE = Path("data/tickets.json")


def load_tickets() -> list[dict[str, Any]]:
    with TICKETS_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def save_tickets(tickets: list[dict[str, Any]]) -> None:
    with TICKETS_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            tickets,
            file,
            ensure_ascii=False,
            indent=2,
        )


def get_all_tickets() -> list[dict[str, Any]]:
    return load_tickets()


def get_ticket(ticket_id: str) -> dict[str, Any] | None:
    return next(
        (
            ticket
            for ticket in load_tickets()
            if ticket["ticket_id"] == ticket_id
        ),
        None,
    )


def create_ticket(
    order_id: str,
    reason: str,
    priority: str,
) -> dict[str, Any]:
    tickets = load_tickets()

    ticket = {
        "ticket_id": f"TICKET-{uuid.uuid4().hex[:8].upper()}",
        "order_id": order_id,
        "reason": reason,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    tickets.append(ticket)
    save_tickets(tickets)

    return ticket


def update_ticket_status(
    ticket_id: str,
    status: str,
) -> dict[str, Any] | None:
    tickets = load_tickets()

    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            ticket["status"] = status
            save_tickets(tickets)
            return ticket

    return None