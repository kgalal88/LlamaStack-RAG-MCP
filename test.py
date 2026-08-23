import httpx
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="fake", http_client=httpx.Client(verify=False))

response = client.responses.create(
    model="vllm/Qwen/Qwen3-4B",
    input="What is OGX?",
)
print(response.output_text)