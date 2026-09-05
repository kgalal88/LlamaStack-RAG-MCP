# LlamaStack-RAG-MCP

A high-performance FastAPI service integrating **Llama Stack**, **RAG (Retrieval-Augmented Generation)**, **Tool/Function Calling**, and **Model Context Protocol (MCP)** server connectivity. The project features local deployment options using **vLLM** and **Docker**, as well as enterprise Kubernetes/OpenShift deployment manifests and scripts.

---

## 📋 Table of Contents
- [Architecture & Features](#-architecture--features)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start & Local Setup](#-quick-start--local-setup)
  - [1. Running vLLM (Inference Server)](#1-running-vllm-inference-server)
  - [2. Running Llama Stack (Distribution Starter)](#2-running-llama-stack-distribution-starter)
  - [3. Running the FastAPI Application](#3-running-the-fastapi-application)
- [Docker Setup](#-docker-setup)
- [OpenShift / Kubernetes Deployment](#-openshift--kubernetes-deployment)
- [API Reference](#-api-reference)
- [Utility & Testing Scripts](#-utility--testing-scripts)
- [Configuration & Environment Variables](#-configuration--environment-variables)

---

## 🏗 Architecture & Features

This project provides an API layer designed to bridge client applications with a Llama Stack inference backend powered by vLLM (specifically configured for Qwen3 models).

### Key Features:
- **FastAPI Core**: Lightweight, fast async endpoints using OpenAI-compatible Python SDK and HTTPX client.
- **RAG Integration**: Support for file indexing and vector store queries via Llama Stack vector store APIs.
- **Function/Tool Calling**: Multi-turn weather mock tool integration using model-directed function calls.
- **MCP Support**: Ready for Server-Sent Events (SSE) based Model Context Protocol tool integrations.
- **Enterprise OpenShift Ready**: Deployment scripts and instructions for OpenShift image registries, Routes, KServe InferenceServices, and cert-manager integration.

<img width="8192" height="5681" alt="RAG Document Ingestion-2026-09-05-104722" src="https://github.com/user-attachments/assets/52c30e5e-cb15-47a5-a274-2e0a8307a56a" />

---

## 📂 Project Structure

```text
.
├── app.py                   # Main FastAPI application with API endpoints & tool calling logic
├── Dockerfile               # Production Docker container definition for the API
├── requirements.txt         # Python dependencies (FastAPI, uvicorn, openai, httpx)
├── rag.py                   # Script for document uploading & vector store creation
└── README.md                # Project documentation
```

---

## ⚙️ Prerequisites

- **Python**: `3.12+`
- **Docker**: Installed with GPU support (`nvidia-container-toolkit`) if running vLLM locally.
- **OpenShift / Kubernetes CLI** (`oc` / `kubectl`): Required for deployment on OpenShift clusters.
- **HuggingFace Access Token**: Access token required for downloading gated model weights (e.g., Qwen3).

---

## 🚀 Quick Start & Local Setup

### 1. Running vLLM (Inference Server)

Start the vLLM container serving `Qwen/Qwen3-4B` with `bitsandbytes` quantization and Hermes tool-call parser:

```bash
# Verify GPU availability
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Export HuggingFace Token
export HF_TOKEN="your_huggingface_token"

# Run vLLM container
docker run --rm \
    --name vllm-qwen3-4B \
    --gpus all \
    -p 8000:8000 \
    -v ~/.cache/huggingface2:/root/.cache/huggingface \
    -e HF_TOKEN=$HF_TOKEN \
    -e VLLM_USE_V2_MODEL_RUNNER=0 \
    --ipc=host \
    vllm/vllm-openai:latest \
    Qwen/Qwen3-4B \
    --quantization bitsandbytes \
    --load-format bitsandbytes \
    --gpu-memory-utilization 0.80 \
    --max-model-len 8192 \
    --enforce-eager \
    --enable-auto-tool-choice \
    --tool-call-parser hermes
```

### 2. Running Llama Stack (Distribution Starter)

Run the OGX Llama Stack distribution starter connected to the vLLM instance:

```bash
docker run -d \
  -p 8321:8321 \
  -v ~/.ogx:/root/.ogx \
  -e INFERENCE_PROVIDER=vllm \
  -e VLLM_URL=http://host.docker.internal:8000/v1 \
  ogxai/distribution-starter
```

### 3. Running the FastAPI Application

Install dependencies and start the app locally:

```bash
# Install dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Run server with Uvicorn
python3 -m uvicorn app:app --host 0.0.0.0 --port 8001
```

---

## 🐳 Docker Setup

Build and run the application container using Docker:

### Build Container Image
```bash
docker build -t llama-rag-mcp:latest .
```

### Run Container
```bash
docker run -d \
  -p 8002:8001 \
  -e LLAMA_STACK_BASE_URL=http://host.docker.internal:8321/v1 \
  --name llama-rag-mcp-app \
  llama-rag-mcp:latest
```

---

## ☸️ OpenShift / Kubernetes Deployment

Detailed workflow for deploying to Red Hat OpenShift (CRC / CodeReady Containers):

### 1. Registry Setup & Login
```bash
# Expose OpenShift internal image registry route
oc patch configs.imageregistry.operator.openshift.io/cluster --type merge -p '{"spec":{"defaultRoute":true}}'
oc get route default-route -n openshift-image-registry

# Login to OpenShift Image Registry
docker login -u developer -p $(oc whoami -t) default-route-openshift-image-registry.apps-crc.testing
```

### 2. Push Container Image
```bash
docker build -t llama-rag-mcp:latest .
docker tag llama-rag-mcp:latest default-route-openshift-image-registry.apps-crc.testing/my-project/llama-rag-mcp:latest
docker push default-route-openshift-image-registry.apps-crc.testing/my-project/llama-rag-mcp:latest
```
#### Build & Push MCP Server Containr Image found in this repo https://github.com/kgalal88/SpringAI-MCP-Server
```bash
docker build -t chat-mcp-server:latest .
docker tag chat-mcp-server:latest default-route-openshift-image-registry.apps-crc.testing/my-project/chat-mcp-server:latest
docker push default-route-openshift-image-registry.apps-crc.testing/my-project/chat-mcp-server:latest
```

### 3. Apply Kubernetes Manifests
```bash
# Setup KServe & Cert-Manager
oc apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.1/cert-manager.yaml
oc apply -f k8s/kserve.yaml

# Deploy vLLM InferenceServices
oc  -n kserve apply -f D:\materials\RHOCP\ai\llama-stack\k8s\vllm-host-proxy.yaml
# Apply App Manifests
oc -n my-project apply -f k8s/ogx-app.yaml
oc -n my-project apply -f k8s/mcp-server.yaml
oc -n my-project apply -f k8s/llama-proxy-app.yaml
```

---

## 📡 API Reference

### Health & Models

#### `GET /health`
Returns system status and base URL configuration.

#### `GET /models`
Returns a list of available models served by Llama Stack.

---

### Inferences & Tool Endpoints

#### `POST /ask`
Standard prompt inference.

**Request Body:**
```json
{
  "model": "vllm/Qwen/Qwen3-4B",
  "prompt": "Who is Khalid?"
}
```
**Response:**
```json
{
    "model": "vllm/Qwen/Qwen3-4B",
    "response": "<think>\nOkay, the user is asking \"Who is Khalid?\" and I need to figure out the answer. First, I should consider the different possible meanings of \"Khalid.\" The name \"Khalid\" is Arabic for \"eternal\" or \"perpetual,\" but there are several notable people with that name.\n\nThat's a popular R&B artist. He's known for his music and his role in the entertainment industry..."
}
```
<img width="1437" height="446" alt="image" src="https://github.com/user-attachments/assets/2e566138-617a-4bcd-933b-bdd6d3b5b1f1" />

---

#### `POST /ask`
Standard prompt inference with optional Vector Store (RAG) tool attachment.

**Request Body:**
```json
{
  "model": "vllm/Qwen/Qwen3-4B",
  "prompt": "Who is Khalid?",
  "vector_store_ids": [
      "vs_a8915121-4bbe-411e-8d99-f8ca02756dc4"
  ]
}
```
**Response:**
```json
{
    "model": "vllm/Qwen/Qwen3-4B",
    "response": "<think>\nOkay, let me try to figure out who Khalid is based on the information provided. The user asked \"Who is Khalid?\" and I used the file_search tool to find relevant information. The results came back with three chunks from a PDF document titled \"Khalid Elmetwally.pdf\". \n\nLooking at the first chunk, it seems to be a resume or profile of someone named Khalid Elmetwally. The document mentions he is a Software Solutions Architect with 15+ years of experience. He has worked at companies like Saudi Telecom Company (STC Group), Ericsson, Jumia Services, and SiliconExpert Technologies..."
}
```
<img width="1436" height="551" alt="image" src="https://github.com/user-attachments/assets/0ef0692a-7856-41af-bcad-64f911268eac" />

---
#### `POST /ask_mcp`
Routes requests through an MCP (Model Context Protocol) tool server via SSE URL.

**Request Body:**
```json
{
  "model": "vllm/Qwen/Qwen3-4B",
  "prompt": "Get all user activities data for Julia Ali"
}
```
**Response:**
```json
{
    "model": "vllm/Qwen/Qwen3-4B",
    "response": "<think>\nOkay, let's see. The user asked for all user activities data for Julia Ali. I called the getUserActivityByName function with her name, and the response came back with a list of activities. Each entry has userId, totalActions, totalScore, and createdDate.\n\nFirst, I need to parse this data. The userId is U001 in all entries, which might be important. The totalActions are all zero, so maybe that's a note to include. The totalScore varies, and each has a createdDate. \n\nThe user probably wants a summary of Julia Ali's activities. Since all entries are under U001, I should mention that the data is for user U001. Also, note that totalActions are zero, so maybe there's no activity in terms of actions, but scores are varying. The dates are spread out from May 2026 to July 2026. \n\nI should present this in a clear way, maybe listing each entry with the dates and scores. Also, point out the consistent userId and the totalActions. Maybe the user is interested in tracking her performance over time, so highlighting the score changes could be useful. I need to make sure the answer is structured and easy to read, maybe bullet points or a table format. Also, check if there's any missing information or if further details are needed.\n</think>\n\nHere's the activity data for Julia Ali (User ID: U001):\n\n**Activity Summary:**\n- **Total Actions:** 0 (No action-based activities recorded)\n- **Score History:**\n  - May 2, 2026: 10 points\n  - May 3, 2026: 96 points\n  - May 22, 2026: 95 points\n  - May 30, 2026: 26 points\n  - June 4, 2026: 78 points\n  - June 7, 2026: 33 points\n  - July 10, 2026: 36 points\n  - July 18, 2026: 66 points\n  - July 23, 2026: 35 points\n\n**Notes:**\n- All entries are associated with User ID: U001\n- No action-based activities were recorded (totalActions = 0)\n- Scores show fluctuating performance over time\n\nWould you like me to analyze this data further or highlight specific trends?"
}
```
<img width="1413" height="720" alt="image" src="https://github.com/user-attachments/assets/4bb4f684-8c18-4ab3-8c79-561bd0888215" />

---

#### `POST /ask_weather`
Performs dynamic function calling to fetch weather data for a queried location.

**Request Body:**
```json
{
  "model": "vllm/Qwen/Qwen3-4B",
  "prompt": "What is the weather in Riyadh?"
}
```
**Response:**
```json
{
    "model": "vllm/Qwen/Qwen3-4B",
    "response": "<think>\nOkay, the user asked for the weather in Riyadh. I called the get_weather function with Riyadh as the location. The response came back with a temperature of 45°C and sunny condition. Now I need to present this information in a clear and friendly way. Let me start by stating the current weather in Riyadh. I should mention both the temperature and the condition. Maybe add a note about it being a hot day since it's sunny and the temperature is quite high. Keep it concise but informative. Make sure to use the symbols correctly, like the degree sign. Also, check if there's any additional info needed, but the response seems complete. Alright, time to put it all together.\n</think>\n\nThe current weather in Riyadh is **45°C** with **Sunny** conditions. It's a hot day! 🌞"
}
```
<img width="1411" height="543" alt="image" src="https://github.com/user-attachments/assets/431e7101-1ea9-4240-b9f5-f047f6fc6f66" />

---

## 🛠 Utility & Testing Scripts

- **`rag.py`**: Uploads documents (e.g. PDFs) to Llama Stack and creates a vector store index.

---

## ⚙️ Configuration & Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `LLAMA_STACK_BASE_URL` | `http://localhost:8321/v1` | Base URL endpoint for Llama Stack |
| `LLAMA_STACK_API_KEY` | `fake` | API Key for authorization |
| `LLAMA_STACK_TIMEOUT_SECONDS` | `60` | HTTP request timeout |
| `MCP_SERVER_URL` | `http://localhost:8081/sse` | Endpoint URL for the MCP Server |
| `PORT` | `8001` | Application port |
| `UVICORN_RELOAD` | `false` | Enable hot-reload for local development |

---

## 🚀 Related Medium Article
https://medium.com/@khalid.mtwaly/building-enterprise-ai-agents-integrating-llama-stack-rag-and-mcp-on-openshift-530edd882634

---

## 👤 Author

**Khalid Galal**

**https://www.linkedin.com/in/khalidgalal**
