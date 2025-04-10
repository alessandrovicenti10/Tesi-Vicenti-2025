import openai
import json
import time
import re

#client = Together(api_key = "api_key")
#API_KEY = "api_key"
#client = openai.OpenAI(api_key=API_KEY)
#MODEL = "gpt-4o"

API_KEY = "api_key"  # Sostituisci con la tua API Key
MODEL = "deepseek/deepseek-r1"   #"meta-llama/llama-4-maverick:free"  #"anthropic/claude-3.7-sonnet" #"google/gemini-2.0-flash-thinking-exp:free"  #"mistralai/mistral-small-3.1-24b-instruct:free" #"deepseek/deepseek-chat-v3-0324:free"
BASE_URL = "https://openrouter.ai/api/v1"
# Inizializza OpenAI
client = openai.OpenAI(api_key=API_KEY)

def generate_production_process(product_name):
    """ Genera le fasi del processo produttivo per un determinato prodotto elettronico."""
    
    output_format = {
        "Product": [{"name": "A", "quantity": 1, "unit": "kg"}],
        "Raw material": [{"name": "B", "quantity": 1, "unit": "kg", "source": "process"}],
        "Energy": [{"name": "C", "quantity": 1, "unit": "kWh"}],
        "Wastewater": [{"name": "D", "quantity": 1, "unit": "kg"}],
        "Solid waste": [{"name": "E", "quantity": 1, "unit": "kg"}],
        "Waste gas": [{"name": "F", "quantity": 1, "unit": "kg"}]
    }
    
    # Conversione `output_format` in una stringa JSON ben formattata
    #output_format_str = json.dumps(output_format, indent=4)
    
    prompt = f'''
    You are an expert in producing "{product_name}".
    Examines and searches the production stages of "{product_name}".
    Then, on the basis of the identified stages, gender and provide me with the product life cycle inventory.
    Example format: '{output_format}'
    If you do not have enough specific information, proceed with a generalized estimate of that product.
    '''
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an industrial process expert."},
            {"role": "user", "content": prompt}
        ],
        #max_tokens=300
    )
    
    raw_response = response.choices[0].message.content
    #print("Risposta API:", raw_response)  # Debug

    # Rimuove i backtick e altre possibili formattazioni errate
    #cleaned_response = re.sub(r"```json|```", "", raw_response).strip()
    try:
        return raw_response
    except json.JSONDecodeError:
      print("Errore nel parsing JSON. La risposta potrebbe non essere in formato corretto.")
    return None


def generate_life_cycle_inventory(product_name, process_list):
    """ Genera l'inventario del ciclo di vita per ogni fase del processo. """
    
    # Definizione del formato JSON per l'output
    output_format = {
        "Product": [{"name": "A", "quantity": 1, "unit": "kg"}],
        "Raw material": [{"name": "B", "quantity": 1, "unit": "kg", "source": "process"}],
        "Energy": [{"name": "C", "quantity": 1, "unit": "kWh"}],
        "Wastewater": [{"name": "D", "quantity": 1, "unit": "kg"}],
        "Solid waste": [{"name": "E", "quantity": 1, "unit": "kg"}],
        "Waste gas": [{"name": "F", "quantity": 1, "unit": "kg"}]
    }
    
    # Conversione `output_format` in una stringa JSON ben formattata
    output_format_str = json.dumps(output_format, indent=4)

    inventory = {}
    for process in process_list:
        prompt = f'''
        Sei un esperto nella produzione di "{product_name}". 
        La produzione è suddivisa nelle seguenti fasi: {process_list}.
        Fornisci input (materie prime, energia) e output (prodotti, rifiuti) per la fase "{process}" in formato JSON.
        
        Il formato JSON deve essere esattamente il seguente:
        {output_format_str}
        
        Rispondi solo con il JSON, senza testo aggiuntivo o spiegazioni
        '''

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Sei un esperto di analisi del ciclo di vita."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )

        raw_response = response.choices[0].message.content
        print(f"Risposta API per {process}: {raw_response}")  # Debug
        
        try:
            inventory[process] = json.loads(raw_response)
        except json.JSONDecodeError:
            print(f"Errore nel parsing JSON per il processo {process}. La risposta potrebbe non essere in formato corretto.")
            inventory[process] = None
        
        time.sleep(1)  # Evita il rate limit

    return inventory


# Test
if __name__ == "__main__":
    product_name = "Valley Enterprises TYT FTDI USB Radio Programming Cable TH-2R, TH-UV3R, TH-7800, TH-9800"
    print(f"Generazione del processo produttivo per {product_name}...")
    process_list = generate_production_process(product_name)
    print("Processi identificati:", process_list)
