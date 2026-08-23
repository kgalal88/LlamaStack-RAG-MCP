import json
from openai import OpenAI

# Initialize client
client = OpenAI(base_url="http://localhost:8321/v1", api_key="fake")

# 1. Mock local function
def get_weather(location):
    mock_data = {
        "Riyadh": {"temperature": "40°C", "condition": "Sunny"},
        "Tokyo": {"temperature": "22°C", "condition": "Rainy"},
        "London": {"temperature": "15°C", "condition": "Cloudy"},        
    }
    data = mock_data.get(location)
    return json.dumps({"location": location, **data})

tools_map = {
    "get_weather": get_weather
}

# 2. Tool definitions schema
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
        },
    }
}]

messages = [{"role": "user", "content": "What is the weather like in Tokyo?"}]

# 3. Initial request
response = client.chat.completions.create(
    model="vllm/Qwen/Qwen3-4B",
    messages=messages,
    tools=tools,
)

response_message = response.choices[0].message
tool_calls = response_message.tool_calls

# 4. Handle tool calls if requested
if tool_calls:
    messages.append(response_message)  # Extend conversation with assistant's response
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        # Execute the function
        function_to_call = tools_map[function_name]
        function_response = function_to_call(**function_args)
        
        # Append tool response message
        messages.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": function_response,
        })

    # 5. Get final response from the model
    final_response = client.chat.completions.create(
        model="vllm/Qwen/Qwen3-4B",
        messages=messages,
    )
    
    print(final_response.choices[0].message.content)