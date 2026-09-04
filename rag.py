import httpx
from openai import OpenAI

#BASE_URL = "http://localhost:8321/v1"
BASE_URL = "http://ogx-route-my-project.apps-crc.testing/v1"

client = OpenAI(base_url=BASE_URL, api_key="fake", http_client=httpx.Client(verify=False))

# Upload a document
file = client.files.create(
    file=open("docs/Khalid_Elmetwally.pdf", "rb"),
    purpose="assistants",
)

# Create a vector store and index the file
vector_store = client.vector_stores.create(
    name="my-docs",
    file_ids=[file.id],
)

print(f"Vector Store ID: {vector_store.id}")

# # Ask questions with file search
# response = client.responses.create(
#     model="vllm/Qwen/Qwen3-4B",
#     input="Who is Khalid?",
#     tools=[{
#         "type": "file_search",
#         "vector_store_ids": [vector_store.id],
#     }],
# )
# print(response.output_text)