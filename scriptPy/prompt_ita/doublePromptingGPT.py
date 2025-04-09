import json
import openai

# Esempio: se usi l’API di OpenAI (usa la tua chiave in openai.api_key)
API_KEY = "api_key"
client = openai.OpenAI(api_key=API_KEY)
MODEL= "gpt-4o"

def get_material_composition(product_data, llm_model=MODEL):
    """
    Primo prompt: genera composizione dei materiali e percentuali.
    """
    prompt = f"""
    Sei un esperto in valutazione ambientale e product design.

    A partire dai seguenti dati di un prodotto elettronico venduto su Amazon,
    identifica i materiali che probabilmente lo compongono e stima per ciascun materiale
    una percentuale di composizione (in % sul peso totale).

    Rispondi solo in JSON con questo formato:
    {{
        "materials": [
            {{"name": "...", "percentage": ...}},
            ...
        ]
    }}

    Dati del prodotto: {json.dumps(product_data, ensure_ascii=False)}
    """

    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    print(f"{response.choices[0].message.content.strip()}")
    raw_content = response.choices[0].message.content.strip()

    # Rimuove eventuali blocchi markdown
    if raw_content.startswith("```json"):
        raw_content = raw_content.replace("```json", "").replace("```", "").strip()
    elif raw_content.startswith("```"):
        raw_content = raw_content.replace("```", "").strip()

    # Ora possiamo fare il parsing JSON
    materials_data = json.loads(raw_content)
    try:
        #print(f"{materials_data}")
        return materials_data
    except:
        return {"materials": []}


def estimate_co2_from_materials(product_data, materials_json, llm_model=MODEL):
    """
    Secondo prompt: stima CO2e/kg basandosi sulla composizione.
    """
    prompt = f"""
    Sei un esperto di analisi LCA e valutazione del ciclo di vita ambientale.

    A partire dalla seguente composizione di materiali e dalle informazioni sul prodotto,
    stima l'impatto in termini di emissioni di CO2 equivalente per kg (CO2e/kg)
    tenendo conto dei fattori di emissione comuni per i materiali indicati.
    
    Se i materiali indicati non sono disponibili, stimali e generali a partire dai dati del prodotto in input.

    Rispondi solo in JSON con il formato:
    {{
        "co2e_kg": ...,
        "explanation": "..."
    }}

    Dati del prodotto: {json.dumps(product_data, ensure_ascii=False)}
    Composizione materiali stimata: {json.dumps(materials_json, ensure_ascii=False)}
    """

    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    try:
        raw_content = response.choices[0].message.content.strip()

        # Rimuove eventuali blocchi markdown
        if raw_content.startswith("```json"):
            raw_content = raw_content.replace("```json", "").replace("```", "").strip()
        elif raw_content.startswith("```"):
            raw_content = raw_content.replace("```", "").strip()
        materials_data = json.loads(raw_content)
        return materials_data
    except:
        return {
            "co2e_kg": None,
            "explanation": "Errore nella generazione o parsing della risposta"
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
    with open("co2_estimates_OR_double_ita2.json", "w", encoding="utf-8") as out:
        json.dump(results, out, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main(10)
