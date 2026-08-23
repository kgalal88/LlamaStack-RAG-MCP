import httpx
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="fake", http_client=httpx.Client(verify=False))

# Upload a document
file = client.files.create(
    file=open("docs/Khalid_Elmetwally.pdf", "rb"),
    purpose="assistants",
)

# Create a vector store and index the file
vector_store = client.beta.vector_stores.create(
    name="my-docs",
    file_ids=[file.id],
)

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