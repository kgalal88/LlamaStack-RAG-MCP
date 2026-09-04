FROM python:3.12-slim

WORKDIR /app

ENV LLAMA_STACK_BASE_URL=http://localhost:8321/v1 \
    LLAMA_STACK_API_KEY=fake \
    LLAMA_STACK_TIMEOUT_SECONDS=60 \
    PORT=8001 \
    UVICORN_RELOAD=false

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --upgrade openai

COPY . .

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
