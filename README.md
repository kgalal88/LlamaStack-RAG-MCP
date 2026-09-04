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

---

## 📂 Project Structure

```text
.
├── app.py                   # Main FastAPI application with API endpoints & tool calling logic
├── Dockerfile               # Production Docker container definition for the API
├── requirements.txt         # Python dependencies (FastAPI, uvicorn, openai, httpx)
├── rag.py                   # Script for document uploading & vector store creation
├── query_vector_store.py    # Script to list & inspect vector stores and files
├── tools.py                 # Standalone script demonstrating OpenAI-compatible function calling
├── test.py                  # Quick smoke-test script for Llama Stack inference
├── cmd.txt                  # Comprehensive execution commands for Docker, vLLM, and OpenShift
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

# Login to OpenShift Image Registry
docker login -u developer -p $(oc whoami -t) default-route-openshift-image-registry.apps-crc.testing
```

### 2. Push Container Image
```bash
docker build -t llama-rag-mcp:latest .
docker tag llama-rag-mcp:latest default-route-openshift-image-registry.apps-crc.testing/my-project/llama-rag-mcp:latest
docker push default-route-openshift-image-registry.apps-crc.testing/my-project/llama-rag-mcp:latest
```

### 3. Apply Kubernetes Manifests
```bash
# Apply App Manifests
oc -n my-project apply -f k8s/llama-proxy-app.yaml
oc -n my-project apply -f k8s/mcp-server.yaml
oc -n my-project apply -f k8s/ogx-app.yaml

# Setup KServe & Cert-Manager
oc apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.1/cert-manager.yaml
oc apply -f k8s/kserve.yaml

# Deploy vLLM Runtime & InferenceServices
oc -n kserve apply -f k8s/vllm-qwen3-runtime.yaml
oc -n kserve apply -f k8s/vllm-qwen3-isvc.yaml
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
Standard prompt inference with optional Vector Store (RAG) tool attachment.

**Request Body:**
```json
{
  "prompt": "What are the core features of OGX?",
  "model": "vllm/Qwen/Qwen3-4B",
  "vector_store_ids": ["vs_12345"]
}
```

**Response:**
```json
{
  "model": "vllm/Qwen/Qwen3-4B",
  "response": "OGX is an AI platform..."
}
```

---

#### `POST /ask_weather`
Performs dynamic function calling to fetch weather data for a queried location.

**Request Body:**
```json
{
  "prompt": "What is the weather like in Riyadh right now?",
  "model": "vllm/Qwen/Qwen3-4B"
}
```

---

#### `POST /ask_mcp`
Routes requests through an MCP (Model Context Protocol) tool server via SSE URL.

**Request Body:**
```json
{
  "prompt": "Check Tokyo weather using MCP",
  "model": "vllm/Qwen/Qwen3-4B"
}
```

---

## 🛠 Utility & Testing Scripts

- **`rag.py`**: Uploads documents (e.g. PDFs) to Llama Stack and creates a vector store index.
- **`query_vector_store.py`**: Lists active vector stores, retrieved details, and indexed files.
- **`tools.py`**: A standalone sample executing 2-pass function calling with the OpenAI Chat Completions endpoint.
- **`test.py`**: Basic sanity script to query `vllm/Qwen/Qwen3-4B`.

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
