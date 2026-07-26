from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.bedrock_service import BedrockService

router = APIRouter(
    prefix="/chat",
    tags=["artificial intelligence"],
)

bedrock_service = BedrockService()


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest) -> dict:
    try:
        return bedrock_service.chat(payload.message)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc