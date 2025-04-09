import openai
import json

#funzione get_weather implementata nel codice
import requests

def get_weather(latitude, longitude):
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m") #chiamata ad un API pubblica
    data = response.json()
    return data['current']['temperature_2m']

# Inizializza il client con la tua API Key
client = openai.OpenAI(api_key="api_key")

# Definizione della funzione come tool
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current temperature for provided coordinates in celsius.",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"}
            },
            "required": ["latitude", "longitude"],
            "additionalProperties": False
        },
        "strict": True
    }
}]

messages = [{"role": "user", "content": "What's the weather like in Paris today?"}]


# Creazione della richiesta al modello con la funzione
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools
)

# Stampa l'output della funzione chiamata
if completion.choices and completion.choices[0].message.tool_calls:
    print(completion.choices[0].message.tool_calls)
else:
    print("No tool calls in response.")

tool_call = completion.choices[0].message.tool_calls[0]
args = json.loads(tool_call.function.arguments)

result = get_weather(args["latitude"], args["longitude"])

messages.append(completion.choices[0].message)  # append model's function call message
messages.append({                               # append result message
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": str(result)
})

completion_2 = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)

print(completion_2.choices[0].message.content)