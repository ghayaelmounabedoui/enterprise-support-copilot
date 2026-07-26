from fastapi import FastAPI
from app.api.refunds import router as refunds_router
from app.api.customers import router as customers_router
from app.api.orders import router as orders_router
from app.api.refunds import router as refunds_router
from app.api.tickets import router as tickets_router
from app.core.config import get_settings
from app.api.chat import router as chat_router
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Backend métier d'un copilote de support client "
        "basé sur Amazon Bedrock."
    ),
)

app.include_router(customers_router)
app.include_router(orders_router)
app.include_router(tickets_router)
app.include_router(refunds_router)
app.include_router(chat_router)
app.include_router(refunds_router)
@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "healthy"}