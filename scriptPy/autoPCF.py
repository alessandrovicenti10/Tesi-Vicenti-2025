import json
#import pandas as pd
import openai
from openai import OpenAI
from together import Together

#client = Together(api_key = "api_key")
#API_KEY = "api_key"
#client = openai.OpenAI(api_key=API_KEY)
#MODEL = "gpt-4o"

API_KEY = "api_key"  # Sostituisci con la tua API Key
MODEL = "deepseek/deepseek-r1"   #"meta-llama/llama-4-maverick:free"  #"anthropic/claude-3.7-sonnet" #"google/gemini-2.0-flash-thinking-exp:free"  #"mistralai/mistral-small-3.1-24b-instruct:free" #"deepseek/deepseek-chat-v3-0324:free"
BASE_URL = "https://openrouter.ai/api/v1"

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

def load_dataset(file_path, num_rows):
    data = []
    with open(file_path, "r") as file:
        for i, line in enumerate(file):
            if i >= num_rows:
                break
            data.append(json.loads(line))
    return data

def get_materials_composition(product_data):
    """First prompt: Analyze product materials composition"""
    prompt = f"""
    You are an expert in product design and materials engineering.
    Analyze the following product and identify its likely material composition:
    
    Product: {json.dumps(product_data, ensure_ascii=False)}
    
    List the main materials and their approximate percentages.
    Reply ONLY with a JSON list of materials, like:
    {{
        "materials": [
            {{"name": "material1", "percentage": XX}},
            {{"name": "material2", "percentage": YY}}
        ]
    }}
    """
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    print("api", response)
    return response.choices[0].message.content

def get_manufacturing_process(product_data, materials):
    """Second prompt: Analyze manufacturing process and energy"""
    prompt = f"""
    You are an expert in manufacturing processes and industrial energy consumption.
    For this product and its materials:
    
    Product: {json.dumps(product_data, ensure_ascii=False)}
    Materials: {materials}
    
    Analyze the manufacturing processes and their energy requirements.
    Consider:
    1. Raw material processing
    2. Manufacturing steps
    3. Assembly processes
    4. Energy consumption per kg of product
    
    Reply ONLY with a JSON containing manufacturing CO2e impact, like:
    {{
        "manufacturing_co2e_kg": XX,
        "explanation": "detailed short reasoning"
    }}
    """
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content

def calculate_final_co2e(product_data, materials_data, manufacturing_data):
    """Final prompt: Calculate total CO2e based on all factors"""
    prompt = f"""
    You are an expert in life cycle assessment (LCA) and carbon footprint calculation, following established international standards and protocols.
    Based on all the analyzed data and following GHG Protocol Product Standard, ISO 14040/14044 LCA methodology, PAS 2050, and ISO/TS 14067 guidelines:
    
    Product: {json.dumps(product_data, ensure_ascii=False)}
    Materials: {materials_data}
    Manufacturing: {manufacturing_data}
    
    Calculate the total CO2e emissions in kg for this product following these methodological steps:
    1. System Boundaries Definition (as per GHG Protocol Product Standard):
       - Material extraction and processing (Scope 3 upstream)
       - Manufacturing emissions (Scope 1 & 2)
       - Transportation and distribution (Scope 3 upstream & downstream)
       - End-of-life disposal (Scope 3 downstream)

    2. Life Cycle Inventory Analysis (as per ISO 14040/14044):
       - Consider all inputs (materials, energy) and outputs (emissions, waste)
       - Use appropriate emission factors for each process
       - Account for primary and secondary data where available

    3. Carbon Footprint Calculation (following PAS 2050 and ISO/TS 14067):
       - Convert all GHG emissions to CO2e using appropriate GWP values
       - Include all relevant direct and indirect emissions
       - Consider the complete product life cycle

    Reply ONLY with a JSON in this exact format:
    {{
        "co2e_kg": XX.XX,
        "explanation": "detailed short explanation of calculations and assumptions, referencing relevant standards"
    }}
    """
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content

def main(num_rows):
    products = load_dataset("../dataset/elctronics.jsonl", num_rows)
    results = []
    
    for product in products:
        try:
            # Step 1: Material composition analysis
            materials_data = get_materials_composition(product)
            
            # Step 2: Manufacturing process analysis
            manufacturing_data = get_manufacturing_process(product, materials_data)
            
            # Step 3: Final CO2e calculation
            final_result = calculate_final_co2e(product, materials_data, manufacturing_data)
            
            # Parse the final result
            try:
                if "```json" in final_result:
                    final_result = final_result.split("```json")[1].split("```")[0].strip()
                elif "```" in final_result:
                    final_result = final_result.split("```")[1].strip()
                
                answer_data = json.loads(final_result)
                
                results.append({
                    "product_name": product.get("title", "Senza nome"),
                    "co2e_kg": answer_data.get("co2e_kg"),
                    "explanation": answer_data.get("explanation")
                })
            except json.JSONDecodeError as e:
                print(f"Error parsing final result: {e}")
                results.append({
                    "product_name": product.get("title", "Senza nome"),
                    "co2e_kg": None,
                    "explanation": f"Error parsing response: {final_result}"
                })
                
        except Exception as e:
            print(f"Error processing product {product.get('title', 'Unknown')}: {e}")
            results.append({
                "product_name": product.get("title", "Senza nome"),
                "co2e_kg": None,
                "explanation": f"Error during processing: {str(e)}"
            })
    
    # Save results
    with open("autoPCF_deepseekR1.json", "w", encoding="utf-8") as out:
        json.dump(results, out, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main(10)