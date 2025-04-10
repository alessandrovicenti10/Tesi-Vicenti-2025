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


def estimate_co2_for_product(product_data, llm_model=MODEL):
    """
    Esempio di funzione che interroga un LLM per stimare la CO2e
    di un prodotto sulla base dei dati in input.
    """

    # Prepara il prompt con le informazioni di contesto
    prompt = f"""
    You are an expert in life cycle analysis (LCA) and CO2e emission calculation for electronic products.
    You must estimate the CO2e emissions, based on the entire life cycle, that is cradle to grave phase, for the following electronic product.

    Product data: {json.dumps(product_data, ensure_ascii=False)}

    INSTRUCTIONS:
    1. Analyze the product information.
    2. Consider the main materials of the product.
    3. Estimate the emission factor in kg of CO2e based on reference factors.
    4. Give a brief explanation of your reasoning.
    5. If information is missing, make reasonable assumptions based on similar products and scientific sources and protocols/standards.
    6. Use scientific methods and protocols/standards.
    7. Use the most recent data available.
    8. Use the most accurate methods available.

    Reply ONLY with a JSON object containing these exact fields:
    {{
        "co2e_kg": <number>,
        "explanation": "<detailed explanation>"
    }}
    Do not include any markdown formatting or additional JSON wrappers.
    """

    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    
    # Proteggi l'accesso in caso la risposta sia None o vuota
    if not response or not response.choices:
        print("Errore: la risposta dal modello è vuota o malformata.")
        return json.dumps({
            "co2e_kg": None,
            "explanation": "Errore: nessuna risposta ricevuta dal modello."
        })

    # Altrimenti tutto ok
    try:
        raw_content = response.choices[0].message.content.strip()
        print(f"\nProcessing product: {product_data.get('title', 'Unknown')[:60]}...")
        
        # Extract JSON object if there's additional text
        if "{" in raw_content and "}" in raw_content:
            start = raw_content.rfind("{")  # Get the last JSON object
            end = raw_content.rfind("}") + 1
            raw_content = raw_content[start:end]
            
        # Clean any remaining newlines or extra spaces
        raw_content = raw_content.replace('\n', ' ').strip()
        
        # Validate JSON before returning
        json.loads(raw_content)  # Test if it's valid JSON
        return raw_content
        
    except Exception as e:
        print(f"Error processing response: {str(e)}")
        return json.dumps({
            "co2e_kg": None,
            "explanation": f"Error processing response: {str(e)}"
        })

def main(num_rows):
    # Carica i dati dal tuo file .jsonl
    products = []
    with open("../dataset/elctronics.jsonl", "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= num_rows:
                break
            product = json.loads(line.strip())
            products.append(product)

    results = []

    # Itera su ciascun prodotto e chiedi al LLM di calcolare stima CO2e/kg
    for product in products:
        try:
            llm_answer = estimate_co2_for_product(product)
            
            # Clean and parse the response
            if isinstance(llm_answer, str):
                # Remove any markdown formatting if present
                if "```json" in llm_answer:
                    llm_answer = llm_answer.split("```json")[1].split("```")[0].strip()
                elif "```" in llm_answer:
                    llm_answer = llm_answer.split("```")[1].strip()
                
                # Find and extract JSON if there's additional text
                if "{" in llm_answer and "}" in llm_answer:
                    start = llm_answer.rfind("{")
                    end = llm_answer.rfind("}") + 1
                    llm_answer = llm_answer[start:end]
                
                llm_answer = llm_answer.strip()
            
            # Parse the JSON response
            answer_data = json.loads(llm_answer)
            
            results.append({
                "product_name": product.get("title", "Senza nome"),
                "co2e_kg": answer_data.get("co2e_kg"),
                "explanation": answer_data.get("explanation")
            })
            
        except Exception as e:
            print(f"Error processing product {product.get('title', 'Unknown')[:60]}: {e}")
            results.append({
                "product_name": product.get("title", "Senza nome"),
                "co2e_kg": None,
                "explanation": f"Error processing response: {llm_answer}"
            })
    
    # Salva i risultati in un file JSON
    with open("lca_gpt_4o_en.json", "w", encoding="utf-8") as out:
        json.dump(results, out, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main(10)
