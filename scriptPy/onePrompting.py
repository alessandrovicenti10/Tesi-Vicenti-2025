import json
import openai
from openai import OpenAI
from together import Together

#client = Together(api_key = "api_key")
#API_KEY = "APIKEY"
#client = openai.OpenAI(api_key=API_KEY)
#MODEL = "gpt-4.1-nano-2025-04-14"

API_KEY = "APIKEY"  # Sostituisci con la tua API Key
MODEL = "anthropic/claude-3.7-sonnet"    #"google/gemini-2.5-pro-preview-03-25"   #"anthropic/claude-3.7-sonnet" #"google/gemini-2.0-flash-thinking-exp:free"       
#"meta-llama/llama-4-maverick:free"  #"mistralai/mistral-small-3.1-24b-instruct:free" #"deepseek/deepseek-chat-v3-0324:free"
BASE_URL = "https://openrouter.ai/api/v1"

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


def estimate_co2_for_product(product_data, llm_model=MODEL):
    """
    Esempio di funzione che interroga un LLM per stimare la CO2e in kg
    di un prodotto sulla base dei dati in input.
    """

    # Prepara il prompt con le informazioni di contesto
    prompt = f"""
    You are an expert in life cycle analysis (LCA). 
    Give me the CO2e emissions value in kg for the following product, 
    using its characteristics and assuming the percentage of materials, emission factors and most important 
    international protocols.

    Product data: {json.dumps(product_data, ensure_ascii=False)}

    Reply ONLY with a JSON object containing these exact fields:
    {{
        "co2e_kg": <number>,
        "explanation": "<detailed explanation>"
    }}
    Do not include any markdown formatting or additional JSON wrappers.
    """

    try:
        response = client.chat.completions.create(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        
        print("Full API Response:", response)  # Debug print
        
        if not response or not hasattr(response, 'choices') or not response.choices:
            raise Exception("Invalid API response structure")

        content = response.choices[0].message.content.strip()
        print("Raw content:", content)  # Debug print
        
        # Clean the response if it contains markdown or extra text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        # Try to find and extract just the JSON object if there's additional text
        if "{" in content and "}" in content:
            start = content.rfind("{")
            end = content.rfind("}") + 1
            content = content[start:end]
            
        print("Cleaned content:", content)  # Debug print
        
        # Validate JSON before returning
        json.loads(content)  # Test if it's valid JSON
        return content
        
    except Exception as e:
        print(f"API or parsing error: {str(e)}")
        return json.dumps({
            "co2e_kg": None,
            "explanation": f"Error in API response or parsing: {str(e)}"
        })

def main(num_rows):
    # Carica i dati dal tuo file .jsonl
    products = []
    with open("../dataset/Multi_products.jsonl", "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= num_rows:
                break
            product = json.loads(line.strip())
            products.append(product)

    results = []

    # Itera su ciascun prodotto e chiedi al LLM di calcolare stima CO2e/kg
    for product in products:
        llm_answer = estimate_co2_for_product(product)
        
        try:
            # Remove any markdown formatting if present
            if "```json" in llm_answer:
                llm_answer = llm_answer.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_answer:
                llm_answer = llm_answer.split("```")[1].strip()
            
            # Parse the JSON response
            answer_data = json.loads(llm_answer)
            
            results.append({
                "product_name": product.get("title", "Senza nome"),
                "co2e_kg": answer_data.get("co2e_kg"),
                "explanation": answer_data.get("explanation")
            })
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for product {product.get('title', 'Unknown')}: {e}")
            results.append({
                "product_name": product.get("title", "Senza nome"),
                "co2e_kg": None,
                "explanation": f"Error parsing response: {llm_answer}"
            })
    
    # Salva i risultati in un file JSON
    with open("M_calude3.7sonnetaltiririiri.json", "w", encoding="utf-8") as out:
        json.dump(results, out, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main(16)
