import json
import pandas as pd
import openai


#client = Together(api_key = "api_key")
#API_KEY = "api_key"
#client = openai.OpenAI(api_key=API_KEY)
#MODEL = "gpt-4o"

API_KEY = "api_key"  # Sostituisci con la tua API Key
MODEL = "deepseek/deepseek-r1"   #"meta-llama/llama-4-maverick:free"  #"anthropic/claude-3.7-sonnet" #"google/gemini-2.0-flash-thinking-exp:free"  #"mistralai/mistral-small-3.1-24b-instruct:free" #"deepseek/deepseek-chat-v3-0324:free"
BASE_URL = "https://openrouter.ai/api/v1"

# Percorso del file JSONL contenente i dati dei prodotti Amazon Electronics
file_path = "../dataset/electronics.jsonl"

# Funzione per leggere il file JSONL e caricare il dataset
def load_dataset(file_path, num_rows):
    """
    Legge il dataset JSONL e restituisce un DataFrame pandas.
    Può limitare il numero di righe per una rapida ispezione.
    """
    data = []
    with open(file_path, "r") as file:
        for i, line in enumerate(file):
            if i >= num_rows:  # Legge solo le prime num_rows righe
                break
            data.append(json.loads(line))
    
    df = pd.DataFrame(data)
    return df

# Funzione per generare il prompt per la costruzione del processo di produzione
def generate_process_prompt(product_name):
    """
    Genera un prompt per un LLM per identificare le fasi del processo di produzione di un prodotto.
    """
    prompt_template = f"""
    You are now an expert in the production of "{product_name}".
    Please tell me the process stages involved in the "{product_name}" production process and
    return the results as follows:
    1. Output the result in JSON format without 'json' tag.
    2. The result is a list containing only the names of the production process, such as ["process A", "process B", "process C"]
    3. If you can't get an answer from known information, return the process involved in the generalization of "{product_name}" else return "None".
    """
    return prompt_template


# Funzione per chiamare l'API OpenAI con il prompt generato
def get_production_process_from_llm(prompt):
    """
    Invia il prompt all'API OpenAI e restituisce la risposta.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Usa GPT-4 per una risposta più precisa
            messages=[
                {"role": "system", "content": "Sei un esperto di analisi del ciclo di vita."},
                {"role": "user", "content": prompt}
            ],
            #max_tokens=150,  # Limita la lunghezza della risposta
            #n=1,  # Unica risposta
            #stop=None,  # Nessun carattere di stop specifico
            temperature=0.8  # Impostazione della temperatura per il controllo della creatività
        )
        
        # Estrai la risposta dalla risposta dell'API
        production_process = response.choices[0].message.content
        
        # Verifica se la risposta è vuota
        if not production_process.strip():
            print(f"Avviso: Risposta vuota per il prodotto '{prompt}'")
            return "None"
        
        # Log della risposta per debugging
        print(f"Risposta dell'API per '{prompt}': {production_process}")
        
        # Verifica se la risposta è un JSON valido
        try:
            process_list = json.loads(str(production_process))
            return process_list
        except json.JSONDecodeError:
            print(f"Errore: La risposta non è un JSON valido per il prodotto '{prompt}'")
            return "None"
    
    except Exception as e:
        print(f"Errore durante la chiamata API: {e}")
        return "None"
    

def generate_lci_prompt(product_name, process_list, current_process, unit="kg"):
    
    # Definizione del formato JSON per l'output
    output_format = {
        "Product": [{"name": "A", "quantity": 1, "unit": "kg"}],
        "Raw material": [{"name": "B", "quantity": 1, "unit": "kg", "source": "process"}],
        "Energy": [{"name": "C", "quantity": 1, "unit": "kWh"}],
        "Wastewater": [{"name": "D", "quantity": 1, "unit": "kg"}],
        "Solid waste": [{"name": "E", "quantity": 1, "unit": "kg"}],
        "Waste gas": [{"name": "F", "quantity": 1, "unit": "kg"}]
    }
    
    """
    Genera un prompt per un LLM per ottenere l'inventario del ciclo di vita di un prodotto.
    """
    prompt_template = f"""
    You are now an expert in the production of "{product_name}". The production process of
    "{product_name}" can be divided into the following stages: {process_list}. Based on your knowledge, standard, protoccol, and scientific research,
    please tell me what raw materials and energy are needed, what products,
    and waste gas are produced in the "{current_process}" process of producing 1 {unit} of
    "{product_name}", and provide the corresponding quantities of raw materials, energy, products,
    and waste gas in JSON format. Please note the following requirements:
    
    1. The entity types included in JSON must belong to: [Product, Raw material, Energy, Waste gas].
    2. The JSON format must be as follows: {output_format}.
    3. The units used in the results should be in international standard units: [kg].
    4. If the substance in "Raw material" comes from a previous process, it should be noted which process it comes from in "source"; if not, "source" should be "None".
    """
    return prompt_template


# Funzione per chiamare l'API OpenAI per ottenere l'inventario del ciclo di vita (LCI)
def get_lci_from_llm(prompt):
    """
    Invia il prompt all'API OpenAI e restituisce l'inventario del ciclo di vita (LCI).
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Usa GPT-4 per una risposta più precisa
            messages=[
                {"role": "system", "content": "Sei un esperto di analisi del ciclo di vita."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8  # Impostazione della temperatura per il controllo della creatività
        )
        
        # Estrai la risposta dalla risposta dell'API
        lci_data = response.choices[0].message.content
        return lci_data
    
    except Exception as e:
        print(f"Errore durante la chiamata API: {e}")
        return "None"

    
# Caricamento del dataset (con un subset di 10 righe per test)
df = load_dataset(file_path, num_rows=1)

# Generazione dei prompt e invio all'API OpenAI per ottenere i processi di produzione
for index, row in df.iterrows():
    product_name = row.get("title", "Unknown Product")
    prompt_process = generate_process_prompt(product_name)
    
    print(f"Invio del prompt per il prodotto '{product_name}'...\n")
    print(prompt_process)
    
    # Chiamata all'API per ottenere il processo di produzione
    production_process = get_production_process_from_llm(prompt_process)
    print(f"Processo di produzione per '{product_name}':\n{production_process}")
    
    # Verifica che siano stati identificati dei processi di produzione
    if production_process != "None":
        try:
            process_list = production_process # Lista dei processi di produzione
            for process in process_list:
                # Per ogni processo, genera il prompt per l'inventario del ciclo di vita
                prompt_lci = generate_lci_prompt(product_name, process_list, process)
                
                print(f"Invio del prompt per l'inventario del ciclo di vita del processo '{process}'...\n")
                print(prompt_lci)
                
                # Chiamata all'API per ottenere l'inventario del ciclo di vita
                lci_data = get_lci_from_llm(prompt_lci)
                print(f"Inventario del ciclo di vita per '{product_name}' (processo {process}):\n{lci_data}")
        
        except json.JSONDecodeError:
            print(f"Errore nel decodificare i dati per '{product_name}'")
    
    print("-" * 80)
