import httpx
from openai import OpenAI

# Initialize custom HTTP client with explicit timeout configuration
http_client = httpx.Client(
    timeout=httpx.Timeout(60.0, connect=10.0),
    follow_redirects=True
)

# Point client directly to your Llama Stack server endpoint
client = OpenAI(
    base_url="http://localhost:8321/v1",  # Or http://localhost:5000/v1
    api_key="fake",  # API key is required by OpenAI SDK but ignored by Llama Stack
    http_client=http_client
)

# 1. List all vector stores registered in Llama Stack
vector_stores = client.vector_stores.list()
for vs in vector_stores.data:
    print(f"Store ID: {vs.id} | Name: {vs.name} | File Count: {vs.file_counts.completed}")

    # 2. Get details for a specific vector store
    vector_store_id = vs.id  # Replace with your vector_db_id
    store_details = client.vector_stores.retrieve(vector_store_id)
    print(f"\nRetrieved Store: {store_details.id} | Status: {store_details.status}")

    # 3. List files attached to the vector store
    store_files = client.vector_stores.files.list(vector_store_id=vector_store_id)
    for file in store_files.data:
        print(f"File ID: {file.id} | Status: {file.status}")