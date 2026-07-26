from fastapi import FastAPI

app = FastAPI(
    title="Enterprise Support Copilot",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}