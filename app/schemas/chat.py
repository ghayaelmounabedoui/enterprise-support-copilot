from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class ChatResponse(BaseModel):
    answer: str
    input_tokens: int
    output_tokens: int
    latency_ms: int