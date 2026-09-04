# LlamaStack-RAG-MCP

This project exposes a FastAPI application that talks to a Llama Stack service.

## Docker

Build and run the app with Docker Compose:

```bash
docker build -t llama-rag-mcp:latest .
```

The API will be available at `http://localhost:8001`.

If your Llama Stack instance is running locally, configure the base URL in the environment before starting:

```bash
export LLAMA_STACK_BASE_URL=http://host.docker.internal:8321/v1
```

For Linux hosts, Docker Compose includes `host.docker.internal` via `extra_hosts` so the container can reach the host machine.

Useful endpoints:

- `GET /health`
- `GET /models`
- `POST /ask`
- `POST /ask_weather`
