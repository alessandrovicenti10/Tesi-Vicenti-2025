import json
from openai import OpenAI
from together import Together
import openai

#client = Together(api_key = "5a49da191ec54d69ba99d57d9f6413d527a061172fbd48d51cfbeee2e7561568")
API_KEY = "APIKEY"
client = openai.OpenAI(api_key=API_KEY)
MODEL =  "gpt-4.1-mini-2025-04-14" #"o1-2024-12-17" #"o3-mini-2025-01-31" #"gpt-4.1-nano-2025-04-14" #"gpt-4o-2024-08-06" #"o3-2025-04-16"

#API_KEY = "APIKEY"  # Sostituisci con la tua API Key
#MODEL = "google/gemini-2.5-pro-preview-03-25"  #"deepseek/deepseek-r1:free" # "perplexity/sonar-deep-research"     #"google/gemini-2.5-pro-preview-03-25"   #"anthropic/claude-3.7-sonnet" #"google/gemini-2.0-flash-thinking-exp:free"   
#"meta-llama/llama-4-maverick:free"  #"mistralai/mistral-small-3.1-24b-instruct:free" #"deepseek/deepseek-chat-v3-0324:free"
#BASE_URL = "https://openrouter.ai/api/v1"

#client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


def estimate_co2_for_product(product_data, llm_model=MODEL):
    """
    Esempio di funzione che interroga un LLM per stimare la CO2e
    di un prodotto sulla base dei dati in input.
    """

    # Prepara il prompt con le informazioni di contesto
    prompt = f"""
    You are an expert in life cycle analysis (LCA) and CO2e emission calculation for electronic products.
    You must estimate the CO2e emissions, based on the entire life cycle (cradle to grave), for the following electronic product.

    Product data: {json.dumps(product_data, ensure_ascii=False)}

    INSTRUCTIONS:
    1. FIRST, check if there are any official carbon footprint reports or environmental product declarations (EPD) 
       from the manufacturer for this specific product.
       If found, use these official values as your primary source.

    2. If NO official manufacturer reports are available, then estimate emissions following these protocols:
       - GHG Protocol Product Standard for system boundaries and calculation methodology
       - ISO 14040/14044 for Life Cycle Assessment principles
       - PAS 2050 and ISO/TS 14067 for carbon footprint calculation guidelines

    3. For estimation, consider:
       - Main materials composition
       - Manufacturing processes
       - Transportation
       - Use phase energy consumption
       - End-of-life disposal

    4. Use the most recent emission factors and scientific data available
    5. Document your sources and assumptions in the explanation
    6. Clearly state if you're using manufacturer data or estimation

    Reply ONLY with a JSON object containing these exact fields:
    {{
        "co2e_kg": <number>,
        "explanation": "<detailed explanation including data source (manufacturer report or estimation)>"
    }}
    Do not include any markdown formatting or additional JSON wrappers.
    """

    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    print(response)
    
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
    with open("../dataset/Multi_products.jsonl", "r", encoding="utf-8") as f:
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
    with open("Mlca_gpt4.1mini_4.json", "w", encoding="utf-8") as out:
        json.dump(results, out, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main(26)
