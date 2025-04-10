import json
from openai import OpenAI
from together import Together
import openai

#client = Together(api_key = "api_key")
#API_KEY = "api_key"
#client = openai.OpenAI(api_key=API_KEY)
#MODEL = "gpt-4o"

API_KEY = "api_key"  # Sostituisci con la tua API Key
MODEL = "deepseek/deepseek-r1"   #"meta-llama/llama-4-maverick:free"  #"anthropic/claude-3.7-sonnet" #"google/gemini-2.0-flash-thinking-exp:free"  #"mistralai/mistral-small-3.1-24b-instruct:free" #"deepseek/deepseek-chat-v3-0324:free"
BASE_URL = "https://openrouter.ai/api/v1"

#client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

def get_material_composition(product_data, llm_model=MODEL):
    """
    Primo prompt: genera composizione dei materiali e percentuali.
    """
    prompt = f"""
    You are an expert in environmental assessment and product design.

    From the following data of an electronic product sold on Amazon,
    Identify the materials likely to make it up and estimate for each material
    a percentage composition (in % of the total weight).

    Reply only in JSON with this format:
    {{
        "materials": [
            {{"name": "...", "percentage": ...}},
            ...
        ]
    }}

    Product Data: {json.dumps(product_data, ensure_ascii=False)}
    """

    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    # Add debug print to see raw response
    #print("Raw API Response:", response.choices[0].message.content)

    try:
        raw_content = response.choices[0].message.content.strip()
        print(f"Raw response from materials: {raw_content}")  # Debug print
        
        # Cerca di estrarre solo la parte JSON se c'è testo aggiuntivo
        if "{" in raw_content and "}" in raw_content:
            start = raw_content.find("{")
            end = raw_content.rfind("}") + 1
            raw_content = raw_content[start:end]
            
        # Rimuove eventuali blocchi markdown
        if raw_content.startswith("```json"):
            raw_content = raw_content.replace("```json", "").replace("```", "").strip()
        elif raw_content.startswith("```"):
            raw_content = raw_content.replace("```", "").strip()

        print(f"Cleaned content for parsing: {raw_content}")  # Debug print
        
        materials_data = json.loads(raw_content)
        return materials_data
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in materials: {e}\nContent: {raw_content}")
        return {"materials": []}
    except Exception as e:
        print(f"Unexpected error in materials: {e}")
        return {"materials": []}

def estimate_co2_from_materials(product_data, materials_json, llm_model=MODEL):
    """
    Secondo prompt: stima CO2e/kg basandosi sulla composizione.
    """
    prompt = f"""
    You are an expert in LCA and environmental life cycle assessment.

    From the following material composition and product information,
    estimate the impact in terms of total Co2e emissions in kg for the product.
    Taking into account the emission factors common to the materials listed.
    
    If the materials indicated are not available, estimate and general from the input product data.

    Reply only in JSON with this format:
    {{
        "co2e_kg": ...,
        "explanation": "..."
    }}

    Product data: {json.dumps(product_data, ensure_ascii=False)}
    Estimated material composition: {json.dumps(materials_json, ensure_ascii=False)}
    """

    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    try:
        raw_content = response.choices[0].message.content.strip()
        print(f"Raw response from CO2: {raw_content}")  # Debug print

        # Cerca di estrarre solo la parte JSON se c'è testo aggiuntivo
        if "{" in raw_content and "}" in raw_content:
            start = raw_content.find("{")
            end = raw_content.rfind("}") + 1
            raw_content = raw_content[start:end]

        # Rimuove eventuali blocchi markdown
        if raw_content.startswith("```json"):
            raw_content = raw_content.replace("```json", "").replace("```", "").strip()
        elif raw_content.startswith("```"):
            raw_content = raw_content.replace("```", "").strip()

        print(f"Cleaned content for parsing: {raw_content}")  # Debug print
        
        materials_data = json.loads(raw_content)
        return materials_data
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in CO2: {e}\nContent: {raw_content}")
        return {
            "co2e_kg": None,
            "explanation": f"Error parsing JSON response: {str(e)}"
        }
    except Exception as e:
        print(f"Unexpected error in CO2: {e}")
        return {
            "co2e_kg": None,
            "explanation": f"Error processing response: {str(e)}"
        }


def main(num_rows):
    products = []
    with open("../dataset/elctronics.jsonl", "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= num_rows:
                break
            product = json.loads(line.strip())
            products.append(product)

    results = []

    for product in products:
        print(f"Elaborazione: {product.get('title', 'senza nome')[:60]}...")

        # Step 1: composizione materiali
        materials_json = get_material_composition(product)

        # Step 2: stima CO2e/kg
        co2_data = estimate_co2_from_materials(product, materials_json)

        results.append({
            "product_name": product.get("title", "Senza nome"),
            "co2e_kg": co2_data.get("co2e_kg"),
            "explanation": co2_data.get("explanation")
        })

    # Salva il risultato finale
    with open("gpt_4o_double_en.json", "w", encoding="utf-8") as out:
        json.dump(results, out, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main(10)
