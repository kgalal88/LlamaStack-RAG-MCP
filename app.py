import os
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field
import uvicorn

BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321/v1")
API_KEY = os.getenv("LLAMA_STACK_API_KEY", "fake")
TIMEOUT_SECONDS = float(os.getenv("LLAMA_STACK_TIMEOUT_SECONDS", "60"))

app = FastAPI(title="Llama Stack API", version="1.0.0")

http_client = httpx.Client(
    timeout=httpx.Timeout(TIMEOUT_SECONDS, connect=10.0),
    follow_redirects=True,
    verify=False,
)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY, http_client=http_client)


class AskRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Text prompt to send to the model")
    model: str = Field(default="vllm/Qwen/Qwen3-4B", description="Model ID to invoke")
    vector_store_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional vector store IDs to attach to a file search tool",
    )


class AskResponse(BaseModel):
    model: str
    response: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "base_url": BASE_URL}


@app.get("/models")
async def list_models() -> dict:
    try:
        models = client.models.list()
        return {"models": [model.id for model in models.data]}
    except Exception as exc:  # pragma: no cover - depends on upstream service
        raise HTTPException(status_code=502, detail=f"Unable to fetch models: {exc}") from exc


@app.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest) -> AskResponse:
    tools = []
    if payload.vector_store_ids:
        tools.append({
            "type": "file_search",
            "vector_store_ids": payload.vector_store_ids,
        })

    try:
        response = client.responses.create(
            model=payload.model,
            input=payload.prompt,
            tools=tools or None,
        )
        return AskResponse(model=payload.model, response=response.output_text)
    except Exception as exc:  # pragma: no cover - depends on upstream service
        raise HTTPException(status_code=502, detail=f"Model request failed: {exc}") from exc


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
