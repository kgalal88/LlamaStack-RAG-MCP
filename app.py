import json
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
PORT = int(os.getenv("PORT", "8001"))
RELOAD = os.getenv("UVICORN_RELOAD", "false").lower() in {"1", "true", "yes", "on"}

app = FastAPI(title="Llama Stack API", version="1.0.0")

http_client = httpx.Client(
    timeout=httpx.Timeout(TIMEOUT_SECONDS, connect=10.0),
    follow_redirects=True,
    verify=False,
)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY, http_client=http_client)


# --- Mock Weather Function ---
def mock_get_weather(location: str) -> str:
    mock_data = {
        "Riyadh": {"temperature": "45°C", "condition": "Sunny"},
        "Tokyo": {"temperature": "22°C", "condition": "Rainy"},
        "London": {"temperature": "15°C", "condition": "Cloudy"},
    }
    data = mock_data.get(location, {"temperature": "70°F", "condition": "Clear"})
    return json.dumps({"location": location, **data})


# --- Pydantic Schemas ---
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


class WeatherRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Text prompt to send to the model")
    model: str = Field(default="vllm/Qwen/Qwen3-4B", description="Model ID to invoke")


class WeatherResponse(BaseModel):
    model: str
    response: str


# --- Endpoints ---
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


@app.post("/ask_weather", response_model=WeatherResponse)
async def get_weather_info(payload: WeatherRequest) -> WeatherResponse:
    tools = [{
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
        },
    }]

    try:
        # Step 1: Request tool execution from model
        initial_response = client.responses.create(
            model=payload.model,
            input=payload.prompt,
            tools=tools,
        )

        # Step 2: Extract function call outputs
        function_outputs = []
        for item in getattr(initial_response, "output", []):
            if item.type == "function_call":
                args = json.loads(item.arguments)
                location = args.get("location", "")
                tool_result = mock_get_weather(location)

                function_outputs.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": tool_result,
                })

        # Step 3: Pass FULL conversation history back to the model
        if function_outputs:
            conversation_input = [
                {"role": "user", "content": payload.prompt},
            ]
            
            # Append output items from the initial response
            for item in getattr(initial_response, "output", []):
                conversation_input.append(item)
                
            # Append function execution results
            conversation_input.extend(function_outputs)

            final_response = client.responses.create(
                model=payload.model,
                input=conversation_input,
                tools=tools,
            )
            return WeatherResponse(model=payload.model, response=final_response.output_text)

        return WeatherResponse(model=payload.model, response=initial_response.output_text)

    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Weather request failed: {exc}") from exc
    
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=RELOAD)