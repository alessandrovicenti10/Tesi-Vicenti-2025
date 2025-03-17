import openai
import json
import pandas as pd  # Libreria per gestire il dataset

# Funzione per recuperare i dati di emissioni di CO2 da un CSV
def get_co2_emission(material_name, quantity):
    df = pd.read_csv("materials_co2_emission_gpt.csv")  # Carica il dataset co2_data.csv
    print(df.columns)  # Stampa le colonne per verificare il nome esatto
    row = df[df["material"].str.lower() == material_name.lower()]  # Trova il materiale richiesto
    
    if row.empty:
        return f"No data available for {material_name}"
    
    total = (row["CO2_kg"].values[0]) * quantity
    return {
        "material": material_name,
        "CO2/kg": row["CO2_kg"].values[0],
        "totale": total,
        "source": "Local dataset: materials_co2_emission_gpt.csv"
    }

# Inizializza il client con la tua API Key
client = openai.OpenAI(api_key="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")

# Definizione della funzione come tool
tools = [{
    "type": "function",
    "function": {
        "name": "get_co2_emission",
        "description": "Retrieve CO2 emission data for a given material quantity (kg CO2 per kg).",
        "parameters": {
            "type": "object",
            "properties": {
                "material_name": {
                    "type": "string",
                    "description": "The name of the material to look up."
                },
                "quantity" : {
                    "type": "number",
                    "description": "The quantity of the material in the product."
                }
            },
            "required": ["material_name", "quantity"],
            "additionalProperties": False
        }
    }
}]

messages = [{"role": "user", "content": "How much CO2 is total emitted for 2 kg of Steel production? Provide the answer in JSON format"},]

# Chiamata a GPT con Function Calling
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools
)

# Controlla se GPT ha chiamato la funzione
if completion.choices and completion.choices[0].message.tool_calls:
    tool_call = completion.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)

    # Recupera il dato dal dataset locale
    result = get_co2_emission(args["material_name"], args["quantity"])

    # Aggiorna il contesto della conversazione con il risultato 
    messages.append(completion.choices[0].message)  # Risposta di GPT con la richiesta della funzione
    messages.append({                               # Risultato della funzione
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result)
    })

    # Esegue una nuova richiesta per ottenere un output strutturato
    final_response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": "json_object"}, 
    )

    print(final_response.choices[0].message.content)